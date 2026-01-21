"""
Unit tests for apps/general/utils/task_ops.py
Tests all task management operations.
"""

import pytest
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.general.utils.task_ops import (
    create_task, get_task, update_task, complete_task, start_task, delete_task,
    search_tasks, get_tasks_due_today, get_overdue_tasks, get_upcoming_tasks,
    add_task_tag, create_task_reminder, add_task_checklist, complete_checklist_item,
    get_task_categories, get_task_tags, get_task_stats, log_task_action
)
from core.exceptions import ValidationError


@pytest.mark.unit
@pytest.mark.database
class TestTaskCreation:
    """Test task creation operations."""

    def test_create_task_valid_data(self, test_user, sample_task_data, test_db_path):
        """Test creating task with valid data."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        assert isinstance(task_id, int)
        assert task_id > 0

    def test_create_task_missing_title(self, test_user, sample_task_data, test_db_path):
        """Test creating task without title raises error."""
        sample_task_data.pop('title')
        with pytest.raises(ValidationError):
            create_task(test_user['id'], sample_task_data, test_db_path)

    def test_create_task_short_title(self, test_user, sample_task_data, test_db_path):
        """Test creating task with title too short."""
        sample_task_data['title'] = 'ab'
        with pytest.raises(ValidationError):
            create_task(test_user['id'], sample_task_data, test_db_path)

    def test_create_task_invalid_priority(self, test_user, sample_task_data, test_db_path):
        """Test creating task with invalid priority."""
        sample_task_data['priority'] = 10
        with pytest.raises(ValidationError):
            create_task(test_user['id'], sample_task_data, test_db_path)

    def test_create_task_invalid_date(self, test_user, sample_task_data, test_db_path):
        """Test creating task with invalid date."""
        sample_task_data['due_date'] = 'invalid-date'
        with pytest.raises(ValidationError):
            create_task(test_user['id'], sample_task_data, test_db_path)

    def test_create_task_sets_defaults(self, test_user, sample_task_data, test_db_path):
        """Test that defaults are set."""
        sample_task_data.pop('status', None)
        sample_task_data.pop('priority', None)

        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert task['status'] == 'pending'
        assert task['priority'] == 3


@pytest.mark.unit
@pytest.mark.database
class TestTaskRetrieval:
    """Test task retrieval operations."""

    def test_get_task_valid_id(self, test_user, sample_task_data, test_db_path):
        """Test retrieving existing task."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert task is not None
        assert task['id'] == task_id
        assert task['title'] == sample_task_data['title']

    def test_get_task_invalid_id(self, test_user, test_db_path):
        """Test retrieving non-existent task."""
        task = get_task(test_user['id'], 99999, test_db_path)
        assert task is None

    def test_get_task_wrong_user(self, test_user, test_user2, sample_task_data, test_db_path):
        """Test retrieving task from different user."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        task = get_task(test_user2['id'], task_id, test_db_path)
        assert task is None

    def test_get_task_includes_reminders(self, test_user, sample_task_data, test_db_path):
        """Test that retrieved task includes reminders."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        create_task_reminder(task_id, 'days-before', 1, db_path=test_db_path)

        task = get_task(test_user['id'], task_id, test_db_path)
        assert 'reminders' in task
        assert len(task['reminders']) > 0


