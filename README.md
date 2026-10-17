# O — Lore Asistanı

Yazarın dünyasını tutan, karakterlere derinlik katan, hikâyeyi devam ettiren lore asistanı.

Hem bilgisayar hem telefon tarayıcısından çalışır (Streamlit Cloud).

---

## Özellikler

- Yerel (Ollama) + API (OpenAI / xAI Grok / Custom)
- Görselleri vision ile analiz
- Karakter derinliği & olası tercihler
- Lore genişletme
- Hikâyeyi mevcut lore’a sadık devam ettirme
- Knowledge Graph + RAG
- Türkçe öncelikli

---

## 1. Yerel Çalıştırma (Bilgisayar)

```bash
# Windows
baslat.bat

# Linux / Mac
chmod +x baslat.sh
./baslat.sh
```

---

## 2. İnternette Yayınlama (Streamlit Cloud) — PC + Telefon

### Adım 1: GitHub’a yükle

1. https://github.com/new adresine git
2. Repository name: `O` (veya `lore-asistani`)
3. Public seç
4. “Create repository” tıkla
5. Bu klasördeki **tüm dosyaları** o repoya yükle (Upload files veya Git ile)

### Adım 2: Streamlit Cloud’a bağla

1. https://share.streamlit.io adresine git
2. GitHub hesabınla giriş yap (KuriBocchi)
3. “New app” tıkla
4. Repository olarak az önce oluşturduğun `O` reposunu seç
5. Main file path: `app.py`
6. Deploy!

Birkaç dakika sonra sana özel bir link verecek.  
Örnek: `https://o-xxxx.streamlit.app`

Bu linki hem bilgisayarında hem telefonunda açabilirsin.

### Adım 3: API Key’leri güvenli ekle (önerilir)

Streamlit Cloud → senin app’in → Settings → Secrets

Şunu yapıştır (istediğin key’leri doldur):

```toml
OPENAI_API_KEY = "sk-..."
GROK_API_KEY = "xai-..."
OPENAI_BASE_URL = "https://api.openai.com/v1"
```

Kaydet. Artık sidebar’dan key girmene gerek kalmaz.

---

## Önemli Notlar (Cloud)

- Streamlit Cloud’da dosya sistemi geçicidir. Lore ve görselleri her seferinde yüklemen veya yedeklemen gerekebilir.
- Ücretsiz planda bellek sınırı vardır. Çok büyük indeksler veya ağır modeller yavaşlayabilir.
- En stabil kullanım için API (Grok / OpenAI) tercih et.

---

## Klasör Yapısı

```
O/
├── app.py
├── config.py
├── requirements.txt
├── lore/
│   ├── karakterler/
│   ├── dunya/
│   ├── sistemler/
│   ├── olaylar/
│   └── notlar/
├── gorseller/
└── modules/
```

---

O, senin dünyanı unutmaz.
