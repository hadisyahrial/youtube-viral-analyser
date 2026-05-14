import streamlit as st
from googleapiclient.discovery import build
import random
import requests
from bs4 import BeautifulSoup
import re
import time
import bcrypt

# --- KONFIGURASI ---
try:
    API_KEY = st.secrets["AIzaSyCoTQTLR8YCopYzHOV-f9a5mY4y9KXT7GA"]
except Exception:
    API_KEY = "AIzaSyCoTQTLR8YCopYzHOV-f9a5mY4y9KXT7GA"  # fallback lokal

try:
    GROQ_API_KEY = st.secrets["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"]
except Exception:
    GROQ_API_KEY = "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"

def call_groq(prompt, max_tokens=1500):
    """Panggil Groq API untuk generate teks"""
    if not GROQ_API_KEY:
        return None, "GROQ_API_KEY tidak ditemukan di Secrets."
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload, timeout=30
        )
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'], None
        else:
            return None, f"Groq error: {resp.status_code} — {resp.text[:200]}"
    except Exception as e:
        return None, str(e)

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
    """Generate variasi judul menggunakan Groq AI"""
    topic, tag_keyword = extract_topic(title, tags)
    tags_str = ', '.join(tags[:10]) if tags else 'tidak ada'

    if GROQ_API_KEY:
        prompt = f"""Kamu adalah YouTube title specialist berpengalaman.
Buat 5 variasi judul YouTube yang menarik dan relevan berdasarkan:

Judul asli: "{title}"
Topik utama: {topic}
Tags: {tags_str}

Kriteria setiap judul:
- Panjang 40–70 karakter
- Mengandung kata emosional atau angka spesifik
- Relevan dengan topik dan audiens yang tepat
- Bervariasi: coba format pertanyaan, listicle, storytelling, curiosity gap, dan versus
- Dalam bahasa yang sama dengan judul asli (Indonesia atau Inggris)

Tulis HANYA 5 judul, satu per baris, tanpa nomor atau penjelasan tambahan."""

        result, err = call_groq(prompt, max_tokens=300)
        if result:
            titles = [t.strip() for t in result.strip().split('\n') if t.strip()]
            return titles[:5]

    # Fallback ke template jika Groq tidak tersedia
    templates = [
        f"Fakta Menarik tentang {topic} yang Jarang Diketahui Publik",
        f"Inilah Kebenaran di Balik {topic} — Banyak yang Tidak Tahu!",
        f"{random.randint(3,7)} Fakta Mengejutkan tentang {topic}",
        f"Benarkah {topic}? Ini yang Sebenarnya Terjadi",
        f"Sisi Lain {topic} yang Tidak Pernah Diceritakan Media",
    ]
    return templates

def generate_hooks(title, grade):
    """Generate hook pembuka video menggunakan Groq AI"""
    topic, _ = extract_topic(title, [])

    if GROQ_API_KEY:
        prompt = f"""Kamu adalah YouTube scriptwriter profesional.
Buat 4 variasi hook pembuka video (30 detik pertama) yang sangat kuat berdasarkan:

Judul video: "{title}"
Topik: {topic}
Grade engagement: {grade}

Kriteria setiap hook:
- Panjang 15–30 kata
- Langsung menyentuh pain point atau rasa ingin tahu
- Mengandung curiosity gap, angka spesifik, atau pernyataan mengejutkan
- Bervariasi: coba format pertanyaan, pernyataan mengejutkan, personal story, dan urgensi
- Dalam bahasa yang sama dengan judul (Indonesia atau Inggris)
- Natural seperti orang berbicara, bukan membaca teks

Tulis HANYA 4 hook, satu per baris, tanpa nomor atau penjelasan tambahan."""

        result, err = call_groq(prompt, max_tokens=300)
        if result:
            hooks = [h.strip() for h in result.strip().split('\n') if h.strip()]
            return hooks[:4]

    # Fallback ke template jika Groq tidak tersedia
    keyword = topic.lower()
    hooks = [
        f"Pernahkah kamu bertanya-tanya kenapa {keyword} tidak pernah berkembang? Dalam video ini, saya ungkap rahasianya.",
        f"Hentikan dulu apa yang sedang kamu lakukan — informasi tentang {keyword} ini bisa mengubah segalanya.",
        f"Kebanyakan orang melakukan kesalahan besar soal {keyword}. Dan kemungkinan besar, kamu juga melakukannya.",
        f"Saya hampir menyerah dengan {keyword} — sampai saya menemukan cara ini.",
    ]
    return hooks

def generate_narasi(title, tags, grade, engagement):
    """Generate struktur narasi video menggunakan Groq AI"""
    topic, tag_keyword = extract_topic(title, tags)
    tags_str = ', '.join(tags[:10]) if tags else 'tidak ada'

    if GROQ_API_KEY:
        prompt = f"""Kamu adalah YouTube scriptwriter dan content strategist profesional.
Buat struktur narasi video YouTube yang detail dan actionable berdasarkan:

Judul video: "{title}"
Topik: {topic}
Tags: {tags_str}
Engagement grade: {grade} ({engagement:.2f}%)

Buat struktur narasi dengan format:

**🎬 Struktur Narasi untuk: "{title}"**

**[0:00 – 0:30] HOOK PEMBUKA**
[Tulis contoh kalimat hook yang spesifik dan kuat untuk topik ini]

**[0:30 – 1:30] IDENTIFIKASI MASALAH**
[Tulis masalah spesifik yang dihadapi penonton terkait topik ini]

**[1:30 – 4:00] ISI UTAMA**
[Tulis 3 poin utama yang harus dibahas, spesifik untuk topik ini]
- Poin 1: [spesifik]
- Poin 2: [spesifik]
- Poin 3: [spesifik]

**[4:00 – 4:30] BUKTI / CONTOH NYATA**
[Tulis jenis bukti atau contoh yang relevan untuk topik ini]

**[4:30 – 5:00] CTA PENUTUP**
[Tulis contoh CTA yang spesifik dan natural untuk topik ini]

**💡 Tips Produksi Spesifik**
[3 tips produksi yang relevan untuk konten ini — B-roll, grafik, atau elemen visual yang disarankan]

Tulis dalam bahasa yang sama dengan judul video. Sangat spesifik, bukan template generik."""

        result, err = call_groq(prompt, max_tokens=800)
        if result:
            return result

    # Fallback ke template jika Groq tidak tersedia
    keyword = topic.lower()
    return f"""
**🎬 Struktur Narasi untuk: "{title}"**

**[0:00 – 0:30] HOOK PEMBUKA**
Buka dengan pertanyaan yang relevan dengan {keyword}.

**[0:30 – 1:30] IDENTIFIKASI MASALAH**
Jelaskan masalah yang dihadapi penonton terkait {keyword}.

**[1:30 – 4:30] ISI UTAMA**
- Poin 1: Penjelasan + contoh nyata
- Poin 2: Penjelasan + contoh nyata
- Poin 3: Penjelasan + contoh nyata

**[4:30 – 5:00] CTA PENUTUP**
Like, subscribe, dan ajak komentar dengan pertanyaan terbuka.
"""

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

# ============================================================
# FUNGSI GLOBAL: HOOK & NARRATIVE ANALYSER
# ============================================================

def score_hook(hook):
    hook_lower = hook.lower()
    words = hook.split()
    score = 0
    feedback = []
    improvements = []

    word_count = len(words)
    if 10 <= word_count <= 30:
        score += 20
        feedback.append(("✅", f"Panjang hook ideal ({word_count} kata)."))
    elif word_count < 10:
        score += 8
        feedback.append(("⚠️", f"Hook terlalu pendek ({word_count} kata)."))
        improvements.append("Tambahkan konteks. Target 15-25 kata.")
    else:
        score += 10
        feedback.append(("⚠️", f"Hook terlalu panjang ({word_count} kata)."))
        improvements.append("Pangkas menjadi maksimal 30 kata.")

    curiosity_words = ['tahukah','ternyata','rahasia','mengejutkan','siapa sangka',
                       'fakta','sebenarnya','did you know','secret','surprising',
                       'shocked','truth','exposed','revealed','hampir']
    if any(w in hook_lower for w in curiosity_words):
        score += 20
        feedback.append(("✅", "Mengandung curiosity gap."))
    else:
        feedback.append(("❌", "Tidak ada curiosity gap."))
        improvements.append("Tambahkan elemen yang memancing rasa penasaran.")

    if any(c.isdigit() for c in hook):
        score += 15
        feedback.append(("✅", "Mengandung angka spesifik."))
    else:
        feedback.append(("⚠️", "Tidak ada angka spesifik."))
        improvements.append("Tambahkan angka. Contoh: 9 dari 10 creator gagal di langkah pertama.")

    urgency_words = ['sekarang','jangan','stop','hentikan','penting','harus',
                     'wajib','segera','now','before','immediately','must','never']
    if any(w in hook_lower for w in urgency_words):
        score += 15
        feedback.append(("✅", "Mengandung urgensi/FOMO."))
    else:
        feedback.append(("⚠️", "Tidak ada urgensi."))
        improvements.append("Tambahkan urgensi: Sebelum upload video berikutnya, tonton ini dulu.")

    personal_words = ['saya','aku','kamu','kita','pernah','dulu','cerita','pengalaman']
    if any(w in hook_lower for w in personal_words):
        score += 15
        feedback.append(("✅", "Mengandung elemen personal."))
    else:
        feedback.append(("⚠️", "Kurang personal."))
        improvements.append("Gunakan kata kamu atau cerita personal singkat.")

    if '?' in hook:
        score += 15
        feedback.append(("✅", "Menggunakan pertanyaan."))
    else:
        feedback.append(("💡", "Pertimbangkan menambahkan pertanyaan retoris."))

    return score, feedback, improvements


def get_narrative_data(url_or_id):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        channel_id = None
        handle = None
        handle_match = re.search(r'youtube\.com\/@([\w.-]+)', url_or_id)
        if handle_match:
            handle = handle_match.group(1)
        channel_match = re.search(r'youtube\.com\/channel\/(UC[\w-]+)', url_or_id)
        if channel_match:
            channel_id = channel_match.group(1)
        if not channel_id and handle:
            sr = youtube.search().list(
                part="snippet", q=handle, type="channel", maxResults=1
            ).execute()
            if sr.get('items'):
                channel_id = sr['items'][0]['snippet']['channelId']
        if not channel_id:
            st.error("Channel tidak ditemukan.")
            return None
        ch = youtube.channels().list(
            part="snippet,contentDetails", id=channel_id
        ).execute()
        if not ch.get('items'):
            return None
        name = ch['items'][0]['snippet']['title']
        playlist_id = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        pl = youtube.playlistItems().list(
            part="contentDetails", playlistId=playlist_id, maxResults=10
        ).execute()
        video_ids = [i['contentDetails']['videoId'] for i in pl.get('items', [])]
        if not video_ids:
            return None
        vids = youtube.videos().list(
            part="snippet,statistics", id=','.join(video_ids)
        ).execute()
        videos = []
        for v in vids.get('items', []):
            stats = v.get('statistics', {})
            sn = v.get('snippet', {})
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            comments = int(stats.get('commentCount', 0))
            eng = ((likes + comments) / views * 100) if views > 0 else 0
            videos.append({
                "title": sn.get('title', ''),
                "description": sn.get('description', '')[:300],
                "views": views,
                "engagement": eng,
            })
        return {"name": name, "videos": videos}
    except Exception as e:
        st.error(f"Error get_narrative_data: {e}")
        return None


