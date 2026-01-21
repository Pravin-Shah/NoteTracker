"""
NoteTracker Dashboard App - Unified home page with quick access to all features.
Compact layout with global search and quick add functionality.
"""

import streamlit as st
from datetime import date
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ui_components import set_compact_layout, render_stat_card, render_success_message, render_error_message
from apps.general.utils.task_ops import get_task_stats, get_overdue_tasks, get_tasks_due_today
from apps.general.utils.note_ops import get_note_stats
from apps.general.utils.calendar_ops import get_event_stats, get_today_events
from apps.tradevault.utils.edge_ops import get_edge_stats
from apps.tradevault.utils.analytics import get_portfolio_statistics
from apps.general.utils.search import global_search as gen_global_search
from apps.tradevault.utils.search import global_search as tv_global_search


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'current_app' not in st.session_state:
        st.session_state.current_app = 'home'


def render_app_selector():
    """Render app selector buttons."""
    st.subheader("Select App")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📱 General App", use_container_width=True):
            st.switch_page("pages/notes")

    with col2:
        if st.button("💹 TradeVault", use_container_width=True):
            st.switch_page("pages/edges")

    with col3:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_app = 'settings'
            st.rerun()


def render_quick_stats():
    """Render quick statistics from all apps."""
    st.subheader("Quick Overview")

    user_id = st.session_state.user_id

    col1, col2, col3, col4, col5 = st.columns(5)

    try:
        # General App stats
        note_stats = get_note_stats(user_id)
        with col1:
            render_stat_card("📝 Notes", str(note_stats['total']), "All notes", color="📘")

        task_stats = get_task_stats(user_id)
        with col2:
            render_stat_card("✅ Tasks", str(task_stats['total']), f"Due: {task_stats['pending']}", color="📗")

        event_stats = get_event_stats(user_id)
        with col3:
            render_stat_card("📅 Events", str(event_stats['total']), f"Upcoming: {event_stats['upcoming']}", color="📙")

        # TradeVault stats
        edge_stats = get_edge_stats(user_id)
        with col4:
            render_stat_card("🎯 Edges", str(edge_stats['total']), f"Active: {edge_stats['active']}", color="📊")

        portfolio = get_portfolio_statistics(user_id)
        with col5:
            render_stat_card("📈 Avg W.R.", f"{portfolio.get('avg_win_rate', 0):.1f}%",
                            f"P.F.: {portfolio.get('avg_profit_factor', 0):.2f}", color="📊")

    except Exception as e:
        render_error_message(f"Failed to load stats: {str(e)}")


def render_global_search():
    """Render global search across all apps."""
    st.subheader("Global Search")

    query = st.text_input("Search all items", key="home_global_search",
                         placeholder="Search notes, tasks, edges, prompts...")

    col1, col2 = st.columns([3, 1])

    with col1:
        search_type = st.selectbox("Search in",
                                  options=["All", "General App", "TradeVault"],
                                  key="home_search_type")

    with col2:
        st.write("")  # Spacer for alignment

    if st.button("🔍 Search", use_container_width=True):
        if not query:
            render_error_message("Enter a search query")
            return

        try:
            user_id = st.session_state.user_id

            if search_type in ["All", "General App"]:
                st.write("**General App Results**")
                gen_results = gen_global_search(user_id, query, limit=50)

                if gen_results.get('notes'):
                    st.caption(f"📝 Notes ({len(gen_results['notes'])})")
                    for note in gen_results['notes'][:3]:
                        st.caption(f"  • {note['title']}")

                if gen_results.get('tasks'):
                    st.caption(f"✅ Tasks ({len(gen_results['tasks'])})")
                    for task in gen_results['tasks'][:3]:
                        st.caption(f"  • {task['title']}")

                if gen_results.get('events'):
                    st.caption(f"📅 Events ({len(gen_results['events'])})")
                    for event in gen_results['events'][:3]:
                        st.caption(f"  • {event['title']}")

            if search_type in ["All", "TradeVault"]:
                st.write("**TradeVault Results**")
                tv_results = tv_global_search(user_id, query, limit=50)

                if tv_results.get('edges'):
                    st.caption(f"🎯 Edges ({len(tv_results['edges'])})")
                    for edge in tv_results['edges'][:3]:
                        st.caption(f"  • {edge['title']}")

                if tv_results.get('prompts'):
                    st.caption(f"📝 Prompts ({len(tv_results['prompts'])})")
                    for prompt in tv_results['prompts'][:3]:
                        st.caption(f"  • {prompt['title']}")

        except Exception as e:
            render_error_message(f"Search failed: {str(e)}")


def render_quick_actions():
    """Render quick action buttons."""
    st.subheader("Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Add Note", use_container_width=True):
            st.info("Redirecting to General App...")
            st.switch_page("pages/notes")

    with col2:
        if st.button("✅ Add Task", use_container_width=True):
            st.info("Redirecting to General App...")
            st.switch_page("pages/tasks")

    with col3:
        if st.button("🎯 Add Edge", use_container_width=True):
            st.info("Redirecting to TradeVault...")
            st.switch_page("pages/edges")

    with col4:
        if st.button("💡 Log Insight", use_container_width=True):
            st.info("Redirecting to TradeVault...")
            st.switch_page("pages/insights")


def render_today_summary():
    """Render today's summary section."""
    st.subheader("Today's Summary")

    user_id = st.session_state.user_id

    col1, col2 = st.columns(2)

    try:
        with col1:
            st.write("**Tasks Due Today**")
            tasks = get_tasks_due_today(user_id)
            if tasks:
                for task in tasks[:5]:
                    priority_emoji = "🔴" if task['priority'] >= 4 else "🟢"
                    st.caption(f"{priority_emoji} {task['title']}")
            else:
                st.caption("No tasks due today")

        with col2:
            st.write("**Events Today**")
            events = get_today_events(user_id)
            if events:
                for event in events[:5]:
                    time_str = event.get('start_time', 'All day')
                    st.caption(f"🕐 {time_str} - {event['title']}")
            else:
                st.caption("No events today")

    except Exception as e:
        render_error_message(f"Failed to load today's summary: {str(e)}")


def render_alerts():
    """Render alerts section."""
    user_id = st.session_state.user_id

    try:
        # Overdue tasks
        overdue_tasks = get_overdue_tasks(user_id)
        if overdue_tasks:
            st.warning(f"⚠️ {len(overdue_tasks)} Overdue Task(s)", icon="⚠️")
            for task in overdue_tasks[:2]:
                st.caption(f"🔴 {task['title']} (Due: {task['due_date']})")

    except Exception as e:
        pass  # Silently fail for alerts


def main():
    """Main dashboard home page."""
    init_session()
    set_compact_layout()

    st.title("🏠 NoteTracker Dashboard")

    # Alert section
    render_alerts()

    st.divider()

    # Quick stats
    render_quick_stats()

    st.divider()

    # App selector
    render_app_selector()

    st.divider()

    # Global search
    render_global_search()

    st.divider()

    # Quick actions
    render_quick_actions()

    st.divider()

    # Today's summary
    render_today_summary()

    st.divider()

    st.caption("Welcome to NoteTracker! Use the sidebar to navigate between General App, TradeVault, and Settings.")


if __name__ == "__main__":
    main()
