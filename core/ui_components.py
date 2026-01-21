"""
Reusable Streamlit UI components shared across all apps.
Compact design with focus on content, minimal chrome.
"""

import streamlit as st
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, date


# ============================================
# COMPACT UI HELPERS
# ============================================

def set_compact_layout():
    """Configure Streamlit for compact, content-focused UI."""
    st.set_page_config(
        layout="wide",
        initial_sidebar_state="collapsed",
        page_icon="📚",
    )
    # Reduce padding/margins
    st.markdown("""
    <style>
        /* Compact margins and padding */
        .main { padding: 0.5rem 1rem; }
        .stMetric { margin: 0; padding: 0.25rem; }
        .stContainer { margin: 0; padding: 0.25rem; }
        /* Reduce space between elements */
        [data-testid="column"] { gap: 0.5rem; }
        /* Compact buttons */
        button { padding: 0.25rem 0.5rem; font-size: 0.85rem; }
        /* Compact input fields */
        input, textarea, select { padding: 0.25rem 0.5rem; font-size: 0.85rem; }
        /* Remove extra spacing */
        .stMarkdown > div { margin: 0; }
    </style>
    """, unsafe_allow_html=True)


# ============================================
# SEARCH & FILTER COMPONENTS
# ============================================

def render_search_bar(
    placeholder: str = "Search...",
    key: str = "search",
    cols: int = 3
) -> str:
    """
    Compact search input.

    Args:
        placeholder: Input placeholder
        key: Streamlit key
        cols: Number of columns (for layout)

    Returns:
        Search query string
    """
    col1, col2 = st.columns([cols, 1])
    with col1:
        query = st.text_input(placeholder, key=key, label_visibility="collapsed")
    with col2:
        if st.button("🔍", key=f"{key}_btn", help="Search"):
            return query
    return query


def render_filter_tabs(filters: List[str], key: str = "filter") -> str:
    """
    Compact filter tabs.

    Args:
        filters: List of filter options
        key: Streamlit key

    Returns:
        Selected filter
    """
    return st.selectbox(
        "Filter:",
        filters,
        key=key,
        label_visibility="collapsed"
    )


def render_quick_filters(
    categories: List[str] = None,
    statuses: List[str] = None,
    key_prefix: str = "qf"
) -> Dict[str, Any]:
    """
    Compact quick filters (category, status, etc).

    Args:
        categories: Available categories
        statuses: Available statuses
        key_prefix: Key prefix for Streamlit

    Returns:
        Dict of selected filters
    """
    filters = {}
    cols = st.columns(len([x for x in [categories, statuses] if x]))

    idx = 0
    if categories:
        with cols[idx]:
            filters['category'] = st.selectbox(
                "Category:",
                [None] + categories,
                key=f"{key_prefix}_cat",
                label_visibility="collapsed"
            )
        idx += 1

    if statuses:
        with cols[idx]:
            filters['status'] = st.selectbox(
                "Status:",
                [None] + statuses,
                key=f"{key_prefix}_status",
                label_visibility="collapsed"
            )

    return {k: v for k, v in filters.items() if v is not None}


# ============================================
# SELECTION COMPONENTS
# ============================================

def render_tag_selector(
    all_tags: List[str],
    selected_tags: List[str] = None,
    key: str = "tags"
) -> List[str]:
    """
    Compact tag multi-selector.

    Args:
        all_tags: Available tags
        selected_tags: Pre-selected tags
        key: Streamlit key

    Returns:
        List of selected tags
    """
    return st.multiselect(
        "Tags:",
        all_tags,
        default=selected_tags or [],
        key=key,
        label_visibility="collapsed"
    )


def render_priority_selector(
    key: str = "priority",
    default: int = 3
) -> int:
    """
    Compact priority selector (1-5).

    Args:
        key: Streamlit key
        default: Default value

    Returns:
        Selected priority (1-5)
    """
    options = {
        "🔴 Critical": 5,
        "🟠 High": 4,
        "🟡 Medium": 3,
        "🟢 Low": 2,
        "⚪ Minimal": 1
    }
    selected = st.selectbox(
        "Priority:",
        list(options.keys()),
        index=3,  # Default to Medium
        key=key,
        label_visibility="collapsed"
    )
    return options.get(selected, 3)


