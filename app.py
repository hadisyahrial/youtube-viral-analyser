import streamlit as st
from googleapiclient.discovery import build
import random
import requests
from bs4 import BeautifulSoup
import re
import time
import bcrypt

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

# --- AUTENTIKASI SEDERHANA ---
def check_password(username, password):
    try:
        # Format secrets: USER_admin = "password123"
        key = f"USER_{username}"
        stored_password = st.secrets[key]
        return password == stored_password
    except Exception:
        # Fallback lokal
        if username == "admin" and password == "password123":
            return True
    return False

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.title("🔐 Login — YouTube Viral Analyser Pro")
    st.markdown("Masukkan username dan password untuk melanjutkan.")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if check_password(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Username atau password salah!")
    st.stop()
# --- KONTEN UTAMA (setelah login) ---
# Tombol logout di sidebar
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()
st.sidebar.markdown(f"👤 Login sebagai: **{st.session_state.username}**")
st.sidebar.divider()

st.title("🚀 YouTube Viral Analyser Pro")
st.markdown("Bongkar rahasia algoritma YouTube. **Cukup paste link video Anda!**")

show_disclaimer()

mode = st.sidebar.selectbox("Pilih Mode Analisis", ["Single Analysis", "Video Battle ⚔️", "Competitor Tracker 🕵️", "Monetization Estimator 💰"])

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

elif mode == "Competitor Tracker 🕵️":
    st.subheader("🕵️ Competitor Tracker — Bandingkan Channel")
    st.markdown("Masukkan 2–3 link channel YouTube untuk dibandingkan strateginya.")

    def extract_channel_id(url_or_id):
        """Ekstrak channel ID dari berbagai format URL YouTube"""
        import re
        if not url_or_id:
            return None, None
        # Format @handle
        handle_match = re.search(r'youtube\.com\/@([\w.-]+)', url_or_id)
        if handle_match:
            return None, handle_match.group(1)
        # Format /channel/UC...
        channel_match = re.search(r'youtube\.com\/channel\/(UC[\w-]+)', url_or_id)
        if channel_match:
            return channel_match.group(1), None
        # Format /c/name atau /user/name
        custom_match = re.search(r'youtube\.com\/(?:c\/|user\/)([\w-]+)', url_or_id)
        if custom_match:
            return None, custom_match.group(1)
        # Jika langsung channel ID
        if url_or_id.startswith('UC') and len(url_or_id) > 20:
            return url_or_id, None
        return None, url_or_id

    def analyze_channel(url_or_id):
        """Ambil data channel dan 10 video terakhir dari YouTube API"""
        try:
            youtube = build('youtube', 'v3', developerKey=API_KEY)
            channel_id, handle = extract_channel_id(url_or_id)

            # Cari channel berdasarkan handle jika tidak ada ID
            if not channel_id and handle:
                search_resp = youtube.search().list(
                    part="snippet", q=handle, type="channel", maxResults=1
                ).execute()
                if search_resp['items']:
                    channel_id = search_resp['items'][0]['snippet']['channelId']

            if not channel_id:
                return None

            # Ambil info channel
            ch_resp = youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            ).execute()

            if not ch_resp['items']:
                return None

            ch = ch_resp['items'][0]
            name = ch['snippet']['title']
            description = ch['snippet'].get('description', '')[:200]
            subscribers = int(ch['statistics'].get('subscriberCount', 0))
            total_views = int(ch['statistics'].get('viewCount', 0))
            total_videos = int(ch['statistics'].get('videoCount', 0))
            playlist_id = ch['contentDetails']['relatedPlaylists']['uploads']

            # Ambil 10 video terakhir
            pl_resp = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=10
            ).execute()

            video_ids = [item['contentDetails']['videoId'] for item in pl_resp['items']]

            # Ambil statistik video
            vids_resp = youtube.videos().list(
                part="snippet,statistics",
                id=','.join(video_ids)
            ).execute()

            videos = []
            total_engagement = 0
            all_tags = []
            upload_days = []

            for v in vids_resp['items']:
                stats = v.get('statistics', {})
                snippet = v['snippet']
                views = int(stats.get('viewCount', 0))
                likes = int(stats.get('likeCount', 0))
                comments = int(stats.get('commentCount', 0))
                engagement = ((likes + comments) / views * 100) if views > 0 else 0
                total_engagement += engagement

                pub_date = snippet.get('publishedAt', '')
                if pub_date:
                    from datetime import datetime, timezone
                    dt = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ")
                    upload_days.append(dt.strftime("%A"))

                tags = snippet.get('tags', [])
                all_tags.extend(tags[:5])

                videos.append({
                    "title": snippet['title'],
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "engagement": engagement,
                    "published": pub_date[:10] if pub_date else "N/A",
                    "tags": tags
                })

            avg_engagement = total_engagement / len(videos) if videos else 0
            avg_views = sum(v['views'] for v in videos) / len(videos) if videos else 0

            # Hitung frekuensi upload per hari
            from collections import Counter
            day_freq = Counter(upload_days)
            most_active_day = day_freq.most_common(1)[0][0] if day_freq else "N/A"

            # Top tags
            tag_freq = Counter(all_tags)
            top_tags = [t[0] for t in tag_freq.most_common(8)]

            # Video terbaik
            top_video = max(videos, key=lambda x: x['engagement']) if videos else None

            return {
                "name": name,
                "description": description,
                "subscribers": subscribers,
                "total_views": total_views,
                "total_videos": total_videos,
                "avg_engagement": avg_engagement,
                "avg_views": avg_views,
                "most_active_day": most_active_day,
                "top_tags": top_tags,
                "top_video": top_video,
                "recent_videos": videos,
                "upload_days": upload_days,
            }
        except Exception as e:
            st.error(f"Error menganalisis channel: {e}")
            return None

    # --- INPUT CHANNEL ---
    col1, col2, col3 = st.columns(3)
    with col1:
        ch_input_a = st.text_input("🔴 Channel A", placeholder="https://youtube.com/@channel")
    with col2:
        ch_input_b = st.text_input("🔵 Channel B", placeholder="https://youtube.com/@channel")
    with col3:
        ch_input_c = st.text_input("🟢 Channel C (opsional)", placeholder="https://youtube.com/@channel")

    if st.button("🔍 Analisis Competitor", use_container_width=True):
        inputs = [i for i in [ch_input_a, ch_input_b, ch_input_c] if i.strip()]
        labels = ["🔴 Channel A", "🔵 Channel B", "🟢 Channel C"]
        colors = ["red", "blue", "green"]

        if len(inputs) < 2:
            st.warning("Masukkan minimal 2 channel untuk dibandingkan!")
        else:
            channels = []
            for i, inp in enumerate(inputs):
                with st.spinner(f"Menganalisis {labels[i]}..."):
                    data = analyze_channel(inp)
                    if data:
                        data['label'] = labels[i]
                        data['color'] = colors[i]
                        channels.append(data)
                    else:
                        st.error(f"{labels[i]}: Channel tidak ditemukan.")

            if len(channels) >= 2:
                st.success(f"✅ Berhasil menganalisis {len(channels)} channel!")
                st.divider()

                # --- OVERVIEW METRICS ---
                st.subheader("📊 Overview Channel")
                cols = st.columns(len(channels))
                for i, ch in enumerate(channels):
                    with cols[i]:
                        st.markdown(f"### {ch['label']}")
                        st.markdown(f"**{ch['name']}**")
                        st.metric("Subscribers", f"{ch['subscribers']:,}")
                        st.metric("Total Views", f"{ch['total_views']:,}")
                        st.metric("Total Video", f"{ch['total_videos']:,}")
                        st.metric("Avg Engagement (10 vid)", f"{ch['avg_engagement']:.2f}%")
                        st.metric("Avg Views (10 vid)", f"{int(ch['avg_views']):,}")

                st.divider()

                # --- PEMENANG PER KATEGORI ---
                st.subheader("🏆 Siapa yang Unggul?")
                categories = {
                    "👥 Subscribers": ("subscribers", lambda x: f"{x:,}"),
                    "👁️ Avg Views": ("avg_views", lambda x: f"{int(x):,}"),
                    "💬 Avg Engagement": ("avg_engagement", lambda x: f"{x:.2f}%"),
                    "🎬 Total Video": ("total_videos", lambda x: f"{x:,}"),
                }
                cat_cols = st.columns(len(categories))
                for i, (cat_name, (key, fmt)) in enumerate(categories.items()):
                    with cat_cols[i]:
                        winner = max(channels, key=lambda x: x[key])
                        st.markdown(f"**{cat_name}**")
                        st.success(f"🏆 {winner['name']}\n\n{fmt(winner[key])}")

                st.divider()

                # --- FREKUENSI UPLOAD ---
                st.subheader("📅 Pola Upload")
                up_cols = st.columns(len(channels))
                for i, ch in enumerate(channels):
                    with up_cols[i]:
                        st.markdown(f"**{ch['label']} — {ch['name']}**")
                        st.markdown(f"📌 Hari paling aktif: **{ch['most_active_day']}**")
                        from collections import Counter
                        day_counts = Counter(ch['upload_days'])
                        for day, count in day_counts.most_common():
                            st.caption(f"{day}: {count}x upload")

                st.divider()

                # --- TOP TAGS ---
                st.subheader("🏷️ Tags yang Paling Sering Dipakai")
                tag_cols = st.columns(len(channels))
                for i, ch in enumerate(channels):
                    with tag_cols[i]:
                        st.markdown(f"**{ch['label']} — {ch['name']}**")
                        if ch['top_tags']:
                            for tag in ch['top_tags']:
                                st.markdown(f"🔹 `{tag}`")
                        else:
                            st.info("Tidak ada tags ditemukan.")

                st.divider()

                # --- VIDEO TERBAIK ---
                st.subheader("🎬 Video Terbaik (Engagement Tertinggi)")
                vid_cols = st.columns(len(channels))
                for i, ch in enumerate(channels):
                    with vid_cols[i]:
                        st.markdown(f"**{ch['label']} — {ch['name']}**")
                        if ch['top_video']:
                            tv = ch['top_video']
                            st.markdown(f"📹 *{tv['title']}*")
                            st.markdown(f"👁️ {tv['views']:,} views | 👍 {tv['likes']:,} | 💬 {tv['comments']:,}")
                            st.markdown(f"🔥 Engagement: **{tv['engagement']:.2f}%**")
                            st.caption(f"Upload: {tv['published']}")

                st.divider()

                # --- INSIGHT STRATEGI ---
                st.subheader("💡 Insight Strategi")
                top_eng = max(channels, key=lambda x: x['avg_engagement'])
                top_sub = max(channels, key=lambda x: x['subscribers'])
                top_views = max(channels, key=lambda x: x['avg_views'])

                def generate_content_style_insight(ch):
                    """Analisis gaya konten & CTA dari data video nyata channel"""
                    videos = ch['recent_videos']
                    if not videos:
                        return None

                    # Analisis pola judul
                    titles = [v['title'] for v in videos]
                    avg_title_len = sum(len(t) for t in titles) / len(titles)
                    has_question = sum(1 for t in titles if '?' in t)
                    has_number = sum(1 for t in titles if any(c.isdigit() for c in t))
                    has_caps = sum(1 for t in titles if sum(1 for c in t if c.isupper()) > 3)
                    has_exclaim = sum(1 for t in titles if '!' in t)

                    # Analisis CTA dari rasio komentar
                    avg_comment_ratio = sum(
                        (v['comments'] / v['views'] * 100) if v['views'] > 0 else 0
                        for v in videos
                    ) / len(videos)

                    avg_like_ratio = sum(
                        (v['likes'] / v['views'] * 100) if v['views'] > 0 else 0
                        for v in videos
                    ) / len(videos)

                    # Top performing video pattern
                    top_v = max(videos, key=lambda x: x['engagement'])

                    style_notes = []
                    cta_notes = []

                    # Gaya judul
                    if has_question >= len(titles) * 0.3:
                        style_notes.append(f"❓ **Sering pakai judul pertanyaan** ({has_question} dari {len(titles)} video) — memancing rasa ingin tahu penonton.")
                    if has_number >= len(titles) * 0.3:
                        style_notes.append(f"🔢 **Sering pakai angka di judul** ({has_number} dari {len(titles)} video) — memberi kesan konkret dan terstruktur.")
                    if has_caps >= len(titles) * 0.3:
                        style_notes.append(f"🔠 **Sering pakai huruf kapital** ({has_caps} dari {len(titles)} video) — menciptakan urgensi dan emosi.")
                    if has_exclaim >= len(titles) * 0.3:
                        style_notes.append(f"❗ **Sering pakai tanda seru** ({has_exclaim} dari {len(titles)} video) — menambah energi dan excitement.")
                    if avg_title_len < 40:
                        style_notes.append(f"✂️ **Judul pendek & padat** (rata-rata {avg_title_len:.0f} karakter) — langsung ke poin, mudah dibaca di mobile.")
                    elif avg_title_len > 60:
                        style_notes.append(f"📝 **Judul deskriptif panjang** (rata-rata {avg_title_len:.0f} karakter) — detail dan kaya kata kunci SEO.")
                    else:
                        style_notes.append(f"⚖️ **Judul seimbang** (rata-rata {avg_title_len:.0f} karakter) — optimal untuk SEO dan keterbacaan.")

                    # Pola CTA dari data
                    if avg_comment_ratio > 0.5:
                        cta_notes.append(f"💬 **CTA komentar sangat kuat** (avg {avg_comment_ratio:.2f}%) — kemungkinan sering melempar pertanyaan di akhir video atau meminta pendapat penonton.")
                    elif avg_comment_ratio > 0.1:
                        cta_notes.append(f"💬 **CTA komentar cukup aktif** (avg {avg_comment_ratio:.2f}%) — ada dorongan interaksi namun bisa ditingkatkan.")
                    else:
                        cta_notes.append(f"💬 **CTA komentar lemah** (avg {avg_comment_ratio:.2f}%) — jarang memancing diskusi di kolom komentar.")

                    if avg_like_ratio > 3:
                        cta_notes.append(f"👍 **CTA like sangat efektif** (avg {avg_like_ratio:.2f}%) — kemungkinan secara eksplisit meminta like di awal atau akhir video.")
                    elif avg_like_ratio > 1:
                        cta_notes.append(f"👍 **CTA like cukup baik** (avg {avg_like_ratio:.2f}%) — penonton cukup terdorong untuk like.")
                    else:
                        cta_notes.append(f"👍 **CTA like perlu ditingkatkan** (avg {avg_like_ratio:.2f}%) — penonton kurang terdorong untuk like.")

                    # Video terbaik sebagai contoh nyata
                    return {
                        "style_notes": style_notes,
                        "cta_notes": cta_notes,
                        "top_video": top_v,
                        "avg_comment_ratio": avg_comment_ratio,
                        "avg_like_ratio": avg_like_ratio,
                    }

                # Insight engagement terbaik
                eng_insight = generate_content_style_insight(top_eng)
                with st.expander(f"🏆 Channel Engagement Terbaik: {top_eng['name']} ({top_eng['avg_engagement']:.2f}%) — klik untuk detail gaya konten & CTA", expanded=False):
                    if eng_insight:
                        st.markdown("##### 🎨 Gaya Konten")
                        for note in eng_insight['style_notes']:
                            st.markdown(f"- {note}")
                        st.markdown("##### 📣 Pola CTA (Call-to-Action)")
                        for note in eng_insight['cta_notes']:
                            st.markdown(f"- {note}")
                        st.markdown("##### 🎬 Contoh Video Terbaik Mereka")
                        tv = eng_insight['top_video']
                        st.info(f"**{tv['title']}**\n\n👁️ {tv['views']:,} views | 👍 {tv['likes']:,} | 💬 {tv['comments']:,} | 🔥 Engagement: {tv['engagement']:.2f}%")
                        st.caption("💡 Pelajari judul, thumbnail, dan bagaimana video ini diawali — ini adalah formula terbaik channel tersebut.")

                # Insight subscriber terbanyak
                sub_insight = generate_content_style_insight(top_sub)
                with st.expander(f"👥 Channel Subscriber Terbanyak: {top_sub['name']} ({top_sub['subscribers']:,}) — klik untuk detail topik & pola konten", expanded=False):
                    if sub_insight:
                        from collections import Counter
                        # Analisis topik dari judul video
                        all_words = []
                        for v in top_sub['recent_videos']:
                            words = [w.lower() for w in v['title'].split() if len(w) > 4]
                            all_words.extend(words)
                        common_words = Counter(all_words).most_common(8)

                        st.markdown("##### 🔑 Kata Kunci yang Sering Muncul di Judul")
                        if common_words:
                            kw_str = " | ".join([f"`{w}`" for w, _ in common_words])
                            st.markdown(kw_str)
                        st.markdown("##### 🎨 Gaya Konten")
                        for note in sub_insight['style_notes']:
                            st.markdown(f"- {note}")
                        st.markdown("##### 🎬 Video Terbaik Mereka")
                        tv = sub_insight['top_video']
                        st.info(f"**{tv['title']}**\n\n👁️ {tv['views']:,} views | 👍 {tv['likes']:,} | 💬 {tv['comments']:,} | 🔥 Engagement: {tv['engagement']:.2f}%")

                # Insight views tertinggi
                views_insight = generate_content_style_insight(top_views)
                with st.expander(f"👁️ Channel Avg Views Tertinggi: {top_views['name']} ({int(top_views['avg_views']):,}) — klik untuk strategi judul & thumbnail", expanded=False):
                    if views_insight:
                        st.markdown("##### 🎨 Pola Judul (Kunci CTR Tinggi)")
                        for note in views_insight['style_notes']:
                            st.markdown(f"- {note}")
                        st.markdown("##### 📋 Contoh Judul Video Terbaru Mereka")
                        for v in top_views['recent_videos'][:5]:
                            st.markdown(f"- *{v['title']}* — **{v['views']:,} views**")
                        st.markdown("##### 💡 Tips Thumbnail")
                        avg_views_val = top_views['avg_views']
                        if avg_views_val > 100000:
                            st.success("Channel ini punya CTR sangat tinggi. Kemungkinan menggunakan thumbnail dengan wajah ekspresif, warna kontras tinggi, dan teks maksimal 3 kata. Tiru formula visual mereka!")
                        elif avg_views_val > 10000:
                            st.success("Channel ini punya distribusi yang baik. Fokus pada konsistensi visual branding — warna, font, dan layout thumbnail yang seragam membangun recognition.")
                        else:
                            st.info("Views masih berkembang. Eksperimen dengan berbagai gaya thumbnail dan pantau CTR di YouTube Analytics.")

                # Gap analisis tags
                if len(channels) >= 2:
                    st.divider()
                    st.markdown("#### 🕵️ Tag Gap — Tags Eksklusif per Channel")
                    for i, ch in enumerate(channels):
                        other_tags = set()
                        for j, other in enumerate(channels):
                            if i != j:
                                other_tags.update(set(other['top_tags']))
                        unique = set(ch['top_tags']) - other_tags
                        if unique:
                            st.markdown(f"**{ch['label']} — {ch['name']}** punya tags eksklusif:")
                            for t in unique:
                                st.markdown(f"✨ `{t}`")

    st.markdown("---")
    st.caption("YouTube Viral Analyser Pro v5.2 | Free Edition — Insight berbasis best practice industri, bukan algoritma resmi YouTube.")

