"""
LLM Client - Hem yerel (Ollama) hem API (OpenAI uyumlu / xAI) destekler.
Vision modellerini de yönetir.
"""
from __future__ import annotations
import os
import base64
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path
import httpx
from openai import OpenAI
import config


class LLMClient:
    def __init__(self):
        self.mode = "local"  # "local" | "api" | "auto"
        self.api_provider = "openai"  # "openai" | "xai" | "custom"
        self.local_model = config.DEFAULT_LOCAL_MODEL
        self.api_model = config.DEFAULT_API_MODEL
        self.vision_local = config.VISION_MODEL_LOCAL
        self.vision_api = config.VISION_MODEL_API
        self.temperature = 0.7
        self.max_tokens = 4096

        self._openai_client: Optional[OpenAI] = None
        self._xai_client: Optional[OpenAI] = None

    def set_mode(self, mode: str):
        if mode in ("local", "api", "auto"):
            self.mode = mode

    def set_api_provider(self, provider: str, api_key: str = "", base_url: str = ""):
        self.api_provider = provider
        if provider == "openai":
            key = api_key or config.OPENAI_API_KEY
            url = base_url or config.OPENAI_BASE_URL
            if key:
                self._openai_client = OpenAI(api_key=key, base_url=url)
        elif provider == "xai":
            key = api_key or config.GROK_API_KEY
            if key:
                self._xai_client = OpenAI(api_key=key, base_url=config.GROK_BASE_URL)
        elif provider == "custom":
            if api_key and base_url:
                self._openai_client = OpenAI(api_key=api_key, base_url=base_url)

    def _get_api_client(self) -> Optional[OpenAI]:
        if self.api_provider == "xai":
            return self._xai_client
        return self._openai_client

    def is_local_available(self) -> bool:
        try:
            r = httpx.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    def list_local_models(self) -> List[str]:
        try:
            r = httpx.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        force_mode: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> str | Generator[str, None, None]:
        mode = force_mode or self.mode

        if mode == "auto":
            mode = "local" if self.is_local_available() else "api"

        if mode == "local":
            return self._chat_ollama(messages, stream, model_override or self.local_model)
        else:
            return self._chat_api(messages, stream, model_override or self.api_model)

    def _chat_ollama(
        self, messages: List[Dict[str, str]], stream: bool, model: str
    ) -> str | Generator[str, None, None]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        url = f"{config.OLLAMA_BASE_URL}/api/chat"

        if stream:
            def gen():
                with httpx.stream("POST", url, json=payload, timeout=120.0) as r:
                    for line in r.iter_lines():
                        if line:
                            import json
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except Exception:
                                continue
            return gen()
        else:
            r = httpx.post(url, json=payload, timeout=120.0)
            r.raise_for_status()
            return r.json()["message"]["content"]

    def _chat_api(
        self, messages: List[Dict[str, str]], stream: bool, model: str
    ) -> str | Generator[str, None, None]:
        client = self._get_api_client()
        if not client:
            raise RuntimeError("API client yapılandırılmamış. API Key girin.")

        if stream:
            def gen():
                stream_resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=True,
                )
                for chunk in stream_resp:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return gen()
        else:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return resp.choices[0].message.content or ""

    def vision_analyze(
        self,
        image_path: str | Path,
        prompt: str = "Bu görseli detaylı şekilde betimle. Karakter, ortam, atmosfer, renkler, semboller ve hikâyeye dair her detayı yaz.",
        force_mode: Optional[str] = None,
    ) -> str:
        """Görseli vision modeli ile analiz eder."""
        path = Path(image_path)
        if not path.exists():
            return "Görsel bulunamadı."

        mode = force_mode or self.mode
        if mode == "auto":
            mode = "local" if self.is_local_available() else "api"

        # Base64 encode
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        mime = "image/jpeg"
        if path.suffix.lower() in (".png",):
            mime = "image/png"
        elif path.suffix.lower() in (".webp",):
            mime = "image/webp"

        if mode == "local":
            # Ollama vision (llava vb.)
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [b64],
                }
            ]
            # Ollama vision formatı biraz farklı, özel endpoint kullanıyoruz
            payload = {
                "model": self.vision_local,
                "prompt": prompt,
                "images": [b64],
                "stream": False,
            }
            try:
                r = httpx.post(
                    f"{config.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                    timeout=180.0,
                )
                r.raise_for_status()
                return r.json().get("response", "Analiz başarısız.")
            except Exception as e:
                return f"Yerel vision hatası: {e}. API kullanmayı deneyin."
        else:
            # API vision (OpenAI / xAI uyumlu)
            client = self._get_api_client()
            if not client:
                return "API client yok."
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ]
            try:
                resp = client.chat.completions.create(
                    model=self.vision_api,
                    messages=messages,
                    max_tokens=1500,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:
                return f"API vision hatası: {e}"


# Singleton
llm = LLMClient()
