"""
Task-specific database operations for General App.
CRUD operations, reminders, recurring tasks, and management.
"""

from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from core.db import (
    create_record, update_record, get_record, search_records,
    execute_query, execute_update, delete_record
)
from core.validators import validate_task_title, validate_priority, validate_date
from core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def create_task(user_id: int, task_data: Dict, db_path: str = None) -> int:
    """
    Create new task.

    Args:
        user_id: User ID
        task_data: {
            'title': str (3-200 chars),
            'description': str (optional),
            'category': str ('personal', 'work', 'financial', 'health'),
            'priority': int (1-5),
            'due_date': str (YYYY-MM-DD, optional),
            'due_time': str (HH:MM, optional),
            'is_recurring': int (0/1),
            'recurrence_pattern': str ('daily', 'weekly', 'monthly'),
            'estimated_hours': float (optional),
        }

    Returns:
        Task ID

    Raises:
        ValidationError: If validation fails
    """
    if not validate_task_title(task_data.get('title', '')):
        raise ValidationError("Invalid task title (3-200 chars)")

    if not validate_priority(task_data.get('priority', 3)):
        raise ValidationError("Invalid priority (1-5)")

    if task_data.get('due_date') and not validate_date(task_data['due_date']):
        raise ValidationError("Invalid date (YYYY-MM-DD)")

    task_data['user_id'] = user_id
    task_data.setdefault('status', 'pending')
    task_data.setdefault('priority', 3)
    task_data.setdefault('is_recurring', 0)

    task_id = create_record('gen_tasks', task_data, db_path)
    logger.info(f"Task created: {task_id} by user {user_id}")
    return task_id


def get_task(user_id: int, task_id: int, db_path: str = None) -> Optional[Dict]:
    """
    Get single task with all details.

    Args:
        user_id: User ID (for verification)
        task_id: Task ID

    Returns:
        Task dict with tags, reminders, checklist, history
    """
    task = get_record('gen_tasks', task_id, db_path)

    if not task or task['user_id'] != user_id:
        return None

    task = dict(task)

    # Get tags
    tags = execute_query(
        "SELECT tag FROM gen_task_tags WHERE task_id = ?",
        (task_id,),
        db_path
    )
    task['tags'] = [t['tag'] for t in tags]

    # Get reminders
    reminders = execute_query(
        "SELECT * FROM gen_task_reminders WHERE task_id = ? ORDER BY reminder_time",
        (task_id,),
        db_path
    )
    task['reminders'] = [dict(r) for r in reminders]

    # Get checklist
    checklist = execute_query(
        "SELECT * FROM gen_task_checklist WHERE task_id = ? ORDER BY id",
        (task_id,),
        db_path
    )
    task['checklist'] = [dict(c) for c in checklist]

    # Get parent task if exists
    if task['parent_task_id']:
        parent = get_record('gen_tasks', task['parent_task_id'], db_path)
        task['parent_task'] = dict(parent) if parent else None

    return task


def update_task(user_id: int, task_id: int, updates: Dict, db_path: str = None) -> None:
    """
    Update task.

    Args:
        user_id: User ID (for verification)
        task_id: Task ID
        updates: Fields to update
    """
    task = get_record('gen_tasks', task_id, db_path)
    if not task or task['user_id'] != user_id:
        raise ValidationError("Task not found")

    if 'title' in updates and not validate_task_title(updates['title']):
        raise ValidationError("Invalid task title (3-200 chars)")

    if 'priority' in updates and not validate_priority(updates['priority']):
        raise ValidationError("Invalid priority (1-5)")

    if 'due_date' in updates and updates['due_date'] and not validate_date(updates['due_date']):
        raise ValidationError("Invalid date (YYYY-MM-DD)")

    update_record('gen_tasks', task_id, updates, db_path)
    logger.info(f"Task updated: {task_id}")


def complete_task(user_id: int, task_id: int, db_path: str = None) -> None:
    """
    Mark task as completed.

    Args:
        user_id: User ID
        task_id: Task ID
    """
    task = get_record('gen_tasks', task_id, db_path)
    if not task or task['user_id'] != user_id:
        raise ValidationError("Task not found")

    update_record('gen_tasks', task_id, {
        'status': 'completed',
        'completed_date': datetime.now().isoformat()
    }, db_path)

    # Log action
    create_record('gen_task_history', {
        'task_id': task_id,
        'action': 'completed'
    }, db_path)

    logger.info(f"Task completed: {task_id}")