elif mode == "Monetization Estimator 💰":
    st.subheader("💰 Monetization Estimator")
    st.markdown("Estimasi potensi penghasilan channel YouTube berdasarkan data video dan benchmark industri.")

    with st.expander("⚠️ Disclaimer Penting — Baca Sebelum Menggunakan", expanded=True):
        st.warning("""
        Angka yang ditampilkan adalah **ESTIMASI KASAR** berbasis benchmark industri umum — bukan penghasilan aktual.
        RPM (Revenue Per Mille) nyata sangat bervariasi tergantung negara audiens, musim iklan, niche spesifik, dan kebijakan AdSense masing-masing creator.
        Gunakan hasil ini sebagai **gambaran umum**, bukan proyeksi keuangan yang pasti.
        Tools seperti Social Blade pun menggunakan pendekatan estimasi yang sama.
        """)

    # --- INPUT ---
    channel_input = st.text_input("Paste Link Channel YouTube", placeholder="https://www.youtube.com/@channelname")

    niche_options = {
        "💼 Finance & Bisnis": {"rpm_min": 8, "rpm_max": 15, "sponsorship_mult": 3.0},
        "💻 Teknologi": {"rpm_min": 5, "rpm_max": 10, "sponsorship_mult": 2.5},
        "🎓 Edukasi": {"rpm_min": 4, "rpm_max": 9, "sponsorship_mult": 2.0},
        "🏥 Kesehatan & Lifestyle": {"rpm_min": 3, "rpm_max": 7, "sponsorship_mult": 2.0},
        "🎮 Gaming": {"rpm_min": 2, "rpm_max": 5, "sponsorship_mult": 1.5},
        "🎬 Entertainment & Vlog": {"rpm_min": 1, "rpm_max": 4, "sponsorship_mult": 1.5},
        "🍳 Food & Cooking": {"rpm_min": 2, "rpm_max": 5, "sponsorship_mult": 1.8},
        "✈️ Travel": {"rpm_min": 3, "rpm_max": 7, "sponsorship_mult": 2.0},
        "👗 Fashion & Beauty": {"rpm_min": 2, "rpm_max": 6, "sponsorship_mult": 2.2},
        "⚽ Sport": {"rpm_min": 2, "rpm_max": 5, "sponsorship_mult": 1.8},
    }

    # Mapping YouTube categoryId ke niche
    category_to_niche = {
        "1":  "🎬 Entertainment & Vlog",   # Film & Animation
        "2":  "⚽ Sport",                   # Autos & Vehicles
        "10": "🎬 Entertainment & Vlog",   # Music
        "15": "🐾 Entertainment & Vlog",   # Pets & Animals
        "17": "⚽ Sport",                   # Sports
        "19": "✈️ Travel",                  # Travel & Events
        "20": "🎮 Gaming",                  # Gaming
        "22": "🎬 Entertainment & Vlog",   # People & Blogs
        "23": "🎬 Entertainment & Vlog",   # Comedy
        "24": "🎬 Entertainment & Vlog",   # Entertainment
        "25": "💼 Finance & Bisnis",        # News & Politics
        "26": "🏥 Kesehatan & Lifestyle",   # Howto & Style
        "27": "🎬 Entertainment & Vlog",   # Education (general)
        "28": "💻 Teknologi",               # Science & Technology
        "29": "🎬 Entertainment & Vlog",   # Nonprofits & Activism
    }

    if st.button("💰 Hitung Estimasi Monetisasi", use_container_width=True):
        if channel_input:
            with st.spinner("Mengambil data channel & mendeteksi niche..."):

                def extract_channel_id_simple(url_or_id):
                    handle_match = re.search(r'youtube\.com\/@([\w.-]+)', url_or_id)
                    if handle_match:
                        return None, handle_match.group(1)
                    channel_match = re.search(r'youtube\.com\/channel\/(UC[\w-]+)', url_or_id)
                    if channel_match:
                        return channel_match.group(1), None
                    if url_or_id.startswith('UC'):
                        return url_or_id, None
                    return None, url_or_id

                def get_channel_monetization_data(url_or_id):
                    try:
                        youtube = build('youtube', 'v3', developerKey=API_KEY)
                        channel_id, handle = extract_channel_id_simple(url_or_id)

                        if not channel_id and handle:
                            search_resp = youtube.search().list(
                                part="snippet", q=handle, type="channel", maxResults=1
                            ).execute()
                            if search_resp['items']:
                                channel_id = search_resp['items'][0]['snippet']['channelId']

                        if not channel_id:
                            return None

                        ch_resp = youtube.channels().list(
                            part="snippet,statistics,contentDetails",
                            id=channel_id
                        ).execute()

                        if not ch_resp['items']:
                            return None

                        ch = ch_resp['items'][0]
                        subscribers = int(ch['statistics'].get('subscriberCount', 0))
                        total_views = int(ch['statistics'].get('viewCount', 0))
                        total_videos = int(ch['statistics'].get('videoCount', 0))
                        name = ch['snippet']['title']
                        playlist_id = ch['contentDetails']['relatedPlaylists']['uploads']

                        # Ambil 10 video terakhir
                        pl_resp = youtube.playlistItems().list(
                            part="contentDetails", playlistId=playlist_id, maxResults=10
                        ).execute()
                        video_ids = [item['contentDetails']['videoId'] for item in pl_resp['items']]

                        # Ambil statistik + snippet (untuk categoryId & publishedAt)
                        vids_resp = youtube.videos().list(
                            part="statistics,snippet", id=','.join(video_ids)
                        ).execute()

                        views_list = []
                        likes_list = []
                        comments_list = []
                        category_ids = []
                        pub_dates = []

                        from datetime import datetime, timezone
                        from collections import Counter

                        for v in vids_resp['items']:
                            stats = v.get('statistics', {})
                            snippet = v.get('snippet', {})
                            views_list.append(int(stats.get('viewCount', 0)))
                            likes_list.append(int(stats.get('likeCount', 0)))
                            comments_list.append(int(stats.get('commentCount', 0)))

                            # Kumpulkan categoryId untuk deteksi niche
                            cat_id = snippet.get('categoryId', '')
                            if cat_id:
                                category_ids.append(cat_id)

                            # Kumpulkan tanggal publish untuk hitung frekuensi
                            pub = snippet.get('publishedAt', '')
                            if pub:
                                pub_dates.append(datetime.strptime(pub, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc))

                        avg_views = sum(views_list) / len(views_list) if views_list else 0
                        avg_likes = sum(likes_list) / len(likes_list) if likes_list else 0
                        avg_comments = sum(comments_list) / len(comments_list) if comments_list else 0
                        avg_engagement = ((avg_likes + avg_comments) / avg_views * 100) if avg_views > 0 else 0

                        # Deteksi niche dari categoryId terbanyak
                        detected_niche = "🎬 Entertainment & Vlog"  # default
                        if category_ids:
                            most_common_cat = Counter(category_ids).most_common(1)[0][0]
                            detected_niche = category_to_niche.get(most_common_cat, "🎬 Entertainment & Vlog")

                        # Hitung frekuensi upload otomatis dari selisih tanggal
                        detected_monthly_uploads = 4  # default
                        if len(pub_dates) >= 2:
                            pub_dates_sorted = sorted(pub_dates, reverse=True)
                            date_diffs = []
                            for i in range(len(pub_dates_sorted) - 1):
                                diff = (pub_dates_sorted[i] - pub_dates_sorted[i+1]).days
                                if diff > 0:
                                    date_diffs.append(diff)
                            if date_diffs:
                                avg_days_between = sum(date_diffs) / len(date_diffs)
                                detected_monthly_uploads = max(1, round(30 / avg_days_between))

                        return {
                            "name": name,
                            "subscribers": subscribers,
                            "total_views": total_views,
                            "total_videos": total_videos,
                            "avg_views": avg_views,
                            "avg_engagement": avg_engagement,
                            "detected_niche": detected_niche,
                            "detected_monthly_uploads": detected_monthly_uploads,
                        }
                    except Exception as e:
                        st.error(f"Error: {e}")
                        return None

                data = get_channel_monetization_data(channel_input)

            if data:
                # Gunakan niche & frekuensi yang terdeteksi otomatis
                niche = data['detected_niche']
                monthly_uploads = data['detected_monthly_uploads']
                niche_data = niche_options[niche]
                rpm_min = niche_data["rpm_min"]
                rpm_max = niche_data["rpm_max"]
                rpm_avg = (rpm_min + rpm_max) / 2
                sponsorship_mult = niche_data["sponsorship_mult"]

                avg_views = data['avg_views']
                subscribers = data['subscribers']
                avg_engagement = data['avg_engagement']

                # Estimasi views per bulan
                monthly_views_est = avg_views * monthly_uploads

                # Estimasi AdSense (70% revenue share untuk creator)
                adsense_min = (monthly_views_est / 1000) * rpm_min * 0.7
                adsense_max = (monthly_views_est / 1000) * rpm_max * 0.7
                adsense_avg = (monthly_views_est / 1000) * rpm_avg * 0.7

                # Estimasi sponsorship per video (berbasis subscribers & engagement)
                # Formula: base rate $500 per 100K subscribers, dikali engagement multiplier
                base_sponsorship = (subscribers / 100000) * 500
                engagement_multiplier = min(avg_engagement / 2, 3.0)  # max 3x
                sponsorship_per_video = base_sponsorship * sponsorship_mult * max(engagement_multiplier, 0.5)
                sponsorship_monthly = sponsorship_per_video * monthly_uploads

                # Estimasi membership (5% subscriber join di $5/bulan)
                membership_est = subscribers * 0.005 * 5

                # Total estimasi
                total_min = adsense_min
                total_max = adsense_max + sponsorship_monthly + membership_est
                total_avg = adsense_avg + (sponsorship_monthly * 0.3)  # 30% kemungkinan dapat sponsor

                st.success(f"✅ Data channel **{data['name']}** berhasil diambil!")
                st.divider()

                # --- OVERVIEW ---
                st.subheader(f"📊 Profile: {data['name']}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Subscribers", f"{subscribers:,}")
                c2.metric("Avg Views/Video", f"{int(avg_views):,}")
                c3.metric("Avg Engagement", f"{avg_engagement:.2f}%")
                c4.metric("Total Video", f"{data['total_videos']:,}")

                # Tampilkan hasil deteksi otomatis
                d1, d2 = st.columns(2)
                d1.info(f"🎯 **Niche Terdeteksi:** {niche}")
                d2.info(f"📅 **Frekuensi Upload:** ~{monthly_uploads}x per bulan (dihitung dari 10 video terakhir)")

                # --- ESTIMASI ADSENSE ---
                st.subheader("📺 Estimasi Penghasilan AdSense")
                st.caption(f"Berdasarkan niche **{niche}** | RPM benchmark: ${rpm_min}–${rpm_max} per 1.000 views")

                a1, a2, a3 = st.columns(3)
                a1.metric("Estimasi Minimum/Bulan", f"${adsense_min:,.0f}", help="Berdasarkan RPM terendah niche ini")
                a2.metric("Estimasi Rata-rata/Bulan", f"${adsense_avg:,.0f}", help="Berdasarkan RPM rata-rata niche ini")
                a3.metric("Estimasi Maksimum/Bulan", f"${adsense_max:,.0f}", help="Berdasarkan RPM tertinggi niche ini")

                st.caption(f"📌 Asumsi: {monthly_uploads} video/bulan (terdeteksi otomatis) × rata-rata {int(avg_views):,} views/video = **{int(monthly_views_est):,} views/bulan**")

                st.divider()

                # --- ESTIMASI SPONSORSHIP ---
                st.subheader("🤝 Estimasi Sponsorship")
                st.caption("Berdasarkan jumlah subscriber, engagement rate, dan rata-rata industri niche ini")

                s1, s2 = st.columns(2)
                s1.metric("Estimasi per Video", f"${sponsorship_per_video:,.0f}")
                s2.metric("Estimasi per Bulan", f"${sponsorship_monthly:,.0f}", help="Asumsi semua video dapat sponsor — sangat optimistis")

                st.info(f"💡 Dengan {subscribers:,} subscriber dan engagement {avg_engagement:.2f}%, rate sponsorship wajar untuk channel ini berkisar **${sponsorship_per_video*0.5:,.0f} – ${sponsorship_per_video*1.5:,.0f} per video**.")

                st.divider()

                # --- ESTIMASI MEMBERSHIP ---
                st.subheader("👥 Estimasi YouTube Membership")
                st.caption("Asumsi: 0.5% subscriber bergabung di tier $5/bulan")
                st.metric("Estimasi Membership/Bulan", f"${membership_est:,.0f}")

                st.divider()

                # --- TOTAL POTENSI ---
                st.subheader("💎 Total Potensi Penghasilan Bulanan")
                t1, t2, t3 = st.columns(3)
                t1.metric("Skenario Konservatif", f"${total_min:,.0f}", help="AdSense saja, RPM minimum")
                t2.metric("Skenario Realistis", f"${total_avg:,.0f}", help="AdSense + 30% kemungkinan dapat sponsor")
                t3.metric("Skenario Optimistis", f"${total_max:,.0f}", help="AdSense + semua video dapat sponsor + membership")

                # Konversi ke Rupiah
                usd_idr = 15800
                st.markdown(f"**Dalam Rupiah (kurs ~Rp{usd_idr:,}/USD):**")
                r1, r2, r3 = st.columns(3)
                r1.metric("Konservatif", f"Rp{total_min * usd_idr:,.0f}")
                r2.metric("Realistis", f"Rp{total_avg * usd_idr:,.0f}")
                r3.metric("Optimistis", f"Rp{total_max * usd_idr:,.0f}")

                st.divider()

                # --- REKOMENDASI ---
                st.subheader("🚀 Rekomendasi untuk Meningkatkan Monetisasi")

                if avg_engagement < 1:
                    st.warning("⚠️ **Engagement masih rendah** — fokus dulu meningkatkan interaksi sebelum pitch ke sponsor. Sponsor melihat engagement lebih dari sekadar views.")
                elif avg_engagement < 3:
                    st.info("📈 **Engagement cukup** — sudah layak pitch ke sponsor micro/nano. Tingkatkan lagi untuk membuka pintu ke brand besar.")
                else:
                    st.success("🔥 **Engagement sangat baik** — posisi kuat untuk negosiasi sponsorship premium. Jangan undercharge!")

                if subscribers < 1000:
                    st.info("🌱 **Belum monetisasi AdSense** — butuh minimal 1.000 subscriber & 4.000 jam tayang. Fokus konsistensi konten dulu.")
                elif subscribers < 10000:
                    st.info("📣 **Fase micro-creator** — mulai bangun personal brand dan cari micro-sponsorship di niche kamu.")
                elif subscribers < 100000:
                    st.success("💪 **Mid-tier creator** — saatnya diversifikasi: digital product, affiliate marketing, dan membership.")
                else:
                    st.success("🏆 **Top-tier creator** — pertimbangkan membangun tim, agency deal, dan revenue stream pasif seperti online course.")

        else:
            st.warning("Masukkan link channel YouTube!")
