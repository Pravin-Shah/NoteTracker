"""
Task reminder scheduling and notifications.
Uses APScheduler for scheduled reminders.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from core.db import execute_query, execute_update, update_record, get_record
from core.notifications import send_email, send_telegram, create_in_app_notification
import logging

logger = logging.getLogger(__name__)


class ReminderEngine:
    """Handles task reminder scheduling and sending."""

    def __init__(self):
        """Initialize reminder engine."""
        self.scheduler = None
        self.running = False

    def start(self):
        """
        Start the reminder scheduler.
        Should be called once at app startup.
        """
        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            if self.running:
                logger.warning("Reminder engine already running")
                return

            self.scheduler = BackgroundScheduler()
            # Check for due reminders every minute
            self.scheduler.add_job(
                self.check_reminders,
                'interval',
                minutes=1,
                id='check_reminders',
                replace_existing=True
            )
            self.scheduler.start()
            self.running = True
            logger.info("Reminder engine started")
        except ImportError:
            logger.error("APScheduler not installed. Install with: pip install apscheduler")
        except Exception as e:
            logger.error(f"Failed to start reminder engine: {e}")

    def stop(self):
        """
        Stop the reminder scheduler.
        Call at app shutdown.
        """
        if self.scheduler and self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("Reminder engine stopped")

    def check_reminders(self, db_path: str = None):
        """
        Check and send due reminders.
        Called every minute by scheduler.
        """
        try:
            # Get all unsent reminders
            reminders = execute_query("""
                SELECT r.*, t.user_id, t.title, t.due_date, t.due_time,
                       u.email, u.telegram_id
                FROM gen_task_reminders r
                JOIN gen_tasks t ON r.task_id = t.id
                JOIN users u ON t.user_id = u.id
                WHERE r.is_sent = 0 AND t.archived = 0
            """, (), db_path)

            current_time = datetime.now()
            current_date = current_time.date().isoformat()
            current_hour = current_time.hour

            for reminder in reminders:
                should_send = False

                # Check if reminder is due
                if reminder['reminder_type'] == 'on-due-date':
                    # Send on due date at midnight (or specific time if set)
                    if reminder['due_date'] == current_date:
                        should_send = True

                elif reminder['reminder_type'] == 'days-before':
                    # Send N days before due date
                    days_before = reminder['reminder_value']
                    due = datetime.fromisoformat(f"{reminder['due_date']}T00:00:00")
                    send_date = (due - timedelta(days=days_before)).date().isoformat()

                    if send_date == current_date:
                        should_send = True

                elif reminder['reminder_type'] == 'specific-time':
                    # Send at specific time of day
                    if reminder['reminder_time']:
                        reminder_hour = int(reminder['reminder_time'].split(':')[0])
                        if current_hour == reminder_hour:
                            should_send = True

                if should_send:
                    self.send_reminder(reminder)

        except Exception as e:
            logger.error(f"Error checking reminders: {e}")

    def send_reminder(self, reminder: Dict, db_path: str = None) -> None:
        """
        Send a single reminder via all channels.

        Args:
            reminder: Reminder dict from database
            db_path: Path to database (for testing)
        """
        try:
            message = f"Task Reminder: {reminder['title']}"

            # In-app notification (always)
            create_in_app_notification(
                reminder['user_id'],
                'general',
                'Task Reminder',
                message,
                'reminder'
            )

            # Email
            if reminder['email']:
                email_body = f"""
                <h2>Task Reminder</h2>
                <p><strong>Task:</strong> {reminder['title']}</p>
                <p><strong>Due:</strong> {reminder['due_date']}</p>
                <p>Please log in to NoteTracker to manage this task.</p>
                """
                send_email(reminder['email'], "Task Reminder", email_body)

            # Telegram
            if reminder['telegram_id']:
                telegram_msg = f"🔔 <b>Task Reminder</b>\n{reminder['title']}"
                send_telegram(reminder['telegram_id'], telegram_msg)

            # Mark as sent
            update_record('gen_task_reminders', reminder['id'], {
                'is_sent': 1,
                'sent_date': datetime.now().isoformat()
            }, db_path)

            logger.info(f"Reminder sent for task {reminder['task_id']} to user {reminder['user_id']}")

        except Exception as e:
            logger.error(f"Failed to send reminder {reminder['id']}: {e}")

    def send_immediate_reminder(self, user_id: int, task_id: int, db_path: str = None) -> bool:
        """
        Send reminder immediately (for testing or manual trigger).

        Args:
            user_id: User ID
            task_id: Task ID
            db_path: Path to database (for testing)

        Returns:
            True if sent successfully
        """
        try:
            reminder_data = execute_query("""
                SELECT r.*, t.user_id, t.title, t.due_date,
                       u.email, u.telegram_id
                FROM gen_task_reminders r
                JOIN gen_tasks t ON r.task_id = t.id
                JOIN users u ON t.user_id = u.id
                WHERE t.id = ? AND t.user_id = ? AND r.is_sent = 0
                LIMIT 1
            """, (task_id, user_id), db_path)

            if reminder_data:
                self.send_reminder(reminder_data[0], db_path)
                return True
            else:
                logger.warning(f"No unsent reminder found for task {task_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to send immediate reminder: {e}")
            return False


# Global instance
_reminder_engine = ReminderEngine()


def get_reminder_engine() -> ReminderEngine:
    """Get global reminder engine instance."""
    return _reminder_engine


def start_reminder_scheduler():
    """Start the reminder scheduler."""
    _reminder_engine.start()


def stop_reminder_scheduler():
    """Stop the reminder scheduler."""
    _reminder_engine.stop()


def is_reminder_engine_running() -> bool:
    """Check if reminder engine is running."""
    return _reminder_engine.running


def get_pending_reminders(user_id: int, db_path: str = None) -> List[Dict]:
    """
    Get pending (unsent) reminders for user.

    Args:
        user_id: User ID
        db_path: Path to database (for testing)

    Returns:
        List of pending reminders
    """
    results = execute_query("""
        SELECT r.*, t.title, t.due_date
        FROM gen_task_reminders r
        JOIN gen_tasks t ON r.task_id = t.id
        WHERE t.user_id = ? AND r.is_sent = 0
        ORDER BY t.due_date ASC
    """, (user_id,), db_path)

    return [dict(row) for row in results]


def get_sent_reminders(user_id: int, limit: int = 100, db_path: str = None) -> List[Dict]:
    """
    Get sent reminders for user.

    Args:
        user_id: User ID
        limit: Max results
        db_path: Path to database (for testing)

    Returns:
        List of sent reminders
    """
    results = execute_query("""
        SELECT r.*, t.title, t.due_date
        FROM gen_task_reminders r
        JOIN gen_tasks t ON r.task_id = t.id
        WHERE t.user_id = ? AND r.is_sent = 1
        ORDER BY r.sent_date DESC
        LIMIT ?
    """, (user_id, limit), db_path)

    return [dict(row) for row in results]


def delete_reminder(reminder_id: int, db_path: str = None) -> None:
    """
    Delete reminder.

    Args:
        reminder_id: Reminder ID
        db_path: Path to database (for testing)
    """
    from core.db import execute_update
    execute_update(
        "DELETE FROM gen_task_reminders WHERE id = ?",
        (reminder_id,),
        db_path
    )
    logger.info(f"Reminder deleted: {reminder_id}")


def resend_reminder(reminder_id: int, db_path: str = None) -> bool:
    """
    Resend a reminder (mark as not sent and force check).

    Args:
        reminder_id: Reminder ID
        db_path: Path to database (for testing)

    Returns:
        True if resent successfully
    """
    try:
        update_record('gen_task_reminders', reminder_id, {'is_sent': 0}, db_path)

        # Get reminder and send immediately
        reminder = get_record('gen_task_reminders', reminder_id, db_path)
        if reminder:
            # Get full reminder data
            full_reminder = execute_query("""
                SELECT r.*, t.user_id, t.title, t.due_date,
                       u.email, u.telegram_id
                FROM gen_task_reminders r
                JOIN gen_tasks t ON r.task_id = t.id
                JOIN users u ON t.user_id = u.id
                WHERE r.id = ?
            """, (reminder_id,), db_path)

            if full_reminder:
                _reminder_engine.send_reminder(full_reminder[0], db_path)
                return True

        return False

    except Exception as e:
        logger.error(f"Failed to resend reminder {reminder_id}: {e}")
        return False


def get_reminder_stats(user_id: int, db_path: str = None) -> Dict:
    """
    Get reminder statistics for user.

    Args:
        user_id: User ID
        db_path: Path to database (for testing)

    Returns:
        Stats dict
    """
    pending = execute_query(
        """SELECT COUNT(*) as count FROM gen_task_reminders r
           JOIN gen_tasks t ON r.task_id = t.id
           WHERE t.user_id = ? AND r.is_sent = 0""",
        (user_id,),
        db_path
    )

    sent = execute_query(
        """SELECT COUNT(*) as count FROM gen_task_reminders r
           JOIN gen_tasks t ON r.task_id = t.id
           WHERE t.user_id = ? AND r.is_sent = 1""",
        (user_id,),
        db_path
    )

    return {
        'pending': pending[0]['count'] if pending else 0,
        'sent': sent[0]['count'] if sent else 0,
        'engine_running': is_reminder_engine_running()
    }
