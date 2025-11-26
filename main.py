# main.py
import streamlit as st
from dotenv import load_dotenv
import time

# Import modules
import styles
import ui
import services
import loader_page
import analysis_page # <--- IMPORT BARU

# SETUP
load_dotenv()
st.set_page_config(page_title="MoodCine AI", page_icon="🎬", layout="wide")

# STATE
if 'page' not in st.session_state: st.session_state.page = "input"
if 'user_prompt' not in st.session_state: st.session_state.user_prompt = ""
if 'analysis_data' not in st.session_state: st.session_state.analysis_data = None # Simpan data JSON analisis
if 'results' not in st.session_state: st.session_state.results = None

def main():
    ui.inject_style(styles.CINEMATIC_CSS)
    
    # --- PAGE 1: INPUT ---
    if st.session_state.page == "input":
        ui.render_header()
        user_text, btn_search = ui.render_search_area()
        
        if btn_search and user_text:
            st.session_state.user_prompt = user_text
            st.session_state.page = "loading"
            st.rerun()

    # --- PAGE 2: LOADING (PROCESS) ---
    elif st.session_state.page == "loading":
        loader_page.render()
        
        gemini_key, tmdb_key = services.configure_apis()
        if not gemini_key or not tmdb_key:
            st.error("API Key missing.")
            st.stop()
        else:
            time.sleep(2) # Delay estetik
            
            # 1. Analisis Mood (Dapatkan JSON)
            data = services.analyze_mood(st.session_state.user_prompt)
            st.session_state.analysis_data = data
            
            # Pindah ke halaman Analisis
            st.session_state.page = "analysis"
            st.rerun()

    # --- PAGE 3: ANALYSIS DASHBOARD ---
    elif st.session_state.page == "analysis":
        # Jangan render header besar, biarkan fokus ke dashboard
        
        # Render Halaman Analisis
        is_generated = analysis_page.render(st.session_state.analysis_data)
        
        if is_generated:
            with st.spinner("Curating your personal watchlist..."):
                gemini_key, tmdb_key = services.configure_apis()
                
                # Gunakan summary text dari hasil analisis sebelumnya untuk mencari film
                mood_summary = st.session_state.analysis_data.get('summary_text', st.session_state.user_prompt)
                
                # 2. Cari Rekomendasi
                recs = services.get_recommendations(mood_summary)
                
                final_data = []
                for r in recs:
                    details = services.search_tmdb_details(r['title'], tmdb_key)
                    if details:
                        # Gabungkan reason AI
                        details['reason'] = r['reason']
                        final_data.append(details)
                
                st.session_state.results = final_data
                st.session_state.page = "results"
                st.rerun()

    # --- PAGE 4: RESULTS ---
    elif st.session_state.page == "results":
        ui.render_header()
        
        if st.sidebar.button("Reset Search") or st.button("Start Over", type="secondary"):
            st.session_state.page = "input"
            st.session_state.results = None
            st.session_state.analysis_data = None
            st.rerun()

        # Render Grid (Gunakan summary mood sebagai konteks teks)
        mood_context = st.session_state.analysis_data.get('detected_moods', ['Mood'])[0]
        ui.render_movie_grid(st.session_state.results, f"Mood: {mood_context}")

if __name__ == "__main__":
    main()