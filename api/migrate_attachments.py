"""
Migration script to add original_filename and file_size columns to gen_note_attachments table.
"""

import sqlite3
from pathlib import Path

# Database path
DATA_DIR = Path(__file__).parent.parent / "data"
DATABASE_PATH = DATA_DIR / "shared_database.db"

def migrate():
    """Add new columns to gen_note_attachments table."""
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(gen_note_attachments)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add original_filename column if it doesn't exist
        if 'original_filename' not in columns:
            print("Adding original_filename column...")
            cursor.execute("""
                ALTER TABLE gen_note_attachments 
                ADD COLUMN original_filename TEXT
            """)
            print("✓ Added original_filename column")
        else:
            print("✓ original_filename column already exists")
        
        # Add file_size column if it doesn't exist
        if 'file_size' not in columns:
            print("Adding file_size column...")
            cursor.execute("""
                ALTER TABLE gen_note_attachments 
                ADD COLUMN file_size INTEGER
            """)
            print("✓ Added file_size column")
        else:
            print("✓ file_size column already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
