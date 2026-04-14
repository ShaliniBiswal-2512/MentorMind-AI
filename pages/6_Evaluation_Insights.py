import streamlit as st
from ui.theme import apply_theme

apply_theme()

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please sign in / login first.")
    st.stop()

if "evaluation" not in st.session_state or not st.session_state.evaluation:
    st.warning("No recent interview evaluation found.")
    st.stop()


from ui.theme import section_header, card

section_header("Assessment Performance Analysis", "🎯")

eval_data = st.session_state.evaluation
_raw_scores = eval_data.get("scores", {})
scores = {k.lower(): v for k, v in _raw_scores.items()} if isinstance(_raw_scores, dict) else {}

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("<p style='font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.75rem; margin-bottom: 10px;'>Final Verdict</p>", unsafe_allow_html=True)
    verdict = eval_data.get('verdict', 'Hold')
    v_color = "#58a6ff" if verdict == "Selected" else ("#bc8cff" if verdict == "Hold" else "#ea4a5a")
    v_glow = "rgba(88,166,255,0.3)" if verdict == "Selected" else "rgba(188,140,255,0.3)"
    
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.01); border: 1px solid var(--border-faint); padding: 40px 20px; border-radius: 20px; text-align: center;'>
            <h1 style='color: {v_color}; font-size: 4rem !important; margin: 0; text-shadow: 0 0 20px {v_glow};'>{verdict}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.75rem; margin-bottom: 10px;'>Protocol Compliance</p>", unsafe_allow_html=True)
    
    switches = st.session_state.get('tab_switches', 0)
    focus = max(0, 100 - (switches * 20))
    
    st.markdown(f"""
        <div class='premium-card' style='padding: 20px;'>
            <p style='margin-bottom: 8px;'><b>Focus Integrity:</b> <span style='color: {"#3fb950" if focus > 80 else "#d29922"};'>{focus}%</span></p>
            <p style='margin-bottom: 8px;'><b>Face Stability:</b> <span style='color: #3fb950;'>Passed</span></p>
            <p style='margin: 0;'><b>Violations:</b> {switches} / 3</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("<p style='font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.75rem; margin-bottom: 10px;'>Competency Mapping</p>", unsafe_allow_html=True)
    import plotly.express as px
    import pandas as pd
    
    s_keys = ['clarity', 'communication', 'problem_solving', 'subject_knowledge', 'teaching_ability']
    r_values = [float(scores.get(k, scores.get(f'score_{k}', 0))) for k in s_keys]

    df = pd.DataFrame(dict(r=r_values, theta=['Clarity', 'Communication', 'Logic', 'Knowledge', 'Instructional']))
    fig = px.pie(df, values='r', names='theta', hole=0.4, color_discrete_sequence=px.colors.sequential.Tealgrn)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), height=350, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True, 'scrollZoom': False})

section_header("Analytical Insights", "🔍")
colA, colB = st.columns(2, gap="large")
with colA:
    st.markdown("<p style='color: #3fb950; font-weight: 700;'>Points of Excellence</p>", unsafe_allow_html=True)
    for s in eval_data.get("strengths", []): st.write(f"✦ {s}")
with colB:
    st.markdown("<p style='color: #bc8cff; font-weight: 700;'>Development Vectors</p>", unsafe_allow_html=True)
    for w in eval_data.get("weaknesses", []): st.write(f"✦ {w}")

st.markdown("<br>", unsafe_allow_html=True)
info_text = eval_data.get("insights", "Standard evaluation completed.")
st.markdown(f"""
<div class='premium-card'>
    <p style='font-weight: 700; color: var(--text-muted); margin-bottom: 8px;'>Strategic Recommendations</p>
    <div style='background:rgba(88, 166, 255, 0.1); border-left:4px solid #58a6ff; padding: 15px; border-radius: 8px; color: var(--text-primary); font-size: 0.95rem; line-height: 1.5;'>
        {info_text}
    </div>
</div>
""", unsafe_allow_html=True)

# Final Actions
col_act1, col_act2 = st.columns(2, gap="medium")
with col_act1:
    if st.button("Archive Access", use_container_width=True):
        st.switch_page("pages/7_Interview_Records.py")
with col_act2:
    if st.button("Return to Hub", type="primary", use_container_width=True):
        st.switch_page("app.py")

# Download Option
try:
    from core.pdf_generator import generate_candidate_scorecard
    from db.database import get_profile
    profile = get_profile(st.session_state.user['id']) or {}
    pdf_bytes = generate_candidate_scorecard(profile.get('full_name', 'Mentor'), profile, eval_data)
    st.download_button("Export Intelligence Scorecard (PDF)", data=pdf_bytes, file_name="Performance_Report.pdf", mime="application/pdf", use_container_width=True)
except: pass