def detect_dominant_format(titles):
    listicle = sum(1 for t in titles if t.split() and any(c.isdigit() for c in t.split()[0]))
    question = sum(1 for t in titles if '?' in t)
    howto = sum(1 for t in titles if any(w in t.lower() for w in ['how','cara','tutorial','tips','trick','guide','panduan']))
    story = sum(1 for t in titles if any(w in t.lower() for w in ['story','cerita','pengalaman','journey','kenapa','saya']))
    versus = sum(1 for t in titles if any(w in t.lower() for w in ['vs','versus','atau','better','best','terbaik']))
    review = sum(1 for t in titles if any(w in t.lower() for w in ['review','honest','jujur','worth','test','tried']))
    formats = {
        "🔢 Listicle": listicle,
        "❓ Pertanyaan": question,
        "📚 How-To": howto,
        "📖 Storytelling": story,
        "⚔️ Versus": versus,
        "🔍 Review": review,
    }
    dominant = max(formats, key=formats.get)
    return formats, dominant


def generate_hooks_from_pattern(dominant, top_video_title, channel_name):
    words = [w for w in top_video_title.split() if len(w) > 3]
    kw = ' '.join(words[:3]).lower() if words else "topik ini"
    hook_map = {
        "🔢 Listicle": [
            f"Ada {random.randint(5,9)} hal tentang {kw} yang belum kamu ketahui — dan channel seperti {channel_name} sudah membuktikannya.",
            f"Saya pelajari {random.randint(10,20)} video terbaik tentang {kw} dan menemukan pola yang selalu berulang. Ini dia.",
        ],
        "❓ Pertanyaan": [
            f"Pernahkah kamu bertanya-tanya kenapa konten tentang {kw} milik orang lain selalu viral, sementara punyamu tidak?",
            f"Apa yang sebenarnya membedakan creator sukses dari yang gagal ketika membahas {kw}? Jawabannya mengejutkan saya.",
        ],
        "📚 How-To": [
            f"Dalam video ini saya tunjukkan cara yang benar tentang {kw} — cara yang dipakai creator top tapi jarang diajarkan gratis.",
            f"Sebelum saya ajarkan cara {kw}, ada satu kesalahan fatal yang harus kamu hindari. Kebanyakan orang melewatkan ini.",
        ],
        "📖 Storytelling": [
            f"Dulu saya tidak percaya bahwa {kw} bisa mengubah segalanya. Sampai sesuatu terjadi yang memaksa saya berpikir ulang.",
            f"Ini bukan tutorial biasa tentang {kw}. Ini cerita tentang kegagalan saya dan apa yang saya pelajari darinya.",
        ],
        "⚔️ Versus": [
            f"Semua orang debat soal {kw} tapi tidak ada yang benar-benar mengujinya secara langsung. Sampai hari ini.",
            f"Saya bandingkan dua pendekatan berbeda untuk {kw} selama 30 hari. Hasilnya jauh dari yang saya ekspektasikan.",
        ],
        "🔍 Review": [
            f"Saya jujur: sebelum mencoba {kw} sendiri, saya skeptis. Tapi setelah {random.randint(2,6)} bulan, saya harus akui sesuatu.",
            f"Ini review paling jujur tentang {kw} yang akan kamu temukan — termasuk bagian yang tidak ingin didengar siapapun.",
        ],
    }
    return hook_map.get(dominant, hook_map["❓ Pertanyaan"])


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

mode = st.sidebar.selectbox("Pilih Mode Analisis", [
    "Single Analysis",
    "Video Battle ⚔️",
    "Competitor Tracker 🕵️",
    "Monetization Estimator 💰",
    "Hook & Narrative Analyser 🎣",
    "Content Repurposing Planner 🔄",
    "Script Video Generator 📝",
    "Audience Intelligence 🧠",
    "Channel Growth Roadmap 🗺️",
    "Thumbnail Analyser 🖼️",
])

st.sidebar.divider()
if st.sidebar.button("🔄 Reset / Clear Halaman", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ============================================================
# FUNGSI GLOBAL: HOOK & NARRATIVE ANALYSER
# ============================================================
def score_hook(hook):
    hook_lower = hook.lower()
    words = hook.split()
    score = 0
    feedback = []
    improvements = []

    word_count = len(words)
    if 10 <= word_count <= 30:
        score += 20
        feedback.append(("✅", f"Panjang hook ideal ({word_count} kata)."))
    elif word_count < 10:
        score += 8
        feedback.append(("⚠️", f"Hook terlalu pendek ({word_count} kata)."))
        improvements.append("Tambahkan konteks. Target 15–25 kata.")
    else:
        score += 10
        feedback.append(("⚠️", f"Hook terlalu panjang ({word_count} kata)."))
        improvements.append("Pangkas menjadi maksimal 30 kata.")

    curiosity_words = ['tahukah','ternyata','rahasia','mengejutkan','tidak disangka',
                       'siapa sangka','fakta','sebenarnya','did you know','secret',
                       'surprising','shocked','truth','exposed','revealed','hampir']
    if any(w in hook_lower for w in curiosity_words):
        score += 20
        feedback.append(("✅", "Mengandung curiosity gap — memancing rasa ingin tahu."))
    else:
        feedback.append(("❌", "Tidak ada curiosity gap."))
        improvements.append("Tambahkan: 'Yang tidak pernah diceritakan orang lain adalah...'")

    if any(c.isdigit() for c in hook):
        score += 15
        feedback.append(("✅", "Mengandung angka spesifik — konkret dan kredibel."))
    else:
        feedback.append(("⚠️", "Tidak ada angka spesifik."))
        improvements.append("Tambahkan angka. Contoh: '9 dari 10 creator gagal di langkah pertama'.")

    urgency_words = ['sekarang','jangan','stop','hentikan','sebelum terlambat',
                     'penting','harus','wajib','segera','now','before',
                     'immediately','urgent','critical','must','never']
    if any(w in hook_lower for w in urgency_words):
        score += 15
        feedback.append(("✅", "Mengandung urgensi/FOMO."))
    else:
        feedback.append(("⚠️", "Tidak ada urgensi."))
        improvements.append("Tambahkan: 'Sebelum kamu upload video berikutnya, tonton ini dulu.'")

    personal_words = ['saya','aku','kamu','kita','i ','my ','you ','we ',
                      'your','our','me ','pernah','dulu','cerita','pengalaman']
    if any(w in hook_lower for w in personal_words):
        score += 15
        feedback.append(("✅", "Mengandung elemen personal."))
    else:
        feedback.append(("⚠️", "Kurang personal."))
        improvements.append("Gunakan kata 'kamu' atau cerita personal singkat.")

    if '?' in hook:
        score += 15
        feedback.append(("✅", "Menggunakan pertanyaan — otak otomatis mencari jawaban."))
    else:
        feedback.append(("💡", "Pertimbangkan menambahkan pertanyaan retoris."))

    return score, feedback, improvements


def get_narrative_data(url_or_id):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        channel_id, handle = None, None
        handle_match = re.search(r'youtube\.com\/@([\w.-]+)', url_or_id)
        if handle_match: handle = handle_match.group(1)
        channel_match = re.search(r'youtube\.com\/channel\/(UC[\w-]+)', url_or_id)
        if channel_match: channel_id = channel_match.group(1)
        if not channel_id and handle:
            sr = youtube.search().list(part="snippet", q=handle, type="channel", maxResults=1).execute()
            if sr['items']: channel_id = sr['items'][0]['snippet']['channelId']
        if not channel_id: return None
        ch = youtube.channels().list(part="snippet,contentDetails", id=channel_id).execute()
        if not ch['items']: return None
        name = ch['items'][0]['snippet']['title']
        playlist_id = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        pl = youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=10).execute()
        vids = youtube.videos().list(
            part="snippet,statistics",
            id=','.join([i['contentDetails']['videoId'] for i in pl['items']])
        ).execute()
        videos = []
        for v in vids['items']:
            stats = v.get('statistics', {})
            sn = v['snippet']
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            comments = int(stats.get('commentCount', 0))
            eng = ((likes + comments) / views * 100) if views > 0 else 0
            videos.append({
                "title": sn['title'],
                "description": sn.get('description', '')[:300],
                "views": views, "engagement": eng,
            })
        return {"name": name, "videos": videos}
    except Exception as e:
        st.error(f"Error get_narrative_data: {e}")
        return None


def detect_dominant_format(titles):
    listicle = sum(1 for t in titles if t.split() and any(c.isdigit() for c in t.split()[0]))
    question = sum(1 for t in titles if '?' in t)
    howto = sum(1 for t in titles if any(w in t.lower() for w in ['how','cara','tutorial','tips','trick','guide','panduan']))
    story = sum(1 for t in titles if any(w in t.lower() for w in ['story','cerita','pengalaman','journey','why i','kenapa','saya']))
    versus = sum(1 for t in titles if any(w in t.lower() for w in ['vs','versus','or','atau','better','best','terbaik']))
    review = sum(1 for t in titles if any(w in t.lower() for w in ['review','honest','jujur','worth','test','tried']))
    formats = {
        "🔢 Listicle": listicle, "❓ Pertanyaan": question,
        "📚 How-To": howto, "📖 Storytelling": story,
        "⚔️ Versus": versus, "🔍 Review": review,
    }
    return formats, max(formats, key=formats.get)


