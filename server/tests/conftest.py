"""
Test configuration and fixtures for the townsquare test suite
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the server app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    with patch('app.config.Config') as mock:
        mock.return_value.AZURE_SQL_SERVER = 'test-server'
        mock.return_value.AZURE_SQL_DATABASE = 'test-db'
        mock.return_value.AZURE_SQL_USERNAME = 'test-user'
        mock.return_value.AZURE_SQL_PASSWORD = 'test-pass'
        mock.return_value.FIREBASE_SERVICE_ACCOUNT_KEY = 'test-firebase-key.json'
        mock.return_value.azure_sql_connection_string = 'test-connection-string'
        yield mock

@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing"""
    with patch('pyodbc.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.commit.return_value = None
        mock_conn.rollback.return_value = None
        mock_conn.close.return_value = None
        
        # Configure mock cursor for database initialization
        mock_cursor.fetchone.return_value = [1]  # Table exists
        
        yield (mock_connect, mock_conn, mock_cursor)

@pytest.fixture
def mock_firebase():
    """Mock Firebase admin functionality"""
    with patch('firebase_admin.auth') as mock_auth:
        mock_auth.verify_id_token.return_value = {
            'uid': 'test-firebase-uid',
            'email': 'test@example.com',
            'name': 'Test User',
            'given_name': 'Test',
            'family_name': 'User'
        }
        yield mock_auth

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'firebase_uid': 'test-firebase-uid',
        'username': 'testuser',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'location': 'Test City',
        'bio': 'Test bio'
    }

@pytest.fixture
def client(mock_config, mock_db_connection):
    """Flask test client fixture"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_require_auth():
    """Mock the require_auth decorator"""
    with patch('app.routes.require_auth') as mock_auth:
        def mock_decorator(func):
            def wrapper(*args, **kwargs):
                # Simulate passing firebase_uid as first argument
                return func('test-firebase-uid', *args, **kwargs)
            return wrapper
        mock_auth.side_effect = mock_decorator
        yield mock_auth