def render_status_badge(status: str, key: str = None) -> None:
    """
    Compact status indicator badge.

    Args:
        status: Status string
        key: Optional key for tracking
    """
    status_colors = {
        'active': ('🟢', '#00ff00'),
        'pending': ('🟡', '#ffff00'),
        'completed': ('✅', '#00ff00'),
        'deprecated': ('🔴', '#ff0000'),
        'in-progress': ('🔵', '#0000ff'),
        'testing': ('🧪', '#9900ff'),
        'hibernated': ('❄️', '#00ccff'),
    }

    emoji, color = status_colors.get(status.lower(), ('⚪', '#808080'))
    st.markdown(f"<span style='font-size: 0.9rem;'>{emoji} {status}</span>", unsafe_allow_html=True)


def render_category_badge(category: str) -> None:
    """Display category as compact badge."""
    colors = {
        'personal': '#FFB6C1',
        'work': '#87CEEB',
        'financial': '#90EE90',
        'health': '#FFD700',
        'ideas': '#DDA0DD',
        'grid': '#FF9999',
        'bias': '#99CCFF',
        'pivot': '#99FF99',
    }
    color = colors.get(category.lower(), '#CCCCCC')
    st.markdown(
        f"<span style='background-color: {color}; padding: 0.2rem 0.4rem; border-radius: 3px; font-size: 0.8rem;'>"
        f"{category}</span>",
        unsafe_allow_html=True
    )


# ============================================
# DATE & TIME COMPONENTS
# ============================================

def render_date_picker(
    label: str = "Date:",
    key: str = "date",
    value: date = None
) -> date:
    """
    Compact date picker.

    Args:
        label: Field label
        key: Streamlit key
        value: Initial value

    Returns:
        Selected date
    """
    return st.date_input(
        label,
        value=value or datetime.now().date(),
        key=key,
        label_visibility="collapsed"
    )


def render_time_picker(
    label: str = "Time:",
    key: str = "time",
    value = None
):
    """
    Compact time picker.

    Args:
        label: Field label
        key: Streamlit key
        value: Initial value

    Returns:
        Selected time
    """
    return st.time_input(
        label,
        value=value,
        key=key,
        label_visibility="collapsed"
    )


def render_datetime_range(
    key_prefix: str = "dt_range"
) -> tuple:
    """
    Compact datetime range selector.

    Args:
        key_prefix: Key prefix

    Returns:
        (start_date, end_date)
    """
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From:", key=f"{key_prefix}_start")
    with col2:
        end_date = st.date_input("To:", key=f"{key_prefix}_end")
    return start_date, end_date


# ============================================
# DISPLAY COMPONENTS
# ============================================

def render_stat_card(label: str, value: Any, description: str = None, color: str = None, icon: str = "", metric_format: str = None) -> None:
    """
    Compact statistic card.

    Args:
        label: Card label
        value: Statistic value
        description: Secondary text/delta
        color: Color accent (unused in native metric, kept for compatibility)
        icon: Emoji icon
        metric_format: Format string
    """
    if metric_format and isinstance(value, (int, float)):
        value = metric_format.format(value)
    
    display_value = f"{icon} {value}" if icon else value
    st.metric(label, display_value, delta=description)


def render_item_card(
    title: str,
    subtitle: str = "",
    tags: List[str] = None,
    status: str = None,
    on_click: Callable = None,
    key: str = None
) -> bool:
    """
    Compact item card (for lists).

    Args:
        title: Card title
        subtitle: Secondary text
        tags: List of tags
        status: Status string
        on_click: Click callback
        key: Streamlit key

    Returns:
        True if clicked
    """
    cols = st.columns([1, 4, 1]) if status else [None, None, None]

    if status:
        with cols[0]:
            render_status_badge(status)

    with cols[1] if cols[1] else st.container():
        st.write(f"**{title}**")
        if subtitle:
            st.caption(subtitle)
        if tags:
            tag_str = " ".join([f"#{tag}" for tag in tags])
            st.caption(tag_str)

    if on_click and key:
        with cols[2] if cols[2] else st.container():
            return st.button("→", key=key, on_click=on_click)

    return False


