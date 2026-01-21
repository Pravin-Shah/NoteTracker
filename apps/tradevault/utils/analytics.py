"""
Performance analytics for TradeVault App.
Edge performance calculations and analysis.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from core.db import execute_query
import logging

logger = logging.getLogger(__name__)


def calculate_edge_performance(
    win_rate: float,
    profit_factor: float,
    sample_size: int,
    avg_points: float = None,
    risk_reward_ratio: float = None, db_path: str = None) -> Dict:
    """
    Calculate comprehensive performance metrics for an edge.

    Args:
        win_rate: Win rate percentage (0-100)
        profit_factor: Profit factor (profit / loss)
        sample_size: Number of trades
        avg_points: Average profit per trade
        risk_reward_ratio: Risk/reward ratio

    Returns:
        Dict with calculated metrics and scores
    """
    metrics = {
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'sample_size': sample_size,
        'avg_points': avg_points,
        'risk_reward_ratio': risk_reward_ratio,
    }

    # Calculate derived metrics
    loss_rate = 100 - win_rate

    # Expectancy (average profit per trade)
    if profit_factor > 0:
        # Simplified: avg_win = avg_profit, avg_loss = avg_profit / profit_factor
        if avg_points:
            expectancy = (win_rate / 100 * avg_points) - (loss_rate / 100 * (avg_points / profit_factor if profit_factor > 0 else 0))
        else:
            expectancy = None
    else:
        expectancy = None

    metrics['expectancy'] = expectancy

    # Sample quality score (higher sample size = better)
    if sample_size >= 100:
        sample_quality = 100
    elif sample_size >= 50:
        sample_quality = 75
    elif sample_size >= 20:
        sample_quality = 50
    else:
        sample_quality = 25

    metrics['sample_quality'] = sample_quality

    # Robustness score (combination of win rate, profit factor, sample size)
    robustness = (
        (win_rate / 100 * 40) +  # 40% from win rate
        (min(profit_factor, 3) / 3 * 30) +  # 30% from profit factor (capped at 3)
        (sample_quality / 100 * 30)  # 30% from sample quality
    )

    metrics['robustness_score'] = robustness

    # Risk assessment
    if risk_reward_ratio and risk_reward_ratio > 0:
        if risk_reward_ratio < 1:
            risk_level = 'high'
        elif risk_reward_ratio < 1.5:
            risk_level = 'moderate'
        else:
            risk_level = 'low'
    else:
        risk_level = 'unknown'

    metrics['risk_level'] = risk_level

    return metrics


def get_edge_performance_percentile(user_id: int, edge_id: int, metric: str = 'win_rate', db_path: str = None) -> float:
    """
    Get percentile ranking for edge among user's edges.

    Args:
        user_id: User ID
        edge_id: Edge ID
        metric: Metric to rank by ('win_rate', 'profit_factor', 'sample_size')

    Returns:
        Percentile (0-100)
    """
    # Whitelist allowed metrics to prevent SQL injection
    allowed_metrics = {'win_rate', 'profit_factor', 'sample_size', 'avg_points', 'risk_reward_ratio'}
    if metric not in allowed_metrics:
        raise ValueError(f"Invalid metric: {metric}. Must be one of {allowed_metrics}")

    edge = execute_query(
        f"SELECT {metric} FROM tv_edges WHERE id = ? AND user_id = ?",
        (edge_id, user_id),
        db_path
    )

    if not edge:
        return 0

    edge_value = edge[0][metric]

    # Count edges with better value
    better_count = execute_query(
        f"SELECT COUNT(*) as count FROM tv_edges WHERE user_id = ? AND {metric} > ? AND status IN ('active', 'testing')",
        (user_id, edge_value),
        db_path
    )

    # Count total active edges
    total_count = execute_query(
        "SELECT COUNT(*) as count FROM tv_edges WHERE user_id = ? AND status IN ('active', 'testing')",
        (user_id,),
        db_path
    )

    total = total_count[0]['count'] if total_count else 1
    better = better_count[0]['count'] if better_count else 0

    percentile = ((total - better) / total) * 100 if total > 0 else 0
    return round(percentile, 2)


def get_portfolio_statistics(user_id: int, status: str = 'active', db_path: str = None) -> Dict:
    """
    Get portfolio statistics across all edges.

    Args:
        user_id: User ID
        status: Filter by status ('active', 'testing', all)

    Returns:
        Stats dict
    """
    sql = "SELECT * FROM tv_edges WHERE user_id = ?"
    params = [user_id]

    if status:
        sql += " AND status = ?"
        params.append(status)

    results = execute_query(sql, tuple(params), db_path)
    edges = [dict(row) for row in results]

    if not edges:
        return {
            'total_edges': 0,
            'avg_win_rate': 0,
            'avg_profit_factor': 0,
            'total_trades': 0,
        }

    win_rates = [e['win_rate'] or 0 for e in edges if e['win_rate']]
    profit_factors = [e['profit_factor'] or 0 for e in edges if e['profit_factor']]
    sample_sizes = [e['sample_size'] or 0 for e in edges if e['sample_size']]

    avg_wr = sum(win_rates) / len(win_rates) if win_rates else 0
    avg_pf = sum(profit_factors) / len(profit_factors) if profit_factors else 0
    total_trades = sum(sample_sizes) if sample_sizes else 0

    return {
        'total_edges': len(edges),
        'avg_win_rate': round(avg_wr, 2),
        'avg_profit_factor': round(avg_pf, 2),
        'total_trades': total_trades,
        'best_win_rate': max(win_rates) if win_rates else 0,
        'best_profit_factor': max(profit_factors) if profit_factors else 0,
        'edges_with_high_sample': len([s for s in sample_sizes if s >= 100]),
    }


def get_category_performance(user_id: int, db_path: str = None) -> Dict[str, Dict]:
    """
    Get performance metrics grouped by category.

    Args:
        user_id: User ID

    Returns:
        Dict with category as key and metrics as value
    """
    categories = execute_query(
        "SELECT DISTINCT category FROM tv_edges WHERE user_id = ? AND status IN ('active', 'testing') ORDER BY category",
        (user_id,),
        db_path
    )

    category_stats = {}

    for cat_row in categories:
        category = cat_row['category']

        edges = execute_query(
            "SELECT * FROM tv_edges WHERE user_id = ? AND category = ? AND status IN ('active', 'testing')",
            (user_id, category),
            db_path
        )

        if not edges:
            continue

        edges_list = [dict(e) for e in edges]

        win_rates = [e['win_rate'] or 0 for e in edges_list if e['win_rate']]
        profit_factors = [e['profit_factor'] or 0 for e in edges_list if e['profit_factor']]
        sample_sizes = [e['sample_size'] or 0 for e in edges_list if e['sample_size']]

        category_stats[category] = {
            'count': len(edges_list),
            'avg_win_rate': round(sum(win_rates) / len(win_rates), 2) if win_rates else 0,
            'avg_profit_factor': round(sum(profit_factors) / len(profit_factors), 2) if profit_factors else 0,
            'total_trades': sum(sample_sizes),
        }

    return category_stats


def get_timeframe_performance(user_id: int, db_path: str = None) -> Dict[str, Dict]:
    """
    Get performance metrics grouped by timeframe.

    Args:
        user_id: User ID

    Returns:
        Dict with timeframe as key and metrics as value
    """
    timeframes = execute_query(
        "SELECT DISTINCT timeframe FROM tv_edges WHERE user_id = ? AND status IN ('active', 'testing') ORDER BY timeframe",
        (user_id,),
        db_path
    )

    timeframe_stats = {}

    for tf_row in timeframes:
        timeframe = tf_row['timeframe']

        edges = execute_query(
            "SELECT * FROM tv_edges WHERE user_id = ? AND timeframe = ? AND status IN ('active', 'testing')",
            (user_id, timeframe),
            db_path
        )

        if not edges:
            continue

        edges_list = [dict(e) for e in edges]

        win_rates = [e['win_rate'] or 0 for e in edges_list if e['win_rate']]
        profit_factors = [e['profit_factor'] or 0 for e in edges_list if e['profit_factor']]

        timeframe_stats[timeframe] = {
            'count': len(edges_list),
            'avg_win_rate': round(sum(win_rates) / len(win_rates), 2) if win_rates else 0,
            'avg_profit_factor': round(sum(profit_factors) / len(profit_factors), 2) if profit_factors else 0,
        }

    return timeframe_stats


def get_confidence_distribution(user_id: int, db_path: str = None) -> Dict[str, int]:
    """
    Get distribution of confidence grades.

    Args:
        user_id: User ID

    Returns:
        Dict with grade as key and count as value
    """
    results = execute_query(
        "SELECT confidence_grade, COUNT(*) as count FROM tv_edges WHERE user_id = ? AND status IN ('active', 'testing') GROUP BY confidence_grade",
        (user_id,),
        db_path
    )

    return {row['confidence_grade']: row['count'] for row in results} if results else {}


def get_edge_correlation_analysis(user_id: int, db_path: str = None) -> Dict:
    """
    Analyze relationships between edges.

    Args:
        user_id: User ID

    Returns:
        Analysis dict with relationship data
    """
    relationships = execute_query("""
        SELECT relationship_type, COUNT(*) as count
        FROM tv_edge_relationships
        WHERE edge_id_1 IN (SELECT id FROM tv_edges WHERE user_id = ?)
        GROUP BY relationship_type
    """, (user_id,), db_path)

    return {row['relationship_type']: row['count'] for row in relationships} if relationships else {}


def get_performance_trend(user_id: int, days: int = 90, db_path: str = None) -> List[Dict]:
    """
    Get performance trend over time.

    Args:
        user_id: User ID
        days: Number of days to analyze

    Returns:
        List of daily performance data
    """
    start_date = (date.today() - timedelta(days=days)).isoformat()

    results = execute_query("""
        SELECT
            DATE(created_date) as date,
            COUNT(*) as edges_added,
            AVG(win_rate) as avg_win_rate,
            AVG(profit_factor) as avg_profit_factor
        FROM tv_edges
        WHERE user_id = ? AND created_date >= ?
        GROUP BY DATE(created_date)
        ORDER BY date ASC
    """, (user_id, start_date), db_path)

    return [dict(row) for row in results] if results else []


def get_edge_comparison(user_id: int, edge_ids: List[int], db_path: str = None) -> Dict:
    """
    Compare multiple edges side-by-side.

    Args:
        user_id: User ID
        edge_ids: List of edge IDs to compare

    Returns:
        Comparison dict
    """
    comparison = {}

    for edge_id in edge_ids:
        edge = execute_query(
            "SELECT id, title, category, win_rate, profit_factor, sample_size, confidence_grade FROM tv_edges WHERE id = ? AND user_id = ?",
            (edge_id, user_id),
            db_path
        )

        if edge:
            edge_data = dict(edge[0])
            comparison[edge_id] = edge_data

    return comparison


def calculate_optimal_portfolio(user_id: int, db_path: str = None) -> Dict:
    """
    Suggest optimal portfolio based on edge metrics.

    Args:
        user_id: User ID

    Returns:
        Portfolio recommendation dict
    """
    # Get top performers
    top_edges = execute_query("""
        SELECT id, title, category, win_rate, profit_factor, confidence_grade, sample_size
        FROM tv_edges
        WHERE user_id = ? AND status = 'active'
        ORDER BY
            confidence_grade ASC,
            win_rate DESC,
            profit_factor DESC,
            sample_size DESC
        LIMIT 5
    """, (user_id,), db_path)

    recommended_edges = [dict(e) for e in top_edges] if top_edges else []

    # Calculate diversification by category
    categories_used = set(e['category'] for e in recommended_edges)

    return {
        'recommended_edges': recommended_edges,
        'count': len(recommended_edges),
        'categories_covered': list(categories_used),
        'avg_confidence_grade': sum(1 for e in recommended_edges if e['confidence_grade'] == 'A') / len(recommended_edges) * 100 if recommended_edges else 0,
    }


def get_performance_report(user_id: int, db_path: str = None) -> Dict:
    """
    Generate comprehensive performance report.

    Args:
        user_id: User ID

    Returns:
        Complete performance report
    """
    return {
        'portfolio_stats': get_portfolio_statistics(user_id),
        'category_performance': get_category_performance(user_id),
        'timeframe_performance': get_timeframe_performance(user_id),
        'confidence_distribution': get_confidence_distribution(user_id),
        'edge_relationships': get_edge_correlation_analysis(user_id),
        'performance_trend': get_performance_trend(user_id, days=30),  # Last 30 days
        'portfolio_recommendation': calculate_optimal_portfolio(user_id),
    }
