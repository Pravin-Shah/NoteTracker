"""
Notifications: Email, Telegram, In-app.
"""

import smtplib
import os
from typing import List, Dict
from email.mime.text import MIMEText
from core.db import create_record, execute_query, update_record
from core.config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, TELEGRAM_TOKEN
from core.exceptions import NotificationError
import logging

logger = logging.getLogger(__name__)


def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Send email via SMTP.

    Args:
        recipient: Email address
        subject: Email subject
        body: Email body (HTML or plain text)

    Returns:
        True if sent, False otherwise
    """
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.warning("Email credentials not configured")
        return False

    try:
        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return False


def send_telegram(chat_id: str, message: str) -> bool:
    """
    Send message via Telegram.

    Args:
        chat_id: Telegram chat ID
        message: Message text

    Returns:
        True if sent, False otherwise
    """
    if not TELEGRAM_TOKEN:
        logger.warning("Telegram token not configured")
        return False

    try:
        import requests

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)

        if response.status_code == 200:
            logger.info(f"Telegram message sent to {chat_id}")
            return True
        else:
            logger.error(f"Telegram error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def create_in_app_notification(
    user_id: int,
    app_name: str,
    title: str,
    message: str,
    notification_type: str = 'alert'
) -> int:
    """
    Create in-app notification (stored in DB).

    Args:
        user_id: User ID
        app_name: 'tradevault' or 'general'
        title: Notification title
        message: Notification message
        notification_type: Type of notification

    Returns:
        Notification ID
    """
    return create_record('notifications', {
        'user_id': user_id,
        'app_name': app_name,
        'notification_type': notification_type,
        'title': title,
        'message': message,
        'is_read': 0
    })


def get_unread_notifications(user_id: int, limit: int = 50) -> List[Dict]:
    """
    Get unread notifications for user.

    Args:
        user_id: User ID
        limit: Max results

    Returns:
        List of notifications
    """
    results = execute_query(
        """SELECT * FROM notifications
           WHERE user_id = ? AND is_read = 0
           ORDER BY created_date DESC LIMIT ?""",
        (user_id, limit)
    )
    return [dict(row) for row in results]


def get_all_notifications(user_id: int, limit: int = 100) -> List[Dict]:
    """
    Get all notifications for user.

    Args:
        user_id: User ID
        limit: Max results

    Returns:
        List of notifications
    """
    results = execute_query(
        """SELECT * FROM notifications
           WHERE user_id = ?
           ORDER BY created_date DESC LIMIT ?""",
        (user_id, limit)
    )
    return [dict(row) for row in results]


def mark_notification_read(notification_id: int) -> None:
    """
    Mark notification as read.

    Args:
        notification_id: Notification ID
    """
    update_record('notifications', notification_id, {'is_read': 1})


def mark_all_notifications_read(user_id: int) -> None:
    """
    Mark all notifications as read for user.

    Args:
        user_id: User ID
    """
    try:
        from core.db import execute_update
        execute_update(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
            (user_id,)
        )
        logger.info(f"All notifications marked as read for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to mark notifications as read: {e}")


def delete_notification(notification_id: int) -> None:
    """
    Delete notification.

    Args:
        notification_id: Notification ID
    """
    try:
        from core.db import execute_update
        execute_update(
            "DELETE FROM notifications WHERE id = ?",
            (notification_id,)
        )
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")


def send_multi_channel_notification(
    user_id: int,
    app_name: str,
    title: str,
    message: str,
    email: str = None,
    telegram_id: str = None
) -> Dict:
    """
    Send notification via all available channels.

    Args:
        user_id: User ID
        app_name: App name
        title: Notification title
        message: Notification message
        email: Email address (optional)
        telegram_id: Telegram chat ID (optional)

    Returns:
        Dict with send status for each channel
    """
    results = {
        'in_app': False,
        'email': False,
        'telegram': False
    }

    # Always create in-app notification
    try:
        create_in_app_notification(user_id, app_name, title, message)
        results['in_app'] = True
    except Exception as e:
        logger.error(f"Failed to create in-app notification: {e}")

    # Send email if provided
    if email:
        results['email'] = send_email(email, title, message)

    # Send Telegram if provided
    if telegram_id:
        results['telegram'] = send_telegram(telegram_id, f"<b>{title}</b>\n{message}")

    return results


def get_notification_stats(user_id: int) -> Dict:
    """
    Get notification statistics for user.

    Args:
        user_id: User ID

    Returns:
        Stats dict
    """
    all_notifs = execute_query(
        "SELECT COUNT(*) as total FROM notifications WHERE user_id = ?",
        (user_id,)
    )
    unread = execute_query(
        "SELECT COUNT(*) as unread FROM notifications WHERE user_id = ? AND is_read = 0",
        (user_id,)
    )

    return {
        'total': all_notifs[0]['total'] if all_notifs else 0,
        'unread': unread[0]['unread'] if unread else 0,
        'read': (all_notifs[0]['total'] - unread[0]['unread']) if (all_notifs and unread) else 0
    }
