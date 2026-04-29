from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import users_collection, log_activity
from datetime import datetime
from auth import create_auth_token, get_current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'customer')
    if role not in ['customer', 'seller']:
        return jsonify({"message": "Invalid account role"}), 400

    # Strict Security Validation
    if not name or not email or not password:
        return jsonify({"message": "Name, email, and password are strictly required"}), 400
        
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters long"}), 400

    if role == 'seller':
        if not data.get('shop_name'):
            return jsonify({"message": "Security Error: Sellers must provide a Shop Name"}), 400

    # Ensure unique email
    if users_collection.find_one({"email": email}):
        return jsonify({"message": "Email already exists"}), 400

    verified = True if role != 'seller' else False

    user = {
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "role": role,
        "shop_name": data.get('shop_name', '').strip() if role == 'seller' else '',
        "aadhaar_number": data.get('aadhaar_number', '').strip() if role == 'seller' else '',
        "verified": verified,
        "created_at": datetime.now()
    }
    
    users_collection.insert_one(user)
    log_activity("SIGNUP", f"New {role} registered: {name}", email)
    return jsonify({"message": "Registration successful"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Missing email or password"}), 400

    user = users_collection.find_one({"email": data['email']})
    if not user or not check_password_hash(user.get('password', ''), data['password']):
        return jsonify({"message": "Invalid password or email. Authentication failed."}), 401

    if user.get('status') == 'blocked':
        return jsonify({"message": "This account is blocked"}), 403

    # Set session variables
    session['user_email'] = user['email']
    session['user_role'] = user.get('role', 'customer')
    session['user_id'] = str(user['_id'])
    
    # If user is admin, also set admin session
    if user.get('role') == 'admin' or user.get('email') == 'admin@faircart.com':
        session['admin'] = True

    return jsonify({
        "message": "Login successful",
        "token": create_auth_token(user),
        "user": {
            "name": user.get("name"),
            "email": user.get("email"),
            "id": str(user.get("_id")),
            "role": user.get("role"),
            "shop_name": user.get("shop_name", ""),
            "verified": user.get("verified", True)
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"message": "Not authenticated"}), 401
    
    return jsonify({
        "token": create_auth_token(user),
        "user": {
            "name": user.get("name"),
            "email": user.get("email"),
            "id": str(user.get("_id")),
            "role": user.get("role"),
            "shop_name": user.get("shop_name", ""),
            "verified": user.get("verified", True)
        }
    }), 200

@auth_bp.route('/local-restore', methods=['POST'])
def local_restore():
    """Repair local demo sessions after switching between localhost and 127.0.0.1."""
    if request.remote_addr not in {"127.0.0.1", "::1", "::ffff:127.0.0.1"}:
        return jsonify({"message": "Local session restore is only available on this machine"}), 403

    data = request.json or {}
    email = data.get("email", "").strip()
    user = users_collection.find_one({"email": email})
    if not user or user.get("role") != "seller":
        return jsonify({"message": "Seller account not found"}), 404

    session['user_email'] = user['email']
    session['user_role'] = user.get('role', 'seller')
    session['user_id'] = str(user['_id'])

    return jsonify({
        "message": "Session restored",
        "token": create_auth_token(user),
        "user": {
            "name": user.get("name"),
            "email": user.get("email"),
            "id": str(user.get("_id")),
            "role": user.get("role"),
            "shop_name": user.get("shop_name", ""),
            "verified": user.get("verified", True)
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200
