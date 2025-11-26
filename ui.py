# ui.py
import streamlit as st
import services 

def inject_style(css_string):
    st.markdown(css_string, unsafe_allow_html=True)

def render_header():
    """Header Minimalis Kiri Atas"""
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 10px; padding-top: 10px;'>
            <div style='background: linear-gradient(135deg, #dc2626, #7f1d1d); width: 35px; height: 35px; border-radius: 8px; display: flex; align-items: center; justify-content: center;'>
                <i class="fa-solid fa-film" style="color: white; font-size: 18px;"></i>
            </div>
            <div>
                <div style='font-weight: 700; font-size: 16px; line-height: 1.2; color: white;'>MoodCine AI</div>
                <div style='font-size: 10px; color: #64748b;'>Powered by Gemini & TMDB</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_header():
    """Header dengan Logo Kiri dan Tombol Restart Kanan"""
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 10px; padding-top: 10px;'>
            <div style='background: linear-gradient(135deg, #4f46e5, #9333ea); width: 35px; height: 35px; border-radius: 8px; display: flex; align-items: center; justify-content: center;'>
                <i class="fa-solid fa-film" style="color: white; font-size: 18px;"></i>
            </div>
            <div>
                <div style='font-weight: 700; font-size: 16px; line-height: 1.2; color: white;'>MoodCine AI</div>
                <div style='font-size: 10px; color: #64748b;'>Powered by Gemini 2.5 Flash & TMDB</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        # Tombol Start Over dummy (Action-nya dihandle logic main.py via st.rerun kalau mau functional)
        st.markdown("<div style='text-align:right; padding-top:15px;'><span class='header-restart'>Start Over</span></div>", unsafe_allow_html=True)

def render_custom_loader():
    """Menampilkan Animasi Loading Full Center"""
    st.markdown("""
        <div class="loading-container">
            <div class="custom-spinner"></div>
            <div class="loading-title">Decoding your emotions...</div>
            <div class="loading-subtitle">Our AI is extracting mood vectors and intensity.</div>
        </div>
    """, unsafe_allow_html=True)
    
def render_search_area():
    """Hero Section + Input Card Style"""
    
    # 1. Spacer agar konten turun ke tengah vertikal
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 2. Hero Text (Centered)
    st.markdown("<h1 style='text-align: center;'>How are you feeling?</h1>", unsafe_allow_html=True)
    st.markdown("""
        <p style='text-align: center;' class='subtext'>
        Tell us about your current mood, what kind of vibe you need, or simply vent.<br>
        Our AI will curate the perfect cinematic experience for you.
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 3. THE MAGIC CARD (Container sebagai Wrapper)
    # Kita menggunakan layout kolom untuk membatasi lebar agar tidak full width
    _, col_center, _ = st.columns([1, 2, 1]) 
    
    with col_center:
        # Container ini akan memiliki border & glow (diatur di CSS styles.py)
        with st.container(border=True):
            
            # Text Area (CSS membuatnya transparan tanpa border)
            user_input = st.text_area(
                "Mood Input", 
                placeholder="Example: I'm feeling a bit exhausted from work, I want something heartwarming but funny to lift my spirits...",
                height=150,
                label_visibility="collapsed"
            )
            
            # Bagian Bawah Card: Character Count (Kiri) & Tombol (Kanan)
            c_char, c_btn = st.columns([3, 2])
            
            with c_char:
                # Hitung karakter real-time
                char_count = len(user_input) if user_input else 0
                st.markdown(f"<div style='color: #475569; font-size: 12px; padding-top: 10px;'>{char_count} chars</div>", unsafe_allow_html=True)
            
            with c_btn:
                # Tombol Submit
                search_clicked = st.button("Analyze Mood \u2192", type="primary", use_container_width=True)

    # 4. Footer Dots (Indikator Teknologi)
    st.markdown("""
        <div class="footer-dots">
            <div><span class="dot"></span>NLP Analysis</div>
            <div><span class="dot dot-blue"></span>TMDB Data</div>
            <div><span class="dot dot-purple"></span>Generative AI</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Return values ke main.py
    return user_input, search_clicked

# --- Helper function for Modal & Grid (Sama seperti sebelumnya) ---
@st.dialog("Movie Details")
def show_details_modal(movie, mood_context):
    col_img, col_txt = st.columns([1, 1.5])
    with col_img:
        st.image(movie['poster'], use_container_width=True)
        st.markdown(f"<div style='background:#1e293b; color:#4ade80; padding:8px; border-radius:6px; text-align:center; margin-top:10px; font-weight:bold; font-size:0.9rem;'>{movie['match']}% Match</div>", unsafe_allow_html=True)
    with col_txt:
        st.markdown(f"<h2 style='margin:0; color:white;'>{movie['title']}</h2>", unsafe_allow_html=True)
        st.caption(f"{movie['year']} • ⭐ {movie['rating']}")
        st.write(movie['overview'])
        st.markdown("---")
        with st.spinner("AI Director's Cut..."):
            script = services.generate_creative_script(movie['title'], mood_context)
            st.info(f"\"{script}\"", icon="✨")
        st.link_button("Watch Trailer", f"https://www.youtube.com/results?search_query={movie['title']}+trailer", use_container_width=True)

def render_movie_grid(movies_data, mood_context):
    st.markdown("<br><hr style='border-color: #334155;'><br>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center;'>Curated for: <span style='color:#dc2626'>{mood_context}</span></h3><br>", unsafe_allow_html=True)
    
    cols = st.columns(4)
    for idx, movie in enumerate(movies_data):
        with cols[idx % 4]:
            with st.container(border=True):
                st.image(movie['poster'], use_container_width=True)
                st.markdown(f"<div style='font-weight:600; margin-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{movie['title']}</div>", unsafe_allow_html=True)
                st.caption(f"{movie['year']} • ⭐ {movie['rating']}")
                if st.button("Details", key=f"btn_{movie['id']}", use_container_width=True):
                    show_details_modal(movie, mood_context)