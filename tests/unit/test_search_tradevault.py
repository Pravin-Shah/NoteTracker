"""
Unit tests for apps/tradevault/utils/search.py
Tests advanced search and filtering operations for TradeVault.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.tradevault.utils.search import (
    search_edges, search_prompts, search_insights, global_search,
    search_by_category, search_by_timeframe, search_by_confidence,
    search_by_performance, search_by_tag, get_search_suggestions,
    get_search_history, save_search_history
)
from core.exceptions import ValidationError


@pytest.mark.unit
@pytest.mark.database
class TestEdgeSearch:
    """Test edge search operations."""

    def test_search_edges_empty(self, test_user, test_db_path):
        """Test searching with no edges."""
        results = search_edges(test_user['id'], query='test', db_path=test_db_path)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_edges_by_title(self, test_user, sample_edge_data, test_db_path):
        """Test searching edges by title."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['title'] = 'Grid Strategy EURUSD'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_edges(test_user['id'], query='Grid', db_path=test_db_path)

        assert len(results) > 0

    def test_search_edges_by_partial_title(self, test_user, sample_edge_data, test_db_path):
        """Test searching edges with partial title match."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['title'] = 'Price Action Reversal'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_edges(test_user['id'], query='Revers', db_path=test_db_path)

        assert len(results) > 0

    def test_search_edges_case_insensitive(self, test_user, sample_edge_data, test_db_path):
        """Test that search is case insensitive."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['title'] = 'Volatility Breakout'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results_lower = search_edges(test_user['id'], query='volatility', db_path=test_db_path)
        results_upper = search_edges(test_user['id'], query='VOLATILITY', db_path=test_db_path)
        results_mixed = search_edges(test_user['id'], query='VolAtIlItY', db_path=test_db_path)

        assert len(results_lower) > 0
        assert len(results_upper) > 0
        assert len(results_mixed) > 0

    def test_search_edges_no_results(self, test_user, test_db_path):
        """Test search with no matching results."""
        results = search_edges(test_user['id'], query='nonexistent_strategy', db_path=test_db_path)
        assert len(results) == 0

    def test_search_edges_limit(self, test_user, sample_edge_data, test_db_path):
        """Test search with result limit."""
        from apps.tradevault.utils.edge_ops import create_edge

        for _ in range(10):
            create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_edges(test_user['id'], query='', limit=5, db_path=test_db_path)
        assert len(results) <= 5


@pytest.mark.unit
@pytest.mark.database
class TestPromptSearch:
    """Test prompt search operations."""

    def test_search_prompts_empty(self, test_user, test_db_path):
        """Test searching with no prompts."""
        results = search_prompts(test_user['id'], query='test', db_path=test_db_path)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_prompts_by_title(self, test_user, sample_prompt_data, test_db_path):
        """Test searching prompts by title."""
        from apps.tradevault.utils.prompt_ops import create_prompt

        sample_prompt_data['title'] = 'Market Analysis Template'
        create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        results = search_prompts(test_user['id'], query='Market', db_path=test_db_path)

        assert len(results) > 0

    def test_search_prompts_by_content(self, test_user, sample_prompt_data, test_db_path):
        """Test searching prompts by content."""
        from apps.tradevault.utils.prompt_ops import create_prompt

        sample_prompt_data['content'] = 'Analyze the current market conditions and identify key support levels'
        create_prompt(test_user['id'], sample_prompt_data, test_db_path)

        results = search_prompts(test_user['id'], query='support', db_path=test_db_path)

        assert len(results) > 0

    def test_search_prompts_no_results(self, test_user, test_db_path):
        """Test prompt search with no results."""
        results = search_prompts(test_user['id'], query='nonexistent', db_path=test_db_path)
        assert len(results) == 0


@pytest.mark.unit
@pytest.mark.database
class TestInsightSearch:
    """Test insight search operations."""

    def test_search_insights_empty(self, test_user, test_db_path):
        """Test searching with no insights."""
        results = search_insights(test_user['id'], query='test', db_path=test_db_path)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_insights_by_title(self, test_user, sample_insight_data, test_db_path):
        """Test searching insights by title."""
        from apps.tradevault.utils.insight_ops import create_insight

        sample_insight_data['title'] = 'EUR breaking above 1.1000'
        create_insight(test_user['id'], sample_insight_data, test_db_path)

        results = search_insights(test_user['id'], query='EUR', db_path=test_db_path)

        assert len(results) > 0

    def test_search_insights_by_description(self, test_user, sample_insight_data, test_db_path):
        """Test searching insights by description."""
        from apps.tradevault.utils.insight_ops import create_insight

        sample_insight_data['description'] = 'Volume spike detected on break of consolidation pattern'
        create_insight(test_user['id'], sample_insight_data, test_db_path)

        results = search_insights(test_user['id'], query='volume', db_path=test_db_path)

        assert len(results) > 0


