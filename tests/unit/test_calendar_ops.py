"""
Unit tests for apps/general/utils/calendar_ops.py
Tests all calendar event operations.
"""

import pytest
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.general.utils.calendar_ops import (
    create_event, get_event, update_event, delete_event, get_events_on_date,
    get_events_in_range, get_upcoming_events, get_today_events, get_event_categories,
    get_calendar_data, get_event_stats, search_events, get_conflicting_events,
    export_events
)
from core.exceptions import ValidationError


@pytest.mark.unit
@pytest.mark.database
class TestEventCreation:
    """Test event creation operations."""

    def test_create_event_valid_data(self, test_user, sample_event_data, test_db_path):
        """Test creating event with valid data."""
        event_id = create_event(test_user['id'], sample_event_data, test_db_path)
        assert isinstance(event_id, int)
        assert event_id > 0

    def test_create_event_missing_title(self, test_user, sample_event_data, test_db_path):
        """Test creating event without title raises error."""
        sample_event_data.pop('title')
        with pytest.raises(ValidationError):
            create_event(test_user['id'], sample_event_data, test_db_path)

    def test_create_event_short_title(self, test_user, sample_event_data, test_db_path):
        """Test creating event with title too short."""
        sample_event_data['title'] = 'a'
        with pytest.raises(ValidationError):
            create_event(test_user['id'], sample_event_data, test_db_path)

    def test_create_event_invalid_date(self, test_user, sample_event_data, test_db_path):
        """Test creating event with invalid date."""
        sample_event_data['start_date'] = 'invalid-date'
        with pytest.raises(ValidationError):
            create_event(test_user['id'], sample_event_data, test_db_path)

    def test_create_event_sets_defaults(self, test_user, sample_event_data, test_db_path):
        """Test that defaults are set."""
        sample_event_data.pop('reminder_minutes_before', None)

        event_id = create_event(test_user['id'], sample_event_data, test_db_path)
        event = get_event(test_user['id'], event_id, test_db_path)

        assert event['reminder_minutes_before'] == 1440


@pytest.mark.unit
@pytest.mark.database
class TestEventRetrieval:
    """Test event retrieval operations."""

    def test_get_event_valid_id(self, test_user, sample_event_data, test_db_path):
        """Test retrieving existing event."""
        event_id = create_event(test_user['id'], sample_event_data, test_db_path)
        event = get_event(test_user['id'], event_id, test_db_path)

        assert event is not None
        assert event['id'] == event_id
        assert event['title'] == sample_event_data['title']

    def test_get_event_invalid_id(self, test_user, test_db_path):
        """Test retrieving non-existent event."""
        event = get_event(test_user['id'], 99999, test_db_path)
        assert event is None

    def test_get_event_wrong_user(self, test_user, test_user2, sample_event_data, test_db_path):
        """Test retrieving event from different user."""
        event_id = create_event(test_user['id'], sample_event_data, test_db_path)
        event = get_event(test_user2['id'], event_id, test_db_path)
        assert event is None


@pytest.mark.unit
@pytest.mark.database
class TestEventUpdate:
    """Test event update operations."""

    def test_update_event_title(self, test_user, sample_event_data, test_db_path):
        """Test updating event title."""
        event_id = create_event(test_user['id'], sample_event_data, test_db_path)

        update_event(test_user['id'], event_id, {'title': 'New Title'}, test_db_path)
        event = get_event(test_user['id'], event_id, test_db_path)

        assert event['title'] == 'New Title'

    def test_update_event_time(self, test_user, sample_event_data, test_db_path):
        """Test updating event time."""
        event_id = create_event(test_user['id'], sample_event_data, test_db_path)

        update_event(test_user['id'], event_id, {'start_time': '16:00'}, test_db_path)
        event = get_event(test_user['id'], event_id, test_db_path)

        assert event['start_time'] == '16:00'

    def test_update_non_existent_event(self, test_user, test_db_path):
        """Test updating non-existent event raises error."""
        with pytest.raises(ValidationError):
            update_event(test_user['id'], 99999, {'title': 'New'}, test_db_path)


@pytest.mark.unit
@pytest.mark.database
class TestEventDelete:
    """Test event deletion operations."""

    def test_delete_event(self, test_user, sample_event_data, test_db_path):
        """Test deleting an event."""
        event_id = create_event(test_user['id'], sample_event_data, test_db_path)

        delete_event(test_user['id'], event_id, test_db_path)
        event = get_event(test_user['id'], event_id, test_db_path)

        assert event is None

    def test_delete_non_existent_event(self, test_user, test_db_path):
        """Test deleting non-existent event raises error."""
        with pytest.raises(ValidationError):
            delete_event(test_user['id'], 99999, test_db_path)