def generate_hooks_from_pattern(dominant, top_video_title, channel_name):
    words = [w for w in top_video_title.split() if len(w) > 3]
    keyword = ' '.join(words[:3]) if words else "topik ini"
    kw = keyword.lower()
    hooks = {
        "🔢 Listicle": [
            f"Ada {random.randint(5,9)} hal tentang {kw} yang belum kamu ketahui — dan channel seperti {channel_name} sudah membuktikannya.",
            f"Saya pelajari {random.randint(10,20)} video terbaik tentang {kw} dan menemukan pola yang selalu berulang. Ini dia.",
        ],
        "❓ Pertanyaan": [
            f"Pernahkah kamu bertanya-tanya kenapa konten tentang {kw} milik orang lain selalu viral, sementara punyamu tidak?",
            f"Apa yang sebenarnya membedakan creator sukses dari yang gagal ketika membahas {kw}? Jawabannya mengejutkan saya.",
        ],
        "📚 How-To": [
            f"Dalam video ini saya akan tunjukkan cara yang benar tentang {kw} — cara yang dipakai creator top tapi jarang diajarkan secara gratis.",
            f"Sebelum saya ajarkan cara {kw}, ada satu kesalahan fatal yang harus kamu hindari dulu. Kebanyakan orang melewatkan ini.",
        ],
        "📖 Storytelling": [
            f"Dulu saya tidak percaya bahwa {kw} bisa mengubah segalanya. Sampai sesuatu terjadi yang memaksa saya berpikir ulang.",
            f"Ini bukan tutorial biasa tentang {kw}. Ini adalah cerita tentang kegagalan saya — dan apa yang saya pelajari darinya.",
        ],
        "⚔️ Versus": [
            f"Semua orang debat soal {kw} — tapi tidak ada yang benar-benar mengujinya secara langsung. Sampai hari ini.",
            f"Saya bandingkan dua pendekatan berbeda untuk {kw} selama 30 hari. Hasilnya jauh dari yang saya ekspektasikan.",
        ],
        "🔍 Review": [
            f"Saya jujur: sebelum mencoba {kw} sendiri, saya skeptis. Tapi setelah {random.randint(2,6)} bulan, saya harus akui sesuatu.",
            f"Ini review paling jujur tentang {kw} yang akan kamu temukan — termasuk bagian yang tidak ingin didengar siapapun.",
        ],
    }
    return hooks.get(dominant, hooks["❓ Pertanyaan"])



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



elif mode == "Hook & Narrative Analyser 🎣":
    st.subheader("🎣 Hook & Narrative Analyser")
    st.markdown("Analisis pola narasi kompetitor → generate hook → score hook kamu.")
    st.markdown("---")

    st.markdown("### 📌 Step 1 — Input Channel Kompetitor")
    ch_input = st.text_input(
        "Paste Link Channel Kompetitor",
        placeholder="https://www.youtube.com/@channelname",
        key="hook_ch_input"
    )

    if st.button("🔍 Analisis Kompetitor & Generate Hook", use_container_width=True, key="hook_btn"):
        if not ch_input.strip():
            st.warning("Masukkan link channel kompetitor!")
        else:
            with st.spinner("Menganalisis pola narasi kompetitor..."):
                ch_data = get_narrative_data(ch_input)

            if ch_data:
                titles_list = [v["title"] for v in ch_data["videos"]]
                formats_result, dominant_result = detect_dominant_format(titles_list)
                top_videos_result = sorted(ch_data["videos"], key=lambda x: x["engagement"], reverse=True)
                top_title = top_videos_result[0]["title"] if top_videos_result else ""

                generated_hooks_result = []
                if GROQ_API_KEY:
                    with st.spinner("Groq AI membuat hook dari formula kompetitor..."):
                        ch_nm = ch_data["name"]
                        titles_preview = " | ".join(titles_list[:6])
                        gp = (
                            "Kamu adalah YouTube scriptwriter profesional. "
                            "Buat 2 hook pembuka video terinspirasi dari pola narasi channel kompetitor berikut. "
                            f"Channel: {ch_nm}. "
                            f"Format dominan: {dominant_result}. "
                            f"Video terbaik: {top_title}. "
                            f"Judul terbaru: {titles_preview}. "
                            "Buat 2 hook masing-masing 20-35 kata, mengandung curiosity gap, "
                            "dipisahkan dengan satu baris kosong, tanpa nomor atau label."
                        )
                        gr, ge = call_groq(gp, max_tokens=300)
                    if gr:
                        raw_hooks = [h.strip() for h in gr.strip().split("\n\n") if h.strip()]
                        if len(raw_hooks) < 2:
                            raw_hooks = [h.strip() for h in gr.strip().split("\n") if h.strip()]
                        generated_hooks_result = raw_hooks[:2]
                    else:
                        generated_hooks_result = generate_hooks_from_pattern(dominant_result, top_title, ch_nm)
                else:
                    generated_hooks_result = generate_hooks_from_pattern(dominant_result, top_title, ch_data["name"])

                st.session_state["hn_ch_data"] = ch_data
                st.session_state["hn_titles"] = titles_list
                st.session_state["hn_formats"] = formats_result
                st.session_state["hn_dominant"] = dominant_result
                st.session_state["hn_top_videos"] = top_videos_result
                st.session_state["hn_ch_name"] = ch_data["name"]
                st.session_state["hn_hooks"] = generated_hooks_result
                st.rerun()
            else:
                st.error("Channel tidak ditemukan. Periksa link dan coba lagi.")

    if "hn_ch_data" in st.session_state:
        hn_ch_name = st.session_state["hn_ch_name"]
        hn_dominant = st.session_state["hn_dominant"]
        hn_formats = st.session_state["hn_formats"]
        hn_top_videos = st.session_state["hn_top_videos"]
        hn_titles = st.session_state["hn_titles"]
        hn_hooks = st.session_state["hn_hooks"]

        st.success(f"✅ Berhasil menganalisis **{hn_ch_name}**")
        st.divider()

        # --- STEP 2: HASIL ANALISIS NARASI ---
        st.markdown("### 📖 Step 2 — Hasil Analisis Pola Narasi")
        col_fmt, col_kw = st.columns(2)

        with col_fmt:
            st.markdown("#### 🎬 Format Narasi")
            for fmt, count in sorted(hn_formats.items(), key=lambda x: x[1], reverse=True):
                pct = count / len(hn_titles) * 100 if hn_titles else 0
                if count > 0:
                    bar = "█" * count + "░" * (len(hn_titles) - count)
                    st.markdown(f"**{fmt}** `{bar}` {count}x ({pct:.0f}%)")
            st.info(f"🏆 **Format dominan: {hn_dominant}**")

        with col_kw:
            st.markdown("#### 🔑 Kata Kunci Dominan")
            from collections import Counter
            sw = {"the","and","for","with","this","that","from","are","was","how","why",
                  "what","when","who","you","your","have","yang","dan","ini","itu",
                  "untuk","dengan","dari","akan","sudah","tidak","bisa","ada"}
            all_kw = []
            for t in hn_titles:
                all_kw.extend([w.lower().strip("?!.,") for w in t.split()
                                if len(w) > 3 and w.lower() not in sw])
            top_kw = Counter(all_kw).most_common(8)
            for w, c in top_kw:
                st.markdown(f"🔹 `{w}` — {c}x")

        st.divider()
        st.markdown("#### 🏆 Video Terbaik Kompetitor (Referensi Formula)")
        for i, v in enumerate(hn_top_videos[:3], 1):
            with st.expander(f"#{i} — {v['title']} ({v['engagement']:.2f}% engagement)", expanded=(i == 1)):
                notes = []
                if "?" in v["title"]: notes.append("❓ Pertanyaan")
                if any(c.isdigit() for c in v["title"]): notes.append("🔢 Angka")
                if sum(1 for c in v["title"] if c.isupper()) > 3: notes.append("🔠 Kapital")
                tlen = len(v["title"])
                notes.append("✂️ Pendek" if tlen < 40 else ("📝 Panjang" if tlen > 60 else "⚖️ Seimbang"))
                st.markdown("**Struktur judul:** " + " | ".join(notes))
                if v.get("description"):
                    st.caption(f"Deskripsi: {v['description'][:200]}...")

        st.divider()

        # --- STEP 3: HOOK GENERATED ---
        st.markdown("### 🎣 Step 3 — Hook Terinspirasi dari Kompetitor")
        st.caption(f"Hook dibuat menggunakan formula **{hn_dominant}** dari {hn_ch_name}.")
        for i, hook in enumerate(hn_hooks):
            col_h, col_b = st.columns([5, 1])
            with col_h:
                st.info(f"**Hook {i+1}:**\n\n*\"{hook}\"*")
            with col_b:
                if st.button("Pakai", key=f"hn_use_{i}"):
                    st.session_state["hn_selected_hook"] = hook
                    st.rerun()

        st.divider()

        # --- STEP 4: HOOK SCORER ---
        st.markdown("### 🎯 Step 4 — Score Hook Kamu")
        default_h = st.session_state.get("hn_selected_hook", "")
        hook_input_val = st.text_area(
            "Tulis atau edit hook di sini",
            value=default_h,
            placeholder="Tulis hook pembuka video kamu...",
            height=120,
            key="hn_hook_textarea"
        )

        if st.button("🏆 Score Hook Ini", use_container_width=True, key="hn_score_btn"):
            if not hook_input_val.strip():
                st.warning("Tulis atau pilih hook terlebih dahulu!")
            else:
                hn_score, hn_feedback, hn_improvements = score_hook(hook_input_val)

                if hn_score >= 85:
                    hn_grade, hn_color, hn_msg = "S-Tier 🏆", "green", "Hook luar biasa! Langsung rekam."
                elif hn_score >= 70:
                    hn_grade, hn_color, hn_msg = "A-Tier 🔥", "blue", "Hook sangat baik."
                elif hn_score >= 50:
                    hn_grade, hn_color, hn_msg = "B-Tier ✅", "orange", "Hook cukup, bisa diperkuat."
                else:
                    hn_grade, hn_color, hn_msg = "C-Tier ⚠️", "red", "Hook perlu direvisi."

                col_s, col_g = st.columns([1, 2])
                with col_s:
                    st.metric("Hook Score", f"{hn_score}/100")
                with col_g:
                    st.markdown(f"### :{hn_color}[{hn_grade}]")
                    st.caption(hn_msg)

                st.divider()
                st.markdown("#### 📋 Detail Penilaian")
                for icon, msg in hn_feedback:
                    if icon == "✅":
                        st.success(f"{icon} {msg}")
                    elif icon == "❌":
                        st.error(f"{icon} {msg}")
                    elif icon == "⚠️":
                        st.warning(f"{icon} {msg}")
                    else:
                        st.info(f"{icon} {msg}")

                if hn_improvements:
                    st.divider()
                    st.markdown("#### 🚀 Rekomendasi Perbaikan")
                    for idx_i, imp in enumerate(hn_improvements, 1):
                        st.info(f"**{idx_i}.** {imp}")

                st.divider()
                st.markdown("#### 📊 Posisi Hook Kamu vs Kompetitor")
                top_comp = hn_top_videos[0]
                comp_sc, _, _ = score_hook(top_comp["title"])
                c1, c2 = st.columns(2)
                c1.metric("Score Hook Kamu", f"{hn_score}/100")
                c2.metric(f"Score Terbaik {hn_ch_name}", f"{comp_sc}/100",
                          delta=f"{hn_score - comp_sc:+d}")
                if hn_score >= comp_sc:
                    st.success(f"🏆 Hook kamu lebih kuat dari formula terbaik {hn_ch_name}!")
                else:
                    st.warning(f"⚠️ Masih {comp_sc - hn_score} poin di bawah {hn_ch_name}. Terapkan rekomendasi di atas.")


