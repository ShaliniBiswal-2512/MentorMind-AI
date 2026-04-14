import os
import json
from groq import Groq

# We will initialize the groq client inside the functions or gracefully handle if key is not found
def get_groq_client():
    from dotenv import load_dotenv
    import os
    from groq import Groq
    
    # Force absolute path context since Streamlit pages can execute in detached dirs
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path, override=True)
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "replace_this_with_your_actual_key" or api_key == "your_groq_api_key_here":
        return None
        
    return Groq(api_key=api_key)

def summarize_resume(extracted_text):
    client = get_groq_client()
    if not client: return '{"summary": "Groq API key not set. Please enter it in the sidebar."}'
    
    prompt = f"""
    You are an expert HR assistant. Analyze the following resume and extract the required information into JSON format.
    Fields required:
    - full_name: The full name of the candidate found at the top of the resume.
    - qualification: Highest degree or certification (e.g., "B.Ed", "M.Sc Mathematics"). Max 3 words.
    - subjects: Comma separated list of subjects the candidate can teach (e.g., "Science, English"). If not explicitly mentioned, infer from qualification.
    - experience: Years of experience. Extract as exactly "Fresher", "1-2 yrs", or "3+ yrs".
    - summary: A concise 3-4 sentence paragraph summarizing their educational qualifications, teaching experience, and key skills.

    Resume Text:
    {extracted_text[:3000]}
    
    Return pure JSON EXACTLY matching this format:
    {{
        "full_name": "string",
        "qualification": "string",
        "subjects": "string",
        "experience": "string",
        "summary": "string"
    }}
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        import json
        return json.dumps({"summary": f"Error analyzing resume: {str(e)}", "full_name": "", "qualification": "", "subjects": "", "experience": "Fresher"})

def generate_interview_questions(subject, class_level, profile_summary):
    client = get_groq_client()
    if not client: return [
        "Please tell me a little bit about yourself and your teaching background.",
        f"How would you introduce a foundational topic in {subject} to {class_level} students?",
        "Can you describe a time you had to handle a disruptive or confused student?"
    ]

    prompt = f"""
    You are an expert Teacher Screener conducting a Level 3 oral interview for a '{subject}' tutor who will teach students of '{class_level}'.
    Candidate Profile Summary: {profile_summary}
    
    Generate EXACTLY 6 distinct, advanced questions. 
    ALL 6 questions MUST be strictly Managerial and Situation-Based pedagogy scenarios (e.g., handling difficult parents, disruptive classrooms, navigating syllabus roadblocks, balancing student mental health, etc.) tailored specifically to the context of teaching '{subject}' at the '{class_level}' level.
    Do NOT ask for self-introductions or basic core concepts. 

    Return the exact questions as a pure JSON list of strings. Do NOT include markdown blocks or any other text.
    Example: ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.7
        )
        content = response.choices[0].message.content
        # sometimes llms wrap JSON in json block, let's extract it safely
        import re
        match = re.search(r'\[.*\]', content.replace('\n', ' '))
        if match:
            return json.loads(match.group())
        return [q.strip() for q in content.split('\n') if q.strip()]
    except Exception as e:
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        return [f"({ts}) Could not generate questions: {str(e)}", "Please tell me about yourself.", "How would you teach a confused student?"]

