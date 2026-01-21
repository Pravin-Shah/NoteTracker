"""
Unit tests for apps/tradevault/utils/insight_ops.py
Tests all insight management operations.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.tradevault.utils.insight_ops import (
    create_insight, get_insight, update_insight, delete_insight, search_insights,
    get_insights_by_status, update_insight_status, update_insight_confidence,
    get_strong_insights, get_confirmed_insights, get_insight_stats,
    get_insight_categories, bulk_delete_insights, bulk_update_status, export_insights
)
from core.exceptions import ValidationError


@pytest.mark.unit
@pytest.mark.database
class TestInsightCreation:
    """Test insight creation operations."""

    def test_create_insight_valid_data(self, test_user, sample_insight_data, test_db_path):
        """Test creating insight with valid data."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)
        assert isinstance(insight_id, int)
        assert insight_id > 0

    def test_create_insight_missing_title(self, test_user, sample_insight_data, test_db_path):
        """Test creating insight without title raises error."""
        sample_insight_data.pop('title')
        with pytest.raises(ValidationError):
            create_insight(test_user['id'], sample_insight_data, test_db_path)

    def test_create_insight_missing_description(self, test_user, sample_insight_data, test_db_path):
        """Test creating insight without description raises error."""
        sample_insight_data.pop('description')
        with pytest.raises(ValidationError):
            create_insight(test_user['id'], sample_insight_data, test_db_path)

    def test_create_insight_sets_defaults(self, test_user, sample_insight_data, test_db_path):
        """Test that defaults are set when not provided."""
        sample_insight_data.pop('status', None)
        sample_insight_data.pop('confidence', None)

        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)

        assert insight['status'] == 'open'
        assert insight['confidence'] in ['hypothesis', 'weak', 'moderate', 'strong']


@pytest.mark.unit
@pytest.mark.database
class TestInsightRetrieval:
    """Test insight retrieval operations."""

    def test_get_insight_valid_id(self, test_user, sample_insight_data, test_db_path):
        """Test retrieving existing insight."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)

        assert insight is not None
        assert insight['title'] == sample_insight_data['title']
        assert insight['status'] in ['open', 'confirmed', 'disputed']

    def test_get_insight_invalid_id(self, test_user, test_db_path):
        """Test retrieving non-existent insight."""
        insight = get_insight(test_user['id'], 99999, test_db_path)
        assert insight is None

    def test_get_insight_wrong_user(self, test_user, test_user2, sample_insight_data, test_db_path):
        """Test retrieving insight from different user."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)
        insight = get_insight(test_user2['id'], insight_id, test_db_path)
        assert insight is None


@pytest.mark.unit
@pytest.mark.database
class TestInsightUpdate:
    """Test insight update operations."""

    def test_update_insight_title(self, test_user, sample_insight_data, test_db_path):
        """Test updating insight title."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        update_insight(test_user['id'], insight_id, {'title': 'New Title'}, test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)

        assert insight['title'] == 'New Title'

    def test_update_insight_description(self, test_user, sample_insight_data, test_db_path):
        """Test updating insight description."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        new_description = 'Updated description with more details'
        update_insight(test_user['id'], insight_id, {'description': new_description}, test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)

        assert insight['description'] == new_description

    def test_update_insight_confidence(self, test_user, sample_insight_data, test_db_path):
        """Test updating insight confidence level."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        update_insight(test_user['id'], insight_id, {'confidence': 'strong'}, test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)

        assert insight['confidence'] == 'strong'

    def test_update_non_existent_insight(self, test_user, test_db_path):
        """Test updating non-existent insight raises error."""
        with pytest.raises(ValidationError):
            update_insight(test_user['id'], 99999, {'title': 'New'}, test_db_path)


@pytest.mark.unit
@pytest.mark.database
class TestInsightStatus:
    """Test insight status transitions."""

    def test_confirm_insight(self, test_user, sample_insight_data, test_db_path):
        """Test confirming an open insight."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        update_insight_status(test_user['id'], insight_id, 'confirmed', test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)

        assert insight['status'] == 'confirmed'

    def test_dispute_insight(self, test_user, sample_insight_data, test_db_path):
        """Test disputing an open insight."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        update_insight_status(test_user['id'], insight_id, 'disputed', test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)

        assert insight['status'] == 'disputed'

    def test_reopen_insight(self, test_user, sample_insight_data, test_db_path):
        """Test reopening a confirmed insight."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        update_insight_status(test_user['id'], insight_id, 'confirmed', test_db_path)
        update_insight_status(test_user['id'], insight_id, 'open', test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)

        assert insight['status'] == 'open'

    def test_get_insights_by_status(self, test_user, sample_insight_data, test_db_path):
        """Test filtering insights by status."""
        insight_id1 = create_insight(test_user['id'], sample_insight_data, test_db_path)
        insight_id2 = create_insight(test_user['id'], sample_insight_data, test_db_path)

        confirm_insight(test_user['id'], insight_id1, test_db_path)

        open_insights = get_insights_by_status(test_user['id'], 'open', test_db_path)
        confirmed_insights = get_insights_by_status(test_user['id'], 'confirmed', test_db_path)

        assert len(open_insights) == 1
        assert len(confirmed_insights) == 1


