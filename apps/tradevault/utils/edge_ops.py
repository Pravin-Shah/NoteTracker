"""
Edge-specific database operations for TradeVault App.
Trading edges management with performance tracking and relationships.
"""

from typing import List, Dict, Optional
from datetime import datetime
from core.db import (
    create_record, update_record, get_record, search_records,
    execute_query, delete_record
)
from core.validators import validate_edge_title, validate_confidence_grade
from core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def create_edge(user_id: int, edge_data: Dict, db_path: str = None) -> int:
    """
    Create new trading edge.

    Args:
        user_id: User ID
        edge_data: {
            'title': str (5-100 chars),
            'category': str ('grid', 'bias', 'pivot', 'MA-trail', 'volatility', 'reversal'),
            'strategy_id': int (optional),
            'timeframe': str ('1m', '5m', '15m', '30m', '1h', 'daily'),
            'market_condition': str ('trending-up', 'ranging', 'volatile'),
            'instrument': str ('Nifty', 'Bank Nifty', 'stocks'),
            'description': str,
            'status': str ('active', 'testing', 'deprecated', 'hibernated'),
            'win_rate': float (0-100),
            'avg_points': float,
            'sample_size': int,
            'profit_factor': float,
            'confidence_grade': str ('A', 'B', 'C'),
            'risk_reward_ratio': float,
            'testing_period_start': str (YYYY-MM-DD),
            'testing_period_end': str (YYYY-MM-DD),
            'live_performance': float (optional),
            'source': str ('backtesting', 'live', 'observation'),
            'observations': str,
            'why_it_works': str,
            'failure_conditions': str,
        }

    Returns:
        Edge ID

    Raises:
        ValidationError: If validation fails
    """
    if not validate_edge_title(edge_data.get('title', '')):
        raise ValidationError("Invalid edge title (5-100 chars)")

    if edge_data.get('confidence_grade') and not validate_confidence_grade(edge_data['confidence_grade']):
        raise ValidationError("Invalid confidence grade (A, B, or C)")

    # Validate required fields
    if not edge_data.get('category'):
        raise ValidationError("Category is required")

    edge_data['user_id'] = user_id
    edge_data.setdefault('status', 'active')
    edge_data.setdefault('confidence_grade', 'B')

    edge_id = create_record('tv_edges', edge_data, db_path)
    logger.info(f"Edge created: {edge_id} by user {user_id}")
    return edge_id


def get_edge(user_id: int, edge_id: int, db_path: str = None) -> Optional[Dict]:
    """
    Get single edge with all details.

    Args:
        user_id: User ID (for verification)
        edge_id: Edge ID

    Returns:
        Edge dict with tags, screenshots, relationships
    """
    edge = get_record('tv_edges', edge_id, db_path)

    if not edge or edge['user_id'] != user_id:
        return None

    edge = dict(edge)

    # Get tags
    tags = execute_query(
        "SELECT tag FROM tv_edge_tags WHERE edge_id = ?",
        (edge_id,),
        db_path
    )
    edge['tags'] = [t['tag'] for t in tags]

    # Get screenshots
    screenshots = execute_query(
        "SELECT id, file_path, caption FROM tv_edge_screenshots WHERE edge_id = ? ORDER BY upload_date DESC",
        (edge_id,),
        db_path
    )
    edge['screenshots'] = [dict(s) for s in screenshots]

    # Get relationships
    relationships = execute_query(
        """SELECT edge_id_2, relationship_type, notes FROM tv_edge_relationships
           WHERE edge_id_1 = ?
           UNION
           SELECT edge_id_1, relationship_type, notes FROM tv_edge_relationships
           WHERE edge_id_2 = ?""",
        (edge_id, edge_id),
        db_path
    )
    edge['relationships'] = [dict(r) for r in relationships]

    return edge


def update_edge(user_id: int, edge_id: int, updates: Dict, db_path: str = None) -> None:
    """
    Update edge.

    Args:
        user_id: User ID
        edge_id: Edge ID
        updates: Fields to update
    """
    edge = get_record('tv_edges', edge_id, db_path)
    if not edge or edge['user_id'] != user_id:
        raise ValidationError("Edge not found")

    if 'title' in updates and not validate_edge_title(updates['title']):
        raise ValidationError("Invalid edge title (5-100 chars)")

    if 'confidence_grade' in updates and not validate_confidence_grade(updates['confidence_grade']):
        raise ValidationError("Invalid confidence grade (A, B, or C)")

    update_record('tv_edges', edge_id, updates, db_path)
    logger.info(f"Edge updated: {edge_id}")


def delete_edge(user_id: int, edge_id: int, db_path: str = None) -> None:
    """
    Delete edge (soft delete - archives).

    Args:
        user_id: User ID
        edge_id: Edge ID
    """
    edge = get_record('tv_edges', edge_id, db_path)
    if not edge or edge['user_id'] != user_id:
        raise ValidationError("Edge not found")

    # Mark as deprecated instead of deleting
    update_edge(user_id, edge_id, {'status': 'deprecated'})
    logger.info(f"Edge deprecated: {edge_id}")


