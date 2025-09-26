# routes.py: Define API endpoints
from flask import jsonify, request
from firebase_admin import auth
from .models import User
from .auth_utils import require_auth
import pyodbc

def register_routes(app):
    @app.route('/')
    def home():
        return jsonify({"message": "Welcome to Townsquare API"})
    
    @app.route('/api/auth/verify', methods=['POST'])
    def verify_firebase_token():
        """Verify Firebase ID token and create/get user in Azure SQL"""
        try:
            # Get the ID token from the request
            id_token = request.json.get('idToken')
            if not id_token:
                return jsonify({"error": "No ID token provided"}), 400
            
            # Verify the ID token with Firebase
            decoded_token = auth.verify_id_token(id_token)
            firebase_uid = decoded_token['uid']
            email = decoded_token.get('email')
            username = decoded_token.get('name') or email.split('@')[0]  # Use email prefix as fallback
            
            # Check if user exists in our database
            existing_user = User.get_user_by_firebase_uid(firebase_uid)
            
            if existing_user:
                # User exists, return user data
                return jsonify({
                    "success": True,
                    "user": existing_user.to_dict()
                })
            else:
                # User doesn't exist, create new user
                try:
                    # Extract additional info from Firebase token if available
                    first_name = decoded_token.get('given_name')
                    last_name = decoded_token.get('family_name')
                    
                    new_user = User.create_user(
                        firebase_uid=firebase_uid, 
                        username=username, 
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        location="Unknown"  # Default location, can be updated later
                    )
                    return jsonify({
                        "success": True,
                        "user": new_user.to_dict(),
                        "message": "User created successfully"
                    })
                except pyodbc.IntegrityError:
                    # Handle duplicate email/username
                    return jsonify({"error": "User with this email or username already exists"}), 409
                
        except auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid ID token"}), 401
        except Exception as e:
            return jsonify({"error": f"Authentication failed: {str(e)}"}), 500
    
    @app.route('/api/user/profile', methods=['GET'])
    @require_auth
    def get_user_profile(firebase_uid):
        """Get user profile (requires Firebase token in Authorization header)"""
        try:
            user = User.get_user_by_firebase_uid(firebase_uid)
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            return jsonify({
                "success": True,
                "user": user.to_dict()
            })
            
        except Exception as e:
            return jsonify({"error": f"Failed to get user profile: {str(e)}"}), 500
    
    @app.route('/api/user/profile', methods=['PUT'])
    @require_auth
    def update_user_profile(firebase_uid):
        """Update user profile (requires Firebase token in Authorization header)"""
        try:
            update_data = request.json or {}
            allowed_fields = ['username', 'first_name', 'last_name', 'location', 'bio']
            
            # Filter and validate data
            filtered_data = {k: v for k, v in update_data.items() 
                           if k in allowed_fields and v is not None}
            
            if not filtered_data:
                return jsonify({"error": "No valid fields to update"}), 400
            
            # Update user in database
            success = User.update_user(firebase_uid, **filtered_data)
            
            if success:
                # Return updated user data
                user = User.get_user_by_firebase_uid(firebase_uid)
                return jsonify({
                    "success": True,
                    "message": "Profile updated successfully",
                    "user": user.to_dict()
                })
            else:
                return jsonify({"error": "No fields were updated"}), 400
            
        except pyodbc.IntegrityError:
            return jsonify({"error": "Username already exists"}), 409
        except Exception as e:
            return jsonify({"error": f"Failed to update user profile: {str(e)}"}), 500