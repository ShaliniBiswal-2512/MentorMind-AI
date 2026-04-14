from gtts import gTTS
import base64
from io import BytesIO

def generate_tts_base64(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        b64 = base64.b64encode(fp.read()).decode()
        return b64
    except Exception as e:
        print("TTS Error:", e)
        return None

def get_audio_html(b64_audio):
    if not b64_audio:
        return ""
    audio_html = f'''
        <script>
            var base64_str = "data:audio/mp3;base64,{b64_audio}";
            try {{
                var parentDom = window.parent.document;
                var audio = parentDom.getElementById("ai-audio-player");
                if(!audio) {{
                    audio = parentDom.createElement("audio");
                    audio.id = "ai-audio-player";
                    parentDom.body.appendChild(audio);
                }}
                audio.src = base64_str;
                audio.playbackRate = 1.2;

                var isAI_Speaking = true;
                var _lastState = null;

                function applyState() {{
                    var styles = `
                        <style>
                        @keyframes ai-wave {{ 
                            0%, 100% {{ transform: scaleY(0.4); opacity: 0.5; }} 
                            50% {{ transform: scaleY(1); opacity: 1; }} 
                        }}
                        @keyframes glow-pulse {{
                            0%, 100% {{ box-shadow: 0 0 5px rgba(88, 166, 255, 0.2); }}
                            50% {{ box-shadow: 0 0 15px rgba(88, 166, 255, 0.5); }}
                        }}
                        .sc-wave-container {{ display: flex; align-items: center; height: 18px; gap: 4px; margin-left: auto; }}
                        .sc-wave-ai {{ width: 3px; background: #58a6ff; border-radius: 4px; height: 100%; }}
                        .sc-wave-ai:nth-child(1) {{ animation: ai-wave 1.2s infinite 0.1s; }}
                        .sc-wave-ai:nth-child(2) {{ animation: ai-wave 1.4s infinite 0.3s; }}
                        .sc-wave-ai:nth-child(3) {{ animation: ai-wave 1.0s infinite 0.6s; }}
                        .sc-wave-ai:nth-child(4) {{ animation: ai-wave 1.3s infinite 0.2s; }}
                        .sc-wave-ai:nth-child(5) {{ animation: ai-wave 1.1s infinite 0.4s; }}
                        .sc-wave-user {{ width: 4px; background: #3fb950; border-radius: 2px; height: 12px; opacity: 0.3; }}
                        .sc-btn-premium {{
                            background: rgba(88, 166, 255, 0.1);
                            border: 1px solid rgba(88, 166, 255, 0.3);
                            color: #58a6ff;
                            border-radius: 30px;
                            padding: 6px 14px;
                            font-size: 0.8rem;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            gap: 6px;
                            font-family: inherit;
                            font-weight: 600;
                            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                        }}
                        .sc-btn-premium:hover {{
                            background: rgba(88, 166, 255, 0.2);
                            border-color: #58a6ff;
                            transform: translateY(-1px);
                            box-shadow: 0 4px 12px rgba(88, 166, 255, 0.2);
                        }}
                        </style>
                    `;

                    var statusEl = parentDom.getElementById('ai-speaking-status');
                    if(statusEl && _lastState !== isAI_Speaking) {{
                        _lastState = isAI_Speaking;
                        if(isAI_Speaking) {{
                            statusEl.innerHTML = styles + `
                                <div style="font-family: 'Inter', sans-serif; display: flex; align-items: center; background: rgba(13, 17, 23, 0.6); backdrop-filter: blur(10px); padding: 10px 20px; border-radius: 14px; border: 1px solid rgba(88, 166, 255, 0.2); width: 100%; box-shadow: 0 8px 32px rgba(0,0,0,0.2); margin-top: 5px; animation: glow-pulse 3s infinite;">
                                    <div style="background: rgba(88, 166, 255, 0.1); width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px;">
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#58a6ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v1a7 7 0 0 1-14 0v-1"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>
                                    </div>
                                    <div style="display: flex; flex-direction: column; flex-grow: 1;">
                                        <div style="color: #58a6ff; font-size: 0.95rem; font-weight: 700; letter-spacing: 0.3px; display: flex; align-items: center; gap: 8px;">
                                            SYSTEM SPEAKING
                                            <span style="width: 6px; height: 6px; background: #58a6ff; border-radius: 50%; display: inline-block;"></span>
                                        </div>
                                        <span style="color: #8b949e; font-size: 0.8rem; font-weight: 500;">Listening to responses...</span>
                                    </div>
                                    <div class="sc-wave-container">
                                        <div class="sc-wave-ai"></div><div class="sc-wave-ai"></div><div class="sc-wave-ai"></div><div class="sc-wave-ai"></div><div class="sc-wave-ai"></div>
                                    </div>
                                </div>
                            `;
                        }} else {{
                            statusEl.innerHTML = styles + `
                                <div style="font-family: 'Inter', sans-serif; display: flex; align-items: center; background: rgba(13, 17, 23, 0.6); backdrop-filter: blur(10px); padding: 10px 20px; border-radius: 14px; border: 1px solid rgba(63, 185, 80, 0.2); width: 100%; box-shadow: 0 8px 32px rgba(0,0,0,0.2); margin-top: 5px;">
                                    <div style="background: rgba(63, 185, 80, 0.1); width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px;">
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3fb950" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v1a7 7 0 0 1-14 0v-1"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>
                                    </div>
                                    <div style="display: flex; flex-direction: column; flex-grow: 1;">
                                        <div style="color: #3fb950; font-size: 0.95rem; font-weight: 700; letter-spacing: 0.3px;">YOUR TURN</div>
                                        <span style="color: #8b949e; font-size: 0.8rem; font-weight: 500;">Mic unlocked. Speak now.</span>
                                    </div>
                                    <div style="display: flex; align-items: center; margin-right: 15px;">
                                        <button class="sc-btn-premium" onclick="window.parent.replayInterviewAudio()">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                                            REPLAY
                                        </button>
                                    </div>
                                    <div class="sc-wave-container">
                                        <div class="sc-wave-user"></div><div class="sc-wave-user"></div><div class="sc-wave-user"></div>
                                    </div>
                                </div>
                            `;
                        }}
                    }}
                    
                    var iframes = parentDom.querySelectorAll('iframe');
                    iframes.forEach(function(i) {{
                        if(i.title && (i.title.includes("mic_recorder") || i.title.includes("speech_to_text"))) {{
                            var container = i.parentElement;
                            if(isAI_Speaking) {{
                                container.style.opacity = '0.3';
                                container.style.pointerEvents = 'none';
                                container.style.transition = 'opacity 0.3s';
                            }} else {{
                                container.style.opacity = '1';
                                container.style.pointerEvents = 'auto';
                            }}
                        }}
                    }});
                }}

                // Expose a global replay function to the parent Streamlit window
                window.parent.replayInterviewAudio = function() {{
                    if(audio) {{
                        audio.currentTime = 0;
                        audio.play();
                    }}
                }};
                
                audio.onplay = function() {{ isAI_Speaking = true; applyState(); }};
                audio.onended = function() {{ 
                    isAI_Speaking = false; 
                    applyState(); 
                    if(window.parent.triggerSystemEvent) window.parent.triggerSystemEvent('SYS_READ_DONE');
                }};
                audio.onerror = function() {{ 
                    isAI_Speaking = false; 
                    applyState(); 
                    if(window.parent.triggerSystemEvent) window.parent.triggerSystemEvent('SYS_READ_DONE');
                }};
                
                // Polling handles cases where Streamlit's React tree mounts the mic iframe late,
                // or if it reuses an old div container with stuck pointerEvents.
                setInterval(applyState, 300);

                var playPromise = audio.play();
                if (playPromise !== undefined) {{
                    playPromise.catch(function(error) {{
                        // Autoplay blocked by browser policy, fallback to enabling mic manually
                        isAI_Speaking = false;
                        applyState();
                        if(window.parent.triggerSystemEvent) window.parent.triggerSystemEvent('SYS_READ_DONE');
                    }});
                }}
            }} catch(e) {{
                console.log("Cross-origin parent DOM restriction:", e);
            }}
        </script>
    '''
    return audio_html
