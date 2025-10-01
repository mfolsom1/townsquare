"""
Integration tests for API routes
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
import pyodbc
import firebase_admin
from app import create_app
from app.models import User

class TestRoutes:
    """Test API routes and endpoints"""
    
    def setup_method(self):
        """Setup test Flask app for each test"""
        # Mock Firebase initialization to prevent actual Firebase calls
        with patch('firebase_admin._apps', {}), \
             patch('firebase_admin.initialize_app'), \
             patch('app.database.init_database'):
            self.app = create_app()
            self.app.config['TESTING'] = True
            self.client = self.app.test_client()
    
    def test_home_route(self):
        """Test the home route"""
        response = self.client.get('/')
        
        assert response.status_code == 200
        assert response.json['message'] == "Welcome to Townsquare API"
    
    @patch('firebase_admin.auth.verify_id_token')
    @patch('app.models.User.get_user_by_firebase_uid')
    def test_verify_firebase_token_existing_user(self, mock_get_user, mock_verify_token):
        """Test Firebase token verification with existing user"""
        # Setup mocks
        mock_verify_token.return_value = {
            'uid': 'test-firebase-uid',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        mock_user = Mock()
        mock_user.to_dict.return_value = {
            'firebase_uid': 'test-firebase-uid',
            'username': 'testuser',
            'email': 'test@example.com'
        }
        mock_get_user.return_value = mock_user
        
        # Test the endpoint
        response = self.client.post('/api/auth/verify', 
                                  json={'idToken': 'valid-token'})
        
        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['user']['firebase_uid'] == 'test-firebase-uid'
        mock_verify_token.assert_called_once_with('valid-token')
        mock_get_user.assert_called_once_with('test-firebase-uid')
    
    @patch('firebase_admin.auth.verify_id_token')
    @patch('app.models.User.get_user_by_firebase_uid')
    @patch('app.models.User.create_user')
    def test_verify_firebase_token_new_user(self, mock_create_user, mock_get_user, mock_verify_token):
        """Test Firebase token verification with new user creation"""
        # Setup mocks
        mock_verify_token.return_value = {
            'uid': 'new-firebase-uid',
            'email': 'newuser@example.com',
            'name': 'New User',
            'given_name': 'New',
            'family_name': 'User'
        }
        
        mock_get_user.return_value = None  # User doesn't exist
        
        mock_new_user = Mock()
        mock_new_user.to_dict.return_value = {
            'firebase_uid': 'new-firebase-uid',
            'username': 'newuser',
            'email': 'newuser@example.com'
        }
        mock_create_user.return_value = mock_new_user
        
        # Test the endpoint
        response = self.client.post('/api/auth/verify', 
                                  json={'idToken': 'valid-token'})
        
        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['message'] == "User created successfully"
        assert response.json['user']['firebase_uid'] == 'new-firebase-uid'
        
        mock_create_user.assert_called_once_with(
            firebase_uid='new-firebase-uid',
            username='New User',  # Falls back to name from token
            email='newuser@example.com',
            first_name='New',
            last_name='User',
            location='Unknown'
        )
    
    def test_verify_firebase_token_no_token(self):
        """Test Firebase token verification without token"""
        response = self.client.post('/api/auth/verify', json={})
        
        assert response.status_code == 400
        assert response.json['error'] == "No ID token provided"
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_verify_firebase_token_invalid_token(self, mock_verify_token):
        """Test Firebase token verification with invalid token"""
        mock_verify_token.side_effect = firebase_admin.auth.InvalidIdTokenError("Invalid token")
        
        response = self.client.post('/api/auth/verify', 
                                  json={'idToken': 'invalid-token'})
        
        assert response.status_code == 401
        assert response.json['error'] == "Invalid ID token"
    
    @patch('firebase_admin.auth.verify_id_token')
    @patch('app.models.User.get_user_by_firebase_uid')
    @patch('app.models.User.create_user')
    def test_verify_firebase_token_duplicate_user_error(self, mock_create_user, mock_get_user, mock_verify_token):
        """Test Firebase token verification with duplicate user error"""
        # Setup mocks
        mock_verify_token.return_value = {
            'uid': 'test-firebase-uid',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        mock_get_user.return_value = None
        mock_create_user.side_effect = pyodbc.IntegrityError("Duplicate key")
        
        # Test the endpoint
        response = self.client.post('/api/auth/verify', 
                                  json={'idToken': 'valid-token'})
        
        assert response.status_code == 409
        assert response.json['error'] == "User with this email or username already exists"
    
    @patch('app.auth_utils.auth.verify_id_token')
    @patch('app.models.User.get_user_by_firebase_uid')
    def test_get_user_profile_success(self, mock_get_user, mock_verify_token):
        """Test successful user profile retrieval"""
        # Setup mocks
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
        
        mock_user = Mock()
        mock_user.to_dict.return_value = {
            'firebase_uid': 'test-firebase-uid',
            'username': 'testuser',
            'email': 'test@example.com'
        }
        mock_get_user.return_value = mock_user
        
        # Test the endpoint
        response = self.client.get('/api/user/profile', 
                                 headers={'Authorization': 'Bearer valid-token'})
        
        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['user']['firebase_uid'] == 'test-firebase-uid'
    
    @patch('app.auth_utils.auth.verify_id_token')
    @patch('app.models.User.get_user_by_firebase_uid')
    def test_get_user_profile_user_not_found(self, mock_get_user, mock_verify_token):
        """Test user profile retrieval when user not found"""
        # Setup mocks
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
        mock_get_user.return_value = None
        
        # Test the endpoint
        response = self.client.get('/api/user/profile', 
                                 headers={'Authorization': 'Bearer valid-token'})
        
        assert response.status_code == 404
        assert response.json['error'] == "User not found"
    
    def test_get_user_profile_no_auth(self):
        """Test user profile retrieval without authentication"""
        response = self.client.get('/api/user/profile')
        
        assert response.status_code == 401
        assert response.json['error'] == "No authorization token provided"
    
    @patch('app.auth_utils.auth.verify_id_token')
    @patch('app.models.User.update_user')
    @patch('app.models.User.get_user_by_firebase_uid')
    def test_update_user_profile_success(self, mock_get_user, mock_update_user, mock_verify_token):
        """Test successful user profile update"""
        # Setup mocks
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
        mock_update_user.return_value = True
        
        mock_user = Mock()
        mock_user.to_dict.return_value = {
            'firebase_uid': 'test-firebase-uid',
            'username': 'updateduser',
            'email': 'test@example.com'
        }
        mock_get_user.return_value = mock_user
        
        # Test the endpoint
        update_data = {
            'username': 'updateduser',
            'first_name': 'Updated',
            'bio': 'Updated bio'
        }
        response = self.client.put('/api/user/profile', 
                                 json=update_data,
                                 headers={'Authorization': 'Bearer valid-token'})
        
        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['message'] == "Profile updated successfully"
        assert response.json['user']['username'] == 'updateduser'
        
        mock_update_user.assert_called_once_with('test-firebase-uid', 
                                               username='updateduser',
                                               first_name='Updated',
                                               bio='Updated bio')
    
    @patch('app.auth_utils.auth.verify_id_token')
    def test_update_user_profile_no_valid_fields(self, mock_verify_token):
        """Test user profile update with no valid fields"""
        # Setup mocks
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
        
        # Test the endpoint with invalid fields
        update_data = {
            'invalid_field': 'value',
            'another_invalid': 'value'
        }
        response = self.client.put('/api/user/profile', 
                                 json=update_data,
                                 headers={'Authorization': 'Bearer valid-token'})
        
        assert response.status_code == 400
        assert response.json['error'] == "No valid fields to update"
    
    @patch('app.auth_utils.auth.verify_id_token')
    @patch('app.models.User.update_user')
    def test_update_user_profile_no_changes(self, mock_update_user, mock_verify_token):
        """Test user profile update when no changes are made"""
        # Setup mocks
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
        mock_update_user.return_value = False
        
        # Test the endpoint
        update_data = {'username': 'testuser'}
        response = self.client.put('/api/user/profile', 
                                 json=update_data,
                                 headers={'Authorization': 'Bearer valid-token'})
        
        assert response.status_code == 400
        assert response.json['error'] == "No fields were updated"
    
    @patch('app.auth_utils.auth.verify_id_token')
    @patch('app.models.User.update_user')
    def test_update_user_profile_duplicate_username(self, mock_update_user, mock_verify_token):
        """Test user profile update with duplicate username"""
        # Setup mocks
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
        mock_update_user.side_effect = pyodbc.IntegrityError("Duplicate username")
        
        # Test the endpoint
        update_data = {'username': 'existinguser'}
        response = self.client.put('/api/user/profile', 
                                 json=update_data,
                                 headers={'Authorization': 'Bearer valid-token'})
        
        assert response.status_code == 409
        assert response.json['error'] == "Username already exists"
    
    @patch('app.auth_utils.auth.verify_id_token')
    @patch('app.models.Event.create_event')
    def test_create_event_success(self, mock_create_event, mock_verify_token):
        """Test successful event creation"""
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}

        mock_event = Mock()
        mock_event.to_dict.return_value = {
            "event_id": 1,
            "organizer_uid": "test-firebase-uid",
            "title": "Community Meetup",
            "description": "A meetup for the local community.",
            "start_time": "2025-09-30T10:00:00",
            "end_time": "2025-09-30T12:00:00",
            "location": "Community Hall",
            "category_id": 1,
            "max_attendees": 50,
            "image_url": "",
            "created_at": "2025-09-26T12:00:00",
            "updated_at": "2025-09-26T12:00:00"
        }
        mock_create_event.return_value = mock_event

        event_data = {
            "Title": "Community Meetup",
            "Description": "A meetup for the local community.",
            "StartTime": "2025-09-30T10:00:00",
            "EndTime": "2025-09-30T12:00:00",
            "Location": "Community Hall",
            "CategoryID": 1,
            "MaxAttendees": 50,
            "ImageURL": ""
        }

        # POST request
        response = self.client.post(
            "/events",
            json=event_data,
            headers={"Authorization": "Bearer valid-token"}
        )

        # Check output
        assert response.status_code == 201
        response_json = response.get_json()
        assert response_json["success"] is True
        assert response_json["message"] == "Event created successfully"
        assert "new_event" in response_json
        assert response_json["new_event"]["title"] == "Community Meetup"
        assert response_json["new_event"]["location"] == "Community Hall"
    
    @patch('app.models.Event.get_all_events')
    def test_get_events_success(self, mock_get_all_events):
        """Test successful retrieval of all events"""
        mock_event = Mock()
        mock_event.to_dict.return_value = {
            "event_id": 1,
            "organizer_uid": "test-firebase-uid",
            "title": "Community Meetup",
            "description": "A meetup for the local community.",
            "start_time": "2025-09-30T10:00:00",
            "end_time": "2025-09-30T12:00:00",
            "location": "Community Hall",
            "category_id": 1,
            "max_attendees": 50,
            "image_url": "",
            "created_at": "2025-09-26T12:00:00",
            "updated_at": "2025-09-26T12:00:00"
        }
        mock_get_all_events.return_value = [mock_event]

        # Get all events
        response = self.client.get("/events")

        # Check output
        assert response.status_code == 200
        response_json = response.get_json()
        assert response_json["success"] is True
        assert len(response_json["events"]) == 1
        assert response_json["events"][0]["title"] == "Community Meetup"

    @patch('app.models.Event.get_event_by_id')
    def test_get_event_by_id_success(self, mock_get_event_by_id):
        """Test successful retrieval of an event by ID"""
        mock_event = Mock()
        mock_event.to_dict.return_value = {
            "event_id": 1,
            "organizer_uid": "test-firebase-uid",
            "title": "Community Meetup",
            "description": "A meetup for the local community.",
            "start_time": "2025-09-30T10:00:00",
            "end_time": "2025-09-30T12:00:00",
            "location": "Community Hall",
            "category_id": 1,
            "max_attendees": 50,
            "image_url": "",
            "created_at": "2025-09-26T12:00:00",
            "updated_at": "2025-09-26T12:00:00"
        }
        mock_get_event_by_id.return_value = mock_event

        # GET request by ID
        response = self.client.get("/events/1")

        # Check output
        assert response.status_code == 200
        response_json = response.get_json()
        assert response_json["success"] is True
        assert response_json["event"]["title"] == "Community Meetup"
    
    @patch('app.auth_utils.auth.verify_id_token')
    @patch('app.models.Event.create_event')
    @patch('app.models.Event.update_event')
    def test_create_and_update_event(self, mock_update_event, mock_create_event, mock_verify_token):
        """Test creating an event and then updating it"""
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}

        # Create mock
        mock_created_event = Mock()
        mock_created_event.to_dict.return_value = {
            "event_id": 1,
            "organizer_uid": "test-firebase-uid",
            "title": "Original Event Title",
            "description": "Original description",
            "start_time": "2025-09-30T10:00:00",
            "end_time": "2025-09-30T12:00:00",
            "location": "Original Location",
            "category_id": 1,
            "max_attendees": 50,
            "image_url": "",
            "created_at": "2025-09-26T12:00:00",
            "updated_at": "2025-09-26T12:00:00"
        }
        mock_create_event.return_value = mock_created_event

        # Update mock
        mock_updated_event = Mock()
        mock_updated_event.to_dict.return_value = {
            "event_id": 1,
            "organizer_uid": "test-firebase-uid",
            "title": "Updated Event Title",
            "description": "Updated description",
            "start_time": "2025-09-30T10:00:00",
            "end_time": "2025-09-30T12:00:00",
            "location": "Updated Location",
            "category_id": 1,
            "max_attendees": 100,
            "image_url": "",
            "created_at": "2025-09-26T12:00:00",
            "updated_at": "2025-09-27T12:00:00"
        }
        mock_update_event.return_value = mock_updated_event

        # Create the event
        create_data = {
            "Title": "Original Event Title",
            "Description": "Original description",
            "StartTime": "2025-09-30T10:00:00",
            "EndTime": "2025-09-30T12:00:00",
            "Location": "Original Location",
            "CategoryID": 1,
            "MaxAttendees": 50,
            "ImageURL": ""
        }
        # CREATE request
        create_response = self.client.post(
            "/events",
            json=create_data,
            headers={"Authorization": "Bearer valid-token"}
        )

        # Check create output
        assert create_response.status_code == 201
        create_response_json = create_response.get_json()
        assert create_response_json["success"] is True
        assert create_response_json["new_event"]["title"] == "Original Event Title"

        # Update the event
        update_data = {
            "title": "Updated Event Title",
            "description": "Updated description",
            "location": "Updated Location",
            "max_attendees": 100
        }
        # UPDATE request
        update_response = self.client.put(
            "/events/1",
            json=update_data,
            headers={"Authorization": "Bearer valid-token"}
        )

        # Check update output
        assert update_response.status_code == 200
        update_response_json = update_response.get_json()
        assert update_response_json["success"] is True
        assert update_response_json["updated_event"]["title"] == "Updated Event Title"
    
    @patch('app.auth_utils.auth.verify_id_token')
    @patch('app.models.Event.delete_event')
    def test_delete_event_success(self, mock_delete_event, mock_verify_token):
        """Test successful event deletion"""
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
        mock_delete_event.return_value = True

        # Delete event
        response = self.client.delete(
            "/events/1",
            headers={"Authorization": "Bearer valid-token"}
        )

        # Check output
        assert response.status_code == 200
        response_json = response.get_json()
        assert response_json["success"] is True
        assert response_json["message"] == "Event deleted successfully"