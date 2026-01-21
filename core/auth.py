"""
User authentication, registration, and session management.
Single login system for all apps.
"""

import hashlib
from typing import Optional, Dict, Tuple
from core.db import create_record, execute_query, get_record, update_record
from core.validators import validate_email
from core.exceptions import AuthenticationError, ValidationError
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hash password with SHA256.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format.

    Args:
        username: Username to validate

    Returns:
        (is_valid, error_message)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    if not username.replace('_', '').replace('-', '').isalnum():
        return False, "Username can only contain letters, numbers, - and _"
    return True, ""


def register_user(
    username: str,
    password: str,
    email: str = None,
    telegram_id: str = None,
    db_path: str = None
) -> Dict:
    """
    Register new user.

    Args:
        username: Unique username
        password: User password
        email: Email address (optional)
        telegram_id: Telegram chat ID (optional)
        db_path: Path to database (for testing)

    Returns:
        User dict if successful

    Raises:
        ValidationError: If validation fails
        AuthenticationError: If user already exists
    """
    # Validate username
    is_valid, error = validate_username(username)
    if not is_valid:
        logger.warning(f"Invalid username: {username} - {error}")
        raise ValidationError(error)

    # Validate password
    is_valid, error = validate_password(password)
    if not is_valid:
        logger.warning(f"Invalid password for user {username}")
        raise ValidationError(error)

    # Validate email if provided
    if email and not validate_email(email):
        logger.warning(f"Invalid email: {email}")
        raise ValidationError("Invalid email format")

    # Check if user exists
    existing = execute_query("SELECT id FROM users WHERE username = ?", (username,), db_path)
    if existing:
        logger.warning(f"User already exists: {username}")
        raise AuthenticationError("User already exists")

    # Create user
    password_hash = hash_password(password)
    user_id = create_record('users', {
        'username': username,
        'password_hash': password_hash,
        'email': email,
        'telegram_id': telegram_id
    }, db_path)

    logger.info(f"User registered: {username} (ID: {user_id})")
    return {
        'id': user_id,
        'username': username,
        'email': email,
        'telegram_id': telegram_id
    }


def login_user(username: str, password: str) -> Dict:
    """
    Authenticate user.

    Args:
        username: Username
        password: Password

    Returns:
        User dict if successful

    Raises:
        AuthenticationError: If authentication fails
    """
    results = execute_query("SELECT * FROM users WHERE username = ?", (username,))

    if not results:
        logger.warning(f"Login failed: user not found - {username}")
        raise AuthenticationError("Invalid username or password")

    user = results[0]

    # Check if user is active
    if not user['is_active']:
        logger.warning(f"Login failed: user inactive - {username}")
        raise AuthenticationError("User account is inactive")

    # Check password
    password_hash = hash_password(password)

    if user['password_hash'] != password_hash:
        logger.warning(f"Login failed: wrong password - {username}")
        raise AuthenticationError("Invalid username or password")

    logger.info(f"User logged in: {username}")
    return dict(user)


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Get user by ID.

    Args:
        user_id: User ID

    Returns:
        User dict or None if not found
    """
    return get_record('users', user_id)


def get_user_by_username(username: str) -> Optional[Dict]:
    """
    Get user by username.

    Args:
        username: Username

    Returns:
        User dict or None if not found
    """
    results = execute_query("SELECT * FROM users WHERE username = ?", (username,))
    return results[0] if results else None


def update_user_email(user_id: int, email: str) -> None:
    """
    Update user email address.

    Args:
        user_id: User ID
        email: New email address

    Raises:
        ValidationError: If email is invalid
    """
    if not validate_email(email):
        raise ValidationError("Invalid email format")

    update_record('users', user_id, {'email': email})
    logger.info(f"Email updated for user {user_id}")


def update_user_telegram_id(user_id: int, telegram_id: str) -> None:
    """
    Update user Telegram ID.

    Args:
        user_id: User ID
        telegram_id: Telegram chat ID
    """
    update_record('users', user_id, {'telegram_id': telegram_id})
    logger.info(f"Telegram ID updated for user {user_id}")


def change_password(user_id: int, old_password: str, new_password: str) -> None:
    """
    Change user password.

    Args:
        user_id: User ID
        old_password: Current password
        new_password: New password

    Raises:
        AuthenticationError: If old password is incorrect
        ValidationError: If new password is invalid
    """
    user = get_user_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")

    # Verify old password
    old_hash = hash_password(old_password)
    if user['password_hash'] != old_hash:
        logger.warning(f"Password change failed: wrong old password - user {user_id}")
        raise AuthenticationError("Current password is incorrect")

    # Validate new password
    is_valid, error = validate_password(new_password)
    if not is_valid:
        raise ValidationError(error)

    # Update password
    new_hash = hash_password(new_password)
    update_record('users', user_id, {'password_hash': new_hash})
    logger.info(f"Password changed for user {user_id}")


def deactivate_user(user_id: int) -> None:
    """
    Deactivate user account.

    Args:
        user_id: User ID
    """
    update_record('users', user_id, {'is_active': 0})
    logger.info(f"User deactivated: {user_id}")


def reactivate_user(user_id: int) -> None:
    """
    Reactivate user account.

    Args:
        user_id: User ID
    """
    update_record('users', user_id, {'is_active': 1})
    logger.info(f"User reactivated: {user_id}")


def list_users(limit: int = 100) -> list:
    """
    List all users (admin function).

    Args:
        limit: Max results

    Returns:
        List of user dicts
    """
    results = execute_query(
        "SELECT id, username, email, created_date, is_active FROM users LIMIT ?",
        (limit,)
    )
    return [dict(row) for row in results]
