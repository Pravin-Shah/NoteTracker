"""
Unit tests for apps/general/utils/search.py
Tests all general app search operations.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.general.utils.search import (
    search_notes, search_tasks, search_events, global_search,
    search_by_tag, search_by_category, search_by_date_range,
    save_search_history, get_search_history, clear_search_history,
    get_search_suggestions
)
from apps.general.utils.note_ops import create_note, add_note_tag
from apps.general.utils.task_ops import create_task, add_task_tag
from apps.general.utils.calendar_ops import create_event


@pytest.mark.unit
@pytest.mark.database
class TestSearchNotes:
    """Test note search operations."""

    def test_search_notes_by_title(self, test_user, sample_note_data, test_db_path):
        """Test searching notes by title."""
        create_note(test_user['id'], sample_note_data, test_db_path)

        results = search_notes(test_user['id'], query='Test Note', db_path=test_db_path)

        assert len(results) > 0
        assert 'title' in results[0]

    def test_search_notes_by_content(self, test_user, sample_note_data, test_db_path):
        """Test searching notes by content."""
        create_note(test_user['id'], sample_note_data, test_db_path)

        results = search_notes(test_user['id'], query='test note content', db_path=test_db_path)

        assert len(results) > 0

    def test_search_notes_no_results(self, test_user, test_db_path):
        """Test search with no results."""
        results = search_notes(test_user['id'], query='nonexistent', db_path=test_db_path)
        assert len(results) == 0

    def test_search_notes_limit(self, test_user, sample_note_data, test_db_path):
        """Test search with result limit."""
        for i in range(10):
            sample_note_data['title'] = f'Test Note {i}'
            create_note(test_user['id'], sample_note_data, test_db_path)

        results = search_notes(test_user['id'], limit=5, db_path=test_db_path)
        assert len(results) <= 5


@pytest.mark.unit
@pytest.mark.database
class TestSearchTasks:
    """Test task search operations."""

    def test_search_tasks_by_title(self, test_user, sample_task_data, test_db_path):
        """Test searching tasks by title."""
        create_task(test_user['id'], sample_task_data, test_db_path)

        results = search_tasks(test_user['id'], query='Test Task', db_path=test_db_path)

        assert len(results) > 0

    def test_search_tasks_by_status(self, test_user, sample_task_data, test_db_path):
        """Test searching tasks by status."""
        create_task(test_user['id'], sample_task_data, test_db_path)

        results = search_tasks(test_user['id'], status='pending', db_path=test_db_path)

        assert len(results) > 0
        assert all(t['status'] == 'pending' for t in results)

    def test_search_tasks_no_results(self, test_user, test_db_path):
        """Test task search with no results."""
        results = search_tasks(test_user['id'], query='nonexistent', db_path=test_db_path)
        assert len(results) == 0


@pytest.mark.unit
@pytest.mark.database
class TestSearchEvents:
    """Test event search operations."""

    def test_search_events_by_title(self, test_user, sample_event_data, test_db_path):
        """Test searching events by title."""
        create_event(test_user['id'], sample_event_data, test_db_path)

        results = search_events(test_user['id'], query='Test Event', db_path=test_db_path)

        assert len(results) > 0

    def test_search_events_no_results(self, test_user, test_db_path):
        """Test event search with no results."""
        results = search_events(test_user['id'], query='nonexistent', db_path=test_db_path)
        assert len(results) == 0


@pytest.mark.unit
@pytest.mark.database
class TestGlobalSearch:
    """Test global cross-item search."""

    def test_global_search_all_items(self, test_user, sample_note_data, sample_task_data, sample_event_data, test_db_path):
        """Test global search across all item types."""
        create_note(test_user['id'], sample_note_data, test_db_path)
        create_task(test_user['id'], sample_task_data, test_db_path)
        create_event(test_user['id'], sample_event_data, test_db_path)

        results = global_search(test_user['id'], query='Test', db_path=test_db_path)

        assert 'notes' in results
        assert 'tasks' in results
        assert 'events' in results

    def test_global_search_filter_by_type(self, test_user, sample_note_data, test_db_path):
        """Test global search with type filter."""
        create_note(test_user['id'], sample_note_data, test_db_path)

        results = global_search(test_user['id'], query='Test', item_types=['note'], db_path=test_db_path)

        assert len(results['notes']) > 0

    def test_global_search_no_results(self, test_user, test_db_path):
        """Test global search with no results."""
        results = global_search(test_user['id'], query='nonexistent', db_path=test_db_path)

        assert len(results['notes']) == 0
        assert len(results['tasks']) == 0
        assert len(results['events']) == 0


@pytest.mark.unit
@pytest.mark.database
class TestSearchHistory:
    """Test search history operations."""

    def test_save_search_history(self, test_user, test_db_path):
        """Test saving search query to history."""
        save_search_history(test_user['id'], 'test query', db_path=test_db_path)

        history = get_search_history(test_user['id'], db_path=test_db_path)

        assert 'test query' in history

    def test_get_search_history(self, test_user, test_db_path):
        """Test retrieving search history."""
        for i in range(5):
            save_search_history(test_user['id'], f'query {i}', db_path=test_db_path)

        history = get_search_history(test_user['id'], db_path=test_db_path)

        assert len(history) > 0

    def test_get_search_history_limit(self, test_user, test_db_path):
        """Test search history with limit."""
        for i in range(30):
            save_search_history(test_user['id'], f'query {i}', db_path=test_db_path)

        history = get_search_history(test_user['id'], limit=10, db_path=test_db_path)

        assert len(history) <= 10


@pytest.mark.unit
@pytest.mark.database
class TestSearchSuggestions:
    """Test search suggestions."""

    def test_get_search_suggestions_notes(self, test_user, sample_note_data, test_db_path):
        """Test getting search suggestions from notes."""
        create_note(test_user['id'], sample_note_data, test_db_path)

        suggestions = get_search_suggestions(test_user['id'], prefix='Test', db_path=test_db_path)

        assert 'edges' in suggestions
        assert 'prompts' in suggestions
        assert 'tags' in suggestions

    def test_get_search_suggestions_no_matches(self, test_user, test_db_path):
        """Test search suggestions with no matches."""
        suggestions = get_search_suggestions(test_user['id'], prefix='zzz', db_path=test_db_path)

        assert isinstance(suggestions, dict)


@pytest.mark.unit
@pytest.mark.database
class TestSearchWithTags:
    """Test tag-based search."""

    def test_search_by_tag_notes(self, test_user, sample_note_data, test_db_path):
        """Test searching notes by tag."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        add_note_tag(note_id, 'important', test_db_path)

        results = search_by_tag(test_user['id'], tag='important', db_path=test_db_path)

        assert len(results) > 0

    def test_search_by_tag_tasks(self, test_user, sample_task_data, test_db_path):
        """Test searching tasks by tag."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        add_task_tag(task_id, 'urgent', test_db_path)

        results = search_by_tag(test_user['id'], tag='urgent', db_path=test_db_path)

        assert len(results) > 0


@pytest.mark.unit
@pytest.mark.database
class TestSearchByCategory:
    """Test category-based search."""

    def test_search_by_category_notes(self, test_user, sample_note_data, test_db_path):
        """Test searching notes by category."""
        sample_note_data['category'] = 'personal'
        create_note(test_user['id'], sample_note_data, test_db_path)

        results = search_by_category(test_user['id'], category='personal', db_path=test_db_path)

        assert len(results) > 0


@pytest.mark.unit
@pytest.mark.database
class TestSearchByDateRange:
    """Test date range search."""

    def test_search_by_date_range(self, test_user, sample_task_data, test_db_path):
        """Test searching by date range."""
        from datetime import date, timedelta

        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=7)).isoformat()

        sample_task_data['due_date'] = start_date
        create_task(test_user['id'], sample_task_data, test_db_path)

        results = search_by_date_range(test_user['id'], start_date=start_date, end_date=end_date, db_path=test_db_path)

        assert len(results) > 0
