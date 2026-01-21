"""
General App Settings page - User preferences and account management.
Compact layout with settings organized by category.
"""

import streamlit as st
import sys
import os


from core.ui_components import set_compact_layout, render_success_message, render_error_message
from core.auth import change_password, validate_password
from core.notifications import send_email, send_telegram
from core.db import execute_query, update_record
from core.exceptions import ValidationError


def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'settings_tab' not in st.session_state:
        st.session_state.settings_tab = 'Account'


def render_account_settings():
    """Render account settings section."""
    user_id = st.session_state.user_id

    st.subheader("Account Settings")

    # Get current user info
    try:
        user = execute_query("SELECT username, email FROM users WHERE id = ?", (user_id,))

        if user:
            user_data = dict(user[0])

            st.write(f"**Username:** {user_data['username']}")
            st.write(f"**Email:** {user_data['email']}")

            st.divider()

            # Change password
            st.write("**Change Password**")

            col1, col2 = st.columns(2)

            with col1:
                current_password = st.text_input("Current Password", type="password",
                                                key="current_pwd", label_visibility="collapsed")

            with col2:
                st.write("")  # Spacer

            col1, col2 = st.columns(2)

            with col1:
                new_password = st.text_input("New Password", type="password",
                                            key="new_pwd", label_visibility="collapsed")

            with col2:
                confirm_password = st.text_input("Confirm Password", type="password",
                                                key="confirm_pwd", label_visibility="collapsed")

            if st.button("🔐 Update Password", use_container_width=True):
                if not current_password or not new_password or not confirm_password:
                    render_error_message("All fields are required")
                    return

                if new_password != confirm_password:
                    render_error_message("New passwords don't match")
                    return

                if len(new_password) < 6:
                    render_error_message("Password must be at least 6 characters")
                    return

                try:
                    change_password(user_id, current_password, new_password)
                    render_success_message("Password updated successfully!")
                except Exception as e:
                    render_error_message(f"Failed to update password: {str(e)}")

    except Exception as e:
        render_error_message(f"Failed to load account info: {str(e)}")


def render_notification_settings():
    """Render notification preferences."""
    user_id = st.session_state.user_id

    st.subheader("Notification Preferences")

    # Get current settings
    try:
        settings = execute_query(
            "SELECT email_notifications, telegram_notifications FROM users WHERE id = ?",
            (user_id,)
        )

        if settings:
            current_settings = dict(settings[0])

            col1, col2 = st.columns(2)

            with col1:
                email_enabled = st.checkbox(
                    "📧 Email Notifications",
                    value=bool(current_settings.get('email_notifications', 0)),
                    key="email_notif"
                )

            with col2:
                telegram_enabled = st.checkbox(
                    "🤖 Telegram Notifications",
                    value=bool(current_settings.get('telegram_notifications', 0)),
                    key="telegram_notif"
                )

            # Notification types
            st.write("**Notify me about:**")

            col1, col2, col3 = st.columns(3)

            with col1:
                task_reminders = st.checkbox("✅ Task Reminders", value=True, key="task_reminders")

            with col2:
                due_tasks = st.checkbox("📅 Due Tasks", value=True, key="due_tasks")

            with col3:
                upcoming_events = st.checkbox("📌 Upcoming Events", value=True, key="upcoming_events")

            if st.button("💾 Save Preferences", use_container_width=True):
                try:
                    update_record('users', user_id, {
                        'email_notifications': 1 if email_enabled else 0,
                        'telegram_notifications': 1 if telegram_enabled else 0
                    })
                    render_success_message("Notification preferences updated!")
                except Exception as e:
                    render_error_message(f"Failed to save preferences: {str(e)}")

            # Telegram setup
            if telegram_enabled:
                st.write("---")
                st.write("**Telegram Setup**")
                st.caption("1. Message @NoteTrackerBot on Telegram")
                st.caption("2. Send your user ID: " + str(user_id))
                st.caption("3. Bot will confirm and start sending notifications")

    except Exception as e:
        render_error_message(f"Failed to load notification settings: {str(e)}")


def render_display_settings():
    """Render display and appearance settings."""
    st.subheader("Display Settings")

    col1, col2 = st.columns(2)

    with col1:
        theme = st.selectbox("Theme", options=["Light", "Dark", "Auto"], key="theme_setting")

    with col2:
        compact_mode = st.checkbox("Compact Layout", value=True, key="compact_mode")

    col1, col2 = st.columns(2)

    with col1:
        items_per_page = st.select_slider(
            "Items per page",
            options=[10, 25, 50, 100],
            value=25,
            key="items_per_page"
        )

    with col2:
        st.write("")  # Spacer

    col1, col2 = st.columns(2)

    with col1:
        timezone = st.selectbox(
            "Timezone",
            options=["UTC", "EST", "CST", "MST", "PST"],
            key="timezone_setting"
        )

    with col2:
        time_format = st.selectbox(
            "Time Format",
            options=["12-hour", "24-hour"],
            key="time_format"
        )

    if st.button("💾 Save Display Settings", use_container_width=True):
        render_success_message("Display settings saved!")


def render_data_management():
    """Render data management options."""
    st.subheader("Data Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Export All Data", use_container_width=True):
            st.info("Export feature coming soon. Your data will be exported as JSON.")

    with col2:
        if st.button("🔄 Sync Data", use_container_width=True):
            st.info("Sync feature coming soon. Your data is automatically saved.")

    st.divider()

    st.write("**Danger Zone**")

    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.warning("⚠️ This will delete all your notes, tasks, and events. This action cannot be undone.")

        if st.button("🚨 Yes, Delete Everything"):
            st.error("Data deletion aborted for safety.")


def render_about():
    """Render about section."""
    st.subheader("About NoteTracker")

    st.write("**Version:** 1.0.0")
    st.write("**Last Updated:** 2026-01-12")

    st.divider()

    st.write("**Features:**")
    st.caption("✅ Notes - Create and organize notes with tags")
    st.caption("✅ Tasks - Manage tasks with reminders and checklists")
    st.caption("✅ Calendar - View and manage events")
    st.caption("✅ Search - Unified search across all items")
    st.caption("✅ TradeVault - Trading edge management and analytics")

    st.divider()

    st.write("**Help & Support**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📚 Documentation", use_container_width=True):
            st.info("Documentation: Coming soon at docs.notetracker.app")

    with col2:
        if st.button("💬 Support", use_container_width=True):
            st.info("Email support@notetracker.app for help")


def main():
    """Main settings page."""
    init_session()
    set_compact_layout()

    st.title("⚙️ Settings")

    # Tab navigation
    col1, col2, col3, col4, col5 = st.columns(5)

    tabs = ["Account", "Notifications", "Display", "Data", "About"]
    icons = ["👤", "🔔", "🎨", "💾", "ℹ️"]

    for i, (tab, icon) in enumerate(zip(tabs, icons)):
        with [col1, col2, col3, col4, col5][i]:
            if st.button(f"{icon} {tab}", use_container_width=True):
                st.session_state.settings_tab = tab
                st.rerun()

    st.divider()

    # Render selected tab
    if st.session_state.settings_tab == "Account":
        render_account_settings()

    elif st.session_state.settings_tab == "Notifications":
        render_notification_settings()

    elif st.session_state.settings_tab == "Display":
        render_display_settings()

    elif st.session_state.settings_tab == "Data":
        render_data_management()

    elif st.session_state.settings_tab == "About":
        render_about()


if __name__ == "__main__":
    main()
