"""
Ana Lore Asistanı - Tüm özellikleri birleştirir
"""
from __future__ import annotations
from typing import Optional, List, Dict, Generator
from pathlib import Path

from modules.llm_client import llm
from modules.retriever import retriever
from modules.indexer import indexer
from prompts.system import (
    SYSTEM_BASE,
    PROMPT_CHARACTER_DEPTH,
    PROMPT_CHOICE,
    PROMPT_EXPAND_LORE,
    PROMPT_CONTINUE_STORY,
    PROMPT_CONSISTENCY,
    PROMPT_GENERAL,
)


class LoreAssistant:
    def __init__(self):
        self.llm = llm
        self.retriever = retriever
        self.indexer = indexer

    def _build_messages(self, system: str, user: str) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def character_depth(self, character: str, stream: bool = False) -> str | Generator:
        context = self.retriever.build_context(f"{character} kişilik geçmiş", character=character)
        user_prompt = PROMPT_CHARACTER_DEPTH.format(character=character, context=context)
        messages = self._build_messages(SYSTEM_BASE, user_prompt)
        return self.llm.chat(messages, stream=stream)

    def suggest_choices(self, character: str, situation: str, stream: bool = False) -> str | Generator:
        context = self.retriever.build_context(f"{character} {situation}", character=character)
        user_prompt = PROMPT_CHOICE.format(character=character, situation=situation, context=context)
        messages = self._build_messages(SYSTEM_BASE, user_prompt)
        return self.llm.chat(messages, stream=stream)

    def expand_lore(self, topic: str, stream: bool = False) -> str | Generator:
        context = self.retriever.build_context(topic)
        user_prompt = PROMPT_EXPAND_LORE.format(topic=topic, context=context)
        messages = self._build_messages(SYSTEM_BASE, user_prompt)
        return self.llm.chat(messages, stream=stream)

    def continue_story(self, instruction: str, focus_characters: Optional[List[str]] = None, stream: bool = False) -> str | Generator:
        # Birden fazla karakter varsa hepsini bağlamda tut
        if focus_characters:
            contexts = []
            for c in focus_characters:
                contexts.append(self.retriever.build_context(instruction, character=c, max_chars=4000))
            context = "\n\n".join(contexts)
        else:
            context = self.retriever.build_context(instruction, max_chars=10000)

        user_prompt = PROMPT_CONTINUE_STORY.format(instruction=instruction, context=context)
        messages = self._build_messages(SYSTEM_BASE, user_prompt)
        return self.llm.chat(messages, stream=stream)

    def check_consistency(self, new_text: str, stream: bool = False) -> str | Generator:
        context = self.retriever.build_context(new_text[:500], max_chars=8000)
        user_prompt = PROMPT_CONSISTENCY.format(new_text=new_text, context=context)
        messages = self._build_messages(SYSTEM_BASE, user_prompt)
        return self.llm.chat(messages, stream=stream)

    def ask(self, query: str, character: Optional[str] = None, stream: bool = False) -> str | Generator:
        context = self.retriever.build_context(query, character=character)
        user_prompt = PROMPT_GENERAL.format(query=query, context=context)
        messages = self._build_messages(SYSTEM_BASE, user_prompt)
        return self.llm.chat(messages, stream=stream)

    def analyze_image(self, image_path: str | Path, extra_prompt: str = "") -> str:
        base_prompt = (
            "Bu görseli kitap lore'u açısından detaylı incele. "
            "Karakter, kıyafet, ifade, ortam, semboller, atmosfer ve hikâyeye dair her şeyi yaz. Türkçe cevap ver."
        )
        if extra_prompt:
            base_prompt += f"\n\nEk istek: {extra_prompt}"
        return self.llm.vision_analyze(image_path, base_prompt)

    def reindex(self, force: bool = False, analyze_images: bool = True) -> Dict:
        return self.indexer.full_reindex(force=force, analyze_images=analyze_images)

    def get_stats(self) -> Dict:
        return self.indexer.get_stats()


assistant = LoreAssistant()
