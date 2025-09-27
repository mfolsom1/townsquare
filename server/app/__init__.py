from flask import Flask
from flask_cors import CORS
from .config import Config
import firebase_admin
from firebase_admin import credentials

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Firebase Admin
    if not firebase_admin._apps:
        config = Config()
        if config.FIREBASE_SERVICE_ACCOUNT_KEY:
            cred = credentials.Certificate(config.FIREBASE_SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred)

    CORS(app)

    from .routes import register_routes
    register_routes(app)
    
    # Initialize database tables on first run
    from .database import init_database
    init_database()

    return app