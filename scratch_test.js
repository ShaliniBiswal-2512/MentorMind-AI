
    // 0. CORE STEALTH: Hide any SYS_ button immediately before they even render fully
    const enforceHardStealth = () => {
        const P = window.parent;
        if(!P) return;
        P.document.querySelectorAll('button').forEach(btn => {
            const txt = btn.textContent || "";
            if (txt.includes('SYS_')) {
                const container = btn.closest('[data-testid="element-container"]');
                if (container) { 
                    container.style.position = 'absolute';
                    container.style.top = '0';
                    container.style.left = '0';
                    container.style.width = '1px';
                    container.style.height = '1px';
                    container.style.opacity = '0.01';
                    container.style.overflow = 'hidden';
                    container.style.pointerEvents = 'none'; // Only the button inside will be clicked programmatically
                }
            }
        });
    };
    setInterval(enforceHardStealth, 10); // High frequency check

    const SID = "{config.get('session_id', 'global')}";
    const LVL = "1";
    const P = window.parent;
    
    // NUCLEAR RESET: Purge everything and start over
    P.killAndRestartPortal = () => {
        if(P.mm_HardwareHost) P.mm_HardwareHost.stop();
        P.portalEngine.stream = null;
        P.portalEngine.recorder = null;
        P.portalEngine.chunks = [];
        P.portalEngine.isStarting = false;
        P.portalEngine.aiPollingStarted = false;
        
        const mounts = P.document.querySelectorAll('.core-cam-mount');
        mounts.forEach(m => delete m.dataset.aiRunning);
        
        // Signal Streamlit to rerun via a dummy button if needed
        triggerSystemEvent('SYS_CAM_READY'); 
    };

    if (P && "false" === "false") {
        P.camRdy = false;
    }

    const triggerSystemEvent = (actionName) => {
        if(!P) return;
        const btns = Array.from(P.document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent && b.textContent.includes(actionName));
        if(btn) btn.click();
    };

    // 1. GLOBAL TIMER (Accumulating only when face is present and tab active)
    const runGlobalTimer = () => {
        let max_sec = (LVL === '3') ? 1800 : ((LVL === '2') ? 900 : 600); 
        
        let elapsed = parseFloat(localStorage.getItem('mm_elapsed_' + SID + '_L' + LVL) || '0');
        let lastTick = parseFloat(localStorage.getItem('mm_lastTick_' + SID + '_L' + LVL) || Date.now().toString());
        
        let now = Date.now();
        let delta = (now - lastTick) / 1000.0;
        
        let isFocused = !P.document.hidden;
        // If proctoring is off, faceState might not update, so assume true if not explicitly LOST
        let isFaceVisible = (P.portalEngine.faceState === 'FOUND' || "true" === "false");
        
        if (isFocused && isFaceVisible) {
            elapsed += delta;
            localStorage.setItem('mm_elapsed_' + SID + '_L' + LVL, elapsed.toString());
        }
        localStorage.setItem('mm_lastTick_' + SID + '_L' + LVL, now.toString());
        
        let rem = max_sec - elapsed;
        if (rem < 0) rem = 0;
        
        const m = Math.floor(rem / 60).toString().padStart(2, '0');
        const s = Math.floor(rem % 60).toString().padStart(2, '0');
        
        const timerUI = P.document.getElementById('global-timer');
        if(timerUI) timerUI.innerText = m + ":" + s;
        // Global timeout logic can be handled natively by python when they try to reply but elapsed is > max_sec
    };

    // Initialize strikes on parent to persist across iframe refreshes
    if (typeof P.mm_strikes === 'undefined') {
        P.mm_strikes = parseInt("0");
    }

    // 3. TAB PROTECTION & NAVIGATION GUARD
    if (!P.securityArmed) {
        P.document.addEventListener('visibilitychange', () => {
            if (P.document.hidden) {
                P.mm_strikes++;
                triggerSystemEvent('SYS_TAB_EVENT');
                setTimeout(() => {
                    alert("🚨 STRICT WARNING (Strike " + P.mm_strikes + "/3): Tab switching is strictly prohibited. Your activity has been logged. The session will terminate automatically on the 3rd strike.");
                }, 100);
            }
        });
        
        // Focus Monitoring
        P.window.addEventListener('blur', () => {
            console.log("Window blur detected - suspicious activity.");
        });
        // Sidebar link protection
        const protectSidebar = () => {
            if(!P) return;
            const links = P.document.querySelectorAll('[data-testid="stSidebarNav"] a, [data-testid="stSidebar"] a, a[data-testid="stSidebarNavLink"]');
            links.forEach(link => {
                if(!link.dataset.guarded) {
                    link.dataset.guarded = 'true';
                    link.onclick = (e) => {
                        const proceed = confirm("🚨 WARNING: Navigating away via the sidebar will immediately TERMINATE your interview. Any unsaved progress will be lost.\n\nDo you want to proceed and terminate the session?");
                        if (proceed) {
                            triggerSystemEvent('SYS_END_SECTION');
                        } else {
                            e.preventDefault();
                            e.stopPropagation();
                            return false;
                        }
                    };
                }
            });
        };
        setInterval(protectSidebar, 500);

        P.onbeforeunload = (e) => {
            e.preventDefault();
            e.returnValue = "WARNING: Leaving this page results in immediate disqualification.";
            return e.returnValue;
        };
        
        // --- STRICT PROCTORING: INPUT PROTECTION ---
        P.document.addEventListener('contextmenu', e => e.preventDefault());
        P.document.addEventListener('paste', e => e.preventDefault());
        P.document.addEventListener('copy', e => e.preventDefault());
        P.document.addEventListener('cut', e => e.preventDefault());
        
        P.document.addEventListener('keydown', e => {
            // Block Ctrl+C, Ctrl+V, Ctrl+U (source), F12, Ctrl+Shift+I (inspect)
            if (e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'u' || e.key === 'j' || e.key === 'i')) {
                e.preventDefault();
                alert("🚨 SECURITY ALERT: Unauthorized keyboard shortcut blocked.");
            }
            if (e.key === 'F12') {
                e.preventDefault();
                alert("🚨 SECURITY ALERT: Developer Tools access is prohibited.");
            }
        });
        
        P.securityArmed = true;
    }

    // 4. PORTAL ENGINE (CAMERA & AI)
    if (typeof P.portalEngine === 'undefined') {
        P.portalEngine = { stream: null, recorder: null, chunks: [], fApiLoaded: false };
    }
    // Safely recover from interrupted iframe reloads
    P.portalEngine.isStarting = false;
    if (P.mm_HardwareHost) P.mm_HardwareHost.isRequesting = false;

    // 4. NATIVE HARDWARE HOST (Sandbox Bypass)
    if (!P.mm_HardwareHost) {
        const hostScript = P.document.createElement('script');
        hostScript.id = 'mm-hardware-host';
        hostScript.textContent = `
            window.mm_HardwareHost = {
                stream: null,
                isRequesting: false,
                request: async function(options) {
                    if (this.isRequesting) return;
                    this.isRequesting = true;
                    try {
                        console.log("HardwareHost: Requesting permissions in parent context...");
                        // Attempt combined first
                        this.stream = await navigator.mediaDevices.getUserMedia(options);
                        return this.stream;
                    } catch (err) {
                        console.warn("HardwareHost: Combined request failed, trying Video-only fallback:", err);
                        // Fallback: Video only
                        try {
                            this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                            return this.stream;
                        } catch (vErr) {
                            console.error("HardwareHost: Total hardware failure:", vErr);
                            throw vErr;
                        }
                    } finally {
                        this.isRequesting = false;
                    }
                },
                stop: function() {
                    if(this.stream) this.stream.getTracks().forEach(t => t.stop());
                    this.stream = null;
                }
            };
        `;
        P.document.head.appendChild(hostScript);
    }

    const managePortal = () => {
        const mounts = Array.from(P.document.querySelectorAll('.core-cam-mount'));
        if (mounts.length === 0) return;
        
        // Always try to attach to all detected mounts in case Streamlit DOM leaves zombies
        mounts.forEach(mount => startHardware(mount));
    };

    const startHardware = async (mount) => {
        if (P.portalEngine.isStarting) return;
        const video = mount.querySelector('video');
        const loader = mount.querySelector('.portal-loading');
        
        let isDead = false;
        if (P.portalEngine.stream) {
            if (!P.portalEngine.stream.active) isDead = true;
            if (P.portalEngine.stream.getTracks().some(t => t.readyState === 'ended')) isDead = true;
        }

        if (P.portalEngine.stream && isDead) {
            P.portalEngine.stream = null; // Stream died due to iframe recreate
        }

        if (P.portalEngine.stream) {
            if (video && (video.srcObject !== P.portalEngine.stream || video.paused)) {
                video.srcObject = P.portalEngine.stream;
                video.muted = true;
                video.play().catch(e => {});
            }
            // Force hide initial loader if stream is active
            if (loader && !P.portalEngine.aiStatusActive) loader.style.display = 'none';
        } else {
            P.portalEngine.isStarting = true;
            try {
                if (loader) {
                    loader.style.display = 'block';
                    loader.innerHTML = "Requesting Hardware Permissions...";
                }
                
                // USE NATIVE PARENT HOST (Bypasses Iframe Sandbox)
                const stream = await P.mm_HardwareHost.request({ video: true, audio: true });
                if (!stream) throw new Error("Hardware stream not acquired. Camera blocked by user or hardware error.");
                P.portalEngine.stream = stream;
                if (video) {
                    video.srcObject = stream;
                    video.muted = true;
                    video.play().catch(e => {});
                }
                try {
                    const recorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8,opus' });
                    P.portalEngine.recorder = recorder;
                    recorder.ondataavailable = (e) => { if (e.data.size > 0) P.portalEngine.chunks.push(e.data); };
                    recorder.start(1000);
                } catch (re) {
                    console.warn("MediaRecorder init failed, trying generic webm fallback:", re);
                    try {
                        const fallbackRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
                        P.portalEngine.recorder = fallbackRecorder;
                        fallbackRecorder.ondataavailable = (e) => { if (e.data.size > 0) P.portalEngine.chunks.push(e.data); };
                        fallbackRecorder.start(1000);
                    } catch (e2) { console.error("MediaRecorder completely failed:", e2); }
                }
                
                P.stopAndSaveInterviewVideo = async (sid) => {
                    if(P.mm_HardwareHost) P.mm_HardwareHost.stop();
                    return new Promise((resolve) => {
                        const finish = () => { if (typeof triggerSystemEvent === 'function') triggerSystemEvent('SYS_VIDEO_SAVED'); resolve(); };
                        if (!P.portalEngine.recorder || P.portalEngine.recorder.state === "inactive") { finish(); return; }
                        P.portalEngine.recorder.onstop = async () => {
                            const blob = new Blob(P.portalEngine.chunks, { type: 'video/webm' });
                            const request = indexedDB.open("MentorMindDB", 1);
                            request.onsuccess = (e) => {
                                const db = e.target.result;
                                try {
                                    const tx = db.transaction("VideosStore", "readwrite");
                                    tx.objectStore("VideosStore").put(blob, sid);
                                    tx.oncomplete = () => finish();
                                } catch(e) { finish(); }
                            };
                            request.onerror = () => finish();
                        };
                        P.portalEngine.recorder.stop();
                    });
                };
            } catch (err) {
                console.error("Hardware Init Error:", err);
                if(loader) { 
                    loader.style.display = 'block';
                    loader.innerHTML = "<div style='color: #ea4a5a; font-weight: 700; margin-bottom: 5px;'>🚫 HARDWARE ERROR</div><div style='font-size: 10px; line-height: 1.3;'>" + String(err) + "<br/><br/>Try closing other camera apps or using the Reset button below.</div>";
                    loader.style.color = "#ea4a5a"; 
                }
            } finally {
                P.portalEngine.isStarting = false;
            }
        }

        if (!mount.dataset.aiRunning && P.portalEngine.stream) {
            mount.dataset.aiRunning = 'true';
            const runAI = async () => {
                let fApi = P.faceapi || window.faceapi;
                if(!fApi) { 
                    if (!P.document.querySelector('#face-api-script')) {
                        const s = P.document.createElement('script');
                        s.id = 'face-api-script';
                        s.src = "https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js";
                        P.document.head.appendChild(s);
                    }
                    while(!P.faceapi) await new Promise(r => setTimeout(r, 200));
                    fApi = P.faceapi;
                }
                
                if (!P.portalEngine.ssdModelsLoaded && !P.portalEngine.tinyModelsLoaded) {
                    P.portalEngine.aiStatusActive = true;
                    if(loader) {
                        loader.style.display = 'block';
                        loader.innerHTML = "Optimizing Neural Security...";
                    }
                    
                    // 15-second Bypass Escape Hatch
                    setTimeout(() => {
                        if (!P.portalEngine.ssdModelsLoaded && !P.portalEngine.tinyModelsLoaded) {
                            if(loader) {
                                loader.innerHTML = "<div style='color: #ea4a5a; font-weight: 700; margin-bottom: 5px;'>⚠️ NETWORK LAG DETECTED</div>Use the button on the left to unlock manually.";
                            }
                        }
                    }, 15000);

                    try {
                        // Attempt SSD first with a timeout fallback
                        const ssdPromise = fApi.nets.ssdMobilenetv1.loadFromUri('https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights');
                        const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error("Timeout")), 8000));
                        
                        await Promise.race([ssdPromise, timeoutPromise]);
                        P.portalEngine.ssdModelsLoaded = true;
                    } catch (err) {
                        console.warn("SSD Load failed or timed out, falling back to Tiny:", err);
                        if(loader) loader.innerHTML = "Activating Performance Mode...";
                        try {
                            await fApi.nets.tinyFaceDetector.loadFromUri('https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights');
                            P.portalEngine.tinyModelsLoaded = true;
                        } catch (tinyErr) {
                            console.error("Tiny Load FAIL:", tinyErr);
                            if(loader) loader.innerHTML = "⚠️ Model Load Error - Use Manual Unlock.";
                        }
                    }
                    P.portalEngine.aiStatusActive = false;
                }
                
                if(loader && (P.portalEngine.ssdModelsLoaded || P.portalEngine.tinyModelsLoaded)) {
                    loader.style.display = 'none';
                }
                
                // SIGNAL READINESS FASTER
                if(!P.camRdy) { P.camRdy = true; triggerSystemEvent('SYS_CAM_READY'); }
                
                if (!P.portalEngine.aiPollingStarted) {
                    P.portalEngine.aiPollingStarted = true;
                    let faceStrikes = 0;
                    
                    const aiLoop = async () => {
                        const currentMounts = Array.from(P.document.querySelectorAll('.core-cam-mount'));
                        if (currentMounts.length === 0) return;
                        const activeMount = currentMounts[currentMounts.length - 1];
                        const currentVid = activeMount.querySelector('video');
                        const currentAlertBox = activeMount.querySelector('#portal-alert');
                        
                        if (currentVid && currentVid.srcObject && !currentVid.paused && !currentVid.ended && (P.portalEngine.ssdModelsLoaded || P.portalEngine.tinyModelsLoaded)) {
                            try {
                                let detections = [];
                                if (P.portalEngine.ssdModelsLoaded) {
                                    detections = await fApi.detectAllFaces(currentVid, new fApi.SsdMobilenetv1Options({ minConfidence: 0.5 }));
                                } else {
                                    detections = await fApi.detectAllFaces(currentVid, new fApi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.15 }));
                                }
                                
                                if (detections.length === 0) { 
                                    faceStrikes++;
                                    if (faceStrikes >= 3) {
                                        if (currentAlertBox) {
                                            currentAlertBox.style.display = 'block'; 
                                            currentAlertBox.style.zIndex = '9999';
                                            currentAlertBox.innerHTML = "⚠️ FACE NOT VISIBLE"; 
                                        }
                                        if (P.portalEngine.faceState !== 'LOST') {
                                            P.portalEngine.faceState = 'LOST';
                                            triggerSystemEvent('SYS_FACE_LOST');
                                        }
                                    }
                                }
                                else if (detections.length > 1) { 
                                    faceStrikes = 0;
                                    if(currentAlertBox) { 
                                        currentAlertBox.style.display = 'block'; 
                                        currentAlertBox.style.zIndex = '9999';
                                        currentAlertBox.innerHTML = "⚠️ MULTIPLE PEOPLE DETECTED"; 
                                    } 
                                    if (P.portalEngine.faceState !== 'LOST') {
                                        P.portalEngine.faceState = 'LOST';
                                        triggerSystemEvent('SYS_FACE_LOST');
                                    }
                                }
                                else { 
                                    faceStrikes = 0;
                                    if(currentAlertBox) currentAlertBox.style.display = 'none'; 
                                    if (P.portalEngine.faceState !== 'FOUND') {
                                        P.portalEngine.faceState = 'FOUND';
                                        triggerSystemEvent('SYS_FACE_FOUND');
                                    }
                                }
                            } catch (e) { console.error("FaceAPI Loop Error:", e); }
                        }
                        setTimeout(aiLoop, 800);
                    };
                    aiLoop();
                }
            };
            runAI();
        }
    };

    setInterval(() => { managePortal(); runGlobalTimer(); }, 200);
