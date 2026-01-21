"""
Integration tests for UI ↔ Backend interactions.
Tests complete user workflows from UI layer to database.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.general.utils.note_ops import create_note, get_note, update_note, search_notes
from apps.general.utils.task_ops import create_task, get_task, update_task, search_tasks
from apps.tradevault.utils.edge_ops import create_edge, get_edge, update_edge, search_edges
from apps.tradevault.utils.prompt_ops import create_prompt, get_prompt, update_prompt, search_prompts
from apps.tradevault.utils.insight_ops import create_insight, get_insight, update_insight, search_insights
from core.exceptions import ValidationError


@pytest.mark.integration
@pytest.mark.database
class TestNoteWorkflow:
    """Test complete note management workflow."""

    def test_create_note_workflow(self, test_user, sample_note_data, test_db_path):
        """Test creating a note through UI."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        assert note_id is not None
        note = get_note(test_user['id'], note_id, test_db_path)
        assert note is not None

    def test_create_edit_delete_note_workflow(self, test_user, sample_note_data, test_db_path):
        """Test complete note lifecycle."""
        # Create
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        original_note = get_note(test_user['id'], note_id, test_db_path)
        assert original_note is not None

        # Edit
        update_note(test_user['id'], note_id, {'title': 'Updated Title'}, test_db_path)
        updated_note = get_note(test_user['id'], note_id, test_db_path)
        assert updated_note['title'] == 'Updated Title'

        # Delete
        from apps.general.utils.note_ops import delete_note
        delete_note(test_user['id'], note_id, test_db_path)
        deleted_note = get_note(test_user['id'], note_id, test_db_path)
        assert deleted_note is None

    def test_note_search_workflow(self, test_user, sample_note_data, test_db_path):
        """Test creating note and then searching for it."""
        sample_note_data['title'] = 'Important Meeting Notes'
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        results = search_notes(test_user['id'], query='Important', db_path=test_db_path)

        assert len(results) > 0
        assert any(r['id'] == note_id for r in results)

    def test_note_tagging_workflow(self, test_user, sample_note_data, test_db_path):
        """Test adding tags to note."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        from apps.general.utils.note_ops import add_note_tag
        add_note_tag(note_id, 'urgent', test_db_path)

        note = get_note(test_user['id'], note_id, test_db_path)
        assert 'urgent' in note['tags']

    def test_multiple_notes_workflow(self, test_user, sample_note_data, test_db_path):
        """Test creating and managing multiple notes."""
        note_ids = []
        for i in range(5):
            sample_note_data['title'] = f'Note {i}'
            note_id = create_note(test_user['id'], sample_note_data, test_db_path)
            note_ids.append(note_id)

        results = search_notes(test_user['id'], db_path=test_db_path)
        assert len(results) >= 5


@pytest.mark.integration
@pytest.mark.database
class TestTaskWorkflow:
    """Test complete task management workflow."""

    def test_create_task_workflow(self, test_user, sample_task_data, test_db_path):
        """Test creating a task through UI."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        assert task_id is not None
        task = get_task(test_user['id'], task_id, test_db_path)
        assert task is not None

    def test_create_update_complete_task_workflow(self, test_user, sample_task_data, test_db_path):
        """Test task lifecycle: create → update → complete."""
        # Create
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)
        assert task['status'] == 'pending'

        # Update priority
        update_task(test_user['id'], task_id, {'priority': 5}, test_db_path)
        updated_task = get_task(test_user['id'], task_id, test_db_path)
        assert updated_task['priority'] == 5

        # Complete
        update_task(test_user['id'], task_id, {'status': 'completed'}, test_db_path)
        completed_task = get_task(test_user['id'], task_id, test_db_path)
        assert completed_task['status'] == 'completed'

    def test_task_search_workflow(self, test_user, sample_task_data, test_db_path):
        """Test creating tasks and searching for them."""
        sample_task_data['title'] = 'Complete Project Report'
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        results = search_tasks(test_user['id'], query='Report', db_path=test_db_path)

        assert len(results) > 0
        assert any(r['id'] == task_id for r in results)

    def test_overdue_task_workflow(self, test_user, sample_task_data, test_db_path):
        """Test creating and managing overdue tasks."""
        from datetime import datetime, timedelta

        past_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        sample_task_data['due_date'] = past_date
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        task = get_task(test_user['id'], task_id, test_db_path)
        assert task is not None

    def test_task_reminders_workflow(self, test_user, sample_task_data, test_db_path):
        """Test adding reminders to tasks."""
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)

        from apps.general.utils.task_ops import add_task_reminder
        add_task_reminder(task_id, 1, 'day', test_db_path)

        task = get_task(test_user['id'], task_id, test_db_path)
        assert task is not None


