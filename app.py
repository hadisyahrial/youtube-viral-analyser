import streamlit as st
from googleapiclient.discovery import build
import random
import requests
from bs4 import BeautifulSoup
import re
import time

# --- KONFIGURASI ---
# Untuk development lokal: isi langsung di sini
# Untuk Streamlit Cloud: isi di Settings → Secrets
try:
    API_KEY = st.secrets["AIzaSyCoTQTLR8YCopYzHOV-f9a5mY4y9KXT7GA"]
except Exception:
    API_KEY = "AIzaSyCoTQTLR8YCopYzHOV-f9a5mY4y9KXT7GA"  # fallback lokal

def extract_video_id(url_or_id):
    import re
    try:
        regex = r"(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})"
        match = re.search(regex, url_or_id)
        if match:
            return match.group(1)
    except Exception as e:
        st.error(f"Error saat membaca link: {e}")
    return url_or_id

def analyze_virality(video_id):
    try:
        clean_id = extract_video_id(video_id)
        if not clean_id:
            return None

        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request = youtube.videos().list(part="snippet,statistics", id=clean_id)
        response = request.execute()

        if not response['items']:
            return None

        data = response['items'][0]
        title = data['snippet']['title']
        description = data['snippet'].get('description', '')
        tags = data['snippet'].get('tags', [])
        published_at = data['snippet'].get('publishedAt', 'N/A')
        stats = data.get('statistics', {})
        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))

        engagement_rate = ((likes + comments) / views) * 100 if views > 0 else 0

        if engagement_rate > 5: grade, color = "S-Tier", "green"
        elif engagement_rate > 3: grade, color = "A-Tier", "blue"
        elif engagement_rate > 1: grade, color = "B-Tier", "orange"
        else: grade, color = "C-Tier", "red"

        return {
            "title": title,
            "description": description,
            "views": views,
            "likes": likes,
            "comments": comments,
            "engagement": engagement_rate,
            "grade": grade,
            "color": color,
            "tags": tags,
            "published_at": published_at,
        }
    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
        return None

def generate_analysis(result):
    views = result['views']
    likes = result['likes']
    comments = result['comments']
    tags = result['tags']
    description = result['description']
    title = result['title']

    issues = []
    recommendations = []
    diagnosis_points = []

    if len(title) < 30:
        diagnosis_points.append("⚠️ **Judul terlalu pendek** — kurang deskriptif dan tidak menarik klik.")
        issues.append("Judul terlalu singkat dan kurang menarik")
        recommendations.append("✏️ **Perbaiki Judul:** Gunakan judul 50–70 karakter yang mengandung kata emosional (Rahasia, Tips, Cara Mudah, dll.) dan angka jika relevan.")
    elif len(title) > 70:
        diagnosis_points.append("⚠️ **Judul terlalu panjang** — bisa terpotong di hasil pencarian YouTube.")
        issues.append("Judul terlalu panjang dan bisa terpotong")
        recommendations.append("✏️ **Pangkas Judul:** Pastikan judul di bawah 70 karakter.")
    else:
        diagnosis_points.append("✅ **Panjang judul sudah baik** — berada di rentang ideal 30–70 karakter.")

    if len(tags) == 0:
        diagnosis_points.append("🚫 **Tidak ada tags** — sangat sulit ditemukan melalui pencarian YouTube.")
        issues.append("Tidak menggunakan tags sama sekali")
        recommendations.append("🏷️ **Tambahkan Tags:** Gunakan 10–15 tags relevan.")
    elif len(tags) < 5:
        diagnosis_points.append(f"⚠️ **Tags terlalu sedikit** — hanya {len(tags)} tag.")
        issues.append(f"Tags kurang optimal, hanya {len(tags)} tag")
        recommendations.append("🏷️ **Tambah Tags:** Idealnya gunakan 10–15 tags per video.")
    else:
        diagnosis_points.append(f"✅ **Tags cukup** — menggunakan {len(tags)} tags.")

    if len(description) < 100:
        diagnosis_points.append("⚠️ **Deskripsi terlalu singkat** — mengurangi potensi SEO.")
        issues.append("Deskripsi video terlalu singkat")
        recommendations.append("📝 **Perkaya Deskripsi:** Tulis minimal 200–500 kata dengan kata kunci utama di awal.")
    else:
        diagnosis_points.append("✅ **Deskripsi cukup panjang** — membantu SEO pencarian YouTube.")

    like_ratio = (likes / views * 100) if views > 0 else 0
    if like_ratio < 1:
        diagnosis_points.append(f"📉 **Rasio Like sangat rendah** ({like_ratio:.2f}%)")
        issues.append("Rasio like terhadap views sangat rendah")
        recommendations.append("👍 **Dorong Penonton Like:** Minta penonton like secara eksplisit di awal dan akhir video.")

    comment_ratio = (comments / views * 100) if views > 0 else 0
    if comment_ratio < 0.1:
        diagnosis_points.append(f"💬 **Komentar sangat sepi** ({comment_ratio:.2f}%)")
        issues.append("Komentar sangat sedikit")
        recommendations.append("💬 **Pancing Komentar:** Akhiri video dengan pertanyaan terbuka.")

    if views < 1000:
        diagnosis_points.append("📊 **Views masih sangat rendah** — distribusi konten belum optimal.")
        issues.append("Views sangat rendah")
        recommendations.append("📣 **Distribusi Konten:** Bagikan video ke media sosial segera setelah upload.")
    elif views < 10000:
        diagnosis_points.append("📊 **Views masih di bawah rata-rata.**")
        issues.append("Views masih rendah")
        recommendations.append("🖼️ **Optimalkan Thumbnail:** Gunakan wajah ekspresif, teks besar kontras, warna mencolok.")

    long_term = [
        "📅 **Konsistensi Upload:** Jadwal upload yang konsisten membangun ekspektasi penonton dan disukai algoritma YouTube.",
        "🎯 **Riset Konten Berbasis Data:** Gunakan YouTube Analytics untuk fokus pada topik yang terbukti diminati audiensmu.",
        "🤝 **Kolaborasi & Cross-Promotion:** Kolaborasi dengan kreator lain di niche yang sama untuk bertukar audiens.",
    ]

    return {
        "diagnosis": diagnosis_points,
        "issues": issues,
        "recommendations": recommendations,
        "long_term": long_term,
    }

