"""
Script to backfill original_filename and file_size for existing attachments.
"""

import sqlite3
from pathlib import Path
import os

# Database path
DATA_DIR = Path(__file__).parent.parent / "data"
DATABASE_PATH = DATA_DIR / "shared_database.db"
UPLOADS_DIR = DATA_DIR / "uploads"

def backfill_attachment_metadata():
    """Backfill original_filename and file_size for existing attachments."""
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    try:
        # Get all attachments without metadata
        cursor.execute("""
            SELECT id, file_path 
            FROM gen_note_attachments 
            WHERE original_filename IS NULL OR file_size IS NULL
        """)
        attachments = cursor.fetchall()
        
        print(f"Found {len(attachments)} attachments to update...")
        
        for att_id, file_path in attachments:
            # Get file size
            full_path = UPLOADS_DIR / file_path
            file_size = None
            if full_path.exists():
                file_size = os.path.getsize(full_path)
            
            # Use file_path as original_filename for old attachments
            original_filename = file_path
            
            # Update the record
            cursor.execute("""
                UPDATE gen_note_attachments 
                SET original_filename = ?, file_size = ?
                WHERE id = ?
            """, (original_filename, file_size, att_id))
            
            print(f"✓ Updated attachment {att_id}: {original_filename} ({file_size} bytes)")
        
        conn.commit()
        print(f"\n✅ Successfully updated {len(attachments)} attachments!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    backfill_attachment_metadata()