elif mode == "Content Repurposing Planner 🔄":
    st.subheader("🔄 Content Repurposing Planner")
    st.markdown("Maksimalkan satu video YouTube menjadi konten di banyak platform sekaligus.")

    # --- PLATFORM OPTIONS ---
    PLATFORMS = {
        "📱 YouTube Shorts": {
            "icon": "📱",
            "format": "Video vertikal 60 detik",
            "best_for": "Momen paling menarik / insight terkuat dari video",
            "tips": [
                "Ambil 1 insight terbaik dari video (menit ke berapa yang paling banyak ditonton)",
                "Potong menjadi 45–60 detik, tambahkan teks overlay di layar",
                "Judul Shorts harus berbeda dari video utama — lebih pendek dan langsung",
                "Upload dalam 24–48 jam setelah video utama untuk memaksimalkan momentum",
            ],
            "template": "🎬 [{JUDUL_SINGKAT}] — {POIN_UTAMA} #Shorts"
        },
        "🎙️ Podcast / Audio": {
            "icon": "🎙️",
            "format": "Audio 5–15 menit",
            "best_for": "Konten berbasis opini, wawancara, atau edukasi mendalam",
            "tips": [
                "Rekam ulang audio dengan intro/outro podcast yang konsisten",
                "Hapus bagian visual-dependent (demo layar, grafik) — ganti dengan penjelasan verbal",
                "Upload ke Spotify for Podcasters (gratis) untuk distribusi otomatis",
                "Tambahkan timestamps di deskripsi podcast untuk navigasi mudah",
            ],
            "template": "🎙️ Ep. {NOMOR}: {JUDUL_VIDEO} | {NAMA_PODCAST}"
        },
        "🐦 Thread X (Twitter)": {
            "icon": "🐦",
            "format": "Thread 5–10 tweet",
            "best_for": "Konten berbasis poin-poin atau fakta menarik",
            "tips": [
                "Tweet pertama = hook terkuat (kutip statistik atau pernyataan mengejutkan)",
                "Setiap tweet = satu poin utama dari video (maksimal 280 karakter)",
                "Tweet terakhir = CTA + link video YouTube",
                "Posting thread di jam peak: Selasa–Kamis pukul 08.00–10.00 atau 19.00–21.00",
            ],
            "template": "🧵 THREAD: {POIN_UTAMA}\n\n(1/{TOTAL}) {HOOK_PEMBUKA}\n\n👇"
        },
        "📸 Carousel Instagram": {
            "icon": "📸",
            "format": "Slide 5–10 halaman",
            "best_for": "Konten tips, how-to, atau rangkuman visual",
            "tips": [
                "Slide 1 = judul/hook yang memaksa orang swipe (gunakan angka atau pertanyaan)",
                "Slide 2–9 = satu poin per slide, teks minimal, visual dominan",
                "Slide terakhir = CTA + arahkan ke link bio (video YouTube)",
                "Gunakan Canva template yang konsisten dengan branding channel",
            ],
            "template": "📊 {JUDUL}: {POIN_UTAMA} [Slide 1/{TOTAL_SLIDE}]"
        },
        "✍️ Artikel Blog": {
            "icon": "✍️",
            "format": "Artikel 800–1500 kata",
            "best_for": "Konten edukasi atau how-to yang butuh penjelasan mendalam",
            "tips": [
                "Gunakan judul yang mengandung keyword SEO untuk traffic Google organik",
                "Struktur: Intro → Problem → Solusi (H2) → Kesimpulan → CTA embed video",
                "Embed video YouTube di dalam artikel untuk meningkatkan watch time",
                "Publish di Medium, LinkedIn Article, atau blog pribadi",
            ],
            "template": "{JUDUL_SEO}: Panduan Lengkap {TAHUN} untuk {TARGET_AUDIENS}"
        },
        "📧 Newsletter": {
            "icon": "📧",
            "format": "Email 300–500 kata",
            "best_for": "Membangun hubungan langsung dengan subscriber loyal",
            "tips": [
                "Subject line = versi terpendek dari hook video (maksimal 50 karakter)",
                "Paragraf pembuka = ringkasan 2 kalimat mengapa konten ini penting buat pembaca",
                "Sisipkan 1–2 kutipan terbaik dari video sebagai preview",
                "CTA tunggal: satu tombol/link ke video — jangan terlalu banyak pilihan",
            ],
            "template": "📬 [{NAMA_NEWSLETTER}] {SUBJEK_SINGKAT} — edisi minggu ini"
        },
        "🎵 TikTok": {
            "icon": "🎵",
            "format": "Video vertikal 15–60 detik",
            "best_for": "Konten entertainment, hook kuat, dan tren audio",
            "tips": [
                "3 detik pertama KRUSIAL — langsung ke poin tanpa intro",
                "Gunakan trending audio untuk boost distribusi organik",
                "Tambahkan teks on-screen karena 85% penonton TikTok nonton tanpa suara",
                "Posting 1–3x sehari untuk hasil optimal di awal pertumbuhan akun",
            ],
            "template": "{HOOK_3_DETIK} #fyp #{NICHE_TAG} #{KEYWORD_TAG}"
        },
        "💼 LinkedIn Post": {
            "icon": "💼",
            "format": "Post teks 150–300 kata",
            "best_for": "Konten bisnis, karir, atau professional insight",
            "tips": [
                "Baris pertama = hook yang memaksa orang klik 'see more' (jangan lebih dari 2 baris)",
                "Format: Insight + Pengalaman Personal + Pelajaran yang Bisa Diterapkan",
                "Tag 2–3 orang relevan untuk meningkatkan jangkauan",
                "Posting Selasa–Kamis pagi (07.00–09.00) untuk engagement tertinggi di LinkedIn",
            ],
            "template": "💡 {INSIGHT_UTAMA}\n\nDulu saya pikir {ASUMSI_SALAH}...\n\nTapi setelah {PENGALAMAN}, saya sadar: {PELAJARAN}"
        },
    }

    # --- INPUT ---
    video_input_rp = st.text_input(
        "Paste Link Video YouTube",
        placeholder="https://www.youtube.com/watch?v=...",
        key="rp_video_input"
    )

    st.markdown("#### 🎯 Pilih Platform Repurposing")
    st.caption("Pilih platform mana saja yang ingin kamu gunakan untuk mendistribusikan konten ini.")

    selected_platforms = []
    cols = st.columns(4)
    platform_list = list(PLATFORMS.keys())
    for i, platform in enumerate(platform_list):
        with cols[i % 4]:
            if st.checkbox(platform, key=f"plat_{i}", value=(i < 3)):
                selected_platforms.append(platform)

    if st.button("🔄 Buat Repurposing Plan", use_container_width=True):
        if not video_input_rp:
            st.warning("Masukkan link video YouTube!")
        elif not selected_platforms:
            st.warning("Pilih minimal 1 platform!")
        else:
            with st.spinner("Menganalisis video & membuat repurposing plan..."):
                result = analyze_virality(video_input_rp)

            if result:
                title = result['title']
                views = result['views']
                likes = result['likes']
                comments = result['comments']
                engagement = result['engagement']
                tags = result['tags']
                grade = result['grade']

                # Ekstrak topik utama
                topic, tag_keyword = extract_topic(title, tags)

                st.success("✅ Video berhasil dianalisis!")
                st.divider()

                # --- OVERVIEW VIDEO ---
                st.subheader(f"🎬 Video: {title}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Views", f"{views:,}")
                c2.metric("Likes", f"{likes:,}")
                c3.metric("Comments", f"{comments:,}")
                c4.metric("Engagement", f"{engagement:.2f}%")
                st.markdown(f"**Topik utama terdeteksi:** `{topic}`")

                st.divider()

                # --- REPURPOSING PRIORITY ---
                st.subheader("🗓️ Rencana Repurposing")
                st.markdown(f"**{len(selected_platforms)} platform dipilih** — estimasi total konten yang dihasilkan dari 1 video ini:")

                # Hitung ROI konten
                total_content = len(selected_platforms)
                st.info(f"🚀 Dari **1 video** ini kamu bisa membuat **{total_content} konten** di platform berbeda — melipatgandakan jangkauan tanpa effort membuat konten dari nol.")

                st.divider()

                # --- PLAN PER PLATFORM ---
                st.subheader("📋 Detail Plan per Platform")

                for i, platform in enumerate(selected_platforms, 1):
                    p = PLATFORMS[platform]
                    with st.expander(f"{platform} — {p['format']}", expanded=(i <= 2)):

                        col_info, col_template = st.columns([3, 2])

                        with col_info:
                            st.markdown(f"**🎯 Paling cocok untuk:** {p['best_for']}")
                            st.markdown("**📌 Tips spesifik untuk video ini:**")
                            for tip in p['tips']:
                                st.markdown(f"- {tip}")

                        with col_template:
                            st.markdown("**✏️ Template Konten:**")

                            # Customize template dengan data video nyata
                            template = p['template']
                            judul_singkat = ' '.join(title.split()[:5])
                            template_filled = (template
                                .replace("{JUDUL_SINGKAT}", judul_singkat)
                                .replace("{JUDUL_VIDEO}", title[:50])
                                .replace("{POIN_UTAMA}", topic)
                                .replace("{HOOK_PEMBUKA}", f"Tahukah kamu tentang {topic.lower()}?")
                                .replace("{TOTAL}", "8")
                                .replace("{TOTAL_SLIDE}", "8")
                                .replace("{NOMOR}", str(i))
                                .replace("{TAHUN}", "2025")
                                .replace("{TARGET_AUDIENS}", "Content Creator")
                                .replace("{NAMA_NEWSLETTER}", "Creator Weekly")
                                .replace("{SUBJEK_SINGKAT}", topic[:40])
                                .replace("{NAMA_PODCAST}", f"{topic} Podcast")
                                .replace("{JUDUL_SEO}", title[:50])
                                .replace("{HOOK_3_DETIK}", f"Stop! Kamu harus tahu tentang {topic.lower()}")
                                .replace("{NICHE_TAG}", tag_keyword.lower().replace(' ', ''))
                                .replace("{KEYWORD_TAG}", topic.lower().replace(' ', ''))
                                .replace("{INSIGHT_UTAMA}", f"Fakta tentang {topic} yang mengubah cara saya berkonten")
                                .replace("{ASUMSI_SALAH}", f"{topic.lower()} itu mudah")
                                .replace("{PENGALAMAN}", "mencoba sendiri selama 3 bulan")
                                .replace("{PELAJARAN}", f"konsistensi di {topic.lower()} jauh lebih penting dari viral")
                            )
                            st.code(template_filled, language=None)

                st.divider()

                # --- JADWAL DISTRIBUSI ---
                st.subheader("📅 Jadwal Distribusi yang Disarankan")
                st.markdown("Urutan distribusi optimal untuk memaksimalkan momentum setiap platform:")

                schedule = []
                priority_order = [
                    "📱 YouTube Shorts",
                    "🎵 TikTok",
                    "📸 Carousel Instagram",
                    "🐦 Thread X (Twitter)",
                    "💼 LinkedIn Post",
                    "✍️ Artikel Blog",
                    "📧 Newsletter",
                    "🎙️ Podcast / Audio",
                ]

                day = 0
                timing = {
                    0: "Hari H (sama dengan upload video utama)",
                    1: "Hari H+1",
                    2: "Hari H+2",
                    3: "Hari H+3",
                    5: "Hari H+5",
                    7: "Hari H+7 (1 minggu setelah upload)",
                    10: "Hari H+10",
                    14: "Hari H+14 (2 minggu setelah upload)",
                }
                day_map = [0, 1, 2, 3, 5, 7, 10, 14]

                ordered_selected = [p for p in priority_order if p in selected_platforms]
                remaining = [p for p in selected_platforms if p not in priority_order]
                ordered_selected += remaining

                for i, platform in enumerate(ordered_selected):
                    day_val = day_map[i] if i < len(day_map) else day_map[-1] + (i - len(day_map) + 1) * 2
                    timing_str = timing.get(day_val, f"Hari H+{day_val}")
                    st.markdown(f"**{i+1}.** {platform} → ⏰ {timing_str}")

                st.divider()

                # --- ESTIMASI JANGKAUAN TAMBAHAN ---
                st.subheader("📊 Estimasi Jangkauan Tambahan")
                st.caption("Estimasi kasar berdasarkan rata-rata industri — bukan jaminan hasil.")

                reach_multipliers = {
                    "📱 YouTube Shorts": 0.3,
                    "🎵 TikTok": 0.5,
                    "📸 Carousel Instagram": 0.2,
                    "🐦 Thread X (Twitter)": 0.15,
                    "💼 LinkedIn Post": 0.1,
                    "✍️ Artikel Blog": 0.2,
                    "📧 Newsletter": 0.05,
                    "🎙️ Podcast / Audio": 0.1,
                }

                total_additional = 0
                for platform in selected_platforms:
                    mult = reach_multipliers.get(platform, 0.1)
                    additional = int(views * mult)
                    total_additional += additional
                    st.markdown(f"- {platform}: +**{additional:,}** estimasi tambahan reach")

                st.success(f"🚀 Total estimasi tambahan reach dari repurposing: **+{total_additional:,}** — tanpa membuat konten baru dari nol!")

            else:
                st.error("Video tidak ditemukan. Pastikan link benar!")

