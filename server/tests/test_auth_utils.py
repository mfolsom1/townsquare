"""
Unit tests for authentication utilities
"""
import pytest
from unittest.mock import Mock, patch
from flask import Flask, request
from app.auth_utils import require_auth
import firebase_admin

class TestRequireAuth:
    """Test the require_auth decorator"""
    
    def setup_method(self):
        """Setup test Flask app for each test"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_require_auth_valid_token(self, mock_verify_token):
        """Test require_auth with valid Firebase token"""
        # Setup mock
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
        
        # Create a test route with the decorator
        @self.app.route('/test')
        @require_auth
        def test_route(firebase_uid):
            return {'firebase_uid': firebase_uid}
        
        with self.app.test_client() as client:
            response = client.get('/test', headers={
                'Authorization': 'Bearer valid-token'
            })
            
            assert response.status_code == 200
            mock_verify_token.assert_called_once_with('valid-token')
    
    def test_require_auth_no_authorization_header(self):
        """Test require_auth with no Authorization header"""
        @self.app.route('/test')
        @require_auth
        def test_route(firebase_uid):
            return {'firebase_uid': firebase_uid}
        
        with self.app.test_client() as client:
            response = client.get('/test')
            
            assert response.status_code == 401
            assert response.json['error'] == "No authorization token provided"
    
    def test_require_auth_invalid_header_format(self):
        """Test require_auth with invalid Authorization header format"""
        @self.app.route('/test')
        @require_auth
        def test_route(firebase_uid):
            return {'firebase_uid': firebase_uid}
        
        with self.app.test_client() as client:
            response = client.get('/test', headers={
                'Authorization': 'InvalidFormat token'
            })
            
            assert response.status_code == 401
            assert response.json['error'] == "No authorization token provided"
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_require_auth_invalid_token(self, mock_verify_token):
        """Test require_auth with invalid Firebase token"""
        # Setup mock to raise InvalidIdTokenError
        mock_verify_token.side_effect = firebase_admin.auth.InvalidIdTokenError("Invalid token")
        
        @self.app.route('/test')
        @require_auth
        def test_route(firebase_uid):
            return {'firebase_uid': firebase_uid}
        
        with self.app.test_client() as client:
            response = client.get('/test', headers={
                'Authorization': 'Bearer invalid-token'
            })
            
            assert response.status_code == 401
            assert response.json['error'] == "Invalid authorization token"
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_require_auth_general_exception(self, mock_verify_token):
        """Test require_auth with general exception during verification"""
        # Setup mock to raise general exception
        mock_verify_token.side_effect = Exception("Network error")
        
        @self.app.route('/test')
        @require_auth
        def test_route(firebase_uid):
            return {'firebase_uid': firebase_uid}
        
        with self.app.test_client() as client:
            response = client.get('/test', headers={
                'Authorization': 'Bearer some-token'
            })
            
            assert response.status_code == 500
            assert "Authentication failed: Network error" in response.json['error']
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_require_auth_passes_firebase_uid_to_route(self, mock_verify_token):
        """Test that require_auth passes firebase_uid to the decorated function"""
        # Setup mock
        mock_verify_token.return_value = {'uid': 'test-firebase-uid-123'}
        
        @self.app.route('/test')
        @require_auth
        def test_route(firebase_uid):
            return {'received_uid': firebase_uid}
        
        with self.app.test_client() as client:
            response = client.get('/test', headers={
                'Authorization': 'Bearer valid-token'
            })
            
            assert response.status_code == 200
            assert response.json['received_uid'] == 'test-firebase-uid-123'
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_require_auth_preserves_other_args_and_kwargs(self, mock_verify_token):
        """Test that require_auth preserves other function arguments"""
        # Setup mock
        mock_verify_token.return_value = {'uid': 'test-firebase-uid'}
        
        @self.app.route('/test/<param>')
        @require_auth
        def test_route(param, firebase_uid):
            return {'param': param, 'firebase_uid': firebase_uid}
        
        with self.app.test_client() as client:
            response = client.get('/test/hello', headers={
                'Authorization': 'Bearer valid-token'
            })
            
            assert response.status_code == 200
            assert response.json['param'] == 'hello'
            assert response.json['firebase_uid'] == 'test-firebase-uid'