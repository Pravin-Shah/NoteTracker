"""
Full-text search for General App.
Unified search across notes, tasks, and events.
"""

from typing import List, Dict, Optional
from core.db import execute_query, create_record
from core.exceptions import DatabaseError
import logging

logger = logging.getLogger(__name__)


def search_notes(
    user_id: int,
    query: str,
    limit: int = 50,
    db_path: str = None) -> List[Dict]:
    """
    Full-text search in notes.

    Args:
        user_id: User ID
        query: Search query
        limit: Max results

    Returns:
        List of matching notes
    """
    results = execute_query("""
        SELECT id, title, content, category, importance, created_date,
               'note' as item_type, title as display_title
        FROM gen_notes
        WHERE user_id = ? AND archived = 0
        AND (title LIKE ? OR content LIKE ?)
        ORDER BY
            CASE WHEN title LIKE ? THEN 0 ELSE 1 END,
            last_updated DESC
        LIMIT ?
    """, (user_id, f"%{query}%", f"%{query}%", f"%{query}%", limit), db_path)

    return [dict(row) for row in results]


def search_tasks(
    user_id: int,
    query: str,
    limit: int = 50,
    db_path: str = None) -> List[Dict]:
    """
    Full-text search in tasks.

    Args:
        user_id: User ID
        query: Search query
        limit: Max results

    Returns:
        List of matching tasks
    """
    results = execute_query("""
        SELECT id, title, description, status, priority, due_date, created_date,
               'task' as item_type, title as display_title
        FROM gen_tasks
        WHERE user_id = ? AND archived = 0
        AND (title LIKE ? OR description LIKE ?)
        ORDER BY
            CASE WHEN title LIKE ? THEN 0 ELSE 1 END,
            due_date ASC,
            priority DESC
        LIMIT ?
    """, (user_id, f"%{query}%", f"%{query}%", f"%{query}%", limit), db_path)

    return [dict(row) for row in results]


def search_events(
    user_id: int,
    query: str,
    limit: int = 50,
    db_path: str = None) -> List[Dict]:
    """
    Full-text search in events.

    Args:
        user_id: User ID
        query: Search query
        limit: Max results

    Returns:
        List of matching events
    """
    results = execute_query("""
        SELECT id, title, description, location, start_date, category, created_date,
               'event' as item_type, title as display_title
        FROM gen_events
        WHERE user_id = ?
        AND (title LIKE ? OR description LIKE ? OR location LIKE ?)
        ORDER BY
            CASE WHEN title LIKE ? THEN 0 ELSE 1 END,
            start_date DESC
        LIMIT ?
    """, (user_id, f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit), db_path)

    return [dict(row) for row in results]


