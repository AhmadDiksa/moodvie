# styles.py

FONTS_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap"
ICONS_URL = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css"

CINEMATIC_CSS = f"""
<style>
    @import url('{FONTS_URL}');
    @import url('{ICONS_URL}');

    :root {{
        --bg-main: #050505;
        --bg-card: #0d1117; /* Sesuai React bg-card (GitHub dark style) */
        --border-color: #30363d; /* border-gray-800 */
        --accent: #5B5BD6; /* Warna Ungu dari React Code */
        --accent-hover: #4c4cb5;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
    }}

    /* RESET */
    .stApp {{
        background-color: var(--bg-main);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }}
    
    /* HIDE DEFAULT HEADER/FOOTER */
    header, footer {{ visibility: hidden; }}
    
    /* --- COMPONENT: ANALYSIS CARD (React Clone) --- */
    
    .dashboard-container {{
        width: 100%;
        max-width: 900px; /* max-w-4xl */
        margin: 0 auto;
        animation: fadeUp 0.6s ease-out;
    }}
    
    @keyframes fadeUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* CARD STYLING */
    .react-card {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px; /* rounded-xl */
        padding: 24px; /* p-6 */
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); /* shadow-2xl */
        margin-bottom: 32px;
    }}

    .card-header {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 24px;
        font-family: 'Poppins', sans-serif;
        font-size: 1.5rem; /* text-2xl */
        font-weight: 700;
        color: var(--text-primary);
    }}

    .dot-accent {{
        color: var(--accent);
        font-size: 1.2rem;
    }}

    /* GRID LAYOUT (md:grid-cols-2) */
    .card-grid {{
        display: grid;
        grid-template-columns: 1fr;
        gap: 32px;
    }}
    
    @media (min-width: 768px) {{
        .card-grid {{
            grid-template-columns: 1fr 1fr;
        }}
    }}

    /* LABELS */
    .section-label {{
        color: var(--text-secondary);
        font-size: 0.75rem; /* text-sm */
        text-transform: uppercase;
        letter-spacing: 0.05em; /* tracking-wider */
        font-weight: 600;
        margin-bottom: 8px;
        display: block;
    }}

    /* --- LEFT COLUMN COMPONENTS --- */

    /* MOOD PILLS */
    .mood-pill {{
        display: inline-block;
        padding: 4px 12px;
        background-color: rgba(91, 91, 214, 0.15); /* bg-accent/20 */
        color: #7979ff; /* text-accent lighter */
        border: 1px solid rgba(91, 91, 214, 0.3);
        border-radius: 9999px; /* rounded-full */
        font-size: 0.875rem; /* text-sm */
        font-weight: 500;
        margin-right: 8px;
        margin-bottom: 8px;
    }}

    /* INTENSITY BAR */
    .intensity-track {{
        width: 100%;
        background-color: #1f2937; /* bg-gray-800 */
        border-radius: 9999px;
        height: 12px;
        overflow: hidden;
    }}
    .intensity-fill {{
        height: 100%;
        background: linear-gradient(to right, #3b82f6, var(--accent));
        border-radius: 9999px;
        transition: width 1s ease-out;
    }}

    /* HASHTAGS */
    .hashtag {{
        display: inline-block;
        padding: 2px 8px;
        background-color: #161b22; /* bg-gray-800-ish */
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        font-size: 0.75rem; /* text-xs */
        margin-right: 6px;
        margin-bottom: 6px;
    }}

    /* --- RIGHT COLUMN COMPONENTS (CHART) --- */
    
    .chart-container {{
        background-color: rgba(17, 24, 39, 0.5); /* bg-gray-900/50 */
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
        height: 100%;
        min-height: 250px;
        display: flex;
        flex-direction: column;
    }}

    .chart-bar-row {{
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        height: 24px;
    }}
    .chart-y-axis {{
        width: 80px;
        font-size: 0.75rem;
        color: #9ba1a7;
        text-align: right;
        padding-right: 12px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .chart-bar-area {{
        flex: 1;
        height: 100%;
        display: flex;
        align-items: center;
    }}
    .chart-bar {{
        height: 16px;
        background-color: var(--accent);
        border-radius: 0 4px 4px 0;
        transition: width 0.5s ease;
    }}

    /* --- BUTTON STYLING (Override Streamlit) --- */
    
    /* Target tombol utama */
    div.stButton > button {{
        background-color: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 9999px !important; /* rounded-full */
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto !important; /* Center button */
        box-shadow: 0 4px 12px rgba(91, 91, 214, 0.3) !important;
    }}
    
    div.stButton > button:hover {{
        background-color: var(--accent-hover) !important;
        transform: scale(1.05) !important;
        box-shadow: 0 6px 20px rgba(91, 91, 214, 0.5) !important;
    }}

    /* Hide label on top of text area for cleaner look */
    .stTextArea label {{ display: none; }}
</style>
"""