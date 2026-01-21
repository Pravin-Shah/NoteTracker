"""
General App Tasks page - Create, manage, and track tasks.
Compact layout with status filtering, priority levels, and due date management.
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.ui_components import (
    set_compact_layout, render_text_input, render_text_area,
    render_success_message, render_error_message
)
from apps.general.utils.task_ops import (
    create_task, get_task, update_task, complete_task, start_task, delete_task,
    search_tasks, get_overdue_tasks, get_tasks_due_today, get_upcoming_tasks,
    get_task_categories, get_task_tags, add_task_tag, create_task_reminder,
    add_task_checklist
)
from core.exceptions import ValidationError


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'editing_task_id' not in st.session_state:
        st.session_state.editing_task_id = None
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False
    if 'task_status_filter' not in st.session_state:
        st.session_state.task_status_filter = 'All'


def render_create_form():
    """Render task creation form."""
    user_id = st.session_state.user_id

    st.subheader("Create New Task")

    title = st.text_input("Task Title", key="new_task_title", label_visibility="collapsed",
                         placeholder="What needs to be done?")

    col1, col2 = st.columns([2, 1])

    with col1:
        category = st.selectbox("Category", options=["Personal", "Work", "Financial", "Health"],
                               key="new_task_category", label_visibility="collapsed")

    with col2:
        priority = st.select_slider("Priority", options=[1, 2, 3, 4, 5], value=3, key="new_task_priority")

    col1, col2 = st.columns(2)

    with col1:
        due_date = st.date_input("Due Date (optional)", key="new_task_due_date")

    with col2:
        due_time = st.time_input("Due Time (optional)", key="new_task_due_time", value=None)

    description = st.text_area("Description (optional)", height=80, key="new_task_description",
                              placeholder="Add details...")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Create Task", use_container_width=True):
            if not title.strip():
                render_error_message("Task title is required")
                return

            try:
                task_data = {
                    'title': title,
                    'description': description,
                    'category': category.lower(),
                    'priority': priority,
                    'due_date': due_date.isoformat() if due_date else None,
                    'due_time': due_time.strftime("%H:%M") if due_time else None,
                    'status': 'pending'
                }

                task_id = create_task(user_id, task_data)
                render_success_message(f"Task created! (ID: {task_id})")
                st.session_state.show_create_form = False
                st.rerun()

            except ValidationError as e:
                render_error_message(f"Validation error: {str(e)}")
            except Exception as e:
                render_error_message(f"Failed to create task: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_create_form = False
            st.rerun()


def render_task_card(task: Dict):
    """Render individual task card."""
    user_id = st.session_state.user_id

    # Status styling
    status_icons = {
        'pending': '⏳',
        'in-progress': '🔄',
        'completed': '✅',
        'cancelled': '❌'
    }
    status_icon = status_icons.get(task.get('status'), '•')

    # Priority styling
    priority_emoji = {
        5: '🔴',
        4: '🟠',
        3: '🟡',
        2: '🟢',
        1: '⚪'
    }
    priority_icon = priority_emoji.get(task.get('priority', 3), '•')

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.write(f"{status_icon} **{task['title']}** {priority_icon}")
        if task.get('due_date'):
            st.caption(f"📅 {task['due_date']}")

    with col2:
        if task['status'] == 'pending':
            if st.button("▶️", key=f"start_{task['id']}", help="Start"):
                try:
                    start_task(user_id, task['id'])
                    render_success_message("Task started")
                    st.rerun()
                except Exception as e:
                    render_error_message(str(e))

    with col3:
        if task['status'] != 'completed':
            if st.button("✓", key=f"complete_{task['id']}", help="Complete"):
                try:
                    complete_task(user_id, task['id'])
                    render_success_message("Task completed!")
                    st.rerun()
                except Exception as e:
                    render_error_message(str(e))

    with col4:
        if st.button("🗑️", key=f"delete_task_{task['id']}", help="Delete"):
            try:
                delete_task(user_id, task['id'])
                render_success_message("Task deleted")
                st.rerun()
            except Exception as e:
                render_error_message(str(e))

    # Description preview
    if task.get('description'):
        preview = task['description'][:80] + "..." if len(task['description']) > 80 else task['description']
        st.caption(preview)

    st.divider()


def render_quick_shortcuts():
    """Render quick shortcuts for common views."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("⏳ Pending", use_container_width=True):
            st.session_state.task_status_filter = 'pending'
            st.rerun()

    with col2:
        if st.button("🔄 In Progress", use_container_width=True):
            st.session_state.task_status_filter = 'in-progress'
            st.rerun()

    with col3:
        if st.button("📅 Due Today", use_container_width=True):
            st.session_state.task_status_filter = 'today'
            st.rerun()

    with col4:
        if st.button("🚨 Overdue", use_container_width=True):
            st.session_state.task_status_filter = 'overdue'
            st.rerun()


def main():
    """Main tasks page."""
    init_session()
    set_compact_layout()

    st.title("✅ Tasks")

    # Search and filters
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input("Search tasks", key="search_tasks", placeholder="Type to search...")

    with col2:
        if st.button("➕ New Task", use_container_width=True):
            st.session_state.show_create_form = not st.session_state.show_create_form
            st.rerun()

    st.divider()

    # Quick shortcuts
    render_quick_shortcuts()

    st.divider()

    # Show create form if toggled
    if st.session_state.show_create_form:
        render_create_form()
        st.divider()

    # Get and display tasks
    try:
        user_id = st.session_state.user_id

        if st.session_state.task_status_filter == 'today':
            tasks = get_tasks_due_today(user_id)
        elif st.session_state.task_status_filter == 'overdue':
            tasks = get_overdue_tasks(user_id)
        elif st.session_state.task_status_filter == 'All':
            tasks = search_tasks(user_id, query=search_query)
        else:
            tasks = search_tasks(user_id, query=search_query, status=st.session_state.task_status_filter)

        if tasks:
            st.write(f"Found {len(tasks)} task(s)")
            for task in tasks:
                render_task_card(task)
        else:
            st.info("No tasks found. Create one to get started!")

    except Exception as e:
        render_error_message(f"Failed to load tasks: {str(e)}")


if __name__ == "__main__":
    main()
