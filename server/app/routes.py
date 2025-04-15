# routes.py: Define API endpoints
from flask import jsonify

def register_routes(app):
    @app.route('/')
    def home():
        return jsonify({"message": "Welcome to Townsquare API"})