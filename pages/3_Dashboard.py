import streamlit as st
from db.database import get_profile, get_user_interviews, clear_user_interviews
from ui.theme import apply_theme, card

apply_theme()

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please sign in / login first.")
    st.stop()


from ui.theme import section_header, card

section_header("Mentor Dashboard")

user_id = st.session_state.user['id']
profile = get_profile(user_id)
interviews = get_user_interviews(user_id)

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    with st.expander("Candidate Identity Matrix", expanded=False):
        if profile:
            display_name = profile.get('full_name') or st.session_state.user.get('name', 'Unknown')
            st.markdown(f"""
                <div style='background: rgba(88, 166, 255, 0.04); border: 1px solid rgba(88, 166, 255, 0.1); border-radius: 15px; padding: 25px;'>
                    <p style='margin: 0 0 10px 0; font-size: 1rem;'><span style='color: var(--accent-glow); font-weight: 700;'>Identity:</span> {display_name}</p>
                    <p style='margin: 0 0 10px 0; font-size: 1rem;'><span style='color: var(--accent-glow); font-weight: 700;'>Credentials:</span> {profile.get('qualification')}</p>
                    <p style='margin: 0 0 10px 0; font-size: 1rem;'><span style='color: var(--accent-glow); font-weight: 700;'>Expertise:</span> {profile.get('subjects')}</p>
                    <p style='margin: 0 0 10px 0; font-size: 1rem;'><span style='color: var(--accent-glow); font-weight: 700;'>Experience:</span> {profile.get('experience')}</p>
                    <p style='margin: 0; font-size: 1rem;'><span style='color: var(--accent-glow); font-weight: 700;'>Focus:</span> {profile.get('specific_class')}</p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Modify Identity Profile", use_container_width=True):
                st.switch_page("pages/2_Candidate_Profile.py")
        else:
            st.warning("Identity Profile not detected.")
            if st.button("Configure Identity", type="primary", use_container_width=True):
                st.switch_page("pages/2_Candidate_Profile.py")
    
with col2:
    with st.expander("Strategic AI Insights", expanded=False):
        if not profile or not profile.get('resume_summary'):
            st.info("Provision a resume in Profile to unlock Strategic Insights.")
        else:
            st.markdown(f"""
                <div style='background: rgba(188, 140, 255, 0.04); border: 1px solid rgba(188, 140, 255, 0.1); border-radius: 15px; padding: 25px; font-style: italic; line-height: 1.7;'>
                    "{profile.get('resume_summary')}"
                </div>
            """, unsafe_allow_html=True)

section_header("Recent Session Snapshots")

if not interviews:
    st.info("No recorded sessions found. Launch a new screening to begin.")
else:
    for idx, inv in enumerate(interviews[:3]):
        verdict = str(inv['verdict']).upper()
        v_color = "#3fb950" if verdict == "SELECTED" else ("#ea4a5a" if verdict == "REJECTED" else "#bc8cff")
        
        with st.expander(f"Session: {inv['date']} | {inv['subject']} | {verdict}", expanded=False):
            p_col1, p_col2 = st.columns([1, 1], gap="medium")
            with p_col1:
                st.markdown(f"<p style='color: {v_color}; font-weight: 800; font-size: 1.2rem; margin-bottom: 10px;'>{verdict}</p>", unsafe_allow_html=True)
                st.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 15px; border-radius: 12px; font-size: 0.95rem; border: 1px solid var(--border-faint);'>{inv['feedback'][:300]}...</div>", unsafe_allow_html=True)
                
                if profile:
                    try:
                        from core.pdf_generator import generate_candidate_scorecard
                        c_name = profile.get('full_name') or st.session_state.user.get('name', 'Unknown')
                        pdf_bytes = generate_candidate_scorecard(c_name, profile, inv)
                        st.download_button(label="Download Full Intelligence Report (PDF)", data=pdf_bytes, file_name=f"Report_{inv['id']}.pdf", mime="application/pdf", key=f"dl_dash_{inv['id']}")
                    except: pass
            
            with p_col2:
                import plotly.express as px
                import pandas as pd
                df = pd.DataFrame(dict(
                    r=[inv.get('score_clarity',0), inv.get('score_communication',0), inv.get('score_simplicity',0), inv.get('score_subject',0), inv.get('score_patience',0)],
                    theta=['Clarity', 'Communication', 'Logic', 'Knowledge', 'Instructional']
                ))
                fig = px.pie(df, values='r', names='theta', hole=0.4, color_discrete_sequence=px.colors.sequential.Tealgrn)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), height=230, showlegend=False)
                st.plotly_chart(fig, use_container_width=True, key=f"radar_dash_{inv['id']}", config={'displayModeBar': False, 'staticPlot': True, 'scrollZoom': False})

            if inv.get('session_id'):
                st.markdown("<div style='margin-top: 15px; background: #010409; border-radius: 12px; border: 1px solid var(--border-faint); padding: 10px;'>", unsafe_allow_html=True)
                playback_html = f"""
                <div id="video-container-{inv['session_id']}" style="width: 100%; min-height: 40px; display: flex; align-items: center; justify-content: center;">
                    <p id="video-status-{inv['session_id']}" style="color: #484f58; font-family: sans-serif; font-size: 0.85rem;">Checking session buffer...</p>
                </div>
                <script>
                (function() {{
                    const sid = "{inv['session_id']}";
                    const container = document.getElementById('video-container-' + sid);
                    const status = document.getElementById('video-status-' + sid);
                    const request = indexedDB.open("MentorMindDB", 2);
                    request.onsuccess = (e) => {{
                        const db = e.target.result;
                        if (!db.objectStoreNames.contains("VideosStore")) return;
                        const transaction = db.transaction("VideosStore", "readonly");
                        const getReq = transaction.objectStore("VideosStore").get(sid);
                        getReq.onsuccess = () => {{
                            if (getReq.result) {{
                                const url = URL.createObjectURL(getReq.result);
                                container.innerHTML = `<video src="${{url}}" controls style="width: 100%; border-radius: 8px; border: 1px solid #30363d;"></video>`;
                            }}
                        }};
                    }};
                }})();
                </script>
                """
                st.components.v1.html(playback_html, height=250)
                st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("Launch New Screening Session", type="primary", use_container_width=True):
    st.switch_page("pages/4_Start_Screening.py")

col1, col2 = st.columns(2, gap="small")
with col1:
    if st.button("Access Full Archive", use_container_width=True):
        st.switch_page("pages/7_Interview_Records.py")
with col2:
    if st.button("Wipe Recent History", use_container_width=True):
        clear_user_interviews(user_id)
        st.rerun()
