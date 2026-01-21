"""
Unit tests for apps/general/utils/note_ops.py
Tests all note management operations.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.general.utils.note_ops import (
    create_note, get_note, update_note, delete_note, search_notes,
    pin_note, unpin_note, archive_note, unarchive_note, get_pinned_notes,
    add_note_tag, remove_note_tag, add_note_attachment, remove_note_attachment,
    get_note_categories, get_note_tags, get_note_stats, bulk_add_tags,
    bulk_delete_notes, export_notes
)
from core.exceptions import ValidationError


@pytest.mark.unit
@pytest.mark.database
class TestNoteCreation:
    """Test note creation operations."""

    def test_create_note_valid_data(self, test_user, sample_note_data, test_db_path):
        """Test creating note with valid data."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        assert isinstance(note_id, int)
        assert note_id > 0

    def test_create_note_missing_title(self, test_user, sample_note_data, test_db_path):
        """Test creating note without title raises error."""
        sample_note_data.pop('title')
        with pytest.raises(ValidationError):
            create_note(test_user['id'], sample_note_data, test_db_path)

    def test_create_note_short_title(self, test_user, sample_note_data, test_db_path):
        """Test creating note with title too short."""
        sample_note_data['title'] = 'a'
        with pytest.raises(ValidationError):
            create_note(test_user['id'], sample_note_data, test_db_path)

    def test_create_note_sets_defaults(self, test_user, sample_note_data, test_db_path):
        """Test that defaults are set when not provided."""
        sample_note_data.pop('category', None)
        sample_note_data.pop('importance', None)

        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        note = get_note(test_user['id'], note_id, test_db_path)

        assert note['category'] is not None
        assert note['importance'] == 3


@pytest.mark.unit
@pytest.mark.database
class TestNoteRetrieval:
    """Test note retrieval operations."""

    def test_get_note_valid_id(self, test_user, sample_note_data, test_db_path):
        """Test retrieving existing note."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        note = get_note(test_user['id'], note_id, test_db_path)

        assert note is not None
        assert note['id'] == note_id
        assert note['title'] == sample_note_data['title']

    def test_get_note_invalid_id(self, test_user, test_db_path):
        """Test retrieving non-existent note."""
        note = get_note(test_user['id'], 99999, test_db_path)
        assert note is None

    def test_get_note_wrong_user(self, test_user, test_user2, sample_note_data, test_db_path):
        """Test retrieving note from different user."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        note = get_note(test_user2['id'], note_id, test_db_path)
        assert note is None

    def test_get_note_includes_tags(self, test_user, sample_note_data, test_db_path):
        """Test that retrieved note includes tags."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        add_note_tag(note_id, 'test-tag', test_db_path)

        note = get_note(test_user['id'], note_id, test_db_path)
        assert 'tags' in note
        assert 'test-tag' in note['tags']


@pytest.mark.unit
@pytest.mark.database
class TestNoteUpdate:
    """Test note update operations."""

    def test_update_note_title(self, test_user, sample_note_data, test_db_path):
        """Test updating note title."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        update_note(test_user['id'], note_id, {'title': 'New Title'}, test_db_path)
        note = get_note(test_user['id'], note_id, test_db_path)

        assert note['title'] == 'New Title'

    def test_update_note_content(self, test_user, sample_note_data, test_db_path):
        """Test updating note content."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        new_content = 'Updated content'
        update_note(test_user['id'], note_id, {'content': new_content}, test_db_path)
        note = get_note(test_user['id'], note_id, test_db_path)

        assert note['content'] == new_content

    def test_update_note_importance(self, test_user, sample_note_data, test_db_path):
        """Test updating note importance."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        update_note(test_user['id'], note_id, {'importance': 5}, test_db_path)
        note = get_note(test_user['id'], note_id, test_db_path)

        assert note['importance'] == 5

    def test_update_non_existent_note(self, test_user, test_db_path):
        """Test updating non-existent note raises error."""
        with pytest.raises(ValidationError):
            update_note(test_user['id'], 99999, {'title': 'New'}, test_db_path)