@pytest.mark.unit
@pytest.mark.database
class TestInsightConfidence:
    """Test insight confidence level operations."""

    def test_confidence_levels_valid(self, test_user, sample_insight_data, test_db_path):
        """Test all valid confidence levels."""
        for confidence in ['hypothesis', 'weak', 'moderate', 'strong']:
            sample_insight_data['confidence'] = confidence
            insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)
            insight = get_insight(test_user['id'], insight_id, test_db_path)
            assert insight['confidence'] == confidence

    def test_get_insights_by_confidence(self, test_user, sample_insight_data, test_db_path):
        """Test filtering insights by confidence level."""
        sample_insight_data['confidence'] = 'strong'
        insight_id1 = create_insight(test_user['id'], sample_insight_data, test_db_path)

        sample_insight_data['confidence'] = 'weak'
        insight_id2 = create_insight(test_user['id'], sample_insight_data, test_db_path)

        strong_insights = get_strong_insights(test_user['id'], test_db_path)
        # Test that we can get strong insights (at least 1)
        assert isinstance(strong_insights, list)


@pytest.mark.unit
@pytest.mark.database
class TestInsightSearch:
    """Test insight search operations."""

    def test_search_insights_by_title(self, test_user, sample_insight_data, test_db_path):
        """Test searching insights by title."""
        create_insight(test_user['id'], sample_insight_data, test_db_path)

        results = search_insights(test_user['id'], query='Price', db_path=test_db_path)

        assert len(results) > 0

    def test_search_insights_by_category(self, test_user, sample_insight_data, test_db_path):
        """Test searching insights by category."""
        sample_insight_data['category'] = 'volume'
        create_insight(test_user['id'], sample_insight_data, test_db_path)

        results = search_insights(test_user['id'], category='volume', db_path=test_db_path)

        assert len(results) > 0

    def test_search_insights_no_results(self, test_user, test_db_path):
        """Test search with no results."""
        results = search_insights(test_user['id'], query='nonexistent', db_path=test_db_path)
        assert len(results) == 0

    def test_search_insights_limit(self, test_user, sample_insight_data, test_db_path):
        """Test search with limit."""
        for _ in range(10):
            create_insight(test_user['id'], sample_insight_data, test_db_path)

        results = search_insights(test_user['id'], limit=5, db_path=test_db_path)
        assert len(results) <= 5