def start_task(user_id: int, task_id: int, db_path: str = None) -> None:
    """
    Mark task as in-progress.

    Args:
        user_id: User ID
        task_id: Task ID
    """
    task = get_record('gen_tasks', task_id, db_path)
    if not task or task['user_id'] != user_id:
        raise ValidationError("Task not found")

    update_record('gen_tasks', task_id, {'status': 'in-progress'}, db_path)

    create_record('gen_task_history', {
        'task_id': task_id,
        'action': 'started'
    }, db_path)

    logger.info(f"Task started: {task_id}")


def delete_task(user_id: int, task_id: int, db_path: str = None) -> None:
    """
    Delete task (soft delete - archives).

    Args:
        user_id: User ID
        task_id: Task ID
    """
    task = get_record('gen_tasks', task_id, db_path)
    if not task or task['user_id'] != user_id:
        raise ValidationError("Task not found")

    delete_record('gen_tasks', task_id, db_path)
    logger.info(f"Task deleted: {task_id}")


def search_tasks(
    user_id: int,
    query: str = "",
    status: str = None,
    priority: int = None,
    category: str = None,
    due_date: str = None,
    archived: bool = False,
    limit: int = 100, db_path: str = None) -> List[Dict]:
    """
    Search tasks by text and filters.

    Args:
        user_id: User ID
        query: Search text
        status: Filter by status ('pending', 'in-progress', 'completed', 'cancelled')
        priority: Filter by priority (1-5)
        category: Filter by category
        due_date: Filter by due date (YYYY-MM-DD)
        archived: Include archived
        limit: Max results

    Returns:
        List of matching tasks
    """
    sql = "SELECT * FROM gen_tasks WHERE user_id = ?"
    params = [user_id]

    if query:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])

    if status:
        sql += " AND status = ?"
        params.append(status)

    if priority:
        sql += " AND priority = ?"
        params.append(priority)

    if category:
        sql += " AND category = ?"
        params.append(category)

    if due_date:
        sql += " AND due_date = ?"
        params.append(due_date)

    if not archived:
        sql += " AND archived = 0"

    sql += " ORDER BY priority DESC, due_date ASC, created_date DESC LIMIT ?"
    params.append(limit)

    results = execute_query(sql, tuple(params), db_path)
    tasks = [dict(row) for row in results]

    # Add tags
    for task in tasks:
        tags = execute_query(
            "SELECT tag FROM gen_task_tags WHERE task_id = ?",
            (task['id'],),
            db_path
        )
        task['tags'] = [t['tag'] for t in tags]

    return tasks