@pytest.mark.unit
@pytest.mark.database
class TestTaskStatus:
    """Test task status operations."""

    def test_start_task(self, test_user, sample_task_data, test_db_path):
        """Test starting a task."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        start_task(test_user['id'], task_id, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert task['status'] == 'in-progress'

    def test_complete_task(self, test_user, sample_task_data, test_db_path):
        """Test completing a task."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        complete_task(test_user['id'], task_id, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert task['status'] == 'completed'
        assert task['completed_date'] is not None

    def test_task_status_progression(self, test_user, sample_task_data, test_db_path):
        """Test task status progression."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        # pending -> in-progress
        start_task(test_user['id'], task_id, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)
        assert task['status'] == 'in-progress'

        # in-progress -> completed
        complete_task(test_user['id'], task_id, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)
        assert task['status'] == 'completed'


@pytest.mark.unit
@pytest.mark.database
class TestTaskUpdate:
    """Test task update operations."""

    def test_update_task_title(self, test_user, sample_task_data, test_db_path):
        """Test updating task title."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        update_task(test_user['id'], task_id, {'title': 'New Title'}, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert task['title'] == 'New Title'

    def test_update_task_priority(self, test_user, sample_task_data, test_db_path):
        """Test updating task priority."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        update_task(test_user['id'], task_id, {'priority': 5}, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert task['priority'] == 5

    def test_update_task_due_date(self, test_user, sample_task_data, test_db_path):
        """Test updating task due date."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        new_date = (date.today() + timedelta(days=5)).isoformat()
        update_task(test_user['id'], task_id, {'due_date': new_date}, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert task['due_date'] == new_date


@pytest.mark.unit
@pytest.mark.database
class TestTaskDelete:
    """Test task deletion operations."""

    def test_delete_task(self, test_user, sample_task_data, test_db_path):
        """Test deleting a task."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        delete_task(test_user['id'], task_id, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert task is None

    def test_delete_non_existent_task(self, test_user, test_db_path):
        """Test deleting non-existent task raises error."""
        with pytest.raises(ValidationError):
            delete_task(test_user['id'], 99999, test_db_path)


@pytest.mark.unit
@pytest.mark.database
class TestTaskSearch:
    """Test task search operations."""

    def test_search_tasks_by_title(self, test_user, sample_task_data, test_db_path):
        """Test searching tasks by title."""
        create_task(test_user['id'], sample_task_data, test_db_path)

        results = search_tasks(test_user['id'], query='Test Task', db_path=test_db_path)

        assert len(results) > 0

    def test_search_tasks_by_status(self, test_user, sample_task_data, test_db_path):
        """Test searching tasks by status."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        complete_task(test_user['id'], task_id, test_db_path)

        results = search_tasks(test_user['id'], status='completed', db_path=test_db_path)

        assert len(results) > 0
        assert all(t['status'] == 'completed' for t in results)

    def test_search_tasks_by_priority(self, test_user, sample_task_data, test_db_path):
        """Test searching tasks by priority."""
        sample_task_data['priority'] = 5
        create_task(test_user['id'], sample_task_data, test_db_path)

        results = search_tasks(test_user['id'], priority=5, db_path=test_db_path)

        assert len(results) > 0
        assert all(t['priority'] == 5 for t in results)

    def test_search_tasks_no_results(self, test_user, test_db_path):
        """Test search with no results."""
        results = search_tasks(test_user['id'], query='nonexistent', db_path=test_db_path)
        assert len(results) == 0


@pytest.mark.unit
@pytest.mark.database
class TestTaskDueDate:
    """Test task due date operations."""

    def test_get_tasks_due_today(self, test_user, sample_task_data, test_db_path):
        """Test retrieving tasks due today."""
        today = date.today().isoformat()
        sample_task_data['due_date'] = today

        create_task(test_user['id'], sample_task_data, test_db_path)
        tasks = get_tasks_due_today(test_user['id'], test_db_path)

        assert len(tasks) > 0

    def test_get_overdue_tasks(self, test_user, sample_task_data, test_db_path):
        """Test retrieving overdue tasks."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        sample_task_data['due_date'] = yesterday

        create_task(test_user['id'], sample_task_data, test_db_path)
        tasks = get_overdue_tasks(test_user['id'], test_db_path)

        assert len(tasks) > 0

    def test_get_upcoming_tasks(self, test_user, sample_task_data, test_db_path):
        """Test retrieving upcoming tasks."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        sample_task_data['due_date'] = tomorrow

        create_task(test_user['id'], sample_task_data, test_db_path)
        tasks = get_upcoming_tasks(test_user['id'], days=7, db_path=test_db_path)

        assert len(tasks) > 0


@pytest.mark.unit
@pytest.mark.database
class TestTaskTags:
    """Test task tag operations."""

    def test_add_task_tag(self, test_user, sample_task_data, test_db_path):
        """Test adding tag to task."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        add_task_tag(task_id, 'urgent', test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert 'urgent' in task['tags']

    def test_get_task_tags(self, test_user, sample_task_data, test_db_path):
        """Test getting all task tags."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        add_task_tag(task_id, 'work', test_db_path)
        add_task_tag(task_id, 'important', test_db_path)

        tags = get_task_tags(test_user['id'], test_db_path)

        assert 'work' in tags
        assert 'important' in tags


@pytest.mark.unit
@pytest.mark.database
class TestTaskReminders:
    """Test task reminder operations."""

    def test_create_task_reminder_days_before(self, test_user, sample_task_data, test_db_path):
        """Test creating days-before reminder."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        reminder_id = create_task_reminder(task_id, 'days-before', reminder_value=3, db_path=test_db_path)

        assert isinstance(reminder_id, int)
        assert reminder_id > 0

    def test_create_task_reminder_specific_time(self, test_user, sample_task_data, test_db_path):
        """Test creating specific-time reminder."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        reminder_id = create_task_reminder(task_id, 'specific-time', reminder_time='09:00', db_path=test_db_path)

        assert isinstance(reminder_id, int)


@pytest.mark.unit
@pytest.mark.database
class TestTaskChecklist:
    """Test task checklist operations."""

    def test_add_task_checklist(self, test_user, sample_task_data, test_db_path):
        """Test adding checklist items."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        items = ['Item 1', 'Item 2', 'Item 3']

        add_task_checklist(task_id, items, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)

        assert len(task['checklist']) == 3

    def test_complete_checklist_item(self, test_user, sample_task_data, test_db_path):
        """Test completing checklist item."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        add_task_checklist(task_id, ['Item 1'], test_db_path)

        task = get_task(test_user['id'], task_id, test_db_path)
        item_id = task['checklist'][0]['id']

        complete_checklist_item(item_id, test_db_path)

        task = get_task(test_user['id'], task_id, test_db_path)
        assert task['checklist'][0]['is_completed'] == 1


@pytest.mark.unit
@pytest.mark.database
class TestTaskStatistics:
    """Test task statistics operations."""

    def test_get_task_stats_empty(self, test_user, test_db_path):
        """Test statistics with no tasks."""
        stats = get_task_stats(test_user['id'], test_db_path)

        assert stats['total'] == 0
        assert stats['pending'] == 0

    def test_get_task_stats_with_tasks(self, test_user, sample_task_data, test_db_path):
        """Test statistics with tasks."""
        create_task(test_user['id'], sample_task_data, test_db_path)

        task_id2 = create_task(test_user['id'], sample_task_data, test_db_path)
        complete_task(test_user['id'], task_id2, test_db_path)

        stats = get_task_stats(test_user['id'], test_db_path)

        assert stats['total'] >= 2
        assert stats['completed'] >= 1

    def test_get_task_categories(self, test_user, sample_task_data, test_db_path):
        """Test getting all task categories."""
        create_task(test_user['id'], sample_task_data, test_db_path)

        categories = get_task_categories(test_user['id'], test_db_path)

        assert 'personal' in categories


@pytest.mark.unit
@pytest.mark.database
class TestTaskHistory:
    """Test task history operations."""

    def test_log_task_action(self, test_user, sample_task_data, test_db_path):
        """Test logging task action."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        log_task_action(task_id, 'started', 'Task started for testing', test_db_path)

        # Verify action was logged
        task = get_task(test_user['id'], task_id, test_db_path)
        assert task is not None
