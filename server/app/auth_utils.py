from functools import wraps
from flask import request, jsonify
from firebase_admin import auth


def require_auth(f):
    """Decorator to require Firebase authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "No authorization token provided"}), 401

            id_token = auth_header.split('Bearer ')[1]
            decoded_token = auth.verify_id_token(id_token)

            # Add firebase_uid to kwargs for the route function
            kwargs['firebase_uid'] = decoded_token['uid']
            return f(*args, **kwargs)

        except auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid authorization token"}), 401
        except Exception as e:
            return jsonify({"error": f"Authentication failed: {str(e)}"}), 500

    return decorated_function


def require_organization(f):
    """Decorator to require organization account type for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "No authorization token provided"}), 401

            id_token = auth_header.split('Bearer ')[1]
            decoded_token = auth.verify_id_token(id_token)
            firebase_uid = decoded_token['uid']

            # Lazy import user to avoid circulars
            from .models import User
            user = User.get_user_by_firebase_uid(firebase_uid)

            if not user:
                return jsonify({"error": "User not found"}), 404

            if getattr(user, 'user_type', None) != 'organization':
                return jsonify({"error": "Organization account required"}), 403

            kwargs['firebase_uid'] = firebase_uid
            kwargs['user'] = user
            return f(*args, **kwargs)

        except auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid authorization token"}), 401
        except Exception as e:
            return jsonify({"error": f"Authentication failed: {str(e)}"}), 500

    return decorated_function