@pytest.mark.unit
@pytest.mark.database
class TestEventRetrieval_ByDate:
    """Test event retrieval by date."""

    def test_get_events_on_date(self, test_user, sample_event_data, test_db_path):
        """Test retrieving events on specific date."""
        event_date = date.today().isoformat()
        sample_event_data['start_date'] = event_date

        create_event(test_user['id'], sample_event_data, test_db_path)
        events = get_events_on_date(test_user['id'], event_date, test_db_path)

        assert len(events) > 0

    def test_get_events_in_range(self, test_user, sample_event_data, test_db_path):
        """Test retrieving events in date range."""
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=7)).isoformat()

        sample_event_data['start_date'] = start_date
        create_event(test_user['id'], sample_event_data, test_db_path)

        events = get_events_in_range(test_user['id'], start_date, end_date, test_db_path)

        assert len(events) > 0

    def test_get_today_events(self, test_user, sample_event_data, test_db_path):
        """Test retrieving today's events."""
        today = date.today().isoformat()
        sample_event_data['start_date'] = today

        create_event(test_user['id'], sample_event_data, test_db_path)
        events = get_today_events(test_user['id'], test_db_path)

        assert len(events) > 0

    def test_get_upcoming_events(self, test_user, sample_event_data, test_db_path):
        """Test retrieving upcoming events."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        sample_event_data['start_date'] = tomorrow

        create_event(test_user['id'], sample_event_data, test_db_path)
        events = get_upcoming_events(test_user['id'], days=7, db_path=test_db_path)

        assert len(events) > 0


@pytest.mark.unit
@pytest.mark.database
class TestEventSearch:
    """Test event search operations."""

    def test_search_events_by_title(self, test_user, sample_event_data, test_db_path):
        """Test searching events by title."""
        create_event(test_user['id'], sample_event_data, test_db_path)

        results = search_events(test_user['id'], query='Test Event', db_path=test_db_path)

        assert len(results) > 0

    def test_search_events_by_category(self, test_user, sample_event_data, test_db_path):
        """Test searching events by category."""
        create_event(test_user['id'], sample_event_data, test_db_path)

        results = search_events(test_user['id'], category='personal', db_path=test_db_path)

        assert len(results) > 0

    def test_search_events_by_date_range(self, test_user, sample_event_data, test_db_path):
        """Test searching events by date range."""
        start = date.today().isoformat()
        end = (date.today() + timedelta(days=7)).isoformat()
        sample_event_data['start_date'] = start

        create_event(test_user['id'], sample_event_data, test_db_path)
        results = search_events(test_user['id'], start_date=start, end_date=end, db_path=test_db_path)

        assert len(results) > 0


@pytest.mark.unit
@pytest.mark.database
class TestEventConflicts:
    """Test event conflict detection."""

    def test_get_conflicting_events(self, test_user, sample_event_data, test_db_path):
        """Test detecting conflicting events."""
        event_date = date.today().isoformat()
        sample_event_data['start_date'] = event_date
        sample_event_data['start_time'] = '10:00'

        event_id1 = create_event(test_user['id'], sample_event_data, test_db_path)

        # Create overlapping event
        sample_event_data['title'] = 'Conflicting Event'
        sample_event_data['start_time'] = '10:30'
        event_id2 = create_event(test_user['id'], sample_event_data, test_db_path)

        conflicts = get_conflicting_events(test_user['id'], event_id1, test_db_path)

        assert len(conflicts) > 0


@pytest.mark.unit
@pytest.mark.database
class TestEventStatistics:
    """Test event statistics operations."""

    def test_get_event_stats_empty(self, test_user, test_db_path):
        """Test statistics with no events."""
        stats = get_event_stats(test_user['id'], test_db_path)

        assert stats['total'] == 0
        assert stats['upcoming'] == 0

    def test_get_event_stats_with_events(self, test_user, sample_event_data, test_db_path):
        """Test statistics with events."""
        create_event(test_user['id'], sample_event_data, test_db_path)

        stats = get_event_stats(test_user['id'], test_db_path)

        assert stats['total'] >= 1

    def test_get_event_categories(self, test_user, sample_event_data, test_db_path):
        """Test getting all event categories."""
        create_event(test_user['id'], sample_event_data, test_db_path)

        categories = get_event_categories(test_user['id'], test_db_path)

        assert 'personal' in categories


@pytest.mark.unit
@pytest.mark.database
class TestCalendarData:
    """Test calendar data operations."""

    def test_get_calendar_data(self, test_user, sample_event_data, test_db_path):
        """Test retrieving calendar data for month."""
        create_event(test_user['id'], sample_event_data, test_db_path)

        today = date.today()
        cal_data = get_calendar_data(test_user['id'], today.year, today.month, test_db_path)

        assert isinstance(cal_data, dict)


@pytest.mark.unit
@pytest.mark.database
class TestEventExport:
    """Test event export operations."""

    def test_export_events(self, test_user, sample_event_data, test_db_path):
        """Test exporting events."""
        create_event(test_user['id'], sample_event_data, test_db_path)

        exported = export_events(test_user['id'], test_db_path)

        assert isinstance(exported, list)
        assert len(exported) > 0
        assert 'title' in exported[0]
