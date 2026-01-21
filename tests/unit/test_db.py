"""
Unit tests for core/db.py - Database operations
"""

import pytest
import sqlite3
from pathlib import Path
from core.db import (
    init_database, get_connection, execute_query, execute_update,
    create_record, update_record, get_record, search_records,
    delete_record, count_records, get_all_records
)
from core.exceptions import DatabaseError


@pytest.fixture
def test_db(tmp_path):
    """Create a fresh test database."""
    db_path = str(tmp_path / "test.db")
    init_database(db_path)
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


class TestDatabaseConnection:
    """Test database connection management."""

    def test_get_connection(self, test_db):
        """Test getting a database connection."""
        conn = get_connection(test_db)
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_invalid_path(self):
        """Test connection with invalid path."""
        with pytest.raises(DatabaseError):
            get_connection("/invalid/path/db.sqlite")


class TestDatabaseInitialization:
    """Test database initialization."""

    def test_init_database_creates_tables(self, tmp_path):
        """Test that init_database creates all required tables."""
        db_path = str(tmp_path / "new_db.db")
        init_database(db_path)

        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Check essential tables exist
        assert 'users' in tables
        assert 'gen_notes' in tables
        assert 'gen_tasks' in tables
        assert 'tv_edges' in tables
        assert 'notifications' in tables

        Path(db_path).unlink(missing_ok=True)


class TestCRUDOperations:
    """Test CRUD operations."""

    def test_create_user(self, test_db):
        """Test creating a user record."""
        user_id = create_record('users', {
            'username': 'testuser',
            'password_hash': 'hash123',
            'email': 'test@example.com'
        }, test_db)

        assert user_id is not None
        assert isinstance(user_id, int)

    def test_get_record(self, test_db):
        """Test retrieving a record."""
        # Create
        user_id = create_record('users', {
            'username': 'testuser',
            'password_hash': 'hash123',
            'email': 'test@example.com'
        }, test_db)

        # Retrieve
        user = get_record('users', user_id, test_db)

        assert user is not None
        assert user['username'] == 'testuser'
        assert user['email'] == 'test@example.com'

    def test_get_nonexistent_record(self, test_db):
        """Test retrieving non-existent record returns None."""
        user = get_record('users', 9999, test_db)
        assert user is None

    def test_update_record(self, test_db):
        """Test updating a record."""
        # Create
        user_id = create_record('users', {
            'username': 'testuser',
            'password_hash': 'hash123',
            'email': 'test@example.com'
        }, test_db)

        # Update
        update_record('users', user_id, {
            'email': 'newemail@example.com'
        }, test_db)

        # Verify
        user = get_record('users', user_id, test_db)
        assert user['email'] == 'newemail@example.com'
        assert user['username'] == 'testuser'  # Unchanged

    def test_delete_record_soft_delete(self, test_db):
        """Test soft delete (archived flag)."""
        # Create a note (has archived column)
        note_id = create_record('gen_notes', {
            'user_id': 1,
            'title': 'Test Note',
            'content': 'Test content',
            'archived': 0
        }, test_db)

        # Delete (should soft delete)
        delete_record('gen_notes', note_id, test_db)

        # Verify archived flag is set
        note = get_record('gen_notes', note_id, test_db)
        assert note is not None
        assert note['archived'] == 1


class TestSearch:
    """Test search operations."""

    def test_search_with_filters(self, test_db):
        """Test searching with filters."""
        # Create test data
        create_record('gen_notes', {
            'user_id': 1,
            'title': 'Note 1',
            'content': 'Content 1',
            'category': 'work',
            'importance': 5
        }, test_db)

        create_record('gen_notes', {
            'user_id': 1,
            'title': 'Note 2',
            'content': 'Content 2',
            'category': 'personal',
            'importance': 3
        }, test_db)

        # Search with filters
        results = search_records('gen_notes', {
            'user_id': 1,
            'category': 'work'
        }, test_db)

        assert len(results) == 1
        assert results[0]['title'] == 'Note 1'

    def test_search_no_filters(self, test_db):
        """Test search without filters returns all."""
        # Create test data
        for i in range(3):
            create_record('gen_notes', {
                'user_id': 1,
                'title': f'Note {i}',
                'content': f'Content {i}'
            }, test_db)

        # Search all
        results = search_records('gen_notes', db_path=test_db)

        assert len(results) >= 3

    def test_search_with_limit(self, test_db):
        """Test search respects limit."""
        # Create many records
        for i in range(10):
            create_record('gen_notes', {
                'user_id': 1,
                'title': f'Note {i}',
                'content': f'Content {i}'
            }, test_db)

        # Search with limit
        results = search_records('gen_notes', limit=5, db_path=test_db)

        assert len(results) == 5


