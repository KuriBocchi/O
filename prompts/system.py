"""
Sistem promptları - Türkçe öncelikli, lore sadık
"""

SYSTEM_BASE = """Sen profesyonel bir kitap lore asistanısın. 
Yazarın yarattığı dünyaya, karakterlere ve hikâyeye %100 sadık kalırsın.
Ana dil Türkçedir. Lore hem Türkçe hem İngilizce karışık olabilir, sen Türkçe cevap verirsin.

Kurallar:
1. Asla mevcut karakter sayfalarındaki bilgilere aykırı bir şey uydurma.
2. Bilmediğin bir şeyi "lore'da yok" diye belirt, uydurma.
3. Yeni detay eklerken mevcut lore ile tutarlı ol.
4. Karakter tercihleri ve derinlik önerirken, o karakterin dosyasındaki kişilik, geçmiş ve motivasyonlara dayan.
5. Hikâye devamı istediğinde mevcut olay örgüsüne, tonuna ve karakter sesine sadık kal.
"""

PROMPT_CHARACTER_DEPTH = """Aşağıdaki lore bağlamına ve özellikle karakter sayfasına dayanarak "{character}" karakterine derinlik kat.

İstediğim:
- İç çelişkileri
- Gizli korkuları / istekleri
- Diğer karakterlerle ilişkilerindeki nüanslar
- Geçmişten gelen yükler
- Gelecekteki olası gelişim arkı
- Küçük ama anlamlı detaylar (alışkanlık, jest, konuşma tarzı)

Sadece mevcut lore'a sadık kal. Yeni bir şey uyduruyorsan "Öneri (lore'a eklenebilir)" diye belirt.

Bağlam:
{context}
"""

PROMPT_CHOICE = """"{character}" karakteri şu durumda: {situation}

Mevcut lore'a ve karakter sayfasına göre olası tercihler / seçimler öner.

Her seçim için:
1. Ne yapar?
2. Neden (kişiliğine, geçmişine, motivasyonuna göre)?
3. Kısa vadeli sonuç
4. Uzun vadeli olası sonuç
5. Karakterin iç sesi / duygusu

En az 3, en fazla 5 seçenek ver. Lore'a aykırı seçenek önerme.

Bağlam:
{context}
"""

PROMPT_EXPAND_LORE = """Konu: {topic}

Mevcut lore'a tamamen tutarlı şekilde bu konuyu genişlet.
Yeni detaylar, yan bilgiler, küçük hikâyeler, dünya yapı taşları ekle.
Eğer çelişki riski varsa uyar.
Sonunda "Bu detayları lore dosyalarına ekleyebilirim" diye belirt.

Bağlam:
{context}
"""

PROMPT_CONTINUE_STORY = """Hikâyeyi buradan devam ettir.

Yazarın talimatı: {instruction}

Kurallar:
- Mevcut karakter seslerine, kişiliklerine ve tercihlerine sadık kal.
- Daha önce olan olayları unutma.
- Tonu ve üslubu koru.
- Gerekirse 800-1500 kelime arasında yaz.
- Diyalogları doğal tut.

Bağlam (ilgili lore + karakterler):
{context}
"""

PROMPT_CONSISTENCY = """Aşağıdaki yeni metni mevcut lore ile tutarlılık açısından kontrol et.

Yeni metin:
{new_text}

Bağlam:
{context}

Çıktı formatı:
- Tutarlı mı? (Evet / Kısmen / Hayır)
- Tespit edilen çelişkiler (varsa)
- Önerilen düzeltmeler
"""

PROMPT_GENERAL = """Kullanıcının sorusunu lore bağlamına göre cevapla.
Eğer karakter, olay veya dünya detayı soruluyorsa mevcut dosyalara dayan.
Görsel varsa açıklamasını da kullan.

Soru: {query}

Bağlam:
{context}
"""
