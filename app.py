"""
O — Lore Asistanı
Yazarın dünyasını tutan, karakterlere derinlik katan, hikâyeyi devam ettiren asistan.
"""
import streamlit as st
from pathlib import Path
import time
from datetime import datetime

import config
from modules.assistant import assistant
from modules.llm_client import llm
from modules.indexer import indexer

# ─────────────────────────────────────────────
# Sayfa ayarları
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="O — Lore Asistanı",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Özel CSS - O Teması (koyu, minimal, havalı)
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    .stApp {
        background: linear-gradient(160deg, #0a0a0f 0%, #12121a 45%, #0d1117 100%);
        color: #e6e6e6;
    }

    /* Başlıklar */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: #f0f0f0 !important;
        letter-spacing: -0.02em;
    }

    h1 {
        font-size: 2.6rem !important;
        background: linear-gradient(90deg, #ffffff, #a0a0a0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .stMarkdown, .stText, p, li, .stCaption {
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        line-height: 1.7;
        color: #d0d0d0;
    }

    /* Butonlar */
    .stButton > button {
        background: #1c1c24;
        color: #f5f5f5;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 0.55rem 1.3rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: #2a2a35;
        border-color: #666;
        transform: translateY(-1px);
    }

    /* Input alanları */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background-color: #14141c !important;
        color: #eaeaea !important;
        border: 1px solid #2a2a35 !important;
        border-radius: 10px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0c0c12;
        border-right: 1px solid #1f1f2a;
    }
    [data-testid="stSidebar"] * {
        color: #c8c8c8 !important;
    }

    /* Kartlar */
    .lore-card {
        background: #14141c;
        border: 1px solid #252530;
        border-radius: 14px;
        padding: 1.6rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.35);
    }

    .stat-box {
        background: #14141c;
        border-left: 3px solid #888;
        padding: 0.9rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 0.6rem 0;
        font-size: 0.95rem;
    }

    /* Sohbet balonları */
    .chat-message {
        padding: 1.1rem 1.3rem;
        border-radius: 14px;
        margin: 0.9rem 0;
        line-height: 1.75;
    }
    .user-msg {
        background: #1a1a24;
        border: 1px solid #2e2e3a;
    }
    .assistant-msg {
        background: #12121a;
        border: 1px solid #252530;
    }

    /* Logo / O işareti */
    .o-logo {
        font-family: 'Playfair Display', serif;
        font-size: 3.2rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
    }
    .o-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #888;
        margin-bottom: 1.8rem;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0a0a0f; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }

    /* Tab stilleri */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: #14141c;
        border-radius: 10px;
        color: #aaa;
        border: 1px solid #252530;
    }
    .stTabs [aria-selected="true"] {
        background: #1c1c28 !important;
        color: #fff !important;
        border-color: #444 !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode" not in st.session_state:
    st.session_state.mode = "local"
if "api_configured" not in st.session_state:
    st.session_state.api_configured = False


# ─────────────────────────────────────────────
# Sidebar - Ayarlar & Araçlar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="o-logo">O</div>', unsafe_allow_html=True)
    st.markdown('<div class="o-subtitle">Lore Asistanı</div>', unsafe_allow_html=True)
    st.markdown("---")

    # LLM Modu
    st.markdown("### ⚙️ Model Ayarları")
    mode = st.radio(
        "Çalışma Modu",
        ["Yerel (Ollama)", "API", "Otomatik"],
        index=0 if st.session_state.mode == "local" else (1 if st.session_state.mode == "api" else 2),
        help="Yerel: Ollama | API: OpenAI / xAI / Custom | Otomatik: Önce yerel dener"
    )
    mode_map = {"Yerel (Ollama)": "local", "API": "api", "Otomatik": "auto"}
    st.session_state.mode = mode_map[mode]
    llm.set_mode(st.session_state.mode)

    # Yerel modeller
    if st.session_state.mode in ("local", "auto"):
        local_models = llm.list_local_models()
        if local_models:
            selected_local = st.selectbox("Yerel Model", local_models, index=0)
            llm.local_model = selected_local
        else:
            st.warning("Ollama bulunamadı veya model yok. `ollama serve` çalışıyor mu?")

    # API Ayarları
    if st.session_state.mode in ("api", "auto"):
        st.markdown("#### API Yapılandırması")
        provider = st.selectbox("Sağlayıcı", ["OpenAI", "xAI (Grok)", "Custom"])
        api_key = st.text_input("API Key", type="password", value="")
        base_url = ""
        if provider == "Custom":
            base_url = st.text_input("Base URL", value="https://api.openai.com/v1")
        model_name = st.text_input("Model Adı", value="gpt-4o" if provider != "xAI (Grok)" else "grok-2")

        if st.button("API'yi Kaydet"):
            if provider == "OpenAI":
                llm.set_api_provider("openai", api_key)
            elif provider == "xAI (Grok)":
                llm.set_api_provider("xai", api_key)
            else:
                llm.set_api_provider("custom", api_key, base_url)
            llm.api_model = model_name
            st.session_state.api_configured = True
            st.success("API kaydedildi!")

    st.markdown("---")

    # İndeksleme
    st.markdown("### 📚 Lore Yönetimi")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 İndeksle", use_container_width=True):
            with st.spinner("Lore taranıyor ve indeksleniyor..."):
                stats = assistant.reindex(force=False, analyze_images=True)
                st.success(f"Tamamlandı!\nMetin: {stats['text_files']} dosya ({stats['text_chunks']} parça)\nGörsel: {stats['images']} adet")
    with col2:
        if st.button("♻️ Zorla Yenile", use_container_width=True):
            with st.spinner("Tüm lore yeniden indeksleniyor (görseller de analiz ediliyor)..."):
                stats = assistant.reindex(force=True, analyze_images=True)
                st.success(f"Tamamlandı!\nMetin: {stats['text_files']} | Görsel: {stats['images']}")

    # İstatistikler
    stats = assistant.get_stats()
    st.markdown(f"""
    <div class="stat-box">
        <b>Toplam Parça:</b> {stats.get('total_chunks', 0)}<br>
        <b>Dosya:</b> {stats.get('indexed_files', 0)}<br>
        <b>Son İndeks:</b> {stats.get('last_index', 'Henüz yok')[:19] if stats.get('last_index') else 'Henüz yok'}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📁 Klasörler")
    st.code(f"lore/     → Metin lore\ngorseller/ → Görseller", language=None)
    st.caption("Dosyaları bu klasörlere at, sonra İndeksle butonuna bas.")


# ─────────────────────────────────────────────
# Ana İçerik
# ─────────────────────────────────────────────
st.markdown('<div class="o-logo">O</div>', unsafe_allow_html=True)
st.markdown('<div class="o-subtitle">Karakterlerine derinlik kat · Lore’unu genişlet · Hikâyeni devam ettir</div>', unsafe_allow_html=True)

# Sekmeler
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💬 Sohbet",
    "🧠 Karakter Derinliği",
    "⚖️ Seçim Öner",
    "🌌 Lore Genişlet",
    "📖 Hikâye Devam",
    "🖼️ Görsel Analiz"
])

# ─── 1. Sohbet ───
with tab1:
    st.markdown("### Serbest Sohbet")
    st.caption("Lore hakkında istediğini sor. Karakter, olay, dünya detayı...")

    for msg in st.session_state.messages:
        css_class = "user-msg" if msg["role"] == "user" else "assistant-msg"
        with st.container():
            st.markdown(f'<div class="chat-message {css_class}"><b>{"Sen" if msg["role"]=="user" else "Asistan"}:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

    query = st.chat_input("Lore hakkında sor...")
    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.spinner("Düşünüyor..."):
            response = assistant.ask(query)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# ─── 2. Karakter Derinliği ───
with tab2:
    st.markdown("### Karakterine Derinlik Kat")
    char_name = st.text_input("Karakter Adı", key="depth_char", placeholder="Örn: Elara, Kael, Ayşe...")
    if st.button("Derinlik Analizi Yap", key="btn_depth"):
        if char_name.strip():
            with st.spinner(f"{char_name} inceleniyor..."):
                result = assistant.character_depth(char_name.strip())
            st.markdown(f'<div class="lore-card">{result}</div>', unsafe_allow_html=True)
        else:
            st.warning("Karakter adı gir.")

# ─── 3. Seçim Öner ───
with tab3:
    st.markdown("### Karakter Tercih / Seçim Önerisi")
    col_a, col_b = st.columns(2)
    with col_a:
        char2 = st.text_input("Karakter", key="choice_char", placeholder="Karakter adı")
    with col_b:
        situation = st.text_area("Durum / Çatışma", key="choice_sit", placeholder="Örn: Eski düşmanıyla karşı karşıya, yardım mı etmeli yoksa intikam mı almalı?", height=100)

    if st.button("Seçimleri Öner", key="btn_choice"):
        if char2.strip() and situation.strip():
            with st.spinner("Olası tercihler hesaplanıyor..."):
                result = assistant.suggest_choices(char2.strip(), situation.strip())
            st.markdown(f'<div class="lore-card">{result}</div>', unsafe_allow_html=True)
        else:
            st.warning("Karakter ve durum gerekli.")

# ─── 4. Lore Genişlet ───
with tab4:
    st.markdown("### Lore Genişletme")
    topic = st.text_input("Konu / Başlık", key="expand_topic", placeholder="Örn: Kuzey dağlarındaki unutulmuş tapınak, Büyü sisteminin kökeni...")
    if st.button("Lore'u Genişlet", key="btn_expand"):
        if topic.strip():
            with st.spinner("Tutarlı detaylar üretiliyor..."):
                result = assistant.expand_lore(topic.strip())
            st.markdown(f'<div class="lore-card">{result}</div>', unsafe_allow_html=True)
            st.info("Beğendiğin kısımları kopyalayıp ilgili .md dosyasına ekleyebilirsin.")
        else:
            st.warning("Bir konu gir.")

# ─── 5. Hikâye Devam ───
with tab5:
    st.markdown("### Hikâyeyi Devam Ettir")
    instruction = st.text_area(
        "Ne olmasını istiyorsun? / Nereden devam etsin?",
        key="story_inst",
        height=120,
        placeholder="Örn: Elara ormanın derinliklerinde eski bir harabe bulur. İçeride bir şeyler kıpırdanıyor..."
    )
    focus_chars = st.text_input("Odak Karakterler (virgülle ayır, opsiyonel)", key="story_chars", placeholder="Elara, Kael")
    if st.button("Hikâyeyi Yaz", key="btn_story"):
        if instruction.strip():
            chars = [c.strip() for c in focus_chars.split(",") if c.strip()] if focus_chars else None
            with st.spinner("Hikâye örülüyor..."):
                result = assistant.continue_story(instruction.strip(), focus_characters=chars)
            st.markdown(f'<div class="lore-card">{result}</div>', unsafe_allow_html=True)
        else:
            st.warning("Talimat gir.")

# ─── 6. Görsel Analiz ───
with tab6:
    st.markdown("### Görsel Analiz & Lore'a Ekleme")
    uploaded = st.file_uploader("Görsel yükle (png, jpg, webp)", type=["png", "jpg", "jpeg", "webp"])
    extra = st.text_input("Ek talimat (opsiyonel)", placeholder="Bu karakterin silahını detaylı anlat...")

    if uploaded and st.button("Görseli Analiz Et", key="btn_vision"):
        # Kaydet
        save_path = config.IMAGES_DIR / uploaded.name
        config.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())

        with st.spinner("Görsel inceleniyor (vision modeli)..."):
            desc = assistant.analyze_image(save_path, extra_prompt=extra)
            # İndekse de ekle
            indexer.index_image(save_path, force=True, analyze=False)  # zaten analiz ettik

        st.image(uploaded, caption=uploaded.name, use_container_width=True)
        st.markdown(f'<div class="lore-card"><b>Analiz Sonucu:</b><br><br>{desc}</div>', unsafe_allow_html=True)
        st.success(f"Görsel kaydedildi ve indekslendi: gorseller/{uploaded.name}")


# Footer
st.markdown("---")
st.caption("O · Yerel + API · Multimodal · Knowledge Graph")