def search_edges(
    user_id: int,
    query: str = "",
    category: str = None,
    status: str = None,
    timeframe: str = None,
    confidence_grade: str = None,
    strategy_id: int = None,
    tags: List[str] = None,
    limit: int = 100, db_path: str = None) -> List[Dict]:
    """
    Search edges by text and filters.

    Args:
        user_id: User ID
        query: Search text
        category: Filter by category
        status: Filter by status
        timeframe: Filter by timeframe
        confidence_grade: Filter by confidence
        strategy_id: Filter by strategy
        tags: Filter by tags (match any)
        limit: Max results

    Returns:
        List of matching edges
    """
    sql = "SELECT * FROM tv_edges WHERE user_id = ?"
    params = [user_id]

    if query:
        sql += " AND (title LIKE ? OR description LIKE ? OR observations LIKE ? OR why_it_works LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"])

    if category:
        sql += " AND category = ?"
        params.append(category)

    if status:
        sql += " AND status = ?"
        params.append(status)

    if timeframe:
        sql += " AND timeframe = ?"
        params.append(timeframe)

    if confidence_grade:
        sql += " AND confidence_grade = ?"
        params.append(confidence_grade)

    if strategy_id:
        sql += " AND strategy_id = ?"
        params.append(strategy_id)

    sql += " ORDER BY win_rate DESC, profit_factor DESC, created_date DESC LIMIT ?"
    params.append(limit)

    results = execute_query(sql, tuple(params), db_path)
    edges = [dict(row) for row in results]

    # Add tags if filtering
    if tags:
        filtered_edges = []
        for edge in edges:
            edge_tags = execute_query(
                "SELECT tag FROM tv_edge_tags WHERE edge_id = ?",
                (edge['id'],),
                db_path
            )
            edge_tag_list = [t['tag'] for t in edge_tags]

            if any(tag in edge_tag_list for tag in tags):
                edge['tags'] = edge_tag_list
                filtered_edges.append(edge)

        edges = filtered_edges
    else:
        for edge in edges:
            edge_tags = execute_query(
                "SELECT tag FROM tv_edge_tags WHERE edge_id = ?",
                (edge['id'], db_path)
            )
            edge['tags'] = [t['tag'] for t in edge_tags]

    return edges


def get_top_performers(user_id: int, limit: int = 10, db_path: str = None) -> List[Dict]:
    """
    Get highest win-rate edges.

    Args:
        user_id: User ID
        limit: Max results

    Returns:
        List of top performing edges
    """
    results = execute_query("""
        SELECT * FROM tv_edges
        WHERE user_id = ? AND status IN ('active', 'testing')
        ORDER BY win_rate DESC, profit_factor DESC, sample_size DESC
        LIMIT ?
    """, (user_id, limit), db_path)

    edges = [dict(row) for row in results]

    # Add tags
    for edge in edges:
        tags = execute_query(
            "SELECT tag FROM tv_edge_tags WHERE edge_id = ?",
            (edge['id'], db_path)
        )
        edge['tags'] = [t['tag'] for t in tags]

    return edges


def get_edges_by_strategy(user_id: int, strategy_id: int, db_path: str = None) -> List[Dict]:
    """
    Get all edges used in a strategy.

    Args:
        user_id: User ID
        strategy_id: Strategy ID

    Returns:
        List of edges in strategy
    """
    results = execute_query("""
        SELECT * FROM tv_edges
        WHERE user_id = ? AND strategy_id = ? AND status IN ('active', 'testing')
        ORDER BY confidence_grade ASC, win_rate DESC
    """, (user_id, strategy_id), db_path)

    return [dict(row) for row in results]


def add_edge_tag(edge_id: int, tag: str, db_path: str = None) -> None:
    """
    Add tag to edge.

    Args:
        edge_id: Edge ID
        tag: Tag name
    """
    try:
        create_record('tv_edge_tags', {
            'edge_id': edge_id,
            'tag': tag.lower()
        }, db_path)
        logger.info(f"Tag added to edge {edge_id}: {tag}")
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            logger.debug(f"Tag already exists on edge {edge_id}: {tag}")
        else:
            raise


def remove_edge_tag(edge_id: int, tag: str, db_path: str = None) -> None:
    """
    Remove tag from edge.

    Args:
        edge_id: Edge ID
        tag: Tag name
    """
    from core.db import execute_update
    execute_update(
        "DELETE FROM tv_edge_tags WHERE edge_id = ? AND tag = ?",
        (edge_id, tag.lower()),
        db_path
    )


def upload_edge_screenshot(edge_id: int, file_path: str, caption: str = "", db_path: str = None) -> int:
    """
    Upload screenshot for edge.

    Args:
        edge_id: Edge ID
        file_path: Path to screenshot
        caption: Caption text

    Returns:
        Screenshot ID
    """
    screenshot_id = create_record('tv_edge_screenshots', {
        'edge_id': edge_id,
        'file_path': file_path,
        'caption': caption
    }, db_path)
    logger.info(f"Screenshot uploaded for edge {edge_id}")
    return screenshot_id


