---
title: MentorMind AI
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: "1.37.0"
app_file: app.py
pinned: false
---

# 🧠 MentorMind AI - Intelligence Protocol
**An Advanced AI-Proctored Teacher Interview & Evaluation System**

## 🌐 Overview
MentorMind AI is a state-of-the-art interview and assessment logic engine designed to evaluate teaching candidates. Leveraging large language models (Llama 3.1) and Azure Voice Synthesis, this platform administers an adaptive, multi-tier oral interview to mathematically aggregate a candidate's pedagogical aptitude, specific subject knowledge, emotional patience, and communication clarity.

### ✨ Core Features
* **Resume Extraction Intelligence:** Automatically decodes and parses unstructured PDF portfolios/resumes to dynamically reconstruct candidate profiles.
* **Three-Tier Evaluation Gates:** Processes candidates through Aptitude, Pedagogy Scenarios, and a dynamic Oral Voice Interview.
* **Synthesized Proctoring:** Simulates a live human interviewer utilizing high-fidelity Edge-TTS voice generation.
* **Competency Radar Generation:** Deploys a mathematical AI holistic matrix to calculate granular scores and renders precise Plotly Pie-Charts natively linked to the PDF Scorecard generator.
* **WebRTC Voice Capture:** Browser-based native microphone interactions processing real-time transcription.

## 🛠️ Technology Stack
* **Language:** Python 3.11
* **Framework:** Streamlit
* **Neural Language Engine:** Groq Cloud API (Llama-3.1-8b-instant)
* **Voice Synthesis:** `edge-tts`
* **Data Visualization:** Plotly & Matplotlib
* **Document Processing:** PyPDF2 & FPDF

## 🚀 Running Locally
To launch the MentorMind platform locally:
1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Setup your environment keys: Create a `.env` file and insert `GROQ_API_KEY="your_api_key_here"`
4. Boot the server: `streamlit run app.py`
