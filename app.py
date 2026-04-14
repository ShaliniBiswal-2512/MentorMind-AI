import streamlit as st
import os
import time
from dotenv import load_dotenv
from ui.theme import apply_theme
from db.database import init_db, get_user_by_id, count_today_attempts

load_dotenv(override=True)

# Initialize Database
init_db()

st.set_page_config(
    page_title="MentorMind AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()

# Strict Session Validation
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.switch_page("pages/1_Sign_In.py")
else:
    # -------------------------------------------------------------
    # COMMAND CENTER OVERHAUL
    # -------------------------------------------------------------
    from db.database import get_user_interviews, get_profile
    from ui.theme import section_header, card
    import pandas as pd
    
    user_id = st.session_state.user['id']
    interviews = get_user_interviews(user_id)
    profile = get_profile(user_id) or {}
    
    # Check Daily Limit
    attempts_today = count_today_attempts(user_id)
    limit_reached = attempts_today >= 5
    
    # 1. Futuristic Greeting
    greet = "Welcome" if st.session_state.user.get('login_count', 0) <= 1 else "Welcome back"
    st.markdown(f"""
        <div style='margin-top: 10px; margin-bottom: 45px;'>
            <div style='font-family: inherit; font-size: 3.4rem; font-weight: 800; letter-spacing: -0.03em; color: var(--text-primary); line-height: 1.1; margin-bottom: 5px;'>{greet}, <span class='neon-text'>{st.session_state.user['name']}</span></div>
            <div style='color: var(--text-secondary); font-size: 1.15rem; opacity: 0.9; font-weight: 500;'>Command Center is active. Review performance or launch a screening protocol.</div>
        </div>
    """, unsafe_allow_html=True)
    
    total_interviews = len(interviews)
    
    # 2. Quick Metrics Banner / Empty State
    if total_interviews == 0:
        section_header("Screening Workspace", "✦")
        with st.container():
            st.markdown("""
                <div class='premium-card' style='text-align: center; padding: 60px 20px; border-radius: 16px; margin-bottom: 30px;'>
                    <div style='font-family: inherit; font-size: 1.8rem; font-weight: 700; color: var(--text-primary); margin-bottom: 12px; letter-spacing: -0.01em;'>No interview records found</div>
                    <div style='color: var(--text-secondary); font-size: 1.05rem; line-height: 1.6; max-width: 600px; margin: 0 auto;'>Initiate your first AI-powered screening to generate deep analytical insights, performance metrics, and professional candidate reports.</div>
                </div>
            """, unsafe_allow_html=True)
            emp1, emp2, emp3 = st.columns([1, 1, 1])
            with emp2:
                if st.button("Launch Screening Protocol", type="primary", use_container_width=True):
                    st.switch_page("pages/4_Start_Screening.py")

        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    
    # 3. Two-Column Action Split
    col_start, col_recent = st.columns([1, 1.1], gap="large")
    
    with col_start:
        section_header("Assessment Protocol", "✦")
        # Populate subject dynamically or use generic if absent
        cand_subjects = [s.strip() for s in profile.get('subjects', '').split(',')] if profile.get('subjects') else []
        default_subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "English", "History", "Geography"]
        combined_subjects = list(dict.fromkeys(cand_subjects + default_subjects))
        
        with st.container():
            subject = st.selectbox("Interview Subject", options=combined_subjects, key="app_qs_subj")
            class_level = st.selectbox("Assigning Class", options=["Class 1-5", "Class 6-8", "Class 9-10", "Class 11-12"], key="app_qs_lvl")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Launch Interview Now", type="primary"):
                st.session_state.interview_config = {
                    'subject': subject,
                    'class_level': class_level,
                    'proctoring': True,
                    'mode': 'voice',
                    'session_id': f"qs_{st.session_state.user['id']}_{int(time.time())}"
                }
                # Atomic Assessment Reset
                reset_keys = [
                    'current_level', 'consent_given', 'apt_score', 'scen_score', 'tab_switches', 
                    'transcript', 'violation_logs', 'interview_finished', 'video_saved', 
                    'video_saving_triggered', 'apt_idx', 'scen_idx', 'int_idx', 'l1_answers', 'l2_answers',
                    'face_detected', 'face_status', 'failure_count', 'detection_buffer', 'cam_error',
                    'apt_qs', 'scen_qs', 'int_qs'
                ]
                for key in reset_keys:
                    if key in st.session_state: del st.session_state[key]
                st.switch_page("pages/_Live_Interview.py")
        
    with col_recent:
        section_header("Latest Snapshot", "✦")
        if total_interviews == 0:
            st.info("No interviews recorded yet.")
        else:
            latest = interviews[0]
            verdict = str(latest['verdict']).upper()
            v_color = "#3fb950" if verdict == "SELECTED" else ("#ea4a5a" if verdict == "REJECTED" else "#bc8cff")
            
            st.markdown(f"""
            <div class='premium-card' style='background: rgba(255, 255, 255, 0.015);'>
                <p style='color: var(--text-muted); font-size: 0.8rem; font-weight: 700; text-transform: uppercase;'>{latest['date']}</p>
                <h3 style='margin-bottom: 5px;'>{latest['subject']}</h3>
                <p style='margin-bottom: 12px;'>Verdict: <span style='font-weight: 700; color: {v_color};'>{verdict}</span></p>
                <div style='background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; font-style: italic; font-size: 0.9rem;'>
                    "{latest['feedback'][:150]}..."
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                from core.pdf_generator import generate_candidate_scorecard
                c_name = profile.get('full_name') or st.session_state.user.get('name', 'Unknown')
                pdf_bytes = generate_candidate_scorecard(c_name, profile, latest)
                st.download_button(
                    label="Download Full Scorecard (PDF)",
                    data=pdf_bytes,
                    file_name=f"{c_name.replace(' ', '_')}_Latest.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except: pass
                
    st.markdown(f"""
        <div style='margin-top: 40px; position: relative; padding: 30px 35px; border-radius: 16px; background: linear-gradient(145deg, rgba(22, 27, 34, 0.5) 0%, rgba(10, 13, 19, 0.8) 100%); border: 1px solid rgba(188, 140, 255, 0.15); box-shadow: 0 8px 30px rgba(0,0,0,0.4); overflow: hidden;'>
            <div style='position: absolute; top: 0; left: 0; width: 5px; height: 100%; background: var(--premium-gradient); box-shadow: 0 0 20px rgba(188, 140, 255, 0.8);'></div>
            <div style='position: absolute; top: -50%; left: -20%; width: 50%; height: 200%; background: radial-gradient(circle, rgba(188,140,255,0.08) 0%, transparent 70%); pointer-events: none;'></div>
            <div style='color: var(--accent-secondary); font-family: "Outfit", sans-serif; font-size: 0.8rem; font-weight: 800; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 12px; position: relative; z-index: 1;'>✦ AI Tutor Insight</div>
            <p style='color: var(--text-primary); margin: 0; font-size: 1.1rem; line-height: 1.7; opacity: 0.95; font-family: "Inter", sans-serif; position: relative; z-index: 1;'><span style='font-weight: 600; color: #ffffff;'>The Socratic Method:</span> Instead of correcting a student's answer immediately, try asking: <span style='font-style: italic; color: #a5c8ff;'>"What led you to that conclusion?"</span> This triggers metamorphic neural pathways and encourages critical self-correction.</p>
        </div>
    """, unsafe_allow_html=True)
