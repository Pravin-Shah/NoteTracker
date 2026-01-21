"""
Database initialization, connection management, and CRUD operations.
All apps use this module. No UI logic here—pure functions.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import logging
from core.config import DATABASE_PATH
from core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """
    Get database connection. Sets row factory for dict-like access.

    Args:
        db_path: Optional path to database

    Returns:
        Database connection
    """
    path = db_path or str(DATABASE_PATH)
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise DatabaseError(f"Failed to connect to database: {e}")


def init_database(db_path: str = None) -> None:
    """
    Initialize database and create all tables if they don't exist.

    Args:
        db_path: Optional path to database (for testing)

    Raises:
        DatabaseError: If initialization fails
    """
    path = db_path or str(DATABASE_PATH)
    try:
        conn = get_connection(path)
        cursor = conn.cursor()

        schema = _get_database_schema()
        cursor.executescript(schema)

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {path}")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise DatabaseError(f"Database initialization failed: {e}")


def execute_query(query: str, params: tuple = (), db_path: str = None) -> List[Dict]:
    """
    Execute SELECT query and return results as list of dicts.

    Args:
        query: SQL SELECT query
        params: Query parameters
        db_path: Optional database path

    Returns:
        List of results (empty if no rows)

    Raises:
        DatabaseError: If query fails
    """
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except sqlite3.Error as e:
        logger.error(f"Query failed: {e}")
        raise DatabaseError(f"Query failed: {e}")


def execute_update(query: str, params: tuple = (), db_path: str = None) -> int:
    """
    Execute INSERT/UPDATE/DELETE query.

    Args:
        query: SQL statement
        params: Query parameters
        db_path: Optional database path

    Returns:
        Last inserted row ID or rows affected

    Raises:
        DatabaseError: If query fails
    """
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

        last_id = cursor.lastrowid
        conn.close()
        return last_id
    except sqlite3.Error as e:
        logger.error(f"Update failed: {e}")
        raise DatabaseError(f"Update failed: {e}")


def create_record(table: str, data: Dict, db_path: str = None) -> int:
    """
    Generic INSERT function.

    Args:
        table: Table name
        data: Dict of {column: value}
        db_path: Optional database path

    Returns:
        Last inserted ID

    Example:
        >>> edge_id = create_record('tv_edges', {
        ...     'user_id': 1,
        ...     'title': 'Grid Support',
        ...     'category': 'grid'
        ... })
    """
    if not data:
        raise ValueError("Data cannot be empty")

    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    return execute_update(query, tuple(data.values()), db_path)


def update_record(table: str, record_id: int, data: Dict, db_path: str = None) -> None:
    """
    Generic UPDATE function.

    Args:
        table: Table name
        record_id: Row ID
        data: Dict of {column: value} to update
        db_path: Optional database path

    Example:
        >>> update_record('tv_edges', 42, {'status': 'deprecated'})
    """
    if not data:
        raise ValueError("Data cannot be empty")

    set_clause = ', '.join([f"{k} = ?" for k in data.keys()])

    # Check if table has 'last_updated' column
    try:
        has_last_updated = False
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        has_last_updated = 'last_updated' in columns
        conn.close()
    except:
        has_last_updated = False

    if has_last_updated:
        query = f"UPDATE {table} SET {set_clause}, last_updated = CURRENT_TIMESTAMP WHERE id = ?"
    else:
        query = f"UPDATE {table} SET {set_clause} WHERE id = ?"

    params = tuple(list(data.values()) + [record_id])
    execute_update(query, params, db_path)


def get_record(table: str, record_id: int, db_path: str = None) -> Optional[Dict]:
    """
    Fetch single record by ID.

    Args:
        table: Table name
        record_id: Row ID
        db_path: Optional database path

    Returns:
        Record dict or None if not found
    """
    results = execute_query(
        f"SELECT * FROM {table} WHERE id = ?",
        (record_id,),
        db_path
    )
    return results[0] if results else None


def search_records(
    table: str,
    filters: Dict = None,
    limit: int = 100,
    db_path: str = None
) -> List[Dict]:
    """
    Search records with multiple filters.

    Args:
        table: Table name
        filters: Dict of {column: value} for WHERE clause
        limit: Max results
        db_path: Optional database path

    Returns:
        List of matching records

    Example:
        >>> edges = search_records('tv_edges', {
        ...     'user_id': 1,
        ...     'category': 'grid',
        ...     'status': 'active'
        ... })
    """
    if not filters:
        return execute_query(
            f"SELECT * FROM {table} LIMIT ?",
            (limit,),
            db_path
        )

    where_clause = ' AND '.join([f"{k} = ?" for k in filters.keys()])
    query = f"SELECT * FROM {table} WHERE {where_clause} LIMIT ?"

    params = tuple(list(filters.values()) + [limit])
    return execute_query(query, params, db_path)


def delete_record(table: str, record_id: int, db_path: str = None) -> None:
    """
    Delete record (soft delete if 'archived' column exists).

    Args:
        table: Table name
        record_id: Row ID
        db_path: Optional database path
    """
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        if 'archived' in columns:
            # Soft delete
            update_record(table, record_id, {'archived': 1}, db_path)
        else:
            # Hard delete
            execute_update(
                f"DELETE FROM {table} WHERE id = ?",
                (record_id,),
                db_path
            )
    except sqlite3.Error as e:
        logger.error(f"Delete failed: {e}")
        raise DatabaseError(f"Delete failed: {e}")


def count_records(table: str, filters: Dict = None, db_path: str = None) -> int:
    """
    Count records matching filters.

    Args:
        table: Table name
        filters: Optional filter dict
        db_path: Optional database path

    Returns:
        Count of matching records
    """
    if not filters:
        query = f"SELECT COUNT(*) as count FROM {table}"
        results = execute_query(query, (), db_path)
    else:
        where_clause = ' AND '.join([f"{k} = ?" for k in filters.keys()])
        query = f"SELECT COUNT(*) as count FROM {table} WHERE {where_clause}"
        results = execute_query(query, tuple(filters.values()), db_path)

    return results[0]['count'] if results else 0


def get_all_records(table: str, limit: int = 1000, db_path: str = None) -> List[Dict]:
    """
    Get all records from a table.

    Args:
        table: Table name
        limit: Max results
        db_path: Optional database path

    Returns:
        List of all records
    """
    return execute_query(
        f"SELECT * FROM {table} LIMIT ?",
        (limit,),
        db_path
    )


def _get_database_schema() -> str:
    """Return the complete database schema."""
    return """
    -- ============================================
    -- USER & SESSION MANAGEMENT
    -- ============================================

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        telegram_id TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1
    );

    -- ============================================
    -- NOTIFICATIONS (Shared across apps)
    -- ============================================

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        app_name TEXT,
        notification_type TEXT,
        title TEXT NOT NULL,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- ============================================
    -- GLOBAL TAGS & SEARCH (Shared)
    -- ============================================

    CREATE TABLE IF NOT EXISTS global_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag TEXT UNIQUE NOT NULL,
        category TEXT,
        usage_count INTEGER DEFAULT 0,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        query TEXT NOT NULL,
        app_name TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS saved_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        search_name TEXT NOT NULL,
        query_params TEXT,
        app_name TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- ============================================
    -- TRADEVAULT: STRATEGIES
    -- ============================================

    CREATE TABLE IF NOT EXISTS tv_strategies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        timeframe TEXT,
        instrument TEXT,
        grid_details TEXT,
        is_active INTEGER DEFAULT 1,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- ============================================
    -- TRADEVAULT: EDGES
    -- ============================================

    CREATE TABLE IF NOT EXISTS tv_edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        strategy_id INTEGER,
        timeframe TEXT,
        market_condition TEXT,
        instrument TEXT,
        description TEXT,
        status TEXT DEFAULT 'active',
        win_rate REAL,
        avg_points REAL,
        sample_size INTEGER,
        profit_factor REAL,
        confidence_grade TEXT,
        risk_reward_ratio REAL,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        testing_period_start DATE,
        testing_period_end DATE,
        live_performance REAL,
        source TEXT,
        observations TEXT,
        why_it_works TEXT,
        failure_conditions TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (strategy_id) REFERENCES tv_strategies(id)
    );

    CREATE TABLE IF NOT EXISTS tv_edge_screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        edge_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        caption TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (edge_id) REFERENCES tv_edges(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tv_edge_tags (
        edge_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        PRIMARY KEY (edge_id, tag),
        FOREIGN KEY (edge_id) REFERENCES tv_edges(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tv_edge_relationships (
        edge_id_1 INTEGER NOT NULL,
        edge_id_2 INTEGER NOT NULL,
        relationship_type TEXT,
        notes TEXT,
        PRIMARY KEY (edge_id_1, edge_id_2),
        FOREIGN KEY (edge_id_1) REFERENCES tv_edges(id) ON DELETE CASCADE,
        FOREIGN KEY (edge_id_2) REFERENCES tv_edges(id) ON DELETE CASCADE
    );

    -- ============================================
    -- TRADEVAULT: PROMPTS & VERSIONING
    -- ============================================

    CREATE TABLE IF NOT EXISTS tv_prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        content TEXT NOT NULL,
        use_case TEXT,
        expected_output TEXT,
        version TEXT DEFAULT '1.0',
        status TEXT DEFAULT 'active',
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used_date TIMESTAMP,
        usage_count INTEGER DEFAULT 0,
        is_favorite INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS tv_prompt_tags (
        prompt_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        PRIMARY KEY (prompt_id, tag),
        FOREIGN KEY (prompt_id) REFERENCES tv_prompts(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tv_prompt_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_id INTEGER NOT NULL,
        version TEXT NOT NULL,
        content TEXT NOT NULL,
        modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prompt_id) REFERENCES tv_prompts(id) ON DELETE CASCADE
    );

    -- ============================================
    -- TRADEVAULT: INSIGHTS
    -- ============================================

    CREATE TABLE IF NOT EXISTS tv_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT,
        date_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        confidence_level TEXT,
        status TEXT DEFAULT 'open',
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- ============================================
    -- TRADEVAULT: OBSERVATIONS (New)
    -- ============================================

    CREATE TABLE IF NOT EXISTS tv_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stock_name TEXT NOT NULL,
        observation_text TEXT NOT NULL,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS tv_observation_screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        observation_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        caption TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (observation_id) REFERENCES tv_observations(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tv_observation_tags (
        observation_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        PRIMARY KEY (observation_id, tag),
        FOREIGN KEY (observation_id) REFERENCES tv_observations(id) ON DELETE CASCADE
    );

    -- ============================================
    -- GENERAL: NOTES
    -- ============================================

    CREATE TABLE IF NOT EXISTS gen_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT,
        importance INTEGER,
        color TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        archived INTEGER DEFAULT 0,
        pinned INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS gen_note_tags (
        note_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        PRIMARY KEY (note_id, tag),
        FOREIGN KEY (note_id) REFERENCES gen_notes(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS gen_note_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (note_id) REFERENCES gen_notes(id) ON DELETE CASCADE
    );

    -- ============================================
    -- GENERAL: TASKS
    -- ============================================

    CREATE TABLE IF NOT EXISTS gen_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        priority INTEGER,
        status TEXT DEFAULT 'pending',
        due_date DATE,
        due_time TIME,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_date TIMESTAMP,
        is_recurring INTEGER DEFAULT 0,
        recurrence_pattern TEXT,
        recurrence_end_date DATE,
        parent_task_id INTEGER,
        estimated_hours REAL,
        actual_hours_spent REAL,
        archived INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (parent_task_id) REFERENCES gen_tasks(id)
    );

    CREATE TABLE IF NOT EXISTS gen_task_tags (
        task_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        PRIMARY KEY (task_id, tag),
        FOREIGN KEY (task_id) REFERENCES gen_tasks(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS gen_task_reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        reminder_type TEXT,
        reminder_value INTEGER,
        reminder_time TIME,
        is_sent INTEGER DEFAULT 0,
        sent_date TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES gen_tasks(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS gen_task_checklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        item TEXT NOT NULL,
        is_completed INTEGER DEFAULT 0,
        FOREIGN KEY (task_id) REFERENCES gen_tasks(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS gen_task_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        action TEXT,
        action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (task_id) REFERENCES gen_tasks(id) ON DELETE CASCADE
    );

    -- ============================================
    -- GENERAL: EVENTS (CALENDAR)
    -- ============================================

    CREATE TABLE IF NOT EXISTS gen_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        start_date DATE NOT NULL,
        start_time TIME,
        end_date DATE,
        end_time TIME,
        location TEXT,
        is_all_day INTEGER DEFAULT 0,
        category TEXT,
        reminder_minutes_before INTEGER DEFAULT 1440,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- ============================================
    -- INDEXES (Performance optimization)
    -- ============================================

    CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
    CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id);

    CREATE INDEX IF NOT EXISTS idx_tv_edges_user ON tv_edges(user_id);
    CREATE INDEX IF NOT EXISTS idx_tv_edges_status ON tv_edges(status);
    CREATE INDEX IF NOT EXISTS idx_tv_edges_category ON tv_edges(category);
    CREATE INDEX IF NOT EXISTS idx_tv_edges_strategy ON tv_edges(strategy_id);
    CREATE INDEX IF NOT EXISTS idx_tv_edges_created ON tv_edges(created_date);
    CREATE INDEX IF NOT EXISTS idx_tv_prompts_user ON tv_prompts(user_id);
    CREATE INDEX IF NOT EXISTS idx_tv_insights_user ON tv_insights(user_id);
    CREATE INDEX IF NOT EXISTS idx_tv_edge_tags_tag ON tv_edge_tags(tag);

    CREATE INDEX IF NOT EXISTS idx_gen_notes_user ON gen_notes(user_id);
    CREATE INDEX IF NOT EXISTS idx_gen_notes_created ON gen_notes(created_date);
    CREATE INDEX IF NOT EXISTS idx_gen_notes_importance ON gen_notes(importance);
    CREATE INDEX IF NOT EXISTS idx_gen_tasks_user ON gen_tasks(user_id);
    CREATE INDEX IF NOT EXISTS idx_gen_tasks_status ON gen_tasks(status);
    CREATE INDEX IF NOT EXISTS idx_gen_tasks_due_date ON gen_tasks(due_date);
    CREATE INDEX IF NOT EXISTS idx_gen_tasks_priority ON gen_tasks(priority);
    CREATE INDEX IF NOT EXISTS idx_gen_events_user ON gen_events(user_id);
    CREATE INDEX IF NOT EXISTS idx_gen_events_date ON gen_events(start_date);
    CREATE INDEX IF NOT EXISTS idx_gen_note_tags_tag ON gen_note_tags(tag);
    CREATE INDEX IF NOT EXISTS idx_gen_task_tags_tag ON gen_task_tags(tag);
    """
