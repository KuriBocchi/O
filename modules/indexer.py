"""
Lore Indexer - Metin + Görsel indeksleme
ChromaDB + multilingual embedding + görsel açıklama
"""
from __future__ import annotations
import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from PIL import Image
import numpy as np

import config
from modules.llm_client import llm


class LoreIndexer:
    def __init__(self):
        self.chroma = chromadb.PersistentClient(
            path=config.CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma.get_or_create_collection(
            name=config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedder = None  # Lazy load
        self._meta_path = config.INDEX_DIR / "index_meta.json"
        self.meta = self._load_meta()

    def _load_meta(self) -> Dict:
        if self._meta_path.exists():
            return json.loads(self._meta_path.read_text(encoding="utf-8"))
        return {"files": {}, "last_full_index": None}

    def _save_meta(self):
        config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
        self._meta_path.write_text(json.dumps(self.meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def _get_embedder(self):
        if self.embedder is None:
            self.embedder = SentenceTransformer(config.TEXT_EMBEDDING_MODEL)
        return self.embedder

    def _file_hash(self, path: Path) -> str:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _chunk_text(self, text: str, source: str) -> List[Dict[str, Any]]:
        chunks = []
        words = text.split()
        chunk_size = config.CHUNK_SIZE
        overlap = config.CHUNK_OVERLAP

        # Basit ama etkili karakter bazlı chunking (Türkçe için uygun)
        start = 0
        text_len = len(text)
        idx = 0
        while start < text_len:
            end = min(start + chunk_size, text_len)
            # Cümle sonunda kesmeye çalış
            if end < text_len:
                for sep in [". ", "! ", "? ", "\n\n", "\n"]:
                    pos = text.rfind(sep, start, end)
                    if pos > start + chunk_size // 2:
                        end = pos + len(sep)
                        break
            chunk = text[start:end].strip()
            if chunk:
                chunks.append({
                    "id": f"{source}::chunk_{idx}",
                    "text": chunk,
                    "source": source,
                    "type": "text",
                    "chunk_idx": idx,
                })
                idx += 1
            start = end - overlap if end < text_len else text_len
        return chunks

    def index_text_file(self, path: Path, force: bool = False) -> int:
        """Tek bir metin dosyasını indeksle. Değişmediyse atla."""
        rel = str(path.relative_to(config.BASE_DIR))
        current_hash = self._file_hash(path)

        if not force and rel in self.meta["files"] and self.meta["files"][rel].get("hash") == current_hash:
            return 0  # Değişmemiş

        text = path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            return 0

        # Eski chunk'ları sil
        existing = self.collection.get(where={"source": rel})
        if existing and existing["ids"]:
            self.collection.delete(ids=existing["ids"])

        chunks = self._chunk_text(text, rel)
        if not chunks:
            return 0

        embedder = self._get_embedder()
        texts = [c["text"] for c in chunks]
        embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

        self.collection.add(
            ids=[c["id"] for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[{
                "source": c["source"],
                "type": "text",
                "chunk_idx": c["chunk_idx"],
                "filename": path.name,
                "category": path.parent.name,
            } for c in chunks],
        )

        self.meta["files"][rel] = {
            "hash": current_hash,
            "chunks": len(chunks),
            "type": "text",
            "updated": datetime.now().isoformat(),
        }
        self._save_meta()
        return len(chunks)

    def index_image(self, path: Path, force: bool = False, analyze: bool = True) -> int:
        """Görseli indeksle. Vision ile açıklama üret + metin olarak sakla."""
        rel = str(path.relative_to(config.BASE_DIR))
        current_hash = self._file_hash(path)

        if not force and rel in self.meta["files"] and self.meta["files"][rel].get("hash") == current_hash:
            return 0

        description = ""
        if analyze:
            prompt = (
                "Bu görseli kitap lore'u açısından çok detaylı incele. "
                "Karakter varsa: görünüş, kıyafet, ifade, duruş, silah/aksesuar. "
                "Ortam varsa: mekan, atmosfer, ışık, mimari, semboller. "
                "Hikâyeye dair her ipucunu yaz. Türkçe cevap ver."
            )
            description = llm.vision_analyze(path, prompt)

        # Açıklamayı da dosya olarak kaydet (kalıcı olsun)
        desc_path = path.with_suffix(path.suffix + ".desc.txt")
        desc_path.write_text(description or "Açıklama üretilemedi.", encoding="utf-8")

        full_text = f"[GÖRSEL: {path.name}]\n\n{description}"

        # Eski kayıtları sil
        existing = self.collection.get(where={"source": rel})
        if existing and existing["ids"]:
            self.collection.delete(ids=existing["ids"])

        chunks = self._chunk_text(full_text, rel)
        if not chunks:
            chunks = [{
                "id": f"{rel}::img",
                "text": full_text,
                "source": rel,
                "type": "image",
                "chunk_idx": 0,
            }]

        embedder = self._get_embedder()
        texts = [c["text"] for c in chunks]
        embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

        self.collection.add(
            ids=[c["id"] for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[{
                "source": c["source"],
                "type": "image",
                "chunk_idx": c["chunk_idx"],
                "filename": path.name,
                "category": "gorseller",
            } for c in chunks],
        )

        self.meta["files"][rel] = {
            "hash": current_hash,
            "chunks": len(chunks),
            "type": "image",
            "description": description[:500],
            "updated": datetime.now().isoformat(),
        }
        self._save_meta()
        return len(chunks)

    def full_reindex(self, force: bool = False, analyze_images: bool = True) -> Dict[str, int]:
        """Tüm lore + görselleri tara ve indeksle."""
        stats = {"text_files": 0, "text_chunks": 0, "images": 0, "image_chunks": 0}

        # Metin dosyaları
        for sub in config.LORE_SUBDIRS:
            folder = config.LORE_DIR / sub
            folder.mkdir(parents=True, exist_ok=True)
            for ext in ("*.md", "*.txt", "*.markdown"):
                for path in folder.rglob(ext):
                    n = self.index_text_file(path, force=force)
                    if n > 0:
                        stats["text_files"] += 1
                        stats["text_chunks"] += n

        # Görseller
        config.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.gif"):
            for path in config.IMAGES_DIR.rglob(ext):
                n = self.index_image(path, force=force, analyze=analyze_images)
                if n > 0:
                    stats["images"] += 1
                    stats["image_chunks"] += n

        self.meta["last_full_index"] = datetime.now().isoformat()
        self._save_meta()
        return stats

    def get_stats(self) -> Dict[str, Any]:
        count = self.collection.count()
        return {
            "total_chunks": count,
            "indexed_files": len(self.meta.get("files", {})),
            "last_index": self.meta.get("last_full_index"),
            "files": self.meta.get("files", {}),
        }


# Singleton
indexer = LoreIndexer()
