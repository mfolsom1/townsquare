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
            patch('firebase_admin.credentials.Certificate'), \
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


@patch('app.routes.auth.verify_id_token')  # Standardized patch path
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


@patch('app.routes.auth.verify_id_token')  # Standardized patch path
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


@patch('app.routes.auth.verify_id_token')  # Standardized patch path
def test_verify_firebase_token_invalid_token(mock_verify_token, client):
    """Test Firebase token verification with invalid token"""
    mock_verify_token.side_effect = firebase_admin.auth.InvalidIdTokenError(
        "Invalid token")
    response = client.post(
        '/api/auth/verify', json={'idToken': 'invalid-token'})
    assert response.status_code == 401
    assert response.json['error'] == "Invalid ID token"

# ... (other user and auth tests would be similarly refactored) ...


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.create_event')
@patch('app.models.User.get_user_by_firebase_uid')
def test_create_event_success(mock_get_user, mock_create_event, mock_verify_token, client):
    """Test successful event creation"""
    mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
    # Requester must be an org user
    mock_user = Mock()
    mock_user.user_type = 'organization'
    mock_get_user.return_value = mock_user
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


# CORRECTED PATH TODO: Delete these comments
@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.update_event')
def test_update_event(mock_update_event, mock_verify_token, client):
    """Test creating an event and then updating it"""
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


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.delete_event')
@patch('app.models.User.get_user_by_firebase_uid')
def test_delete_event_success(mock_get_user, mock_delete_event, mock_verify_token, client):
    """Test successful permanent event deletion"""
    mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
    org_user = Mock()
    org_user.user_type = 'organization'
    mock_get_user.return_value = org_user
    mock_delete_event.return_value = True

    response = client.delete(
        "/events/1",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["message"] == "Event permanently deleted"
    mock_delete_event.assert_called_once_with(1, 'test-firebase-uid')


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.delete_event')
@patch('app.models.User.get_user_by_firebase_uid')
def test_delete_event_not_found(mock_get_user, mock_delete_event, mock_verify_token, client):
    """Test deletion of non-existent event"""
    mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
    org_user = Mock()
    org_user.user_type = 'organization'
    mock_get_user.return_value = org_user
    mock_delete_event.return_value = False

    response = client.delete(
        "/events/999",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 404
    assert response.json["error"] == "Event not found or user not authorized"


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.User.get_user_by_firebase_uid')
def test_create_event_individual(mock_get_user, mock_verify_token, client):
    """Ensure individuals cannot create events (403)."""
    mock_verify_token.return_value = {'uid': 'indiv-uid'}
    indiv = Mock()
    indiv.user_type = 'individual'
    mock_get_user.return_value = indiv

    event_data = {
        "Title": "Community Meetup",
        "Description": "desc",
        "StartTime": "2025-09-30T10:00:00",
        "EndTime": "2025-09-30T12:00:00",
        "Location": "Hall",
        "CategoryID": 1
    }

    resp = client.post(
        "/events",
        json=event_data,
        headers={"Authorization": "Bearer valid-token"}
    )

    assert resp.status_code == 403
    assert resp.json["error"] == "Organization account required"


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.User.get_user_by_firebase_uid')
def test_delete_event_individual(mock_get_user, mock_verify_token, client):
    """Ensure individuals cannot delete events (403)."""
    mock_verify_token.return_value = {'uid': 'indiv-uid'}
    indiv = Mock()
    indiv.user_type = 'individual'
    mock_get_user.return_value = indiv

    resp = client.delete(
        "/events/1",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert resp.status_code == 403
    assert resp.json["error"] == "Organization account required"


# ===== Archiving Tests ===== #


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.archive_event')
@patch('app.models.User.get_user_by_firebase_uid')
def test_archive_event_success(mock_get_user, mock_archive_event, mock_verify_token, client):
    """Test successful event archiving"""
    mock_verify_token.return_value = {'uid': 'org-firebase-uid'}
    org_user = Mock()
    org_user.user_type = 'organization'
    mock_get_user.return_value = org_user

    mock_event = Mock()
    mock_event.to_dict.return_value = {
        "event_id": 1,
        "title": "Test Event",
        "is_archived": True,
        "archived_at": "2025-11-12T10:00:00"
    }
    mock_archive_event.return_value = mock_event

    response = client.post(
        "/events/1/archive",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["message"] == "Event archived successfully"
    assert response.json["archived_event"]["is_archived"] is True
    mock_archive_event.assert_called_once_with(1, 'org-firebase-uid')


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.archive_event')
@patch('app.models.User.get_user_by_firebase_uid')
def test_archive_event_not_found(mock_get_user, mock_archive_event, mock_verify_token, client):
    """Test archiving non-existent event"""
    mock_verify_token.return_value = {'uid': 'org-firebase-uid'}
    org_user = Mock()
    org_user.user_type = 'organization'
    mock_get_user.return_value = org_user
    mock_archive_event.return_value = None

    response = client.post(
        "/events/999/archive",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 404
    assert response.json["error"] == "Event not found or already archived"


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.archive_event')
@patch('app.models.User.get_user_by_firebase_uid')
def test_archive_event_not_authorized(mock_get_user, mock_archive_event, mock_verify_token, client):
    """Test archiving event by non-organizer"""
    mock_verify_token.return_value = {'uid': 'org-firebase-uid'}
    org_user = Mock()
    org_user.user_type = 'organization'
    mock_get_user.return_value = org_user
    mock_archive_event.return_value = False

    response = client.post(
        "/events/1/archive",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 403
    assert response.json["error"] == "Not authorized to archive this event"


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.User.get_user_by_firebase_uid')
def test_archive_event_individual_user(mock_get_user, mock_verify_token, client):
    """Test that individual users cannot archive events"""
    mock_verify_token.return_value = {'uid': 'indiv-uid'}
    indiv = Mock()
    indiv.user_type = 'individual'
    mock_get_user.return_value = indiv

    response = client.post(
        "/events/1/archive",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 403
    assert response.json["error"] == "Organization account required"


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.get_events_by_organizer')
@patch('app.models.User.get_user_by_firebase_uid')
def test_get_user_archived_events(mock_get_user, mock_get_events, mock_verify_token, client):
    """Test getting archived events for organization user"""
    mock_verify_token.return_value = {'uid': 'org-firebase-uid'}
    org_user = Mock()
    org_user.user_type = 'organization'
    mock_get_user.return_value = org_user

    # Create mock archived and active events
    archived_event = Mock()
    archived_event.is_archived = True
    archived_event.to_dict.return_value = {
        "event_id": 1,
        "title": "Archived Event",
        "is_archived": True
    }

    active_event = Mock()
    active_event.is_archived = False
    active_event.to_dict.return_value = {
        "event_id": 2,
        "title": "Active Event",
        "is_archived": False
    }

    mock_get_events.return_value = [archived_event, active_event]

    response = client.get(
        "/api/user/events/archived",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    assert len(response.json["events"]) == 1
    assert response.json["events"][0]["is_archived"] is True
    mock_get_events.assert_called_once_with(
        'org-firebase-uid', include_archived=True)


@patch('app.auth_utils.auth.verify_id_token')
@patch('app.models.Event.get_events_by_organizer')
def test_get_organized_events_with_archived_param(mock_get_events, mock_verify_token, client):
    """Test getting organized events with include_archived parameter"""
    mock_verify_token.return_value = {'uid': 'user-firebase-uid'}
    mock_event = Mock()
    mock_event.to_dict.return_value = {"event_id": 1, "title": "Event"}
    mock_get_events.return_value = [mock_event]

    # Test with include_archived=true
    response = client.get(
        "/api/user/events/organized?include_archived=true",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    mock_get_events.assert_called_once_with(
        'user-firebase-uid', include_archived=True)

    # Test with include_archived=false (default)
    mock_get_events.reset_mock()
    response = client.get(
        "/api/user/events/organized",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    mock_get_events.assert_called_once_with(
        'user-firebase-uid', include_archived=False)