def get_tasks_due_today(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Get all tasks due today.

    Args:
        user_id: User ID

    Returns:
        List of tasks due today
    """
    today = date.today().isoformat()
    return search_tasks(user_id, due_date=today, status='pending', db_path=db_path)


def get_overdue_tasks(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Get overdue tasks.

    Args:
        user_id: User ID

    Returns:
        List of overdue tasks
    """
    today = date.today().isoformat()

    results = execute_query(
        """SELECT * FROM gen_tasks
           WHERE user_id = ? AND due_date < ? AND status != 'completed' AND archived = 0
           ORDER BY due_date ASC, priority DESC""",
        (user_id, today),
        db_path
    )

    tasks = [dict(row) for row in results]

    # Add tags
    for task in tasks:
        tags = execute_query(
            "SELECT tag FROM gen_task_tags WHERE task_id = ?",
            (task['id'],),
            db_path
        )
        task['tags'] = [t['tag'] for t in tags]

    return tasks


def get_upcoming_tasks(user_id: int, days: int = 7, db_path: str = None) -> List[Dict]:
    """
    Get tasks due in next N days.

    Args:
        user_id: User ID
        days: Number of days

    Returns:
        List of upcoming tasks
    """
    today = date.today()
    future_date = (today + timedelta(days=days)).isoformat()

    results = execute_query(
        """SELECT * FROM gen_tasks
           WHERE user_id = ? AND due_date >= ? AND due_date <= ? AND status != 'completed' AND archived = 0
           ORDER BY due_date ASC, priority DESC""",
        (user_id, today.isoformat(), future_date),
        db_path
    )

    tasks = [dict(row) for row in results]

    # Add tags
    for task in tasks:
        tags = execute_query(
            "SELECT tag FROM gen_task_tags WHERE task_id = ?",
            (task['id'],),
            db_path
        )
        task['tags'] = [t['tag'] for t in tags]

    return tasks


def add_task_tag(task_id: int, tag: str, db_path: str = None) -> None:
    """
    Add tag to task.

    Args:
        task_id: Task ID
        tag: Tag name
    """
    try:
        create_record('gen_task_tags', {
            'task_id': task_id,
            'tag': tag.lower()
        }, db_path)
        logger.info(f"Tag added to task {task_id}: {tag}")
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            logger.debug(f"Tag already exists on task {task_id}: {tag}")
        else:
            raise


def create_task_reminder(
    task_id: int,
    reminder_type: str,
    reminder_value: int = None,
    reminder_time: str = None, db_path: str = None) -> int:
    """
    Create reminder for task.

    Args:
        task_id: Task ID
        reminder_type: 'on-due-date', 'days-before', 'specific-time'
        reminder_value: Days before (e.g., 3) or hour (e.g., 9)
        reminder_time: Time in HH:MM format

    Returns:
        Reminder ID
    """
    reminder_id = create_record('gen_task_reminders', {
        'task_id': task_id,
        'reminder_type': reminder_type,
        'reminder_value': reminder_value,
        'reminder_time': reminder_time,
        'is_sent': 0
    }, db_path)

    logger.info(f"Reminder created for task {task_id}")
    return reminder_id


def add_task_checklist(task_id: int, items: List[str], db_path: str = None) -> None:
    """
    Add checklist items to task.

    Args:
        task_id: Task ID
        items: List of checklist items
    """
    for item in items:
        create_record('gen_task_checklist', {
            'task_id': task_id,
            'item': item,
            'is_completed': 0
        }, db_path)

    logger.info(f"Added {len(items)} checklist items to task {task_id}")


def complete_checklist_item(item_id: int, db_path: str = None) -> None:
    """
    Mark checklist item as complete.

    Args:
        item_id: Checklist item ID
    """
    update_record('gen_task_checklist', item_id, {'is_completed': 1}, db_path)


def get_task_categories(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all categories used in user's tasks.

    Args:
        user_id: User ID

    Returns:
        List of categories
    """
    results = execute_query(
        "SELECT DISTINCT category FROM gen_tasks WHERE user_id = ? AND category IS NOT NULL ORDER BY category",
        (user_id,),
        db_path
    )
    return [row['category'] for row in results]


def get_task_tags(user_id: int, db_path: str = None) -> List[str]:
    """
    Get all tags used in user's tasks.

    Args:
        user_id: User ID

    Returns:
        List of tags
    """
    results = execute_query(
        """SELECT DISTINCT tag FROM gen_task_tags
           WHERE task_id IN (SELECT id FROM gen_tasks WHERE user_id = ?)
           ORDER BY tag""",
        (user_id,),
        db_path
    )
    return [row['tag'] for row in results]


def get_task_stats(user_id: int, db_path: str = None) -> Dict:
    """
    Get task statistics for user.

    Args:
        user_id: User ID

    Returns:
        Stats dict
    """
    total = execute_query(
        "SELECT COUNT(*) as count FROM gen_tasks WHERE user_id = ? AND archived = 0",
        (user_id,),
        db_path
    )

    pending = execute_query(
        "SELECT COUNT(*) as count FROM gen_tasks WHERE user_id = ? AND status = 'pending' AND archived = 0",
        (user_id,),
        db_path
    )

    in_progress = execute_query(
        "SELECT COUNT(*) as count FROM gen_tasks WHERE user_id = ? AND status = 'in-progress' AND archived = 0",
        (user_id,),
        db_path
    )

    completed = execute_query(
        "SELECT COUNT(*) as count FROM gen_tasks WHERE user_id = ? AND status = 'completed'",
        (user_id,),
        db_path
    )

    overdue = len(get_overdue_tasks(user_id, db_path))

    return {
        'total': total[0]['count'] if total else 0,
        'pending': pending[0]['count'] if pending else 0,
        'in_progress': in_progress[0]['count'] if in_progress else 0,
        'completed': completed[0]['count'] if completed else 0,
        'overdue': overdue
    }


def log_task_action(task_id: int, action: str, notes: str = None, db_path: str = None) -> None:
    """
    Log task action for history.

    Args:
        task_id: Task ID
        action: Action performed
        notes: Optional notes
    """
    create_record('gen_task_history', {
        'task_id': task_id,
        'action': action,
        'notes': notes
    }, db_path)