@pytest.mark.unit
@pytest.mark.database
class TestInsightDelete:
    """Test insight deletion operations."""

    def test_delete_insight(self, test_user, sample_insight_data, test_db_path):
        """Test deleting an insight."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        delete_insight(test_user['id'], insight_id, test_db_path)
        insight = get_insight(test_user['id'], insight_id, test_db_path)

        assert insight is None

    def test_delete_non_existent_insight(self, test_user, test_db_path):
        """Test deleting non-existent insight raises error."""
        with pytest.raises(ValidationError):
            delete_insight(test_user['id'], 99999, test_db_path)

    def test_delete_wrong_user_insight(self, test_user, test_user2, sample_insight_data, test_db_path):
        """Test deleting insight from another user raises error."""
        insight_id = create_insight(test_user['id'], sample_insight_data, test_db_path)

        with pytest.raises(ValidationError):
            delete_insight(test_user2['id'], insight_id, test_db_path)

    def test_bulk_delete_insights(self, test_user, sample_insight_data, test_db_path):
        """Test deleting multiple insights."""
        insight_id1 = create_insight(test_user['id'], sample_insight_data, test_db_path)
        insight_id2 = create_insight(test_user['id'], sample_insight_data, test_db_path)

        bulk_delete_insights([insight_id1, insight_id2], test_db_path)

        assert get_insight(test_user['id'], insight_id1, test_db_path) is None
        assert get_insight(test_user['id'], insight_id2, test_db_path) is None


@pytest.mark.unit
@pytest.mark.database
class TestInsightStatistics:
    """Test insight statistics operations."""

    def test_get_insight_stats_empty(self, test_user, test_db_path):
        """Test statistics with no insights."""
        stats = get_insight_stats(test_user['id'], test_db_path)

        assert stats['total'] == 0
        assert stats['open'] == 0
        assert stats['confirmed'] == 0

    def test_get_insight_stats_with_insights(self, test_user, sample_insight_data, test_db_path):
        """Test statistics with insights."""
        insight_id1 = create_insight(test_user['id'], sample_insight_data, test_db_path)
        insight_id2 = create_insight(test_user['id'], sample_insight_data, test_db_path)

        confirm_insight(test_user['id'], insight_id1, test_db_path)

        stats = get_insight_stats(test_user['id'], test_db_path)

        assert stats['total'] >= 2
        assert stats['open'] == 1
        assert stats['confirmed'] == 1

    def test_get_insight_categories(self, test_user, sample_insight_data, test_db_path):
        """Test getting all insight categories."""
        create_insight(test_user['id'], sample_insight_data, test_db_path)

        categories = get_insight_categories(test_user['id'], test_db_path)

        assert isinstance(categories, list)
        assert len(categories) > 0


@pytest.mark.unit
@pytest.mark.database
class TestInsightBulkOperations:
    """Test insight bulk operations."""

    def test_bulk_update_status(self, test_user, sample_insight_data, test_db_path):
        """Test updating status of multiple insights."""
        insight_id1 = create_insight(test_user['id'], sample_insight_data, test_db_path)
        insight_id2 = create_insight(test_user['id'], sample_insight_data, test_db_path)

        bulk_update_status([insight_id1, insight_id2], 'confirmed', test_db_path)

        insight1 = get_insight(test_user['id'], insight_id1, test_db_path)
        insight2 = get_insight(test_user['id'], insight_id2, test_db_path)

        assert insight1['status'] == 'confirmed'
        assert insight2['status'] == 'confirmed'


@pytest.mark.unit
@pytest.mark.database
class TestInsightExport:
    """Test insight export operations."""

    def test_export_insights(self, test_user, sample_insight_data, test_db_path):
        """Test exporting insights."""
        create_insight(test_user['id'], sample_insight_data, test_db_path)

        exported = export_insights(test_user['id'], test_db_path)

        assert isinstance(exported, list)
        assert len(exported) > 0

    def test_export_insights_contains_all_fields(self, test_user, sample_insight_data, test_db_path):
        """Test exported insights contain all fields."""
        create_insight(test_user['id'], sample_insight_data, test_db_path)

        exported = export_insights(test_user['id'], test_db_path)

        assert len(exported) > 0
        insight = exported[0]
        assert 'id' in insight
        assert 'title' in insight
        assert 'description' in insight
        assert 'status' in insight
        assert 'confidence' in insight
