import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.models import Event


class TestEventArchiving:
    """Test suite for event archiving operations"""

    @patch('app.models.DatabaseConnection.get_connection')
    def test_archive_event_success(self, mock_get_conn):
        """Test successfully archiving an event"""
        # Setup mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock the SELECT query (event exists, user is organizer, not archived)
        mock_cursor.fetchone.side_effect = [
            ('org-uid-123', 0),  # First call: OrganizerUID, IsArchived
            (1, 'org-uid-123', 'Test Event', 'Description',  # Second call: full event
             datetime.now(), datetime.now() + timedelta(hours=2),
             'Location', 1, 100, 'http://image.url',
             datetime.now(), datetime.now(), 1, datetime.now())
        ]

        # Execute
        result = Event.archive_event(1, 'org-uid-123')

        # Assert
        assert result is not None
        assert isinstance(result, Event)
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_archive_event_not_found(self, mock_get_conn):
        """Test archiving non-existent event"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # Event not found

        result = Event.archive_event(999, 'org-uid-123')

        assert result is None
        mock_conn.rollback.assert_not_called()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_archive_event_not_authorized(self, mock_get_conn):
        """Test archiving event by non-organizer"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('different-org-uid', 0)

        result = Event.archive_event(1, 'org-uid-123')

        assert result is False
        mock_conn.commit.assert_not_called()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_archive_event_already_archived(self, mock_get_conn):
        """Test archiving an already archived event"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (
            'org-uid-123', 1)  # Already archived

        result = Event.archive_event(1, 'org-uid-123')

        assert result is None
        mock_conn.commit.assert_not_called()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_get_events_excludes_archived_by_default(self, mock_get_conn):
        """Test that get_events excludes archived events by default"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock count and events query
        mock_cursor.fetchone.return_value = (5,)  # Total count
        mock_cursor.fetchall.return_value = []  # No events for simplicity

        Event.get_events()

        # Verify the WHERE clause includes IsArchived filter
        calls = mock_cursor.execute.call_args_list
        sql_query = calls[1][0][0]  # Second call is the main query
        assert 'IsArchived = 0' in sql_query

    @patch('app.models.DatabaseConnection.get_connection')
    def test_get_events_includes_archived_when_requested(self, mock_get_conn):
        """Test that get_events can include archived events when requested"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = (5,)
        mock_cursor.fetchall.return_value = []

        Event.get_events(include_archived=True)

        # Verify no IsArchived filter in WHERE clause
        calls = mock_cursor.execute.call_args_list
        sql_query = calls[1][0][0]
        assert 'IsArchived' not in sql_query or 'WHERE' not in sql_query

    @patch('app.models.DatabaseConnection.get_connection')
    def test_get_event_by_id_excludes_archived(self, mock_get_conn):
        """Test that get_event_by_id excludes archived events by default"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # Archived event not found

        result = Event.get_event_by_id(1)

        assert result is None
        sql_query = mock_cursor.execute.call_args[0][0]
        assert 'IsArchived = 0' in sql_query

    @patch('app.models.DatabaseConnection.get_connection')
    def test_get_events_by_organizer_excludes_archived(self, mock_get_conn):
        """Test that get_events_by_organizer excludes archived by default"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        Event.get_events_by_organizer('org-uid-123')

        sql_query = mock_cursor.execute.call_args[0][0]
        assert 'IsArchived = 0' in sql_query

    @patch('app.models.DatabaseConnection.get_connection')
    def test_delete_event_success(self, mock_get_conn):
        """Test permanent deletion of an event"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (
            'org-uid-123',)  # Organizer matches
        mock_cursor.rowcount = 1

        result = Event.delete_event(1, 'org-uid-123')

        assert result is True
        mock_conn.commit.assert_called_once()
        # Verify DELETE was called
        delete_call = [call for call in mock_cursor.execute.call_args_list
                       if 'DELETE' in str(call)]
        assert len(delete_call) > 0

    @patch('app.models.DatabaseConnection.get_connection')
    def test_delete_event_not_authorized(self, mock_get_conn):
        """Test deletion by non-organizer fails"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('different-org-uid',)

        result = Event.delete_event(1, 'org-uid-123')

        assert result is False
        mock_conn.commit.assert_not_called()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_delete_event_not_found(self, mock_get_conn):
        """Test deletion of non-existent event"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        result = Event.delete_event(999, 'org-uid-123')

        assert result is False
        mock_conn.commit.assert_not_called()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_event_to_dict_includes_archive_fields(self, mock_get_conn):
        """Test that Event.to_dict includes archiving fields"""
        now = datetime.now()
        event = Event(
            event_id=1,
            organizer_uid='org-123',
            title='Test Event',
            description='Description',
            start_time=now,
            end_time=now + timedelta(hours=2),
            location='Location',
            category_id=1,
            is_archived=True,
            archived_at=now
        )

        event_dict = event.to_dict()

        assert 'is_archived' in event_dict
        assert 'archived_at' in event_dict
        assert event_dict['is_archived'] is True
        assert event_dict['archived_at'] is not None

    @patch('app.models.DatabaseConnection.get_connection')
    def test_create_event_defaults_not_archived(self, mock_get_conn):
        """Test that newly created events are not archived by default"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # EventID

        now = datetime.now()
        event = Event.create_event(
            organizer_uid='org-123',
            title='New Event',
            start_time=now,
            end_time=now + timedelta(hours=2),
            location='Location',
            category_id=1
        )

        # Verify INSERT doesn't set IsArchived or ArchivedAt
        insert_call = mock_cursor.execute.call_args_list[0][0][0]
        assert 'IsArchived' not in insert_call
        assert 'ArchivedAt' not in insert_call
        mock_conn.commit.assert_called_once()


class TestArchivingIntegration:
    """Integration tests for archiving with other features"""

    @patch('app.models.DatabaseConnection.get_connection')
    def test_archived_events_not_in_friend_feed(self, mock_get_conn):
        """Test that archived events don't appear in friend feeds"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        Event.get_friend_events('user-123')

        sql_query = mock_cursor.execute.call_args[0][0]
        assert 'IsArchived = 0' in sql_query

    @patch('app.models.DatabaseConnection.get_connection')
    def test_archived_events_not_in_attending_list(self, mock_get_conn):
        """Test that archived events don't appear in user's attending list"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        Event.get_events_by_attendee('user-123')

        sql_query = mock_cursor.execute.call_args[0][0]
        assert 'IsArchived = 0' in sql_query
