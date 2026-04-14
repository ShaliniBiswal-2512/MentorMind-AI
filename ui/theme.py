import streamlit as st

def apply_theme():
    # Elite Premium Dark Theme Design System
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@400;500;600;700;800&display=swap');

        /* 1. Global Design Tokens */
        :root {
            --bg-deep: #0d1117;
            --bg-surface: #0a0d13;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-muted: #484f58;
            --accent-glow: #58a6ff;
            --accent-secondary: #bc8cff;
            --border-faint: rgba(240, 246, 252, 0.08);
            --border-hover: rgba(88, 166, 255, 0.3);
            --premium-gradient: linear-gradient(135deg, #58a6ff 0%, #bc8cff 100%);
            --glass-bg: rgba(22, 27, 34, 0.6);
            --hover-transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        /* 2. Page & Layout Sanitization */
        .stApp {
            background-color: var(--bg-deep);
            background-image: 
                radial-gradient(circle at 5% 5%, rgba(88, 166, 255, 0.04) 0%, transparent 35%),
                radial-gradient(circle at 95% 95%, rgba(188, 140, 255, 0.04) 0%, transparent 35%);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
        }
        
        /* Fix the massive Streamlit top padding */
        .block-container {
            padding-top: 1.8rem !important;
            padding-bottom: 2rem !important;
            max-width: 1100px !important;
        }
        
        /* Unified element spacing */
        [data-testid="stVerticalBlock"] > div {
            gap: 1.2rem !important;
        }

        /* 3. Global Typography */
        h1, h2, h3, h4 {
            color: var(--text-primary) !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            letter-spacing: -0.03em !important;
            margin-bottom: 0.5rem !important;
        }
        
        h1 { font-size: 2.8rem !important; line-height: 1.2 !important; }
        h2 { font-size: 2rem !important; margin-bottom: 1.2rem !important; }
        h3 { font-size: 1.4rem !important; color: var(--accent-glow) !important; font-weight: 700 !important; }
        
        p, span, label, li {
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            color: var(--text-secondary);
        }

        /* 4. Premium Design Components */
        .premium-card {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border-faint);
            border-radius: 20px;
            padding: 28px;
            transition: var(--hover-transition);
            margin-bottom: 20px;
        }
        
        .premium-card:hover {
            transform: translateY(-4px);
            border-color: var(--border-hover);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
        }

        .section-header {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 20px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-header::after {
            content: "";
            flex: 1;
            height: 1px;
            background: var(--border-faint);
        }

        .neon-text {
            background: var(--premium-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            font-size: inherit !important;
        }

        /* 5. Streamlit Widget Overrides */
        /* Buttons */
        div.stButton > button {
            background: rgba(255, 255, 255, 0.03) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-faint) !important;
            border-radius: 12px !important;
            padding: 0.7rem 1.4rem !important;
            font-weight: 600 !important;
            font-family: 'Outfit', sans-serif !important;
            transition: var(--hover-transition) !important;
            width: 100%;
        }

        div.stButton > button:hover {
            border-color: var(--accent-glow) !important;
            background: rgba(88, 166, 255, 0.05) !important;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
            transform: translateY(-2px) !important;
        }
        
        div.stButton > button[data-testid="baseButton-primary"] {
            background: #F9E076 !important;
            border: none !important;
            color: #1a1a1a !important;
            font-weight: 700 !important;
        }
        
        div.stButton > button[data-testid="baseButton-primary"]:hover {
            box-shadow: 0 8px 25px rgba(249, 224, 118, 0.4) !important;
            opacity: 0.9 !important;
            color: #000000 !important;
        }

        /* Inputs */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox [data-testid="stSelectbox"] {
            background-color: var(--bg-surface) !important;
            border: 1px solid var(--border-faint) !important;
            border-radius: 10px !important;
            color: var(--text-primary) !important;
            font-size: 0.95rem !important;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: var(--accent-glow) !important;
            box-shadow: 0 0 10px rgba(88, 166, 255, 0.1) !important;
        }

        /* Expander */
        .stExpander {
            border: 1px solid var(--border-faint) !important;
            border-radius: 12px !important;
            background: rgba(255, 255, 255, 0.01) !important;
            margin-bottom: 10px !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            border-radius: 8px 8px 0 0;
            color: var(--text-secondary);
            font-family: 'Outfit', sans-serif;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            color: var(--accent-glow) !important;
            border-bottom-color: var(--accent-glow) !important;
        }

        /* Sidebar Navigation Fixes */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0d13 0%, #030406 100%) !important;
            border-right: 1px solid var(--border-faint);
        }
        [data-testid="stSidebarNav"] span {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            color: var(--text-secondary) !important;
        }
        [data-testid="stSidebarNav"] [aria-current="page"] {
            background: rgba(88, 166, 255, 0.1) !important;
            border-left: 3px solid var(--accent-glow) !important;
        }
        [data-testid="stSidebarNav"] [aria-current="page"] span {
            color: white !important;
            font-weight: 600 !important;
        }
        
        /* Hide Internal Pages from Sidebar Navigation */
        [data-testid="stSidebarNav"] a[href*="Live_Interview"],
        [data-testid="stSidebarNav"] a[href*="live_interview"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Success/Info Alerts */
        [data-testid="stAlert"] {
            border-radius: 10px !important;
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid var(--border-faint) !important;
        }
        
        /* Custom Premium Warning for auth logic */
        .premium-warning {
            background: rgba(234, 74, 90, 0.05);
            border: 1px solid rgba(234, 74, 90, 0.2);
            padding: 15px 20px;
            border-radius: 12px;
            color: #ea4a5a;
            font-weight: 600;
            text-align: center;
            margin: 20px 0;
        }

        </style>
    """, unsafe_allow_html=True)
    
    # Premium Sidebar Header (Logo removed)
    st.sidebar.markdown(f'''
        <div style="text-align: center; margin-top: -15px; margin-bottom: 25px; padding: 25px 15px; background: linear-gradient(145deg, rgba(22, 27, 34, 0.4) 0%, rgba(10, 13, 19, 0.8) 100%); border-radius: 16px; border: 1px solid rgba(255,255,255,0.03); box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 8px 24px rgba(0,0,0,0.4); position: relative; overflow: hidden;">
            <div style="position: absolute; top: -20px; left: 50%; transform: translateX(-50%); width: 100px; height: 40px; background: var(--premium-gradient); filter: blur(30px); opacity: 0.4;"></div>
            <div style="font-size: 1.8rem; line-height: 1.2; font-family: 'Outfit', sans-serif; font-weight: 800; letter-spacing: -0.02em; background: linear-gradient(135deg, #ffffff 0%, #a5c8ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; position: relative; z-index: 1;">MentorMind <span style="font-size: inherit !important; background: var(--premium-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI</span></div>
            <div style="color: #8b949e; font-size: 0.75rem; margin-top: 8px; letter-spacing: 0.25em; text-transform: uppercase; font-weight: 600; position: relative; z-index: 1;">Intelligence Protocol</div>
        </div>
        <hr style="border: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(88,166,255,0.3), transparent); margin-top: 5px; margin-bottom: 25px;">
    ''', unsafe_allow_html=True)

def card(html_content):
    st.markdown(f'<div class="premium-card">{html_content}</div>', unsafe_allow_html=True)

def section_header(title, icon="✦"):
    st.markdown(f'<div class="section-header"><span>{icon}</span>{title}</div>', unsafe_allow_html=True)
