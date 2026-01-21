"""
General App Dashboard - Quick overview of notes, tasks, and events.
Compact layout focused on content and quick actions.
"""

import streamlit as st
from datetime import date, timedelta
from typing import Dict
import sys
import os

# Add parent directory to path

from core.ui_components import (
    set_compact_layout, render_stat_card, render_item_card,
    render_success_message, render_error_message, render_quick_filters
)
from apps.general.utils.note_ops import get_note_stats, search_notes
from apps.general.utils.task_ops import get_task_stats, get_overdue_tasks, get_tasks_due_today, get_upcoming_tasks
from apps.general.utils.calendar_ops import get_today_events, get_upcoming_events, get_event_stats
from apps.general.utils.reminder_engine import get_reminder_stats


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1  # Default to user 1 for demo
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'


def render_quick_add():
    """Render quick add section with compact interface."""
    st.subheader("Quick Add")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 Add Note", use_container_width=True):
            st.session_state.page = 'notes'
            st.rerun()

    with col2:
        if st.button("✅ Add Task", use_container_width=True):
            st.session_state.page = 'tasks'
            st.rerun()

    with col3:
        if st.button("📅 Add Event", use_container_width=True):
            st.session_state.page = 'calendar'
            st.rerun()


def render_stats_overview():
    """Render statistics overview with compact cards."""
    user_id = st.session_state.user_id

    col1, col2, col3 = st.columns(3)

    try:
        # Notes stats
        note_stats = get_note_stats(user_id)
        with col1:
            render_stat_card(
                "📝 Notes",
                str(note_stats['total']),
                f"Pinned: {note_stats['pinned']}",
                color="📘"
            )

        # Tasks stats
        task_stats = get_task_stats(user_id)
        with col2:
            render_stat_card(
                "✅ Tasks",
                str(task_stats['total']),
                f"Overdue: {task_stats['overdue']}",
                color="📗"
            )

        # Events stats
        event_stats = get_event_stats(user_id)
        with col3:
            render_stat_card(
                "📅 Events",
                str(event_stats['total']),
                f"Upcoming: {event_stats['upcoming']}",
                color="📙"
            )

    except Exception as e:
        render_error_message(f"Failed to load statistics: {str(e)}")


def render_today_section():
    """Render today's items section."""
    user_id = st.session_state.user_id

    st.subheader("Today")
    col1, col2 = st.columns(2)

    try:
        # Today's tasks
        with col1:
            st.write("**Tasks Due**")
            tasks = get_tasks_due_today(user_id)
            if tasks:
                for task in tasks[:5]:  # Show top 5
                    priority_emoji = "🔴" if task['priority'] >= 4 else "🟢"
                    st.caption(f"{priority_emoji} {task['title']}")
            else:
                st.caption("No tasks due today")

        # Today's events
        with col2:
            st.write("**Events**")
            events = get_today_events(user_id)
            if events:
                for event in events[:5]:  # Show top 5
                    st.caption(f"🕐 {event.get('start_time', '')} - {event['title']}")
            else:
                st.caption("No events today")

    except Exception as e:
        render_error_message(f"Failed to load today's items: {str(e)}")


def render_upcoming_section():
    """Render upcoming items section."""
    user_id = st.session_state.user_id

    st.subheader("Upcoming (Next 7 Days)")
    col1, col2 = st.columns(2)

    try:
        # Upcoming tasks
        with col1:
            st.write("**Tasks**")
            tasks = get_upcoming_tasks(user_id, days=7)
            if tasks:
                for task in tasks[:5]:  # Show top 5
                    priority_emoji = "🔴" if task['priority'] >= 4 else "🟢"
                    st.caption(f"{priority_emoji} {task['due_date']} - {task['title']}")
            else:
                st.caption("No upcoming tasks")

        # Upcoming events
        with col2:
            st.write("**Events**")
            events = get_upcoming_events(user_id, days=7)
            if events:
                for event in events[:5]:  # Show top 5
                    st.caption(f"📅 {event['start_date']} - {event['title']}")
            else:
                st.caption("No upcoming events")

    except Exception as e:
        render_error_message(f"Failed to load upcoming items: {str(e)}")


def render_overdue_section():
    """Render overdue items section if any exist."""
    user_id = st.session_state.user_id

    try:
        overdue_tasks = get_overdue_tasks(user_id)

        if overdue_tasks:
            st.warning(f"⚠️ {len(overdue_tasks)} Overdue Task(s)", icon="⚠️")
            for task in overdue_tasks[:3]:  # Show top 3
                st.caption(f"🔴 {task['due_date']} - {task['title']}")

    except Exception as e:
        render_error_message(f"Failed to load overdue tasks: {str(e)}")


def render_reminders_section():
    """Render pending reminders section."""
    user_id = st.session_state.user_id

    try:
        reminder_stats = get_reminder_stats(user_id)

        if reminder_stats['pending'] > 0:
            st.info(f"🔔 {reminder_stats['pending']} Pending Reminder(s)")

    except Exception as e:
        render_error_message(f"Failed to load reminder stats: {str(e)}")


def main():
    """Main dashboard page."""
    init_session()
    set_compact_layout()

    st.title("General App Dashboard")

    # Quick add section
    render_quick_add()

    st.divider()

    # Statistics overview
    render_stats_overview()

    st.divider()

    # Reminders alert
    render_reminders_section()

    # Overdue alert
    render_overdue_section()

    st.divider()

    # Today section
    render_today_section()

    st.divider()

    # Upcoming section
    render_upcoming_section()

    st.divider()

    # Footer with quick links
    st.caption("💡 Use the sidebar to navigate to Notes, Tasks, Calendar, or Search")


if __name__ == "__main__":
    main()
