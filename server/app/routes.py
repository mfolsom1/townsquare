from datetime import datetime
from flask import Flask, jsonify, request
from .models import Event, RSVP, Organization
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
                print(f"User already exists: {existing_user.username}")  # Debug log
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
                
                print(f"Creating new user with username: {username}")  # Debug log
                
                # Validate username format
                username = username.strip()
                if len(username) < 3 or len(username) > 20:
                    return jsonify({"error": "Username must be between 3 and 20 characters"}), 400
                
                if not username.replace('_', '').replace('-', '').isalnum():
                    return jsonify({"error": "Username can only contain letters, numbers, underscores, and hyphens"}), 400
                try:
                    # Extract name info from user_data or Firebase token
                    full_name = user_data.get('name') or decoded_token.get('name') or ''
                    name_parts = full_name.split(' ', 1) if full_name else ['', '']
                    
                    first_name = (decoded_token.get('given_name') or 
                                 name_parts[0] if name_parts[0] else None)
                    last_name = (decoded_token.get('family_name') or 
                                name_parts[1] if len(name_parts) > 1 and name_parts[1] else None)
                    
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
            # Explicit check for missing or invalid firebase_uid
            if not firebase_uid:
                return jsonify({"error": "You must be logged in to update your profile."}), 401

            update_data = request.json or {}
            allowed_fields = ['username', 'first_name', 'last_name', 'location', 'bio', 'interests']

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
                filtered_data['interests'] = [interest.strip() for interest in interests]

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
                    "location": user.location
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

            result = Event.get_events(q=q, page=page, per_page=per_page, sort_by=sort_by, sort_dir=sort_dir)
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
    
    @app.route('/events', methods=['GET'])
    def get_all_events():
        try:
            events = Event.get_all_events()
            # Returns a 200 OK with an empty list if no events are found, which is more conventional.
            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events]
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/user/events/organized', methods=['GET'])
    @require_auth
    def get_user_organized_events(firebase_uid):
        """Get events organized by the current user"""
        try:
            events = Event.get_events_by_organizer(firebase_uid)
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
    @require_auth
    def create_event(firebase_uid):
        try:
            # Parse JSON data from the request
            data = request.get_json()

            # Validate required fields (CategoryID is required, OrgID is optional)
            required_fields = ['Title', 'StartTime', 'EndTime', 'Location', 'CategoryID']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

            org_id = data.get('OrgID')
            
            # If an organization is specified, validate that the user is following it
            if org_id:
                if not User.is_following_organization(firebase_uid, org_id):
                    return jsonify({"error": "You can only create events for organizations you follow"}), 403

            # Create a new Event object
            new_event = Event.create_event(
                organizer_uid=firebase_uid,
                title=data['Title'],
                description=data.get('Description'),
                start_time=(data['StartTime']),
                end_time=(data['EndTime']),
                location=data['Location'],
                category_id=data['CategoryID'], # Now a required field
                max_attendees=data.get('MaxAttendees'),
                image_url=data.get('ImageURL'),
                org_id=org_id  # Required organization ID
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
            update_fields = ['Title', 'Description', 'StartTime', 'EndTime', 'Location', 'CategoryID', 'MaxAttendees', 'ImageURL']
            update_data = {field: data[field] for field in update_fields if field in data}
            
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
            update_kwargs = {k: v for k, v in update_kwargs.items() if v is not None}


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
    
    # ===== Friend Event Routes =====
    @app.route('/api/friends/events', methods=['GET'])
    @require_auth
    def get_friend_events(firebase_uid):
        try:
            events = Event.get_friend_events(firebase_uid)
            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events]
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get friend events: {str(e)}"}), 500

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

    # ===== Organization Routes =====
    @app.route('/api/organizations', methods=['GET'])
    def get_all_organizations():
        """Get all organizations"""
        try:
            organizations = Organization.get_all_organizations()
            return jsonify({
                "success": True,
                "organizations": [org.to_dict() for org in organizations]
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get organizations: {str(e)}"}), 500

    @app.route('/api/organizations', methods=['POST'])
    @require_auth
    def create_organization(firebase_uid):
        """Create a new organization"""
        try:
            data = request.json or {}
            name = data.get('name', '').strip()
            description = data.get('description', '').strip() or None
            
            if not name:
                return jsonify({"error": "Organization name is required"}), 400
            
            if len(name) > 100:
                return jsonify({"error": "Organization name must be 100 characters or less"}), 400
            
            organization = Organization.create_organization(name, description)
            return jsonify({
                "success": True,
                "message": "Organization created successfully",
                "organization": organization.to_dict()
            }), 201
        except pyodbc.IntegrityError:
            return jsonify({"error": "Organization with this name already exists"}), 409
        except Exception as e:
            return jsonify({"error": f"Failed to create organization: {str(e)}"}), 500

    @app.route('/api/organizations/<int:org_id>', methods=['GET'])
    def get_organization(org_id):
        """Get organization by ID"""
        try:
            organization = Organization.get_organization_by_id(org_id)
            if not organization:
                return jsonify({"error": "Organization not found"}), 404
            
            return jsonify({
                "success": True,
                "organization": organization.to_dict()
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get organization: {str(e)}"}), 500

    @app.route('/api/organizations/<int:org_id>', methods=['PUT'])
    @require_auth
    def update_organization(firebase_uid, org_id):
        """Update organization information"""
        try:
            data = request.json or {}
            allowed_fields = ['name', 'description']
            
            filtered_data = {k: v for k, v in data.items() 
                           if k in allowed_fields and v is not None}
            
            if not filtered_data:
                return jsonify({"error": "No valid fields to update"}), 400
            
            # Clean up the data
            if 'name' in filtered_data:
                filtered_data['name'] = filtered_data['name'].strip()
                if not filtered_data['name']:
                    return jsonify({"error": "Organization name cannot be empty"}), 400
                if len(filtered_data['name']) > 100:
                    return jsonify({"error": "Organization name must be 100 characters or less"}), 400
            
            if 'description' in filtered_data:
                filtered_data['description'] = filtered_data['description'].strip() or None
            
            success = Organization.update_organization(org_id, **filtered_data)
            if not success:
                return jsonify({"error": "Organization not found"}), 404
            
            # Return updated organization
            organization = Organization.get_organization_by_id(org_id)
            return jsonify({
                "success": True,
                "message": "Organization updated successfully",
                "organization": organization.to_dict()
            })
        except pyodbc.IntegrityError:
            return jsonify({"error": "Organization with this name already exists"}), 409
        except Exception as e:
            return jsonify({"error": f"Failed to update organization: {str(e)}"}), 500

    # ===== Organization Membership Routes =====
    @app.route('/api/organizations/<int:org_id>/join', methods=['POST'])
    @require_auth
    def join_organization(firebase_uid, org_id):
        """Join an organization"""
        try:
            success = User.join_organization(firebase_uid, org_id)
            if success:
                return jsonify({
                    "success": True,
                    "message": "Successfully joined organization"
                })
            else:
                return jsonify({"error": "Already a member of this organization"}), 400
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": f"Failed to join organization: {str(e)}"}), 500

    @app.route('/api/organizations/<int:org_id>/leave', methods=['POST'])
    @require_auth
    def leave_organization(firebase_uid, org_id):
        """Leave an organization"""
        try:
            success = User.leave_organization(firebase_uid, org_id)
            if success:
                return jsonify({
                    "success": True,
                    "message": "Successfully left organization"
                })
            else:
                return jsonify({"error": "Not a member of this organization"}), 400
        except Exception as e:
            return jsonify({"error": f"Failed to leave organization: {str(e)}"}), 500

    @app.route('/api/user/organizations', methods=['GET'])
    @require_auth
    def get_user_organizations(firebase_uid):
        """Get user's organization memberships"""
        try:
            organizations = User.get_user_organizations(firebase_uid)
            return jsonify({
                "success": True,
                "organizations": organizations
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get user organizations: {str(e)}"}), 500

    # ===== Organization Following Routes =====
    @app.route('/api/organizations/<int:org_id>/follow', methods=['POST'])
    @require_auth
    def follow_organization(firebase_uid, org_id):
        """Follow an organization"""
        try:
            success = User.follow_organization(firebase_uid, org_id)
            if success:
                return jsonify({
                    "success": True,
                    "message": "Successfully followed organization"
                })
            else:
                return jsonify({"error": "Already following this organization"}), 400
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": f"Failed to follow organization: {str(e)}"}), 500

    @app.route('/api/organizations/<int:org_id>/unfollow', methods=['POST'])
    @require_auth
    def unfollow_organization(firebase_uid, org_id):
        """Unfollow an organization"""
        try:
            success = User.unfollow_organization(firebase_uid, org_id)
            if success:
                return jsonify({
                    "success": True,
                    "message": "Successfully unfollowed organization"
                })
            else:
                return jsonify({"error": "Not following this organization"}), 400
        except Exception as e:
            return jsonify({"error": f"Failed to unfollow organization: {str(e)}"}), 500

    @app.route('/api/user/followed-organizations', methods=['GET'])
    @require_auth
    def get_followed_organizations(firebase_uid):
        """Get organizations that user is following"""
        try:
            organizations = User.get_followed_organizations(firebase_uid)
            return jsonify({
                "success": True,
                "organizations": organizations
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get followed organizations: {str(e)}"}), 500

    # ===== Organization Events Routes =====
    @app.route('/api/organizations/<int:org_id>/events', methods=['GET'])
    def get_organization_events(org_id):
        """Get events posted under an organization"""
        try:
            events = Event.get_events_by_organization(org_id)
            return jsonify({
                "success": True,
                "events": [event.to_dict() for event in events]
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get organization events: {str(e)}"}), 500
