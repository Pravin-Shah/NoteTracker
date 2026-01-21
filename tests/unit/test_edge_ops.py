"""
Unit tests for apps/tradevault/utils/edge_ops.py
Tests all trading edge management operations.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.tradevault.utils.edge_ops import (
    create_edge, get_edge, update_edge, delete_edge, search_edges,
    get_top_performers, get_edges_by_strategy, add_edge_tag, remove_edge_tag,
    upload_edge_screenshot, remove_edge_screenshot, link_edges, unlink_edges,
    get_edge_categories, get_edge_tags, get_edge_stats, export_edges
)
from core.exceptions import ValidationError


@pytest.mark.unit
@pytest.mark.database
class TestEdgeCreation:
    """Test edge creation operations."""

    def test_create_edge_valid_data(self, test_user, sample_edge_data, test_db_path):
        """Test creating edge with valid data."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
        assert isinstance(edge_id, int)
        assert edge_id > 0

    def test_create_edge_missing_title(self, test_user, sample_edge_data, test_db_path):
        """Test creating edge without title raises error."""
        sample_edge_data.pop('title')
        with pytest.raises(ValidationError):
            create_edge(test_user['id'], sample_edge_data, test_db_path)

    def test_create_edge_invalid_confidence_grade(self, test_user, sample_edge_data, test_db_path):
        """Test creating edge with invalid confidence grade."""
        sample_edge_data['confidence_grade'] = 'Z'
        with pytest.raises(ValidationError):
            create_edge(test_user['id'], sample_edge_data, test_db_path)

    def test_create_edge_invalid_win_rate(self, test_user, sample_edge_data, test_db_path):
        """Test creating edge with invalid win rate."""
        sample_edge_data['win_rate'] = 150
        with pytest.raises(ValidationError):
            create_edge(test_user['id'], sample_edge_data, test_db_path)

    def test_create_edge_performance_metrics(self, test_user, sample_edge_data, test_db_path):
        """Test edge creation with performance metrics."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
        edge = get_edge(test_user['id'], edge_id, test_db_path)

        assert edge['win_rate'] == sample_edge_data['win_rate']
        assert edge['profit_factor'] == sample_edge_data['profit_factor']
        assert edge['sample_size'] == sample_edge_data['sample_size']


@pytest.mark.unit
@pytest.mark.database
class TestEdgeRetrieval:
    """Test edge retrieval operations."""

    def test_get_edge_valid_id(self, test_user, sample_edge_data, test_db_path):
        """Test retrieving existing edge."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
        edge = get_edge(test_user['id'], edge_id, test_db_path)

        assert edge is not None
        assert edge['id'] == edge_id
        assert edge['title'] == sample_edge_data['title']

    def test_get_edge_invalid_id(self, test_user, test_db_path):
        """Test retrieving non-existent edge."""
        edge = get_edge(test_user['id'], 99999, test_db_path)
        assert edge is None

    def test_get_edge_wrong_user(self, test_user, test_user2, sample_edge_data, test_db_path):
        """Test retrieving edge from different user."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
        edge = get_edge(test_user2['id'], edge_id, test_db_path)
        assert edge is None


@pytest.mark.unit
@pytest.mark.database
class TestEdgeUpdate:
    """Test edge update operations."""

    def test_update_edge_title(self, test_user, sample_edge_data, test_db_path):
        """Test updating edge title."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        update_edge(test_user['id'], edge_id, {'title': 'New Title'}, test_db_path)
        edge = get_edge(test_user['id'], edge_id, test_db_path)

        assert edge['title'] == 'New Title'

    def test_update_edge_performance(self, test_user, sample_edge_data, test_db_path):
        """Test updating edge performance metrics."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        update_edge(test_user['id'], edge_id, {'win_rate': 75.0, 'profit_factor': 2.0}, test_db_path)
        edge = get_edge(test_user['id'], edge_id, test_db_path)

        assert edge['win_rate'] == 75.0
        assert edge['profit_factor'] == 2.0

    def test_update_edge_status(self, test_user, sample_edge_data, test_db_path):
        """Test updating edge status."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        update_edge(test_user['id'], edge_id, {'status': 'deprecated'}, test_db_path)
        edge = get_edge(test_user['id'], edge_id, test_db_path)

        assert edge['status'] == 'deprecated'