def global_search(
    user_id: int,
    query: str,
    item_types: List[str] = None,
    limit: int = 100,
    db_path: str = None) -> Dict[str, List[Dict]]:
    """
    Search across all items (notes, tasks, events).

    Args:
        user_id: User ID
        query: Search query
        item_types: List of item types to search ('note', 'task', 'event')
                   Default: all types
        limit: Max total results

    Returns:
        Dict with 'notes', 'tasks', 'events' keys
    """
    if not item_types:
        item_types = ['note', 'task', 'event']

    results = {
        'notes': [],
        'tasks': [],
        'events': []
    }

    if 'note' in item_types:
        results['notes'] = search_notes(user_id, query, limit=limit // 3, db_path=db_path)

    if 'task' in item_types:
        results['tasks'] = search_tasks(user_id, query, limit=limit // 3, db_path=db_path)

    if 'event' in item_types:
        results['events'] = search_events(user_id, query, limit=limit // 3, db_path=db_path)

    # Log search
    save_search_history(user_id, query, 'general', db_path)

    return results


def save_search_history(user_id: int, query: str, app_name: str = 'general', db_path: str = None) -> None:
    """
    Save search query to history.

    Args:
        user_id: User ID
        query: Search query
        app_name: App name
    """
    try:
        create_record('search_history', {
            'user_id': user_id,
            'query': query,
            'app_name': app_name
        }, db_path)
    except Exception as e:
        logger.warning(f"Failed to save search history: {e}")


def get_search_history(user_id: int, limit: int = 20, db_path: str = None) -> List[str]:
    """
    Get recent search history for user.

    Args:
        user_id: User ID
        limit: Max results

    Returns:
        List of recent search queries
    """
    results = execute_query("""
        SELECT DISTINCT query FROM search_history
        WHERE user_id = ? AND app_name = 'general'
        ORDER BY created_date DESC
        LIMIT ?
    """, (user_id, limit), db_path)

    return [row['query'] for row in results]


def clear_search_history(user_id: int, db_path: str = None) -> None:
    """
    Clear search history for user.

    Args:
        user_id: User ID
    """
    from core.db import execute_update
    execute_update(
        "DELETE FROM search_history WHERE user_id = ? AND app_name = 'general'",
        (user_id,),
        db_path
    )
    logger.info(f"Search history cleared for user {user_id}")


def search_by_tag(
    user_id: int,
    tag: str,
    item_types: List[str] = None,
    limit: int = 100,
    db_path: str = None) -> Dict[str, List[Dict]]:
    """
    Search items by tag.

    Args:
        user_id: User ID
        tag: Tag name
        item_types: Item types to search
        limit: Max results

    Returns:
        Dict with search results
    """
    if not item_types:
        item_types = ['note', 'task']

    results = {'notes': [], 'tasks': []}

    # Search notes by tag
    if 'note' in item_types:
        note_results = execute_query("""
            SELECT n.id, n.title, n.content, n.category, n.importance,
                   n.created_date, 'note' as item_type, n.title as display_title
            FROM gen_notes n
            JOIN gen_note_tags nt ON n.id = nt.note_id
            WHERE n.user_id = ? AND nt.tag = ? AND n.archived = 0
            ORDER BY n.last_updated DESC
            LIMIT ?
        """, (user_id, tag.lower(), limit // 2), db_path)

        results['notes'] = [dict(row) for row in note_results]

    # Search tasks by tag
    if 'task' in item_types:
        task_results = execute_query("""
            SELECT t.id, t.title, t.description, t.status, t.priority,
                   t.due_date, t.created_date, 'task' as item_type, t.title as display_title
            FROM gen_tasks t
            JOIN gen_task_tags tt ON t.id = tt.task_id
            WHERE t.user_id = ? AND tt.tag = ? AND t.archived = 0
            ORDER BY t.due_date ASC, t.priority DESC
            LIMIT ?
        """, (user_id, tag.lower(), limit // 2), db_path)

        results['tasks'] = [dict(row) for row in task_results]

    return results


def search_by_category(
    user_id: int,
    category: str,
    item_types: List[str] = None,
    limit: int = 100,
    db_path: str = None) -> Dict[str, List[Dict]]:
    """
    Search items by category.

    Args:
        user_id: User ID
        category: Category name
        item_types: Item types to search
        limit: Max results

    Returns:
        Dict with search results
    """
    if not item_types:
        item_types = ['note', 'task', 'event']

    results = {'notes': [], 'tasks': [], 'events': []}

    if 'note' in item_types:
        notes = execute_query("""
            SELECT * FROM gen_notes
            WHERE user_id = ? AND category = ? AND archived = 0
            ORDER BY last_updated DESC
            LIMIT ?
        """, (user_id, category, limit // 3), db_path)
        results['notes'] = [dict(row) for row in notes]

    if 'task' in item_types:
        tasks = execute_query("""
            SELECT * FROM gen_tasks
            WHERE user_id = ? AND category = ? AND archived = 0
            ORDER BY due_date ASC
            LIMIT ?
        """, (user_id, category, limit // 3), db_path)
        results['tasks'] = [dict(row) for row in tasks]

    if 'event' in item_types:
        events = execute_query("""
            SELECT * FROM gen_events
            WHERE user_id = ? AND category = ?
            ORDER BY start_date ASC
            LIMIT ?
        """, (user_id, category, limit // 3), db_path)
        results['events'] = [dict(row) for row in events]

    return results


def search_by_date_range(
    user_id: int,
    start_date: str,
    end_date: str,
    item_types: List[str] = None,
    limit: int = 100,
    db_path: str = None) -> Dict[str, List[Dict]]:
    """
    Search items in date range.

    Args:
        user_id: User ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        item_types: Item types to search
        limit: Max results

    Returns:
        Dict with search results
    """
    if not item_types:
        item_types = ['task', 'event']

    results = {'tasks': [], 'events': []}

    if 'task' in item_types:
        tasks = execute_query("""
            SELECT * FROM gen_tasks
            WHERE user_id = ? AND due_date >= ? AND due_date <= ? AND archived = 0
            ORDER BY due_date ASC, priority DESC
            LIMIT ?
        """, (user_id, start_date, end_date, limit // 2), db_path)
        results['tasks'] = [dict(row) for row in tasks]

    if 'event' in item_types:
        events = execute_query("""
            SELECT * FROM gen_events
            WHERE user_id = ? AND start_date >= ? AND start_date <= ?
            ORDER BY start_date ASC
            LIMIT ?
        """, (user_id, start_date, end_date, limit // 2), db_path)
        results['events'] = [dict(row) for row in events]

    return results


def get_search_suggestions(user_id: int, prefix: str, limit: int = 10, db_path: str = None) -> Dict[str, List[str]]:
    """
    Get search suggestions based on prefix.

    Args:
        user_id: User ID
        prefix: Search prefix
        limit: Max suggestions

    Returns:
        Dict with suggestions from notes, tasks, tags
    """
    suggestions = {
        'notes': [],
        'tasks': [],
        'tags': []
    }

    # Note titles
    note_titles = execute_query("""
        SELECT DISTINCT title FROM gen_notes
        WHERE user_id = ? AND title LIKE ? AND archived = 0
        ORDER BY title LIMIT ?
    """, (user_id, f"{prefix}%", limit), db_path)
    suggestions['notes'] = [row['title'] for row in note_titles]

    # Task titles
    task_titles = execute_query("""
        SELECT DISTINCT title FROM gen_tasks
        WHERE user_id = ? AND title LIKE ? AND archived = 0
        ORDER BY title LIMIT ?
    """, (user_id, f"{prefix}%", limit), db_path)
    suggestions['tasks'] = [row['title'] for row in task_titles]

    # Tags
    tags = execute_query("""
        SELECT DISTINCT tag FROM gen_note_tags
        WHERE note_id IN (SELECT id FROM gen_notes WHERE user_id = ?)
        AND tag LIKE ?
        UNION
        SELECT DISTINCT tag FROM gen_task_tags
        WHERE task_id IN (SELECT id FROM gen_tasks WHERE user_id = ?)
        AND tag LIKE ?
        ORDER BY tag LIMIT ?
    """, (user_id, f"{prefix}%", user_id, f"{prefix}%", limit), db_path)
    suggestions['tags'] = [row['tag'] for row in tags]

    return suggestions
