"""
General App Search page - Unified search across notes, tasks, and events.
Compact layout with result grouping and filtering.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List
import sys
import os


from core.ui_components import (
    set_compact_layout, render_success_message, render_error_message
)
from apps.general.utils.search import (
    search_notes, search_tasks, search_events, global_search,
    save_search_history, get_search_history, get_search_suggestions
)


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []


def render_search_bar():
    """Render search input with suggestions."""
    user_id = st.session_state.user_id

    col1, col2 = st.columns([4, 1])

    with col1:
        query = st.text_input("Search across all items", key="search_query",
                             placeholder="Search notes, tasks, events...")

    with col2:
        search_button = st.button("🔍 Search", use_container_width=True)

    return query, search_button


def render_search_suggestions(prefix: str):
    """Render search suggestions dropdown."""
    if not prefix or len(prefix) < 2:
        return

    user_id = st.session_state.user_id

    try:
        suggestions = get_search_suggestions(user_id, prefix, limit=5)

        if any(suggestions.values()):
            st.write("**Suggestions:**")

            if suggestions.get('notes'):
                st.caption("📝 Notes")
                for note in suggestions['notes']:
                    st.caption(f"  • {note}")

            if suggestions.get('tasks'):
                st.caption("✅ Tasks")
                for task in suggestions['tasks']:
                    st.caption(f"  • {task}")

            if suggestions.get('tags'):
                st.caption("🏷️ Tags")
                for tag in suggestions['tags']:
                    st.caption(f"  • {tag}")

    except Exception as e:
        pass  # Silently fail for suggestions


def render_note_result(note: Dict):
    """Render note search result."""
    importance_emoji = "⭐" * note.get('importance', 3)
    st.write(f"📝 **{note['title']}** {importance_emoji}")

    if note.get('content'):
        preview = note['content'][:100] + "..." if len(note['content']) > 100 else note['content']
        st.caption(preview)

    metadata = []
    if note.get('category'):
        metadata.append(f"Category: {note['category']}")
    if note.get('created_date'):
        metadata.append(f"Created: {note['created_date']}")

    if metadata:
        st.caption(" • ".join(metadata))

    st.divider()


def render_task_result(task: Dict):
    """Render task search result."""
    status_icons = {
        'pending': '⏳',
        'in-progress': '🔄',
        'completed': '✅',
        'cancelled': '❌'
    }
    status_icon = status_icons.get(task.get('status'), '•')

    priority_emoji = {
        5: '🔴',
        4: '🟠',
        3: '🟡',
        2: '🟢',
        1: '⚪'
    }
    priority_icon = priority_emoji.get(task.get('priority', 3), '•')

    st.write(f"{status_icon} **{task['title']}** {priority_icon}")

    if task.get('description'):
        preview = task['description'][:100] + "..." if len(task['description']) > 100 else task['description']
        st.caption(preview)

    metadata = []
    if task.get('category'):
        metadata.append(f"Category: {task['category']}")
    if task.get('due_date'):
        metadata.append(f"Due: {task['due_date']}")

    if metadata:
        st.caption(" • ".join(metadata))

    st.divider()


def render_event_result(event: Dict):
    """Render event search result."""
    st.write(f"📅 **{event['title']}**")

    if event.get('description'):
        preview = event['description'][:100] + "..." if len(event['description']) > 100 else event['description']
        st.caption(preview)

    metadata = []
    if event.get('start_date'):
        metadata.append(f"Date: {event['start_date']}")
    if event.get('start_time'):
        metadata.append(f"Time: {event['start_time']}")
    if event.get('location'):
        metadata.append(f"Location: {event['location']}")

    if metadata:
        st.caption(" • ".join(metadata))

    st.divider()


def render_search_results(results: Dict):
    """Render grouped search results."""
    if not any(results.values()):
        st.info("No results found")
        return

    # Notes results
    if results.get('notes'):
        st.subheader(f"📝 Notes ({len(results['notes'])})")
        for note in results['notes']:
            render_note_result(note)

    # Tasks results
    if results.get('tasks'):
        st.subheader(f"✅ Tasks ({len(results['tasks'])})")
        for task in results['tasks']:
            render_task_result(task)

    # Events results
    if results.get('events'):
        st.subheader(f"📅 Events ({len(results['events'])})")
        for event in results['events']:
            render_event_result(event)


def render_search_history():
    """Render recent search history."""
    user_id = st.session_state.user_id

    try:
        history = get_search_history(user_id, limit=10)

        if history:
            st.subheader("Recent Searches")

            # Group history into columns for compact display
            cols = st.columns(3)
            for i, query in enumerate(history[:9]):
                with cols[i % 3]:
                    if st.button(f"🔍 {query}", use_container_width=True, key=f"history_{i}"):
                        st.session_state.search_query = query
                        st.rerun()

    except Exception as e:
        pass  # Silently fail for history


def render_filter_options():
    """Render filter options."""
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_type = st.multiselect(
            "Filter by type",
            options=["Notes", "Tasks", "Events"],
            default=["Notes", "Tasks", "Events"],
            key="search_filter_type"
        )

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            options=["Relevance", "Date (Newest)", "Date (Oldest)"],
            key="search_sort"
        )

    with col3:
        limit = st.selectbox(
            "Results per type",
            options=[10, 25, 50, 100],
            value=25,
            key="search_limit"
        )

    return filter_type, sort_by, limit


def main():
    """Main search page."""
    init_session()
    set_compact_layout()

    st.title("🔍 Search")

    # Search bar
    query, search_button = render_search_bar()

    st.divider()

    # Filter options
    filter_types, sort_by, limit = render_filter_options()

    st.divider()

    # Show suggestions or history
    if query and len(query) >= 2:
        render_search_suggestions(query)
        st.divider()

    # Perform search
    if search_button and query:
        try:
            user_id = st.session_state.user_id

            # Determine which types to search
            search_map = {
                "Notes": search_notes,
                "Tasks": search_tasks,
                "Events": search_events
            }

            results = {
                'notes': [],
                'tasks': [],
                'events': []
            }

            # Search selected types
            if "Notes" in filter_types:
                results['notes'] = search_notes(user_id, query, limit=limit)

            if "Tasks" in filter_types:
                results['tasks'] = search_tasks(user_id, query, limit=limit)

            if "Events" in filter_types:
                results['events'] = search_events(user_id, query, limit=limit)

            # Save to history
            save_search_history(user_id, query)

            # Display results
            render_search_results(results)

        except Exception as e:
            render_error_message(f"Search failed: {str(e)}")

    elif not search_button:
        # Show recent search history
        render_search_history()


if __name__ == "__main__":
    main()
