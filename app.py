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
# Menggunakan os.getenv untuk konsistensi, st.secrets hanya untuk deployment Streamlit
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY") or st.secrets.get("TMDB_API_KEY")

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="MoodCine - AI Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# Inisialisasi Klien Gemini
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Gunakan model di sini agar tidak perlu dipanggil berulang-ulang
        MODEL_FLASH = genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        st.error(f"Gagal mengkonfigurasi Gemini API: {e}")
        MODEL_FLASH = None
else:
    st.error("Gemini API Key tidak ditemukan. Silakan atur di file .env atau st.secrets.")
    MODEL_FLASH = None

# Base URL untuk poster TMDB
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
NO_POSTER_URL = "https://via.placeholder.com/500x750?text=No+Poster"

# --- 2. FUNGSI LAYANAN API (SERVICE LAYER) ---

def get_gemini_mood_analysis(text):
    """Menganalisis teks input untuk mendapatkan mood dan tema."""
    if not MODEL_FLASH:
        return None
    
    prompt = f"""
    Analisis input pengguna berikut tentang perasaan atau preferensi film mereka.
    Berikan ringkasan singkat (maksimal 3 kalimat) tentang emosi utama, tema yang diinginkan, dan genre yang cocok.
    Gunakan Bahasa Indonesia.
    
    Input Pengguna: "{text}"
    """
    try:
        response = MODEL_FLASH.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error Analisis Mood: Gagal mendapatkan respons dari Gemini. Detail: {e}")
        return None

def get_gemini_recommendations(mood_summary):
    """Mendapatkan rekomendasi film dalam format JSON berdasarkan analisis mood."""
    if not GEMINI_API_KEY: # Cek API Key lagi, karena konfigurasi model bisa gagal
        return []
    
    # Inisialisasi model lagi di sini untuk memastikan konfigurasi JSON
    model_json = genai.GenerativeModel(
        'gemini-2.0-flash', 
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Judul Film (Tahun)"},
                        "reason": {"type": "string", "description": "Alasan singkat mengapa film ini cocok dengan mood (1 kalimat)"}
                    },
                    "required": ["title", "reason"]
                }
            }
        }
    )

    prompt = f"""
    Berdasarkan analisis mood ini: "{mood_summary}",
    Rekomendasikan 4 sampai 6 film yang sangat cocok.
    
    Kembalikan HANYA format JSON valid sesuai skema yang diminta.
    """
    try:
        response = model_json.generate_content(prompt)
        # Tambahkan penanganan jika JSON kosong atau tidak valid
        if response.text.strip():
            return json.loads(response.text)
        else:
            st.warning("Gemini mengembalikan JSON kosong.")
            return []
    except json.JSONDecodeError as e:
        st.error(f"Error Rekomendasi: Gagal mem-parse JSON. Coba lagi. Detail: {e}")
        return []
    except Exception as e:
        st.error(f"Error Rekomendasi: Gagal mendapatkan respons dari Gemini. Detail: {e}")
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
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status() # Cek HTTP error
        data = response.json()
        
        if data['results']:
            movie = data['results'][0] # Ambil hasil teratas
            overview = movie.get('overview')
            if not overview:
                overview = 'Sinopsis tidak tersedia.'
            return {
                "id": movie['id'],
                "title": movie['title'],
                "overview": overview,
                "release_date": movie.get('release_date', 'N/A') or 'N/A',
                "rating": movie['vote_average'],
                "poster_path": f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}" if movie['poster_path'] else NO_POSTER_URL
            }
        return None
    except requests.exceptions.RequestException as e:
        # st.error(f"TMDB Network Error: {e}") # Optional logging
        return None
    except Exception as e:
        # st.error(f"TMDB General Error: {e}") # Optional logging
        return None

def get_creative_content(movie_title, user_mood):
    """Membuat konten kreatif (trailer script) khusus untuk user."""
    if not MODEL_FLASH:
        return "Gagal memuat konten kreatif karena masalah API."
        
    prompt = f"""
    Pengguna sedang merasa: "{user_mood}".
    Film yang dipilih: "{movie_title}".
    
    Tuliskan sebuah narasi pendek (intro trailer) untuk film ini yang dipersonalisasi agar terdengar sangat relevan dengan perasaan pengguna saat ini.
    Buatlah puitis, dramatis, atau lucu sesuai dengan mood pengguna. Maksimal 100 kata. Bahasa Indonesia.
    """
    try:
        response = MODEL_FLASH.generate_content(prompt)
        return response.text
    except Exception:
        return "Gagal memuat konten kreatif."

# --- 3. KOMPONEN UI (MODAL) ---

def handle_modal_close():
    """Fungsi untuk membersihkan session state setelah modal ditutup."""
    st.session_state.selected_movie_id = None
    st.rerun()

