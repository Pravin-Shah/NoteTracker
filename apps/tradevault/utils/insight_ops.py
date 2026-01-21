"""
Insight management for TradeVault App.
Market observations and trading insights tracking.
"""

from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from core.db import (
    create_record, update_record, get_record, search_records,
    execute_query, delete_record
)
from core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def create_insight(user_id: int, insight_data: Dict, db_path: str = None) -> int:
    """
    Create new insight.

    Args:
        user_id: User ID
        insight_data: {
            'title': str,
            'description': str,
            'category': str ('market-behavior', 'bias', 'psychology', etc),
            'confidence_level': str ('hypothesis', 'weak', 'moderate', 'strong'),
            'status': str ('open', 'confirmed', 'disputed', default: 'open'),
        }

    Returns:
        Insight ID

    Raises:
        ValidationError: If validation fails
    """
    if not insight_data.get('title') or len(insight_data['title']) < 3:
        raise ValidationError("Insight title is required (min 3 chars)")

    if not insight_data.get('description') or len(insight_data['description']) < 10:
        raise ValidationError("Insight description is required (min 10 chars)")

    insight_data['user_id'] = user_id
    insight_data.setdefault('confidence_level', 'hypothesis')
    insight_data.setdefault('status', 'open')

    insight_id = create_record('tv_insights', insight_data, db_path)
    logger.info(f"Insight created: {insight_id} by user {user_id}")
    return insight_id


def get_insight(user_id: int, insight_id: int, db_path: str = None) -> Optional[Dict]:
    """
    Get single insight.

    Args:
        user_id: User ID (for verification)
        insight_id: Insight ID

    Returns:
        Insight dict or None
    """
    insight = get_record('tv_insights', insight_id, db_path)

    if not insight or insight['user_id'] != user_id:
        return None

    return dict(insight)


def update_insight(user_id: int, insight_id: int, updates: Dict, db_path: str = None) -> None:
    """
    Update insight.

    Args:
        user_id: User ID
        insight_id: Insight ID
        updates: Fields to update
    """
    insight = get_record('tv_insights', insight_id, db_path)
    if not insight or insight['user_id'] != user_id:
        raise ValidationError("Insight not found")

    update_record('tv_insights', insight_id, updates, db_path)
    logger.info(f"Insight updated: {insight_id}")


def delete_insight(user_id: int, insight_id: int, db_path: str = None) -> None:
    """
    Delete insight.

    Args:
        user_id: User ID
        insight_id: Insight ID
    """
    insight = get_record('tv_insights', insight_id, db_path)
    if not insight or insight['user_id'] != user_id:
        raise ValidationError("Insight not found")

    delete_record('tv_insights', insight_id, db_path)
    logger.info(f"Insight deleted: {insight_id}")


def search_insights(
    user_id: int,
    query: str = "",
    category: str = None,
    status: str = None,
    confidence_level: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100, db_path: str = None) -> List[Dict]:
    """
    Search insights by text and filters.

    Args:
        user_id: User ID
        query: Search text
        category: Filter by category
        status: Filter by status
        confidence_level: Filter by confidence
        start_date: Filter by date (YYYY-MM-DD)
        end_date: Filter by date (YYYY-MM-DD)
        limit: Max results

    Returns:
        List of matching insights
    """
    sql = "SELECT * FROM tv_insights WHERE user_id = ?"
    params = [user_id]

    if query:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])

    if category:
        sql += " AND category = ?"
        params.append(category)

    if status:
        sql += " AND status = ?"
        params.append(status)

    if confidence_level:
        sql += " AND confidence_level = ?"
        params.append(confidence_level)

    if start_date:
        sql += " AND DATE(date_observed) >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND DATE(date_observed) <= ?"
        params.append(end_date)

    sql += " ORDER BY date_observed DESC LIMIT ?"
    params.append(limit)

    results = execute_query(sql, tuple(params), db_path)
    return [dict(row) for row in results]


def get_recent_insights(user_id: int, days: int = 30, db_path: str = None) -> List[Dict]:
    """
    Get recent insights.

    Args:
        user_id: User ID
        days: Last N days

    Returns:
        List of recent insights
    """
    start_date = (date.today() - timedelta(days=days)).isoformat()
    return search_insights(user_id, start_date=start_date, db_path=db_path)


