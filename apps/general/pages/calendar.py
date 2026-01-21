"""
General App Calendar page - View and manage events in calendar format.
Compact layout with month view and quick event creation.
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import Dict, List
import sys
import os
import calendar

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.ui_components import (
    set_compact_layout, render_success_message, render_error_message
)
from apps.general.utils.calendar_ops import (
    create_event, get_event, update_event, delete_event,
    get_events_on_date, get_events_in_range, get_today_events,
    get_upcoming_events, get_calendar_data, get_event_categories,
    search_events, get_conflicting_events
)
from core.exceptions import ValidationError


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'current_month' not in st.session_state:
        st.session_state.current_month = date.today().month
    if 'current_year' not in st.session_state:
        st.session_state.current_year = date.today().year
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False


def render_create_form():
    """Render event creation form."""
    user_id = st.session_state.user_id

    st.subheader("Create New Event")

    title = st.text_input("Event Title", key="new_event_title", label_visibility="collapsed",
                         placeholder="Event name")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", key="new_event_start_date")

    with col2:
        is_all_day = st.checkbox("All Day", value=False, key="new_event_all_day")

    if not is_all_day:
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Start Time", key="new_event_start_time")
        with col2:
            end_date = st.date_input("End Date (optional)", key="new_event_end_date")

    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox("Category", options=["Personal", "Work", "Birthday", "Holiday"],
                               key="new_event_category", label_visibility="collapsed")

    with col2:
        reminder = st.selectbox("Reminder", options=["None", "15 min", "1 hour", "1 day"],
                               key="new_event_reminder", label_visibility="collapsed")

    location = st.text_input("Location (optional)", key="new_event_location", label_visibility="collapsed")
    description = st.text_area("Description (optional)", height=80, key="new_event_description")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📅 Create Event", use_container_width=True):
            if not title.strip():
                render_error_message("Event title is required")
                return

            try:
                reminder_map = {"None": 0, "15 min": 15, "1 hour": 60, "1 day": 1440}

                event_data = {
                    'title': title,
                    'description': description,
                    'start_date': start_date.isoformat(),
                    'location': location,
                    'is_all_day': 1 if is_all_day else 0,
                    'category': category.lower(),
                    'reminder_minutes_before': reminder_map.get(reminder, 1440)
                }

                if not is_all_day and start_time:
                    event_data['start_time'] = start_time.strftime("%H:%M")

                if not is_all_day and end_date:
                    event_data['end_date'] = end_date.isoformat()

                event_id = create_event(user_id, event_data)
                render_success_message(f"Event created! (ID: {event_id})")
                st.session_state.show_create_form = False
                st.rerun()

            except ValidationError as e:
                render_error_message(f"Validation error: {str(e)}")
            except Exception as e:
                render_error_message(f"Failed to create event: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_create_form = False
            st.rerun()


def render_calendar_grid():
    """Render month calendar grid."""
    user_id = st.session_state.user_id
    year = st.session_state.current_year
    month = st.session_state.current_month

    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("◀ Prev", use_container_width=True):
            if month == 1:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
            else:
                st.session_state.current_month -= 1
            st.rerun()

    with col2:
        month_name = calendar.month_name[month]
        st.write(f"<h3 style='text-align: center'>{month_name} {year}</h3>", unsafe_allow_html=True)

    with col3:
        if st.button("Next ▶", use_container_width=True):
            if month == 12:
                st.session_state.current_month = 1
                st.session_state.current_year += 1
            else:
                st.session_state.current_month += 1
            st.rerun()

    # Get calendar data
    try:
        cal_data = get_calendar_data(user_id, year, month)

        # Render calendar grid
        cal = calendar.monthcalendar(year, month)

        # Day headers
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        cols = st.columns(7)
        for i, day in enumerate(days):
            with cols[i]:
                st.write(f"<b>{day}</b>", unsafe_allow_html=True)

        # Calendar cells
        for week in cal:
            cols = st.columns(7)
            for day_col, day in enumerate(week):
                with cols[day_col]:
                    if day == 0:
                        st.write("")
                    else:
                        date_key = date(year, month, day).isoformat()
                        events = cal_data.get(date_key, [])

                        # Highlight today
                        today = date.today().isoformat()
                        bg_color = "#e3f2fd" if date_key == today else "transparent"

                        event_display = f"<div style='background-color: {bg_color}; padding: 4px; border-radius: 4px'>"
                        event_display += f"<b>{day}</b>"

                        if events:
                            event_display += f"<br><small>{len(events)} event(s)</small>"

                        event_display += "</div>"

                        st.write(event_display, unsafe_allow_html=True)

                        if st.button("📅", key=f"day_{day}_{month}_{year}", help=f"View {day}"):
                            st.session_state.selected_date = date_key
                            st.rerun()

    except Exception as e:
        render_error_message(f"Failed to load calendar: {str(e)}")


def render_date_details(date_str: str):
    """Render details for selected date."""
    user_id = st.session_state.user_id

    st.subheader(f"Events for {date_str}")

    try:
        events = get_events_on_date(user_id, date_str)

        if events:
            for event in events:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    time_display = event.get('start_time', 'All day')
                    st.write(f"🕐 {time_display} - **{event['title']}**")

                with col2:
                    if st.button("✏️", key=f"edit_event_{event['id']}", help="Edit"):
                        st.info("Edit feature coming soon")

                with col3:
                    if st.button("🗑️", key=f"delete_event_{event['id']}", help="Delete"):
                        try:
                            delete_event(user_id, event['id'])
                            render_success_message("Event deleted")
                            st.session_state.selected_date = None
                            st.rerun()
                        except Exception as e:
                            render_error_message(str(e))

                if event.get('description'):
                    st.caption(event['description'])
                if event.get('location'):
                    st.caption(f"📍 {event['location']}")

                st.divider()

        else:
            st.info("No events on this date")

    except Exception as e:
        render_error_message(f"Failed to load events: {str(e)}")


def render_upcoming_events():
    """Render upcoming events section."""
    user_id = st.session_state.user_id

    st.subheader("Upcoming Events (7 days)")

    try:
        events = get_upcoming_events(user_id, days=7)

        if events:
            for event in events[:10]:  # Show top 10
                st.caption(f"📅 {event['start_date']} - **{event['title']}**")
        else:
            st.caption("No upcoming events")

    except Exception as e:
        render_error_message(f"Failed to load upcoming events: {str(e)}")


def main():
    """Main calendar page."""
    init_session()
    set_compact_layout()

    st.title("📅 Calendar")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("➕ New Event", use_container_width=True):
            st.session_state.show_create_form = not st.session_state.show_create_form
            st.rerun()

    with col2:
        if st.session_state.selected_date:
            if st.button("❌ Clear Selection", use_container_width=True):
                st.session_state.selected_date = None
                st.rerun()

    st.divider()

    # Show create form if toggled
    if st.session_state.show_create_form:
        render_create_form()
        st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        # Calendar grid
        render_calendar_grid()

    with col2:
        # Selected date details or upcoming
        if st.session_state.selected_date:
            render_date_details(st.session_state.selected_date)
        else:
            render_upcoming_events()


if __name__ == "__main__":
    main()