def evaluate_interview(transcript, subject, class_level, l1_summary="", l2_summary=""):
    client = get_groq_client()
    if not client: 
        return {
            "scores": {"clarity": 0, "communication": 0, "problem_solving": 0, "subject_knowledge": 0, "teaching_ability": 0},
            "strengths": ["API not configured"], 
            "weaknesses": ["API not configured"], 
            "insights": "API key not set. Please enter it in the sidebar.",
            "improvement_suggestions": "N/A",
            "verdict": "Hold"
        }
        
    user_words = [line for line in transcript.split('\n') if line.startswith('Candidate: ')]
    total_spoken = sum(len(line.replace('Candidate: ', '').strip()) for line in user_words)
    
    # Do not auto-reject on brevity, instead evaluate based on merit
    prompt = f"""
    You are evaluating a teaching candidate holistically across three distinct assessment levels for '{subject}' (Class Level: '{class_level}').
    
    IMPORTANT CONTEXT: This candidate HAS ALREADY SUCCESSFULLY CLEARED Level 1 and Level 2. Do NOT hallucinate that they lack basic subject knowledge or pedagogy if they chose to skip or abbreviate their oral responses in Level 3. Acknowledge their strengths demonstrated in L1/L2 objectively.
    
    Level 1 (Aptitude/Pedagogy Data):
    {l1_summary}
    
    Level 2 (Subject Knowledge Data):
    {l2_summary}
    
    Level 3 (Oral Managerial Interview Transcript):
    {transcript}
    
    Evaluate the candidate out of 100 on these EXACT categories by synthesizing performance across ALL three levels: 
    1. clarity (clear voice and logical structure in L3)
    2. communication (flow and articulation during L3)
    3. problem_solving (handling scenarios accurately in L2 and L3)
    4. subject_knowledge (factual accuracy in L2 and L3)
    5. teaching_ability (pedagogical strengths in L1 and L3)

    Based on the overall holistic scores, provide a final verdict ("Selected", "Hold", or "Rejected").
    Provide 2 strings for 'strengths', 2 for 'weaknesses', a string for 'insights', and a string for 'improvement_suggestions'.
    
    Return pure JSON format EXACTLY like this:
    {{
        "scores": {{"clarity": 85, "communication": 80, "problem_solving": 90, "subject_knowledge": 88, "teaching_ability": 95}},
        "strengths": ["...", "..."], "weaknesses": ["...", "..."], "insights": "...", "improvement_suggestions": "...", "verdict": "Selected"
    }}
    Ensure NO markdown or other text is generated, ONLY valid JSON.
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.2
        )
        content = response.choices[0].message.content
        # Clean potential markdown
        content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return data
    except Exception as e:
        print(e)
        return {
            "scores": {"clarity": 0, "communication": 0, "problem_solving": 0, "subject_knowledge": 0, "teaching_ability": 0},
            "strengths": ["API Error"], 
            "weaknesses": ["API Error"], 
            "insights": "An error occurred during evaluation.", 
            "improvement_suggestions": "An error occurred.",
            "verdict": "Hold"
        }

def get_whisper_transcription(audio_file_path):
    client = get_groq_client()
    if not client: return "API key missing for transcription. Please enter your API key in the sidebar."
    try:
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
              file=(audio_file_path, file.read()),
              model="whisper-large-v3",
              language="en",
              prompt="The candidate is answering an interview question.",
              temperature=0.0
            )
            text = transcription.text.strip()
            
            # Simple hallucination check for silent or static audio
            lower_val = text.lower()
            if not text or "takk for at" in lower_val or "thanks for watching" in lower_val or lower_val == "thank you." or "amara.org" in lower_val:
                return "ERROR_AUDIO:No speech was detected in the recording. Please ensure your microphone is not muted and the correct input device is selected in your system settings."
                
            return text
    except Exception as e:
        return f"Transcription error: {str(e)}"


def generate_aptitude_questions(class_level):
    import random
    STATIC_APTITUDE_BANK = [
        {"question": "Which of the following best describes 'formative assessment'?", "options": ["Evaluating student learning at the end of a unit", "Monitoring student learning to provide ongoing feedback", "Standardized testing across a district", "A final exam grade"], "answer": "Monitoring student learning to provide ongoing feedback"},
        {"question": "What is the primary purpose of 'scaffolding' in education?", "options": ["To rigidly enforce classroom rules", "To provide temporary support to help a student achieve a learning goal", "To assign more homework for advanced learners", "To group students exclusively by age"], "answer": "To provide temporary support to help a student achieve a learning goal"},
        {"question": "Which teaching methodology emphasizes learning through active, hands-on experiences?", "options": ["Rote memorization", "Experiential learning", "Direct instruction", "Didactic teaching"], "answer": "Experiential learning"},
        {"question": "What does 'differentiated instruction' entail?", "options": ["Teaching every student the exact same way", "Tailoring instruction to meet individual needs", "Only grading the highest-performing students", "Using only one textbook for the entire semester"], "answer": "Tailoring instruction to meet individual needs"},
        {"question": "According to Bloom's Taxonomy, which of the following is the highest level of cognitive skill?", "options": ["Remembering", "Applying", "Creating", "Understanding"], "answer": "Creating"},
        {"question": "A student consistently struggles to stay focused during 45-minute lectures. What is the best pedagogical response?", "options": ["Reprimand the student for inattention", "Incorporate brief, interactive breaks into the lesson", "Send the student to the principal", "Ignore the student and continue lecturing"], "answer": "Incorporate brief, interactive breaks into the lesson"},
        {"question": "What is a 'flipped classroom'?", "options": ["A classroom where desks face the back wall", "Students learn new content at home and do practice/homework in class", "The teacher acts as a student for a day", "There are no written assignments, only verbal exams"], "answer": "Students learn new content at home and do practice/homework in class"},
        {"question": "Which of the following is an example of 'summative assessment'?", "options": ["A mid-lesson pop quiz not graded for credit", "A final end-of-term research project", "A quick thumbs-up/thumbs-down check for understanding", "A daily learning journal"], "answer": "A final end-of-term research project"},
        {"question": "How can a teacher best foster a 'growth mindset' in students?", "options": ["Praising their natural intelligence", "Praising their effort and strategy", "Telling them some people are just not good at math", "Only rewarding perfect scores"], "answer": "Praising their effort and strategy"},
        {"question": "What is the main goal of classroom management?", "options": ["Establishing a quiet environment at all times", "Creating a safe, efficient, and positive learning environment", "Ensuring students fear the teacher's authority", "Minimizing the amount of teaching required"], "answer": "Creating a safe, efficient, and positive learning environment"},
        {"question": "Which term refers to the idea that students have unique ways of absorbing and processing information?", "options": ["Cognitive dissonance", "Learning styles", "Standardized learning", "Summative processing"], "answer": "Learning styles"},
        {"question": "When a student gives an incorrect answer in class, what is the most constructive teacher response?", "options": ["'No, that's completely wrong.'", "'You need to pay more attention.'", "'That's not quite it. Can someone else help out?'", "'I see how you got there. Let's look at the second step again.'"], "answer": "'I see how you got there. Let's look at the second step again.'"},
        {"question": "What does it mean to create an 'inclusive classroom'?", "options": ["Only allowing high-achieving students to participate", "Ensuring all students, regardless of ability or background, are engaged and supported", "Teaching only the mainstream curriculum without any adaptations", "Grouping students strictly by their socio-economic backgrounds"], "answer": "Ensuring all students, regardless of ability or background, are engaged and supported"},
        {"question": "What is the primary benefit of 'peer tutoring'?", "options": ["It allows the teacher to take a break", "It reinforces learning for the tutor and provides individualized support for the tutee", "It guarantees perfect test scores", "It eliminates the need for lesson planning"], "answer": "It reinforces learning for the tutor and provides individualized support for the tutee"},
        {"question": "Which instructional strategy involves giving students choices in how they learn and demonstrate their knowledge?", "options": ["Authoritarian teaching", "Universal Design for Learning (UDL)", "Rote learning", "Standardized mapping"], "answer": "Universal Design for Learning (UDL)"},
        {"question": "What is 'extrinsic motivation' in the context of learning?", "options": ["Learning driven by personal curiosity", "Learning driven by external rewards like grades or praise", "Learning driven by genetic predisposition", "Learning driven by a desire to master a skill for oneself"], "answer": "Learning driven by external rewards like grades or praise"},
        {"question": "A 'rubric' is best used for which of the following?", "options": ["Taking attendance", "Providing clear expectations and grading criteria for an assignment", "Decorating the classroom bulletin board", "Punishing students for late work"], "answer": "Providing clear expectations and grading criteria for an assignment"},
        {"question": "What is the 'zone of proximal development' (ZPD)?", "options": ["The physical distance between the teacher's desk and the student", "The gap between what a learner can do independently and what they can do with guidance", "The area sequence in a textbook", "The timeline required to memorize a list of facts"], "answer": "The gap between what a learner can do independently and what they can do with guidance"},
        {"question": "Why is 'wait time' (pausing after asking a question) important in teaching?", "options": ["It gives the teacher time to check their phone", "It increases the quantity and quality of student responses", "It wastes classroom time purposely", "It ensures only the fastest thinkers answer"], "answer": "It increases the quantity and quality of student responses"},
        {"question": "Which of the following best defines 'project-based learning' (PBL)?", "options": ["Taking multiple-choice tests every Friday", "Students gaining knowledge by working for an extended period to investigate a complex question or challenge", "Reading a chapter and answering questions at the back of the book", "Memorizing lists of historical dates"], "answer": "Students gaining knowledge by working for an extended period to investigate a complex question or challenge"}
    ]
    
    selected = random.sample(STATIC_APTITUDE_BANK, 10)
    for q in selected:
        random.shuffle(q["options"])
    return selected

def generate_scenario_questions(subject, class_level):
    client = get_groq_client()
    if not client: 
        return [{"question": "Scenario: A student...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Default.", "concept": "Pedagogy"}] * 15
    
    prompt = f"""
    You are assessing a '{subject}' teacher for '{class_level}'. 
    Generate exactly 15 conceptual Multiple Choice Questions (MCQs).
    Focus: Hard subject matter facts, core theoretical concepts, and subject knowledge specific to '{subject}' at the '{class_level}' level.
    Do NOT include scenario-based or pedagogical teaching questions.
    
    Return pure JSON EXACTLY in this format:
    {{
        "questions": [
            {{
                "question": "Subject concept question...", 
                "options": ["First option full text.", "Second option full text.", "Third option full text.", "Fourth option full text."], 
                "answer": "First option full text.",
                "explanation": "Why this answer is factually correct.",
                "concept": "Subject Knowledge"
            }}
        ]
    }}
    CRITICAL INSTRUCTION: The value in "answer" MUST perfectly match the exact string text of the correct option in "options", character for character. Do not just return 'A', 'B', 'C', or 'D'.
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        qs = data.get("questions", data.get("Questions", []))
        if not qs or len(qs) == 0:
            raise ValueError("Empty question list returned by API.")
        return qs[:15]
    except Exception as e:
        print(f"Scenario Error: {e}")
        return [{"question": f"Scenario: Teaching {subject} to {class_level}...", "options": ["O1", "O2", "O3", "O4"], "answer": "O1", "explanation": "Default.", "concept": "General"}] * 15

def evaluate_scenario_responses(qa_pairs, subject, class_level):
    client = get_groq_client()
    if not client:
        return {"passed": True, "feedback": "API not configured - Auto pass."}
        
    transcript = "\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs])
    
    prompt = f"""
    Candidate applied for {subject} ({class_level}). They answered 6 teaching scenario questions:
    {transcript}
    
    Did the candidate give satisfactory answers overall? Give a final boolean 'passed' (true/false) and a brief 'feedback' string. 
    THRESHOLD: Pass them if they show any effort and a basic understanding of teaching. 
    CRITICAL: BE EXTREMELY LENIENT. Only fail them if the answers are offensive, completely blank, or total gibberish like 'asdf'. 
    If they tried to answer, PASS THEM.
    
    Return pure JSON:
    {{
        "passed": true,
        "feedback": "string"
    }}
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        import json
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception:
        return {"passed": False, "feedback": "Error evaluating scenarios."}

