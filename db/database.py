import sqlite3
import os
import bcrypt
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "mentor_mind.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            login_count INTEGER DEFAULT 0
        )
    ''')
    try:
        c.execute('ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    # Candidate Profiles Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            qualification TEXT,
            subjects TEXT,
            experience TEXT,
            pref_class_level TEXT,
            specific_class TEXT,
            resume_extracted_text TEXT,
            resume_summary TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    try:
        c.execute('ALTER TABLE profiles ADD COLUMN full_name TEXT')
    except sqlite3.OperationalError:
        pass
    # Interviews Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            subject TEXT,
            class_level TEXT,
            score_clarity INTEGER,
            score_communication INTEGER,
            score_problem_solving INTEGER,
            score_subject_knowledge INTEGER,
            score_teaching_ability INTEGER,
            verdict TEXT,
            feedback TEXT,
            transcript TEXT,
            session_id TEXT,
            l1_score INTEGER,
            l2_score INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    try:
        c.execute('ALTER TABLE interviews ADD COLUMN score_problem_solving INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE interviews ADD COLUMN score_subject_knowledge INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE interviews ADD COLUMN score_teaching_ability INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE interviews ADD COLUMN session_id TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE interviews ADD COLUMN l1_score INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE interviews ADD COLUMN l2_score INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE interviews ADD COLUMN focus_consistency REAL DEFAULT 0.0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE interviews ADD COLUMN face_visibility REAL DEFAULT 0.0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE interviews ADD COLUMN violations_count INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass

    # Attempt Logs Table (Security Layer)
    c.execute('''
        CREATE TABLE IF NOT EXISTS attempt_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def create_user(name, email, password):
    conn = get_connection()
    c = conn.cursor()
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute('INSERT INTO users (name, email, password_hash, login_count) VALUES (?, ?, ?, 0)', (name, email, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = get_connection()
    c = conn.cursor()
    clean_email = email.strip()
    c.execute('SELECT id, name, password_hash, login_count FROM users WHERE email = ?', (clean_email,))
    user = c.fetchone()
    if user:
        # Cross-platform robust cast for SQLite returned blobs
        db_hash = user[2]
        if isinstance(db_hash, str):
            db_hash = db_hash.encode('utf-8')
            
        try:
            if bcrypt.checkpw(password.strip().encode('utf-8'), db_hash):
                new_count = (user[3] if user[3] is not None else 0) + 1
                c.execute('UPDATE users SET login_count = ? WHERE id = ?', (new_count, user[0]))
                conn.commit()
                conn.close()
                return {"id": user[0], "name": user[1], "email": clean_email, "login_count": new_count}
        except Exception as e:
            pass # fallback on crash

    conn.close()
    return None

def get_user_by_id(user_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT id, name, email, login_count FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def update_profile(user_id, data):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO profiles (user_id, full_name, qualification, subjects, experience, pref_class_level, specific_class, resume_extracted_text, resume_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            full_name=excluded.full_name,
            qualification=excluded.qualification,
            subjects=excluded.subjects,
            experience=excluded.experience,
            pref_class_level=excluded.pref_class_level,
            specific_class=excluded.specific_class,
            resume_extracted_text=excluded.resume_extracted_text,
            resume_summary=excluded.resume_summary
    ''', (user_id, data.get("full_name", ""), data.get("qualification", ""), data.get("subjects", ""), data.get("experience", ""), 
          data.get("pref_class_level", ""), data.get("specific_class", ""), 
          data.get("resume_extracted_text", ""), data.get("resume_summary", "")))
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,))
    profile = c.fetchone()
    conn.close()
    return dict(profile) if profile else None

def save_interview(user_id, subject, class_level, scores, verdict, feedback, transcript, session_id=None, l1_score=0, l2_score=0, focus_consistency=0.0, face_visibility=0.0, violations_count=0):
    conn = get_connection()
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Map new score keys to database columns
    c.execute('''
        INSERT INTO interviews (user_id, date, subject, class_level, score_clarity, score_communication, score_problem_solving, score_subject_knowledge, score_teaching_ability, verdict, feedback, transcript, session_id, l1_score, l2_score, focus_consistency, face_visibility, violations_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, date_str, subject, class_level, 
          scores.get("clarity", 0), scores.get("communication", 0), 
          scores.get("problem_solving", scores.get("simplicity", 0)), 
          scores.get("subject_knowledge", scores.get("subject", 0)), 
          scores.get("teaching_ability", scores.get("patience", 0)), 
          verdict, feedback, transcript, session_id, l1_score, l2_score,
          focus_consistency, face_visibility, violations_count))
    conn.commit()
    conn.close()

def get_user_interviews(user_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM interviews WHERE user_id = ? ORDER BY date DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
    
def count_today_attempts(user_id):
    conn = get_connection()
    c = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    c.execute('SELECT COUNT(*) FROM attempt_logs WHERE user_id = ? AND date LIKE ?', (user_id, f"{today_str}%"))
    count = c.fetchone()[0]
    conn.close()
    return count

def log_attempt(user_id):
    conn = get_connection()
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO attempt_logs (user_id, date) VALUES (?, ?)', (user_id, date_str))
    conn.commit()
    conn.close()

def delete_interview(interview_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM interviews WHERE id = ? AND user_id = ?', (interview_id, user_id))
    conn.commit()
    conn.close()

def clear_user_interviews(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM interviews WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Initialize DB on load
init_db()
