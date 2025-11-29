"""
Integration tests for API routes
"""
import pytest
import pyodbc
from unittest.mock import Mock, patch
import firebase_admin
from app import create_app


@pytest.fixture
def client():
    """Configures the Flask app for testing and yields a test client."""
    with patch('firebase_admin._apps', {}), \
            patch('firebase_admin.initialize_app'), \
            patch('firebase_admin.credentials.Certificate'), \
            patch('app.database.init_database'):
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client


def test_home_route(client):
    """Test the home route"""
    response = client.get('/')
    assert response.status_code == 200
    assert response.json['message'] == "Welcome to Townsquare API"


@patch('app.routes.auth.verify_id_token')
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


@patch('app.routes.auth.verify_id_token')
@patch('app.models.User.get_user_by_firebase_uid')
@patch('app.models.User.create_user')
def test_verify_firebase_token_new_user(mock_create_user, mock_get_user, mock_verify_token, client):
    """Test Firebase token verification with new user creation"""
    mock_verify_token.return_value = {
        'uid': 'new-firebase-uid', 'email': 'newuser@example.com', 'name': 'New User',
        'given_name': 'New', 'family_name': 'User'
    }
    mock_get_user.return_value = None
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


@patch('app.routes.auth.verify_id_token')
def test_verify_firebase_token_invalid_token(mock_verify_token, client):
    """Test Firebase token verification with invalid token"""
    mock_verify_token.side_effect = firebase_admin.auth.InvalidIdTokenError(
        "Invalid token")
    response = client.post(
        '/api/auth/verify', json={'idToken': 'invalid-token'})
    assert response.status_code == 401
    assert response.json['error'] == "Invalid ID token"


@patch('app.models.User.get_user_by_firebase_uid')
@patch('app.auth_utils.auth.verify_id_token')
def test_create_event_individual_user_forbidden(mock_verify_token, mock_get_user, client):
    """Test that individual users cannot create events"""
    mock_verify_token.return_value = {'uid': 'individual-user-123'}
    individual_user = Mock()
    individual_user.user_type = 'individual'
    mock_get_user.return_value = individual_user

    event_data = {
        "Title": "Community Meetup",
        "Description": "desc",
        "StartTime": "2025-12-30T10:00:00",
        "EndTime": "2025-12-30T12:00:00",
        "Location": "Hall",
        "CategoryID": 1
    }

    response = client.post(
        "/events",
        json=event_data,
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 403
    assert response.json["error"] == "Organization account required"


@patch('app.models.Event.get_events')
def test_get_events_success(mock_get_events, client):
    """Test successful retrieval of all events"""
    mock_event = Mock()
    mock_event.to_dict.return_value = {
        "event_id": 1, "title": "Community Meetup"}
    mock_get_events.return_value = {"events": [mock_event], "total": 1}

    response = client.get("/events")

    assert response.status_code == 200
    assert response.json["success"] is True
    assert len(response.json["events"]) == 1
    assert response.json["events"][0]["title"] == "Community Meetup"


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.update_event')
def test_update_event(mock_update_event, mock_verify_token, client):
    """Test updating an event"""
    mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
    mock_updated_event = Mock()
    mock_updated_event.to_dict.return_value = {
        "event_id": 1, "title": "Updated Event Title"}
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


@patch('app.models.User.get_user_by_firebase_uid')
@patch('app.auth_utils.auth.verify_id_token')
def test_delete_event_individual_user_forbidden(mock_verify_token, mock_get_user, client):
    """Test that individual users cannot delete events"""
    mock_verify_token.return_value = {'uid': 'individual-user-123'}
    individual_user = Mock()
    individual_user.user_type = 'individual'
    mock_get_user.return_value = individual_user

    response = client.delete(
        "/events/1",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 403
    assert response.json["error"] == "Organization account required"


@patch('app.models.User.get_user_by_firebase_uid')
@patch('app.auth_utils.auth.verify_id_token')
def test_archive_event_individual_user_forbidden(mock_verify_token, mock_get_user, client):
    """Test that individual users cannot archive events"""
    mock_verify_token.return_value = {'uid': 'individual-user-123'}
    individual_user = Mock()
    individual_user.user_type = 'individual'
    mock_get_user.return_value = individual_user

    response = client.post(
        "/events/1/archive",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 403
    assert response.json["error"] == "Organization account required"


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.get_events_by_organizer')
def test_get_organized_events_with_archived_param(mock_get_events, mock_verify_token, client):
    """Test getting organized events with include_archived parameter"""
    mock_verify_token.return_value = {'uid': 'user-firebase-uid'}
    mock_event = Mock()
    mock_event.to_dict.return_value = {"event_id": 1, "title": "Event"}
    mock_get_events.return_value = [mock_event]

    response = client.get(
        "/api/user/events/organized?include_archived=true",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    mock_get_events.assert_called_once_with(
        'user-firebase-uid', include_archived=True)

    mock_get_events.reset_mock()
    response = client.get(
        "/api/user/events/organized",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    mock_get_events.assert_called_once_with(
        'user-firebase-uid', include_archived=False)
