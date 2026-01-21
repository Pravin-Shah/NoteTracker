"""
Event and calendar management for General App.
CRUD operations for calendar events.
"""

from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from core.db import (
    create_record, update_record, get_record, search_records,
    execute_query, delete_record
)
from core.validators import validate_date
from core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def create_event(user_id: int, event_data: Dict, db_path: str = None) -> int:
    """
    Create calendar event.

    Args:
        user_id: User ID
        event_data: {
            'title': str,
            'description': str (optional),
            'start_date': str (YYYY-MM-DD),
            'start_time': str (HH:MM, optional),
            'end_date': str (YYYY-MM-DD, optional),
            'end_time': str (HH:MM, optional),
            'location': str (optional),
            'is_all_day': int (0/1),
            'category': str ('personal', 'work', 'birthday', 'holiday'),
            'reminder_minutes_before': int (1440 = 1 day, default),
        }

    Returns:
        Event ID

    Raises:
        ValidationError: If validation fails
    """
    if not event_data.get('title') or len(event_data['title']) < 2:
        raise ValidationError("Event title is required (min 2 chars)")

    if not validate_date(event_data.get('start_date', '')):
        raise ValidationError("Invalid start date (YYYY-MM-DD)")

    if event_data.get('end_date') and not validate_date(event_data['end_date']):
        raise ValidationError("Invalid end date (YYYY-MM-DD)")

    event_data['user_id'] = user_id
    event_data.setdefault('is_all_day', 0)
    event_data.setdefault('reminder_minutes_before', 1440)  # 1 day

    event_id = create_record('gen_events', event_data, db_path)
    logger.info(f"Event created: {event_id} by user {user_id}")
    return event_id


def get_event(user_id: int, event_id: int, db_path: str = None) -> Optional[Dict]:
    """
    Get single event.

    Args:
        user_id: User ID (for verification)
        event_id: Event ID

    Returns:
        Event dict or None
    """
    event = get_record('gen_events', event_id, db_path)

    if not event or event['user_id'] != user_id:
        return None

    return dict(event)


def update_event(user_id: int, event_id: int, updates: Dict, db_path: str = None) -> None:
    """
    Update event.

    Args:
        user_id: User ID
        event_id: Event ID
        updates: Fields to update
    """
    event = get_record('gen_events', event_id, db_path)
    if not event or event['user_id'] != user_id:
        raise ValidationError("Event not found")

    update_record('gen_events', event_id, updates, db_path)
    logger.info(f"Event updated: {event_id}")


def delete_event(user_id: int, event_id: int, db_path: str = None) -> None:
    """
    Delete event.

    Args:
        user_id: User ID
        event_id: Event ID
    """
    event = get_record('gen_events', event_id, db_path)
    if not event or event['user_id'] != user_id:
        raise ValidationError("Event not found")

    delete_record('gen_events', event_id, db_path)
    logger.info(f"Event deleted: {event_id}")


def get_events_on_date(user_id: int, event_date: str, db_path: str = None) -> List[Dict]:
    """
    Get all events on a specific date.

    Args:
        user_id: User ID
        event_date: Date (YYYY-MM-DD)

    Returns:
        List of events on that date
    """
    results = execute_query("""
        SELECT * FROM gen_events
        WHERE user_id = ? AND start_date = ?
        ORDER BY start_time ASC
    """, (user_id, event_date), db_path)

    return [dict(row) for row in results]


def get_events_in_range(user_id: int, start_date: str, end_date: str, db_path: str = None) -> List[Dict]:
    """
    Get events in date range.

    Args:
        user_id: User ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of events in range
    """
    results = execute_query("""
        SELECT * FROM gen_events
        WHERE user_id = ? AND start_date >= ? AND start_date <= ?
        ORDER BY start_date ASC, start_time ASC
    """, (user_id, start_date, end_date), db_path)

    return [dict(row) for row in results]


def get_upcoming_events(user_id: int, days: int = 7, db_path: str = None) -> List[Dict]:
    """
    Get upcoming events.

    Args:
        user_id: User ID
        days: Number of days to look ahead

    Returns:
        List of upcoming events
    """
    today = date.today().isoformat()
    future_date = (date.today() + timedelta(days=days)).isoformat()

    return get_events_in_range(user_id, today, future_date, db_path)


