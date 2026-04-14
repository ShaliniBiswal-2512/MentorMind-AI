import streamlit as st
import time
import base64
import cv2
import numpy as np
import mediapipe as mp
try:
    import mediapipe.python.solutions.face_detection as mp_face_detection # type: ignore
except ImportError:
    mp_face_detection = None
import json
from streamlit_mic_recorder import mic_recorder
from core.groq_api import (
    generate_interview_questions, 
    evaluate_interview, 
    generate_aptitude_questions, 
    generate_scenario_questions
)
from db.database import save_interview, get_profile
import asyncio
import re
import edge_tts

# --- BACKGROUND TTS ENGINE ---
import concurrent.futures
if "tts_cache" not in st.session_state:
    st.session_state.tts_cache = {}

def synthesize_question(text, q_id):
    import re as _re
    import asyncio
    import edge_tts
    import tempfile
    import os

    if q_id in st.session_state.tts_cache:
        return st.session_state.tts_cache[q_id]

    # Clean text
    try:
        if isinstance(text, dict): text = text.get('question', str(text))
        elif not isinstance(text, str): text = str(text)
        clean = _re.sub(r'[*_#]', '', text).strip()
        if not clean: return None
    except: return None

    try:
        tf = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tf.close()
        temp_path = tf.name

        async def _amain():
            communicate = edge_tts.Communicate(clean, "en-IN-NeerjaNeural", rate="+10%")
            await communicate.save(temp_path)

        # Handle async execution robustly
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(_amain())

        if os.path.exists(temp_path):
            with open(temp_path, 'rb') as f:
                audio_b = f.read()
            os.remove(temp_path)
            st.session_state.tts_cache[q_id] = audio_b
            return audio_b
        else:
            st.session_state.tts_cache[q_id] = None
            return None
    except Exception as e:
        print(f"TTS Sync Exc: {e}")
        st.session_state.tts_cache[q_id] = None
        return None

from ui.theme import apply_theme, section_header, card
from core.proctor_component import proctor_comp
import json

# --- INITIALIZATION ---
apply_theme()

if "user" not in st.session_state or st.session_state.user is None:
    st.markdown("<div class='premium-warning'>Please authorize via the login protocol first.</div>", unsafe_allow_html=True)
    st.stop()

if "interview_config" not in st.session_state:
    st.switch_page("pages/4_Start_Screening.py")

user_id = st.session_state.user['id']
config = st.session_state.interview_config

# --- STATE GUARD ---
if 'audio_lock' not in st.session_state: st.session_state.audio_lock = False
if 'last_q_index' not in st.session_state: st.session_state.last_q_index = -1

default_states = {
    'current_level': 1, 'tab_switches': 0, 'show_switch_warning': False,
    'consent_given': False, 'face_detected': True, 'face_status': "FOUND", 'detection_buffer': [True] * 15,
    'bounding_box': [0, 0, 0, 0], 'transcript': "", 'l1_answers': {}, 'l2_answers': {},
    'apt_idx': 0, 'scen_idx': 0, 'int_idx': 0, 'show_tutor_msg': None,
    'l1_wrong_cats': [], 'l2_wrong_concepts': [],
    'remaining_time': 600, 'last_timer_update': time.time(),
    'failure_count': 0, 'cam_error': False
}
for k, v in default_states.items():
    if k not in st.session_state: st.session_state[k] = v

# --- AI ENGINES ---
@st.cache_resource
def get_detectors():
    try:
        mp_face = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) if mp_face_detection else None
    except Exception:
        mp_face = None
    haar_face = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    return mp_face, haar_face

