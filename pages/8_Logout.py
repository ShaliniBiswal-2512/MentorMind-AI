import streamlit as st
import time
from ui.theme import apply_theme

apply_theme()

# Clear all session state
st.session_state.clear()
st.session_state.user = None

st.markdown("""
<div style='text-align: center; margin-top: 50px;'>
    <div style='display: inline-block; background: rgba(88, 166, 255, 0.1); padding: 30px; border-radius: 50%; margin-bottom: 30px; border: 1px solid rgba(88, 166, 255, 0.2);'>
        <img src='https://api.iconify.design/fluent/lock-closed-20-regular.svg?color=%2358a6ff' style='width: 60px;'>
    </div>
    <h1 style='font-size: 2.5rem; margin-bottom: 10px;'>Session <span class='neon-text'>Closed</span></h1>
    <p style='color: var(--text-secondary); font-size: 1.1rem; max-width: 500px; margin: 0 auto 40px auto; line-height: 1.6;'>You have been securely signed out. All local session buffers have been flushed for your privacy.</p>
</div>

<script>
    // Clear persistence
    localStorage.removeItem('mentormind_uid');
</script>
""", unsafe_allow_html=True)

# Smooth Re-auth
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("Return to Hub Authorization", type="primary", use_container_width=True):
        st.switch_page("pages/1_Sign_In.py")

st.markdown("<p style='text-align: center; color: var(--text-muted); font-size: 0.85rem; margin-top: 50px;'>Protocol finalized. Session expired.</p>", unsafe_allow_html=True)

time.sleep(3)
st.switch_page("pages/1_Sign_In.py")
