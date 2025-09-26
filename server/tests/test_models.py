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
            bio='Test bio'
        )
        
        assert user.firebase_uid == 'test-uid'
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.location == 'Test City'
        assert user.bio == 'Test bio'
    
    def test_user_to_dict(self):
        """Test User.to_dict() method"""
        user = User(
            firebase_uid='test-uid',
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            location='Test City',
            bio='Test bio'
        )
        
        result = user.to_dict()
        expected = {
            "firebase_uid": 'test-uid',
            "username": 'testuser',
            "email": 'test@example.com',
            "first_name": 'Test',
            "last_name": 'User',
            "location": 'Test City',
            "bio": 'Test bio'
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
            location='Test City'
        )
        
        # Verify database operations
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO Users (FirebaseUID, Username, Email, FirstName, LastName, Location) VALUES (?, ?, ?, ?, ?, ?)",
            ('test-uid', 'testuser', 'test@example.com', 'Test', 'User', 'Test City')
        )
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        
        # Verify return value
        assert isinstance(result, User)
        assert result.firebase_uid == 'test-uid'
        assert result.username == 'testuser'
        assert result.email == 'test@example.com'
    
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
        
        # Mock database row
        mock_row = ('test-uid', 'testuser', 'test@example.com', 'Test', 'User', 'Test City', 'Test bio', '2023-01-01', '2023-01-02')
        mock_cursor.fetchone.return_value = mock_row
        
        # Test user retrieval
        result = User.get_user_by_firebase_uid('test-uid')
        
        # Verify database operations
        mock_cursor.execute.assert_called_once_with(
            "SELECT FirebaseUID, Username, Email, FirstName, LastName, Location, Bio, CreatedAt, UpdatedAt FROM Users WHERE FirebaseUID = ?",
            ('test-uid',)
        )
        mock_conn.close.assert_called_once()
        
        # Verify return value
        assert isinstance(result, User)
        assert result.firebase_uid == 'test-uid'
        assert result.username == 'testuser'
        assert result.email == 'test@example.com'
    
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
        
        # Mock database row
        mock_row = ('test-uid', 'testuser', 'test@example.com', 'Test', 'User', 'Test City', 'Test bio', '2023-01-01', '2023-01-02')
        mock_cursor.fetchone.return_value = mock_row
        
        # Test user retrieval
        result = User.get_user_by_email('test@example.com')
        
        # Verify database operations
        mock_cursor.execute.assert_called_once_with(
            "SELECT FirebaseUID, Username, Email, FirstName, LastName, Location, Bio, CreatedAt, UpdatedAt FROM Users WHERE Email = ?",
            ('test@example.com',)
        )
        
        # Verify return value
        assert isinstance(result, User)
        assert result.email == 'test@example.com'
    
    @patch('app.models.DatabaseConnection.get_connection')
    def test_update_user_success(self, mock_get_connection):
        """Test successful user update"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
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
        
        mock_cursor.execute.assert_called_once_with(expected_query, expected_values)
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
        
        # Test user update with error
        with pytest.raises(Exception) as exc_info:
            User.update_user('test-uid', username='newusername')
        
        assert str(exc_info.value) == "Database error"
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()