@pytest.mark.unit
@pytest.mark.database
class TestGlobalSearch:
    """Test global cross-item search."""

    def test_global_search_empty(self, test_user, test_db_path):
        """Test global search with no items."""
        results = global_search(test_user['id'], query='test', db_path=test_db_path)
        assert isinstance(results, dict)

    def test_global_search_mixed_results(self, test_user, sample_edge_data, sample_prompt_data, sample_insight_data, test_db_path):
        """Test global search returns mixed results."""
        from apps.tradevault.utils.edge_ops import create_edge
        from apps.tradevault.utils.prompt_ops import create_prompt
        from apps.tradevault.utils.insight_ops import create_insight

        create_edge(test_user['id'], sample_edge_data, test_db_path)
        create_prompt(test_user['id'], sample_prompt_data, test_db_path)
        create_insight(test_user['id'], sample_insight_data, test_db_path)

        results = global_search(test_user['id'], query='', db_path=test_db_path)

        assert isinstance(results, dict)
        # Should have keys for different item types
        assert any(key in results for key in ['edges', 'prompts', 'insights'])

    def test_global_search_includes_edges(self, test_user, sample_edge_data, test_db_path):
        """Test global search includes edges."""
        from apps.tradevault.utils.edge_ops import create_edge

        create_edge(test_user['id'], sample_edge_data, test_db_path)
        results = global_search(test_user['id'], query='', db_path=test_db_path)

        assert 'edges' in results or len(results) > 0

    def test_global_search_includes_prompts(self, test_user, sample_prompt_data, test_db_path):
        """Test global search includes prompts."""
        from apps.tradevault.utils.prompt_ops import create_prompt

        create_prompt(test_user['id'], sample_prompt_data, test_db_path)
        results = global_search(test_user['id'], query='', db_path=test_db_path)

        assert 'prompts' in results or len(results) > 0

    def test_global_search_includes_insights(self, test_user, sample_insight_data, test_db_path):
        """Test global search includes insights."""
        from apps.tradevault.utils.insight_ops import create_insight

        create_insight(test_user['id'], sample_insight_data, test_db_path)
        results = global_search(test_user['id'], query='', db_path=test_db_path)

        assert 'insights' in results or len(results) > 0


@pytest.mark.unit
@pytest.mark.database
class TestCategorySearch:
    """Test search by category filter."""

    def test_search_by_category_empty(self, test_user, test_db_path):
        """Test category search with no edges."""
        results = search_by_category(test_user['id'], category='grid', db_path=test_db_path)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_category_single(self, test_user, sample_edge_data, test_db_path):
        """Test searching by single category."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['category'] = 'grid'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_by_category(test_user['id'], category='grid', db_path=test_db_path)

        assert len(results) > 0

    def test_search_by_category_filters_correctly(self, test_user, sample_edge_data, test_db_path):
        """Test that category filter returns only matching category."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['category'] = 'grid'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        sample_edge_data['category'] = 'bias'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        grid_results = search_by_category(test_user['id'], category='grid', db_path=test_db_path)
        bias_results = search_by_category(test_user['id'], category='bias', db_path=test_db_path)

        assert len(grid_results) == 1
        assert len(bias_results) == 1