elif mode == "Script Video Generator 📝":
    st.subheader("📝 Script Video Generator")
    st.markdown("Generate script video lengkap berbasis data YouTube nyata — ditenagai **Groq AI (Llama 3)**.")

    if not GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY belum diisi di Streamlit Secrets. Tambahkan dulu untuk menggunakan fitur ini.")
        st.stop()

    # --- INPUT ---
    st.markdown("### 📌 Step 1 — Sumber Inspirasi Script")
    source_mode = st.radio(
        "Buat script berdasarkan:",
        ["🔗 Analisis video kompetitor (direkomendasikan)", "✏️ Input topik manual"],
        horizontal=True
    )

    competitor_data = None
    topic_input = ""
    niche_input = ""
    target_audience = ""

    if "🔗" in source_mode:
        comp_url = st.text_input("Paste Link Video Kompetitor", placeholder="https://www.youtube.com/watch?v=...")
        if comp_url and st.button("🔍 Analisis Video Kompetitor", use_container_width=False):
            with st.spinner("Menganalisis video kompetitor..."):
                competitor_data = analyze_virality(comp_url)
                if competitor_data:
                    st.session_state['script_competitor'] = competitor_data
                    st.success(f"✅ Video kompetitor dianalisis: **{competitor_data['title']}**")
                else:
                    st.error("Video tidak ditemukan.")

        if 'script_competitor' in st.session_state:
            competitor_data = st.session_state['script_competitor']
            cd = competitor_data
            st.info(f"📊 **{cd['title']}** | 👁️ {cd['views']:,} views | 🔥 {cd['engagement']:.2f}% engagement | Grade: {cd['grade']}")
    else:
        topic_input = st.text_input("Topik Video", placeholder="Contoh: Cara meningkatkan engagement YouTube")

    st.divider()
    st.markdown("### ✏️ Step 2 — Detail Script")

    col1, col2 = st.columns(2)
    with col1:
        video_title = st.text_input(
            "Judul Video yang Akan Dibuat",
            value=competitor_data['title'][:80] if competitor_data else topic_input,
            placeholder="Judul video kamu..."
        )
        duration = st.selectbox("Durasi Target Video", ["3–5 menit", "5–8 menit", "8–12 menit", "12–20 menit"])
        language = st.selectbox("Bahasa Script", ["Bahasa Indonesia", "English"])

    with col2:
        niche_input = st.text_input("Niche / Kategori Konten", placeholder="Contoh: YouTube Tips, Finance, Gaming")
        target_audience = st.text_input("Target Audiens", placeholder="Contoh: Content creator pemula usia 18–30 tahun")
        tone = st.selectbox("Tone / Gaya Bahasa", ["Santai & Conversational", "Profesional & Edukatif", "Energetik & Motivatif", "Storytelling Personal"])

    st.divider()
    st.markdown("### 🎯 Step 3 — Pilih Bagian Script")
    st.caption("Pilih bagian mana yang ingin di-generate — bisa satu per satu atau semua sekaligus.")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1: gen_hook = st.checkbox("🎣 Hook Pembuka", value=True)
    with col_s2: gen_body = st.checkbox("📖 Isi Utama", value=True)
    with col_s3: gen_cta = st.checkbox("📣 CTA Penutup", value=True)
    with col_s4: gen_desc = st.checkbox("📄 Deskripsi YouTube", value=True)

    if st.button("🚀 Generate Script dengan Groq AI", use_container_width=True, type="primary"):
        if not video_title:
            st.warning("Isi judul video terlebih dahulu!")
        elif not any([gen_hook, gen_body, gen_cta, gen_desc]):
            st.warning("Pilih minimal 1 bagian script!")
        else:
            # Bangun konteks dari data kompetitor jika ada
            competitor_context = ""
            if competitor_data:
                competitor_context = f"""
Data video kompetitor untuk referensi:
- Judul: {competitor_data['title']}
- Views: {competitor_data['views']:,}
- Engagement: {competitor_data['engagement']:.2f}%
- Grade: {competitor_data['grade']}
- Tags: {', '.join(competitor_data['tags'][:10]) if competitor_data['tags'] else 'tidak ada'}
Gunakan pola dan gaya yang terinspirasi dari video ini, namun buat konten yang orisinal.
"""

            st.divider()
            st.subheader("🎬 Script yang Digenerate")

            # --- GENERATE HOOK ---
            if gen_hook:
                with st.spinner("✍️ Generating hook pembuka..."):
                    hook_prompt = f"""Kamu adalah scriptwriter YouTube profesional berpengalaman.
Buat hook pembuka video YouTube yang sangat kuat dalam {language}.

Judul video: {video_title}
Niche: {niche_input or 'General'}
Target audiens: {target_audience or 'Content creator'}
Tone: {tone}
Durasi hook: 30–45 detik pertama (sekitar 75–100 kata)
{competitor_context}

Kriteria hook yang harus dipenuhi:
1. Langsung menyentuh pain point atau rasa ingin tahu audiens
2. Mengandung curiosity gap atau pernyataan mengejutkan
3. Ada angka spesifik jika relevan
4. Berikan alasan mengapa penonton harus terus menonton
5. Tidak ada basa-basi atau intro panjang

Tulis HANYA teks hook-nya saja, tanpa label atau penjelasan tambahan."""

                    hook_result, err = call_groq(hook_prompt, max_tokens=300)

                with st.expander("🎣 Hook Pembuka (30–45 detik pertama)", expanded=True):
                    if hook_result:
                        st.markdown(hook_result)
                        st.code(hook_result, language=None)
                    else:
                        st.error(f"Gagal generate hook: {err}")

            # --- GENERATE BODY ---
            if gen_body:
                with st.spinner("📖 Generating isi utama video..."):
                    dur_map = {"3–5 menit": "3", "5–8 menit": "5", "8–12 menit": "8", "12–20 menit": "12"}
                    min_dur = dur_map.get(duration, "5")

                    body_prompt = f"""Kamu adalah scriptwriter YouTube profesional berpengalaman.
Buat script isi utama video YouTube dalam {language}.

Judul video: {video_title}
Niche: {niche_input or 'General'}
Target audiens: {target_audience or 'Content creator'}
Tone: {tone}
Durasi video: {duration} (buat script untuk bagian isi utama sekitar {int(min_dur)*2}–{int(min_dur)*3} menit)
{competitor_context}

Format script:
- Bagi menjadi 3–5 segmen utama dengan judul segmen
- Setiap segmen berisi penjelasan, contoh nyata, dan transisi ke segmen berikutnya
- Gunakan format [VISUAL: ...] untuk menandai instruksi visual/B-roll
- Sertakan [PAUSE] di momen yang butuh penekanan
- Tulis dengan natural seperti orang berbicara, bukan membaca teks

Tulis HANYA script-nya, tanpa penjelasan tambahan."""

                    body_result, err = call_groq(body_prompt, max_tokens=1500)

                with st.expander("📖 Isi Utama Video", expanded=True):
                    if body_result:
                        st.markdown(body_result)
                        st.code(body_result, language=None)
                    else:
                        st.error(f"Gagal generate isi: {err}")

            # --- GENERATE CTA ---
            if gen_cta:
                with st.spinner("📣 Generating CTA penutup..."):
                    cta_prompt = f"""Kamu adalah scriptwriter YouTube profesional berpengalaman.
Buat script CTA (Call-to-Action) penutup video YouTube dalam {language}.

Judul video: {video_title}
Niche: {niche_input or 'General'}
Tone: {tone}
Durasi CTA: 30–60 detik terakhir

Kriteria CTA yang harus dipenuhi:
1. Ringkas poin utama dalam 1–2 kalimat
2. Minta like dengan alasan yang jelas (bukan sekadar "jangan lupa like")
3. Minta subscribe dengan value proposition spesifik
4. Ajak komentar dengan pertanyaan spesifik yang mudah dijawab
5. Tease konten berikutnya jika relevan
6. Natural dan tidak terkesan memaksa

Tulis HANYA teks CTA-nya saja, tanpa label atau penjelasan tambahan."""

                    cta_result, err = call_groq(cta_prompt, max_tokens=300)

                with st.expander("📣 CTA Penutup (30–60 detik terakhir)", expanded=True):
                    if cta_result:
                        st.markdown(cta_result)
                        st.code(cta_result, language=None)
                    else:
                        st.error(f"Gagal generate CTA: {err}")

            # --- GENERATE DESKRIPSI ---
            if gen_desc:
                with st.spinner("📄 Generating deskripsi YouTube..."):
                    tags_context = ""
                    if competitor_data and competitor_data['tags']:
                        tags_context = f"Tags kompetitor untuk referensi keyword: {', '.join(competitor_data['tags'][:15])}"

                    desc_prompt = f"""Kamu adalah SEO specialist YouTube profesional.
Buat deskripsi video YouTube yang optimal untuk SEO dalam {language}.

Judul video: {video_title}
Niche: {niche_input or 'General'}
Target audiens: {target_audience or 'Content creator'}
{tags_context}

Format deskripsi:
1. Paragraf pertama (2–3 kalimat): ringkasan video + keyword utama
2. Timestamps: buat 5–7 timestamp fiktif yang relevan dengan topik
3. Tentang channel: 2 kalimat deskripsi channel
4. Social media placeholder: Twitter, Instagram, TikTok
5. Hashtags: 10–15 hashtag relevan di akhir

Tulis deskripsi lengkapnya langsung tanpa penjelasan tambahan."""

                    desc_result, err = call_groq(desc_prompt, max_tokens=600)

                with st.expander("📄 Deskripsi YouTube (SEO Optimized)", expanded=True):
                    if desc_result:
                        st.markdown(desc_result)
                        st.code(desc_result, language=None)
                    else:
                        st.error(f"Gagal generate deskripsi: {err}")

            st.divider()
            st.success("✅ Script selesai digenerate! Copy bagian yang kamu butuhkan dan sesuaikan dengan gaya kontenmu.")
            st.caption("⚠️ Script ini adalah draft awal — selalu review dan sesuaikan dengan suara asli kamu sebelum rekam.")

