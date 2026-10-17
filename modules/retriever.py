"""
Retriever + basit Knowledge Graph
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
import json

from sentence_transformers import SentenceTransformer
import networkx as nx

import config
from modules.indexer import indexer


class KnowledgeGraph:
    """Basit ama etkili entity-relationship graph."""

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._path = config.INDEX_DIR / "knowledge_graph.json"
        self.load()

    def load(self):
        if self._path.exists():
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self.graph = nx.node_link_graph(data, directed=True, multigraph=True)
        else:
            self.graph = nx.MultiDiGraph()

    def save(self):
        data = nx.node_link_data(self.graph)
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_entity(self, name: str, entity_type: str = "character", **attrs):
        name = name.strip()
        if name not in self.graph:
            self.graph.add_node(name, type=entity_type, **attrs)
        else:
            self.graph.nodes[name].update(attrs)

    def add_relation(self, source: str, relation: str, target: str, **attrs):
        self.graph.add_edge(source.strip(), target.strip(), key=relation, relation=relation, **attrs)

    def get_related(self, name: str, depth: int = 1) -> List[Dict]:
        if name not in self.graph:
            return []
        results = []
        for node in nx.ego_graph(self.graph, name, radius=depth).nodes:
            if node != name:
                results.append({
                    "name": node,
                    "type": self.graph.nodes[node].get("type", "unknown"),
                    "attrs": dict(self.graph.nodes[node]),
                })
        return results

    def get_relations(self, name: str) -> List[Dict]:
        if name not in self.graph:
            return []
        rels = []
        for _, target, data in self.graph.out_edges(name, data=True):
            rels.append({"direction": "out", "relation": data.get("relation"), "target": target})
        for source, _, data in self.graph.in_edges(name, data=True):
            rels.append({"direction": "in", "relation": data.get("relation"), "source": source})
        return rels


class Retriever:
    def __init__(self):
        self.kg = KnowledgeGraph()
        self.embedder = None

    def _get_embedder(self):
        if self.embedder is None:
            self.embedder = SentenceTransformer(config.TEXT_EMBEDDING_MODEL)
        return self.embedder

    def search(self, query: str, top_k: int = None, filter_category: Optional[str] = None) -> List[Dict]:
        top_k = top_k or config.TOP_K
        embedder = self._get_embedder()
        q_emb = embedder.encode([query]).tolist()

        where = None
        if filter_category:
            where = {"category": filter_category}

        results = indexer.collection.query(
            query_embeddings=q_emb,
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        docs = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                docs.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i],  # cosine distance -> similarity
                })
        return docs

    def search_character(self, character_name: str, top_k: int = 12) -> List[Dict]:
        """Belirli bir karakter için en ilgili lore parçalarını getir."""
        query = f"{character_name} karakter kişilik geçmiş tercih motivasyon ilişki"
        results = self.search(query, top_k=top_k)
        # Karakter dosyasını önceliklendir
        char_file = None
        for f in (config.LORE_DIR / "karakterler").glob("*.md"):
            if character_name.lower() in f.stem.lower():
                char_file = f
                break
        if char_file:
            text = char_file.read_text(encoding="utf-8", errors="ignore")
            results.insert(0, {
                "id": f"charfile::{char_file.name}",
                "text": text,
                "metadata": {"source": str(char_file.relative_to(config.BASE_DIR)), "type": "character_sheet", "filename": char_file.name},
                "score": 1.0,
            })
        return results

    def build_context(self, query: str, character: Optional[str] = None, max_chars: int = 12000) -> str:
        """Soru için en iyi bağlamı oluştur."""
        if character:
            docs = self.search_character(character)
        else:
            docs = self.search(query)

        context_parts = []
        total = 0
        seen = set()
        for d in docs:
            src = d["metadata"].get("source", "")
            if src in seen:
                continue
            seen.add(src)
            part = f"--- Kaynak: {src} ---\n{d['text']}\n"
            if total + len(part) > max_chars:
                break
            context_parts.append(part)
            total += len(part)

        # Knowledge Graph ekle
        if character and character in self.kg.graph:
            rels = self.kg.get_relations(character)
            if rels:
                kg_text = f"\n--- Knowledge Graph ({character}) ---\n"
                for r in rels:
                    if r["direction"] == "out":
                        kg_text += f"{character} --[{r['relation']}]--> {r['target']}\n"
                    else:
                        kg_text += f"{r['source']} --[{r['relation']}]--> {character}\n"
                context_parts.append(kg_text)

        return "\n".join(context_parts)


retriever = Retriever()
