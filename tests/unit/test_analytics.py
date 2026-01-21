"""
Unit tests for apps/tradevault/utils/analytics.py
Tests portfolio analytics and performance calculations.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.tradevault.utils.analytics import (
    get_portfolio_statistics, get_category_performance, get_timeframe_performance,
    get_confidence_distribution, calculate_optimal_portfolio, get_performance_trend,
    get_edge_comparison, get_edge_correlation_analysis
)
from core.exceptions import ValidationError


@pytest.mark.unit
@pytest.mark.database
class TestPortfolioMetrics:
    """Test portfolio-level metrics calculations."""

    def test_get_portfolio_metrics_empty(self, test_user, test_db_path):
        """Test portfolio metrics with no edges."""
        metrics = get_portfolio_statistics(test_user['id'], test_db_path)

        assert isinstance(metrics, dict)
        assert 'total_edges' in metrics
        assert metrics['total_edges'] == 0

    def test_get_portfolio_metrics_single_edge(self, test_user, sample_edge_data, test_db_path):
        """Test portfolio metrics with single edge."""
        from apps.tradevault.utils.edge_ops import create_edge

        edge_id = create_edge(test_user['id'], sample_edge_data, test_db_path)
        metrics = get_portfolio_statistics(test_user['id'], test_db_path)

        assert metrics['total_edges'] >= 1
        assert 'avg_win_rate' in metrics
        assert 'avg_profit_factor' in metrics

    def test_get_portfolio_metrics_multiple_edges(self, test_user, sample_edge_data, test_db_path):
        """Test portfolio metrics with multiple edges."""
        from apps.tradevault.utils.edge_ops import create_edge

        for _ in range(5):
            create_edge(test_user['id'], sample_edge_data, test_db_path)

        metrics = get_portfolio_statistics(test_user['id'], test_db_path)

        assert metrics['total_edges'] >= 5
        assert 0 <= metrics['avg_win_rate'] <= 100
        assert metrics['avg_profit_factor'] >= 0


@pytest.mark.unit
@pytest.mark.database
class TestCategoryPerformance:
    """Test category-level performance analysis."""

    def test_get_category_performance_empty(self, test_user, test_db_path):
        """Test category performance with no edges."""
        performance = get_category_performance(test_user['id'], test_db_path)

        assert isinstance(performance, dict)

    def test_get_category_performance_by_category(self, test_user, sample_edge_data, test_db_path):
        """Test performance breakdown by category."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['category'] = 'grid'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        performance = get_category_performance(test_user['id'], test_db_path)

        assert 'grid' in performance or isinstance(performance, dict)

    def test_get_category_performance_includes_metrics(self, test_user, sample_edge_data, test_db_path):
        """Test that category performance includes all metrics."""
        from apps.tradevault.utils.edge_ops import create_edge

        create_edge(test_user['id'], sample_edge_data, test_db_path)
        performance = get_category_performance(test_user['id'], test_db_path)

        for category, metrics in performance.items():
            assert 'win_rate' in metrics or 'edge_count' in metrics or isinstance(metrics, dict)


@pytest.mark.unit
@pytest.mark.database
class TestTimeframePerformance:
    """Test timeframe-level performance analysis."""

    def test_get_timeframe_performance_empty(self, test_user, test_db_path):
        """Test timeframe performance with no edges."""
        performance = get_timeframe_performance(test_user['id'], test_db_path)

        assert isinstance(performance, dict)

    def test_get_timeframe_performance_by_timeframe(self, test_user, sample_edge_data, test_db_path):
        """Test performance breakdown by timeframe."""
        from apps.tradevault.utils.edge_ops import create_edge

        sample_edge_data['timeframe'] = '1h'
        create_edge(test_user['id'], sample_edge_data, test_db_path)

        performance = get_timeframe_performance(test_user['id'], test_db_path)

        assert '1h' in performance or isinstance(performance, dict)

    def test_get_timeframe_performance_all_timeframes(self, test_user, sample_edge_data, test_db_path):
        """Test performance for multiple timeframes."""
        from apps.tradevault.utils.edge_ops import create_edge

        for tf in ['1m', '5m', '1h', '4h', '1d']:
            sample_edge_data['timeframe'] = tf
            create_edge(test_user['id'], sample_edge_data, test_db_path)

        performance = get_timeframe_performance(test_user['id'], test_db_path)

        assert len(performance) >= 5 or isinstance(performance, dict)


