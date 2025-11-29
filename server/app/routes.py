from datetime import datetime
from flask import Flask, jsonify, request
from .models import Event, RSVP, User
from .config import Config
from firebase_admin import auth
from .auth_utils import require_auth, require_organization
import pyodbc
import os
import sys
from pathlib import Path

parent_dir = Path(__file__).resolve().parents[2]
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from ml.recommend import RecommendationAPI
    ML_AVAILABLE = True
except Exception as e:
    print(f"Warning: ML recommendation engine not available: {e}")
    ML_AVAILABLE = False


def register_routes(app):

    def transform_event_for_frontend(event):
        """Transform database field names (PascalCase) to frontend field names (snake_case)"""
        def safe_isoformat(dt):
            if dt is None:
                return None
            if hasattr(dt, 'isoformat'):
                return dt.isoformat()
            return str(dt)  # Already a string

        return {
            'event_id': event.get('event_id') or event.get('EventID'),
            'title': event.get('title') or event.get('Title'),
            'description': event.get('description') or event.get('Description'),
            'start_time': safe_isoformat(event.get('start_time') or event.get('StartTime')),
            'end_time': safe_isoformat(event.get('end_time') or event.get('EndTime')),
            'location': event.get('location') or event.get('Location'),
            'category_id': event.get('category_id') or event.get('CategoryID'),
            'image_url': event.get('image_url') or event.get('ImageURL'),
            'max_attendees': event.get('max_attendees') or event.get('MaxAttendees') or 0,
            'organizer_uid': event.get('organizer_uid') or event.get('OrganizerUID'),
            # Preserve ML-specific fields
            'similarity_score': event.get('similarity_score'),
            'friend_boost': event.get('friend_boost'),
            'friend_username': event.get('friend_username'),
            'is_mutual_friend': event.get('is_mutual_friend'),
            'source': event.get('source')
        }

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

                    user_type = user_data.get('userType', 'individual')
                    organization_name = user_data.get('organizationName')

                    new_user = User.create_user(
                        firebase_uid=firebase_uid,
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        location=user_data.get('location', 'Unknown'),
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
            if not firebase_uid:
                return jsonify({"error": "You must be logged in to update your profile."}), 401

            update_data = request.json or {}
            allowed_fields = ['username', 'first_name',
                              'last_name', 'location', 'bio', 'interests']

            # Filter and validate data
            filtered_data = {k: v for k, v in update_data.items()
                             if k in allowed_fields and v is not None}

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

    # ===== Social Connection functions ===== #

    @app.route('/api/social/follow', methods=['POST'])
    @require_auth
    def follow_user(firebase_uid):
        """Follow another user"""
        try:
            data = request.json or {}
            target_username = data.get('username')
            target_uid = data.get('firebase_uid')

            # Must provide either username or firebase_uid
            if not target_username and not target_uid:
                return jsonify({"error": "Either username or firebase_uid is required"}), 400

            # If both are provided, cross-validate
            if target_username and target_uid:
                target_user = User.get_user_by_username(target_username)
                if not target_user:
                    return jsonify({"error": "User not found"}), 404
                if target_user.firebase_uid != target_uid:
                    return jsonify({"error": "Provided username and firebase_uid do not match"}), 400
                # Use the firebase_uid from the username to ensure consistency
                target_uid = target_user.firebase_uid
            # If only username is provided
            elif target_username and not target_uid:
                target_user = User.get_user_by_username(target_username)
                if not target_user:
                    return jsonify({"error": "User not found"}), 404
                target_uid = target_user.firebase_uid

            # Follow the user
            success = User.follow_user(firebase_uid, target_uid)

            if success:
                return jsonify({
                    "success": True,
                    "message": "User followed successfully"
                })
            else:
                return jsonify({"error": "Already following this user"}), 409

        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            return jsonify({"error": f"Failed to follow user: {str(e)}"}), 500

    @app.route('/api/social/unfollow', methods=['POST'])
    @require_auth
    def unfollow_user(firebase_uid):
        """Unfollow a user"""
        try:
            data = request.json or {}
            target_username = data.get('username')
            target_uid = data.get('firebase_uid')

            # Must provide either username or firebase_uid
            if not target_username and not target_uid:
                return jsonify({"error": "Either username or firebase_uid is required"}), 400

            # If both are provided, ensure they refer to the same user
            if target_username and target_uid:
                target_user = User.get_user_by_username(target_username)
                if not target_user:
                    return jsonify({"error": "User not found"}), 404
                if target_user.firebase_uid != target_uid:
                    return jsonify({"error": "Provided username and firebase_uid do not match"}), 400
                # Use the firebase_uid from the username to ensure consistency
                target_uid = target_user.firebase_uid
            # If only username is provided, get the firebase_uid
            elif target_username and not target_uid:
                target_user = User.get_user_by_username(target_username)
                if not target_user:
                    return jsonify({"error": "User not found"}), 404
                target_uid = target_user.firebase_uid

            # Unfollow the user
            success = User.unfollow_user(firebase_uid, target_uid)

            if success:
                return jsonify({
                    "success": True,
                    "message": "User unfollowed successfully"
                })
            else:
                return jsonify({"error": "Not following this user"}), 404

        except Exception as e:
            return jsonify({"error": f"Failed to unfollow user: {str(e)}"}), 500

    @app.route('/api/social/following', methods=['GET'])
    @require_auth
    def get_following(firebase_uid):
        """Get list of users that the current user is following"""
        try:
            following = User.get_following(firebase_uid)
            return jsonify({
                "success": True,
                "following": following,
                "count": len(following)
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get following list: {str(e)}"}), 500

    @app.route('/api/social/followers', methods=['GET'])
    @require_auth
    def get_followers(firebase_uid):
        """Get list of users that are following the current user"""
        try:
            followers = User.get_followers(firebase_uid)
            return jsonify({
                "success": True,
                "followers": followers,
                "count": len(followers)
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get followers list: {str(e)}"}), 500

    @app.route('/api/social/following/<target_uid>', methods=['GET'])
    @require_auth
    def check_following_status(firebase_uid, target_uid):
        """Check if current user is following the target user"""
        try:
            is_following = User.is_following(firebase_uid, target_uid)
            return jsonify({
                "success": True,
                "is_following": is_following
            })
        except Exception as e:
            return jsonify({"error": f"Failed to check following status: {str(e)}"}), 500

    @app.route('/api/social/user/<username>/following', methods=['GET'])
    def get_user_following_by_username(username):
        """Get list of users that a specific user is following (public endpoint)"""
        try:
            # Get user by username
            user = User.get_user_by_username(username)
            if not user:
                return jsonify({"error": "User not found"}), 404

            following = User.get_following(user.firebase_uid)
            return jsonify({
                "success": True,
                "username": username,
                "following": following,
                "count": len(following)
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get following list: {str(e)}"}), 500

    @app.route('/api/social/user/<username>/followers', methods=['GET'])
    def get_user_followers_by_username(username):
        """Get list of users that are following a specific user (public endpoint)"""
        try:
            # Get user by username
            user = User.get_user_by_username(username)
            if not user:
                return jsonify({"error": "User not found"}), 404

            followers = User.get_followers(user.firebase_uid)
            return jsonify({
                "success": True,
                "username": username,
                "followers": followers,
                "count": len(followers)
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get followers list: {str(e)}"}), 500

    @app.route('/api/user/<firebase_uid>/public', methods=['GET'])
    def get_user_public_info(firebase_uid):
        """Get public user information by Firebase UID"""
        try:
            user = User.get_user_by_firebase_uid(firebase_uid)
            if not user:
                return jsonify({"error": "User not found"}), 404

            return jsonify({
                "success": True,
                "user": {
                    "firebase_uid": user.firebase_uid,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "location": user.location,
                    "user_type": user.user_type
                }
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get user info: {str(e)}"}), 500

    # ===== Event functions ===== #
    @app.route('/events', methods=['GET'])
    def get_events():
        try:
            # simple pagination + sorting
            try:
                page = int(request.args.get('page', 1))
            except ValueError:
                page = 1
            try:
                per_page = int(request.args.get('per_page', 20))
            except ValueError:
                per_page = 20

            sort_by = request.args.get('sort_by', 'StartTime')
            sort_dir = request.args.get('sort_dir', 'ASC')

            # only accept the free-text 'q' from the search bar
            q = request.args.get('q')

            result = Event.get_events(
                q=q, page=page, per_page=per_page, sort_by=sort_by, sort_dir=sort_dir)
            events = result['events']
            total = result['total']

            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page if per_page else 0
                }
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/user/events/organized', methods=['GET'])
    @require_auth
    def get_user_organized_events(firebase_uid):
        """Get events organized by the current user"""
        try:
            # Check for include_archived parameter
            include_archived = request.args.get(
                'include_archived', 'false').lower() == 'true'
            events = Event.get_events_by_organizer(
                firebase_uid, include_archived=include_archived)
            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events]
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get organized events: {str(e)}"}), 500

    @app.route('/api/user/events/attending', methods=['GET'])
    @require_auth
    def get_user_attending_events(firebase_uid):
        """Get events the current user is attending"""
        try:
            events = Event.get_events_by_attendee(firebase_uid)
            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events]
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get attending events: {str(e)}"}), 500

    # ===== RSVP functions ===== #
    @app.route('/api/events/<int:event_id>/rsvp', methods=['POST'])
    @require_auth
    def create_or_update_rsvp(firebase_uid, event_id):
        """Create or update an RSVP for an event"""
        try:
            data = request.json or {}
            status = data.get('status', 'Going')

            # Validate status
            valid_statuses = ['Going', 'Interested', 'Not Going']
            if status not in valid_statuses:
                return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

            # Check if event exists
            event = Event.get_event_by_id(event_id)
            if not event:
                return jsonify({"error": "Event not found"}), 404

            rsvp = RSVP.create_or_update_rsvp(firebase_uid, event_id, status)
            return jsonify({
                "success": True,
                "message": "RSVP updated successfully",
                "rsvp": rsvp.to_dict()
            })
        except Exception as e:
            return jsonify({"error": f"Failed to update RSVP: {str(e)}"}), 500

    @app.route('/api/events/<int:event_id>/rsvp', methods=['DELETE'])
    @require_auth
    def delete_rsvp(firebase_uid, event_id):
        """Delete an RSVP for an event"""
        try:
            success = RSVP.delete_rsvp(firebase_uid, event_id)
            if success:
                return jsonify({
                    "success": True,
                    "message": "RSVP deleted successfully"
                })
            else:
                return jsonify({"error": "RSVP not found"}), 404
        except Exception as e:
            return jsonify({"error": f"Failed to delete RSVP: {str(e)}"}), 500

    @app.route('/api/user/rsvps', methods=['GET'])
    @require_auth
    def get_user_rsvps(firebase_uid):
        """Get all RSVPs for the current user"""
        try:
            rsvps = RSVP.get_user_rsvps(firebase_uid)
            return jsonify({
                "success": True,
                "rsvps": [rsvp.to_dict() for rsvp in rsvps]
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get RSVPs: {str(e)}"}), 500

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
    @require_organization
    def create_event(firebase_uid=None, user=None, **kwargs):
        # normalize uid whether decorator passed firebase_uid or a user object
        if not firebase_uid:
            firebase_uid = getattr(user, 'firebase_uid',
                                   None) or getattr(user, 'uid', None)
        if not firebase_uid:
            return jsonify({"error": "Unauthorized"}), 401

        try:
            # Parse JSON data from the request
            data = request.get_json() or {}

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
    @require_organization
    def delete_event(firebase_uid, user, event_id):
        try:
            success = Event.delete_event(event_id, firebase_uid)

            if not success:
                return jsonify({"error": "Event not found or user not authorized"}), 404

            return jsonify({
                "success": True,
                "message": "Event permanently deleted"
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Recommendation functions =====

    # Initialize ML engine (lazy loading)
    _ml_engine = None

    def get_ml_engine():
        """Get or initialize the ML recommendation engine"""
        nonlocal _ml_engine
        if _ml_engine is None and ML_AVAILABLE:
            try:
                _ml_engine = RecommendationAPI()
            except Exception as e:
                print(f"Error initializing ML engine: {e}")
                return None
        return _ml_engine

    @app.route('/api/recommendations', methods=['GET'])
    @require_auth
    def get_recommendations(firebase_uid):
        """Get personalized recommendations for the authenticated user"""
        try:
            # Get query parameters
            top_k = request.args.get('top_k', default=10, type=int)
            strategy = request.args.get('strategy', default='hybrid', type=str)

            # Validate parameters
            if top_k < 1 or top_k > 50:
                return jsonify({"error": "top_k must be between 1 and 50"}), 400

            valid_strategies = ['hybrid', 'friends_only', 'friends_boosted']
            if strategy not in valid_strategies:
                return jsonify({"error": f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}"}), 400

            # Get ML engine
            ml_engine = get_ml_engine()
            if not ml_engine:
                return jsonify({"error": "Recommendation engine not available"}), 503

            # Get recommendations
            result = ml_engine.get_recommendations(
                user_uid=firebase_uid,
                top_k=top_k,
                filters=None,  # Could be extended to support filters
                recommendation_strategy=strategy
            )

            # Transform recommendations to frontend format
            recommendations = result.get('recommendations', [])
            transformed_recommendations = [
                transform_event_for_frontend(rec) for rec in recommendations]

            return jsonify({
                "success": True,
                "recommendations": transformed_recommendations,
                "count": len(transformed_recommendations),
                "strategy": result.get('strategy_used', strategy),
                "user_uid": firebase_uid
            }), 200

        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return jsonify({"error": f"Failed to get recommendations: {str(e)}"}), 500

    @app.route('/api/recommendations/refresh', methods=['POST'])
    @require_auth
    def refresh_recommendations(firebase_uid):
        """Refresh the recommendation models (admin/testing only)"""
        try:
            ml_engine = get_ml_engine()
            if not ml_engine:
                return jsonify({"error": "Recommendation engine not available"}), 503

            result = ml_engine.refresh_models()

            return jsonify({
                "success": True,
                "message": "Recommendation models refreshed",
                "status": result.get('status', 'models_refreshed')
            }), 200

        except Exception as e:
            return jsonify({"error": f"Failed to refresh models: {str(e)}"}), 500

    # Legacy endpoint for backward compatibility
    @app.route('/recommendations/<user_id>', methods=['GET'])
    def get_recommendations_legacy(user_id):
        """Legacy recommendation endpoint (deprecated)"""
        return jsonify({
            "message": "This endpoint is deprecated. Use /api/recommendations with authentication.",
            "recommendations": []
        }), 200

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    # ===== Friend Event Routes =====
    @app.route('/api/friends/rsvps', methods=['GET'])
    @require_auth
    def get_friend_rsvps(firebase_uid):
        try:
            events = Event.get_friend_rsvps(firebase_uid)
            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events]
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get friend rsvps: {str(e)}"}), 500

    @app.route('/api/friends/created', methods=['GET'])
    @require_auth
    def get_friend_created_events(firebase_uid):
        try:
            events = Event.get_friend_created_events(firebase_uid)
            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events]
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get friend created events: {str(e)}"}), 500

    @app.route('/api/friends/feed', methods=['GET'])
    @require_auth
    def get_friend_feed(firebase_uid):
        try:
            events = Event.get_friend_feed(firebase_uid)
            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events]
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get friend feed: {str(e)}"}), 500

    @app.route("/api/org/metrics/rsvps/30days", methods=["GET"])
    @require_organization
    def org_rsvps_30days(firebase_uid=None, user=None, **kwargs):
        """
        Returns RSVPs per day for the current org for the last 30 days.
        Response: { success: True, total: N, timeseries: [{ date: 'YYYY-MM-DD', count: N }, ...] }
        """
        # normalize firebase uid if decorator provided `user` object
        if not firebase_uid:
            firebase_uid = getattr(user, "firebase_uid",
                                   None) or getattr(user, "uid", None)
        if not firebase_uid:
            return jsonify({"error": "Unauthorized"}), 401

        cfg = Config()
        conn = None
        try:
            conn = pyodbc.connect(cfg.azure_sql_connection_string)
            cursor = conn.cursor()
            # last 30 days including today
            q = """
                SELECT CAST(r.CreatedAt AS DATE) AS day, COUNT(*) AS cnt
                FROM RSVPs r
                INNER JOIN Events e ON r.EventID = e.EventID
                WHERE e.OrganizerUID = ? AND r.CreatedAt >= DATEADD(day, -29, CAST(GETDATE() AS DATE))
                GROUP BY CAST(r.CreatedAt AS DATE)
                ORDER BY day ASC
            """
            cursor.execute(q, (firebase_uid,))
            rows = cursor.fetchall()
            timeseries = [{"date": row[0].strftime("%Y-%m-%d") if hasattr(
                row[0], "strftime") else str(row[0]), "count": int(row[1])} for row in rows]

            total_q = """
                SELECT COUNT(*)
                FROM RSVPs r
                INNER JOIN Events e ON r.EventID = e.EventID
                WHERE e.OrganizerUID = ? AND r.CreatedAt >= DATEADD(day, -29, CAST(GETDATE() AS DATE))
            """
            cursor.execute(total_q, (firebase_uid,))
            total = int(cursor.fetchone()[0] or 0)

            return jsonify({"success": True, "total": total, "timeseries": timeseries}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if conn:
                conn.close()

    @app.route("/api/org/metrics/followers/30days", methods=["GET"])
    @require_organization
    def org_followers_30days(firebase_uid=None, user=None, **kwargs):
        """
        Returns new followers per day for the current org for the last 30 days.
        Response: { success: True, total: N, timeseries: [{ date: 'YYYY-MM-DD', count: N }, ...] }
        """
        if not firebase_uid:
            firebase_uid = getattr(user, "firebase_uid",
                                   None) or getattr(user, "uid", None)
        if not firebase_uid:
            return jsonify({"error": "Unauthorized"}), 401

        cfg = Config()
        conn = None
        try:
            conn = pyodbc.connect(cfg.azure_sql_connection_string)
            cursor = conn.cursor()
            q = """
                SELECT CAST(sc.CreatedAt AS DATE) AS day, COUNT(*) AS cnt
                FROM SocialConnections sc
                WHERE sc.FollowingUID = ? AND sc.CreatedAt >= DATEADD(day, -29, CAST(GETDATE() AS DATE))
                GROUP BY CAST(sc.CreatedAt AS DATE)
                ORDER BY day ASC
            """
            cursor.execute(q, (firebase_uid,))
            rows = cursor.fetchall()
            timeseries = [{"date": row[0].strftime("%Y-%m-%d") if hasattr(
                row[0], "strftime") else str(row[0]), "count": int(row[1])} for row in rows]

            total_q = """
                SELECT COUNT(*)
                FROM SocialConnections sc
                WHERE sc.FollowingUID = ? AND sc.CreatedAt >= DATEADD(day, -29, CAST(GETDATE() AS DATE))
            """
            cursor.execute(total_q, (firebase_uid,))
            total = int(cursor.fetchone()[0] or 0)

            return jsonify({"success": True, "total": total, "timeseries": timeseries}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if conn:
                conn.close()