def extract_topic(title, tags):
    """Ekstrak topik utama dari judul secara lebih cerdas"""

    # Bersihkan emoji, hashtag, dan karakter khusus dari judul
    clean_title = re.sub(r'#\w+', '', title)
    clean_title = re.sub(r'[&/\\|?!]', ' ', clean_title)
    # Hapus emoji
    clean_title = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u0400-\u04FF\s]', '', clean_title).strip()
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()

    # Stopwords diperluas — termasuk kata tanya bahasa Inggris & Indonesia
    stopwords = {
        # Kata tanya & auxiliary verb Inggris
        'did', 'does', 'do', 'is', 'are', 'was', 'were', 'has', 'have', 'had',
        'will', 'would', 'could', 'should', 'may', 'might', 'can',
        'how', 'why', 'what', 'when', 'where', 'which', 'who', 'whom',
        # Artikel & preposisi Inggris
        'the', 'and', 'for', 'with', 'this', 'that', 'from', 'its',
        'your', 'their', 'our', 'his', 'her', 'its', 'not', 'but',
        'about', 'just', 'more', 'also', 'into', 'than', 'then',
        # Kata umum Indonesia
        'yang', 'dan', 'atau', 'dari', 'untuk', 'dengan', 'adalah', 'ini',
        'itu', 'saya', 'kamu', 'anda', 'kita', 'mereka', 'tidak', 'bisa',
        'akan', 'sudah', 'juga', 'apakah', 'kenapa', 'mengapa', 'bagaimana',
        'siapa', 'kapan', 'dimana', 'bahwa', 'karena', 'oleh', 'pada',
    }

    # Hapus kata pertama jika masuk stopword (misal "Did", "Is", "Was" di awal kalimat)
    words_check = clean_title.split()
    if words_check and words_check[0].lower() in stopwords:
        clean_title = ' '.join(words_check[1:]).strip()

    # Prioritas 1: Deteksi nama tokoh/orang (kata berkapital berurutan, bukan di awal kalimat)
    # Nama tokoh biasanya 2+ kata berkapital berurutan
    proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', clean_title)
    if proper_nouns:
        # Ambil nama tokoh terpanjang (kemungkinan nama lengkap)
        topic = max(proper_nouns, key=len)
        # Jika ada lebih dari satu tokoh, gabungkan dua pertama
        if len(proper_nouns) >= 2:
            topic = f"{proper_nouns[0]} & {proper_nouns[1]}"
    else:
        # Prioritas 2: Ambil kata bermakna yang bukan stopword
        words = [w for w in clean_title.split() if len(w) > 2 and w.lower() not in stopwords]
        if len(words) >= 2:
            topic = ' '.join(words[:3])
        elif len(words) == 1:
            topic = words[0]
        elif tags:
            # Fallback ke tags (bersihkan #)
            clean_tags = [t.replace('#', '').strip() for t in tags[:2]]
            topic = ' & '.join(clean_tags)
        else:
            topic = clean_title[:40] if clean_title else "Konten Ini"

    # Tag keyword dari tags jika ada
    tag_keyword = tags[0].replace('#', '') if tags else topic

    return topic, tag_keyword

