"""
O — Lore Asistanı - Konfigürasyon
Cloud (Streamlit) + yerel uyumlu
"""
import os
from pathlib import Path

# Proje kök dizini
BASE_DIR = Path(__file__).parent.resolve()

# Klasörler
LORE_DIR = BASE_DIR / "lore"
IMAGES_DIR = BASE_DIR / "gorseller"
INDEX_DIR = BASE_DIR / "index"
PROMPTS_DIR = BASE_DIR / "prompts"

# Alt lore klasörleri
LORE_SUBDIRS = ["karakterler", "dunya", "sistemler", "olaylar", "notlar"]

# Vektör veritabanı
CHROMA_PATH = str(INDEX_DIR / "chroma")
COLLECTION_NAME = "kitap_lore"

# Embedding modelleri (cloud'da daha hafif model tercih edilebilir)
TEXT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
IMAGE_EMBEDDING_MODEL = "openai/clip-vit-base-patch32"

# LLM Ayarları
DEFAULT_LOCAL_MODEL = "llama3.1:8b"
DEFAULT_API_MODEL = "gpt-4o"
VISION_MODEL_LOCAL = "llava:13b"
VISION_MODEL_API = "gpt-4o"

# API Key'ler - önce environment, sonra Streamlit secrets dener
def _get_secret(key: str, default: str = "") -> str:
    # 1. Environment
    val = os.getenv(key, "")
    if val:
        return val
    # 2. Streamlit secrets (cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
OPENAI_BASE_URL = _get_secret("OPENAI_BASE_URL", "https://api.openai.com/v1")
GROK_API_KEY = _get_secret("GROK_API_KEY")
GROK_BASE_URL = "https://api.x.ai/v1"

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Retrieval
TOP_K = 8
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# Dil
PRIMARY_LANGUAGE = "tr"
