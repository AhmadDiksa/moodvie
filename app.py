import streamlit as st
import google.generativeai as genai
import requests
import json
import os
from dotenv import load_dotenv

# --- 1. CONFIG ---
st.set_page_config(page_title="Moodie AI (Fixed)", page_icon="🎬", layout="wide")
load_dotenv()

# --- 2. FACTORY FUNCTION UNTUK TOOLS ---
# Kita membungkus tools di dalam fungsi ini agar API Key "terkunci" di dalamnya.
# Jadi Gemini tidak perlu mencari session state.

def create_tools(tmdb_api_key):
    
    # Helper request sederhana
    def make_request(endpoint, params={}):
        base_url = "https://api.themoviedb.org/3"
        # Menyuntikkan API Key ke setiap request
        params['api_key'] = tmdb_api_key 
        params['language'] = 'id-ID'
        
        try:
            print(f"DEBUG: Requesting {endpoint}") # Cek terminal vscode
            response = requests.get(f"{base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            return {"error": str(e)}

    # --- DEFINISI TOOLS ---
    
    def cari_film_berdasarkan_mood(mood: str):
        """
        Mencari rekomendasi film berdasarkan mood/genre.
        Args: mood (str) - contoh: 'sedih', 'bahagia', 'tegang', 'takut', 'aksi'.
        """
        genre_map = {
            "sedih": 18, "bahagia": 35, "lucu": 35, 
            "tegang": 53, "takut": 27, "seram": 27, 
            "romantis": 10749, "aksi": 28, "anime": 16
        }
        
        # Default Drama (18) jika mood tidak ketemu
        genre_id = 18
        for k, v in genre_map.items():
            if k in mood.lower():
                genre_id = v
                break
        
        # Ubah sort_by dari 'popularity.desc' ke 'vote_average.desc'
        # Tambahkan 'vote_count.gte' untuk memastikan ratingnya reliable (dari minimal 300 suara)
        params = {"with_genres": genre_id, "sort_by": "vote_average.desc", "vote_count.gte": 300}
        data = make_request("/discover/movie", params)

        if "results" in data:
            return json.dumps(data['results'][:5])
        return json.dumps(data)

    def cari_judul_spesifik(judul: str):
        """
        Mencari detail info film tertentu berdasarkan judul.
        Args: judul (str) - Judul film.
        """
        data = make_request("/search/movie", {"query": judul})
        if "results" in data:
            return json.dumps(data['results'][:3])
        return json.dumps(data)

    def cek_film_trending(waktu: str = "week"):
        """
        Melihat film yang sedang populer/trending.
        Args: waktu (str) - 'day' atau 'week'.
        """
        safe_waktu = 'day' if waktu == 'day' else 'week'
        data = make_request(f"/trending/movie/{safe_waktu}")
        if "results" in data:
            return json.dumps(data['results'][:5])
        return json.dumps(data)

    def get_watch_providers(movie_id: int):
        """
        Mendapatkan daftar platform streaming untuk sebuah film berdasarkan ID-nya.
        Args: movie_id (int) - ID unik dari film di TMDB.
        """
        data = make_request(f"/movie/{movie_id}/watch/providers")
        # Fokus pada hasil untuk Indonesia (ID)
        if "results" in data and "ID" in data["results"]:
            providers = data["results"]["ID"]
            # Ambil dari 'flatrate' (langganan) dulu, lalu 'buy' atau 'rent'
            provider_names = []
            if "flatrate" in providers:
                provider_names.extend([p['provider_name'] for p in providers['flatrate']])
            return json.dumps(list(set(provider_names))[:3]) # Ambil 3 teratas unik
        return json.dumps([]) # Kembalikan list kosong jika tidak ada

    # Kembalikan list fungsi yang sudah siap dipakai
    return [cari_film_berdasarkan_mood, cari_judul_spesifik, cek_film_trending, get_watch_providers]

# --- 3. SYSTEM INSTRUCTION ---

SYSTEM_PROMPT = """
Anda adalah Moodie AI. Tugas: Rekomendasi film menggunakan Tools.

ATURAN:
1. Panggil `cari_film_berdasarkan_mood` jika user curhat perasaan.
2. Panggil `cari_judul_spesifik` jika user tanya film tertentu.
3. Panggil `cek_film_trending` jika user tanya yang lagi hits.
4. Dari hasil pencarian film, ambil `id` film yang paling relevan.
5. Panggil tool `get_watch_providers` menggunakan `id` film untuk mencari platform streaming.
6. PENTING: Jika hasil dari `get_watch_providers` adalah list kosong `[]`, artinya film tidak tersedia. Ulangi proses dari langkah 4 dengan film lain dari hasil pencarian awal. JANGAN merekomendasikan film yang tidak punya platform streaming.
7. Selalu awali jawaban teks dengan kalimat "Tentu, ini dia rekomendasi film yang cocok untukmu:" sebelum masuk ke detail film.
8. Untuk `poster_url`, gabungkan 'https://image.tmdb.org/t/p/w500' dengan `poster_path` dari tool. Jika `poster_path` null, gunakan string kosong.
9. Gunakan data JSON dari semua tools untuk menjawab. Jangan mengarang.
10. FORMAT OUTPUT WAJIB ADA JSON BLOCK:

<<MOVIE_JSON_START>>
{
  "title": "Judul Film",
  "year": "Tahun",
  "poster_url": "https://image.tmdb.org/t/p/w500/path_dari_tool",
  "rating": "Rating",
  "summary": "Ringkasan cerita",
  "platform": "Streaming Platform (Prediksi)",
  "reason": "Alasan rekomendasi"
}
<<MOVIE_JSON_END>>
"""

# --- 4. PARSER & UI HELPERS ---

def parse_final_response(text):
    s_tag = "<<MOVIE_JSON_START>>"
    e_tag = "<<MOVIE_JSON_END>>"
    if s_tag in text and e_tag in text:
        s = text.find(s_tag)
        e = text.find(e_tag)
        json_str = text[s+len(s_tag):e].strip()
        try:
            return text[:s].strip(), json.loads(json_str)
        except: pass
    return text, None

def render_card(data):
    poster_url = data.get('poster_url')
    # Fallback jika URL poster tidak ada atau kosong
    if not poster_url:
        poster_url = "https://via.placeholder.com/500x750.png?text=No+Image"
    
    platforms = data.get('platform', [])
    platform_html = ""
    if platforms:
        # Pastikan 'platforms' adalah list, bukan string tunggal
        if isinstance(platforms, str):
            platforms = [platforms]
            
        # Sederhanakan nama platform dan gabungkan dengan koma
        simple_names = [p.replace(" Plus", "+").split(' ')[0] for p in platforms]
        platform_list_str = ", ".join(simple_names)
        platform_html = f"<div style='margin-top:10px; font-size:13px; color:#9CA3AF;'>Tersedia di: <span style='color:#D1D5DB; font-weight:500;'>{platform_list_str}</span></div>"

    st.markdown(f"""
    <div style="background:#1E2026; padding:15px; border-radius:10px; border:1px solid #4B5563; margin-top:10px; display:flex; gap: 20px;">
        <div style="flex-shrink:0; width:150px;">
            <img src="{poster_url}" style="width:100%; border-radius:8px;">
        </div>
        <div style="flex-grow:1;">
            <h3 style="color:#fff; margin:0; margin-bottom:5px;">{data.get('title')} <span style="font-size:0.8em; color:#9CA3AF">({data.get('year')})</span></h3>
            <div style="display:flex; gap:10px; margin:5px 0; font-size:14px; color:#34D399;">
                <span>⭐ {data.get('rating', 'N/A')}</span>
            </div>
            <p style="color:#D1D5DB; font-size:14px; margin-top:10px;">{data.get('summary')}</p>
            {platform_html}
            <small style="color:#60A5FA; display:block; margin-top:15px;">💡 {data.get('reason')}</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN APP ---

with st.sidebar:
    st.title("⚙️ Konfigurasi")
    
    # Input API Key
    google_key = st.text_input("Google Gemini API Key", type="password", value=os.getenv("API_KEY", ""))
    
    # Input TMDB Key (Gunakan API Key pendek v3, bukan Token panjang)
    tmdb_key = st.text_input("TMDB API Key (v3 Auth)", type="password", value=os.getenv("TMDB_API_KEY", ""), help="Pakai API Key pendek (bukan Read Access Token)")
    
    if st.button("🗑️ Reset / Apply"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

if not google_key or not tmdb_key:
    st.warning("⚠️ Mohon isi Google API Key DAN TMDB API Key di sidebar.")
    st.stop()

# Init Model & Chat
if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    try:
        genai.configure(api_key=google_key)
        
        # Buat tools dengan menyuntikkan key TMDB
        my_tools = create_tools(tmdb_key)
        
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=SYSTEM_PROMPT,
            tools=my_tools
        )
        st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
        st.session_state.messages = []
        st.toast("System Ready! Tools loaded.", icon="🚀")
    except Exception as e:
        st.error(f"Gagal inisialisasi: {e}")
        st.stop()

# Tampilkan pesan sambutan jika chat masih kosong
if not st.session_state.messages:
    welcome_message = "Halo! 👋 Saya Moodie AI, asisten sinematik pribadimu. Lagi suntuk, butuh semangat, atau sekadar ingin nonton yang lagi trending? Ceritakan saja perasaanmu, dan aku akan carikan film yang pas. Mau coba?"
    with st.chat_message("assistant"):
        st.markdown(welcome_message)
    # Simpan pesan sambutan ke history agar tidak muncul lagi
    st.session_state.messages.append({"role": "assistant", "content": welcome_message, "data": None})


# Tampilkan Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("data"): render_card(msg["data"])

# Input User
if prompt := st.chat_input("Contoh: Film horor terbaru, atau cari film Interstellar..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("🔄 *Sedang menghubungi TMDB...*")
        
        try:
            # Kirim pesan
            response = st.session_state.chat_session.send_message(prompt)
            
            # Cek apakah function terpanggil (dari history)
            tool_msg = ""
            try:
                last_req = st.session_state.chat_session.history[-2]
                if hasattr(last_req.parts[0], 'function_call'):
                    fname = last_req.parts[0].function_call.name
                    tool_msg = f"`🛠️ Tool Used: {fname}`"
            except: pass

            text, data = parse_final_response(response.text)
            
            placeholder.empty()
            if tool_msg: st.caption(tool_msg)
            st.markdown(text)
            if data: render_card(data)
            
            st.session_state.messages.append({"role": "assistant", "content": text, "data": data})
            
        except Exception as e:
            placeholder.error(f"Error: {e}\n\nPastikan TMDB API Key benar.")