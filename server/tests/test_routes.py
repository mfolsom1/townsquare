"""
Integration tests for API routes
"""
import pytest
import pyodbc
from unittest.mock import Mock, patch
import firebase_admin
from app import create_app

# Use a pytest fixture for a cleaner, more modular setup.
@pytest.fixture
def client():
    """Configures the Flask app for testing and yields a test client."""
    # Mock external services during app creation
    with patch('firebase_admin._apps', {}), \
         patch('firebase_admin.initialize_app'), \
         patch('app.database.init_database'):
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

# --- Test Functions (No longer in a class) ---

def test_home_route(client):
    """Test the home route"""
    response = client.get('/')
    assert response.status_code == 200
    assert response.json['message'] == "Welcome to Townsquare API"

@patch('app.routes.auth.verify_id_token') # Standardized patch path
@patch('app.models.User.get_user_by_firebase_uid')
def test_verify_firebase_token_existing_user(mock_get_user, mock_verify_token, client):
    """Test Firebase token verification with existing user"""
    mock_verify_token.return_value = {
        'uid': 'test-firebase-uid', 'email': 'test@example.com', 'name': 'Test User'
    }
    mock_user = Mock()
    mock_user.to_dict.return_value = {
        'firebase_uid': 'test-firebase-uid', 'username': 'testuser', 'email': 'test@example.com'
    }
    mock_get_user.return_value = mock_user

    response = client.post('/api/auth/verify', json={'idToken': 'valid-token'})

    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['user']['firebase_uid'] == 'test-firebase-uid'
    mock_get_user.assert_called_once_with('test-firebase-uid')

@patch('app.routes.auth.verify_id_token') # Standardized patch path
@patch('app.models.User.get_user_by_firebase_uid')
@patch('app.models.User.create_user')
def test_verify_firebase_token_new_user(mock_create_user, mock_get_user, mock_verify_token, client):
    """Test Firebase token verification with new user creation"""
    mock_verify_token.return_value = {
        'uid': 'new-firebase-uid', 'email': 'newuser@example.com', 'name': 'New User',
        'given_name': 'New', 'family_name': 'User'
    }
    mock_get_user.return_value = None  # User doesn't exist
    mock_new_user = Mock()
    mock_new_user.to_dict.return_value = {
        'firebase_uid': 'new-firebase-uid', 'username': 'newuser', 'email': 'newuser@example.com'
    }
    mock_create_user.return_value = mock_new_user

    response = client.post('/api/auth/verify', json={
        'idToken': 'valid-token',
        'userData': {'username': 'newuser'}
    })

    assert response.status_code == 200
    assert response.json['message'] == "User created successfully"
    assert response.json['user']['firebase_uid'] == 'new-firebase-uid'
    mock_create_user.assert_called_once()

def test_verify_firebase_token_no_token(client):
    """Test Firebase token verification without token"""
    response = client.post('/api/auth/verify', json={})
    assert response.status_code == 400
    assert response.json['error'] == "No ID token provided"

@patch('app.routes.auth.verify_id_token') # Standardized patch path
def test_verify_firebase_token_invalid_token(mock_verify_token, client):
    """Test Firebase token verification with invalid token"""
    mock_verify_token.side_effect = firebase_admin.auth.InvalidIdTokenError("Invalid token")
    response = client.post('/api/auth/verify', json={'idToken': 'invalid-token'})
    assert response.status_code == 401
    assert response.json['error'] == "Invalid ID token"
    
# ... (other user and auth tests would be similarly refactored) ...

@patch('app.auth_utils.auth.verify_id_token') # CORRECTED PATH
@patch('app.models.Event.create_event')
def test_create_event_success(mock_create_event, mock_verify_token, client):
    """Test successful event creation"""
    mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
    mock_event = Mock()
    mock_event.to_dict.return_value = {
        "event_id": 1, "title": "Community Meetup", "location": "Community Hall"
    }
    mock_create_event.return_value = mock_event

    event_data = {
        "Title": "Community Meetup", "Description": "A meetup for the local community.",
        "StartTime": "2025-09-30T10:00:00", "EndTime": "2025-09-30T12:00:00",
        "Location": "Community Hall", "CategoryID": 1
    }

    response = client.post(
        "/events",
        json=event_data,
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 201
    assert response.json["success"] is True
    assert response.json["new_event"]["title"] == "Community Meetup"

@patch('app.models.Event.get_all_events')
def test_get_events_success(mock_get_all_events, client):
    """Test successful retrieval of all events"""
    mock_event = Mock()
    mock_event.to_dict.return_value = {"event_id": 1, "title": "Community Meetup"}
    mock_get_all_events.return_value = [mock_event]

    response = client.get("/events")

    assert response.status_code == 200
    assert response.json["success"] is True
    assert len(response.json["events"]) == 1
    assert response.json["events"][0]["title"] == "Community Meetup"

@patch('app.auth_utils.auth.verify_id_token') # CORRECTED PATH
@patch('app.models.Event.update_event')
def test_update_event(mock_update_event, mock_verify_token, client):
    """Test creating an event and then updating it"""
    mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
    mock_updated_event = Mock()
    mock_updated_event.to_dict.return_value = {"event_id": 1, "title": "Updated Event Title"}
    mock_update_event.return_value = mock_updated_event

    update_data = {
        "Title": "Updated Event Title",
        "Description": "Updated description",
        "Location": "Updated Location",
        "MaxAttendees": 100
    }
    
    update_response = client.patch(
        "/events/1",
        json=update_data,
        headers={"Authorization": "Bearer valid-token"}
    )

    assert update_response.status_code == 200
    assert update_response.json["success"] is True
    assert update_response.json["updated_event"]["title"] == "Updated Event Title"
@patch('app.auth_utils.auth.verify_id_token') # CORRECTED PATH
@patch('app.models.Event.delete_event')
def test_delete_event_success(mock_delete_event, mock_verify_token, client):
    """Test successful event deletion"""
    mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
    mock_delete_event.return_value = True

    response = client.delete(
        "/events/1",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["message"] == "Event deleted successfully"