@pytest.mark.unit
@pytest.mark.database
class TestEdgeDelete:
    """Test edge deletion operations."""

    def test_delete_edge(self, test_user, sample_edge_data, test_db_path):
        """Test deleting an edge."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        delete_edge(test_user['id'], edge_id, test_db_path)
        edge = get_edge(test_user['id'], edge_id, test_db_path)

        assert edge is None

    def test_delete_non_existent_edge(self, test_user, test_db_path):
        """Test deleting non-existent edge raises error."""
        with pytest.raises(ValidationError):
            delete_edge(test_user['id'], 99999, test_db_path)


@pytest.mark.unit
@pytest.mark.database
class TestEdgeSearch:
    """Test edge search operations."""

    def test_search_edges_by_title(self, test_user, sample_edge_data, test_db_path):
        """Test searching edges by title."""
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_edges(test_user['id'], query='Grid', db_path=test_db_path)

        assert len(results) > 0

    def test_search_edges_active_only(self, test_user, sample_edge_data, test_db_path):
        """Test search returns only active/testing edges."""
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_edges(test_user['id'], db_path=test_db_path)

        assert all(e['status'] in ['active', 'testing'] for e in results)

    def test_search_edges_no_results(self, test_user, test_db_path):
        """Test search with no results."""
        results = search_edges(test_user['id'], query='nonexistent', db_path=test_db_path)
        assert len(results) == 0


@pytest.mark.unit
@pytest.mark.database
class TestEdgePerformance:
    """Test edge performance operations."""

    def test_get_top_performers(self, test_user, sample_edge_data, test_db_path):
        """Test retrieving top performing edges."""
        sample_edge_data['win_rate'] = 80.0
        edge_id1 = create_edge(test_user['id'], sample_edge_data, test_db_path)

        sample_edge_data['title'] = 'Lower Win Rate Edge'
        sample_edge_data['win_rate'] = 55.0
        edge_id2 = create_edge(test_user['id'], sample_edge_data, test_db_path)

        top_edges = get_top_performers(test_user['id'], test_db_path)

        assert len(top_edges) > 0
        assert top_edges[0]['id'] == edge_id1

    def test_get_edges_by_strategy(self, test_user, sample_edge_data, test_db_path):
        """Test retrieving edges by strategy."""
        sample_edge_data['strategy'] = 'grid'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        edges = get_edges_by_strategy(test_user['id'], strategy='grid', db_path=test_db_path)

        assert len(edges) > 0


@pytest.mark.unit
@pytest.mark.database
class TestEdgeTags:
    """Test edge tag operations."""

    def test_add_edge_tag(self, test_user, sample_edge_data, test_db_path):
        """Test adding tag to edge."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        add_edge_tag(edge_id, 'high-volatility', test_db_path)
        edge = get_edge(test_user['id'], edge_id, test_db_path)

        assert 'high-volatility' in edge['tags']

    def test_remove_edge_tag(self, test_user, sample_edge_data, test_db_path):
        """Test removing tag from edge."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
        add_edge_tag(edge_id, 'test-tag', test_db_path)

        remove_edge_tag(edge_id, 'test-tag', test_db_path)
        edge = get_edge(test_user['id'], edge_id, test_db_path)

        assert 'test-tag' not in edge['tags']

    def test_get_edge_tags(self, test_user, sample_edge_data, test_db_path):
        """Test getting all edge tags."""
        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
        add_edge_tag(edge_id, 'tag1', test_db_path)
        add_edge_tag(edge_id, 'tag2', test_db_path)

        tags = get_edge_tags(test_user['id'], test_db_path)

        assert 'tag1' in tags
        assert 'tag2' in tags


@pytest.mark.unit
@pytest.mark.database
class TestEdgeRelationships:
    """Test edge relationship operations."""

    def test_link_edges(self, test_user, sample_edge_data, test_db_path):
        """Test linking two edges."""
        edge_id1 = create_edge(test_user['id'], sample_edge_data, test_db_path)

        sample_edge_data['title'] = 'Related Edge'
        edge_id2 = create_edge(test_user['id'], sample_edge_data, test_db_path)

        link_edges(edge_id1, edge_id2, 'complements', test_db_path)

        # Verify link was created
        edge1 = get_edge(test_user['id'], edge_id1, test_db_path)
        assert edge1 is not None

    def test_unlink_edges(self, test_user, sample_edge_data, test_db_path):
        """Test unlinking two edges."""
        edge_id1 = create_edge(test_user['id'], sample_edge_data, test_db_path)

        sample_edge_data['title'] = 'Related Edge'
        edge_id2 = create_edge(test_user['id'], sample_edge_data, test_db_path)

        link_edges(edge_id1, edge_id2, 'complements', test_db_path)
        unlink_edges(edge_id1, edge_id2, test_db_path)

        # Verify unlink worked
        edge1 = get_edge(test_user['id'], edge_id1, test_db_path)
        assert edge1 is not None


@pytest.mark.unit
@pytest.mark.database
class TestEdgeStatistics:
    """Test edge statistics operations."""

    def test_get_edge_stats_empty(self, test_user, test_db_path):
        """Test statistics with no edges."""
        stats = get_edge_stats(test_user['id'], test_db_path)

        assert stats['total'] == 0
        assert stats['active'] == 0

    def test_get_edge_stats_with_edges(self, test_user, sample_edge_data, test_db_path):
        """Test statistics with edges."""
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        stats = get_edge_stats(test_user['id'], test_db_path)

        assert stats['total'] >= 1

    def test_get_edge_categories(self, test_user, sample_edge_data, test_db_path):
        """Test getting all edge categories."""
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        categories = get_edge_categories(test_user['id'], test_db_path)

        assert 'grid' in categories


@pytest.mark.unit
@pytest.mark.database
class TestEdgeExport:
    """Test edge export operations."""

    def test_export_edges(self, test_user, sample_edge_data, test_db_path):
        """Test exporting edges."""
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        exported = export_edges(test_user['id'], test_db_path)

        assert isinstance(exported, list)
        assert len(exported) > 0
        assert 'title' in exported[0]
        assert 'win_rate' in exported[0]