def remove_edge_screenshot(screenshot_id: int, db_path: str = None) -> None:
    """
    Remove screenshot from edge.

    Args:
        screenshot_id: Screenshot ID
    """
    from core.db import execute_update
    execute_update(
        "DELETE FROM tv_edge_screenshots WHERE id = ?",
        (screenshot_id, db_path)
    )


def link_edges(
    edge_id_1: int,
    edge_id_2: int,
    relationship_type: str,
    notes: str = "", db_path: str = None) -> None:
    """
    Link two edges with relationship.

    Args:
        edge_id_1: First edge ID
        edge_id_2: Second edge ID
        relationship_type: 'complements', 'conflicts', 'prerequisite', 'advanced_version'
        notes: Optional notes
    """
    create_record('tv_edge_relationships', {
        'edge_id_1': edge_id_1,
        'edge_id_2': edge_id_2,
        'relationship_type': relationship_type,
        'notes': notes
    }, db_path)
    logger.info(f"Edges linked: {edge_id_1} -> {edge_id_2} ({relationship_type})")


def unlink_edges(edge_id_1: int, edge_id_2: int, db_path: str = None) -> None:
    """
    Remove relationship between edges.

    Args:
        edge_id_1: First edge ID
        edge_id_2: Second edge ID
    """
    from core.db import execute_update
    execute_update(
        "DELETE FROM tv_edge_relationships WHERE (edge_id_1 = ? AND edge_id_2 = ?) OR (edge_id_1 = ? AND edge_id_2 = ?)",
        (edge_id_1, edge_id_2, edge_id_2, edge_id_1),
        db_path
    )


def get_edge_categories(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all edge categories used by user.

    Args:
        user_id: User ID

    Returns:
        List of categories
    """
    results = execute_query(
        "SELECT DISTINCT category FROM tv_edges WHERE user_id = ? ORDER BY category",
        (user_id, db_path)
    )
    return [row['category'] for row in results]


def get_edge_tags(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all tags used in user's edges.

    Args:
        user_id: User ID

    Returns:
        List of tags
    """
    results = execute_query(
        """SELECT DISTINCT tag FROM tv_edge_tags
           WHERE edge_id IN (SELECT id FROM tv_edges WHERE user_id = ?)
           ORDER BY tag""",
        (user_id,),
        db_path
    )
    return [row['tag'] for row in results]


def get_edge_stats(user_id: int, db_path: str = None) -> Dict:
    """
    Get edge statistics for user.

    Args:
        user_id: User ID

    Returns:
        Stats dict
    """
    total = execute_query(
        "SELECT COUNT(*) as count FROM tv_edges WHERE user_id = ?",
        (user_id,),
        db_path
    )

    active = execute_query(
        "SELECT COUNT(*) as count FROM tv_edges WHERE user_id = ? AND status = 'active'",
        (user_id,),
        db_path
    )

    testing = execute_query(
        "SELECT COUNT(*) as count FROM tv_edges WHERE user_id = ? AND status = 'testing'",
        (user_id,),
        db_path
    )

    by_category = execute_query(
        "SELECT category, COUNT(*) as count FROM tv_edges WHERE user_id = ? GROUP BY category",
        (user_id,),
        db_path
    )

    avg_stats = execute_query(
        "SELECT AVG(win_rate) as avg_wr, AVG(profit_factor) as avg_pf FROM tv_edges WHERE user_id = ? AND status IN ('active', 'testing')",
        (user_id,),
        db_path
    )

    return {
        'total': total[0]['count'] if total else 0,
        'active': active[0]['count'] if active else 0,
        'testing': testing[0]['count'] if testing else 0,
        'by_category': {row['category']: row['count'] for row in by_category} if by_category else {},
        'avg_win_rate': avg_stats[0]['avg_wr'] if avg_stats and avg_stats[0]['avg_wr'] else 0,
        'avg_profit_factor': avg_stats[0]['avg_pf'] if avg_stats and avg_stats[0]['avg_pf'] else 0
    }


def export_edges(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Export all user's edges.

    Args:
        user_id: User ID

    Returns:
        List of all edges ready for export
    """
    results = execute_query(
        "SELECT * FROM tv_edges WHERE user_id = ? ORDER BY created_date DESC",
        (user_id,),
        db_path
    )

    edges = [dict(row) for row in results]

    # Add tags and screenshots
    for edge in edges:
        tags = execute_query(
            "SELECT tag FROM tv_edge_tags WHERE edge_id = ?",
            (edge['id'], db_path)
        )
        edge['tags'] = [t['tag'] for t in tags]

        screenshots = execute_query(
            "SELECT file_path, caption FROM tv_edge_screenshots WHERE edge_id = ?",
            (edge['id'], db_path)
        )
        edge['screenshots'] = [dict(s) for s in screenshots]

    logger.info(f"Exported {len(edges)} edges for user {user_id}")
    return edges
