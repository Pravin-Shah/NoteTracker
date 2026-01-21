"""
Pytest configuration and fixtures for NoteTracker testing.
Provides database fixtures, mock data, and shared test utilities.
"""

import pytest
import sqlite3
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db import init_database, execute_query, execute_update, create_record
from core.auth import register_user


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_path(tmp_path):
    """Create a temporary database for each test."""
    db_file = tmp_path / "test.db"
    db_path = str(db_file)
    # Initialize database with schema
    init_database(db_path)
    yield db_path
    # Cleanup after test
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass


@pytest.fixture
def test_user(test_db_path):
    """Create a test user for testing."""
    import time

    user_data = {
        'username': 'testuser_' + str(int(time.time() * 1000000) % 1000000),
        'email': 'test@example.com',
        'password': 'TestPassword123'
    }

    # Register user with db_path
    user_result = register_user(
        user_data['username'],
        user_data['password'],
        user_data['email'],
        None,  # telegram_id
        test_db_path
    )

    # Extract user_id from result
    if isinstance(user_result, dict):
        user_id = user_result.get('id')
    else:
        user_id = user_result

    return {
        'id': user_id,
        'username': user_data['username'],
        'email': user_data['email'],
        'password': user_data['password']
    }


@pytest.fixture
def test_user2(test_db_path):
    """Create a second test user for multi-user testing."""
    import time

    user_data = {
        'username': 'testuser2_' + str(int(time.time() * 1000000) % 1000000),
        'email': 'test2@example.com',
        'password': 'TestPassword456'
    }

    # Register user with db_path
    user_result = register_user(
        user_data['username'],
        user_data['password'],
        user_data['email'],
        None,  # telegram_id
        test_db_path
    )

    # Extract user_id from result
    if isinstance(user_result, dict):
        user_id = user_result.get('id')
    else:
        user_id = user_result

    return {
        'id': user_id,
        'username': user_data['username'],
        'email': user_data['email'],
        'password': user_data['password']
    }


# ============================================================================
# General App Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_note_data():
    """Sample note data for testing."""
    return {
        'title': 'Test Note',
        'content': 'This is a test note content',
        'category': 'personal',
        'importance': 3
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        'title': 'Test Task',
        'description': 'This is a test task',
        'category': 'personal',
        'priority': 3,
        'due_date': '2026-02-01',
        'due_time': '09:00',
        'status': 'pending'
    }


@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        'title': 'Test Event',
        'description': 'Test event description',
        'start_date': '2026-02-01',
        'start_time': '14:00',
        'location': 'Test Location',
        'category': 'personal',
        'is_all_day': 0,
        'reminder_minutes_before': 1440
    }


@pytest.fixture
def sample_reminder_data():
    """Sample reminder data for testing."""
    return {
        'reminder_type': 'days-before',
        'reminder_value': 3,
        'is_sent': 0
    }


# ============================================================================
# TradeVault Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_edge_data():
    """Sample edge data for testing."""
    return {
        'title': 'Grid Support Edge',
        'category': 'grid',
        'timeframe': '1h',
        'market_condition': 'bull',
        'instrument': 'EURUSD',
        'confidence_grade': 'A',
        'status': 'active',
        'win_rate': 65.5,
        'profit_factor': 1.85,
        'sample_size': 100,
        'description': 'Trading edge description',
        'observations': 'Key observations',
        'why_it_works': 'Technical explanation',
        'strategy': 'grid'
    }


@pytest.fixture
def sample_prompt_data():
    """Sample prompt data for testing."""
    return {
        'title': 'Grid Analysis Prompt',
        'category': 'analysis',
        'content': 'Analyze the grid support levels...',
        'use_case': 'Analyze grid trading setups',
        'is_favorite': 0
    }


@pytest.fixture
def sample_insight_data():
    """Sample insight data for testing."""
    return {
        'title': 'Support Level Confirmed',
        'description': 'EURUSD support at 1.0500 held strongly',
        'category': 'support_resistance',
        'date_observed': '2026-01-12',
        'status': 'open',
        'confidence_level': 'moderate'
    }


# ============================================================================
# Database Helper Fixtures
# ============================================================================

@pytest.fixture
def db_helper(test_db_path):
    """Helper for database operations during tests."""
    class DBHelper:
        def __init__(self, db_path):
            self.db_path = db_path

        def execute_query(self, sql, params=None):
            return execute_query(sql, params or (), self.db_path)

        def execute_update(self, sql, params=None):
            return execute_update(sql, params or (), self.db_path)

        def create_record(self, table, data):
            return create_record(table, data, self.db_path)

        def get_record_count(self, table):
            result = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            return result[0]['count'] if result else 0

    return DBHelper(test_db_path)


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