@st.dialog("Detail & Pengalaman Mood", width="large")
def show_movie_modal(movie_data, mood_analysis):
    # Panggil fungsi cleanup saat tombol Tutup/Esc ditekan
    st.session_state.modal_open = True
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.image(movie_data['poster_path'], use_container_width=True)
    
    with c2:
        st.header(movie_data['title'])
        # Menggunakan format tanggal yang lebih baik jika memungkinkan
        release_year = movie_data['release_date'].split('-')[0] if movie_data['release_date'] != 'N/A' else 'N/A'
        st.caption(f"Tahun: {release_year} | Rating: ⭐ **{movie_data['rating']:.1f}**/10")
        # Ensure overview is not None or empty string
        overview_text = movie_data.get('overview') or 'Sinopsis tidak tersedia.'
        st.write(f"**Sinopsis:**")
        st.write(overview_text)
        
        st.divider()
        
        st.subheader("✨ Khusus Untuk Mood Anda")
        with st.spinner("Sedang meracik kata-kata..."):
            # Panggilan Gemini ke-3 (Real-time saat modal dibuka)
            creative_text = get_creative_content(movie_data['title'], mood_analysis)
            st.info(creative_text, icon="🤖")

    # Tombol tutup manual (untuk jaga-jaga)
    if st.button("Tutup", key="close_modal_btn"):
        handle_modal_close()

# --- 4. LOGIKA APLIKASI UTAMA ---

def main():
    # Header
    st.title("🎬 MoodCine - AI Movie Recommender")
    st.markdown("""
    **Temukan film yang mengerti perasaanmu.** Ceritakan apa yang sedang kamu rasakan, 
    dan biarkan AI memilihkan tontonan terbaik.
    """, unsafe_allow_html=True)

    # Inisialisasi Session State
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'mood_analysis' not in st.session_state:
        st.session_state.mood_analysis = ""
    if 'selected_movie_id' not in st.session_state:
        st.session_state.selected_movie_id = None
    # Tambahkan state untuk kontrol modal yang lebih baik
    if 'modal_open' not in st.session_state:
        st.session_state.modal_open = False


    # Input Area
    with st.container():
        user_input = st.text_area(
            "Bagaimana perasaanmu hari ini? (Contoh: Saya lelah bekerja dan ingin tertawa, atau saya sedang sedih dan butuh inspirasi)", 
            height=100,
            value=st.session_state.get('last_input', '') # Mempertahankan input terakhir
        )
        
        c_btn, c_reset = st.columns([1, 6])
        with c_btn:
            analyze_btn = st.button("Cari Film 🎥", type="primary")
        with c_reset:
            # Fungsi reset yang lebih bersih
            def reset_app():
                st.session_state.results = None
                st.session_state.mood_analysis = ""
                st.session_state.selected_movie_id = None
                st.session_state.last_input = ""
                st.session_state.modal_open = False
                
            if st.button("Reset"):
                reset_app()
                st.rerun()

    # Proses Utama
    if analyze_btn and user_input:
        st.session_state.last_input = user_input # Simpan input terakhir
        
        if not GEMINI_API_KEY or not TMDB_API_KEY:
            st.error("Mohon lengkapi **Gemini API Key** dan **TMDB API Key** terlebih dahulu.")
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
                        # Membersihkan judul dari tahun dan spasi berlebihan
                        clean_title = rec['title'].split('(')[0].strip() 
                        tmdb_data = get_tmdb_details(clean_title)
                        
                        if tmdb_data:
                            # Gabungkan data AI dan data TMDB
                            combined_data = {**tmdb_data, "reason": rec['reason']}
                            final_movies.append(combined_data)
                    
                    st.session_state.results = final_movies
                    if not final_movies:
                        st.warning("Tidak ditemukan film yang cocok di database TMDB. Coba masukan mood yang lebih spesifik.")
                else:
                    st.session_state.results = None
                    st.warning("Gagal menganalisis mood. Coba kalimat lain.")
                
                # Rerun untuk menampilkan hasil
                st.rerun() 

    # Tampilan Hasil
    if st.session_state.mood_analysis and st.session_state.results:
        st.divider()
        st.success(f"**Analisis Mood Ditemukan:** {st.session_state.mood_analysis}")
        
        st.subheader("Rekomendasi Pilihan 🎬")
        
        # Grid Layout (misal 3 kolom)
        cols = st.columns(3)
        
        for idx, movie in enumerate(st.session_state.results):
            with cols[idx % 3]:
                # Menggunakan card dengan border
                with st.container(border=True):
                    st.image(movie['poster_path'], use_container_width=True)
                    st.markdown(f"**{movie['title']}**")
                    st.caption(f"⭐ **{movie['rating']:.1f}**") # Format rating satu desimal
                    st.markdown(f"💡 *{movie['reason']}*")
                    
                    # Tombol untuk membuka Modal
                    if st.button("Lihat Detail & Trailer Khusus ✨", key=f"btn_{movie['id']}"):
                        st.session_state.selected_movie_id = movie['id']
                        st.rerun()

    # Tampilkan modal detail jika movie dipilih
    if st.session_state.selected_movie_id:
        selected_movie = next((m for m in st.session_state.results if m['id'] == st.session_state.selected_movie_id), None)
        if selected_movie and not st.session_state.modal_open:
            # Memastikan modal_open di-set False saat modal ditutup
            show_movie_modal(selected_movie, st.session_state.mood_analysis)
            st.session_state.modal_open = False # Reset setelah modal tampil

if __name__ == "__main__":
    main()