elif mode == "Audience Intelligence 🧠":
    st.subheader("🧠 Audience Intelligence")
    st.markdown("Temukan **topik viral**, **pain point audiens**, dan **sentimen komentar** — semua dari data nyata, dianalisis Groq AI.")

    if not GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY belum diisi di Streamlit Secrets.")
        st.stop()

    # --- INPUT MODE ---
    st.markdown("### 📌 Pilih Sumber Data")
    source = st.radio("Analisis berdasarkan:", ["🔗 Link Channel Kompetitor", "✏️ Niche / Topik Manual", "🔗 + ✏️ Keduanya"], horizontal=True)

    channel_url_ai = ""
    niche_manual = ""

    if "🔗" in source:
        channel_url_ai = st.text_input("Link Channel Kompetitor", placeholder="https://www.youtube.com/@channelname", key="ai_channel")
    if "✏️" in source:
        niche_manual = st.text_input("Niche / Topik", placeholder="Contoh: Personal Finance, Gaming, Travel Indonesia", key="ai_niche")

    st.divider()

    # --- PILIH FITUR ---
    st.markdown("### 🎯 Pilih Analisis yang Diinginkan")
    col1, col2, col3 = st.columns(3)
    with col1: do_viral = st.checkbox("🎯 Viral Topic Finder", value=True)
    with col2: do_pain = st.checkbox("🧠 Audience Pain Point", value=True)
    with col3: do_sentiment = st.checkbox("💬 Comment Sentiment", value=True)

    if st.button("🚀 Jalankan Audience Intelligence", use_container_width=True, type="primary"):
        has_channel = bool(channel_url_ai.strip())
        has_niche = bool(niche_manual.strip())

        if not has_channel and not has_niche:
            st.warning("Masukkan link channel atau niche terlebih dahulu!")
            st.stop()

        # ============================================================
        # AMBIL DATA CHANNEL JIKA ADA
        # ============================================================
        channel_context = ""
        video_titles = []
        all_tags = []
        channel_name = ""
        comments_data = []
        top_videos_ai = []

        if has_channel:
            with st.spinner("Mengambil data channel..."):
                try:
                    youtube = build('youtube', 'v3', developerKey=API_KEY)

                    # Resolve channel ID
                    handle_match = re.search(r'youtube\.com\/@([\w.-]+)', channel_url_ai)
                    channel_id = None
                    if handle_match:
                        sr = youtube.search().list(part="snippet", q=handle_match.group(1), type="channel", maxResults=1).execute()
                        if sr['items']: channel_id = sr['items'][0]['snippet']['channelId']
                    ch_match = re.search(r'youtube\.com\/channel\/(UC[\w-]+)', channel_url_ai)
                    if ch_match: channel_id = ch_match.group(1)

                    if channel_id:
                        ch_resp = youtube.channels().list(part="snippet,contentDetails,statistics", id=channel_id).execute()
                        if ch_resp['items']:
                            ch = ch_resp['items'][0]
                            channel_name = ch['snippet']['title']
                            subscribers = int(ch['statistics'].get('subscriberCount', 0))
                            playlist_id = ch['contentDetails']['relatedPlaylists']['uploads']

                            # Ambil 15 video terakhir
                            pl_resp = youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=15).execute()
                            video_ids = [i['contentDetails']['videoId'] for i in pl_resp['items']]

                            vids_resp = youtube.videos().list(part="snippet,statistics", id=','.join(video_ids)).execute()

                            for v in vids_resp['items']:
                                stats = v.get('statistics', {})
                                sn = v['snippet']
                                views = int(stats.get('viewCount', 0))
                                likes = int(stats.get('likeCount', 0))
                                comments_count = int(stats.get('commentCount', 0))
                                eng = ((likes + comments_count) / views * 100) if views > 0 else 0
                                video_titles.append(sn['title'])
                                all_tags.extend(sn.get('tags', [])[:5])
                                top_videos_ai.append({
                                    "id": v['id'], "title": sn['title'],
                                    "views": views, "engagement": eng,
                                    "comments_count": comments_count
                                })

                            # Ambil komentar dari 3 video terbaik
                            top3 = sorted(top_videos_ai, key=lambda x: x['engagement'], reverse=True)[:3]
                            for vid in top3:
                                try:
                                    cm_resp = youtube.commentThreads().list(
                                        part="snippet", videoId=vid['id'],
                                        maxResults=30, order="relevance"
                                    ).execute()
                                    for item in cm_resp['items']:
                                        text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                                        likes_cm = item['snippet']['topLevelComment']['snippet']['likeCount']
                                        comments_data.append({"text": text[:200], "likes": likes_cm, "video": vid['title'][:50]})
                                except:
                                    pass

                            channel_context = f"""
Channel: {channel_name} ({subscribers:,} subscribers)
Video terbaru (judul): {', '.join(video_titles[:10])}
Tags yang sering dipakai: {', '.join(list(set(all_tags))[:20])}
"""
                        else:
                            st.error("Channel tidak ditemukan.")
                except Exception as e:
                    st.error(f"Error mengambil data: {e}")

        niche_context = f"Niche/Topik: {niche_manual}" if has_niche else ""
        combined_context = f"{channel_context}\n{niche_context}".strip()

        st.success("✅ Data berhasil dikumpulkan! Groq AI sedang menganalisis...")
        st.divider()

        # ============================================================
        # 1. VIRAL TOPIC FINDER
        # ============================================================
        if do_viral:
            st.subheader("🎯 Viral Topic Finder")
            st.caption("Topik yang berpotensi viral berdasarkan tren niche dan pola konten kompetitor.")

            with st.spinner("Groq AI mencari topik viral..."):
                viral_prompt = f"""Kamu adalah analis konten YouTube berpengalaman.
Berdasarkan data berikut, identifikasi 8 topik konten yang berpotensi viral.

{combined_context}

Untuk setiap topik berikan:
1. Judul konten yang menarik (siap pakai)
2. Alasan mengapa topik ini berpotensi viral (1 kalimat)
3. Tingkat persaingan: Rendah / Sedang / Tinggi
4. Estimasi potensi views: Kecil (<10K) / Sedang (10K-100K) / Besar (>100K)
5. Format konten terbaik: Video panjang / Shorts / Keduanya

Format output dalam Bahasa Indonesia. Buat dalam format terstruktur yang mudah dibaca.
Fokus pada topik yang BELUM banyak dibuat kompetitor tapi SEDANG dicari audiens."""

                viral_result, err = call_groq(viral_prompt, max_tokens=1200)

            if viral_result:
                st.markdown(viral_result)

                # Generate tambahan: topic ideas dari titles
                if video_titles:
                    st.markdown("#### 📊 Pola Topik dari Channel Kompetitor")
                    from collections import Counter
                    stopwords_ai = {'the','and','for','with','this','that','how','why','what',
                                    'yang','dan','ini','itu','untuk','dengan','dari','tidak','bisa'}
                    all_title_words = []
                    for t in video_titles:
                        all_title_words.extend([w.lower().strip('?!.,#') for w in t.split()
                                                if len(w) > 3 and w.lower() not in stopwords_ai])
                    top_topics = Counter(all_title_words).most_common(12)
                    if top_topics:
                        cols = st.columns(4)
                        for i, (word, count) in enumerate(top_topics):
                            with cols[i % 4]:
                                st.metric(f"`{word}`", f"{count}x muncul")
            else:
                st.error(f"Gagal: {err}")

            st.divider()

        # ============================================================
        # 2. AUDIENCE PAIN POINT ANALYSER
        # ============================================================
        if do_pain:
            st.subheader("🧠 Audience Pain Point Analyser")
            st.caption("Pertanyaan, keluhan, dan keinginan audiens yang belum dijawab — tambang emas ide konten.")

            with st.spinner("Groq AI menganalisis pain point audiens..."):
                # Siapkan sample komentar jika ada
                comments_sample = ""
                if comments_data:
                    top_comments = sorted(comments_data, key=lambda x: x['likes'], reverse=True)[:20]
                    comments_sample = "Sample komentar nyata dari video kompetitor:\n"
                    for c in top_comments:
                        comments_sample += f'- "{c["text"]}" (👍 {c["likes"]})\n'

                pain_prompt = f"""Kamu adalah analis audiens YouTube berpengalaman.
Analisis pain point, pertanyaan, dan keinginan audiens berdasarkan data berikut.

{combined_context}

{comments_sample}

Identifikasi dan kategorikan:

## 🔴 Pain Points Utama (masalah yang paling sering dihadapi audiens)
List 5 pain point dengan penjelasan singkat + peluang konten untuk menjawabnya.

## ❓ Pertanyaan yang Sering Ditanyakan (tapi belum terjawab dengan baik)
List 5 pertanyaan yang sering muncul di niche ini + judul konten yang bisa menjawabnya.

## 💡 Keinginan Tersembunyi Audiens (yang tidak diucapkan tapi tersirat)
List 3 keinginan tersembunyi + cara mengeksploitasinya dalam konten.

## 🎯 Rekomendasi Konten Prioritas
3 ide konten yang PALING MENDESAK dibuat berdasarkan pain point di atas.

Tulis dalam Bahasa Indonesia, spesifik dan actionable."""

                pain_result, err = call_groq(pain_prompt, max_tokens=1500)

            if pain_result:
                st.markdown(pain_result)
            else:
                st.error(f"Gagal: {err}")

            st.divider()

        # ============================================================
        # 3. COMMENT SENTIMENT ANALYSER
        # ============================================================
        if do_sentiment:
            st.subheader("💬 Comment Sentiment Analyser")
            st.caption("Analisis sentimen komentar — apakah audiens puas, frustrasi, atau meminta konten lanjutan.")

            if not comments_data:
                if has_channel:
                    st.info("Tidak ada komentar yang berhasil diambil dari channel ini (mungkin komentar dinonaktifkan).")
                else:
                    st.info("Sentiment analysis membutuhkan link channel kompetitor untuk mengambil komentar nyata.")
            else:
                with st.spinner("Groq AI menganalisis sentimen komentar..."):
                    all_comments_text = "\n".join([f'- "{c["text"]}" (👍{c["likes"]})' for c in comments_data[:40]])

                    sentiment_prompt = f"""Kamu adalah analis sentimen konten YouTube profesional.
Analisis sentimen komentar berikut dari channel {channel_name}:

{all_comments_text}

Berikan analisis lengkap:

## 📊 Distribusi Sentimen
Persentase: Positif / Netral / Negatif / Pertanyaan / Request konten

## 😊 Sentimen Positif — Apa yang Disukai Audiens
Top 3 hal yang paling disukai audiens dari konten ini.

## 😤 Sentimen Negatif — Keluhan & Kritik
Top 3 keluhan atau kritik yang perlu diperhatikan creator.

## 🙋 Request & Pertanyaan Audiens
5 request atau pertanyaan spesifik yang paling sering muncul — ini adalah ide konten berikutnya!

## 💡 Insight untuk Creator
3 rekomendasi konkret berdasarkan analisis sentimen ini.

## 🚨 Red Flag
Apakah ada pola komentar negatif yang perlu segera ditangani? Jelaskan.

Tulis dalam Bahasa Indonesia, jelas dan actionable."""

                    sentiment_result, err = call_groq(sentiment_prompt, max_tokens=1200)

                if sentiment_result:
                    # Tampilkan ringkasan komentar terlebih dahulu
                    st.markdown(f"**Total komentar dianalisis:** {len(comments_data)} komentar dari {min(3, len(top_videos_ai))} video terbaik")

                    with st.expander("📝 Lihat Sample Komentar yang Dianalisis", expanded=False):
                        for c in comments_data[:10]:
                            st.markdown(f"👍 **{c['likes']}** | *\"{c['text']}\"*")
                            st.caption(f"Dari video: {c['video']}")

                    st.divider()
                    st.markdown(sentiment_result)
                else:
                    st.error(f"Gagal: {err}")

        # ============================================================
        # RINGKASAN AKHIR
        # ============================================================
        st.divider()
        st.subheader("🎯 Action Plan — Langkah Selanjutnya")

        with st.spinner("Groq AI membuat action plan..."):
            action_prompt = f"""Berdasarkan analisis Audience Intelligence untuk {channel_context or niche_context},
buat Action Plan konten yang sangat konkret dan actionable untuk 30 hari ke depan.

Format:
## 📅 Minggu 1 (Hari 1–7): Quick Win
2 konten yang harus dibuat SEGERA — topik yang sudah terbukti dan mudah dibuat.

## 📅 Minggu 2 (Hari 8–14): Pain Point Content
2 konten yang menjawab pain point terbesar audiens.

## 📅 Minggu 3 (Hari 15–21): Viral Attempt
1 konten dengan potensi viral tertinggi — perlu riset dan produksi lebih matang.

## 📅 Minggu 4 (Hari 22–30): Community Building
1 konten yang memancing interaksi maksimal (Q&A, poll, challenge, atau collab).

## ✅ 3 Hal yang Harus Dilakukan Sebelum Upload Video Berikutnya
Checklist konkret berdasarkan temuan analisis di atas.

Tulis dalam Bahasa Indonesia, spesifik dengan judul konten yang siap dipakai."""

            action_result, err = call_groq(action_prompt, max_tokens=1000)

        if action_result:
            st.markdown(action_result)
        else:
            st.error(f"Gagal membuat action plan: {err}")

