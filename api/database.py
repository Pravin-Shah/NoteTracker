"""
Database connection for FastAPI.
Reuses the existing SQLite database from the Streamlit app.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from api.config import DATABASE_PATH


@contextmanager
def get_db_connection():
    """Get database connection context manager."""
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(sql: str, params: tuple = ()) -> List[Dict]:
    """Execute SELECT query and return results as list of dicts."""
    with get_db_connection() as conn:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def execute_insert(sql: str, params: tuple = ()) -> int:
    """Execute INSERT and return last row id."""
    with get_db_connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid


def execute_update(sql: str, params: tuple = ()) -> int:
    """Execute UPDATE/DELETE and return affected rows."""
    with get_db_connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.rowcount


def get_record_by_id(table: str, record_id: int) -> Optional[Dict]:
    """Get single record by ID."""
    sql = f"SELECT * FROM {table} WHERE id = ?"
    results = execute_query(sql, (record_id,))
    return results[0] if results else None
