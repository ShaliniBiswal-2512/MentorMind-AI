import streamlit as st
from db.database import authenticate_user, create_user, get_user_by_id
from ui.theme import apply_theme

apply_theme()

# Strict Authentication Only

# Load Logo
try:
    import base64
    with open("assets/logo.png", "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 105px; mix-blend-mode: screen; object-fit: contain; opacity: 0.95;">'
except:
    logo_html = '<img src="https://api.iconify.design/fluent/brain-circuit-20-regular.svg?color=%2358a6ff" style="width: 85px;">'

# Centered Premium Container
st.markdown(f"""
<div style='display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 20px; margin-bottom: 25px;'>
    <div style='transform: translateY(-5px);'>{logo_html}</div>
    <div style='text-align: left;'>
        <div style='font-family: inherit; font-size: 2.8rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 0px; color: var(--text-primary); line-height: 1.1;'>MentorMind <span class='neon-text'>AI</span></div>
        <div style='color: var(--text-secondary); font-size: 1.05rem; opacity: 0.9; margin-top: 2px; font-weight: 500; font-style: italic;'>Elevating Education Through Intelligent Screening</div>
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.get("user") is not None:
    st.success("Access granted.")
    if st.button("Enter Command Center", type="primary"):
        st.switch_page("app.py")
    st.stop()

# Form Wrapper
tab1, tab2 = st.tabs(["Secure Login", "New Account"])

with tab1:
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Work Email", placeholder="tutor@institution.edu")
        password = st.text_input("Security PIN", type="password")
        submit = st.form_submit_button("Authorize Access")
        
        if submit:
            if not email.strip() or not password.strip():
                st.error("Access Denied: Missing credentials.")
            else:
                user = authenticate_user(email, password)
                if isinstance(user, dict):
                    st.session_state.user = user
                    st.rerun()
                elif isinstance(user, str):
                    st.error(f"System Error: {user}")
                else:
                    st.error("Authentication failed. Check credentials.")

with tab2:
    with st.form("signup_form"):
        new_name = st.text_input("Full Name")
        new_email = st.text_input("Primary Email")
        new_password = st.text_input("Access PIN", type="password")
        submit_signup = st.form_submit_button("Create Account")
        
        if submit_signup:
            if not new_name.strip() or not new_email.strip() or not new_password.strip():
                st.error("All fields are required to provision an account.")
            else:
                if create_user(new_name, new_email, new_password):
                    st.success("Account provisioned. Please switch to Login tab.")
                else:
                    st.error("Identity already registered in the protocol.")