def get_today_events(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Get today's events.

    Args:
        user_id: User ID

    Returns:
        List of today's events
    """
    today = date.today().isoformat()
    return get_events_on_date(user_id, today, db_path)


def get_event_categories(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all event categories used by user.

    Args:
        user_id: User ID

    Returns:
        List of categories
    """
    results = execute_query(
        "SELECT DISTINCT category FROM gen_events WHERE user_id = ? AND category IS NOT NULL ORDER BY category",
        (user_id,),
        db_path
    )
    return [row['category'] for row in results]


def get_calendar_data(user_id: int, year: int, month: int, db_path: str = None) -> Dict:
    """
    Get all events for a calendar month.

    Args:
        user_id: User ID
        year: Year
        month: Month (1-12)

    Returns:
        Dict with dates as keys and events as values
    """
    # Get first and last day of month
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    last_day = (next_month - timedelta(days=1)).day
    first_date = date(year, month, 1).isoformat()
    last_date = date(year, month, last_day).isoformat()

    events = get_events_in_range(user_id, first_date, last_date, db_path)

    # Group by date
    calendar_data = {}
    for event in events:
        date_key = event['start_date']
        if date_key not in calendar_data:
            calendar_data[date_key] = []
        calendar_data[date_key].append(event)

    return calendar_data


def get_event_stats(user_id: int, db_path: str = None) -> Dict:
    """
    Get event statistics for user.

    Args:
        user_id: User ID

    Returns:
        Stats dict
    """
    today = date.today().isoformat()

    total = execute_query(
        "SELECT COUNT(*) as count FROM gen_events WHERE user_id = ?",
        (user_id,),
        db_path
    )

    upcoming = execute_query(
        "SELECT COUNT(*) as count FROM gen_events WHERE user_id = ? AND start_date >= ?",
        (user_id, today),
        db_path
    )

    past = execute_query(
        "SELECT COUNT(*) as count FROM gen_events WHERE user_id = ? AND start_date < ?",
        (user_id, today),
        db_path
    )

    by_category = execute_query(
        "SELECT category, COUNT(*) as count FROM gen_events WHERE user_id = ? GROUP BY category",
        (user_id,),
        db_path
    )

    return {
        'total': total[0]['count'] if total else 0,
        'upcoming': upcoming[0]['count'] if upcoming else 0,
        'past': past[0]['count'] if past else 0,
        'by_category': {row['category']: row['count'] for row in by_category} if by_category else {}
    }


def search_events(
    user_id: int,
    query: str = "",
    category: str = None,
    start_date: str = None,
    end_date: str = None,
    db_path: str = None) -> List[Dict]:
    """
    Search events.

    Args:
        user_id: User ID
        query: Search text
        category: Filter by category
        start_date: Start date filter
        end_date: End date filter

    Returns:
        List of matching events
    """
    sql = "SELECT * FROM gen_events WHERE user_id = ?"
    params = [user_id]

    if query:
        sql += " AND (title LIKE ? OR description LIKE ? OR location LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

    if category:
        sql += " AND category = ?"
        params.append(category)

    if start_date:
        sql += " AND start_date >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND start_date <= ?"
        params.append(end_date)

    sql += " ORDER BY start_date ASC, start_time ASC"

    results = execute_query(sql, tuple(params), db_path)
    return [dict(row) for row in results]


def get_conflicting_events(user_id: int, event_id: int, db_path: str = None) -> List[Dict]:
    """
    Get events that conflict with given event.

    Args:
        user_id: User ID
        event_id: Event ID to check

    Returns:
        List of conflicting events
    """
    event = get_event(user_id, event_id, db_path)
    if not event:
        return []

    start_date = event['start_date']
    end_date = event['end_date'] or event['start_date']

    results = execute_query("""
        SELECT * FROM gen_events
        WHERE user_id = ? AND id != ?
        AND (
            (start_date = ? OR (start_date >= ? AND start_date <= ?))
            OR (start_date <= ? AND (end_date IS NULL OR end_date >= ?))
        )
        ORDER BY start_date ASC
    """, (user_id, event_id, start_date, start_date, end_date, end_date, start_date), db_path)

    return [dict(row) for row in results]


def export_events(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Export all user's events.

    Args:
        user_id: User ID

    Returns:
        List of all events ready for export
    """
    results = execute_query(
        "SELECT * FROM gen_events WHERE user_id = ? ORDER BY start_date ASC",
        (user_id,),
        db_path
    )

    logger.info(f"Exported {len(results)} events for user {user_id}")
    return [dict(row) for row in results]
