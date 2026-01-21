"""
TradeVault Search page - Advanced search and filtering for edges, prompts, insights.
Compact layout with multi-filter search capabilities.
"""

import streamlit as st
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.ui_components import set_compact_layout, render_error_message
from apps.tradevault.utils.search import (
    search_edges, search_prompts, search_insights, global_search,
    search_by_category, search_by_timeframe, search_by_confidence,
    search_by_tag, search_by_performance, search_related_edges,
    get_search_history, get_search_suggestions
)


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'search_type' not in st.session_state:
        st.session_state.search_type = 'global'


def render_edge_result(edge: Dict):
    """Render edge search result."""
    confidence_icon = "🟢" if edge.get('confidence_grade') == 'A' else ("🟡" if edge.get('confidence_grade') == 'B' else "🔴")
    status_icon = "✅" if edge.get('status') == 'active' else "🧪"

    st.write(f"{confidence_icon} {status_icon} **{edge['title']}**")
    st.caption(f"{edge.get('category', 'N/A').upper()} • {edge.get('timeframe', 'N/A')}")

    if edge.get('description'):
        preview = edge['description'][:80] + "..." if len(edge['description']) > 80 else edge['description']
        st.caption(preview)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"W.R.: {edge.get('win_rate', 0):.1f}%")
    with col2:
        st.caption(f"P.F.: {edge.get('profit_factor', 0):.2f}")
    with col3:
        st.caption(f"n={edge.get('sample_size', 0)}")

    st.divider()


def render_prompt_result(prompt: Dict):
    """Render prompt search result."""
    favorite_icon = "⭐" if prompt.get('is_favorite') else "☆"

    st.write(f"{favorite_icon} **{prompt['title']}**")
    st.caption(f"Category: {prompt.get('category', 'N/A')} • Used: {prompt.get('usage_count', 0)} times")

    if prompt.get('content'):
        preview = prompt['content'][:80] + "..." if len(prompt['content']) > 80 else prompt['content']
        st.caption(f"📝 {preview}")

    st.divider()


def render_insight_result(insight: Dict):
    """Render insight search result."""
    status_icons = {
        'open': '🔵',
        'confirmed': '✅',
        'disputed': '❌'
    }
    status_icon = status_icons.get(insight.get('status', 'open'), '•')

    st.write(f"{status_icon} **{insight['title']}**")
    st.caption(f"{insight.get('category', 'N/A')} • {insight.get('date_observed', 'N/A')}")

    if insight.get('description'):
        preview = insight['description'][:80] + "..." if len(insight['description']) > 80 else insight['description']
        st.caption(preview)

    st.divider()


def render_global_search():
    """Render global search interface."""
    st.subheader("Global Search")

    query = st.text_input("Search all items", key="global_search_query",
                         placeholder="Search edges, prompts, insights...")

    col1, col2, col3 = st.columns(3)

    with col1:
        search_edges_cb = st.checkbox("🎯 Edges", value=True, key="search_edges_cb")

    with col2:
        search_prompts_cb = st.checkbox("📝 Prompts", value=True, key="search_prompts_cb")

    with col3:
        search_insights_cb = st.checkbox("💡 Insights", value=True, key="search_insights_cb")

    if st.button("🔍 Search", use_container_width=True):
        if query:
            try:
                user_id = st.session_state.user_id
                item_types = []

                if search_edges_cb:
                    item_types.append('edge')
                if search_prompts_cb:
                    item_types.append('prompt')
                if search_insights_cb:
                    item_types.append('insight')

                results = global_search(user_id, query, item_types=item_types, limit=100)

                # Display results by type
                if results.get('edges'):
                    st.write(f"**🎯 Edges ({len(results['edges'])})**")
                    for edge in results['edges']:
                        render_edge_result(edge)

                if results.get('prompts'):
                    st.write(f"**📝 Prompts ({len(results['prompts'])})**")
                    for prompt in results['prompts']:
                        render_prompt_result(prompt)

                if results.get('insights'):
                    st.write(f"**💡 Insights ({len(results['insights'])})**")
                    for insight in results['insights']:
                        render_insight_result(insight)

                if not any([results.get('edges'), results.get('prompts'), results.get('insights')]):
                    st.info("No results found")

            except Exception as e:
                render_error_message(f"Search failed: {str(e)}")


