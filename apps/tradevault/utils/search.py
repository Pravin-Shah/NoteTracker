"""
Edge-specific search for TradeVault App.
Advanced search and filtering for trading edges and prompts.
"""

from typing import List, Dict, Optional
from core.db import execute_query, create_record
from core.exceptions import DatabaseError
import logging

logger = logging.getLogger(__name__)


def search_edges(
    user_id: int,
    query: str,
    limit: int = 50, db_path: str = None) -> List[Dict]:
    """
    Full-text search in edges.

    Args:
        user_id: User ID
        query: Search query
        limit: Max results

    Returns:
        List of matching edges
    """
    results = execute_query("""
        SELECT id, title, description, category, win_rate, confidence_grade,
               created_date, 'edge' as item_type, title as display_title
        FROM tv_edges
        WHERE user_id = ? AND status IN ('active', 'testing')
        AND (title LIKE ? OR description LIKE ? OR observations LIKE ? OR why_it_works LIKE ?)
        ORDER BY
            CASE WHEN title LIKE ? THEN 0 ELSE 1 END,
            win_rate DESC,
            profit_factor DESC
        LIMIT ?
    """, (user_id, f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit), db_path)

    return [dict(row) for row in results]


def search_prompts(
    user_id: int,
    query: str,
    limit: int = 50, db_path: str = None) -> List[Dict]:
    """
    Full-text search in prompts.

    Args:
        user_id: User ID
        query: Search query
        limit: Max results

    Returns:
        List of matching prompts
    """
    results = execute_query("""
        SELECT id, title, content, category, usage_count,
               created_date, 'prompt' as item_type, title as display_title
        FROM tv_prompts
        WHERE user_id = ? AND status = 'active'
        AND (title LIKE ? OR content LIKE ? OR use_case LIKE ?)
        ORDER BY
            is_favorite DESC,
            CASE WHEN title LIKE ? THEN 0 ELSE 1 END,
            last_used_date DESC
        LIMIT ?
    """, (user_id, f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit), db_path)

    return [dict(row) for row in results]


def search_insights(
    user_id: int,
    query: str,
    limit: int = 50,
    db_path: str = None) -> List[Dict]:
    """
    Full-text search in insights.

    Args:
        user_id: User ID
        query: Search query
        limit: Max results

    Returns:
        List of matching insights
    """
    results = execute_query("""
        SELECT id, title, description, status, confidence_level, date_observed,
               'insight' as item_type, title as display_title
        FROM tv_insights
        WHERE user_id = ?
        AND (title LIKE ? OR description LIKE ?)
        ORDER BY date_observed DESC
        LIMIT ?
    """, (user_id, f"%{query}%", f"%{query}%", limit), db_path)

    return [dict(row) for row in results]


