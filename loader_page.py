# loader_page.py
import streamlit as st

def render():
    """
    Menampilkan animasi loading spinner dan teks status.
    Pastikan CSS .loading-container sudah ada di styles.py
    """
    st.markdown("""
        <div class="loading-container">
            <div class="custom-spinner"></div>
            <div class="loading-title">Decoding your emotions...</div>
            <div class="loading-subtitle">Our AI is extracting mood vectors and intensity.</div>
        </div>
    """, unsafe_allow_html=True)