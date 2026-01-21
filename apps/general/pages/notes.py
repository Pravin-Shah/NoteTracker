"""
General App Notes page - Create, read, update, delete notes.
Compact layout with inline editing and quick filters.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.ui_components import (
    set_compact_layout, render_text_input, render_text_area,
    render_success_message, render_error_message, render_quick_filters
)
from apps.general.utils.note_ops import (
    create_note, get_note, update_note, delete_note, search_notes,
    pin_note, unpin_note, archive_note, unarchive_note,
    get_note_categories, get_note_tags, add_note_tag, remove_note_tag
)
from core.exceptions import ValidationError


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'editing_note_id' not in st.session_state:
        st.session_state.editing_note_id = None
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False


def render_create_form():
    """Render note creation form."""
    user_id = st.session_state.user_id

    st.subheader("Create New Note")

    col1, col2 = st.columns([2, 1])

    with col1:
        title = st.text_input("Title", key="new_note_title", label_visibility="collapsed", placeholder="Note title")

    with col2:
        importance = st.select_slider("Importance", options=[1, 2, 3, 4, 5], value=3, key="new_note_importance")

    category = st.selectbox("Category", options=["Personal", "Work", "Ideas", "Reference", "Other"],
                           key="new_note_category", label_visibility="collapsed")

    content = st.text_area("Content", height=120, key="new_note_content", placeholder="Note content")

    tags_input = st.text_input("Tags (comma-separated)", key="new_note_tags", label_visibility="collapsed")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Note", use_container_width=True):
            if not title.strip():
                render_error_message("Title is required")
                return

            try:
                note_id = create_note(user_id, {
                    'title': title,
                    'content': content,
                    'category': category.lower(),
                    'importance': importance
                })

                # Add tags
                if tags_input.strip():
                    tags = [t.strip().lower() for t in tags_input.split(',')]
                    for tag in tags:
                        if tag:
                            add_note_tag(note_id, tag)

                render_success_message("Note created successfully!")
                st.session_state.show_create_form = False
                st.session_state.search_query = ""
                st.rerun()

            except ValidationError as e:
                render_error_message(f"Validation error: {str(e)}")
            except Exception as e:
                render_error_message(f"Failed to create note: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_create_form = False
            st.rerun()


def render_note_card(note: Dict):
    """Render individual note card with actions."""
    user_id = st.session_state.user_id

    # Compact note display
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        importance_emoji = "⭐" * note.get('importance', 3)
        st.write(f"**{note['title']}** {importance_emoji}")
        if note.get('content'):
            preview = note['content'][:100] + "..." if len(note['content']) > 100 else note['content']
            st.caption(preview)

    # Action buttons
    with col2:
        action_buttons = []
        if st.button("✏️", key=f"edit_{note['id']}", help="Edit"):
            st.session_state.editing_note_id = note['id']
            st.rerun()
        if st.button("📌" if not note.get('is_pinned') else "📍", key=f"pin_{note['id']}", help="Toggle pin"):
            try:
                if note.get('is_pinned'):
                    unpin_note(user_id, note['id'])
                else:
                    pin_note(user_id, note['id'])
                render_success_message("Note updated")
                st.rerun()
            except Exception as e:
                render_error_message(str(e))

    with col3:
        if st.button("🗑️", key=f"delete_{note['id']}", help="Delete"):
            try:
                delete_note(user_id, note['id'])
                render_success_message("Note deleted")
                st.rerun()
            except Exception as e:
                render_error_message(str(e))

    # Tags and metadata
    if note.get('tags'):
        tags_display = " ".join([f"🏷️ {tag}" for tag in note['tags']])
        st.caption(tags_display)

    st.divider()


def render_edit_form(note: Dict):
    """Render note edit form."""
    user_id = st.session_state.user_id

    st.subheader(f"Edit Note: {note['title']}")

    title = st.text_input("Title", value=note['title'], key="edit_note_title")
    importance = st.select_slider("Importance", options=[1, 2, 3, 4, 5],
                                 value=note.get('importance', 3), key="edit_note_importance")
    category = st.selectbox("Category", options=["Personal", "Work", "Ideas", "Reference", "Other"],
                           index=0, key="edit_note_category")
    content = st.text_area("Content", value=note.get('content', ''), height=120, key="edit_note_content")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Changes", use_container_width=True):
            if not title.strip():
                render_error_message("Title is required")
                return

            try:
                update_note(user_id, note['id'], {
                    'title': title,
                    'content': content,
                    'category': category.lower(),
                    'importance': importance
                })
                render_success_message("Note updated successfully!")
                st.session_state.editing_note_id = None
                st.rerun()

            except ValidationError as e:
                render_error_message(f"Validation error: {str(e)}")
            except Exception as e:
                render_error_message(f"Failed to update note: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.editing_note_id = None
            st.rerun()

    st.divider()


def main():
    """Main notes page."""
    init_session()
    set_compact_layout()

    st.title("📝 Notes")

    # Search and filters
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input("Search notes", key="search_query", placeholder="Type to search...")

    with col2:
        if st.button("➕ New Note", use_container_width=True):
            st.session_state.show_create_form = not st.session_state.show_create_form
            st.rerun()

    # Category filter
    try:
        categories = get_note_categories(st.session_state.user_id)
        selected_category = st.selectbox("Filter by category", options=["All"] + categories,
                                        key="filter_category", label_visibility="collapsed")
    except Exception as e:
        selected_category = "All"

    st.divider()

    # Show create form if toggled
    if st.session_state.show_create_form:
        render_create_form()
        st.divider()

    # Show edit form if editing
    if st.session_state.editing_note_id:
        try:
            note = get_note(st.session_state.user_id, st.session_state.editing_note_id)
            if note:
                render_edit_form(note)
        except Exception as e:
            render_error_message(f"Failed to load note: {str(e)}")
            st.session_state.editing_note_id = None
        st.divider()

    # Search and display notes
    try:
        notes = search_notes(
            st.session_state.user_id,
            query=search_query,
            category=None if selected_category == "All" else selected_category.lower(),
            limit=100
        )

        if notes:
            st.write(f"Found {len(notes)} note(s)")
            for note in notes:
                render_note_card(note)
        else:
            st.info("No notes found. Create one to get started!")

    except Exception as e:
        render_error_message(f"Failed to load notes: {str(e)}")


if __name__ == "__main__":
    main()
