import sqlite3

def create_tables():
    conn = sqlite3.connect('career_counselor.db')
    cursor = conn.cursor()

    # --- Drop old apply table (ONLY if exists, for dev) ---
    cursor.execute("DROP TABLE IF EXISTS chat_history")

    # users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
    ''')

    # recruiter table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recruiter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
    ''')

    # owner table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS owner (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

    # job table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter_id INTEGER,
            company TEXT NOT NULL,
            designation TEXT NOT NULL,
            experience_required TEXT,
            qualification TEXT,
            skills_required TEXT,
            contact_number TEXT,
            email TEXT,
            posted_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # apply table (with user_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, 
            applicant_name TEXT,
            applicant_email TEXT,
            qualification TEXT,
            university TEXT,
            experience INTEGER,
            skills TEXT,
            resume_path TEXT,
            recruiter_id INTEGER,
            job_id INTEGER,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            experience TEXT,
            user_type TEXT,
            suggestions TEXT,
            rating INTEGER
        )
    ''')

    # messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            sender_type TEXT NOT NULL CHECK(sender_type IN ('user','recruiter')),
            receiver_id INTEGER NOT NULL,
            receiver_type TEXT NOT NULL CHECK(receiver_type IN ('user','recruiter')),
            message TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ All tables created successfully.")

if __name__ == '__main__':
    create_tables()
