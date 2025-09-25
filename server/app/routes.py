from datetime import datetime
from flask import Flask, jsonify, request
from sqlalchemy import inspect
from .models import Event, db

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