def global_search(
    user_id: int,
    query: str,
    item_types: List[str] = None,
    limit: int = 100, db_path: str = None) -> Dict[str, List[Dict]]:
    """
    Search across all TradeVault items (edges, prompts, insights).

    Args:
        user_id: User ID
        query: Search query
        item_types: List of item types ('edge', 'prompt', 'insight')
                   Default: all types
        limit: Max total results

    Returns:
        Dict with 'edges', 'prompts', 'insights' keys
    """
    if not item_types:
        item_types = ['edge', 'prompt', 'insight']

    results = {
        'edges': [],
        'prompts': [],
        'insights': []
    }

    if 'edge' in item_types:
        results['edges'] = search_edges(user_id, query, limit=limit // 3)

    if 'prompt' in item_types:
        results['prompts'] = search_prompts(user_id, query, limit=limit // 3)

    if 'insight' in item_types:
        results['insights'] = search_insights(user_id, query, limit=limit // 3)

    # Log search
    save_search_history(user_id, query, 'tradevault')

    return results


def save_search_history(user_id: int, query: str, app_name: str = 'tradevault', db_path: str = None) -> None:
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
        WHERE user_id = ? AND app_name = 'tradevault'
        ORDER BY created_date DESC
        LIMIT ?
    """, (user_id, limit), db_path)

    return [row['query'] for row in results]


def search_by_category(
    user_id: int,
    category: str,
    min_win_rate: float = None,
    min_sample_size: int = None,
    limit: int = 100, db_path: str = None) -> List[Dict]:
    """
    Search edges by category with filters.

    Args:
        user_id: User ID
        category: Edge category
        min_win_rate: Minimum win rate (%)
        min_sample_size: Minimum sample size
        limit: Max results

    Returns:
        List of edges in category
    """
    sql = "SELECT * FROM tv_edges WHERE user_id = ? AND category = ? AND status IN ('active', 'testing')"
    params = [user_id, category]

    if min_win_rate:
        sql += " AND win_rate >= ?"
        params.append(min_win_rate)

    if min_sample_size:
        sql += " AND sample_size >= ?"
        params.append(min_sample_size)

    sql += " ORDER BY win_rate DESC, profit_factor DESC LIMIT ?"
    params.append(limit)

    results = execute_query(sql, tuple(params), db_path)
    return [dict(row) for row in results]


def search_by_timeframe(
    user_id: int,
    timeframe: str,
    limit: int = 100, db_path: str = None) -> List[Dict]:
    """
    Search edges by timeframe.

    Args:
        user_id: User ID
        timeframe: Timeframe (e.g., '5m', '1h', 'daily')
        limit: Max results

    Returns:
        List of edges for timeframe
    """
    results = execute_query("""
        SELECT * FROM tv_edges
        WHERE user_id = ? AND timeframe = ? AND status IN ('active', 'testing')
        ORDER BY win_rate DESC, profit_factor DESC
        LIMIT ?
    """, (user_id, timeframe, limit), db_path)

    return [dict(row) for row in results]


def search_by_confidence(
    user_id: int,
    confidence_grade: str,
    limit: int = 100, db_path: str = None) -> List[Dict]:
    """
    Search edges by confidence grade.

    Args:
        user_id: User ID
        confidence_grade: Grade ('A', 'B', 'C')
        limit: Max results

    Returns:
        List of edges
    """
    results = execute_query("""
        SELECT * FROM tv_edges
        WHERE user_id = ? AND confidence_grade = ? AND status IN ('active', 'testing')
        ORDER BY win_rate DESC, profit_factor DESC
        LIMIT ?
    """, (user_id, confidence_grade, limit), db_path)

    return [dict(row) for row in results]


def search_by_tag(
    user_id: int,
    tag: str,
    item_type: str = None,
    limit: int = 100, db_path: str = None) -> Dict[str, List[Dict]]:
    """
    Search by tag.

    Args:
        user_id: User ID
        tag: Tag name
        item_type: 'edge' or 'prompt'
        limit: Max results

    Returns:
        Dict with search results
    """
    results = {'edges': [], 'prompts': []}

    if not item_type or item_type == 'edge':
        edge_results = execute_query("""
            SELECT e.* FROM tv_edges e
            JOIN tv_edge_tags et ON e.id = et.edge_id
            WHERE e.user_id = ? AND et.tag = ? AND e.status IN ('active', 'testing')
            ORDER BY e.win_rate DESC
            LIMIT ?
        """, (user_id, tag.lower(), limit // 2), db_path)
        results['edges'] = [dict(row) for row in edge_results]

    if not item_type or item_type == 'prompt':
        prompt_results = execute_query("""
            SELECT p.* FROM tv_prompts p
            JOIN tv_prompt_tags pt ON p.id = pt.prompt_id
            WHERE p.user_id = ? AND pt.tag = ? AND p.status = 'active'
            ORDER BY p.is_favorite DESC, p.last_used_date DESC
            LIMIT ?
        """, (user_id, tag.lower(), limit // 2), db_path)
        results['prompts'] = [dict(row) for row in prompt_results]

    return results


def search_by_performance(
    user_id: int,
    min_win_rate: float = 50,
    min_profit_factor: float = 1.0,
    min_sample_size: int = 20,
    limit: int = 100, db_path: str = None) -> List[Dict]:
    """
    Search edges by performance criteria.

    Args:
        user_id: User ID
        min_win_rate: Minimum win rate (%)
        min_profit_factor: Minimum profit factor
        min_sample_size: Minimum sample size
        limit: Max results

    Returns:
        List of edges meeting criteria
    """
    results = execute_query("""
        SELECT * FROM tv_edges
        WHERE user_id = ? AND status IN ('active', 'testing')
        AND win_rate >= ? AND profit_factor >= ? AND sample_size >= ?
        ORDER BY confidence_grade ASC, win_rate DESC, profit_factor DESC
        LIMIT ?
    """, (user_id, min_win_rate, min_profit_factor, min_sample_size, limit), db_path)

    return [dict(row) for row in results]


def search_related_edges(edge_id: int, db_path: str = None) -> List[Dict]:
    """
    Find edges related to a given edge.

    Args:
        edge_id: Edge ID

    Returns:
        List of related edges
    """
    results = execute_query("""
        SELECT e.* FROM tv_edges e
        JOIN tv_edge_relationships er ON (
            (e.id = er.edge_id_2 AND er.edge_id_1 = ?) OR
            (e.id = er.edge_id_1 AND er.edge_id_2 = ?)
        )
        WHERE e.status IN ('active', 'testing')
        ORDER BY e.win_rate DESC
    """, (edge_id, edge_id), db_path)

    return [dict(row) for row in results]


def get_search_suggestions(user_id: int, prefix: str, limit: int = 10, db_path: str = None) -> Dict[str, List[str]]:
    """
    Get search suggestions based on prefix.

    Args:
        user_id: User ID
        prefix: Search prefix
        limit: Max suggestions

    Returns:
        Dict with suggestions from different categories
    """
    suggestions = {
        'edges': [],
        'prompts': [],
        'tags': [],
        'categories': []
    }

    # Edge titles
    edge_titles = execute_query("""
        SELECT DISTINCT title FROM tv_edges
        WHERE user_id = ? AND title LIKE ? AND status IN ('active', 'testing')
        ORDER BY title LIMIT ?
    """, (user_id, f"{prefix}%", limit), db_path)
    suggestions['edges'] = [row['title'] for row in edge_titles]

    # Prompt titles
    prompt_titles = execute_query("""
        SELECT DISTINCT title FROM tv_prompts
        WHERE user_id = ? AND title LIKE ? AND status = 'active'
        ORDER BY title LIMIT ?
    """, (user_id, f"{prefix}%", limit), db_path)
    suggestions['prompts'] = [row['title'] for row in prompt_titles]

    # Tags
    tags = execute_query("""
        SELECT DISTINCT tag FROM tv_edge_tags
        WHERE edge_id IN (SELECT id FROM tv_edges WHERE user_id = ?)
        AND tag LIKE ?
        UNION
        SELECT DISTINCT tag FROM tv_prompt_tags
        WHERE prompt_id IN (SELECT id FROM tv_prompts WHERE user_id = ?)
        AND tag LIKE ?
        ORDER BY tag LIMIT ?
    """, (user_id, f"{prefix}%", user_id, f"{prefix}%", limit), db_path)
    suggestions['tags'] = [row['tag'] for row in tags]

    # Categories
    categories = execute_query("""
        SELECT DISTINCT category FROM tv_edges
        WHERE user_id = ? AND category LIKE ? AND status IN ('active', 'testing')
        ORDER BY category LIMIT ?
    """, (user_id, f"{prefix}%", limit), db_path)
    suggestions['categories'] = [row['category'] for row in categories]

    return suggestions