def detect_face_production(image_b64):
    if not image_b64: return "NOT_FOUND", [0,0,0,0]
    try:
        mp_detector, haar_detector = get_detectors()
        encoded_data = image_b64.split(',')[1]
        encoded_data += "=" * ((4 - len(encoded_data) % 4) % 4)
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        h, w, _ = img.shape
        num_faces, box = 0, [0, 0, 0, 0]
        
        if mp_detector:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = mp_detector.process(img_rgb)
            if results.detections:
                num_faces = len(results.detections)
                b = results.detections[0].location_data.relative_bounding_box
                box = [int(b.xmin * w), int(b.ymin * h), int(b.width * w), int(b.height * h)]
        
        if num_faces == 0 and haar_detector:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = haar_detector.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
            num_faces = len(faces)
            if num_faces > 0: box = faces[0].tolist()
        
        st.session_state.detection_buffer.pop(0)
        st.session_state.detection_buffer.append(num_faces == 1)
        
        print(f"DEBUG: len(image_b64)={len(image_b64) if image_b64 else 0}, num_faces={num_faces}")
        if num_faces == 0: return "NOT_FOUND", [0,0,0,0]
        if num_faces > 1: return "MULTIPLE", box
        return "FOUND", box
    except Exception as e:
        print(f"FACE DETECTION CRASH: {e}")
        import traceback
        traceback.print_exc()
        return st.session_state.get('face_status', "NOT_FOUND"), [0,0,0,0]


# --- PROCTORING JS ---
silent_host_js = r'''
<script>
    (function() {
        if (window.proctor_active) return;
        window.proctor_active = true;
        let video = document.createElement('video');
        video.id = 'proctor-video'; video.autoplay = true; video.playsinline = true;
        video.style.cssText = "width:100%; border-radius:18px; position:absolute; top:0; left:0; object-fit:cover;";
        let canvas_overlay = document.createElement('canvas');
        canvas_overlay.id = 'proctor-overlay';
        canvas_overlay.style.cssText = "width:100%; height:100%; position:absolute; top:0; left:0; pointer-events:none; z-index:10;";
        function mountHardware() {
            const mount = window.parent.document.querySelector('#proctor-mount');
            if(mount && !mount.contains(video)) {
                mount.appendChild(video); mount.appendChild(canvas_overlay);
                return true;
            }
            return false;
        }
        function startCamera() {
            navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
            .then(stream => {
                video.srcObject = stream;
                setInterval(mountHardware, 1000);
                setInterval(() => {
                    const canvas = document.createElement('canvas');
                    canvas.width = 400; canvas.height = 300;
                    canvas_overlay.width = 640; canvas_overlay.height = 480;
                    if (video.readyState === 4) {
                        canvas.getContext('2d').drawImage(video, 0, 0, 400, 300);
                        const b64 = canvas.toDataURL('image/jpeg', 0.85);
                        const doc = window.parent.document;
                        if (window.parent.setProctorData) {
                            window.parent.setProctorData(b64);
                        }
                        
                        const boxElement = doc.getElementById('proctor-box-data');
                        if (boxElement) {
                            try {
                                const box = JSON.parse(boxElement.textContent);
                                const ctx = canvas_overlay.getContext('2d');
                                ctx.clearRect(0, 0, 640, 480);
                                if(box && box.length === 4 && box[2] > 0) {
                                    ctx.strokeStyle = '#58a6ff'; ctx.lineWidth = 4;
                                    ctx.strokeRect(box[0]*1.6, box[1]*1.6, box[2]*1.6, box[3]*1.6);
                                }
                            } catch(e) {}
                        }
                    }
                }, 1000);
            }).catch(err => {
                const doc = window.parent.document;
                const btns = Array.from(doc.querySelectorAll('button'));
                const camBtn = btns.find(b => b.textContent && b.textContent.includes('\u200b\u200b\u200b'));
                if(camBtn) camBtn.click();
            });
        }
        startCamera();
        window.parent.document.addEventListener('visibilitychange', () => {
            const btns = Array.from(window.parent.document.querySelectorAll('button'));
            if (document.hidden) { 
                const btn = btns.find(b => b.textContent && b.textContent.includes('\u200b') && !b.textContent.includes('\u200b\u200b') && !b.textContent.includes('\u200b '));
                if(btn) btn.click();
            }
            else { 
                const btn = btns.find(b => b.textContent && b.textContent.includes('\u200b '));
                if(btn) btn.click();
            }
        });
    })();
</script>
'''