@pytest.mark.integration
@pytest.mark.database
class TestEdgeWorkflow:
    """Test complete edge management workflow."""

    def test_create_edge_workflow(self, test_user, sample_edge_data, test_db_path):
        """Test creating an edge through UI."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        assert edge_id is not None
        edge = get_edge(test_user['id'], edge_id, test_db_path)
        assert edge is not None

    def test_create_update_edge_workflow(self, test_user, sample_edge_data, test_db_path):
        """Test edge creation and updates."""
        # Create
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
        original_edge = get_edge(test_user['id'], edge_id, test_db_path)
        assert original_edge is not None

        # Update performance
        update_edge(test_user['id'], edge_id, {'win_rate': 75, 'profit_factor': 2.5}, test_db_path)
        updated_edge = get_edge(test_user['id'], edge_id, test_db_path)
        assert updated_edge['win_rate'] == 75

        # Update status
        update_edge(test_user['id'], edge_id, {'status': 'testing'}, test_db_path)
        status_updated_edge = get_edge(test_user['id'], edge_id, test_db_path)
        assert status_updated_edge['status'] == 'testing'

    def test_edge_search_workflow(self, test_user, sample_edge_data, test_db_path):
        """Test creating edges and searching for them."""
        sample_edge_data['category'] = 'grid'
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_edges(test_user['id'], query='', db_path=test_db_path)

        assert len(results) > 0
        assert any(r['id'] == edge_id for r in results)

    def test_edge_tagging_workflow(self, test_user, sample_edge_data, test_db_path):
        """Test tagging edges."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        from apps.tradevault.utils.edge_ops import add_edge_tag
        add_edge_tag(edge_id, 'favorite', test_db_path)

        edge = get_edge(test_user['id'], edge_id, test_db_path)
        assert 'favorite' in edge.get('tags', [])

    def test_multiple_edges_workflow(self, test_user, sample_edge_data, test_db_path):
        """Test creating and managing multiple edges."""
        edge_ids = []
        for i in range(5):
            sample_edge_data['title'] = f'Edge {i}'
            edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
            edge_ids.append(edge_id)

        results = search_edges(test_user['id'], query='', db_path=test_db_path)
        assert len(results) >= 5


@pytest.mark.integration
@pytest.mark.database
class TestPromptWorkflow:
    """Test complete prompt management workflow."""

    def test_create_prompt_workflow(self, test_user, sample_prompt_data, test_db_path):
        """Test creating a prompt through UI."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        assert prompt_id is not None
        prompt = get_prompt(test_user['id'], prompt_id, test_db_path)
        assert prompt is not None

    def test_create_update_prompt_workflow(self, test_user, sample_prompt_data, test_db_path):
        """Test prompt creation and versioning."""
        # Create
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)
        original_prompt = get_prompt(test_user['id'], prompt_id, test_db_path)
        assert original_prompt is not None

        # Update (creates new version)
        update_prompt(test_user['id'], prompt_id, {'content': 'New content'}, create_version=True, db_path=test_db_path)
        updated_prompt = get_prompt(test_user['id'], prompt_id, test_db_path)
        assert updated_prompt['content'] == 'New content'

    def test_prompt_search_workflow(self, test_user, sample_prompt_data, test_db_path):
        """Test creating prompts and searching for them."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        results = search_prompts(test_user['id'], query='', db_path=test_db_path)

        assert len(results) > 0
        assert any(r['id'] == prompt_id for r in results)

    def test_prompt_versioning_workflow(self, test_user, sample_prompt_data, test_db_path):
        """Test creating multiple versions of a prompt."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        for i in range(3):
            update_prompt(test_user['id'], prompt_id, {'content': f'Version {i}'}, create_version=True, db_path=test_db_path)

        from apps.tradevault.utils.prompt_ops import get_prompt_version_history
        history = get_prompt_version_history(test_user['id'], prompt_id, test_db_path)

        assert len(history) >= 1

    def test_prompt_favorites_workflow(self, test_user, sample_prompt_data, test_db_path):
        """Test marking prompts as favorites."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        from apps.tradevault.utils.prompt_ops import toggle_favorite
        toggle_favorite(test_user['id'], prompt_id, test_db_path)

        prompt = get_prompt(test_user['id'], prompt_id, test_db_path)
        assert prompt['is_favorite'] == 1