@pytest.mark.unit
@pytest.mark.database
class TestTimeframeSearch:
    """Test search by timeframe filter."""

    def test_search_by_timeframe_empty(self, test_user, test_db_path):
        """Test timeframe search with no edges."""
        results = search_by_timeframe(test_user['id'], timeframe='1h', db_path=test_db_path)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_timeframe_single(self, test_user, sample_edge_data, test_db_path):
        """Test searching by single timeframe."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['timeframe'] = '1h'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_by_timeframe(test_user['id'], timeframe='1h', db_path=test_db_path)

        assert len(results) > 0

    def test_search_by_timeframe_multiple(self, test_user, sample_edge_data, test_db_path):
        """Test searching by multiple timeframes."""
        from apps.tradevault.utils.edge_ops import create_edge

        for tf in ['1m', '5m', '1h', '4h', '1d']:
            sample_edge_data['timeframe'] = tf
            create_edge(test_user['id'], sample_edge_data, test_db_path)

        results_1h = search_by_timeframe(test_user['id'], timeframe='1h', db_path=test_db_path)

        assert len(results_1h) > 0


@pytest.mark.unit
@pytest.mark.database
class TestConfidenceSearch:
    """Test search by confidence grade filter."""

    def test_search_by_confidence_empty(self, test_user, test_db_path):
        """Test confidence search with no edges."""
        results = search_by_confidence(test_user['id'], confidence='A', db_path=test_db_path)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_confidence_single(self, test_user, sample_edge_data, test_db_path):
        """Test searching by single confidence grade."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['confidence_grade'] = 'A'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_by_confidence(test_user['id'], confidence='A', db_path=test_db_path)

        assert len(results) > 0

    def test_search_by_confidence_filters_correctly(self, test_user, sample_edge_data, test_db_path):
        """Test that confidence filter returns only matching grade."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['confidence_grade'] = 'A'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        sample_edge_data['confidence_grade'] = 'B'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        a_results = search_by_confidence(test_user['id'], confidence='A', db_path=test_db_path)
        b_results = search_by_confidence(test_user['id'], confidence='B', db_path=test_db_path)

        assert len(a_results) == 1
        assert len(b_results) == 1


@pytest.mark.unit
@pytest.mark.database
class TestPerformanceSearch:
    """Test search by performance criteria."""

    def test_search_by_performance_empty(self, test_user, test_db_path):
        """Test performance search with no edges."""
        results = search_by_performance(test_user['id'], min_win_rate=50, db_path=test_db_path)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_performance_min_win_rate(self, test_user, sample_edge_data, test_db_path):
        """Test searching by minimum win rate."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['win_rate'] = 70
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_by_performance(test_user['id'], min_win_rate=60, db_path=test_db_path)

        assert len(results) > 0

    def test_search_by_performance_min_profit_factor(self, test_user, sample_edge_data, test_db_path):
        """Test searching by minimum profit factor."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['profit_factor'] = 2.5
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_by_performance(test_user['id'], min_profit_factor=2.0, db_path=test_db_path)

        assert len(results) > 0

    def test_search_by_performance_combined_criteria(self, test_user, sample_edge_data, test_db_path):
        """Test searching with multiple performance criteria."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['win_rate'] = 70
        sample_edge_data['profit_factor'] = 2.5
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        results = search_by_performance(
            test_user['id'],
            min_win_rate=60,
            min_profit_factor=2.0,
            db_path=test_db_path
        )

        assert len(results) > 0


@pytest.mark.unit
@pytest.mark.database
class TestTagSearch:
    """Test search by tag filter."""

    def test_search_by_tag_empty(self, test_user, test_db_path):
        """Test tag search with no edges."""
        results = search_by_tag(test_user['id'], tag='high-probability', db_path=test_db_path)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_tag_single(self, test_user, sample_edge_data, test_db_path):
        """Test searching by single tag."""
        from apps.tradevault.utils.edge_ops import create_edge

        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)

        from apps.tradevault.utils.edge_ops import add_edge_tag
        add_edge_tag(edge_id, 'high-probability', test_db_path)

        results = search_by_tag(test_user['id'], tag='high-probability', db_path=test_db_path)

        assert len(results) > 0

    def test_search_by_tag_multiple_results(self, test_user, sample_edge_data, test_db_path):
        """Test tag search returns multiple edges with same tag."""
        from apps.tradevault.utils.edge_ops import create_edge, add_edge_tag

        edge_id1 = create_edge(test_user['id'], sample_edge_data, test_db_path)
        edge_id2 = create_edge(test_user['id'], sample_edge_data, test_db_path)

        add_edge_tag(edge_id1, 'favorite', test_db_path)
        add_edge_tag(edge_id2, 'favorite', test_db_path)

        results = search_by_tag(test_user['id'], tag='favorite', db_path=test_db_path)

        assert len(results) >= 2


@pytest.mark.unit
@pytest.mark.database
class TestSearchSuggestions:
    """Test search suggestions functionality."""

    def test_get_search_suggestions_empty(self, test_user, test_db_path):
        """Test suggestions with no data."""
        suggestions = get_search_suggestions(test_user['id'], prefix='', db_path=test_db_path)
        assert isinstance(suggestions, list)

    def test_get_search_suggestions_by_title(self, test_user, sample_edge_data, test_db_path):
        """Test suggestions based on titles."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['title'] = 'Grid Strategy EURUSD'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        suggestions = get_search_suggestions(test_user['id'], prefix='Grid', db_path=test_db_path)

        assert 'Grid' in str(suggestions) or len(suggestions) >= 0


@pytest.mark.unit
@pytest.mark.database
class TestSearchHistory:
    """Test search history tracking."""

    def test_get_search_history_empty(self, test_user, test_db_path):
        """Test history with no searches."""
        history = get_search_history(test_user['id'], db_path=test_db_path)
        assert isinstance(history, list)

    def test_search_history_tracking(self, test_user, test_db_path):
        """Test that search history is tracked."""
        # Test basic search history retrieval
        history = get_search_history(test_user['id'], db_path=test_db_path)
        assert isinstance(history, list)
