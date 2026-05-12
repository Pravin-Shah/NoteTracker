"""
Initialize Second Brain database tables.
"""
import sqlite3
from pathlib import Path
from api.config import DATABASE_PATH

def init_brain_database():
    """Create Second Brain tables if they don't exist."""
    print(f"Initializing Brain database at {DATABASE_PATH}...")
    
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    # 1. brain_raw — staging area for unprocessed dumps
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brain_raw (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            source_type TEXT DEFAULT 'text', -- text/url/telegram/voice
            processed INTEGER DEFAULT 0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. brain_wiki — LLM-maintained structured pages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brain_wiki (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT,
            content TEXT NOT NULL,
            source_ids TEXT, -- JSON array of brain_raw IDs
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. brain_links — connections between wiki pages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brain_links (
            wiki_id_1 INTEGER NOT NULL,
            wiki_id_2 INTEGER NOT NULL,
            relationship_type TEXT,
            notes TEXT,
            PRIMARY KEY (wiki_id_1, wiki_id_2)
        )
    """)
    
    # 4. brain_log — audit trail of LLM operations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brain_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL, -- ingest/lint/query
            input_ref TEXT,
            output_ref TEXT,
            llm_model TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("Brain database initialized successfully.")

if __name__ == "__main__":
    init_brain_database()