@pytest.mark.integration
@pytest.mark.database
class TestInsightWorkflow:
    """Test complete insight management workflow."""

    def test_create_insight_workflow(self, test_user, sample_insight_data, test_db_path):
        """Test creating an insight through UI."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        assert insight_id is not None
        insight = get_insight(test_user['id'], insight_id, test_db_path)
        assert insight is not None

    def test_insight_status_workflow(self, test_user, sample_insight_data, test_db_path):
        """Test changing insight status through UI."""
        # Create as open
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)
        assert insight['status'] == 'open'

        # Confirm
        from apps.tradevault.utils.insight_ops import confirm_insight
        confirm_insight(test_user['id'], insight_id, test_db_path)
        confirmed_insight = get_insight(test_user['id'], insight_id, test_db_path)
        assert confirmed_insight['status'] == 'confirmed'

        # Reopen
        from apps.tradevault.utils.insight_ops import reopen_insight
        reopen_insight(test_user['id'], insight_id, test_db_path)
        reopened_insight = get_insight(test_user['id'], insight_id, test_db_path)
        assert reopened_insight['status'] == 'open'

    def test_insight_search_workflow(self, test_user, sample_insight_data, test_db_path):
        """Test creating insights and searching for them."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        results = search_insights(test_user['id'], query='', db_path=test_db_path)

        assert len(results) > 0
        assert any(r['id'] == insight_id for r in results)

    def test_multiple_insights_workflow(self, test_user, sample_insight_data, test_db_path):
        """Test creating and managing multiple insights."""
        insight_ids = []
        for i in range(5):
            sample_insight_data['title'] = f'Insight {i}'
            insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)
            insight_ids.append(insight_id)

        results = search_insights(test_user['id'], query='', db_path=test_db_path)
        assert len(results) >= 5


@pytest.mark.integration
@pytest.mark.database
class TestCrossAppWorkflow:
    """Test workflows involving multiple apps."""

    def test_dashboard_aggregation_workflow(self, test_user, sample_note_data, sample_task_data, sample_edge_data, test_db_path):
        """Test aggregating data from multiple apps for dashboard."""
        # Create items in different apps
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        task_id = create_task(test_user['id'], sample_task_data, test_db_path)
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        # Verify each can be retrieved
        note = get_note(test_user['id'], note_id, test_db_path)
        task = get_task(test_user['id'], task_id, test_db_path)
        edge = get_edge(test_user['id'], edge_id, test_db_path)

        assert note is not None
        assert task is not None
        assert edge is not None

    def test_global_search_workflow(self, test_user, sample_note_data, sample_edge_data, sample_insight_data, test_db_path):
        """Test global search across multiple app types."""
        from apps.tradevault.utils.search import global_search

        # Create items in different apps
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        # Perform global search
        results = global_search(test_user['id'], query='', db_path=test_db_path)

        assert isinstance(results, dict)

    def test_user_isolation_workflow(self, test_user, test_user2, sample_note_data, test_db_path):
        """Test that items from one user are isolated from another."""
        # Create note for user 1
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        # User 1 can see their note
        user1_note = get_note(test_user['id'], note_id, test_db_path)
        assert user1_note is not None

        # User 2 cannot see user 1's note
        user2_note = get_note(test_user2['id'], note_id, test_db_path)
        assert user2_note is None

    def test_bulk_operations_workflow(self, test_user, sample_note_data, test_db_path):
        """Test bulk operations across multiple items."""
        from apps.general.utils.note_ops import bulk_add_tags

        note_ids = []
        for _ in range(5):
            note_id = create_note(test_user['id'], sample_note_data, test_db_path)
            note_ids.append(note_id)

        bulk_add_tags(note_ids, 'batch-processed', test_db_path)

        for note_id in note_ids:
            note = get_note(test_user['id'], note_id, test_db_path)
            assert 'batch-processed' in note.get('tags', [])
