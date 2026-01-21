"""
Unit tests for core/auth.py - Authentication
"""

import pytest
from pathlib import Path
from core.db import init_database, get_connection
from core.auth import (
    hash_password, validate_password, validate_username,
    register_user, login_user, get_user_by_id, get_user_by_username,
    change_password, deactivate_user, reactivate_user
)
from core.exceptions import AuthenticationError, ValidationError


@pytest.fixture
def test_db(tmp_path):
    """Create a fresh test database."""
    db_path = str(tmp_path / "test.db")
    init_database(db_path)

    # Override db path in auth module for testing
    import core.auth
    import core.db
    original_create = core.db.create_record
    original_execute_query = core.db.execute_query
    original_execute_update = core.db.execute_update
    original_update_record = core.db.update_record

    def patched_create(*args, **kwargs):
        return original_create(*args, db_path=db_path, **kwargs)

    def patched_query(*args, **kwargs):
        return original_execute_query(*args, db_path=db_path, **kwargs)

    def patched_update(*args, **kwargs):
        return original_execute_update(*args, db_path=db_path, **kwargs)

    def patched_update_rec(*args, **kwargs):
        return original_update_record(*args, db_path=db_path, **kwargs)

    core.db.create_record = patched_create
    core.db.execute_query = patched_query
    core.db.execute_update = patched_update
    core.db.update_record = patched_update_rec

    yield db_path

    # Restore original functions
    core.db.create_record = original_create
    core.db.execute_query = original_execute_query
    core.db.execute_update = original_execute_update
    core.db.update_record = original_update_record

    Path(db_path).unlink(missing_ok=True)


class TestPasswordHashing:
    """Test password hashing."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "mysecretpassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Same password produces same hash
        assert hash1 == hash2

        # Hash is different from original
        assert hash1 != password

    def test_different_passwords_different_hashes(self):
        """Test different passwords produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")

        assert hash1 != hash2

    def test_hash_is_deterministic(self):
        """Test hash is always same for same input."""
        password = "test123"
        hashes = [hash_password(password) for _ in range(5)]

        # All hashes should be identical
        assert len(set(hashes)) == 1


class TestPasswordValidation:
    """Test password validation."""

    def test_valid_password(self):
        """Test valid password passes validation."""
        is_valid, error = validate_password("validpass123")
        assert is_valid
        assert error == ""

    def test_password_too_short(self):
        """Test password < 6 chars fails."""
        is_valid, error = validate_password("pass")
        assert not is_valid
        assert "at least 6 characters" in error

    def test_password_too_long(self):
        """Test password > 128 chars fails."""
        is_valid, error = validate_password("a" * 129)
        assert not is_valid
        assert "less than 128 characters" in error

    def test_minimum_length_password(self):
        """Test 6-char password is valid."""
        is_valid, error = validate_password("pass12")
        assert is_valid


class TestUsernameValidation:
    """Test username validation."""

    def test_valid_username(self):
        """Test valid username passes."""
        is_valid, error = validate_username("john_doe")
        assert is_valid
        assert error == ""

    def test_username_with_dash(self):
        """Test username with dash is valid."""
        is_valid, error = validate_username("john-doe")
        assert is_valid

    def test_username_too_short(self):
        """Test username < 3 chars fails."""
        is_valid, error = validate_username("ab")
        assert not is_valid
        assert "at least 3 characters" in error

    def test_username_too_long(self):
        """Test username > 50 chars fails."""
        is_valid, error = validate_username("a" * 51)
        assert not is_valid
        assert "less than 50 characters" in error

    def test_username_special_chars(self):
        """Test username with invalid special chars fails."""
        is_valid, error = validate_username("john@doe")
        assert not is_valid
        assert "only contain letters" in error

    def test_username_with_numbers(self):
        """Test username with numbers is valid."""
        is_valid, error = validate_username("user123")
        assert is_valid


