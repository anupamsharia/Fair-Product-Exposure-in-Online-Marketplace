"""
Authentication and authorization utilities for FairCart.
Provides decorators for role-based access control.
"""
from functools import wraps
import hmac
from flask import session, jsonify, request
from db import users_collection
from config import Config
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
import logging

logger = logging.getLogger(__name__)

AUTH_TOKEN_SALT = "faircart-auth-token"
AUTH_TOKEN_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def _auth_serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY, salt=AUTH_TOKEN_SALT)


def _serialize_user(user):
    user = dict(user)
    if "_id" in user:
        user['_id'] = str(user['_id'])
    return user


def _virtual_admin_user(email=None):
    return {
        "_id": "admin",
        "name": "FairCart Admin",
        "email": email or Config.ADMIN_EMAIL,
        "role": "admin",
        "verified": True,
    }


def create_auth_token(user):
    """Create a signed token for API calls when browser cookies are unavailable."""
    return _auth_serializer().dumps({
        "email": user.get("email"),
        "role": user.get("role"),
    })


def _get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return request.headers.get("X-FairCart-Auth", "").strip()


def _get_token_user():
    token = _get_bearer_token()
    if not token:
        return None

    try:
        payload = _auth_serializer().loads(token, max_age=AUTH_TOKEN_MAX_AGE_SECONDS)
    except SignatureExpired:
        logger.info("Expired auth token rejected")
        return None
    except BadSignature:
        logger.warning("Invalid auth token rejected")
        return None

    email = payload.get("email")
    if not email:
        return None

    user = users_collection.find_one({"email": email})
    if not user:
        token_role = payload.get("role")
        if token_role == "admin" and email == Config.ADMIN_EMAIL:
            return _virtual_admin_user(email)
        return None

    token_role = payload.get("role")
    if token_role and user.get("role") != token_role:
        return None

    return _serialize_user(user)


def get_current_user():
    """Get current user from session or signed API token."""
    if 'user_email' in session:
        email = session['user_email']
        user = users_collection.find_one({"email": email})
        if user:
            return _serialize_user(user)
        if session.get("admin") and email == Config.ADMIN_EMAIL:
            return _virtual_admin_user(email)
    return _get_token_user()


def is_admin_session():
    """Return True when the request has the legacy admin dashboard session."""
    return bool(session.get("admin"))

def login_required(f):
    """Decorator to ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to restrict access by role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            
            if user.get('role') not in allowed_roles:
                return jsonify({"status": "error", "message": "Insufficient permissions"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to ensure user is admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if is_admin_session():
            return f(*args, **kwargs)

        user = get_current_user()
        if not user or user.get("role") != "admin":
            return jsonify({"status": "error", "message": "Admin access required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    """Decorator to ensure user is a seller."""
    return role_required('seller')(f)


def seller_or_admin_required(f):
    """Decorator to allow seller API users or the admin dashboard session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if is_admin_session():
            return f(*args, **kwargs)

        user = get_current_user()
        if not user:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        if user.get('role') not in {'seller', 'admin'}:
            return jsonify({"status": "error", "message": "Insufficient permissions"}), 403

        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    """Decorator to ensure user is a customer."""
    return role_required('customer')(f)

def api_key_required(f):
    """Decorator for API key authentication (for internal services)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not Config.INTERNAL_API_KEY:
            return jsonify({"status": "error", "message": "Internal API key is not configured"}), 503
        if not api_key or not hmac.compare_digest(str(api_key), str(Config.INTERNAL_API_KEY)):
            return jsonify({"status": "error", "message": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated_function
