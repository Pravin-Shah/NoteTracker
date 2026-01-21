"""
TradeVault Analytics page - Performance analysis and portfolio optimization.
Compact layout with charts and performance metrics.
"""

import streamlit as st
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.ui_components import set_compact_layout, render_error_message
from apps.tradevault.utils.analytics import (
    get_performance_report, get_portfolio_statistics, get_category_performance,
    get_timeframe_performance, get_confidence_distribution, get_edge_comparison,
    calculate_optimal_portfolio, get_performance_trend
)


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'analytics_tab' not in st.session_state:
        st.session_state.analytics_tab = 'Overview'


def render_performance_overview():
    """Render portfolio performance overview."""
    user_id = st.session_state.user_id

    st.subheader("Portfolio Overview")

    try:
        report = get_performance_report(user_id)

        portfolio = report.get('portfolio_stats', {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Avg Win Rate", f"{portfolio.get('avg_win_rate', 0):.1f}%")

        with col2:
            st.metric("Avg P.F.", f"{portfolio.get('avg_profit_factor', 0):.2f}")

        with col3:
            st.metric("Avg Expectancy", f"{portfolio.get('avg_expectancy', 0):.2f}")

        with col4:
            st.metric("Robustness", f"{portfolio.get('avg_robustness_score', 0):.1f}/100")

        st.divider()

        # Breakdown
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Sample Quality Distribution**")
            sample_quality = portfolio.get('sample_quality_distribution', {})
            for quality, count in sample_quality.items():
                st.caption(f"{quality}: {count} edges")

        with col2:
            st.write("**Risk Assessment**")
            risk_dist = portfolio.get('risk_level_distribution', {})
            for risk, count in risk_dist.items():
                st.caption(f"{risk}: {count} edges")

    except Exception as e:
        render_error_message(f"Failed to load portfolio overview: {str(e)}")


def render_category_performance():
    """Render performance by category."""
    st.subheader("Performance by Category")

    user_id = st.session_state.user_id

    try:
        category_perf = get_category_performance(user_id)

        if category_perf.get('categories'):
            # Create comparison table
            for category, metrics in category_perf['categories'].items():
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    st.caption(f"**{category.upper()}**")

                with col2:
                    st.caption(f"W.R.: {metrics.get('avg_win_rate', 0):.1f}%")

                with col3:
                    st.caption(f"P.F.: {metrics.get('avg_profit_factor', 0):.2f}")

                with col4:
                    st.caption(f"Robustness: {metrics.get('avg_robustness_score', 0):.1f}")

                with col5:
                    st.caption(f"Edges: {metrics.get('edge_count', 0)}")

        else:
            st.caption("No category data available")

    except Exception as e:
        render_error_message(f"Failed to load category performance: {str(e)}")


def render_timeframe_performance():
    """Render performance by timeframe."""
    st.subheader("Performance by Timeframe")

    user_id = st.session_state.user_id

    try:
        timeframe_perf = get_timeframe_performance(user_id)

        if timeframe_perf.get('timeframes'):
            for timeframe, metrics in timeframe_perf['timeframes'].items():
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    st.caption(f"**{timeframe}**")

                with col2:
                    st.caption(f"W.R.: {metrics.get('avg_win_rate', 0):.1f}%")

                with col3:
                    st.caption(f"P.F.: {metrics.get('avg_profit_factor', 0):.2f}")

                with col4:
                    st.caption(f"Robustness: {metrics.get('avg_robustness_score', 0):.1f}")

                with col5:
                    st.caption(f"Edges: {metrics.get('edge_count', 0)}")

        else:
            st.caption("No timeframe data available")

    except Exception as e:
        render_error_message(f"Failed to load timeframe performance: {str(e)}")


def render_confidence_analysis():
    """Render confidence grade analysis."""
    st.subheader("Confidence Grade Analysis")

    user_id = st.session_state.user_id

    try:
        dist = get_confidence_distribution(user_id)

        col1, col2, col3 = st.columns(3)

        with col1:
            grade_a = dist.get('A', 0)
            st.metric("🟢 Grade A", f"{grade_a} edges", "Highest confidence")

        with col2:
            grade_b = dist.get('B', 0)
            st.metric("🟡 Grade B", f"{grade_b} edges", "Medium confidence")

        with col3:
            grade_c = dist.get('C', 0)
            st.metric("🔴 Grade C", f"{grade_c} edges", "Lower confidence")

    except Exception as e:
        render_error_message(f"Failed to load confidence analysis: {str(e)}")


def render_optimal_portfolio():
    """Render portfolio optimization recommendations."""
    st.subheader("Optimal Portfolio Recommendation")

    user_id = st.session_state.user_id

    try:
        recommendation = calculate_optimal_portfolio(user_id)

        if recommendation.get('recommended_edges'):
            st.write("**Top Recommended Edges:**")

            for i, edge in enumerate(recommendation['recommended_edges'][:5], 1):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.caption(f"{i}. {edge.get('title', 'N/A')}")

                with col2:
                    st.caption(f"W.R.: {edge.get('win_rate', 0):.1f}%")

                with col3:
                    st.caption(f"P.F.: {edge.get('profit_factor', 0):.2f}")

                with col4:
                    st.caption(f"Grade: {edge.get('confidence_grade', 'N/A')}")

            st.divider()

            # Diversification analysis
            st.write("**Diversification Analysis:**")

            if recommendation.get('diversification_analysis'):
                analysis = recommendation['diversification_analysis']

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.caption(f"Categories: {analysis.get('category_count', 0)}")

                with col2:
                    st.caption(f"Timeframes: {analysis.get('timeframe_count', 0)}")

                with col3:
                    st.caption(f"Instruments: {analysis.get('instrument_count', 0)}")

        else:
            st.caption("No edges available for recommendation")

    except Exception as e:
        render_error_message(f"Failed to load portfolio recommendation: {str(e)}")


def render_trend_analysis():
    """Render performance trend analysis."""
    st.subheader("Performance Trend (Last 90 Days)")

    user_id = st.session_state.user_id

    try:
        trend_data = get_performance_trend(user_id, days=90)

        if trend_data.get('daily_metrics'):
            st.write(f"Total entries: {len(trend_data['daily_metrics'])}")

            # Simple trend display
            col1, col2, col3 = st.columns(3)

            with col1:
                st.caption(f"Avg W.R.: {trend_data.get('average_win_rate', 0):.1f}%")

            with col2:
                st.caption(f"Avg P.F.: {trend_data.get('average_profit_factor', 0):.2f}")

            with col3:
                st.caption(f"Peak Robustness: {trend_data.get('peak_robustness_score', 0):.1f}")

            st.caption("📊 Detailed trend charts coming soon")

        else:
            st.caption("Not enough data for trend analysis")

    except Exception as e:
        render_error_message(f"Failed to load trend analysis: {str(e)}")


def main():
    """Main analytics page."""
    init_session()
    set_compact_layout()

    st.title("📊 Analytics")

    # Tab navigation
    col1, col2, col3, col4 = st.columns(4)

    tabs = ["Overview", "Categories", "Timeframes", "Confidence"]
    icons = ["📈", "📊", "⏱️", "🎯"]

    for i, (tab, icon) in enumerate(zip(tabs, icons)):
        with [col1, col2, col3, col4][i]:
            if st.button(f"{icon} {tab}", use_container_width=True):
                st.session_state.analytics_tab = tab
                st.rerun()

    st.divider()

    # Render selected tab
    if st.session_state.analytics_tab == "Overview":
        render_performance_overview()
        st.divider()
        render_optimal_portfolio()
        st.divider()
        render_trend_analysis()

    elif st.session_state.analytics_tab == "Categories":
        render_category_performance()

    elif st.session_state.analytics_tab == "Timeframes":
        render_timeframe_performance()

    elif st.session_state.analytics_tab == "Confidence":
        render_confidence_analysis()


if __name__ == "__main__":
    main()