class TestQuery:
    """Test direct query operations."""

    def test_execute_query(self, test_db):
        """Test executing SELECT query."""
        # Create test data
        user_id = create_record('users', {
            'username': 'testuser',
            'password_hash': 'hash123'
        }, test_db)

        # Query
        results = execute_query(
            "SELECT * FROM users WHERE username = ?",
            ('testuser',),
            test_db
        )

        assert len(results) == 1
        assert results[0]['username'] == 'testuser'

    def test_execute_update(self, test_db):
        """Test executing UPDATE query."""
        # Create
        user_id = create_record('users', {
            'username': 'testuser',
            'password_hash': 'hash123'
        }, test_db)

        # Update via direct query
        execute_update(
            "UPDATE users SET username = ? WHERE id = ?",
            ('newname', user_id),
            test_db
        )

        # Verify
        user = get_record('users', user_id, test_db)
        assert user['username'] == 'newname'

    def test_execute_query_no_results(self, test_db):
        """Test query with no results."""
        results = execute_query(
            "SELECT * FROM users WHERE username = ?",
            ('nonexistent',),
            test_db
        )

        assert results == []


class TestCount:
    """Test count operations."""

    def test_count_all_records(self, test_db):
        """Test counting all records."""
        # Create test data
        for i in range(5):
            create_record('gen_notes', {
                'user_id': 1,
                'title': f'Note {i}',
                'content': f'Content {i}'
            }, test_db)

        # Count
        count = count_records('gen_notes', db_path=test_db)

        assert count == 5

    def test_count_with_filters(self, test_db):
        """Test counting with filters."""
        # Create test data
        create_record('gen_notes', {
            'user_id': 1,
            'title': 'Note 1',
            'content': 'Content 1',
            'importance': 5
        }, test_db)

        create_record('gen_notes', {
            'user_id': 1,
            'title': 'Note 2',
            'content': 'Content 2',
            'importance': 3
        }, test_db)

        # Count with filter
        count = count_records('gen_notes', {
            'importance': 5
        }, test_db)

        assert count == 1


class TestDataTypes:
    """Test various data types."""

    def test_create_with_null_values(self, test_db):
        """Test creating record with NULL values."""
        note_id = create_record('gen_notes', {
            'user_id': 1,
            'title': 'Test',
            'content': 'Content',
            'category': None,  # NULL
            'importance': None  # NULL
        }, test_db)

        note = get_record('gen_notes', note_id, test_db)
        assert note['category'] is None
        assert note['importance'] is None

    def test_numeric_fields(self, test_db):
        """Test numeric field handling."""
        edge_id = create_record('tv_edges', {
            'user_id': 1,
            'title': 'Grid Edge',
            'category': 'grid',
            'win_rate': 85.5,
            'profit_factor': 1.89,
            'sample_size': 100
        }, test_db)

        edge = get_record('tv_edges', edge_id, test_db)
        assert edge['win_rate'] == 85.5
        assert edge['profit_factor'] == 1.89
        assert edge['sample_size'] == 100

    def test_text_fields(self, test_db):
        """Test text field handling."""
        description = "This is a long text with special chars: !@#$%^&*()"
        note_id = create_record('gen_notes', {
            'user_id': 1,
            'title': 'Test',
            'content': description
        }, test_db)

        note = get_record('gen_notes', note_id, test_db)
        assert note['content'] == description


class TestGetAll:
    """Test get_all_records operation."""

    def test_get_all_records(self, test_db):
        """Test getting all records."""
        # Create test data
        for i in range(3):
            create_record('gen_notes', {
                'user_id': 1,
                'title': f'Note {i}',
                'content': f'Content {i}'
            }, test_db)

        # Get all
        records = get_all_records('gen_notes', db_path=test_db)

        assert len(records) >= 3

    def test_get_all_with_limit(self, test_db):
        """Test get_all_records respects limit."""
        # Create test data
        for i in range(10):
            create_record('gen_notes', {
                'user_id': 1,
                'title': f'Note {i}',
                'content': f'Content {i}'
            }, test_db)

        # Get all with limit
        records = get_all_records('gen_notes', limit=5, db_path=test_db)

        assert len(records) == 5


class TestErrorHandling:
    """Test error handling."""

    def test_create_with_empty_data(self, test_db):
        """Test creating with empty data raises error."""
        with pytest.raises(ValueError):
            create_record('users', {}, test_db)

    def test_update_with_empty_data(self, test_db):
        """Test updating with empty data raises error."""
        with pytest.raises(ValueError):
            update_record('users', 1, {}, test_db)

    def test_query_with_invalid_table(self, test_db):
        """Test query with invalid table raises error."""
        with pytest.raises(DatabaseError):
            execute_query("SELECT * FROM nonexistent_table", (), test_db)
