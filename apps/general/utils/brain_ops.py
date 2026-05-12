"""
Database operations for the Second Brain.
Reuses the generic CRUD pattern from api.database.
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from api.database import execute_query, execute_insert, execute_update, get_record_by_id

def add_raw_dump(user_id: int, content: str, source_type: str = 'text', attachments: List[str] = None, external_id: int = None) -> int:
    """Add a raw unprocessed thought/dump to brain_raw with optional external_id link."""
    attachments_json = json.dumps(attachments or [])
    sql = """
        INSERT INTO brain_raw (user_id, content, source_type, processed, attachments, external_id)
        VALUES (?, ?, ?, 0, ?, ?)
    """
    return execute_insert(sql, (user_id, content, source_type, attachments_json, external_id))

def save_raw_dump(user_id: int, content: str, source_type: str = 'text', attachments: List[str] = None, external_id: int = None) -> int:
    """Alias for add_raw_dump used by API."""
    return add_raw_dump(user_id, content, source_type, attachments, external_id)

def get_unprocessed(user_id: int) -> List[Dict]:
    """Get all unprocessed raw dumps for a user."""
    sql = "SELECT * FROM brain_raw WHERE user_id = ? AND processed = 0 ORDER BY created_date ASC"
    return execute_query(sql, (user_id,))

def mark_processed(raw_id: int):
    """Mark a raw dump as processed."""
    sql = "UPDATE brain_raw SET processed = 1 WHERE id = ?"
    execute_update(sql, (raw_id,))

def upsert_wiki_page(user_id: int, title: str, category: str, content: str, source_ids: List[int]) -> int:
    """Create or update a wiki page."""
    # Check if page already exists
    existing = execute_query(
        "SELECT id FROM brain_wiki WHERE user_id = ? AND title = ?",
        (user_id, title)
    )
    
    source_ids_json = json.dumps(source_ids)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if existing:
        wiki_id = existing[0]['id']
        sql = """
            UPDATE brain_wiki 
            SET category = ?, content = ?, source_ids = ?, last_updated = ?
            WHERE id = ?
        """
        execute_update(sql, (category, content, source_ids_json, now, wiki_id))
        return wiki_id
    else:
        sql = """
            INSERT INTO brain_wiki (user_id, title, category, content, source_ids, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return execute_insert(sql, (user_id, title, category, content, source_ids_json, now))

def get_wiki_page(user_id: int, title: str) -> Optional[Dict]:
    """Get a wiki page by title."""
    sql = "SELECT * FROM brain_wiki WHERE user_id = ? AND title = ?"
    results = execute_query(sql, (user_id, title))
    return results[0] if results else None

def list_wiki_pages(user_id: int, category: Optional[str] = None) -> List[Dict]:
    """List all wiki pages, optionally filtered by category."""
    if category:
        sql = "SELECT id, title, category FROM brain_wiki WHERE user_id = ? AND category = ? ORDER BY title ASC"
        return execute_query(sql, (user_id, category))
    else:
        sql = "SELECT id, title, category FROM brain_wiki WHERE user_id = ? ORDER BY title ASC"
        return execute_query(sql, (user_id,))

def add_link(wiki_id_1: int, wiki_id_2: int, relationship_type: str, notes: str = ''):
    """Add a connection between two wiki pages."""
    # Ensure smaller ID is always wiki_id_1 for consistency
    id1, id2 = sorted([wiki_id_1, wiki_id_2])
    sql = """
        INSERT OR REPLACE INTO brain_links (wiki_id_1, wiki_id_2, relationship_type, notes)
        VALUES (?, ?, ?, ?)
    """
    execute_update(sql, (id1, id2, relationship_type, notes))

def get_links(wiki_id: int) -> List[Dict]:
    """Get all connections for a specific wiki page."""
    sql = """
        SELECT * FROM brain_links 
        WHERE wiki_id_1 = ? OR wiki_id_2 = ?
    """
    return execute_query(sql, (wiki_id, wiki_id))

def log_llm_op(operation: str, input_ref: str, output_ref: str, llm_model: str) -> int:
    """Log an LLM operation."""
    sql = """
        INSERT INTO brain_log (operation, input_ref, output_ref, llm_model)
        VALUES (?, ?, ?, ?)
    """
    return execute_insert(sql, (operation, input_ref, output_ref, llm_model))

def delete_wiki_page(wiki_id: int):
    """Delete a wiki page and its connections."""
    # Delete links first
    execute_update("DELETE FROM brain_links WHERE wiki_id_1 = ? OR wiki_id_2 = ?", (wiki_id, wiki_id))
    # Delete the page
    execute_update("DELETE FROM brain_wiki WHERE id = ?", (wiki_id,))