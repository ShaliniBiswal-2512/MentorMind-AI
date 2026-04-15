# 🧠 MentorMind AI  
### 🚀 AI-Powered Teacher Interview & Evaluation Platform  

**Elevating education through intelligent screening**

---

## 🌐 Live Demo  
👉 **Try the app here:**  
🔗 https://mentormind-ai-hgyh.onrender.com  

---

## 📌 Overview  
**MentorMind AI** is an advanced AI-driven platform designed to evaluate teaching candidates through intelligent, multi-stage assessments.  

It combines **LLMs, voice interaction, and automated analysis** to simulate real interview scenarios and generate data-driven insights about a candidate’s teaching ability.

The platform evaluates:
- Pedagogical understanding  
- Subject knowledge  
- Communication clarity  
- Emotional intelligence & patience  

---

## ✨ Key Features  

### 📄 Resume Intelligence  
- Extracts and analyzes resumes (PDF)  
- Builds structured candidate profiles automatically  

### 🧩 Multi-Stage Evaluation  
- Aptitude-based screening  
- Pedagogy scenario testing  
- AI-powered oral interview  

### 🎙️ Voice-Based Interview  
- Real-time speech interaction  
- AI-generated interviewer voice  

### 📊 Smart Analytics  
- Performance insights with charts  
- Competency-based scoring  
- Auto-generated evaluation reports  

---

## 🛠️ Tech Stack  

- **Language:** Python 3.11  
- **Framework:** Streamlit  
- **AI Engine:** Groq API (Llama 3.1)  
- **Voice:** edge-tts  
- **Visualization:** Plotly, Matplotlib  
- **PDF Processing:** PyPDF2, FPDF  

---

## 🚀 Run Locally  

```bash
# Clone the repository
git clone <your-repo-link>

# Navigate to project folder
cd MentorMind-AI

# Create virtual environment
python -m venv venv

# Activate environment
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add environment variables
# Create a .env file and add:
GROQ_API_KEY=your_api_key_here

# Run the app
streamlit run app.py
