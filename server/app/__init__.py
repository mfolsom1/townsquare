# __init__.py: Flask app factory
from flask import Flask
from flask_cors import CORS
from .models import db
from .config import Config
from sqlalchemy.sql import text

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)
    db.init_app(app)
    from .routes import register_routes
    register_routes(app)

    # Test the database connection on startup
    with app.app_context():
        # Test database connection
        try:
            db.session.execute(text('SELECT 1'))
            print("Database connection successful")
        except Exception as e:
            print(f"Database connection failed: {e}")
            raise

    return app