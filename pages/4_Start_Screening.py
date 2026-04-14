import streamlit as st
import uuid
import time
from db.database import get_profile, count_today_attempts, log_attempt
from ui.theme import apply_theme

apply_theme()

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please sign in / login first.")
    st.stop()


from ui.theme import section_header, card

user_id = st.session_state.user['id']
profile = get_profile(user_id) or {}
attempts_today = count_today_attempts(user_id)
limit_reached = attempts_today >= 5

section_header("Assessment Setup", "🛠️")



# Configuration Matrix
st.markdown("<p style='margin-bottom: 25px; margin-top: 15px; color: var(--text-secondary); font-size: 1.05rem;'>Set your analytical parameters. All protocol assessments are recorded locally for deep evaluation.</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")
with col1:
    core_subjects = ["Mathematics", "Science", "English", "Physics", "Chemistry", "Biology", "History", "Geography", "Computer Science"]
    profile_subjects = [s.strip() for s in profile.get("subjects", "").split(',')] if profile and profile.get("subjects") else []
    all_subjects = list(dict.fromkeys(profile_subjects + core_subjects))
    if not all_subjects: all_subjects = ["General"]
    subject = st.selectbox("Interview Specialization", all_subjects)
    
with col2:
    class_level = st.selectbox("Assigning Grade Level", ["Class 1-5", "Class 6-8", "Class 9-10", "Class 11-12"])

st.markdown("<br>", unsafe_allow_html=True)
with st.expander("Protocol Guidelines", expanded=False):
    st.markdown("""
        <div style='font-size: 0.95rem; line-height: 1.7; color: var(--text-secondary); padding: 10px 5px;'>
            ✦ <b>3-Stage Screening</b>: Aptitude MCQ → Scenario Logic → AI Evaluator.<br>
            ✦ <b>Security</b>: Video proctoring is mandatory. No tab switching.<br>
            ✦ <b>Mode</b>: Voice-First interaction (ensure microphone is active).
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("Authorize and Begin Screening", type="primary", use_container_width=True):
    st.cache_data.clear()
    # Sidebar Scroll JS
    st.components.v1.html("""<script>var sb = window.parent.document.querySelector('[data-testid="stSidebarNav"]'); if (sb) { sb.scrollTop = 0; }</script>""", height=0)

    st.session_state.interview_config = {
        'subject': subject,
        'class_level': class_level,
        'proctoring': True,
        'mode': 'voice',
        'session_id': f"screening_{st.session_state.user['id']}_{int(time.time())}"
    }
    
    # Atomic Assessment Reset
    reset_keys = [
        'current_level', 'consent_given', 'apt_score', 'scen_score', 'tab_switches', 
        'transcript', 'violation_logs', 'interview_finished', 'video_saved', 
        'video_saving_triggered', 'apt_idx', 'scen_idx', 'int_idx', 'l1_answers', 'l2_answers',
        'face_detected', 'face_status', 'failure_count', 'detection_buffer', 'cam_error'
    ]
    for key in reset_keys:
        if key in st.session_state: del st.session_state[key]
        
    st.switch_page("pages/_Live_Interview.py")

st.markdown("<p style='text-align: center; color: var(--text-muted); font-size: 0.8rem; margin-top: 25px;'>Protocol Secured by MentorMind Neural Engine</p>", unsafe_allow_html=True)
