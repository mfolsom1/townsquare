"""
Unit tests for the User model and database operations
"""
import pytest
from unittest.mock import Mock, patch, call
import pyodbc
from app.models import User, DatabaseConnection


class TestDatabaseConnection:
    """Test database connection functionality"""

    @patch('app.models.Config')
    @patch('pyodbc.connect')
    def test_get_connection(self, mock_connect, mock_config_class):
        """Test that get_connection returns a database connection"""
        mock_config = Mock()
        mock_config.azure_sql_connection_string = 'test-connection-string'
        mock_config_class.return_value = mock_config

        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        result = DatabaseConnection.get_connection()

        mock_connect.assert_called_once_with('test-connection-string')
        assert result == mock_connection


class TestUser:
    """Test User model functionality"""

    def test_user_initialization(self):
        """Test User object initialization"""
        user = User(
            firebase_uid='test-uid',
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            location='Test City',
            bio='Test bio',
            user_type='individual',
            organization_name=None
        )

        assert user.firebase_uid == 'test-uid'
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.location == 'Test City'
        assert user.bio == 'Test bio'
        assert user.user_type == 'individual'
        assert user.organization_name is None

    def test_user_to_dict(self):
        """Test User.to_dict() method"""
        with patch.object(User, 'get_user_interests_by_uid', return_value=['music', 'sports']):
            user = User(
                firebase_uid='test-uid',
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                location='Test City',
                bio='Test bio',
                user_type='individual',
                organization_name=None
            )

            result = user.to_dict()
            expected = {
                "firebase_uid": 'test-uid',
                "username": 'testuser',
                "email": 'test@example.com',
                "first_name": 'Test',
                "last_name": 'User',
                "location": 'Test City',
                "bio": 'Test bio',
                "user_type": 'individual',
                "organization_name": None,
                "interests": ['music', 'sports']
            }

            assert result == expected

    @patch('app.models.DatabaseConnection.get_connection')
    def test_create_user_success(self, mock_get_connection):
        """Test successful user creation"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Test user creation
        result = User.create_user(
            firebase_uid='test-uid',
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            location='Test City',
            user_type='individual'
        )

        # Verify database operations - check that UserType and OrganizationName are included
        call_args = mock_cursor.execute.call_args[0]
        assert 'UserType' in call_args[0]
        assert 'OrganizationName' in call_args[0]

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        # Verify return value is a User object
        assert isinstance(result, User)
        assert result.firebase_uid == 'test-uid'
        assert result.username == 'testuser'

    @patch('app.models.DatabaseConnection.get_connection')
    def test_create_user_database_error(self, mock_get_connection):
        """Test user creation with database error"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")

        # Test user creation with error
        with pytest.raises(Exception) as exc_info:
            User.create_user(
                firebase_uid='test-uid',
                username='testuser',
                email='test@example.com'
            )

        assert str(exc_info.value) == "Database error"
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_get_user_by_firebase_uid_found(self, mock_get_connection):
        """Test getting user by Firebase UID when user exists"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock database row with user_type and organization_name
        # Order: firebase_uid, username, email, first_name, last_name, location, bio, user_type, organization_name, created_at, updated_at
        mock_row = ('test-uid', 'testuser', 'test@example.com', 'Test', 'User', 'Test City',
                    'Test bio', 'individual', None, '2023-01-01', '2023-01-02')
        mock_cursor.fetchone.return_value = mock_row

        # Test user retrieval
        result = User.get_user_by_firebase_uid('test-uid')

        # Verify database operations
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()

        # Verify return value
        assert isinstance(result, User)
        assert result.firebase_uid == 'test-uid'
        assert result.username == 'testuser'
        assert result.email == 'test@example.com'
        assert result.user_type == 'individual'

    @patch('app.models.DatabaseConnection.get_connection')
    def test_get_user_by_firebase_uid_not_found(self, mock_get_connection):
        """Test getting user by Firebase UID when user doesn't exist"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        # Test user retrieval
        result = User.get_user_by_firebase_uid('nonexistent-uid')

        # Verify return value
        assert result is None
        mock_conn.close.assert_called_once()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_get_user_by_email(self, mock_get_connection):
        """Test getting user by email"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock database row with user_type and organization_name
        # Order: firebase_uid, username, email, first_name, last_name, location, bio, user_type, organization_name, created_at, updated_at
        mock_row = ('test-uid', 'testuser', 'test@example.com', 'Test', 'User', 'Test City',
                    'Test bio', 'individual', None, '2023-01-01', '2023-01-02')
        mock_cursor.fetchone.return_value = mock_row

        # Test user retrieval
        result = User.get_user_by_email('test@example.com')

        # Verify database operations
        mock_cursor.execute.assert_called_once()

        # Verify return value
        assert isinstance(result, User)
        assert result.email == 'test@example.com'
        assert result.user_type == 'individual'

    @patch('app.models.DatabaseConnection.get_connection')
    def test_update_user_success(self, mock_get_connection):
        """Test successful user update"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.closed = False  # Add this to track connection state

        # Test user update
        result = User.update_user(
            'test-uid',
            username='newusername',
            first_name='NewFirst',
            bio='New bio'
        )

        # Verify database operations
        expected_query = "UPDATE Users SET Username = ?, FirstName = ?, Bio = ?, UpdatedAt = GETDATE() WHERE FirebaseUID = ?"
        expected_values = ['newusername', 'NewFirst', 'New bio', 'test-uid']

        mock_cursor.execute.assert_called_once_with(
            expected_query, expected_values)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        # Verify return value
        assert result is True

    @patch('app.models.DatabaseConnection.get_connection')
    def test_update_user_no_valid_fields(self, mock_get_connection):
        """Test user update with no valid fields"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.closed = False  # Add this to track connection state

        # Test user update with invalid fields
        result = User.update_user('test-uid', invalid_field='value')

        # Verify no database operations were performed
        mock_cursor.execute.assert_not_called()
        mock_conn.commit.assert_not_called()
        mock_conn.close.assert_called_once()

        # Verify return value
        assert result is False

    @patch('app.models.DatabaseConnection.get_connection')
    def test_update_user_database_error(self, mock_get_connection):
        """Test user update with database error"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_conn.closed = False  # Add this to track connection state

        # Test user update with error
        with pytest.raises(Exception) as exc_info:
            User.update_user('test-uid', username='newusername')

        assert str(exc_info.value) == "Database error"
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('app.models.DatabaseConnection.get_connection')
    def test_get_user_interests_by_uid(self, mock_get_connection):
        """Test getting user interests by Firebase UID"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock database rows
        mock_rows = [('music',), ('sports',), ('technology',)]
        mock_cursor.fetchall.return_value = mock_rows

        # Test getting user interests
        result = User.get_user_interests_by_uid('test-uid')

        # Verify database operations
        expected_query = """
                SELECT i.Name 
                FROM Interests i 
                INNER JOIN UserInterests ui ON i.InterestID = ui.InterestID 
                WHERE ui.UserUID = ?
                ORDER BY i.Name
                """
        mock_cursor.execute.assert_called_once_with(
            expected_query, ('test-uid',))
        mock_conn.close.assert_called_once()

        # Verify return value
        assert result == ['music', 'sports', 'technology']

    @patch('app.models.DatabaseConnection.get_connection')
    def test_add_user_interest_new_interest(self, mock_get_connection):
        """Test adding a new interest to user"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock that interest doesn't exist, then return new InterestID
        mock_cursor.fetchone.side_effect = [None, (123,)]

        # Test adding interest
        result = User.add_user_interest('test-uid', 'music')

        # Verify database operations
        assert mock_cursor.execute.call_count >= 2
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        assert result is True

    @patch('app.models.DatabaseConnection.get_connection')
    def test_add_user_interest_existing_interest(self, mock_get_connection):
        """Test adding an existing interest to user"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock that interest exists
        mock_cursor.fetchone.return_value = (123,)

        # Test adding interest
        result = User.add_user_interest('test-uid', 'music')

        # Verify database operations
        assert mock_cursor.execute.call_count == 2
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        assert result is True

    @patch('app.models.DatabaseConnection.get_connection')
    def test_remove_user_interest(self, mock_get_connection):
        """Test removing user interest"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        # Test removing interest
        result = User.remove_user_interest('test-uid', 'music')

        # Verify database operations
        expected_query = """
                DELETE ui FROM UserInterests ui
                INNER JOIN Interests i ON ui.InterestID = i.InterestID
                WHERE ui.UserUID = ? AND i.Name = ?
                """
        mock_cursor.execute.assert_called_once_with(
            expected_query, ('test-uid', 'music'))
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        assert result is True

    @patch('app.models.DatabaseConnection.get_connection')
    def test_remove_user_interest_not_found(self, mock_get_connection):
        """Test removing user interest that doesn't exist"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 0

        # Test removing non-existent interest
        result = User.remove_user_interest('test-uid', 'nonexistent')

        # Verify return value
        assert result is False

    @patch('app.models.DatabaseConnection.get_connection')
    def test_set_user_interests(self, mock_get_connection):
        """Test setting user interests (replace all)"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock existing interests - return InterestID for each lookup
        mock_cursor.fetchone.side_effect = [
            (123,),  # music exists
            None, (789,),  # sports new, returns new ID
            (456,)   # tech exists
        ]

        # Test setting interests
        result = User.set_user_interests(
            'test-uid', ['music', 'sports', 'technology'])

        # Verify database operations
        # Should delete existing, then add each interest
        assert mock_cursor.execute.call_count >= 6  # Delete + multiple inserts/checks
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        assert result is True

    @patch('app.models.DatabaseConnection.get_connection')
    def test_update_user_with_interests(self, mock_get_connection):
        """Test updating user with interests"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(User, 'set_user_interests', return_value=True) as mock_set_interests:
            # Test user update with interests
            result = User.update_user(
                'test-uid',
                username='newusername',
                interests=['music', 'sports']
            )

            # Verify basic fields were updated
            expected_query = "UPDATE Users SET Username = ?, UpdatedAt = GETDATE() WHERE FirebaseUID = ?"
            expected_values = ['newusername', 'test-uid']
            mock_cursor.execute.assert_called_once_with(
                expected_query, expected_values)

            # Verify interests were set
            mock_set_interests.assert_called_once_with(
                'test-uid', ['music', 'sports'])

            # Verify return value
            assert result is True

    @patch('app.models.DatabaseConnection.get_connection')
    def test_update_user_interests_only(self, mock_get_connection):
        """Test updating user with only interests (no basic fields)"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(User, 'set_user_interests', return_value=True) as mock_set_interests:
            # Test user update with only interests
            result = User.update_user('test-uid', interests=['music'])

            # Verify no basic field updates
            mock_cursor.execute.assert_not_called()

            # Verify interests were set
            mock_set_interests.assert_called_once_with('test-uid', ['music'])

            # Verify return value
            assert result is True

    @patch('app.models.DatabaseConnection.get_connection')
    def test_get_all_interests(self, mock_get_connection):
        """Test getting all available interests"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock database rows
        mock_rows = [
            ('music', 'Musical interests'),
            ('sports', None),
            ('technology', 'Tech and programming')
        ]
        mock_cursor.fetchall.return_value = mock_rows

        # Test getting all interests
        result = User.get_all_interests()

        # Verify database operations
        mock_cursor.execute.assert_called_once_with(
            "SELECT Name, Description FROM Interests ORDER BY Name"
        )
        mock_conn.close.assert_called_once()

        # Verify return value
        expected = [
            {"name": "music", "description": "Musical interests"},
            {"name": "sports", "description": None},
            {"name": "technology", "description": "Tech and programming"}
        ]
        assert result == expected
