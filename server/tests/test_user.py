"""
Tests for user type permissions and behaviors.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class TestUserTypePermissions:
    """Test permissions for individual and organization user types"""

    @patch('app.models.DatabaseConnection.get_connection')
    def test_organization_user_can_create_event(self, mock_get_conn):
        """Organization users can create events"""
        from app.models import Event

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)

        now = datetime.now()
        event = Event.create_event(
            organizer_uid='org-user-123',
            title='Community Event',
            start_time=now,
            end_time=now + timedelta(hours=2),
            location='Community Center',
            category_id=1
        )

        assert event is not None
        assert event.organizer_uid == 'org-user-123'
        mock_conn.commit.assert_called_once()


class TestUserFollowing:
    """Test that all user types can follow any other user type"""

    @patch('app.models.DatabaseConnection.get_connection')
    def test_users_can_follow_each_other(self, mock_get_conn):
        """Test that any user type can follow any other user type"""
        from app.models import User

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [[2], [0]]

        result = User.follow_user('user-uid-1', 'user-uid-2')

        assert result is True
        mock_conn.commit.assert_called_once()


class TestUserRSVP:
    """Test that all user types can RSVP to events"""

    @patch('app.models.DatabaseConnection.get_connection')
    def test_create_rsvp(self, mock_get_conn):
        """Test creating an RSVP"""
        from app.models import RSVP

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [None, [1]]

        result = RSVP.create_or_update_rsvp('user-uid', 1, 'Going')

        assert isinstance(result, RSVP)
        assert result.rsvp_id == 1
        mock_conn.commit.assert_called_once()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_update_existing_rsvp(self, mock_get_conn):
        """Test updating an existing RSVP"""
        from app.models import RSVP

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]

        result = RSVP.create_or_update_rsvp('user-uid', 1, 'NotGoing')

        assert isinstance(result, RSVP)
        assert result.rsvp_id == 1
        assert result.status == 'NotGoing'
        mock_conn.commit.assert_called_once()


class TestUserCreation:
    """Test user creation for individual and organization types"""

    @patch('app.models.DatabaseConnection.get_connection')
    def test_create_individual_user(self, mock_get_conn):
        """Create an individual user"""
        from app.models import User

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = User.create_user(
            firebase_uid='test-uid',
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            location='Test City',
            user_type='individual'
        )

        assert isinstance(result, User)
        assert result.firebase_uid == 'test-uid'
        assert result.user_type == 'individual'
        mock_conn.commit.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert 'UserType' in call_args[0]

    @patch('app.models.DatabaseConnection.get_connection')
    def test_create_organization_user(self, mock_get_conn):
        """Create an organization user"""
        from app.models import User

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = User.create_user(
            firebase_uid='org-uid',
            username='gainesville_rec',
            email='contact@gainesvillerec.org',
            location='Gainesville',
            user_type='organization',
            organization_name='Gainesville Recreation Department'
        )

        assert isinstance(result, User)
        assert result.firebase_uid == 'org-uid'
        assert result.user_type == 'organization'
        assert result.organization_name == 'Gainesville Recreation Department'
        mock_conn.commit.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert 'UserType' in call_args[0]
        assert 'OrganizationName' in call_args[0]


class TestHybridModelIntegrity:
    """Test hybrid user model integrity"""

    @patch('app.models.DatabaseConnection.get_connection')
    def test_no_organization_table_references(self, mock_get_conn):
        """Ensure User model doesn't reference Organizations table"""
        from app.models import User

        assert not hasattr(User, 'get_user_organizations')
        assert not hasattr(User, 'join_organization')
        assert not hasattr(User, 'leave_organization')
        assert not hasattr(User, 'follow_organization')
        assert not hasattr(User, 'unfollow_organization')

    @patch('app.models.DatabaseConnection.get_connection')
    def test_user_has_user_type_field(self, mock_get_conn):
        """Verify User model uses user_type field"""
        from app.models import User

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = (
            'test-uid', 'testuser', 'test@example.com',
            'Test', 'User', 'Test City', 'Bio text',
            'organization', 'Test Org',
            datetime.now(), datetime.now()
        )

        user = User.get_user_by_firebase_uid('test-uid')

        assert user is not None
        assert hasattr(user, 'user_type')
        assert user.user_type == 'organization'
        assert hasattr(user, 'organization_name')
        assert user.organization_name == 'Test Org'

    @patch('app.models.DatabaseConnection.get_connection')
    def test_event_has_organizer_uid_not_org_id(self, mock_get_conn):
        """Verify Event model uses OrganizerUID field"""
        from app.models import Event

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.now()
        mock_cursor.fetchone.return_value = (
            1, 'org-user-uid', 'Event Title', 'Description',
            now, now + timedelta(hours=2), 'Location', 1, 100,
            'http://image.url', now, now, 0, None
        )

        event = Event.get_event_by_id(1)

        assert event is not None
        assert hasattr(event, 'organizer_uid')
        assert not hasattr(event, 'org_id')
        assert event.organizer_uid == 'org-user-uid'