def generate_titles(title, tags):
    """Generate variasi judul baru berdasarkan judul asli dan tags"""
    topic, tag_keyword = extract_topic(title, tags)

    templates = [
        f"Fakta Menarik tentang {topic} yang Jarang Diketahui Publik",
        f"Inilah Kebenaran di Balik {topic} — Banyak yang Tidak Tahu!",
        f"{random.randint(3,7)} Fakta Mengejutkan tentang {topic}",
        f"Benarkah {topic}? Ini yang Sebenarnya Terjadi",
        f"Mengapa {topic} Jadi Perbincangan Dunia? Ini Faktanya",
        f"Kisah Tersembunyi {topic} yang Akhirnya Terungkap",
        f"Apa yang Sebenarnya Terjadi antara {topic}?",
        f"Semua Orang Salah Paham soal {topic} — Ini Kebenarannya",
        f"{topic}: Fakta vs Rumor yang Perlu Kamu Ketahui",
        f"Sisi Lain {topic} yang Tidak Pernah Diceritakan Media",
    ]
    return random.sample(templates, min(5, len(templates)))

def generate_hooks(title, grade):
    """Generate hook pembuka video berdasarkan judul dan grade"""
    topic, _ = extract_topic(title, [])
    keyword = topic.lower()

    hooks = [
        f"Pernahkah kamu bertanya-tanya kenapa {keyword.lower()} kamu tidak pernah berkembang? Dalam video ini, saya akan ungkap rahasianya.",
        f"Hentikan dulu apa yang sedang kamu lakukan. Karena informasi tentang {keyword.lower()} yang akan saya bagikan ini bisa mengubah segalanya.",
        f"Jika kamu sudah lama berjuang dengan {keyword.lower()} tanpa hasil, kamu berada di tempat yang tepat. Saksikan sampai habis.",
        f"Dalam 60 detik ke depan, kamu akan tahu satu hal tentang {keyword.lower()} yang tidak pernah diajarkan di mana pun.",
        f"Kebanyakan orang melakukan kesalahan besar soal {keyword.lower()}. Dan kemungkinan besar, kamu juga melakukannya.",
        f"Saya hampir menyerah dengan {keyword.lower()} — sampai saya menemukan cara ini. Dan sekarang saya ingin membagikannya ke kamu.",
    ]

    if grade == "C-Tier":
        hooks.insert(0, f"Video ini mungkin belum banyak yang tahu, tapi {keyword.lower()} yang akan kita bahas bisa jadi game changer buatmu.")

    return random.sample(hooks, min(4, len(hooks)))

def generate_narasi(title, tags, grade, engagement):
    """Generate struktur narasi video"""
    keyword, tag_keyword = extract_topic(title, tags)
    keyword = keyword.lower()
    tag_keyword = tag_keyword.lower()

    narasi = f"""
**🎬 Struktur Narasi yang Disarankan untuk: "{title}"**

---

**[0:00 – 0:30] HOOK PEMBUKA**
Buka dengan pernyataan mengejutkan atau pertanyaan yang relevan dengan {keyword.lower()}.
Contoh: *"Tahukah kamu bahwa 90% kreator gagal karena satu kesalahan ini?"*

---

**[0:30 – 1:30] IDENTIFIKASI MASALAH**
Jelaskan masalah yang dihadapi penonton terkait {tag_keyword.lower()}.
Buat penonton merasa "ini persis masalah saya!" — bangun empati dulu sebelum solusi.

---

**[1:30 – 5:00] ISI UTAMA / SOLUSI**
Sampaikan poin utama secara terstruktur. Gunakan format:
- Poin 1: Penjelasan singkat + contoh nyata
- Poin 2: Penjelasan singkat + contoh nyata
- Poin 3: Penjelasan singkat + contoh nyata
Gunakan visual, grafik, atau demo jika memungkinkan.

---

**[5:00 – 5:30] BUKTI / HASIL**
Tampilkan bukti, testimoni, atau hasil nyata yang mendukung klaimmu.
Ini meningkatkan kredibilitas dan mendorong penonton percaya.

---

**[5:30 – 6:00] CALL TO ACTION (CTA)**
Tutup dengan CTA yang jelas:
1. *"Kalau video ini bermanfaat, like dan subscribe ya!"*
2. *"Komen di bawah: apa tantangan terbesarmu soal {keyword.lower()}?"*
3. *"Tonton juga video ini untuk tips lanjutan → [tunjuk end screen]"*

---

> 💡 **Catatan:** Durasi di atas adalah estimasi untuk video 6 menit. Sesuaikan dengan format kontenmu.
"""
    return narasi

