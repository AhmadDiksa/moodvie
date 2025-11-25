import streamlit as st
import google.generativeai as genai
import requests
import os
import json
from dotenv import load_dotenv

# --- 1. KONFIGURASI & SETUP ---
# Memuat environment variables
load_dotenv()

# Mengambil API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY") or st.secrets.get("TMDB_API_KEY")

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="MoodCine - AI Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# Konfigurasi Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("Gemini API Key tidak ditemukan. Silakan atur di file .env atau st.secrets.")

# --- 2. FUNGSI LAYANAN API (SERVICE LAYER) ---

def get_gemini_mood_analysis(text):
    """Menganalisis teks input untuk mendapatkan mood dan tema."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Analisis input pengguna berikut tentang perasaan atau preferensi film mereka.
    Berikan ringkasan singkat (maksimal 3 kalimat) tentang emosi utama, tema yang diinginkan, dan genre yang cocok.
    Gunakan Bahasa Indonesia.
    
    Input Pengguna: "{text}"
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error Analisis Mood: {e}")
        return None

def get_gemini_recommendations(mood_summary):
    """Mendapatkan rekomendasi film dalam format JSON berdasarkan analisis mood."""
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    prompt = f"""
    Berdasarkan analisis mood ini: "{mood_summary}",
    Rekomendasikan 4 sampai 6 film yang sangat cocok.
    
    Kembalikan HANYA format JSON valid dengan struktur berikut:
    [
        {{
            "title": "Judul Film (Tahun)",
            "reason": "Alasan singkat mengapa film ini cocok dengan mood (1 kalimat)"
        }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error Rekomendasi: {e}")
        return []

@st.cache_data
def get_tmdb_details(movie_title):
    """Mencari detail film dari TMDB berdasarkan judul."""
    if not TMDB_API_KEY:
        return None
        
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": movie_title,
        "language": "id-ID"
    }
    
    try:
        response = requests.get(search_url, params=params)
        data = response.json()
        
        if data['results']:
            movie = data['results'][0] # Ambil hasil teratas
            return {
                "id": movie['id'],
                "title": movie['title'],
                "overview": movie['overview'],
                "release_date": movie.get('release_date', 'N/A'),
                "rating": movie['vote_average'],
                "poster_path": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie['poster_path'] else "https://via.placeholder.com/500x750?text=No+Poster"
            }
        return None
    except Exception as e:
        # st.error(f"TMDB Error: {e}") # Optional logging
        return None

def get_creative_content(movie_title, user_mood):
    """Membuat konten kreatif (trailer script) khusus untuk user."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Pengguna sedang merasa: "{user_mood}".
    Film yang dipilih: "{movie_title}".
    
    Tuliskan sebuah narasi pendek (intro trailer) untuk film ini yang dipersonalisasi agar terdengar sangat relevan dengan perasaan pengguna saat ini.
    Buatlah puitis, dramatis, atau lucu sesuai dengan mood pengguna. Maksimal 100 kata. Bahasa Indonesia.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Gagal memuat konten kreatif."

# --- 3. KOMPONEN UI (MODAL) ---

@st.dialog("Detail & Pengalaman Mood", width="large")
def show_movie_modal(movie_data, mood_analysis):
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.image(movie_data['poster_path'], use_container_width=True)
    
    with c2:
        st.header(movie_data['title'])
        st.caption(f"Rilis: {movie_data['release_date']} | Rating: ⭐ {movie_data['rating']}/10")
        st.markdown(f"**Sinopsis:**\n{movie_data['overview']}")
        
        st.divider()
        
        st.subheader("✨ Khusus Untuk Mood Anda")
        with st.spinner("Sedang meracik kata-kata..."):
            # Panggilan Gemini ke-3 (Real-time saat modal dibuka)
            creative_text = get_creative_content(movie_data['title'], mood_analysis)
            st.info(creative_text, icon="🤖")

# --- 4. LOGIKA APLIKASI UTAMA ---

def main():
    # Header
    st.title("🎬 MoodCine")
    st.markdown("""
    <style>
    .stTextArea textarea {font-size: 16px;}
    </style>
    **Temukan film yang mengerti perasaanmu.** Ceritakan apa yang sedang kamu rasakan, 
    dan biarkan AI memilihkan tontonan terbaik.
    """, unsafe_allow_html=True)

    # Inisialisasi Session State
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'mood_analysis' not in st.session_state:
        st.session_state.mood_analysis = ""

    # Input Area
    with st.container():
        user_input = st.text_area("Bagaimana perasaanmu hari ini? (Contoh: Saya lelah bekerja dan ingin tertawa, atau saya sedang sedih dan butuh inspirasi)", height=100)
        
        c_btn, c_reset = st.columns([1, 6])
        with c_btn:
            analyze_btn = st.button("Cari Film 🎥", type="primary")
        with c_reset:
            if st.button("Reset"):
                st.session_state.results = None
                st.session_state.mood_analysis = ""
                st.rerun()

    # Proses Utama
    if analyze_btn and user_input:
        if not GEMINI_API_KEY or not TMDB_API_KEY:
            st.error("Mohon lengkapi API Key di file .env terlebih dahulu.")
        else:
            with st.spinner("Sedang menganalisis emosi dan mencari film..."):
                # Langkah 1: Analisis Mood
                mood_summary = get_gemini_mood_analysis(user_input)
                st.session_state.mood_analysis = mood_summary
                
                if mood_summary:
                    # Langkah 2: Dapatkan Rekomendasi (JSON)
                    raw_recs = get_gemini_recommendations(mood_summary)
                    
                    final_movies = []
                    # Langkah 3: Perkaya dengan Data TMDB
                    for rec in raw_recs:
                        # Hapus tahun dari judul untuk pencarian TMDB yang lebih akurat jika perlu
                        clean_title = rec['title'].split('(')[0].strip() 
                        tmdb_data = get_tmdb_details(clean_title)
                        
                        if tmdb_data:
                            # Gabungkan data AI dan data TMDB
                            combined_data = {**tmdb_data, "reason": rec['reason']}
                            final_movies.append(combined_data)
                    
                    st.session_state.results = final_movies
                else:
                    st.warning("Gagal menganalisis mood. Coba kalimat lain.")

    # Tampilan Hasil
    if st.session_state.mood_analysis and st.session_state.results:
        st.divider()
        st.success(f"**Analisis Mood:** {st.session_state.mood_analysis}")
        
        st.subheader("Rekomendasi Pilihan")
        
        # Grid Layout (misal 3 kolom)
        cols = st.columns(3)
        
        for idx, movie in enumerate(st.session_state.results):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.image(movie['poster_path'], use_container_width=True)
                    st.markdown(f"### {movie['title']}")
                    st.caption(f"⭐ {movie['rating']}")
                    st.write(f"💡 *{movie['reason']}*")
                    
                    # Tombol untuk membuka Modal
                    if st.button("Lihat Detail ✨", key=f"btn_{movie['id']}"):
                        show_movie_modal(movie, st.session_state.mood_analysis)

if __name__ == "__main__":
    main()