if st.session_state.consent_given and st.session_state.current_level < 90:
    st.markdown("<style>[data-testid='stVerticalBlock'] > div:has(.sys-gate) { display: none !important; }</style>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='sys-gate'></div>", unsafe_allow_html=True)
        st.markdown(f"<div id='proctor-box-data' style='display:none;'>{json.dumps(st.session_state.bounding_box)}</div>", unsafe_allow_html=True)
        
        incoming_frame = proctor_comp(default="", key="proctor_comp_inst")
        
        if incoming_frame and incoming_frame != "":
            status, box = detect_face_production(incoming_frame)
            st.session_state.face_status = status
            st.session_state.bounding_box = box
            
            if status == "FOUND":
                st.session_state.failure_count = 0
                st.session_state.face_detected = True
            else:
                st.session_state.failure_count += 1
                if st.session_state.failure_count > 6:
                    st.session_state.face_detected = False
        
        if st.button('\u200b\u200b\u200b', key='sys_cam_error'):
            st.session_state.cam_error = True
            st.rerun()
        if st.button('\u200b', key='sys_tab'):
            st.session_state.tab_switches += 1
            if st.session_state.tab_switches >= 3:
                st.session_state.current_level = 99
                st.session_state.show_switch_warning = False
            else:
                st.session_state.show_switch_warning = True
            st.rerun()
        if st.button('\u200b ', key='sys_tab_res'): st.rerun()
    st.components.v1.html(silent_host_js, height=0)

# --- TIMER ---
if st.session_state.consent_given and st.session_state.tab_switches < 3:
    now = time.time()
    if st.session_state.current_level in [1, 2, 3]:
        dt = now - st.session_state.last_timer_update
        st.session_state.remaining_time -= dt
    st.session_state.last_timer_update = now
    if st.session_state.remaining_time <= 0: st.session_state.current_level = 98
else: st.session_state.last_timer_update = time.time()

# --- CONTENT LOADING ---
@st.cache_data(show_spinner=False)
def get_level1_qs(cl): return generate_aptitude_questions(cl)

@st.cache_data(show_spinner=False)
def get_level2_qs(s, cl): return generate_scenario_questions(s, cl)

@st.cache_data(show_spinner=False)
def get_level3_qs(s, cl): 
    qs = generate_interview_questions(s, cl, "")
    if isinstance(qs, dict):
        qs = list(qs.values())
    elif not isinstance(qs, list):
        qs = [str(qs)]
    return qs

if 'apt_qs' not in st.session_state or len(st.session_state.apt_qs) == 0: 
    st.session_state.apt_qs = get_level1_qs(config['class_level'])
if 'scen_qs' not in st.session_state: st.session_state.scen_qs = get_level2_qs(config['subject'], config['class_level'])
if 'int_qs' not in st.session_state: st.session_state.int_qs = get_level3_qs(config['subject'], config['class_level'])[:6]

# --- UI LOGIC ---


level_names = {1: "Level 1: Teaching Fundamentals", 1.5: "Level 1 Cleared", 1.9: "Screening Concluded", 2: "Level 2: Subject Knowledge", 2.5: "Level 2 Cleared", 2.9: "Screening Concluded", 3: "Level 3: AI Interview", 99: "Disqualified"}
current_level = st.session_state.current_level
if current_level >= 90:
    reason = "exceeding the maximum allowed tab switches (3/3)." if current_level == 99 else ("time expiration." if current_level == 98 else "a security violation.")
    
    if not st.session_state.get('disqualified_saved', False):
        try:
            scores = {"clarity": 0, "communication": 0, "problem_solving": 0, "subject_knowledge": 0, "teaching_ability": 0}
            save_interview(user_id, config['subject'], config['class_level'], scores, "Disqualified", f"Auto-failed due to {reason}", st.session_state.transcript, violations_count=st.session_state.tab_switches)
            st.session_state.disqualified_saved = True
        except Exception as e:
            print("Error saving disqualification record:", e)
            
    st.error(f"SESSION TERMINATED: {level_names.get(current_level, 'Security Breach')}")
    st.markdown(f"<div class='premium-card' style='border-left: 5px solid #ea4a5a;'><h3>Integrity Failure</h3><p>Your session has been permanently locked due to {reason}</p></div>", unsafe_allow_html=True)
    st.page_link("app.py", label="Return to Homepage", use_container_width=True)
    st.stop()