def generate_battle_strategy(winner, loser, label_winner, label_loser):
    strategies = []
    tips = []

    gap = winner['engagement'] - loser['engagement']
    tags_winner = set(winner['tags'])
    tags_loser = set(loser['tags'])
    unique_winner_tags = tags_winner - tags_loser
    like_ratio_winner = (winner['likes'] / winner['views'] * 100) if winner['views'] > 0 else 0
    like_ratio_loser = (loser['likes'] / loser['views'] * 100) if loser['views'] > 0 else 0
    comment_ratio_winner = (winner['comments'] / winner['views'] * 100) if winner['views'] > 0 else 0
    comment_ratio_loser = (loser['comments'] / loser['views'] * 100) if loser['views'] > 0 else 0

    strategies.append(f"🏆 **{label_winner}** unggul dengan engagement **{winner['engagement']:.2f}%** vs **{loser['engagement']:.2f}%** — selisih **{gap:.2f}%**.")

    if len(tags_winner) > len(tags_loser):
        strategies.append(f"🏷️ **Strategi Tags:** {label_winner} menggunakan **{len(tags_winner)} tags** vs {label_loser} hanya **{len(tags_loser)} tags**.")
        if unique_winner_tags:
            sample_tags = list(unique_winner_tags)[:5]
            tips.append(f"💡 Tags eksklusif {label_winner} yang bisa ditiru: `{'`, `'.join(sample_tags)}`")
    elif len(tags_loser) > len(tags_winner):
        strategies.append(f"🏷️ **Catatan Tags:** Meski {label_loser} punya lebih banyak tags, engagement tetap lebih rendah — kualitas konten lebih menentukan daripada jumlah tags.")

    if like_ratio_winner > like_ratio_loser:
        strategies.append(f"👍 **Strategi Like:** Rasio like {label_winner} ({like_ratio_winner:.2f}%) lebih tinggi dari {label_loser} ({like_ratio_loser:.2f}%).")
        tips.append(f"💡 Tiru gaya CTA dari {label_winner} — kemungkinan ada ajakan like yang lebih eksplisit atau konten yang lebih emosional.")

    if comment_ratio_winner > comment_ratio_loser:
        strategies.append(f"💬 **Strategi Komentar:** {label_winner} memancing lebih banyak diskusi ({comment_ratio_winner:.2f}% vs {comment_ratio_loser:.2f}%).")
        tips.append(f"💡 Perhatikan bagaimana {label_winner} mengakhiri videonya — kemungkinan ada pertanyaan atau hook yang mendorong penonton berkomentar.")

    if 30 <= len(winner['title']) <= 70 and (len(loser['title']) < 30 or len(loser['title']) > 70):
        strategies.append(f"✏️ **Strategi Judul:** Panjang judul {label_winner} ({len(winner['title'])} karakter) lebih optimal.")
        tips.append(f"💡 Jadikan struktur judul {label_winner} sebagai template untuk video berikutnya.")

    if winner['views'] > loser['views']:
        strategies.append(f"📊 **Distribusi:** {label_winner} meraih **{winner['views']:,} views** vs {label_loser} **{loser['views']:,} views**.")

    return strategies, tips

