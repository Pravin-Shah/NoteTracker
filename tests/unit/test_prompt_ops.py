"""
Unit tests for apps/tradevault/utils/prompt_ops.py
Tests all prompt template operations with versioning.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.tradevault.utils.prompt_ops import (
    create_prompt, get_prompt, update_prompt, delete_prompt, search_prompts,
    get_favorite_prompts, use_prompt, toggle_favorite, add_prompt_tag,
    remove_prompt_tag, get_prompt_version, get_prompt_version_history,
    restore_prompt_version, get_prompt_categories, get_prompt_tags,
    get_prompt_stats, export_prompts
)
from core.exceptions import ValidationError


@pytest.mark.unit
@pytest.mark.database
class TestPromptCreation:
    """Test prompt creation operations."""

    def test_create_prompt_valid_data(self, test_user, sample_prompt_data, test_db_path):
        """Test creating prompt with valid data."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)
        assert isinstance(prompt_id, int)
        assert prompt_id > 0

    def test_create_prompt_missing_title(self, test_user, sample_prompt_data, test_db_path):
        """Test creating prompt without title raises error."""
        sample_prompt_data.pop('title')
        with pytest.raises(ValidationError):
            create_prompt(test_user['id'], sample_prompt_data, test_db_path)

    def test_create_prompt_missing_content(self, test_user, sample_prompt_data, test_db_path):
        """Test creating prompt without content raises error."""
        sample_prompt_data.pop('content')
        with pytest.raises(ValidationError):
            create_prompt(test_user['id'], sample_prompt_data, test_db_path)


@pytest.mark.unit
@pytest.mark.database
class TestPromptRetrieval:
    """Test prompt retrieval operations."""

    def test_get_prompt_valid_id(self, test_user, sample_prompt_data, test_db_path):
        """Test retrieving existing prompt."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)
        prompt = get_prompt(test_user['id'], prompt_id, test_db_path)

        assert prompt is not None
        assert prompt['title'] == sample_prompt_data['title']

    def test_get_prompt_invalid_id(self, test_user, test_db_path):
        """Test retrieving non-existent prompt."""
        prompt = get_prompt(test_user['id'], 99999, test_db_path)
        assert prompt is None


@pytest.mark.unit
@pytest.mark.database
class TestPromptUpdate:
    """Test prompt update and versioning."""

    def test_update_prompt_content(self, test_user, sample_prompt_data, test_db_path):
        """Test updating prompt content creates new version."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        new_content = 'Updated prompt content'
        update_prompt(test_user['id'], prompt_id, {'content': new_content}, create_version=True, db_path=test_db_path)

        prompt = get_prompt(test_user['id'], prompt_id, test_db_path)
        assert prompt['content'] == new_content

    def test_prompt_versioning(self, test_user, sample_prompt_data, test_db_path):
        """Test that updates create new versions."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        # Update multiple times
        for i in range(3):
            update_prompt(test_user['id'], prompt_id, {'content': f'Version {i}'}, create_version=True, db_path=test_db_path)

        history = get_prompt_version_history(test_user['id'], prompt_id, test_db_path)

        assert len(history) >= 1


@pytest.mark.unit
@pytest.mark.database
class TestPromptSearch:
    """Test prompt search operations."""

    def test_search_prompts_by_title(self, test_user, sample_prompt_data, test_db_path):
        """Test searching prompts by title."""
        create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        results = search_prompts(test_user['id'], query='Grid', db_path=test_db_path)

        assert len(results) > 0

    def test_search_prompts_by_category(self, test_user, sample_prompt_data, test_db_path):
        """Test searching prompts by category."""
        sample_prompt_data['category'] = 'analysis'
        create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        results = search_prompts(test_user['id'], category='analysis', db_path=test_db_path)

        assert len(results) > 0


@pytest.mark.unit
@pytest.mark.database
class TestPromptFavorites:
    """Test prompt favorite operations."""

    def test_toggle_favorite(self, test_user, sample_prompt_data, test_db_path):
        """Test toggling prompt favorite."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        toggle_favorite(test_user['id'], prompt_id, test_db_path)
        prompt = get_prompt(test_user['id'], prompt_id, test_db_path)

        assert prompt['is_favorite'] == 1

    def test_get_favorite_prompts(self, test_user, sample_prompt_data, test_db_path):
        """Test retrieving favorite prompts."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)
        toggle_favorite(test_user['id'], prompt_id, test_db_path)

        favorites = get_favorite_prompts(test_user['id'], test_db_path)

        assert len(favorites) > 0


@pytest.mark.unit
@pytest.mark.database
class TestPromptUsage:
    """Test prompt usage tracking."""

    def test_use_prompt(self, test_user, sample_prompt_data, test_db_path):
        """Test tracking prompt usage."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        use_prompt(test_user['id'], prompt_id, test_db_path)
        prompt = get_prompt(test_user['id'], prompt_id, test_db_path)

        assert prompt['usage_count'] >= 1


@pytest.mark.unit
@pytest.mark.database
class TestPromptTags:
    """Test prompt tag operations."""

    def test_add_prompt_tag(self, test_user, sample_prompt_data, test_db_path):
        """Test adding tag to prompt."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        add_prompt_tag(prompt_id, 'reusable', test_db_path)
        prompt = get_prompt(test_user['id'], prompt_id, test_db_path)

        assert 'reusable' in prompt['tags']

    def test_remove_prompt_tag(self, test_user, sample_prompt_data, test_db_path):
        """Test removing tag from prompt."""
        prompt_id = create_prompt(test_user['id'], sample_prompt_data, test_db_path)
        add_prompt_tag(prompt_id, 'tag-to-remove', test_db_path)

        remove_prompt_tag(prompt_id, 'tag-to-remove', test_db_path)
        prompt = get_prompt(test_user['id'], prompt_id, test_db_path)

        assert 'tag-to-remove' not in prompt['tags']


@pytest.mark.unit
@pytest.mark.database
class TestPromptStatistics:
    """Test prompt statistics operations."""

    def test_get_prompt_stats_empty(self, test_user, test_db_path):
        """Test statistics with no prompts."""
        stats = get_prompt_stats(test_user['id'], test_db_path)

        assert stats['total'] == 0

    def test_get_prompt_stats_with_prompts(self, test_user, sample_prompt_data, test_db_path):
        """Test statistics with prompts."""
        create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        stats = get_prompt_stats(test_user['id'], test_db_path)

        assert stats['total'] >= 1


@pytest.mark.unit
@pytest.mark.database
class TestPromptExport:
    """Test prompt export operations."""

    def test_export_prompts(self, test_user, sample_prompt_data, test_db_path):
        """Test exporting prompts."""
        create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        exported = export_prompts(test_user['id'], test_db_path)

        assert isinstance(exported, list)
        assert len(exported) > 0