def get_today_insights(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Get today's insights.

    Args:
        user_id: User ID

    Returns:
        List of today's insights
    """
    today = date.today().isoformat()
    return search_insights(user_id, start_date=today, db_path=db_path)


def update_insight_status(user_id: int, insight_id: int, new_status: str, db_path: str = None) -> None:
    """
    Update insight status.

    Args:
        user_id: User ID
        insight_id: Insight ID
        new_status: New status ('open', 'confirmed', 'disputed')
    """
    valid_statuses = ['open', 'confirmed', 'disputed']
    if new_status not in valid_statuses:
        raise ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    update_insight(user_id, insight_id, {'status': new_status})
    logger.info(f"Insight status updated: {insight_id} -> {new_status}")


def update_insight_confidence(user_id: int, insight_id: int, confidence_level: str, db_path: str = None) -> None:
    """
    Update insight confidence level.

    Args:
        user_id: User ID
        insight_id: Insight ID
        confidence_level: New confidence ('hypothesis', 'weak', 'moderate', 'strong')
    """
    valid_levels = ['hypothesis', 'weak', 'moderate', 'strong']
    if confidence_level not in valid_levels:
        raise ValidationError(f"Invalid confidence level. Must be one of: {', '.join(valid_levels)}")

    update_insight(user_id, insight_id, {'confidence_level': confidence_level})
    logger.info(f"Insight confidence updated: {insight_id} -> {confidence_level}")


def get_insights_by_category(user_id: int, category: str, db_path: str = None) -> List[Dict]:
    """
    Get insights by category.

    Args:
        user_id: User ID
        category: Category name

    Returns:
        List of insights in category
    """
    return search_insights(user_id, category=category)


def get_insights_by_status(user_id: int, status: str, db_path: str = None) -> List[Dict]:
    """
    Get insights by status.

    Args:
        user_id: User ID
        status: Status ('open', 'confirmed', 'disputed')

    Returns:
        List of insights with status
    """
    return search_insights(user_id, status=status)


def get_strong_insights(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Get strong confidence insights.

    Args:
        user_id: User ID

    Returns:
        List of strong insights
    """
    results = execute_query("""
        SELECT * FROM tv_insights
        WHERE user_id = ? AND confidence_level = 'strong'
        ORDER BY date_observed DESC
    """, (user_id,), db_path)

    return [dict(row) for row in results]


def get_confirmed_insights(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Get confirmed insights.

    Args:
        user_id: User ID

    Returns:
        List of confirmed insights
    """
    results = execute_query("""
        SELECT * FROM tv_insights
        WHERE user_id = ? AND status = 'confirmed'
        ORDER BY date_observed DESC
    """, (user_id,), db_path)

    return [dict(row) for row in results]


def get_insight_categories(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all insight categories used by user.

    Args:
        user_id: User ID

    Returns:
        List of categories
    """
    results = execute_query(
        "SELECT DISTINCT category FROM tv_insights WHERE user_id = ? ORDER BY category",
        (user_id,),
        db_path
    )
    return [row['category'] for row in results]


def get_insight_stats(user_id: int, db_path: str = None) -> Dict:
    """
    Get insight statistics for user.

    Args:
        user_id: User ID

    Returns:
        Stats dict
    """
    total = execute_query(
        "SELECT COUNT(*) as count FROM tv_insights WHERE user_id = ?",
        (user_id,),
        db_path
    )

    by_status = execute_query(
        "SELECT status, COUNT(*) as count FROM tv_insights WHERE user_id = ? GROUP BY status",
        (user_id,),
        db_path
    )

    by_confidence = execute_query(
        "SELECT confidence_level, COUNT(*) as count FROM tv_insights WHERE user_id = ? GROUP BY confidence_level",
        (user_id,),
        db_path
    )

    by_category = execute_query(
        "SELECT category, COUNT(*) as count FROM tv_insights WHERE user_id = ? AND category IS NOT NULL GROUP BY category",
        (user_id,),
        db_path
    )

    return {
        'total': total[0]['count'] if total else 0,
        'by_status': {row['status']: row['count'] for row in by_status} if by_status else {},
        'by_confidence': {row['confidence_level']: row['count'] for row in by_confidence} if by_confidence else {},
        'by_category': {row['category']: row['count'] for row in by_category} if by_category else {}
    }


def export_insights(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Export all user's insights.

    Args:
        user_id: User ID

    Returns:
        List of all insights ready for export
    """
    results = execute_query(
        "SELECT * FROM tv_insights WHERE user_id = ? ORDER BY date_observed DESC",
        (user_id,),
        db_path
    )

    logger.info(f"Exported {len(results)} insights for user {user_id}")
    return [dict(row) for row in results]


def bulk_update_status(user_id: int, insight_ids: List[int], new_status: str, db_path: str = None) -> None:
    """
    Update status for multiple insights.

    Args:
        user_id: User ID
        insight_ids: List of insight IDs
        new_status: New status
    """
    for insight_id in insight_ids:
        try:
            update_insight_status(user_id, insight_id, new_status)
        except Exception as e:
            logger.warning(f"Failed to update insight {insight_id}: {e}")

    logger.info(f"Bulk status updated for {len(insight_ids)} insights")


def bulk_delete_insights(user_id: int, insight_ids: List[int], db_path: str = None) -> None:
    """
    Delete multiple insights.

    Args:
        user_id: User ID
        insight_ids: List of insight IDs
    """
    for insight_id in insight_ids:
        try:
            delete_insight(user_id, insight_id)
        except Exception as e:
            logger.warning(f"Failed to delete insight {insight_id}: {e}")

    logger.info(f"Bulk deleted {len(insight_ids)} insights")