def render_advanced_search():
    """Render advanced search with filters."""
    st.subheader("Advanced Edge Search")

    col1, col2, col3 = st.columns(3)

    with col1:
        search_type = st.selectbox("Search by", options=["Category", "Timeframe", "Confidence", "Performance", "Tag"],
                                  key="adv_search_type")

    if search_type == "Category":
        category = st.selectbox("Select Category",
                               options=["Grid", "Bias", "Pivot", "MA-Trail", "Volatility", "Reversal"],
                               key="adv_category")

        min_wr = st.slider("Min Win Rate (%)", 0, 100, 50, key="adv_min_wr")

        if st.button("🔍 Search by Category", use_container_width=True):
            try:
                results = search_by_category(
                    st.session_state.user_id,
                    category.lower(),
                    min_win_rate=min_wr,
                    limit=100
                )

                if results:
                    st.write(f"Found {len(results)} edges")
                    for edge in results:
                        render_edge_result(edge)
                else:
                    st.info("No edges found for this category")

            except Exception as e:
                render_error_message(f"Search failed: {str(e)}")

    elif search_type == "Timeframe":
        timeframe = st.selectbox("Select Timeframe",
                                options=["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
                                key="adv_timeframe")

        if st.button("🔍 Search by Timeframe", use_container_width=True):
            try:
                results = search_by_timeframe(st.session_state.user_id, timeframe, limit=100)

                if results:
                    st.write(f"Found {len(results)} edges")
                    for edge in results:
                        render_edge_result(edge)
                else:
                    st.info("No edges found for this timeframe")

            except Exception as e:
                render_error_message(f"Search failed: {str(e)}")

    elif search_type == "Confidence":
        confidence = st.selectbox("Select Confidence Grade",
                                 options=["A", "B", "C"],
                                 key="adv_confidence")

        if st.button("🔍 Search by Confidence", use_container_width=True):
            try:
                results = search_by_confidence(st.session_state.user_id, confidence, limit=100)

                if results:
                    st.write(f"Found {len(results)} edges")
                    for edge in results:
                        render_edge_result(edge)
                else:
                    st.info("No edges found for this confidence grade")

            except Exception as e:
                render_error_message(f"Search failed: {str(e)}")

    elif search_type == "Performance":
        col1, col2, col3 = st.columns(3)

        with col1:
            min_wr = st.number_input("Min Win Rate (%)", value=50.0, step=0.5)

        with col2:
            min_pf = st.number_input("Min Profit Factor", value=1.0, step=0.1)

        with col3:
            min_sample = st.number_input("Min Sample Size", value=20, step=1)

        if st.button("🔍 Search by Performance", use_container_width=True):
            try:
                results = search_by_performance(
                    st.session_state.user_id,
                    min_win_rate=min_wr,
                    min_profit_factor=min_pf,
                    min_sample_size=min_sample,
                    limit=100
                )

                if results:
                    st.write(f"Found {len(results)} edges")
                    for edge in results:
                        render_edge_result(edge)
                else:
                    st.info("No edges meet these performance criteria")

            except Exception as e:
                render_error_message(f"Search failed: {str(e)}")

    elif search_type == "Tag":
        tag = st.text_input("Enter Tag", key="adv_tag", placeholder="e.g., support, resistance")

        if st.button("🔍 Search by Tag", use_container_width=True):
            if tag:
                try:
                    results = search_by_tag(st.session_state.user_id, tag.lower(), limit=100)

                    edges = results.get('edges', [])
                    prompts = results.get('prompts', [])

                    if edges:
                        st.write(f"**Edges ({len(edges)})**")
                        for edge in edges:
                            render_edge_result(edge)

                    if prompts:
                        st.write(f"**Prompts ({len(prompts)})**")
                        for prompt in prompts:
                            render_prompt_result(prompt)

                    if not edges and not prompts:
                        st.info("No results found for this tag")

                except Exception as e:
                    render_error_message(f"Search failed: {str(e)}")


def main():
    """Main search page."""
    init_session()
    set_compact_layout()

    st.title("🔍 Advanced Search")

    # Search type selector
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🌐 Global Search", use_container_width=True):
            st.session_state.search_type = 'global'
            st.rerun()

    with col2:
        if st.button("🎯 Advanced Filters", use_container_width=True):
            st.session_state.search_type = 'advanced'
            st.rerun()

    st.divider()

    # Render selected search type
    if st.session_state.search_type == 'global':
        render_global_search()
    else:
        render_advanced_search()

    st.divider()

    # Search history
    st.subheader("Search History")

    try:
        history = get_search_history(st.session_state.user_id, limit=10)

        if history:
            for query in history[:5]:
                if st.button(f"🔍 {query}", use_container_width=True):
                    st.session_state.search_query = query
                    st.rerun()
        else:
            st.caption("No search history yet")

    except Exception as e:
        pass  # Silently fail for history


if __name__ == "__main__":
    main()