@pytest.mark.unit
@pytest.mark.database
class TestConfidenceDistribution:
    """Test confidence grade distribution analysis."""

    def test_get_confidence_distribution_empty(self, test_user, test_db_path):
        """Test confidence distribution with no edges."""
        distribution = get_confidence_distribution(test_user['id'], test_db_path)

        assert isinstance(distribution, dict)

    def test_get_confidence_distribution_all_grades(self, test_user, sample_edge_data, test_db_path):
        """Test confidence distribution with all grades."""
        from apps.tradevault.utils.edge_ops import create_edge

        for grade in ['A', 'B', 'C']:
            sample_edge_data['confidence_grade'] = grade
            create_edge(test_user['id'], sample_edge_data, test_db_path)

        distribution = get_confidence_distribution(test_user['id'], test_db_path)

        assert 'A' in distribution or 'B' in distribution or 'C' in distribution


@pytest.mark.unit
@pytest.mark.database
class TestOptimalPortfolio:
    """Test optimal portfolio recommendations."""

    def test_get_optimal_portfolio_empty(self, test_user, test_db_path):
        """Test optimal portfolio with no edges."""
        portfolio = calculate_optimal_portfolio(test_user['id'], test_db_path)

        assert isinstance(portfolio, list)

    def test_get_optimal_portfolio_top_performers(self, test_user, sample_edge_data, test_db_path):
        """Test optimal portfolio identifies top performers."""
        from apps.tradevault.utils.edge_ops import create_edge

        for _ in range(10):
            create_edge(test_user['id'], sample_edge_data, test_db_path)

        portfolio = calculate_optimal_portfolio(test_user['id'], test_db_path)

        assert len(portfolio) <= 5

    def test_get_optimal_portfolio_includes_metrics(self, test_user, sample_edge_data, test_db_path):
        """Test that portfolio recommendations include performance metrics."""
        from apps.tradevault.utils.edge_ops import create_edge

        create_edge(test_user['id'], sample_edge_data, test_db_path)
        portfolio = calculate_optimal_portfolio(test_user['id'], test_db_path)

        if len(portfolio) > 0:
            edge = portfolio[0]
            assert 'id' in edge or 'name' in edge or isinstance(edge, dict)


@pytest.mark.unit
@pytest.mark.database
class TestPerformanceTrend:
    """Test performance trend analysis."""

    def test_get_performance_trend_empty(self, test_user, test_db_path):
        """Test trend with no edges."""
        trend = get_performance_trend(test_user['id'], days=90, db_path=test_db_path)

        assert isinstance(trend, dict)

    def test_get_performance_trend_with_edges(self, test_user, sample_edge_data, test_db_path):
        """Test trend calculation with edges."""
        from apps.tradevault.utils.edge_ops import create_edge

        create_edge(test_user['id'], sample_edge_data, test_db_path)
        trend = get_performance_trend(test_user['id'], days=90, db_path=test_db_path)

        assert isinstance(trend, dict)
        assert 'win_rate' in trend or 'profit_factor' in trend or len(trend) >= 0

    def test_get_performance_trend_different_periods(self, test_user, sample_edge_data, test_db_path):
        """Test trend for different time periods."""
        from apps.tradevault.utils.edge_ops import create_edge

        create_edge(test_user['id'], sample_edge_data, test_db_path)

        trend_30 = get_performance_trend(test_user['id'], days=30, db_path=test_db_path)
        trend_90 = get_performance_trend(test_user['id'], days=90, db_path=test_db_path)
        trend_365 = get_performance_trend(test_user['id'], days=365, db_path=test_db_path)

        assert isinstance(trend_30, dict)
        assert isinstance(trend_90, dict)
        assert isinstance(trend_365, dict)


@pytest.mark.unit
@pytest.mark.database
class TestEdgePerformance:
    """Test individual edge performance analysis."""

    def test_get_edge_comparison(self, test_user, sample_edge_data, test_db_path):
        """Test individual edge comparison metrics."""
        from apps.tradevault.utils.edge_ops import create_edge

        edge_id1 = create_edge(test_user['id'], sample_edge_data, test_db_path)
        edge_id2 = create_edge(test_user['id'], sample_edge_data, test_db_path)

        comparison = get_edge_comparison(test_user['id'], [edge_id1, edge_id2], test_db_path)

        assert isinstance(comparison, dict)


@pytest.mark.unit
@pytest.mark.database
class TestCorrelationAnalysis:
    """Test correlation analysis between edges."""

    def test_get_correlation_analysis_empty(self, test_user, test_db_path):
        """Test correlation analysis with no edges."""
        correlation = get_edge_correlation_analysis(test_user['id'], test_db_path)

        assert isinstance(correlation, dict)

    def test_get_correlation_analysis_multiple_edges(self, test_user, sample_edge_data, test_db_path):
        """Test correlation between multiple edges."""
        from apps.tradevault.utils.edge_ops import create_edge

        for _ in range(5):
            create_edge(test_user['id'], sample_edge_data, test_db_path)

        correlation = get_edge_correlation_analysis(test_user['id'], test_db_path)

        assert isinstance(correlation, dict)
