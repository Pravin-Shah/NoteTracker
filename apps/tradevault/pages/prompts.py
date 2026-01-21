"""
TradeVault Prompts page - Manage AI prompts with versioning.
Compact layout with version history and usage tracking.
"""

import streamlit as st
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.ui_components import set_compact_layout, render_error_message, render_success_message
from apps.tradevault.utils.prompt_ops import (
    create_prompt, get_prompt, update_prompt, delete_prompt, search_prompts,
    get_favorite_prompts, use_prompt, toggle_favorite, add_prompt_tag,
    remove_prompt_tag, get_prompt_version_history, restore_prompt_version,
    get_prompt_categories, get_prompt_tags
)
from core.exceptions import ValidationError


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False
    if 'selected_prompt_id' not in st.session_state:
        st.session_state.selected_prompt_id = None
    if 'show_history' not in st.session_state:
        st.session_state.show_history = False


def render_create_form():
    """Render prompt creation form."""
    user_id = st.session_state.user_id

    st.subheader("Create New Prompt")

    title = st.text_input("Prompt Title", key="new_prompt_title",
                         label_visibility="collapsed", placeholder="Descriptive title")

    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox("Category",
                               options=["Analysis", "Market", "Trading", "Research", "General"],
                               key="new_prompt_category", label_visibility="collapsed")

    with col2:
        is_favorite = st.checkbox("⭐ Mark as Favorite", key="new_prompt_favorite")

    content = st.text_area("Prompt Content", height=150, key="new_prompt_content",
                          placeholder="Your prompt template here...")

    use_case = st.text_area("Use Case", height=80, key="new_prompt_use_case",
                           placeholder="When and how to use this prompt...")

    tags_input = st.text_input("Tags (comma-separated)", key="new_prompt_tags",
                              label_visibility="collapsed", placeholder="tag1, tag2, tag3")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Create Prompt", use_container_width=True):
            if not title.strip() or not content.strip():
                render_error_message("Title and content are required")
                return

            try:
                prompt_data = {
                    'title': title,
                    'category': category.lower(),
                    'content': content,
                    'use_case': use_case,
                    'is_favorite': 1 if is_favorite else 0
                }

                prompt_id = create_prompt(user_id, prompt_data)

                # Add tags
                if tags_input.strip():
                    tags = [t.strip().lower() for t in tags_input.split(',')]
                    for tag in tags:
                        if tag:
                            add_prompt_tag(prompt_id, tag)

                render_success_message(f"Prompt created! (ID: {prompt_id})")
                st.session_state.show_create_form = False
                st.rerun()

            except ValidationError as e:
                render_error_message(f"Validation error: {str(e)}")
            except Exception as e:
                render_error_message(f"Failed to create prompt: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_create_form = False
            st.rerun()


def render_prompt_card(prompt: Dict):
    """Render individual prompt card."""
    user_id = st.session_state.user_id

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        favorite_icon = "⭐" if prompt.get('is_favorite') else "☆"
        st.write(f"{favorite_icon} **{prompt['title']}**")
        st.caption(f"Category: {prompt.get('category', 'N/A')} • Used: {prompt.get('usage_count', 0)} times")

    with col2:
        if st.button("📋", key=f"copy_prompt_{prompt['id']}", help="Copy"):
            st.info("Copy feature coming soon")

    with col3:
        if st.button("🗑️", key=f"delete_prompt_{prompt['id']}", help="Delete"):
            try:
                delete_prompt(user_id, prompt['id'])
                render_success_message("Prompt deleted")
                st.rerun()
            except Exception as e:
                render_error_message(str(e))

    # Content preview
    content_preview = prompt.get('content', '')[:80] + "..." if len(prompt.get('content', '')) > 80 else prompt.get('content', '')
    st.caption(f"📝 {content_preview}")

    # Tags
    if prompt.get('tags'):
        tags_display = " ".join([f"🏷️ {tag}" for tag in prompt['tags'][:3]])
        st.caption(tags_display)

    # Interactive buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✏️ Edit", key=f"edit_prompt_{prompt['id']}", use_container_width=True):
            st.session_state.selected_prompt_id = prompt['id']
            st.rerun()

    with col2:
        if st.button("📜 History", key=f"history_prompt_{prompt['id']}", use_container_width=True):
            st.session_state.selected_prompt_id = prompt['id']
            st.session_state.show_history = True
            st.rerun()

    with col3:
        favorite_btn_text = "☆ Unfavorite" if prompt.get('is_favorite') else "⭐ Favorite"
        if st.button(favorite_btn_text, key=f"fav_prompt_{prompt['id']}", use_container_width=True):
            try:
                toggle_favorite(user_id, prompt['id'])
                render_success_message("Favorite toggled")
                st.rerun()
            except Exception as e:
                render_error_message(str(e))

    st.divider()


def render_version_history(prompt_id: int):
    """Render prompt version history."""
    user_id = st.session_state.user_id

    st.subheader("Version History")

    try:
        history = get_prompt_version_history(user_id, prompt_id)

        if history:
            for i, version in enumerate(history):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Version {version.get('version', 'N/A')}**")
                    st.caption(f"Created: {version.get('created_date', 'N/A')}")

                with col2:
                    if st.button("👁️ View", key=f"view_v_{prompt_id}_{i}", use_container_width=True):
                        st.write(version.get('content', ''))

                with col3:
                    if i > 0:  # Can't restore current version
                        if st.button("↩️ Restore", key=f"restore_v_{prompt_id}_{i}", use_container_width=True):
                            try:
                                restore_prompt_version(user_id, prompt_id, version.get('version'))
                                render_success_message("Version restored!")
                                st.rerun()
                            except Exception as e:
                                render_error_message(str(e))

                st.divider()

        else:
            st.caption("No version history available")

    except Exception as e:
        render_error_message(f"Failed to load history: {str(e)}")


def main():
    """Main prompts page."""
    init_session()
    set_compact_layout()

    st.title("📝 Prompts")

    # Search and create
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input("Search prompts", key="search_prompts",
                                    placeholder="Type to search...")

    with col2:
        if st.button("➕ New Prompt", use_container_width=True):
            st.session_state.show_create_form = not st.session_state.show_create_form
            st.rerun()

    # Filter buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("All Prompts", use_container_width=True):
            st.session_state.search_query = ""
            st.rerun()

    with col2:
        if st.button("⭐ Favorites", use_container_width=True):
            st.session_state.search_query = "favorite"
            st.rerun()

    with col3:
        if st.button("🔄 Recently Used", use_container_width=True):
            st.session_state.search_query = "recent"
            st.rerun()

    st.divider()

    # Show create form if toggled
    if st.session_state.show_create_form:
        render_create_form()
        st.divider()

    # Show version history if selected
    if st.session_state.show_history and st.session_state.selected_prompt_id:
        render_version_history(st.session_state.selected_prompt_id)
        if st.button("❌ Close History", use_container_width=True):
            st.session_state.show_history = False
            st.rerun()
        st.divider()

    # Display prompts
    try:
        user_id = st.session_state.user_id

        if search_query == "favorite":
            prompts = get_favorite_prompts(user_id)
        elif search_query == "recent":
            prompts = search_prompts(user_id, limit=100)
            prompts = sorted(prompts, key=lambda x: x.get('last_used_date', ''), reverse=True)
        else:
            prompts = search_prompts(user_id, query=search_query, limit=100)

        if prompts:
            st.write(f"Found {len(prompts)} prompt(s)")
            for prompt in prompts:
                render_prompt_card(prompt)
        else:
            st.info("No prompts found. Create your first prompt!")

    except Exception as e:
        render_error_message(f"Failed to load prompts: {str(e)}")


if __name__ == "__main__":
    main()
