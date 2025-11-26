import streamlit as st
import re  # <--- Kita butuh ini untuk membersihkan HTML

def render(data):
    """
    Menampilkan Dashboard Analisis Mood.
    """
    
    # 1. SIAPKAN DATA
    moods = data.get('detected_moods', ['Neutral'])
    
    # Normalisasi intensity (jika > 1, bagi 100)
    raw_intensity = data.get('intensity_score', 0)
    intensity = raw_intensity / 100.0 if raw_intensity > 1 else raw_intensity
    
    keywords = data.get('thematic_keywords', [])
    genres = data.get('genre_alignment', [])

    # 2. GENERATE PARTIAL HTML (Tanpa Indentasi Berlebih)
    
    # Mood Pills
    moods_html = ""
    for mood in moods:
        moods_html += f'<span class="mood-pill">{mood}</span>'

    # Hashtags
    keywords_html = ""
    for k in keywords:
        clean_k = k.replace("#", "")
        keywords_html += f'<span class="hashtag">#{clean_k}</span>'

    # Chart Bars
    chart_rows_html = ""
    for idx, g in enumerate(genres):
        opacity = 0.6 + (idx * 0.05)
        if opacity > 1: opacity = 1
        
        width_pct = g.get('score', 0)
        genre_name = g.get('genre', 'Unknown')
        
        chart_rows_html += f"""
        <div class="chart-bar-row">
            <div class="chart-y-axis" title="{genre_name}">{genre_name}</div>
            <div class="chart-bar-area">
                <div class="chart-bar" style="width: {width_pct}%; opacity: {opacity};"></div>
            </div>
        </div>
        """

    # 3. SUSUN HTML LENGKAP
    # Kita tulis biasa agar mudah dibaca di editor Python
    # Nanti kita bersihkan menggunakan Regex sebelum dirender
    html_template = f"""
    <div class="dashboard-container">
        <div class="react-card">
            
            <!-- HEADER -->
            <h2 class="card-header">
                <span class="dot-accent">●</span> Emotional Analysis
            </h2>

            <div class="card-grid">
                
                <!-- LEFT COLUMN -->
                <div style="display: flex; flex-direction: column; gap: 24px;">
                    
                    <!-- Moods -->
                    <div>
                        <p class="section-label">DETECTED MOODS</p>
                        <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                            {moods_html}
                        </div>
                    </div>

                    <!-- Intensity -->
                    <div>
                        <p class="section-label">EMOTIONAL INTENSITY</p>
                        <div class="intensity-track">
                            <div class="intensity-fill" style="width: {intensity * 100}%;"></div>
                        </div>
                        <p style="text-align: right; font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                            {int(intensity * 100)}%
                        </p>
                    </div>

                    <!-- Keywords -->
                    <div>
                        <p class="section-label">THEMATIC KEYWORDS</p>
                        <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                            {keywords_html}
                        </div>
                    </div>

                </div>

                <!-- RIGHT COLUMN -->
                <div class="chart-container">
                    <p class="section-label" style="margin-bottom: 16px;">GENRE ALIGNMENT</p>
                    <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
                        {chart_rows_html}
                    </div>
                </div>

            </div>
        </div>
    </div>
    """

    # 4. MEMBERSIHKAN HTML (SOLUSI UTAMA)
    # Hapus baris baru dan spasi berlebih antar tag agar menjadi satu baris panjang.
    # Ini mencegah Markdown menganggapnya sebagai Code Block.
    clean_html = re.sub(r'\n\s*', '', html_template)

    # Render HTML yang sudah bersih
    st.markdown(clean_html, unsafe_allow_html=True)

    # 5. TOMBOL ACTION
    st.markdown("<br>", unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 2, 1])
    
    with col_btn:
        if st.button("Generate Recommendations  \u279C", key="gen_btn", use_container_width=True):
            return True
            
    return False