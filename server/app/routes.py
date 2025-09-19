from flask import jsonify

def register_routes(app):
    
    @app.route('/')
    def home():
        return jsonify({"message": "Townsquare API"})
    
    # ===== Event functions =====
    @app.route('/events', methods=['GET'])
    def get_events():
        return jsonify([])
    
    @app.route('/events', methods=['POST'])
    def create_event():
        return jsonify({"id": 1})
    
    @app.route('/events/<int:id>', methods=['GET'])
    def get_event(id):
        return jsonify({"id": id})
    
    @app.route('/events/<int:id>', methods=['PUT'])
    def update_event(id):
        return jsonify({"updated": True})
    
    @app.route('/events/<int:id>', methods=['DELETE'])
    def delete_event(id):
        return jsonify({"deleted": True})
    
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