@pytest.mark.unit
@pytest.mark.database
class TestNotePin:
    """Test note pin/unpin operations."""

    def test_pin_note(self, test_user, sample_note_data, test_db_path):
        """Test pinning a note."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        pin_note(test_user['id'], note_id, test_db_path)
        note = get_note(test_user['id'], note_id, test_db_path)

        assert note['is_pinned'] == 1

    def test_unpin_note(self, test_user, sample_note_data, test_db_path):
        """Test unpinning a note."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        pin_note(test_user['id'], note_id, test_db_path)
        unpin_note(test_user['id'], note_id, test_db_path)

        note = get_note(test_user['id'], note_id, test_db_path)
        assert note['is_pinned'] == 0

    def test_get_pinned_notes(self, test_user, sample_note_data, test_db_path):
        """Test retrieving pinned notes."""
        note_id1 = create_note(test_user['id'], sample_note_data, test_db_path)
        note_id2 = create_note(test_user['id'], sample_note_data, test_db_path)

        pin_note(test_user['id'], note_id1, test_db_path)

        pinned_notes = get_pinned_notes(test_user['id'], test_db_path)

        assert len(pinned_notes) == 1
        assert pinned_notes[0]['id'] == note_id1


@pytest.mark.unit
@pytest.mark.database
class TestNoteDelete:
    """Test note deletion operations."""

    def test_delete_note(self, test_user, sample_note_data, test_db_path):
        """Test deleting a note (soft delete)."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        delete_note(test_user['id'], note_id, test_db_path)
        note = get_note(test_user['id'], note_id, test_db_path)

        assert note is None

    def test_delete_non_existent_note(self, test_user, test_db_path):
        """Test deleting non-existent note raises error."""
        with pytest.raises(ValidationError):
            delete_note(test_user['id'], 99999, test_db_path)

    def test_delete_wrong_user_note(self, test_user, test_user2, sample_note_data, test_db_path):
        """Test deleting note from another user raises error."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        with pytest.raises(ValidationError):
            delete_note(test_user2['id'], note_id, test_db_path)


@pytest.mark.unit
@pytest.mark.database
class TestNoteSearch:
    """Test note search operations."""

    def test_search_notes_by_title(self, test_user, sample_note_data, test_db_path):
        """Test searching notes by title."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        results = search_notes(test_user['id'], query='Test Note', db_path=test_db_path)

        assert len(results) > 0
        assert any(r['id'] == note_id for r in results)

    def test_search_notes_by_content(self, test_user, sample_note_data, test_db_path):
        """Test searching notes by content."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        results = search_notes(test_user['id'], query='test note content', db_path=test_db_path)

        assert len(results) > 0
        assert any(r['id'] == note_id for r in results)

    def test_search_notes_by_category(self, test_user, sample_note_data, test_db_path):
        """Test searching notes by category."""
        create_note(test_user['id'], sample_note_data, test_db_path)

        results = search_notes(test_user['id'], category='personal', db_path=test_db_path)

        assert len(results) > 0
        assert all(r['category'] == 'personal' for r in results)

    def test_search_notes_no_results(self, test_user, test_db_path):
        """Test search with no results."""
        results = search_notes(test_user['id'], query='nonexistent', db_path=test_db_path)
        assert len(results) == 0

    def test_search_notes_limit(self, test_user, sample_note_data, test_db_path):
        """Test search with limit."""
        for _ in range(10):
            create_note(test_user['id'], sample_note_data, test_db_path)

        results = search_notes(test_user['id'], limit=5, db_path=test_db_path)
        assert len(results) <= 5


@pytest.mark.unit
@pytest.mark.database
class TestNoteTags:
    """Test note tag operations."""

    def test_add_note_tag(self, test_user, sample_note_data, test_db_path):
        """Test adding tag to note."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        add_note_tag(note_id, 'important', test_db_path)
        note = get_note(test_user['id'], note_id, test_db_path)

        assert 'important' in note['tags']

    def test_add_multiple_tags(self, test_user, sample_note_data, test_db_path):
        """Test adding multiple tags to note."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)

        add_note_tag(note_id, 'tag1', test_db_path)
        add_note_tag(note_id, 'tag2', test_db_path)
        add_note_tag(note_id, 'tag3', test_db_path)

        note = get_note(test_user['id'], note_id, test_db_path)
        assert len(note['tags']) == 3

    def test_remove_note_tag(self, test_user, sample_note_data, test_db_path):
        """Test removing tag from note."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        add_note_tag(note_id, 'tag-to-remove', test_db_path)

        remove_note_tag(note_id, 'tag-to-remove', test_db_path)
        note = get_note(test_user['id'], note_id, test_db_path)

        assert 'tag-to-remove' not in note['tags']

    def test_get_note_tags(self, test_user, sample_note_data, test_db_path):
        """Test getting all tags for user."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        add_note_tag(note_id, 'tag1', test_db_path)
        add_note_tag(note_id, 'tag2', test_db_path)

        tags = get_note_tags(test_user['id'], test_db_path)

        assert 'tag1' in tags
        assert 'tag2' in tags


