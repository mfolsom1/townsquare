from datetime import datetime
from flask import Flask, jsonify, request
from sqlalchemy import inspect
from .models import Event, db, request
from firebase_admin import auth
from .models import User
from .auth_utils import require_auth
import pyodbc

def register_routes(app):
    
    @app.route('/')
    def home():
        return jsonify({"message": "Townsquare API"})
    
    @app.route('/inspect_db', methods=['GET'])
    def inspect_db():
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            return {"tables": tables}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    # ===== Event functions =====
    @app.route('/events', methods=['GET'])
    def get_events():
        return jsonify(["events"])
    
    @app.route('/events', methods=['POST'])
    def create_event():
        try:
            # Parse JSON data from the request
            data = request.get_json()

            # Validate required fields
            required_fields = ['Title', 'StartTime', 'EndTime', 'Location']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

            # Create a new Event object
            new_event = Event(
                Title=data['Title'],
                Description=data.get('Description'),
                StartTime=datetime.fromisoformat(data['StartTime']),
                EndTime=datetime.fromisoformat(data['EndTime']),
                Location=data['Location']
            )

            # Add the event to the database
            db.session.add(new_event)
            db.session.commit()

            # Return the created event
            return jsonify({
                "EventID": new_event.EventID,
                "Title": new_event.Title,
                "Description": new_event.Description,
                "StartTime": new_event.StartTime.isoformat(),
                "EndTime": new_event.EndTime.isoformat(),
                "Location": new_event.Location,
                "CreatedAt": new_event.CreatedAt.isoformat()
            }), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/events/<int:id>', methods=['GET'])
    def get_event(id):
        # Query the database for the event
        event = Event.query.get(id)

        # If the event is not found, return a 404 error
        if not event:
            return jsonify({"error": "Event not found"}), 404

        # Return the event as JSON
        return jsonify({
            "EventID": event.EventID,
            "Title": event.Title,
            "Description": event.Description,
            "StartTime": event.StartTime.isoformat(),
            "EndTime": event.EndTime.isoformat(),
            "Location": event.Location,
            "CreatedAt": event.CreatedAt.isoformat()
        })
    
    @app.route('/events/<int:id>', methods=['PUT'])
    def update_event(id):
        pass
    
    @app.route('/events/<int:id>', methods=['DELETE'])
    def delete_event(id):
        pass
    
    # ===== User functions =====
    @app.route('/users/<int:id>', methods=['GET'])
    def get_user(id):
        return jsonify({"id": id})
    
    @app.route('/users/<int:id>', methods=['PUT'])
    def update_user(id):
        return jsonify({"updated": True})
    
    # ===== Recommendation functions =====
    @app.route('/recommendations/<int:user_id>', methods=['GET'])
    def get_recommendations(user_id):
        return jsonify([])
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
    
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