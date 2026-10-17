#!/bin/bash
# O — Lore Asistanı başlatıcı (Linux / macOS)

cd "$(dirname "$0")"

# Sanal ortam yoksa oluştur
if [ ! -d "venv" ]; then
    echo "İlk kurulum yapılıyor..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo ""
echo "  O  —  Lore Asistanı başlatılıyor..."
echo "  Tarayıcıda açılacak: http://localhost:8501"
echo ""

streamlit run app.py --server.headless true