elif mode == "Channel Growth Roadmap 🗺️":
    st.subheader("🗺️ Channel Growth Roadmap")
    st.markdown("Roadmap pertumbuhan channel **30 hari** yang spesifik dan actionable — ditenagai Groq AI.")

    if not GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY belum diisi di Streamlit Secrets.")
        st.stop()

    st.markdown("### 📌 Input Channel")
    channel_url_gr = st.text_input("Paste Link Channel YouTube Kamu", placeholder="https://www.youtube.com/@channelname", key="gr_channel")

    st.markdown("### 🎯 Informasi Tambahan")
    col1, col2 = st.columns(2)
    with col1:
        current_goal = st.text_input("Target utama kamu", placeholder="Contoh: Capai 1.000 subscriber, monetisasi AdSense")
        content_freq = st.selectbox("Frekuensi upload saat ini", ["1x seminggu", "2x seminggu", "3x seminggu", "Setiap hari", "Belum konsisten"])
    with col2:
        channel_age = st.selectbox("Umur channel", ["Baru (<3 bulan)", "Berkembang (3–12 bulan)", "Established (>1 tahun)"])
        biggest_challenge = st.text_input("Tantangan terbesar saat ini", placeholder="Contoh: Views rendah, susah dapat subscriber")

    if st.button("🗺️ Generate Growth Roadmap 30 Hari", use_container_width=True, type="primary"):
        if not channel_url_gr:
            st.warning("Masukkan link channel YouTube!")
            st.stop()

        with st.spinner("Mengambil data channel..."):
            try:
                youtube = build('youtube', 'v3', developerKey=API_KEY)
                handle_match = re.search(r'youtube\.com\/@([\w.-]+)', channel_url_gr)
                channel_id = None
                if handle_match:
                    sr = youtube.search().list(part="snippet", q=handle_match.group(1), type="channel", maxResults=1).execute()
                    if sr['items']: channel_id = sr['items'][0]['snippet']['channelId']
                ch_match = re.search(r'youtube\.com\/channel\/(UC[\w-]+)', channel_url_gr)
                if ch_match: channel_id = ch_match.group(1)

                if not channel_id:
                    st.error("Channel tidak ditemukan.")
                    st.stop()

                ch_resp = youtube.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
                if not ch_resp['items']:
                    st.error("Channel tidak ditemukan.")
                    st.stop()

                ch = ch_resp['items'][0]
                ch_name = ch['snippet']['title']
                subscribers = int(ch['statistics'].get('subscriberCount', 0))
                total_views = int(ch['statistics'].get('viewCount', 0))
                total_videos = int(ch['statistics'].get('videoCount', 0))
                playlist_id = ch['contentDetails']['relatedPlaylists']['uploads']

                pl_resp = youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=10).execute()
                video_ids = [i['contentDetails']['videoId'] for i in pl_resp['items']]
                vids_resp = youtube.videos().list(part="snippet,statistics", id=','.join(video_ids)).execute()

                videos_gr = []
                for v in vids_resp['items']:
                    stats = v.get('statistics', {})
                    views = int(stats.get('viewCount', 0))
                    likes = int(stats.get('likeCount', 0))
                    comments = int(stats.get('commentCount', 0))
                    eng = ((likes + comments) / views * 100) if views > 0 else 0
                    videos_gr.append({"title": v['snippet']['title'], "views": views, "engagement": eng})

                avg_eng = sum(v['engagement'] for v in videos_gr) / len(videos_gr) if videos_gr else 0
                avg_views = sum(v['views'] for v in videos_gr) / len(videos_gr) if videos_gr else 0

            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        st.success(f"✅ Data channel **{ch_name}** berhasil diambil!")
        st.divider()

        # --- OVERVIEW ---
        st.subheader(f"📊 Kondisi Channel Saat Ini: {ch_name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Subscribers", f"{subscribers:,}")
        c2.metric("Total Video", f"{total_videos:,}")
        c3.metric("Avg Views", f"{int(avg_views):,}")
        c4.metric("Avg Engagement", f"{avg_eng:.2f}%")

        # Grade channel
        if subscribers < 100: ch_grade, ch_color = "Pemula 🌱", "red"
        elif subscribers < 1000: ch_grade, ch_color = "Berkembang 🌿", "orange"
        elif subscribers < 10000: ch_grade, ch_color = "Growing 🌳", "blue"
        elif subscribers < 100000: ch_grade, ch_color = "Established 🏆", "green"
        else: ch_grade, ch_color = "Top Creator 🚀", "green"

        st.markdown(f"**Level Channel:** :{ch_color}[{ch_grade}]")
        st.divider()

        # --- GENERATE ROADMAP ---
        st.subheader("🗺️ Roadmap 30 Hari")

        with st.spinner("Groq AI menyusun roadmap personalmu..."):
            roadmap_prompt = f"""Kamu adalah coach YouTube profesional berpengalaman lebih dari 10 tahun.
Buat roadmap pertumbuhan channel YouTube yang sangat spesifik dan actionable untuk 30 hari ke depan.

DATA CHANNEL:
- Nama: {ch_name}
- Subscribers: {subscribers:,}
- Total video: {total_videos}
- Rata-rata views per video: {int(avg_views):,}
- Rata-rata engagement: {avg_eng:.2f}%
- Level: {ch_grade}
- Umur channel: {channel_age}
- Frekuensi upload saat ini: {content_freq}
- Target utama: {current_goal or 'Tidak disebutkan'}
- Tantangan terbesar: {biggest_challenge or 'Tidak disebutkan'}

10 video terakhir:
{chr(10).join([f"- {v['title']} ({v['views']:,} views, {v['engagement']:.2f}% eng)" for v in videos_gr[:10]])}

Buat roadmap dengan format:

## 🎯 Diagnosis Channel
Analisis jujur kondisi channel saat ini — kekuatan dan kelemahan utama dalam 3–4 kalimat.

## 📅 MINGGU 1 (Hari 1–7): FONDASI
### Target minggu ini:
### Aksi harian yang harus dilakukan:
- Hari 1:
- Hari 2:
- Hari 3:
- Hari 4:
- Hari 5:
- Hari 6–7:
### KPI yang harus dicapai di akhir minggu 1:

## 📅 MINGGU 2 (Hari 8–14): AKSELERASI
### Target minggu ini:
### Fokus utama:
### 3 konten yang harus dibuat:
### KPI yang harus dicapai:

## 📅 MINGGU 3 (Hari 15–21): OPTIMASI
### Target minggu ini:
### Fokus utama:
### 3 konten yang harus dibuat:
### KPI yang harus dicapai:

## 📅 MINGGU 4 (Hari 22–30): SCALING
### Target minggu ini:
### Fokus utama:
### 3 konten yang harus dibuat:
### KPI yang harus dicapai di akhir 30 hari:

## ⚠️ 3 Hal yang JANGAN Dilakukan (berdasarkan kondisi channel ini)

## 🏆 Milestone Realistis 30 Hari
Prediksi subscribers, views, dan engagement di akhir 30 hari jika roadmap dijalankan konsisten.

Tulis dalam Bahasa Indonesia. Sangat spesifik, personal, dan actionable."""

            roadmap_result, err = call_groq(roadmap_prompt, max_tokens=2000)

        if roadmap_result:
            st.markdown(roadmap_result)
            st.divider()

            # --- DAILY CHECKLIST ---
            st.subheader("✅ Daily Checklist Creator")
            st.markdown("Rutinitas harian yang harus dilakukan selama 30 hari:")

            with st.spinner("Generating daily checklist..."):
                checklist_prompt = f"""Buat daily checklist yang ringkas untuk creator YouTube dengan kondisi:
- Subscribers: {subscribers:,}
- Avg engagement: {avg_eng:.2f}%
- Target: {current_goal or 'Tumbuh konsisten'}
- Frekuensi upload: {content_freq}

Buat checklist harian dalam 2 kategori:

## ⏰ Rutinitas Pagi (15 menit)
5 hal yang harus dilakukan setiap pagi sebelum aktivitas lain.

## 🌙 Rutinitas Malam (15 menit)
5 hal yang harus dilakukan setiap malam untuk evaluasi dan persiapan esok hari.

## 📊 Review Mingguan (30 menit setiap Minggu)
5 hal yang harus dievaluasi setiap minggu.

Tulis dalam Bahasa Indonesia, singkat dan langsung to the point."""

                checklist_result, err2 = call_groq(checklist_prompt, max_tokens=600)

            if checklist_result:
                st.markdown(checklist_result)
        else:
            st.error(f"Gagal generate roadmap: {err}")

