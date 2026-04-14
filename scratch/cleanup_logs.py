import sqlite3
import os
from datetime import datetime

db_path = r"c:\Users\KIIT\Desktop\MentorMind AI\db\mentor_mind.db"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

today = datetime.now().strftime("%Y-%m-%d")
c.execute("SELECT id, user_id, date FROM attempt_logs WHERE date LIKE ? ORDER BY user_id, date", (f"{today}%",))
logs = c.fetchall()

to_delete = []
seen_logs = {} # user_id -> [timestamps]

for log_id, user_id, date_str in logs:
    ts = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    if user_id not in seen_logs:
        seen_logs[user_id] = ts
    else:
        # If this log is within 3 minutes of the previous one, it's a double-log
        diff = (ts - seen_logs[user_id]).total_seconds()
        if diff < 180: 
            to_delete.append(log_id)
        else:
            seen_logs[user_id] = ts

if to_delete:
    c.execute(f"DELETE FROM attempt_logs WHERE id IN ({','.join(map(str, to_delete))})")
    conn.commit()
    print(f"Successfully cleaned up {len(to_delete)} duplicate logs.")
else:
    print("No duplicates were detected for cleanup.")

conn.close()