elif not st.session_state.consent_given:
    st.markdown(f"""
        <div style='margin-bottom: 35px; padding-top: 5px;'>
            <div style='font-family: inherit; font-size: 2.5rem; font-weight: 800; letter-spacing: -0.03em; color: var(--text-primary); line-height: 1.4; margin-bottom: 8px;'>Assessment <span class='neon-text'>Protocol</span></div>
            <div style='color: var(--text-secondary); font-size: 1.1rem; opacity: 0.9; font-weight: 500;'>Strategic vetting active. Review the mandatory security protocols and gate requirements below before initializing your session.</div>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1: st.markdown("<div class='premium-card' style='text-align:center; padding: 25px 20px;'><p style='color:var(--accent-glow); font-weight:700; margin:0;'>GATE 1 (5/10 Req.)</p><h3 style='margin-top: 5px; margin-bottom: 12px;'>Fundamentals</h3><p style='font-size: 0.95rem; color: var(--text-secondary); line-height: 1.5; margin: 0;'>Evaluates foundational pedagogical knowledge, classroom concepts, and teaching theory.</p></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='premium-card' style='text-align:center; padding: 25px 20px;'><p style='color:var(--accent-secondary); font-weight:700; margin:0;'>GATE 2 (11/15 Req.)</p><h3 style='margin-top: 5px; margin-bottom: 12px;'>Subject Knowledge</h3><p style='font-size: 0.95rem; color: var(--text-secondary); line-height: 1.5; margin: 0;'>Assesses teaching methodology, scenario logic, and classroom management techniques.</p></div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='premium-card' style='text-align:center; padding: 25px 20px;'><p style='color:#bc8cff; font-weight:700; margin:0;'>GATE 3 (Audio AI)</p><h3 style='margin-top: 5px; margin-bottom: 12px;'>AI Proctored Interview</h3><p style='font-size: 0.95rem; color: var(--text-secondary); line-height: 1.5; margin: 0;'>Proctors spoken subject-matter expertise and interpersonal communication skills.</p></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: rgba(234, 74, 90, 0.05); border: 1px solid rgba(234, 74, 90, 0.2); padding: 25px; border-radius: 12px; margin-bottom: 30px; margin-top: 10px;'>
        <h4 style='color: #ea4a5a !important; margin-bottom: 15px; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 0.1em;'><span style='margin-right: 8px;'>🚨</span>STRICT PROCTORING RULES ENFORCED</h4>
        <ul style='color: var(--text-primary); font-size: 1.05rem; line-height: 1.8; margin: 0; padding-left: 20px; font-weight: 500;'>
            <li><b>Tab Switch Termination:</b> Browser visibility is monitored. Exactly 3 tab switches or window unfocus events will permanently terminate your session.</li>
            <li><b>Clipboard Lock:</b> Copying and pasting are strictly prohibited.</li>
            <li><b>Continuous Video Oversight:</b> Your webcam is monitored by an AI neural face-lock engine. Moving significantly out of frame triggers a system flag.</li>
            <li><b>Consecutive Gates:</b> Failure to meet the minimal requirements at any Gate will automatically eject you from the assessment.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Acknowledge Rules & Initialize Assessment", type="primary", use_container_width=True):
        st.session_state.consent_given = True
        st.session_state.remaining_time = 600
        st.session_state.last_timer_update = time.time()
        st.rerun()

else:
    col_main, col_side = st.columns([2.5, 1], gap="large")
    with col_side:
        st.markdown('<div id="proctor-mount" style="width:100%; aspect-ratio: 4/3; background: #000; border-radius:18px; overflow:hidden; border: 2px solid rgba(88,166,255,0.1);"></div>', unsafe_allow_html=True)
        m_m, m_s = divmod(int(st.session_state.remaining_time), 60)
        
        status_colors = {"FOUND": "#3fb950", "NOT_FOUND": "#ea4a5a", "MULTIPLE": "#ff9b05"}
        status_labels = {"FOUND": "FACE FOUND", "NOT_FOUND": "FACE NOT FOUND", "MULTIPLE": "MULTIPLE FACES"}
        clr = status_colors.get(st.session_state.face_status, "#8b949e")
        lbl = status_labels.get(st.session_state.face_status, "INITIALIZING...")
        
        st.markdown(f"<div class='premium-card' style='margin-top: 15px; text-align:center;'><p style='font-size:0.7rem; color:var(--text-muted); margin:0;'>TIME REMAINING</p><h2>{'%02d:%02d' % (m_m, m_s)}</h2><p style='color: {clr}; font-size:0.8rem; font-weight:700; margin-bottom: 5px;'>{lbl}</p><p style='color: #8b949e; font-size:0.75rem; font-weight: 600; margin-top: 10px; margin-bottom: 0px;'>TAB SWITCHES: <span style='color: {'#ea4a5a' if st.session_state.tab_switches > 0 else '#8b949e'};'>{st.session_state.tab_switches}</span> / 3</p></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("End Screening", type="secondary", use_container_width=True):
            st.switch_page("pages/3_Dashboard.py")

    with col_main:
        section_header(level_names.get(current_level), "")
        
        if current_level in [1, 2, 3]:
            if st.session_state.cam_error:
                st.error("🚨 CAMERA PROTOCOL FAILED: Access denied or device disconnected. Please check permissions.")
            elif st.session_state.face_status == "NOT_FOUND" and st.session_state.failure_count > 6:
                st.warning("⚠️ PROCTOR WARNING: Face is out of frame. Please return to the camera view.")
            elif st.session_state.face_status == "MULTIPLE":
                st.error("🚨 SECURITY ALERT: Multiple faces detected in frame. Please ensure you are alone.")
            
        if st.session_state.show_switch_warning:
            st.error("🚨 INTEGRITY BREACH: Unauthorized window shift detected.")
            if st.button("RE-VALIDATE AND RESUME", type="primary", use_container_width=True):
                st.session_state.show_switch_warning = False; st.rerun()
            st.stop()

        # ===================== LEVEL 1 =====================
        if current_level == 1:
            total_qs = 10
            curr_q = min(st.session_state.apt_idx + 1, total_qs)
            st.progress(curr_q / total_qs)
            st.markdown(f"<div style='text-align: right; color: var(--text-muted); font-size: 0.9rem; margin-bottom: 15px;'>Question {curr_q} of {total_qs}</div>", unsafe_allow_html=True)
            q = st.session_state.apt_qs[min(st.session_state.apt_idx, 9)]
            st.markdown(f"<div class='premium-card'><h3 style='margin-bottom:20px;'>Q{curr_q}. {q['question']}</h3>", unsafe_allow_html=True)
            
            def _submit_l1():
                ans = st.session_state.get(f"rad_apt_{st.session_state.apt_idx}")
                if ans is None:
                    st.session_state.l1_err = "Please select an option before submitting."
                else:
                    st.session_state.l1_answers[st.session_state.apt_idx] = ans
                    st.session_state.apt_idx += 1
                    st.session_state.l1_err = None
                    if st.session_state.apt_idx >= 10:
                        score = sum(1 for i, a in st.session_state.l1_answers.items() if a == st.session_state.apt_qs[i]['answer'])
                        st.session_state.current_level = 1.5 if score >= 5 else 1.9

            st.radio("Choose the correct option:", q['options'], key=f"rad_apt_{st.session_state.apt_idx}", index=None)
            if st.session_state.get("l1_err"): st.warning(st.session_state.l1_err)
            
            btn_text = "Submit Level 1" if curr_q == 10 else "Submit Answer"
            st.button(btn_text, type="primary", use_container_width=True, on_click=_submit_l1, key=f"btn_apt_{st.session_state.apt_idx}")
            st.markdown("</div>", unsafe_allow_html=True)

        # ===================== LEVEL 1.5 =====================
        elif current_level == 1.5:
            score = sum(1 for i, a in st.session_state.l1_answers.items() if a == st.session_state.apt_qs[i]['answer'])
            st.markdown(f"<div class='premium-card' style='text-align: center; border-left: 5px solid #3fb950; margin-bottom:20px;'><h2 style='color:#3fb950; margin-bottom: 5px;'>Congratulations!</h2><p style='font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 20px;'>You successfully cleared Level 1 with a score of <b>{score}/10</b>.</p><p style='font-size: 0.95rem; margin-bottom: 30px;'>Level 2 assesses core subject knowledge and mastery. Once you begin, a fresh 15-minute timer will activate.</p></div>", unsafe_allow_html=True)
            if st.button("Start Level 2", type="primary", use_container_width=True):
                st.session_state.current_level = 2
                st.session_state.remaining_time = 900
                st.session_state.last_timer_update = time.time()
                st.rerun()

        # ===================== LEVEL 1.9 / 2.9 =====================
        elif current_level == 1.9 or current_level == 2.9:
            lvl_num = 1 if current_level == 1.9 else 2
            score_num = sum(1 for i, a in st.session_state.l1_answers.items() if a == st.session_state.apt_qs[i]['answer']) if lvl_num == 1 else sum(1 for i, a in st.session_state.l2_answers.items() if a == st.session_state.scen_qs[i]['answer'])
            total_qs = 10 if lvl_num == 1 else 15
            
            st.markdown(f"<div class='premium-card' style='text-align: center; border-left: 5px solid #8b949e;'><h2 style='color:#c9d1d9; margin-bottom: 5px;'>Assessment Completed</h2><p style='font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 20px;'>Thank you for participating! You scored <b>{score_num}/{total_qs}</b> on Level {lvl_num}.</p><p style='font-size: 0.95rem; line-height: 1.6; margin-bottom: 30px;'>While this score doesn't meet the critical threshold for the next phase, we truly appreciate your effort. Your application indicates strong potential, and we encourage you to hone your pedagogical strategies and apply again in the future!</p></div>", unsafe_allow_html=True)
            st.page_link("pages/3_Dashboard.py", label="Return to Dashboard", use_container_width=True)

        # ===================== LEVEL 2 =====================
        elif current_level == 2:
            total_qs = 15
            curr_q = min(st.session_state.scen_idx + 1, total_qs)
            st.progress(curr_q / total_qs)
            st.markdown(f"<div style='text-align: right; color: var(--text-muted); font-size: 0.9rem; margin-bottom: 15px;'>Question {curr_q} of {total_qs}</div>", unsafe_allow_html=True)
            q = st.session_state.scen_qs[min(st.session_state.scen_idx, 14)]
            st.markdown(f"<div class='premium-card'><h3 style='margin-bottom:20px;'>Q{curr_q}. {q['question']}</h3>", unsafe_allow_html=True)
            
            def _submit_l2():
                ans = st.session_state.get(f"rad_scen_{st.session_state.scen_idx}")
                if ans is None:
                    st.session_state.l2_err = "Please select an option before submitting."
                else:
                    st.session_state.l2_answers[st.session_state.scen_idx] = ans
                    st.session_state.scen_idx += 1
                    st.session_state.l2_err = None
                    if st.session_state.scen_idx >= 15:
                        score = sum(1 for i, a in st.session_state.l2_answers.items() if a == st.session_state.scen_qs[i]['answer'])
                        st.session_state.current_level = 2.5 if score >= 11 else 2.9

            st.radio("Select Answer:", q['options'], key=f"rad_scen_{st.session_state.scen_idx}", index=None)
            if st.session_state.get("l2_err"): st.warning(st.session_state.l2_err)
            
            btn_text = "Submit Level 2" if curr_q == 15 else "Submit Answer"
            st.button(btn_text, type="primary", use_container_width=True, on_click=_submit_l2, key=f"btn_scen_{st.session_state.scen_idx}")
            st.markdown("</div>", unsafe_allow_html=True)

        # ===================== LEVEL 2.5 =====================
        elif current_level == 2.5:
            score = sum(1 for i, a in st.session_state.l2_answers.items() if a == st.session_state.scen_qs[i]['answer'])
            st.markdown(f"<div class='premium-card' style='text-align: center; border-left: 5px solid #3fb950; margin-bottom:20px;'><h2 style='color:#3fb950; margin-bottom: 5px;'>Level 2 Cleared!</h2><p style='font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 20px;'>You successfully cleared Level 2 with a score of <b>{score}/15</b>.</p><p style='font-size: 0.95rem; margin-bottom: 30px;'>Level 3 is an oral AI-driven interview. This final stage requires microphone access. Once you begin, a fresh 30-minute timer will activate.</p></div>", unsafe_allow_html=True)
            if st.button("Start Level 3", type="primary", use_container_width=True):
                st.session_state.current_level = 3
                st.session_state.remaining_time = 1800
                st.session_state.last_timer_update = time.time()
                st.rerun()

        # ===================== LEVEL 3 =====================
        elif current_level == 3:
            try:
                total_qs = 6
                curr_q = min(st.session_state.int_idx + 1, total_qs)
                st.progress(curr_q / total_qs)
                st.caption(f"Question {curr_q} of {total_qs}")
    
                idx_to_fetch = min(st.session_state.int_idx, len(st.session_state.int_qs) - 1)
                q = st.session_state.int_qs[idx_to_fetch] if idx_to_fetch >= 0 else "Error: No questions loaded."
                st.session_state.last_q_index = st.session_state.int_idx
    
                idx      = st.session_state.int_idx
                import hashlib
                aud_key  = f"aud_{hashlib.md5(q.encode()).hexdigest()}"
                draft_key = f"l3_draft_{idx}"
                autoplay_key = f"l3_autoplay_{idx}"
    
                # ── Generate and cache TTS audio bytes ──
                if aud_key not in st.session_state:
                    with st.spinner("⏳ Synthesizing AI Voice Module... please wait (~5s)..."):
                        result = synthesize_question(q, aud_key)
                        st.session_state[aud_key] = result
                        st.session_state[autoplay_key] = True
    
                audio_bytes = st.session_state.get(aud_key, None)
    
                # ── Ensure q is cleanly formatted ──
                if isinstance(q, dict):
                    q = q.get('question', str(q))
                elif not isinstance(q, str):
                    q = str(q)
    
                # ── Question card ──
                st.markdown(f"""
                    <div class='premium-card'>
                        <h3 style='margin-bottom:14px;'>Q{curr_q}. {q}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                # ── Audio player ──
                if audio_bytes:
                    should_autoplay = st.session_state.get(autoplay_key, False)
                    auto_attr = "autoplay" if should_autoplay else ""
                    
                    import base64
                    b64_audio = base64.b64encode(audio_bytes).decode()
                    st.markdown(f"""
                        <audio id="l3-audio-player" class="sys-audio" controls {auto_attr} style="width: 100%; border-radius: 12px; margin-bottom: 20px; outline: none; border: 1px solid rgba(88,166,255,0.2); background: rgba(0,0,0,0.2);">
                            <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
                        </audio>
                    """, unsafe_allow_html=True)
                    st.session_state[autoplay_key] = False
                else:
                    st.warning("⚠️ Audio unavailable — please read the question above and record your answer.")
    
                st.markdown("<br>", unsafe_allow_html=True)


                # ── Branch A: answer already transcribed ───────────────────────
                if st.session_state.get(draft_key):
                    val = st.session_state[draft_key]
                    if val == "PROCESSING_AUDIO":
                        st.markdown("<div class='premium-card' style='text-align:center;'><h4>⏳ Transcribing your answer securely in the background...</h4><p style='color:var(--text-muted);'>Please remain in frame while we evaluate your vocal nuances.</p></div>", unsafe_allow_html=True)
                    elif val.startswith("ERROR_AUDIO:"):
                        st.error(f"Transcription Failed: {val.replace('ERROR_AUDIO:', '')}")
                        if st.button("Retry Recording", type="primary"):
                            del st.session_state[draft_key]
                            st.rerun()
                    else:
                        st.markdown(
                            f"<div style='background:rgba(88,166,255,0.08); padding:14px 18px; border-radius:10px;"
                            f"border-left:3px solid #58a6ff; font-style:italic; margin-bottom:18px;'>"
                            f"<p style='color:#58a6ff; font-weight:700; margin:0 0 6px 0;'>📝 Your Transcribed Answer</p>"
                            f"<p style='margin:0;'>{st.session_state[draft_key]}</p></div>",
                            unsafe_allow_html=True
                        )
        
                        c1, c2, c3 = st.columns(3)
        
                        with c1:
                            # Replay = just rerun; audio player re-renders (autoplay stays False = manual replay via player)
                            if st.button("🔁 Replay Question", use_container_width=True, key=f"replay_{idx}"):
                                st.session_state[autoplay_key] = True
                                st.rerun()
        
                        with c2:
                            def _re_record():
                                del st.session_state[draft_key]
                                v_key = f"v_int_{st.session_state.int_idx}"
                                if v_key in st.session_state:
                                    del st.session_state[v_key]
                            st.button("🎙️ Re-Record", use_container_width=True,
                                      on_click=_re_record, key=f"rerecord_{idx}")
        
                        with c3:
                            btn_txt = "✅ Submit Final Answer" if curr_q == 6 else "➡️ Next Question"
                            def _submit_l3():
                                st.session_state.transcript += f"AI: {q}\nCandidate: {st.session_state[draft_key]}\n\n"
                                st.session_state.int_idx += 1
                                if st.session_state.int_idx >= 6:
                                    st.session_state.current_level = 4
                            st.button(btn_txt, type="primary", use_container_width=True,
                                      on_click=_submit_l3, key=f"submit_l3_{idx}")
    
                # ── Branch B: waiting for speech input ────────────────────────
                else:
                    st.markdown(
                        "<p style='color:#3fb950; font-weight:700; margin-bottom:10px;'>"
                        "🎙️ Listen to the question above, then record your answer:</p>",
                        unsafe_allow_html=True
                    )
                    
                    audio_val = mic_recorder(
                        start_prompt="🎙️ Start Recording",
                        stop_prompt="⏹️ Stop & Finalize",
                        just_once=True,
                        key=f"v_int_{idx}"
                    )
                    
                    if audio_val is not None and 'bytes' in audio_val:
                        st.session_state[draft_key] = "PROCESSING_AUDIO"
                        audio_data = audio_val['bytes']
                        
                        def _bg_transcribe(audio_b, d_key):
                            import tempfile, os
                            from core.groq_api import get_whisper_transcription
                            try:
                                tf = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
                                tf.write(audio_b)
                                tf.close()
                                spoken = get_whisper_transcription(tf.name)
                                os.remove(tf.name)
                                
                                if spoken and not spoken.startswith("Transcription error:") and not spoken.startswith("API key missing"):
                                    st.session_state[d_key] = spoken
                                else:
                                    st.session_state[d_key] = "ERROR_AUDIO:" + spoken
                            except Exception as e:
                                st.session_state[d_key] = "ERROR_AUDIO:" + str(e)
                                
                        import threading
                        from streamlit.runtime.scriptrunner import add_script_run_ctx
                        t = threading.Thread(target=_bg_transcribe, args=(audio_data, draft_key))
                        add_script_run_ctx(t)
                        t.start()
                        st.rerun()
            except Exception as e:
                import traceback
                st.error(f"CRITICAL UI CRASH IN LEVEL 3: {traceback.format_exc()}")



                # ===================== LEVEL 4 — EVALUATION =====================
        elif current_level == 4:
            st.balloons()
            st.markdown("<h1>Test submitted <span class='neon-text'>successfully!</span></h1>", unsafe_allow_html=True)
            st.markdown("<p style='color: var(--text-secondary); text-align: center; margin-bottom: 30px;'>Synchronizing holistic 3-level evaluation matrix. Please do not close this window...</p>", unsafe_allow_html=True)
            
            with st.spinner("Processing comprehensive evaluation..."):
                l1_data = getattr(st.session_state, 'l1_answers', {})
                l2_data = getattr(st.session_state, 'l2_answers', {})
                apt_qs = getattr(st.session_state, 'apt_qs', [])
                scen_qs = getattr(st.session_state, 'scen_qs', [])

                l1_summary = "\n".join([f"L1 Q: {apt_qs[i]['question']} | User Ans: {a} | Correct Ans: {apt_qs[i]['answer']}" for i, a in l1_data.items() if i < len(apt_qs)])
                l2_summary = "\n".join([f"L2 Q: {scen_qs[i]['question']} | User Ans: {a} | Correct Ans: {scen_qs[i]['answer']}" for i, a in l2_data.items() if i < len(scen_qs)])

                evaluation = evaluate_interview(st.session_state.transcript, config['subject'], config['class_level'], l1_summary, l2_summary)
                save_interview(user_id, config['subject'], config['class_level'], evaluation['scores'], evaluation['verdict'], evaluation['insights'], st.session_state.transcript, evaluation['strengths'], evaluation['weaknesses'])
                st.session_state.evaluation = evaluation
                st.switch_page("pages/6_Evaluation_Insights.py")