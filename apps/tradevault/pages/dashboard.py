"""
TradeVault Dashboard - Performance overview and quick trading stats.
Compact layout focused on edge performance and portfolio metrics.
"""

import streamlit as st
from typing import Dict
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.ui_components import set_compact_layout, render_stat_card, render_error_message
from apps.tradevault.utils.edge_ops import get_edge_stats, get_top_performers, get_edges_by_strategy
from apps.tradevault.utils.analytics import (
    get_portfolio_statistics, get_performance_report, get_category_performance,
    get_confidence_distribution
)


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'


def render_portfolio_metrics():
    """Render portfolio performance metrics."""
    user_id = st.session_state.user_id

    try:
        portfolio_stats = get_portfolio_statistics(user_id)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            render_stat_card(
                "Portfolio Win Rate",
                f"{portfolio_stats.get('avg_win_rate', 0):.1f}%",
                f"Trades: {portfolio_stats.get('total_sample_size', 0)}",
                color="📊"
            )

        with col2:
            render_stat_card(
                "Avg Profit Factor",
                f"{portfolio_stats.get('avg_profit_factor', 0):.2f}",
                f"Expectancy: {portfolio_stats.get('avg_expectancy', 0):.2f}",
                color="💰"
            )

        with col3:
            render_stat_card(
                "Robustness Score",
                f"{portfolio_stats.get('avg_robustness_score', 0):.1f}/100",
                "20%+ edges",
                color="🎯"
            )

        with col4:
            render_stat_card(
                "Risk Assessment",
                f"{portfolio_stats.get('avg_risk_level', 'N/A')}",
                "Based on RRR",
                color="⚠️"
            )

    except Exception as e:
        render_error_message(f"Failed to load portfolio metrics: {str(e)}")


def render_top_performers():
    """Render top performing edges."""
    user_id = st.session_state.user_id

    st.subheader("Top Performing Edges")

    try:
        top_edges = get_top_performers(user_id, limit=5)

        if top_edges:
            for edge in top_edges:
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    confidence_emoji = "🟢" if edge.get('confidence_grade') == 'A' else "🟡"
                    st.write(f"{confidence_emoji} **{edge['title']}**")
                    st.caption(f"Category: {edge.get('category', 'N/A')}")

                with col2:
                    st.metric("Win Rate", f"{edge.get('win_rate', 0):.1f}%")

                with col3:
                    st.metric("P.F.", f"{edge.get('profit_factor', 0):.2f}")

                st.divider()

        else:
            st.info("No edges yet. Create your first edge!")

    except Exception as e:
        render_error_message(f"Failed to load top edges: {str(e)}")


def render_category_breakdown():
    """Render performance by category."""
    user_id = st.session_state.user_id

    st.subheader("Performance by Category")

    try:
        category_perf = get_category_performance(user_id)

        if category_perf.get('categories'):
            for category, metrics in category_perf['categories'].items():
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.caption(f"**{category.title()}**")

                with col2:
                    st.caption(f"WR: {metrics.get('avg_win_rate', 0):.1f}%")

                with col3:
                    st.caption(f"P.F.: {metrics.get('avg_profit_factor', 0):.2f}")

                with col4:
                    st.caption(f"Count: {metrics.get('edge_count', 0)}")

        else:
            st.caption("No category data available")

    except Exception as e:
        render_error_message(f"Failed to load category data: {str(e)}")


def render_confidence_breakdown():
    """Render edges by confidence grade."""
    user_id = st.session_state.user_id

    st.subheader("Edges by Confidence")

    try:
        confidence_dist = get_confidence_distribution(user_id)

        col1, col2, col3 = st.columns(3)

        with col1:
            grade_a = confidence_dist.get('A', 0)
            st.metric("🟢 Grade A", f"{grade_a} edges")

        with col2:
            grade_b = confidence_dist.get('B', 0)
            st.metric("🟡 Grade B", f"{grade_b} edges")

        with col3:
            grade_c = confidence_dist.get('C', 0)
            st.metric("🔴 Grade C", f"{grade_c} edges")

    except Exception as e:
        render_error_message(f"Failed to load confidence data: {str(e)}")


def render_quick_actions():
    """Render quick action buttons."""
    st.subheader("Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("➕ New Edge", use_container_width=True):
            st.session_state.page = 'edges'
            st.rerun()

    with col2:
        if st.button("📝 New Prompt", use_container_width=True):
            st.session_state.page = 'prompts'
            st.rerun()

    with col3:
        if st.button("💡 New Insight", use_container_width=True):
            st.session_state.page = 'insights'
            st.rerun()

    with col4:
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.page = 'analytics'
            st.rerun()


def main():
    """Main TradeVault dashboard."""
    init_session()
    set_compact_layout()

    st.title("TradeVault Dashboard")

    # Portfolio metrics overview
    render_portfolio_metrics()

    st.divider()

    # Quick actions
    render_quick_actions()

    st.divider()

    # Top performers
    render_top_performers()

    st.divider()

    # Category breakdown
    col1, col2 = st.columns(2)

    with col1:
        render_category_breakdown()

    with col2:
        render_confidence_breakdown()

    st.divider()

    st.caption("💡 Use the sidebar to navigate to Edges, Prompts, Insights, or Analytics")


if __name__ == "__main__":
    main()
