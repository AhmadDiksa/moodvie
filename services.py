import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import requests
import json
import random
import os
import streamlit as st
import re

# Kita coba model pro standar dulu yang biasanya lebih stabil
GEMINI_MODEL_NAME = 'gemini-flash-latest'

def configure_apis():
    """Mengambil API key dari env atau secrets"""
    gemini_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    tmdb_key = os.getenv("TMDB_API_KEY") or st.secrets.get("TMDB_API_KEY")
    
    if gemini_key:
        genai.configure(api_key=gemini_key)
    
    return gemini_key, tmdb_key

def _clean_json_string(text_response):
    """Membersihkan format markdown ```json dari respon Gemini"""
    try:
        if "```" in text_response:
            match = re.search(r"```(?:json)?\s*(.*)\s*```", text_response, re.DOTALL)
            if match:
                return match.group(1)
        return text_response.strip()
    except:
        return text_response

def analyze_mood(text):
    """
    Analisis mood yang mengembalikan JSON terstruktur.
    """
    try:
        # 1. KONFIGURASI MODEL & SAFETY SETTINGS (PENTING!)
        # Kita matikan filter agar mood sedih/marah tidak dianggap berbahaya
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        prompt = f"""
        Act as an emotional analysis AI. Analyze this user text: "{text}".
        
        You MUST return a raw JSON object (no markdown, no code blocks) with this structure:
        {{
            "detected_moods": ["mood1", "mood2"],
            "intensity_score": 85,
            "thematic_keywords": ["#keyword1", "#keyword2", "#keyword3"],
            "genre_alignment": [
                {{"genre": "Drama", "score": 90}},
                {{"genre": "Comedy", "score": 40}},
                {{"genre": "Thriller", "score": 60}},
                {{"genre": "Romance", "score": 20}}
            ],
            "summary_text": "Brief summary of the mood."
        }}
        Rules:
        1. intensity_score must be integer 0-100.
        2. genre score must be integer 0-100.
        3. Do not include explanation, just the JSON.
        """
        
        # Request tanpa 'response_mime_type' dulu agar kompatibel semua versi
        response = model.generate_content(prompt, safety_settings=safety_settings)
        
        # Cek apakah response diblokir safety filter
        if not response.text:
            st.error("⚠️ Error: Gemini memblokir respon ini (Safety Filter Triggered).")
            raise ValueError("Empty response from Gemini")

        # Bersihkan dan Parse
        clean_text = _clean_json_string(response.text)
        return json.loads(clean_text)

    except Exception as e:
        # --- DEBUGGING DISPLAY ---
        # Ini akan memunculkan kotak merah di layar berisi alasan errornya
        st.error(f"🚨 DEBUG ERROR DETAILS: {str(e)}")
        
        # Return fallback agar aplikasi tidak crash total
        return {
            "detected_moods": ["Error"],
            "intensity_score": 0,
            "thematic_keywords": ["#TryAgain"],
            "genre_alignment": [{"genre": "Error", "score": 0}],
            "summary_text": "System Error. Check the red box above."
        }

def get_recommendations(mood_summary):
    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        prompt = f"""
        Mood: '{mood_summary}'.
        Recommend 4 movies.
        Output raw JSON list: [{{ "title": "Movie Title", "reason": "Short reason" }}]
        """
        response = model.generate_content(prompt)
        clean_text = _clean_json_string(response.text)
        return json.loads(clean_text)
    except Exception as e:
        st.warning(f"Gagal mengambil rekomendasi: {e}")
        return []

def _calculate_match_score(movie_data):
    vote_avg = movie_data.get('vote_average', 0)
    vote_count = movie_data.get('vote_count', 0)
    base_score = vote_avg * 10
    return min(99, int(base_score * (1 - 1 / (vote_count + 1)) + 10))

def search_tmdb_details(movie_title, api_key):
    if not api_key: return None
    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {"api_key": api_key, "query": movie_title, "language": "id-ID"}
        data = requests.get(url, params=params).json()
        
        if data.get('results'):
            m = data['results'][0]
            match_score = _calculate_match_score(m)
            return {
                "id": m['id'],
                "title": m['title'],
                "overview": m.get('overview') or "Sinopsis belum tersedia.",
                "year": m.get('release_date', '')[:4],
                "rating": round(m['vote_average'], 1),
                "poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m['poster_path'] else "https://via.placeholder.com/500x750",
                "match": match_score
            }
        return None
    except:
        return None

def generate_creative_script(movie_title, mood):
    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        prompt = f"Buat satu kalimat puitis pendek (max 20 kata) tentang film '{movie_title}' untuk mood '{mood}'. Bahasa Indonesia."
        return model.generate_content(prompt).text
    except:
        return "Film ini menunggumu."