class TestRegistration:
    """Test user registration."""

    def test_register_valid_user(self, test_db):
        """Test registering a valid user."""
        user = register_user(
            username="testuser",
            password="password123",
            email="test@example.com"
        )

        assert user is not None
        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"
        assert 'id' in user

    def test_register_user_no_email(self, test_db):
        """Test registering user without email."""
        user = register_user(
            username="testuser",
            password="password123"
        )

        assert user is not None
        assert user['username'] == "testuser"
        assert user['email'] is None

    def test_register_user_invalid_username(self, test_db):
        """Test registration with invalid username."""
        with pytest.raises(ValidationError) as exc_info:
            register_user(
                username="ab",  # Too short
                password="password123"
            )
        assert "at least 3 characters" in str(exc_info.value)

    def test_register_user_invalid_password(self, test_db):
        """Test registration with invalid password."""
        with pytest.raises(ValidationError) as exc_info:
            register_user(
                username="validuser",
                password="pass"  # Too short
            )
        assert "at least 6 characters" in str(exc_info.value)

    def test_register_user_invalid_email(self, test_db):
        """Test registration with invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            register_user(
                username="validuser",
                password="password123",
                email="invalidemail"  # Invalid format
            )
        assert "Invalid email" in str(exc_info.value)

    def test_register_duplicate_user(self, test_db):
        """Test registering duplicate username."""
        # First registration
        register_user(
            username="testuser",
            password="password123"
        )

        # Duplicate should fail
        with pytest.raises(AuthenticationError) as exc_info:
            register_user(
                username="testuser",
                password="password456"
            )
        assert "already exists" in str(exc_info.value)


class TestLogin:
    """Test user login."""

    def test_login_valid_credentials(self, test_db):
        """Test login with valid credentials."""
        # Register
        register_user(
            username="testuser",
            password="password123"
        )

        # Login
        user = login_user("testuser", "password123")

        assert user is not None
        assert user['username'] == "testuser"

    def test_login_wrong_password(self, test_db):
        """Test login with wrong password."""
        register_user(
            username="testuser",
            password="password123"
        )

        with pytest.raises(AuthenticationError) as exc_info:
            login_user("testuser", "wrongpassword")
        assert "Invalid username or password" in str(exc_info.value)

    def test_login_nonexistent_user(self, test_db):
        """Test login with non-existent user."""
        with pytest.raises(AuthenticationError) as exc_info:
            login_user("nouser", "password123")
        assert "Invalid username or password" in str(exc_info.value)

    def test_login_case_sensitive(self, test_db):
        """Test login is case-sensitive for username."""
        register_user(
            username="testuser",
            password="password123"
        )

        with pytest.raises(AuthenticationError):
            login_user("TestUser", "password123")


class TestGetUser:
    """Test getting user information."""

    def test_get_user_by_id(self, test_db):
        """Test getting user by ID."""
        user = register_user(
            username="testuser",
            password="password123",
            email="test@example.com"
        )

        retrieved = get_user_by_id(user['id'])

        assert retrieved is not None
        assert retrieved['username'] == "testuser"
        assert retrieved['email'] == "test@example.com"

    def test_get_user_by_username(self, test_db):
        """Test getting user by username."""
        register_user(
            username="testuser",
            password="password123"
        )

        user = get_user_by_username("testuser")

        assert user is not None
        assert user['username'] == "testuser"

    def test_get_nonexistent_user_by_id(self, test_db):
        """Test getting non-existent user returns None."""
        user = get_user_by_id(9999)
        assert user is None

    def test_get_nonexistent_user_by_username(self, test_db):
        """Test getting non-existent user by username returns None."""
        user = get_user_by_username("nouser")
        assert user is None


class TestChangePassword:
    """Test password change."""

    def test_change_password_success(self, test_db):
        """Test successful password change."""
        user = register_user(
            username="testuser",
            password="oldpassword123"
        )

        change_password(user['id'], "oldpassword123", "newpassword123")

        # Old password should not work
        with pytest.raises(AuthenticationError):
            login_user("testuser", "oldpassword123")

        # New password should work
        logged_in = login_user("testuser", "newpassword123")
        assert logged_in is not None

    def test_change_password_wrong_old_password(self, test_db):
        """Test password change with wrong old password."""
        user = register_user(
            username="testuser",
            password="password123"
        )

        with pytest.raises(AuthenticationError) as exc_info:
            change_password(user['id'], "wrongpassword", "newpass123")
        assert "Current password is incorrect" in str(exc_info.value)

    def test_change_password_invalid_new_password(self, test_db):
        """Test password change with invalid new password."""
        user = register_user(
            username="testuser",
            password="password123"
        )

        with pytest.raises(ValidationError):
            change_password(user['id'], "password123", "short")

    def test_change_password_nonexistent_user(self, test_db):
        """Test password change for non-existent user."""
        with pytest.raises(AuthenticationError):
            change_password(9999, "oldpass", "newpass123")


class TestDeactivation:
    """Test user deactivation."""

    def test_deactivate_user(self, test_db):
        """Test deactivating a user."""
        user = register_user(
            username="testuser",
            password="password123"
        )

        deactivate_user(user['id'])

        # Check user is inactive
        retrieved = get_user_by_id(user['id'])
        assert retrieved['is_active'] == 0

    def test_login_inactive_user(self, test_db):
        """Test login fails for inactive user."""
        user = register_user(
            username="testuser",
            password="password123"
        )

        deactivate_user(user['id'])

        with pytest.raises(AuthenticationError) as exc_info:
            login_user("testuser", "password123")
        assert "User account is inactive" in str(exc_info.value)

    def test_reactivate_user(self, test_db):
        """Test reactivating a user."""
        user = register_user(
            username="testuser",
            password="password123"
        )

        deactivate_user(user['id'])
        reactivate_user(user['id'])

        # Should be able to login
        logged_in = login_user("testuser", "password123")
        assert logged_in is not None
