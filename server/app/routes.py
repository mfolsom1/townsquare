from datetime import datetime
from flask import Flask, jsonify, request
from .models import Event
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
            # Get the ID token and additional user data from the request
            request_data = request.json or {}
            id_token = request_data.get('idToken')
            user_data = request_data.get('userData', {})

            print(f"Backend received user_data: {user_data}")  # Debug log

            if not id_token:
                return jsonify({"error": "No ID token provided"}), 400

            # Verify the ID token with Firebase
            decoded_token = auth.verify_id_token(id_token)
            firebase_uid = decoded_token['uid']
            email = decoded_token.get('email')

            # Check if user exists in our database
            existing_user = User.get_user_by_firebase_uid(firebase_uid)

            if existing_user:
                # Debug log
                print(f"User already exists: {existing_user.username}")
                # User exists, return user data
                return jsonify({
                    "success": True,
                    "user": existing_user.to_dict()
                })
            else:
                # User doesn't exist, create new user
                # For new user creation, username is mandatory
                username = user_data.get('username')
                if not username:
                    return jsonify({"error": "Username is required for account creation"}), 400

                # Debug log
                print(f"Creating new user with username: {username}")

                # Validate username format
                username = username.strip()
                if len(username) < 3 or len(username) > 20:
                    return jsonify({"error": "Username must be between 3 and 20 characters"}), 400

                if not username.replace('_', '').replace('-', '').isalnum():
                    return jsonify({"error": "Username can only contain letters, numbers, underscores, and hyphens"}), 400
                try:
                    # Extract name info from user_data or Firebase token
                    full_name = user_data.get(
                        'name') or decoded_token.get('name') or ''
                    name_parts = full_name.split(
                        ' ', 1) if full_name else ['', '']

                    first_name = (decoded_token.get('given_name') or
                                  name_parts[0] if name_parts[0] else None)
                    last_name = (decoded_token.get('family_name') or
                                 name_parts[1] if len(name_parts) > 1 and name_parts[1] else None)
                    # Determine account type (defaults to individual)
                    user_type = user_data.get('user_type', 'individual')
                    if user_type not in ('individual', 'organization'):
                        user_type = 'individual'
                    organization_name = user_data.get('organization_name')

                    new_user = User.create_user(
                        firebase_uid=firebase_uid,
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        location="Unknown",  # Default location, can be updated later
                        user_type=user_type,
                        organization_name=organization_name
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
            # Explicit check for missing or invalid firebase_uid
            if not firebase_uid:
                return jsonify({"error": "You must be logged in to update your profile."}), 401

            update_data = request.json or {}
            allowed_fields = ['username', 'first_name', 'last_name',
                              'location', 'bio', 'interests', 'user_type', 'organization_name']

            # Filter and validate data
            filtered_data = {k: v for k, v in update_data.items()
                             if k in allowed_fields and v is not None}

            # Special validation for interests
            if 'interests' in filtered_data:
                interests = filtered_data['interests']
                if not isinstance(interests, list):
                    return jsonify({"error": "Interests must be provided as a list"}), 400
                # Validate each interest is a string and not empty
                for interest in interests:
                    if not isinstance(interest, str) or not interest.strip():
                        return jsonify({"error": "Each interest must be a non-empty string"}), 400
                # Clean up interest names (strip whitespace)
                filtered_data['interests'] = [interest.strip()
                                              for interest in interests]

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

        except pyodbc.IntegrityError as e:
            # Return a clearer, generic integrity error for profile updates.
            # The previous message always said 'Username already exists' which is
            # misleading when updating interests or other fields. Include the
            # original error text in the response for easier debugging (can be
            # removed or reduced in production).
            return jsonify({"error": "Database integrity error", "details": str(e)}), 409
        except Exception as e:
            return jsonify({"error": f"Failed to update user profile: {str(e)}"}), 500

    @app.route('/api/user/organization', methods=['POST'])
    @require_auth
    def upgrade_to_organization(firebase_uid):
        """Basic endpoint to convert current user to an organization account."""
        try:
            body = request.json or {}
            org_name = body.get('organization_name')
            # Set the user type and optional organization name
            success = User.update_user(
                firebase_uid, user_type='organization', organization_name=org_name)
            if not success:
                return jsonify({"error": "Failed to update user to organization"}), 400
            user = User.get_user_by_firebase_uid(firebase_uid)
            return jsonify({
                "success": True,
                "message": "User upgraded to organization",
                "user": user.to_dict()
            })
        except Exception as e:
            return jsonify({"error": f"Failed to upgrade to organization: {str(e)}"}), 500

    @app.route('/api/user/interests', methods=['GET'])
    @require_auth
    def get_user_interests(firebase_uid):
        """Get user's interests"""
        try:
            interests = User.get_user_interests_by_uid(firebase_uid)
            return jsonify({
                "success": True,
                "interests": interests
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get user interests: {str(e)}"}), 500

    @app.route('/api/user/interests', methods=['POST'])
    @require_auth
    def add_user_interest(firebase_uid):
        """Add an interest to user's profile"""
        try:
            data = request.json or {}
            interest_name = data.get('interest')

            if not interest_name or not isinstance(interest_name, str) or not interest_name.strip():
                return jsonify({"error": "Interest name is required and must be a non-empty string"}), 400

            interest_name = interest_name.strip()
            success = User.add_user_interest(firebase_uid, interest_name)

            if success:
                interests = User.get_user_interests_by_uid(firebase_uid)
                return jsonify({
                    "success": True,
                    "message": "Interest added successfully",
                    "interests": interests
                })
            else:
                return jsonify({"error": "Failed to add interest"}), 400

        except Exception as e:
            return jsonify({"error": f"Failed to add interest: {str(e)}"}), 500

    @app.route('/api/user/interests', methods=['DELETE'])
    @require_auth
    def remove_user_interest(firebase_uid):
        """Remove an interest from user's profile"""
        try:
            data = request.json or {}
            interest_name = data.get('interest')

            if not interest_name or not isinstance(interest_name, str) or not interest_name.strip():
                return jsonify({"error": "Interest name is required and must be a non-empty string"}), 400

            interest_name = interest_name.strip()
            success = User.remove_user_interest(firebase_uid, interest_name)

            if success:
                interests = User.get_user_interests_by_uid(firebase_uid)
                return jsonify({
                    "success": True,
                    "message": "Interest removed successfully",
                    "interests": interests
                })
            else:
                return jsonify({"error": "Interest not found or already removed"}), 404

        except Exception as e:
            return jsonify({"error": f"Failed to remove interest: {str(e)}"}), 500

    @app.route('/api/interests', methods=['GET'])
    def get_all_interests():
        """Get all available interests in the system"""
        try:
            interests = User.get_all_interests()
            return jsonify({
                "success": True,
                "interests": interests
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get interests: {str(e)}"}), 500

    # ===== Event functions ===== #
    @app.route('/events', methods=['GET'])
    def get_events():
        try:
            events = Event.get_all_events()
            # Returns a 200 OK with an empty list if no events are found, which is more conventional.
            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events]
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/events/<int:event_id>', methods=['GET'])
    def get_event_by_id(event_id):
        try:
            event = Event.get_event_by_id(event_id)

            if not event:
                return jsonify({"error": "Event not found"}), 404

            return jsonify({
                "success": True,
                "event": event.to_dict()
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/events', methods=['POST'])
    @require_auth
    def create_event(firebase_uid):
        try:
            # Only org accounts can create events
            requester = User.get_user_by_firebase_uid(firebase_uid)
            if not requester:
                return jsonify({"error": "User not found"}), 404
            if requester.user_type != 'organization':
                return jsonify({"error": "Only organization accounts can create events"}), 403
            # Parse JSON data from the request
            data = request.get_json()

            # Validate required fields (CategoryID is now included)
            required_fields = ['Title', 'StartTime',
                               'EndTime', 'Location', 'CategoryID']
            missing_fields = [
                field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

            # Create a new Event object
            new_event = Event.create_event(
                organizer_uid=firebase_uid,
                title=data['Title'],
                description=data.get('Description'),
                start_time=(data['StartTime']),
                end_time=(data['EndTime']),
                location=data['Location'],
                category_id=data['CategoryID'],  # Now a required field
                max_attendees=data.get('MaxAttendees'),
                image_url=data.get('ImageURL')
            )

            return jsonify({
                "success": True,
                "message": "Event created successfully",
                "new_event": new_event.to_dict()
            }), 201
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Changed to PATCH for partial updates, which is more REST-compliant.
    @app.route('/events/<int:event_id>', methods=['PATCH'])
    @require_auth
    def update_event(firebase_uid, event_id):
        try:
            data = request.get_json()

            # Keys are now PascalCase to be consistent with the create_event endpoint.
            update_fields = ['Title', 'Description', 'StartTime', 'EndTime',
                             'Location', 'CategoryID', 'MaxAttendees', 'ImageURL']
            update_data = {field: data[field]
                           for field in update_fields if field in data}

            if not update_data:
                return jsonify({"error": "No fields to update provided"}), 400

            # Convert PascalCase keys from JSON to snake_case for the model function call
            update_kwargs = {
                'title': update_data.get('Title'),
                'description': update_data.get('Description'),
                'start_time': update_data.get('StartTime'),
                'end_time': update_data.get('EndTime'),
                'location': update_data.get('Location'),
                'category_id': update_data.get('CategoryID'),
                'max_attendees': update_data.get('MaxAttendees'),
                'image_url': update_data.get('ImageURL')
            }
            # Remove keys that were not provided
            update_kwargs = {k: v for k,
                             v in update_kwargs.items() if v is not None}

            updated_event = Event.update_event(
                event_id,
                firebase_uid,
                **update_kwargs
            )

            if not updated_event:
                return jsonify({"error": "Event not found or not authorized to update"}), 404

            return jsonify({
                "success": True,
                "message": "Event updated successfully",
                "updated_event": updated_event.to_dict()
            }), 200
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/events/<int:event_id>', methods=['DELETE'])
    @require_auth
    def delete_event(firebase_uid, event_id):
        try:
            success = Event.delete_event(event_id, firebase_uid)

            if not success:
                return jsonify({"error": "Event not found or user not authorized"}), 404

            return jsonify({
                "success": True,
                "message": "Event deleted successfully"
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Recommendation functions =====
    @app.route('/recommendations/<int:user_id>', methods=['GET'])
    def get_recommendations(user_id):
        return jsonify([])

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
