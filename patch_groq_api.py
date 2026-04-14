import os

with open('core/groq_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update generate_interview_questions to 10 questions
content = content.replace("Generate 4 distinct, adaptive questions", "Generate 10 distinct, adaptive questions")
if 'Example: ["Q1", "Q2", "Q3", "Q4"]' in content:
    content = content.replace('Example: ["Q1", "Q2", "Q3", "Q4"]', 'Example: ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"]')

# 2. Append new level functions
new_funcs = """

def generate_aptitude_questions(class_level):
    client = get_groq_client()
    if not client: 
        return [{"question": "What is 2+2?", "options": ["3", "4", "5", "6"], "answer": "4"}] * 6
    
    prompt = f\"\"\"
    You are assessing a teacher applying to teach {class_level}. 
    Generate exactly 6 multiple-choice questions (Aptitude, Logic, and basic Pedagogy).
    
    Return pure JSON EXACTLY in this format:
    {{
        "questions": [
            {{"question": "Question text here?", "options": ["A", "B", "C", "D"], "answer": "A"}}
        ]
    }}
    Ensure 'answer' exactly matches one of the strings in the 'options' array.
    \"\"\"
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        import json
        data = json.loads(response.choices[0].message.content)
        return data.get("questions", [])[:6]
    except Exception as e:
        print(f"Aptitude Error: {e}")
        return [{"question": "Error loading logic question.", "options": ["A", "B", "C", "D"], "answer": "A"}] * 6

def generate_scenario_questions(subject, class_level):
    client = get_groq_client()
    if not client: 
        return ["A student is distracted. What do you do?"] * 6
    
    prompt = f\"\"\"
    You are assessing a '{subject}' teacher applying for '{class_level}'. 
    Generate exactly 6 short-response scenario questions. These are 'Teaching Game Scenarios' where the teacher must explain how they handle specific classroom situations or concept explanations.
    
    Return pure JSON EXACTLY in this format:
    {{
        "questions": [
            "Scenario 1...", "Scenario 2..."
        ]
    }}
    \"\"\"
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        import json
        data = json.loads(response.choices[0].message.content)
        return data.get("questions", [])[:6]
    except Exception as e:
        print(f"Scenario Error: {e}")
        return [f"Error generating scenario for {subject}"] * 6

def evaluate_scenario_responses(qa_pairs, subject, class_level):
    client = get_groq_client()
    if not client:
        return {"passed": True, "feedback": "API not configured - Auto pass."}
        
    transcript = "\\n".join([f"Q: {q}\\nA: {a}" for q, a in qa_pairs])
    
    prompt = f\"\"\"
    Candidate applied for {subject} ({class_level}). They answered 6 teaching scenario questions:
    {transcript}
    
    Did the candidate give satisfactory answers overall? Give a final boolean 'passed' (true/false) and a brief 'feedback' string. They should pass if at least 50% of the answers show competent reasoning.
    
    Return pure JSON:
    {{
        "passed": true,
        "feedback": "string"
    }}
    \"\"\"
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

"""
if "def generate_aptitude_questions" not in content:
    content += new_funcs

with open('core/groq_api.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated core/groq_api.py")
