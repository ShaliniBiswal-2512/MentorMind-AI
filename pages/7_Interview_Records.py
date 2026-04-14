import streamlit as st
from db.database import get_user_interviews, delete_interview, get_profile
from ui.theme import apply_theme, section_header
from core.pdf_generator import generate_candidate_scorecard

apply_theme()

if "user" not in st.session_state or st.session_state.user is None:
    st.markdown("<div class='premium-warning'>Please authorize via the login protocol first.</div>", unsafe_allow_html=True)
    st.stop()

section_header("Intelligence Archives", "")

user_id = st.session_state.user['id']
profile = get_profile(user_id) or {}
interviews = get_user_interviews(user_id)

if not interviews:
    st.info("The intelligence archive is currently empty. Complete an assessment to store your records here.")
else:
    for inv in reversed(interviews):
        verdict = str(inv['verdict']).upper()
        v_color = "#3fb950" if verdict == "SELECTED" else ("#ea4a5a" if verdict == "REJECTED" else "#bc8cff")
        
        with st.container():
            st.markdown(f"""
            <div class='premium-card' style='margin-bottom: 10px;'>
                <div style='display: flex; justify-content: space-between; align-items: start;'>
                    <div>
                        <p style='color: var(--text-muted); font-size: 0.8rem; margin: 0;'>{inv['date']}</p>
                        <h3 style='margin: 5px 0;'>{inv['subject']} <span style='font-size: 0.9rem; font-weight: 400; color: var(--text-muted);'>({inv['class_level']})</span></h3>
                    </div>
                    <div>
                        <span style='background: {v_color}22; color: {v_color}; padding: 6px 15px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; border: 1px solid {v_color}44;'>{verdict}</span>
                    </div>
                </div>
                <hr style='border-top: 1px solid var(--border-faint); margin: 15px 0;'>
                <p style='font-weight: 700; color: var(--accent-glow); margin-bottom: 8px;'>AI Assessment Summary</p>
                <div style='font-style: italic; font-size: 0.95rem; line-height: 1.6; color: var(--text-secondary); background: rgba(0,0,0,0.1); padding: 15px; border-radius: 12px;'>\"{inv.get('feedback', '')[:400]}...\"</div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                try:
                    c_name = profile.get('full_name') or st.session_state.user.get('name', 'Unknown')
                    pdf_bytes = generate_candidate_scorecard(c_name, profile, inv)
                    st.download_button("Export Intelligence Report", data=pdf_bytes, file_name=f"Report_{inv['id']}.pdf", key=f"dl_{inv['id']}", use_container_width=True)
                except: pass
            with c2:
                if st.button("Delete Record", key=f"del_{inv['id']}", use_container_width=True):
                    delete_interview(inv['id'], user_id)
                    st.rerun()
            st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("Return to Hub", type="primary", use_container_width=True):
    st.switch_page("app.py")