def render_notification_bell(unread_count: int) -> None:
    """
    Compact notification indicator.

    Args:
        unread_count: Number of unread notifications
    """
    if unread_count > 0:
        st.markdown(f"🔔 **{unread_count}** unread", help="Notifications")
    else:
        st.caption("🔔 No notifications")


# ============================================
# FORM COMPONENTS
# ============================================

def render_text_input(
    label: str,
    placeholder: str = "",
    key: str = None,
    max_chars: int = None,
    value: str = ""
) -> str:
    """
    Compact text input.

    Args:
        label: Field label
        placeholder: Placeholder text
        key: Streamlit key
        max_chars: Max characters
        value: Initial value

    Returns:
        Input value
    """
    return st.text_input(
        label,
        value=value,
        placeholder=placeholder,
        max_chars=max_chars,
        key=key,
        label_visibility="collapsed"
    )


def render_text_area(
    label: str,
    placeholder: str = "",
    key: str = None,
    height: int = 100,
    value: str = ""
) -> str:
    """
    Compact text area.

    Args:
        label: Field label
        placeholder: Placeholder text
        key: Streamlit key
        height: Text area height
        value: Initial value

    Returns:
        Input value
    """
    return st.text_area(
        label,
        value=value,
        placeholder=placeholder,
        height=height,
        key=key,
        label_visibility="collapsed"
    )


def render_number_input(
    label: str,
    min_value: float = None,
    max_value: float = None,
    key: str = None,
    value: float = 0
) -> float:
    """
    Compact number input.

    Args:
        label: Field label
        min_value: Minimum value
        max_value: Maximum value
        key: Streamlit key
        value: Initial value

    Returns:
        Input value
    """
    return st.number_input(
        label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        key=key,
        label_visibility="collapsed"
    )


# ============================================
# NAVIGATION & LAYOUT
# ============================================

def render_tab_navigation(tabs: List[str], key: str = "tab_nav") -> str:
    """
    Compact tab navigation.

    Args:
        tabs: List of tab names
        key: Streamlit key

    Returns:
        Selected tab
    """
    return st.radio("", tabs, horizontal=True, key=key, label_visibility="collapsed")


def render_breadcrumb(path: List[str]) -> None:
    """
    Display breadcrumb navigation.

    Args:
        path: List of path items
    """
    breadcrumb = " / ".join(path)
    st.caption(breadcrumb)


def render_two_column_form(
    left_fields: Dict[str, Any],
    right_fields: Dict[str, Any]
) -> tuple:
    """
    Compact two-column form layout.

    Args:
        left_fields: {label: default_value}
        right_fields: {label: default_value}

    Returns:
        (left_values, right_values)
    """
    col1, col2 = st.columns(2)
    left_vals, right_vals = {}, {}

    with col1:
        for label, default in left_fields.items():
            left_vals[label] = st.text_input(label, value=str(default))

    with col2:
        for label, default in right_fields.items():
            right_vals[label] = st.text_input(label, value=str(default))

    return left_vals, right_vals


# ============================================
# CONFIRMATION & DIALOGS
# ============================================

def render_confirmation_inline(
    message: str,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    key_prefix: str = "confirm"
) -> Optional[bool]:
    """
    Inline confirmation dialog (compact).

    Args:
        message: Confirmation message
        confirm_text: Confirm button text
        cancel_text: Cancel button text
        key_prefix: Key prefix

    Returns:
        True if confirmed, False if cancelled, None if pending
    """
    st.warning(message)
    col1, col2 = st.columns(2)

    with col1:
        if st.button(confirm_text, key=f"{key_prefix}_yes"):
            return True

    with col2:
        if st.button(cancel_text, key=f"{key_prefix}_no"):
            return False

    return None


def render_success_message(message: str) -> None:
    """Display success message."""
    st.success(f"✅ {message}")


def render_error_message(message: str) -> None:
    """Display error message."""
    st.error(f"❌ {message}")


def render_warning_message(message: str) -> None:
    """Display warning message."""
    st.warning(f"⚠️ {message}")


def render_info_message(message: str) -> None:
    """Display info message."""
    st.info(f"ℹ️ {message}")
