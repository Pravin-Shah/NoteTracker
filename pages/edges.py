"""
TradeVault Edges page - Create, manage, and analyze trading edges.
Compact layout with edge creation form, search, and performance metrics display.
"""

import streamlit as st
from typing import Dict, List
import sys
import os


from core.ui_components import set_compact_layout, render_error_message, render_success_message
from apps.tradevault.utils.edge_ops import (
    create_edge, get_edge, update_edge, delete_edge, search_edges,
    get_top_performers, get_edges_by_strategy, get_edge_categories, get_edge_tags,
    add_edge_tag, remove_edge_tag, link_edges, unlink_edges
)
from apps.tradevault.utils.analytics import calculate_edge_performance
from core.exceptions import ValidationError


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False
    if 'editing_edge_id' not in st.session_state:
        st.session_state.editing_edge_id = None
    if 'edge_filter' not in st.session_state:
        st.session_state.edge_filter = 'all'


def render_create_form():
    """Render edge creation form."""
    user_id = st.session_state.user_id

    st.subheader("Create New Edge")

    title = st.text_input("Edge Title", key="new_edge_title", label_visibility="collapsed",
                         placeholder="e.g., Grid Support at 4H")

    col1, col2, col3 = st.columns(3)

    with col1:
        category = st.selectbox("Category",
                               options=["Grid", "Bias", "Pivot", "MA-Trail", "Volatility", "Reversal"],
                               key="new_edge_category", label_visibility="collapsed")

    with col2:
        timeframe = st.selectbox("Timeframe",
                               options=["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
                               key="new_edge_timeframe", label_visibility="collapsed")

    with col3:
        market_condition = st.selectbox("Market Condition",
                                       options=["Bull", "Bear", "Range", "Any"],
                                       key="new_edge_market", label_visibility="collapsed")

    col1, col2, col3 = st.columns(3)

    with col1:
        instrument = st.text_input("Instrument", key="new_edge_instrument",
                                  label_visibility="collapsed", placeholder="EURUSD")

    with col2:
        confidence = st.selectbox("Confidence Grade",
                                 options=["A", "B", "C"],
                                 key="new_edge_confidence", label_visibility="collapsed")

    with col3:
        status = st.selectbox("Status",
                             options=["Active", "Testing", "Deprecated", "Hibernated"],
                             key="new_edge_status", label_visibility="collapsed")

    # Performance metrics
    st.write("**Performance Metrics**")

    col1, col2, col3 = st.columns(3)

    with col1:
        win_rate = st.number_input("Win Rate (%)", min_value=0.0, max_value=100.0,
                                   value=50.0, step=0.1, key="new_edge_wr")

    with col2:
        profit_factor = st.number_input("Profit Factor", min_value=0.0,
                                        value=1.0, step=0.05, key="new_edge_pf")

    with col3:
        sample_size = st.number_input("Sample Size", min_value=1,
                                      value=30, step=1, key="new_edge_sample")

    description = st.text_area("Description", height=100, key="new_edge_description",
                              placeholder="How the edge works, conditions, etc.")

    observations = st.text_area("Observations", height=80, key="new_edge_observations",
                               placeholder="Market observations, notes, etc.")

    why_it_works = st.text_area("Why It Works", height=80, key="new_edge_why",
                               placeholder="Technical explanation, theory, etc.")

    tags_input = st.text_input("Tags (comma-separated)", key="new_edge_tags",
                              label_visibility="collapsed", placeholder="tag1, tag2, tag3")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Create Edge", use_container_width=True):
            if not title.strip():
                render_error_message("Edge title is required")
                return

            try:
                edge_data = {
                    'title': title,
                    'category': category.lower(),
                    'timeframe': timeframe,
                    'market_condition': market_condition.lower(),
                    'instrument': instrument,
                    'confidence_grade': confidence,
                    'status': status.lower(),
                    'win_rate': win_rate,
                    'profit_factor': profit_factor,
                    'sample_size': sample_size,
                    'description': description,
                    'observations': observations,
                    'why_it_works': why_it_works,
                    'strategy': category.lower()
                }

                edge_id = create_edge(user_id, edge_data)

                # Add tags
                if tags_input.strip():
                    tags = [t.strip().lower() for t in tags_input.split(',')]
                    for tag in tags:
                        if tag:
                            add_edge_tag(edge_id, tag)

                render_success_message(f"Edge created! (ID: {edge_id})")
                st.session_state.show_create_form = False
                st.rerun()

            except ValidationError as e:
                render_error_message(f"Validation error: {str(e)}")
            except Exception as e:
                render_error_message(f"Failed to create edge: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_create_form = False
            st.rerun()


def render_edge_card(edge: Dict):
    """Render individual edge card."""
    user_id = st.session_state.user_id

    # Confidence styling
    confidence_icon = "🟢" if edge.get('confidence_grade') == 'A' else ("🟡" if edge.get('confidence_grade') == 'B' else "🔴")
    status_icon = "✅" if edge.get('status') == 'active' else ("🧪" if edge.get('status') == 'testing' else "❌")

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.write(f"{confidence_icon} {status_icon} **{edge['title']}**")
        st.caption(f"{edge.get('category', 'N/A').upper()} • {edge.get('timeframe', 'N/A')} • {edge.get('market_condition', 'N/A')}")

    with col2:
        st.metric("Win Rate", f"{edge.get('win_rate', 0):.1f}%", delta=f"n={edge.get('sample_size', 0)}")

    with col3:
        st.metric("Profit Factor", f"{edge.get('profit_factor', 0):.2f}")

    with col4:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✏️", key=f"edit_edge_{edge['id']}", help="Edit"):
                st.info("Edit feature coming soon")

        with col_b:
            if st.button("🗑️", key=f"delete_edge_{edge['id']}", help="Delete"):
                try:
                    delete_edge(user_id, edge['id'])
                    render_success_message("Edge deleted")
                    st.rerun()
                except Exception as e:
                    render_error_message(str(e))

    # Description preview
    if edge.get('description'):
        preview = edge['description'][:60] + "..." if len(edge['description']) > 60 else edge['description']
        st.caption(f"📝 {preview}")

    # Tags
    if edge.get('tags'):
        tags_display = " ".join([f"🏷️ {tag}" for tag in edge['tags'][:3]])
        st.caption(tags_display)

    st.divider()


def render_filter_options():
    """Render edge filter options."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("All Edges", use_container_width=True):
            st.session_state.edge_filter = 'all'
            st.rerun()

    with col2:
        if st.button("⭐ Top Performers", use_container_width=True):
            st.session_state.edge_filter = 'top'
            st.rerun()

    with col3:
        if st.button("✅ Active", use_container_width=True):
            st.session_state.edge_filter = 'active'
            st.rerun()

    with col4:
        if st.button("🧪 Testing", use_container_width=True):
            st.session_state.edge_filter = 'testing'
            st.rerun()


def main():
    """Main edges page."""
    init_session()
    set_compact_layout()

    st.title("🎯 Edges")

    # Search and create
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input("Search edges", key="search_edges",
                                    placeholder="Type to search...")

    with col2:
        if st.button("➕ New Edge", use_container_width=True):
            st.session_state.show_create_form = not st.session_state.show_create_form
            st.rerun()

    st.divider()

    # Show create form if toggled
    if st.session_state.show_create_form:
        render_create_form()
        st.divider()

    # Filter options
    render_filter_options()

    st.divider()

    # Display edges
    try:
        user_id = st.session_state.user_id

        if st.session_state.edge_filter == 'top':
            edges = get_top_performers(user_id, limit=20)
        elif st.session_state.edge_filter == 'active':
            edges = search_edges(user_id, query=search_query)
            edges = [e for e in edges if e.get('status') == 'active']
        elif st.session_state.edge_filter == 'testing':
            edges = search_edges(user_id, query=search_query)
            edges = [e for e in edges if e.get('status') == 'testing']
        else:
            edges = search_edges(user_id, query=search_query, limit=100)

        if edges:
            st.write(f"Found {len(edges)} edge(s)")
            for edge in edges:
                render_edge_card(edge)
        else:
            st.info("No edges found. Create your first edge!")

    except Exception as e:
        render_error_message(f"Failed to load edges: {str(e)}")


if __name__ == "__main__":
    main()
