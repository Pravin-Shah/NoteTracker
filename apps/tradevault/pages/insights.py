"""
TradeVault Insights page - Log and manage trading insights.
Compact layout with status and confidence tracking.
"""

import streamlit as st
from datetime import datetime, date
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.ui_components import set_compact_layout, render_error_message, render_success_message
from apps.tradevault.utils.insight_ops import (
    create_insight, get_insight, update_insight, delete_insight, search_insights,
    get_today_insights, get_recent_insights, update_insight_status,
    update_insight_confidence, get_insights_by_category, get_insight_categories,
    get_insight_stats, bulk_update_status, bulk_delete_insights
)
from core.exceptions import ValidationError


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False
    if 'insight_status_filter' not in st.session_state:
        st.session_state.insight_status_filter = 'all'


def render_create_form():
    """Render insight creation form."""
    user_id = st.session_state.user_id

    st.subheader("Log New Insight")

    title = st.text_input("Insight Title", key="new_insight_title",
                         label_visibility="collapsed", placeholder="What did you observe?")

    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox("Category",
                               options=["Price Action", "Volume", "Correlation", "Divergence", "Support/Resistance", "Pattern", "Other"],
                               key="new_insight_category", label_visibility="collapsed")

    with col2:
        date_observed = st.date_input("Date Observed", value=date.today(), key="new_insight_date")

    description = st.text_area("Description", height=120, key="new_insight_description",
                              placeholder="Detailed observation and context...")

    col1, col2 = st.columns(2)

    with col1:
        status = st.selectbox("Status",
                             options=["Open", "Confirmed", "Disputed"],
                             key="new_insight_status", label_visibility="collapsed")

    with col2:
        confidence = st.selectbox("Confidence",
                                options=["Hypothesis", "Weak", "Moderate", "Strong"],
                                key="new_insight_confidence", label_visibility="collapsed")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Log Insight", use_container_width=True):
            if not title.strip():
                render_error_message("Title is required")
                return

            try:
                insight_data = {
                    'title': title,
                    'description': description,
                    'category': category.lower().replace('/', '_'),
                    'date_observed': date_observed.isoformat(),
                    'status': status.lower(),
                    'confidence_level': confidence.lower()
                }

                insight_id = create_insight(user_id, insight_data)
                render_success_message(f"Insight logged! (ID: {insight_id})")
                st.session_state.show_create_form = False
                st.rerun()

            except ValidationError as e:
                render_error_message(f"Validation error: {str(e)}")
            except Exception as e:
                render_error_message(f"Failed to log insight: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_create_form = False
            st.rerun()


def render_insight_card(insight: Dict):
    """Render individual insight card."""
    user_id = st.session_state.user_id

    # Status styling
    status_icons = {
        'open': '🔵',
        'confirmed': '✅',
        'disputed': '❌'
    }
    status_icon = status_icons.get(insight.get('status', 'open'), '•')

    # Confidence styling
    confidence_icons = {
        'hypothesis': '❓',
        'weak': '⚠️',
        'moderate': '💡',
        'strong': '⭐'
    }
    confidence_icon = confidence_icons.get(insight.get('confidence_level', 'weak'), '•')

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.write(f"{status_icon} **{insight['title']}**")
        st.caption(f"📅 {insight.get('date_observed', 'N/A')} • {insight.get('category', 'N/A').replace('_', '/')}")

    with col2:
        st.write(f"{confidence_icon}")

    with col3:
        if st.button("✏️", key=f"edit_insight_{insight['id']}", help="Edit"):
            st.info("Edit feature coming soon")

    with col4:
        if st.button("🗑️", key=f"delete_insight_{insight['id']}", help="Delete"):
            try:
                delete_insight(user_id, insight['id'])
                render_success_message("Insight deleted")
                st.rerun()
            except Exception as e:
                render_error_message(str(e))

    # Description preview
    if insight.get('description'):
        preview = insight['description'][:80] + "..." if len(insight['description']) > 80 else insight['description']
        st.caption(f"📝 {preview}")

    # Status change buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if insight.get('status') != 'open':
            if st.button("🔵 Mark Open", key=f"status_open_{insight['id']}", use_container_width=True):
                try:
                    update_insight_status(user_id, insight['id'], 'open')
                    render_success_message("Status updated")
                    st.rerun()
                except Exception as e:
                    render_error_message(str(e))

    with col2:
        if insight.get('status') != 'confirmed':
            if st.button("✅ Confirm", key=f"status_confirmed_{insight['id']}", use_container_width=True):
                try:
                    update_insight_status(user_id, insight['id'], 'confirmed')
                    render_success_message("Status updated")
                    st.rerun()
                except Exception as e:
                    render_error_message(str(e))

    with col3:
        if insight.get('status') != 'disputed':
            if st.button("❌ Dispute", key=f"status_disputed_{insight['id']}", use_container_width=True):
                try:
                    update_insight_status(user_id, insight['id'], 'disputed')
                    render_success_message("Status updated")
                    st.rerun()
                except Exception as e:
                    render_error_message(str(e))

    st.divider()


def render_stats_overview():
    """Render insight statistics."""
    user_id = st.session_state.user_id

    try:
        stats = get_insight_stats(user_id)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total", stats.get('total', 0))

        with col2:
            st.metric("Open", stats.get('by_status', {}).get('open', 0))

        with col3:
            st.metric("Confirmed", stats.get('by_status', {}).get('confirmed', 0))

        with col4:
            st.metric("Disputed", stats.get('by_status', {}).get('disputed', 0))

    except Exception as e:
        pass  # Silently fail for stats


def main():
    """Main insights page."""
    init_session()
    set_compact_layout()

    st.title("💡 Insights")

    # Stats overview
    render_stats_overview()

    st.divider()

    # Search and create
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input("Search insights", key="search_insights",
                                    placeholder="Type to search...")

    with col2:
        if st.button("➕ Log Insight", use_container_width=True):
            st.session_state.show_create_form = not st.session_state.show_create_form
            st.rerun()

    # Filter buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("All", use_container_width=True):
            st.session_state.insight_status_filter = 'all'
            st.rerun()

    with col2:
        if st.button("🔵 Open", use_container_width=True):
            st.session_state.insight_status_filter = 'open'
            st.rerun()

    with col3:
        if st.button("✅ Confirmed", use_container_width=True):
            st.session_state.insight_status_filter = 'confirmed'
            st.rerun()

    with col4:
        if st.button("📅 Today", use_container_width=True):
            st.session_state.insight_status_filter = 'today'
            st.rerun()

    st.divider()

    # Show create form if toggled
    if st.session_state.show_create_form:
        render_create_form()
        st.divider()

    # Display insights
    try:
        user_id = st.session_state.user_id

        if st.session_state.insight_status_filter == 'today':
            insights = get_today_insights(user_id)
        elif st.session_state.insight_status_filter == 'all':
            insights = search_insights(user_id, query=search_query, limit=100)
        else:
            insights = search_insights(user_id, query=search_query, status=st.session_state.insight_status_filter, limit=100)

        if insights:
            st.write(f"Found {len(insights)} insight(s)")
            for insight in insights:
                render_insight_card(insight)
        else:
            st.info("No insights found. Log your first market observation!")

    except Exception as e:
        render_error_message(f"Failed to load insights: {str(e)}")


if __name__ == "__main__":
    main()
