import sqlite3
from pathlib import Path

DATA_DIR = Path("data")
DATABASE_PATH = DATA_DIR / "shared_database.db"

def migrate():
    print(f"Migrating database at {DATABASE_PATH}...")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if google_id already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'google_id' not in columns:
            print("Adding google_id column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        
        if 'avatar_url' not in columns:
            print("Adding avatar_url column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
            
        conn.commit()
        print("Migration successful!")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