elif mode == "Thumbnail Analyser 🖼️":
    st.subheader("🖼️ Thumbnail Analyser")
    st.markdown("Analisis kekuatan thumbnail video — dari URL kompetitor atau upload gambar sendiri.")

    if not GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY belum diisi di Streamlit Secrets.")
        st.stop()

    # --- INPUT MODE ---
    thumb_mode = st.radio(
        "Analisis thumbnail dari:",
        ["🔗 URL Video YouTube (kompetitor)", "📤 Upload Gambar Thumbnail"],
        horizontal=True
    )

    thumbnail_url = ""
    uploaded_thumb = None
    video_title_thumb = ""
    video_data_thumb = None

    if "🔗" in thumb_mode:
        video_url_thumb = st.text_input("Paste Link Video YouTube", placeholder="https://www.youtube.com/watch?v=...", key="thumb_url")
        if video_url_thumb and st.button("🔍 Ambil Thumbnail", key="fetch_thumb"):
            with st.spinner("Mengambil data video..."):
                video_data_thumb = analyze_virality(video_url_thumb)
                if video_data_thumb:
                    vid_id = extract_video_id(video_url_thumb)
                    thumbnail_url = f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg"
                    video_title_thumb = video_data_thumb['title']
                    st.session_state['thumb_url_data'] = {
                        "url": thumbnail_url,
                        "title": video_title_thumb,
                        "video_data": video_data_thumb
                    }
                else:
                    st.error("Video tidak ditemukan.")

        if 'thumb_url_data' in st.session_state:
            td = st.session_state['thumb_url_data']
            thumbnail_url = td['url']
            video_title_thumb = td['title']
            video_data_thumb = td['video_data']

    else:
        uploaded_thumb = st.file_uploader("Upload Gambar Thumbnail", type=["jpg", "jpeg", "png", "webp"])
        video_title_thumb = st.text_input("Judul Video (opsional)", placeholder="Judul video untuk konteks analisis")

    # Tampilkan thumbnail jika ada
    if thumbnail_url or uploaded_thumb:
        st.divider()
        st.markdown("### 🖼️ Preview Thumbnail")

        col_prev, col_info = st.columns([2, 1])
        with col_prev:
            if thumbnail_url:
                st.image(thumbnail_url, caption=video_title_thumb, use_container_width=True)
            elif uploaded_thumb:
                st.image(uploaded_thumb, caption="Thumbnail kamu", use_container_width=True)

        with col_info:
            if video_data_thumb:
                st.metric("Views", f"{video_data_thumb['views']:,}")
                st.metric("Engagement", f"{video_data_thumb['engagement']:.2f}%")
                st.metric("Grade", video_data_thumb['grade'])
                st.caption(f"📅 {video_data_thumb['published_at'][:10]}")

        st.divider()

        # --- ANALISIS THUMBNAIL ---
        st.markdown("### 🔍 Pilih Jenis Analisis")
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1: do_ctr = st.checkbox("📈 CTR Potential Score", value=True)
        with col_a2: do_design = st.checkbox("🎨 Design Element Analysis", value=True)
        with col_a3: do_improve = st.checkbox("🚀 Improvement Suggestions", value=True)

        if st.button("🖼️ Analisis Thumbnail Sekarang", use_container_width=True, type="primary"):

            # Konteks video untuk analisis
            video_context = ""
            if video_data_thumb:
                video_context = f"""
Data video:
- Judul: {video_data_thumb['title']}
- Views: {video_data_thumb['views']:,}
- Engagement: {video_data_thumb['engagement']:.2f}%
- Grade: {video_data_thumb['grade']}
- Tags: {', '.join(video_data_thumb['tags'][:10]) if video_data_thumb['tags'] else 'tidak ada'}
"""
            elif video_title_thumb:
                video_context = f"Judul video: {video_title_thumb}"

            st.divider()
            st.subheader("📊 Hasil Analisis Thumbnail")

            if do_ctr:
                with st.spinner("Menghitung CTR Potential Score..."):
                    ctr_prompt = f"""Kamu adalah YouTube thumbnail expert dan CTR optimization specialist.
Analisis potensi CTR thumbnail berdasarkan informasi berikut:

{video_context}
URL thumbnail: {thumbnail_url if thumbnail_url else "User upload (tidak bisa diakses langsung)"}

Berikan penilaian CTR Potential Score berdasarkan best practices industri:

## 📈 CTR Potential Score: X/100

### Breakdown Skor per Elemen:
- Daya tarik visual (0–25): X/25 — [penjelasan]
- Keterbacaan teks (0–20): X/20 — [penjelasan]
- Relevansi dengan judul (0–20): X/20 — [penjelasan]
- Emosi & curiosity gap (0–20): X/20 — [penjelasan]
- Diferensiasi dari kompetitor (0–15): X/15 — [penjelasan]

### Grade CTR:
- 85–100: Excellent 🏆 — Thumbnail kelas dunia
- 70–84: Good 🔥 — Di atas rata-rata
- 50–69: Average ✅ — Perlu peningkatan
- <50: Poor ⚠️ — Perlu redesign

Berikan grade dan penjelasan singkat mengapa.
Tulis dalam Bahasa Indonesia."""

                    ctr_result, err = call_groq(ctr_prompt, max_tokens=600)

                if ctr_result:
                    with st.expander("📈 CTR Potential Score", expanded=True):
                        st.markdown(ctr_result)
                else:
                    st.error(f"Gagal: {err}")

            if do_design:
                with st.spinner("Menganalisis elemen desain..."):
                    design_prompt = f"""Kamu adalah YouTube thumbnail designer profesional.
Analisis elemen desain thumbnail berdasarkan:

{video_context}

Berikan analisis mendalam:

## 🎨 Analisis Elemen Desain

### 🔤 Teks & Typography
Apakah thumbnail menggunakan teks? Evaluasi: ukuran, keterbacaan, kontras, jumlah kata.
Best practice: maksimal 3–5 kata, ukuran besar, kontras tinggi.

### 🎭 Ekspresi & Manusia
Apakah ada wajah/ekspresi manusia? Wajah ekspresif meningkatkan CTR hingga 38%.
Evaluasi kekuatan emosi yang ditampilkan.

### 🌈 Warna & Kontras
Evaluasi skema warna. Warna cerah dan kontras tinggi terbukti meningkatkan CTR.
Apakah thumbnail mudah dilihat di layar kecil (mobile)?

### 📐 Komposisi & Layout
Rule of thirds, focal point, negative space. Apakah mata penonton langsung tahu harus melihat ke mana?

### 🎯 Brand Consistency
Apakah ada elemen branding yang konsisten (warna khas, font, logo)?

Tulis dalam Bahasa Indonesia, spesifik dan konstruktif."""

                    design_result, err = call_groq(design_prompt, max_tokens=700)

                if design_result:
                    with st.expander("🎨 Design Element Analysis", expanded=True):
                        st.markdown(design_result)
                else:
                    st.error(f"Gagal: {err}")

            if do_improve:
                with st.spinner("Generating improvement suggestions..."):
                    improve_prompt = f"""Kamu adalah YouTube growth hacker dan thumbnail specialist.
Berikan rekomendasi perbaikan thumbnail yang sangat konkret berdasarkan:

{video_context}

## 🚀 Rekomendasi Perbaikan Thumbnail

### 🔴 Perbaikan Prioritas Tinggi (lakukan segera)
3 perubahan yang paling berdampak pada CTR — spesifik dan langsung bisa dieksekusi.

### 🟡 Perbaikan Prioritas Sedang
3 perbaikan tambahan untuk memaksimalkan CTR.

### ✅ Yang Sudah Baik (pertahankan)
2–3 elemen yang sudah efektif dan harus dipertahankan.

### 🖼️ Deskripsi Visual Thumbnail Ideal
Deskripsikan seperti apa thumbnail yang ideal untuk video ini — cukup detail sehingga designer bisa langsung membuatnya.
Format: Background, elemen utama, teks, warna, ekspresi, komposisi.

### 🛠️ Tools yang Disarankan
2–3 tools gratis/murah untuk membuat thumbnail berkualitas tinggi.

Tulis dalam Bahasa Indonesia, actionable dan spesifik."""

                    improve_result, err = call_groq(improve_prompt, max_tokens=800)

                if improve_result:
                    with st.expander("🚀 Improvement Suggestions", expanded=True):
                        st.markdown(improve_result)
                else:
                    st.error(f"Gagal: {err}")

            st.divider()
            st.success("✅ Analisis selesai! Gunakan insight ini untuk membuat thumbnail yang lebih kuat.")
            st.caption("⚠️ Analisis ini berbasis deskripsi konteks video — untuk hasil lebih akurat, pastikan judul dan data video diisi lengkap.")

    else:
        st.info("👆 Pilih sumber thumbnail di atas untuk memulai analisis.")