@pytest.mark.unit
@pytest.mark.database
class TestNoteStatistics:
    """Test note statistics operations."""

    def test_get_note_stats_empty(self, test_user, test_db_path):
        """Test statistics with no notes."""
        stats = get_note_stats(test_user['id'], test_db_path)

        assert stats['total'] == 0
        assert stats['pinned'] == 0

    def test_get_note_stats_with_notes(self, test_user, sample_note_data, test_db_path):
        """Test statistics with notes."""
        note_id = create_note(test_user['id'], sample_note_data, test_db_path)
        pin_note(test_user['id'], note_id, test_db_path)

        stats = get_note_stats(test_user['id'], test_db_path)

        assert stats['total'] >= 1
        assert stats['pinned'] == 1

    def test_get_note_categories(self, test_user, sample_note_data, test_db_path):
        """Test getting all note categories."""
        create_note(test_user['id'], sample_note_data, test_db_path)

        categories = get_note_categories(test_user['id'], test_db_path)

        assert 'personal' in categories


@pytest.mark.unit
@pytest.mark.database
class TestNoteExport:
    """Test note export operations."""

    def test_export_notes_returns_list(self, test_user, sample_note_data, test_db_path):
        """Test exporting notes returns list."""
        create_note(test_user['id'], sample_note_data, test_db_path)

        exported = export_notes(test_user['id'], test_db_path)

        assert isinstance(exported, list)
        assert len(exported) > 0

    def test_export_notes_contains_all_fields(self, test_user, sample_note_data, test_db_path):
        """Test exported notes contain all fields."""
        create_note(test_user['id'], sample_note_data, test_db_path)

        exported = export_notes(test_user['id'], test_db_path)

        assert len(exported) > 0
        note = exported[0]
        assert 'id' in note
        assert 'title' in note
        assert 'content' in note


@pytest.mark.unit
@pytest.mark.database
class TestNoteBulkOperations:
    """Test note bulk operations."""

    def test_bulk_add_tags(self, test_user, sample_note_data, test_db_path):
        """Test adding tags to multiple notes."""
        note_id1 = create_note(test_user['id'], sample_note_data, test_db_path)
        note_id2 = create_note(test_user['id'], sample_note_data, test_db_path)

        bulk_add_tags([note_id1, note_id2], 'bulk-tag', test_db_path)

        note1 = get_note(test_user['id'], note_id1, test_db_path)
        note2 = get_note(test_user['id'], note_id2, test_db_path)

        assert 'bulk-tag' in note1['tags']
        assert 'bulk-tag' in note2['tags']

    def test_bulk_delete_notes(self, test_user, sample_note_data, test_db_path):
        """Test deleting multiple notes."""
        note_id1 = create_note(test_user['id'], sample_note_data, test_db_path)
        note_id2 = create_note(test_user['id'], sample_note_data, test_db_path)

        bulk_delete_notes([note_id1, note_id2], test_db_path)

        assert get_note(test_user['id'], note_id1, test_db_path) is None
        assert get_note(test_user['id'], note_id2, test_db_path) is None


@pytest.mark.unit
@pytest.mark.database
class TestNoteImportance:
    """Test note importance/priority operations."""

    def test_importance_levels_valid(self, test_user, sample_note_data, test_db_path):
        """Test all valid importance levels."""
        for importance in [1, 2, 3, 4, 5]:
            sample_note_data['importance'] = importance
            note_id = create_note(test_user['id'], sample_note_data, test_db_path)
            note = get_note(test_user['id'], note_id, test_db_path)
            assert note['importance'] == importance

    def test_search_by_importance(self, test_user, sample_note_data, test_db_path):
        """Test searching notes by importance."""
        sample_note_data['importance'] = 5
        create_note(test_user['id'], sample_note_data, test_db_path)

        # Search should include high importance notes
        results = search_notes(test_user['id'], db_path=test_db_path)
        assert len(results) > 0