def scrape_real_issues(topic, tags):
    """Scrape berita dan tren terkait topik video dari berbagai sumber"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    })

    query_encoded = requests.utils.quote(topic.strip())
    results = []
    debug_log = []

    # --- Sumber 1: Wikipedia Search API (paling stabil) ---
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query_encoded}&format=json&srlimit=5&utf8=1"
        resp = session.get(url, timeout=10)
        debug_log.append(f"Wikipedia API: HTTP {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get('query', {}).get('search', [])[:4]:
                snippet = BeautifulSoup(item.get('snippet', ''), 'html.parser').get_text()
                results.append({
                    "judul": item['title'],
                    "deskripsi": snippet[:200],
                    "sumber": "Wikipedia",
                    "tipe": "referensi"
                })
    except Exception as e:
        debug_log.append(f"Wikipedia API: error — {e}")

    # --- Sumber 2: Bing Search ---
    try:
        url = f"https://www.bing.com/search?q={query_encoded}+news&setlang=en&cc=US"
        resp = session.get(url, timeout=10)
        debug_log.append(f"Bing Search: HTTP {resp.status_code}")
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for item in soup.select('li.b_algo')[:5]:
                headline = item.select_one('h2')
                caption = item.select_one('.b_caption p, p')
                if headline:
                    results.append({
                        "judul": headline.get_text(strip=True),
                        "deskripsi": caption.get_text(strip=True)[:200] if caption else "",
                        "sumber": "Bing",
                        "tipe": "web"
                    })
    except Exception as e:
        debug_log.append(f"Bing Search: error — {e}")

    # --- Sumber 3: Bing News RSS ---
    try:
        url = f"https://www.bing.com/news/search?q={query_encoded}&format=rss"
        resp = session.get(url, timeout=10)
        debug_log.append(f"Bing News RSS: HTTP {resp.status_code}")
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'xml')
            for item in soup.find_all('item')[:5]:
                title_tag = item.find('title')
                desc_tag = item.find('description')
                if title_tag:
                    desc_text = BeautifulSoup(desc_tag.get_text(), 'html.parser').get_text()[:200] if desc_tag else ""
                    results.append({
                        "judul": title_tag.get_text(strip=True),
                        "deskripsi": desc_text,
                        "sumber": "Bing News",
                        "tipe": "berita"
                    })
    except Exception as e:
        debug_log.append(f"Bing News RSS: error — {e}")

    # --- Sumber 4: DuckDuckGo HTML ---
    if len(results) < 2:
        try:
            url = f"https://html.duckduckgo.com/html/?q={query_encoded}"
            resp = session.get(url, timeout=10)
            debug_log.append(f"DuckDuckGo: HTTP {resp.status_code}")
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for item in soup.select('.result__title a')[:5]:
                    text = item.get_text(strip=True)
                    if text and len(text) > 10:
                        results.append({
                            "judul": text,
                            "deskripsi": "",
                            "sumber": "DuckDuckGo",
                            "tipe": "web"
                        })
        except Exception as e:
            debug_log.append(f"DuckDuckGo: error — {e}")

    return results[:8], debug_log

def analyze_real_issues(topic, tags, title, results):
    """Analisis isu real berdasarkan hasil scraping dan data video"""

    isu_list = []
    konteks = []
    peluang = []

    # Analisis berdasarkan hasil scraping
    if results:
        konteks.append(f"🌐 Ditemukan **{len(results)} artikel/berita** terkait topik **\"{topic}\"** di web.")

        # Cek apakah topik sedang trending (banyak hasil)
        if len(results) >= 5:
            isu_list.append(f"🔥 **Topik Sedang Ramai** — '{topic}' aktif dibicarakan di media online. Ini peluang besar untuk konten yang relevan.")
            peluang.append("📈 **Manfaatkan Momentum:** Topik ini sedang hangat. Buat video follow-up atau seri konten selagi tren masih berlangsung.")
        elif len(results) >= 2:
            isu_list.append(f"📰 **Topik Cukup Relevan** — ada beberapa pemberitaan terkait '{topic}', namun belum viral secara masif.")
            peluang.append("🎯 **Jadilah yang Pertama:** Topik ini belum jenuh. Ada ruang untuk menjadi referensi utama di niche ini.")
        else:
            isu_list.append(f"🔍 **Topik Kurang Populer** — '{topic}' tidak banyak dibahas di media online saat ini.")
            peluang.append("💡 **Edukasi Pasar:** Topik ini masih jarang dibahas. Kamu bisa menjadi pioneer dan membangun otoritas di niche ini lebih awal.")

        # Analisis judul-judul berita untuk temukan pola isu
        all_text = ' '.join([r['judul'].lower() for r in results])

        # Deteksi sentimen/isu dari kata kunci dalam berita
        isu_keywords = {
            "kontroversi": ["kontrovers", "debat", "perdebatan", "dikritik", "protes", "controversy", "scandal"],
            "prestasi": ["berhasil", "sukses", "menang", "juara", "raih", "achieve", "award", "won"],
            "viral": ["viral", "trending", "ramai", "heboh", "buzz", "popular"],
            "negatif": ["gagal", "mundur", "turun", "masalah", "krisis", "failed", "problem"],
            "positif": ["naik", "meningkat", "berkembang", "maju", "growth", "rise"],
        }

        detected = []
        for kategori, keywords in isu_keywords.items():
            if any(kw in all_text for kw in keywords):
                detected.append(kategori)

        if "kontroversi" in detected:
            isu_list.append("⚡ **Isu Kontroversi Terdeteksi** — topik ini memiliki elemen perdebatan yang bisa memicu diskusi panas di kolom komentar.")
            peluang.append("🎭 **Angkat Dua Sisi:** Buat konten yang membahas pro dan kontra secara objektif — ini mendorong lebih banyak komentar dan share.")
        if "viral" in detected:
            isu_list.append("🚀 **Topik Sedang Viral** — konten terkait topik ini berpotensi mendapat dorongan algoritma YouTube secara organik.")
            peluang.append("⚡ **Upload Segera:** Topik viral punya window waktu sempit. Segera upload konten selagi tren masih panas.")
        if "prestasi" in detected:
            isu_list.append("🏆 **Ada Elemen Prestasi/Pencapaian** — penonton cenderung tertarik pada kisah sukses dan pencapaian.")
            peluang.append("🌟 **Angle Inspiratif:** Bingkai konten dari sudut pandang inspirasi dan motivasi untuk memperluas jangkauan audiens.")
        if "negatif" in detected:
            isu_list.append("⚠️ **Sentimen Negatif Terdeteksi** — ada pemberitaan negatif terkait topik ini yang perlu diwaspadai.")
            peluang.append("🛡️ **Jadilah Penyeimbang:** Buat konten berimbang yang meluruskan informasi — audiens menghargai kreator yang objektif.")

    else:
        isu_list.append("🔎 **Data web tidak ditemukan** — topik ini mungkin sangat niche atau pencarian terbatas.")
        konteks.append("Tidak ada hasil scraping yang berhasil. Coba periksa koneksi internet atau topik video terlalu spesifik.")
        peluang.append("💡 **Niche Content:** Topik yang sangat spesifik bisa berarti kompetisi rendah. Bangun audiens loyal di niche ini.")

    # Analisis tambahan dari judul video itu sendiri
    title_lower = title.lower()
    if any(w in title_lower for w in ['shorts', 'short', '#shorts']):
        isu_list.append("📱 **Format Shorts** — video ini adalah Shorts. Algoritma Shorts berbeda dari video biasa, engagement dihitung dari watch time bukan like/komentar.")
        peluang.append("🔄 **Repurpose Konten:** Buat versi panjang (5–10 menit) dari topik yang sama untuk menjangkau audiens yang berbeda.")

    if any(w in title_lower for w in ['royal', 'kerajaan', 'princess', 'prince', 'king', 'queen']):
        isu_list.append("👑 **Konten Kerajaan/Selebriti** — topik ini memiliki fanbase loyal namun juga kompetisi konten yang sangat tinggi di YouTube global.")
        peluang.append("🌍 **Targetkan Bahasa Spesifik:** Buat konten dalam bahasa Indonesia untuk audiens lokal yang belum banyak dilayani kreator lain.")

    return {
        "isu": isu_list,
        "konteks": konteks,
        "peluang": peluang,
        "berita": results
    }

def show_disclaimer():
    with st.expander("ℹ️ Tentang Insight & Analisis di Aplikasi Ini", expanded=False):
        st.markdown("""
        #### 📌 Sumber Insight Aplikasi Ini
        Insight dan rekomendasi yang ditampilkan **bukan berasal langsung dari algoritma resmi YouTube**, karena algoritma YouTube bersifat **rahasia dan tidak dipublikasikan**.

        | Sumber | Keterangan |
        |---|---|
        | ✅ **Data nyata YouTube** | Views, likes, komentar diambil via YouTube Data API v3 |
        | ✅ **Rumus Engagement Rate** | `(likes + comments) / views × 100` — standar industri |
        | ⚠️ **Best practice komunitas** | Panduan judul, tags, deskripsi bersumber dari kreator & tools seperti vidIQ dan TubeBuddy |
        | ⚠️ **Benchmark umum** | Threshold grade dibuat berdasarkan rata-rata industri, bukan aturan resmi YouTube |

        > Gunakan insight ini sebagai **panduan umum**, bukan jaminan hasil.
        """)


# --- TAMPILAN DASHBOARD ---
st.set_page_config(page_title="YouTube Viral Analyser Pro", page_icon="🚀", layout="wide")

st.title("🚀 YouTube Viral Analyser Pro")
st.markdown("Bongkar rahasia algoritma YouTube. **Cukup paste link video Anda!**")

show_disclaimer()

mode = st.sidebar.selectbox("Pilih Mode Analisis", ["Single Analysis", "Video Battle ⚔️"])

st.sidebar.divider()
if st.sidebar.button("🔄 Reset / Clear Halaman", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if mode == "Single Analysis":
    st.subheader("🔍 Analisis Video Tunggal")
    video_input = st.text_input("Paste Link YouTube atau ID Video", placeholder="https://www.youtube.com/watch?v=...")

    if st.button("Analisis Sekarang"):
        if video_input:
            with st.spinner('Menganalisis...'):
                result = analyze_virality(video_input)
                if result:
                    st.success("Analisis Selesai!")

                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.header(f"🎬 {result['title']}")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Views", f"{result['views']:,}")
                        m2.metric("Likes", f"{result['likes']:,}")
                        m3.metric("Comments", f"{result['comments']:,}")
                        st.markdown(f"### Grade: :{result['color']}[{result['grade']}] | Engagement: {result['engagement']:.2f}%")

                        # Tanggal publish
                        if result['published_at'] != 'N/A':
                            from datetime import datetime, timezone
                            try:
                                pub_dt = datetime.strptime(result['published_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                                now = datetime.now(timezone.utc)
                                delta = now - pub_dt
                                days = delta.days
                                if days == 0:
                                    umur = "Hari ini"
                                elif days < 7:
                                    umur = f"{days} hari yang lalu"
                                elif days < 30:
                                    umur = f"{days // 7} minggu yang lalu"
                                elif days < 365:
                                    umur = f"{days // 30} bulan yang lalu"
                                else:
                                    umur = f"{days // 365} tahun yang lalu"
                                pub_str = pub_dt.strftime("%d %B %Y, %H:%M UTC")
                                st.caption(f"📅 **Dipublish:** {pub_str} &nbsp;|&nbsp; ⏱️ {umur}")
                            except Exception:
                                st.caption(f"📅 **Dipublish:** {result['published_at']}")
                    with col2:
                        st.subheader("🏷️ Tags")
                        if result['tags']:
                            for tag in result['tags']: st.markdown(f"🔹 `{tag}`")
                        else: st.info("Tidak ada tags.")

                    st.divider()

                    # --- ANALISIS MENDALAM ---
                    st.subheader("🧠 Analisis Mendalam — Diagnosis & Rekomendasi")
                    analysis = generate_analysis(result)

                    st.markdown("### 🔍 Diagnosis Masalah")
                    for point in analysis['diagnosis']:
                        st.markdown(f"- {point}")

                    st.markdown("### ⚠️ Isu Utama yang Ditemukan")
                    for i, issue in enumerate(analysis['issues'], 1):
                        st.markdown(f"**{i}.** {issue}")

                    st.markdown("### 🚀 Rekomendasi Perbaikan")
                    for rec in analysis['recommendations']:
                        st.info(rec)

                    st.markdown("### 💡 Strategi Jangka Panjang")
                    for tip in analysis['long_term']:
                        st.success(tip)

                    st.divider()

                    # --- GENERATOR KONTEN ---
                    st.subheader("✍️ Generator Konten — Judul, Hook & Narasi")
                    st.caption("Hasil generator bersifat template — sesuaikan dengan gaya dan niche kontenmu.")

                    tab1, tab2, tab3 = st.tabs(["📝 Generator Judul", "🎣 Generator Hook", "🎬 Generator Narasi"])

                    with tab1:
                        st.markdown("#### 📝 5 Variasi Judul yang Lebih Menarik")
                        st.markdown(f"Berdasarkan judul asli: *\"{result['title']}\"*")
                        titles = generate_titles(result['title'], result['tags'])
                        for i, t in enumerate(titles, 1):
                            st.markdown(f"**{i}.** {t}")
                            st.code(t, language=None)

                    with tab2:
                        st.markdown("#### 🎣 4 Variasi Hook Pembuka Video")
                        st.markdown("Hook adalah 30 detik pertama yang menentukan apakah penonton lanjut menonton atau tidak.")
                        hooks = generate_hooks(result['title'], result['grade'])
                        for i, h in enumerate(hooks, 1):
                            st.markdown(f"**Hook {i}:**")
                            st.info(h)

                    with tab3:
                        st.markdown("#### 🎬 Struktur Narasi Video yang Disarankan")
                        narasi = generate_narasi(result['title'], result['tags'], result['grade'], result['engagement'])
                        st.markdown(narasi)

                    st.divider()

                    # --- ANALISIS ISU REAL ---
                    st.subheader("🌐 Analisis Isu Real — Apa yang Sedang Terjadi?")
                    st.caption("Mencari konteks berita dan tren terkait topik video dari web...")

                    topic, _ = extract_topic(result['title'], result['tags'])

                    with st.spinner(f'Mencari isu terkait "{topic}" di web...'):
                        raw_results, debug_log = scrape_real_issues(topic, result['tags'])
                        time.sleep(1)
                        isu_data = analyze_real_issues(topic, result['tags'], result['title'], raw_results)

                    # Debug status scraping (bisa diexpand)
                    with st.expander("🔧 Status Scraping (klik untuk lihat detail)", expanded=False):
                        if debug_log:
                            for log in debug_log:
                                icon = "✅" if "200" in log else "❌"
                                st.caption(f"{icon} {log}")
                        else:
                            st.caption("Tidak ada log tersedia.")

                    # Konteks
                    if isu_data['konteks']:
                        for k in isu_data['konteks']:
                            st.markdown(k)

                    # Isu yang ditemukan
                    st.markdown("#### 🔎 Isu & Kondisi Terkini")
                    if isu_data['isu']:
                        for isu in isu_data['isu']:
                            st.warning(isu)
                    else:
                        st.info("Tidak ada isu spesifik yang terdeteksi untuk topik ini.")

                    # Peluang konten
                    st.markdown("#### 🚀 Peluang Konten Berdasarkan Isu")
                    if isu_data['peluang']:
                        for p in isu_data['peluang']:
                            st.success(p)

                    # Berita/artikel terkait
                    if isu_data['berita']:
                        st.markdown("#### 📰 Artikel & Berita Terkait yang Ditemukan")
                        for i, berita in enumerate(isu_data['berita'], 1):
                            deskripsi = f" — {berita['deskripsi'][:120]}..." if berita.get('deskripsi') else ""
                            st.markdown(f"**{i}.** {berita['judul']} *(via {berita['sumber']})*{deskripsi}")

                    st.caption("⚠️ Hasil scraping bersifat dinamis dan bergantung pada koneksi internet serta ketersediaan sumber web.")

                else: st.error("Video tidak ditemukan. Pastikan link/ID benar.")
        else: st.warning("Masukkan link atau ID video!")

elif mode == "Video Battle ⚔️":
    st.subheader("⚔️ Video Battle: Siapa yang Lebih Viral?")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        input_a = st.text_input("Link/ID Video A", placeholder="https://youtube.com/...")
    with col_input2:
        input_b = st.text_input("Link/ID Video B", placeholder="https://youtube.com/...")

    if st.button("Saring Pemenang! 🏆"):
        if input_a and input_b:
            with st.spinner('Menghitung skor pertarungan...'):
                res_a = analyze_virality(input_a)
                res_b = analyze_virality(input_b)
                if res_a and res_b:
                    st.success("Battle Selesai!")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"### 🎥 Video A")
                        st.write(f"**{res_a['title']}**")
                        st.metric("Engagement Rate", f"{res_a['engagement']:.2f}%")
                        st.write(f"Views: {res_a['views']:,} | Likes: {res_a['likes']:,} | Komentar: {res_a['comments']:,}")
                        st.markdown(f"Grade: :{res_a['color']}[{res_a['grade']}]")
                    with col_b:
                        st.markdown(f"### 🎥 Video B")
                        st.write(f"**{res_b['title']}**")
                        st.metric("Engagement Rate", f"{res_b['engagement']:.2f}%")
                        st.write(f"Views: {res_b['views']:,} | Likes: {res_b['likes']:,} | Komentar: {res_b['comments']:,}")
                        st.markdown(f"Grade: :{res_b['color']}[{res_b['grade']}]")

                    st.divider()

                    if res_a['engagement'] > res_b['engagement']:
                        st.balloons()
                        st.markdown("## 🏆 PEMENANG: VIDEO A")
                        winner, loser, label_w, label_l = res_a, res_b, "Video A", "Video B"
                    elif res_b['engagement'] > res_a['engagement']:
                        st.balloons()
                        st.markdown("## 🏆 PEMENANG: VIDEO B")
                        winner, loser, label_w, label_l = res_b, res_a, "Video B", "Video A"
                    else:
                        st.markdown("## 🤝 HASIL SERI!")
                        winner, loser, label_w, label_l = res_a, res_b, "Video A", "Video B"

                    st.divider()

                    st.subheader("📊 Insight Strategi — Apa yang Bisa Dipelajari?")
                    strategies, tips = generate_battle_strategy(winner, loser, label_w, label_l)

                    st.markdown("#### 🔎 Analisis Perbandingan")
                    for s in strategies:
                        st.markdown(f"- {s}")

                    if tips:
                        st.markdown("#### 💡 Tips yang Bisa Langsung Ditiru")
                        for tip in tips:
                            st.info(tip)

                    st.divider()

                    st.subheader("🕵️ Tag Gap Analysis")
                    tags_a, tags_b = set(res_a['tags']), set(res_b['tags'])
                    diff_b = tags_b - tags_a
                    diff_a = tags_a - tags_b
                    if diff_b:
                        st.write("Tags eksklusif **Video B** (tidak ada di Video A):")
                        for tag in diff_b: st.markdown(f"✨ `{tag}`")
                    if diff_a:
                        st.write("Tags eksklusif **Video A** (tidak ada di Video B):")
                        for tag in diff_a: st.markdown(f"✨ `{tag}`")
                    if not diff_a and not diff_b:
                        st.info("Kedua video menggunakan tags yang sama.")

                else: st.error("Salah satu atau kedua video tidak ditemukan.")
        else: st.warning("Masukkan kedua link video!")

st.markdown("---")
st.caption("YouTube Viral Analyser Pro v5.0 | Free Edition — Insight berbasis best practice industri, bukan algoritma resmi YouTube.")
