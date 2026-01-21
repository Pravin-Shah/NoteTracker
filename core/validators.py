"""
Input validation rules for all data types.
"""

import re
from datetime import datetime
from typing import Tuple


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_date(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_time(time_str: str) -> bool:
    """Validate time format (HH:MM)."""
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False


def validate_priority(priority: int) -> bool:
    """Validate priority (1-5)."""
    return isinstance(priority, int) and 1 <= priority <= 5


def validate_edge_title(title: str) -> bool:
    """Validate edge title (5-100 chars)."""
    return isinstance(title, str) and 5 <= len(title) <= 100


def validate_task_title(title: str) -> bool:
    """Validate task title (3-200 chars)."""
    return isinstance(title, str) and 3 <= len(title) <= 200


def validate_note_title(title: str) -> bool:
    """Validate note title (3-100 chars)."""
    return isinstance(title, str) and 3 <= len(title) <= 100


def validate_importance(importance: int) -> bool:
    """Validate importance (1-5)."""
    return isinstance(importance, int) and 1 <= importance <= 5


def validate_confidence_grade(grade: str) -> bool:
    """Validate confidence grade (A, B, or C)."""
    return grade in ['A', 'B', 'C']


def validate_file_size(file_size: int, max_size: int = 10_485_760) -> bool:
    """Validate file size (default 10MB max)."""
    return file_size <= max_size
