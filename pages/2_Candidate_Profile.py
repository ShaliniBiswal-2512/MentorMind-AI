import streamlit as st
from db.database import get_profile, update_profile
from core.pdf_parser import extract_text_from_pdf
from core.groq_api import summarize_resume
from ui.theme import apply_theme

apply_theme()


if "user" not in st.session_state or st.session_state.user is None:
    st.markdown("<div class='premium-warning'>Please authorize via the login protocol first.</div>", unsafe_allow_html=True)
    st.stop()

from ui.theme import section_header, card

section_header("Candidate Profile Setup", "👤")

user_id = st.session_state.user.get('id')
existing_profile = get_profile(user_id) or {}

with st.container():
    st.markdown("<p style='margin-bottom: 25px; margin-top: 15px; color: var(--text-secondary); font-size: 1.05rem;'>Configure your professional identity to enable detailed AI strategic analysis.</p>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("<h3 style='font-size: 1.1rem !important; margin-bottom: 20px !important;'>Professional Identity</h3>", unsafe_allow_html=True)
        default_name = existing_profile.get("full_name") or st.session_state.user.get('name', '')
        full_name_input = st.text_input("Legal Professional Name", value=default_name)
        qualification = st.text_input("Highest Qualification", value=existing_profile.get("qualification", ""))
        subjects = st.text_input("Teaching Specializations (comma separated)", value=existing_profile.get("subjects", ""))
        experience = st.selectbox("Years of Experience", ["Fresher", "1-2 yrs", "3+ yrs"], 
                                  index=["Fresher", "1-2 yrs", "3+ yrs"].index(existing_profile.get("experience", "Fresher")))
        
        specific_class_list = ["Class 1-5", "Class 6-8", "Class 9-10", "Class 11-12"]
        current_specific = existing_profile.get("specific_class", "Class 6-8")
        if current_specific not in specific_class_list: current_specific = "Class 6-8"
        specific_class = st.selectbox("Target Grade Level", specific_class_list, index=specific_class_list.index(current_specific))

    with col2:
        st.markdown("<h3 style='font-size: 1.1rem !important; margin-bottom: 20px !important;'>Resume Intelligence</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload PDF Portfolio/Resume", type=["pdf"])
        
        temp_text = st.session_state.get("parsed_resume_text", existing_profile.get("resume_extracted_text", ""))
        temp_summary = st.session_state.get("parsed_resume_summary", existing_profile.get("resume_summary", ""))
        
        if uploaded_file is not None:
            if st.button("AI Auto-Analyze", type="primary"):
                with st.spinner("Decoding document intelligence..."):
                    temp_text = extract_text_from_pdf(uploaded_file)
                    import json
                    try:
                        summary_json_str = summarize_resume(temp_text)
                        data = json.loads(summary_json_str)
                        
                        # Map experience
                        mapped_exp = "Fresher"
                        exp_val = data.get("experience", "Fresher").lower()
                        import re
                        exp_nums = re.findall(r'(\d+|one|two)\s*year', exp_val + " " + data.get("summary", "").lower())
                        if exp_nums:
                            val = exp_nums[0]
                            if val in ['1', '2', 'one', 'two']: mapped_exp = "1-2 yrs"
                            elif val.isdigit() and int(val) >= 3: mapped_exp = "3+ yrs"
                        
                        # Direct DB sync for auto-fill
                        updated_data = existing_profile.copy()
                        updated_data.update({
                            "full_name": data.get("full_name") or full_name_input,
                            "qualification": data.get("qualification") or qualification,
                            "subjects": data.get("subjects") or subjects,
                            "experience": mapped_exp,
                            "resume_extracted_text": temp_text,
                            "resume_summary": data.get("summary") or ""
                        })
                        update_profile(user_id, updated_data)
                        st.rerun()
                    except:
                        st.session_state.parsed_resume_text = temp_text
                        st.session_state.parsed_resume_summary = "Structure analysis failed. Please fill manually."
            
        # Removed extraction result sub-text rendering to maintain clean UI
    


st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
if st.button("Finalize and Save Profile", type="primary"):
    data = {
        "full_name": full_name_input,
        "qualification": qualification,
        "subjects": subjects,
        "experience": experience,
        "pref_class_level": "Middle", # Defaulting/Simplifying
        "specific_class": specific_class,
        "resume_extracted_text": temp_text,
        "resume_summary": temp_summary
    }
    update_profile(user_id, data)
    st.success("Identity profile synchronized.")
