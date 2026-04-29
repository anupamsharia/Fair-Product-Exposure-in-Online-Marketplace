from flask import Flask, session, request, redirect, url_for, send_file, send_from_directory, jsonify
from flask_cors import CORS
from routes.auth import auth_bp
from auth import admin_required, create_auth_token
from routes.product import product_bp
from routes.admin import admin_bp
from routes.order import order_bp
from routes.ml import ml_bp
from routes.ai import ai_bp
from db import products_collection, users_collection, orders_collection
from product_scoring import refresh_product_scores_bulk
from pymongo import ASCENDING, DESCENDING
import os
import traceback
from datetime import datetime
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
CORS(
    app,
    supports_credentials=True,
    resources={r"/*": {"origins": Config.CORS_ORIGINS}},
    allow_headers=["Content-Type", "Authorization", "X-FairCart-Auth"],
)

# Admin Credentials from environment
ADMIN_EMAIL = Config.ADMIN_EMAIL
ADMIN_PASSWORD = Config.ADMIN_PASSWORD

class APIError(Exception):
    """Custom exception for API errors."""
    def __init__(self, message, status_code=400, error_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

@app.errorhandler(APIError)
def handle_api_error(error):
    """Handle API errors with JSON response."""
    response = jsonify({
        'status': 'error',
        'message': error.message,
        'error_code': error.error_code
    })
    response.status_code = error.status_code
    return response

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'status': 'error',
        'message': 'Resource not found',
        'error_code': 'NOT_FOUND'
    }), 404

@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors."""
    if Config.FLASK_ENV == 'development':
        return jsonify({
            'status': 'error',
            'message': str(error),
            'traceback': traceback.format_exc()
        }), 500
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error_code': 'INTERNAL_ERROR'
    }), 500

@app.errorhandler(Exception)
def handle_generic_error(error):
    """Handle all other exceptions."""
    if Config.FLASK_ENV == 'development':
        return jsonify({
            'status': 'error',
            'message': str(error),
            'type': error.__class__.__name__,
            'traceback': traceback.format_exc()
        }), 500
    return jsonify({
        'status': 'error',
        'message': 'An unexpected error occurred',
        'error_code': 'UNEXPECTED_ERROR'
    }), 500

# Health check endpoint for monitoring
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "FairCart Backend",
        "version": "1.0.0"
    }), 200

# Paths
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
ADMIN_DIR = os.path.join(FRONTEND_DIR, "admin-frontend")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")

@app.after_request
def add_no_store_for_api(response):
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# ── Gzip compress all JSON responses ─────────────────────────────
try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass  # optional; install with: pip install flask-compress

# Register blueprints
app.register_blueprint(auth_bp,    url_prefix='/api/auth')
app.register_blueprint(product_bp, url_prefix='/api/product')
app.register_blueprint(admin_bp,   url_prefix='/api/admin')
app.register_blueprint(order_bp,   url_prefix='/api/order')
app.register_blueprint(ml_bp,      url_prefix='/api/ml')
app.register_blueprint(ai_bp,      url_prefix='/api/ai')

@app.route('/')
def home():
    # Redirect root to our storefront index
    return redirect("/s-frontend/index.html")

# --- ADMIN AUTH SYSTEM ---

@app.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.json or {}
    if data.get("email") == ADMIN_EMAIL and data.get("password") == ADMIN_PASSWORD:
        session["admin"] = True
        session["user_email"] = ADMIN_EMAIL
        session["user_role"] = "admin"
        session["user_id"] = "admin"
        admin_user = {
            "name": "FairCart Admin",
            "email": ADMIN_EMAIL,
            "role": "admin",
            "verified": True,
        }
        return {
            "status": "success",
            "token": create_auth_token(admin_user),
            "user": admin_user,
        }
    return {"status": "error", "message": "Invalid credentials"}, 401

@app.route("/admin")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin-login.html")
    return send_file(os.path.join(ADMIN_DIR, "admin.html"))

@app.route("/admin-login.html")
def admin_login_page():
    return send_file(os.path.join(ADMIN_DIR, "admin-login.html"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("http://localhost:8000/s-frontend/login.html") # Redirect back to storefront login

# --- ADMIN DATA APIS ---

@app.route("/admin-data")
@admin_required
def admin_data():
    return {
        "total_users": users_collection.count_documents({}),
        "total_orders": orders_collection.count_documents({}),
        "pending_products": products_collection.count_documents({"status": "pending"}),
        "fraud_flagged": products_collection.count_documents({"fraud_flag": True})
    }

@app.route("/admin-activity")
@admin_required
def admin_activity():
    # As requested: Simple activity list
    return [
        "New seller registered: TechWorld",
        "Product approved: Wireless Earbuds",
        "Order placed: #ORD9923",
        "New user joined: anupa@gmail.com"
    ]

# Serve CSS/JS for admin panel
@app.route("/admin-frontend/<path:filename>")
@app.route("/admin.css")
@app.route("/admin.js")
@app.route("/admin-login.css")
def serve_admin_assets(filename=None):
    if filename is None:
        filename = request.path.lstrip("/")
    return send_from_directory(ADMIN_DIR, filename)

# Serve s-frontend assets if accessed without s-frontend prefix (some partials or legacy code)
@app.route("/<any(style.css,auth.js,api.js,app.js,cart.js):filename>")
def serve_root_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "s-frontend"), filename)

@app.route("/uploads/<path:path>")
def serve_uploads(path):
    return send_from_directory(UPLOADS_DIR, path)

@app.route("/s-frontend/<path:path>")
def serve_storefront(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, "s-frontend"), path)

def create_indexes():
    """Create MongoDB indexes for fast queries. Safe to call multiple times."""
    print("--- Creating MongoDB Indexes ---")
    # Products: approved + category filter + sort by fair_score
    products_collection.create_index([("approved", ASCENDING), ("fair_score", DESCENDING)])
    products_collection.create_index([("approved", ASCENDING), ("category", ASCENDING), ("fair_score", DESCENDING)])
    products_collection.create_index([("status", ASCENDING), ("final_score", DESCENDING), ("created_at", DESCENDING)])
    products_collection.create_index([("status", ASCENDING), ("category", ASCENDING), ("final_score", DESCENDING), ("created_at", DESCENDING)])
    products_collection.create_index([("approved", ASCENDING), ("final_score", DESCENDING), ("created_at", DESCENDING)])
    products_collection.create_index([("approved", ASCENDING), ("category", ASCENDING), ("final_score", DESCENDING), ("created_at", DESCENDING)])
    products_collection.create_index([("seller_id", ASCENDING)])
    products_collection.create_index([("name", "text")])  # text search
    products_collection.create_index([("ml_id", ASCENDING)])
    products_collection.create_index([("status", ASCENDING)])  # for pending/approved/rejected queries
    products_collection.create_index([("created_at", DESCENDING)])  # for recent products
    
    # Users
    users_collection.create_index([("email", ASCENDING)], unique=True, sparse=True)
    users_collection.create_index([("role", ASCENDING)])
    users_collection.create_index([("verified", ASCENDING)])  # for seller verification
    
    # Orders
    from db import orders_collection, activity_logs_collection
    orders_collection.create_index([("user_id", ASCENDING)])
    orders_collection.create_index([("seller_id", ASCENDING)])
    orders_collection.create_index([("status", ASCENDING)])
    orders_collection.create_index([("created_at", DESCENDING)])
    
    # Activity logs
    activity_logs_collection.create_index([("timestamp", DESCENDING)])
    activity_logs_collection.create_index([("type", ASCENDING)])
    activity_logs_collection.create_index([("user_email", ASCENDING)])
    
    print("--- Indexes Ready ---")

if __name__ == '__main__':
    try:
        create_indexes()
        updated_scores = refresh_product_scores_bulk(missing_only=True)
        print(f"--- Product Scores Ready ({updated_scores} updated) ---")
    except Exception as e:
        print(f"Warning: Failed to connect to database for index creation. Is your IP whitelisted? Error: {e}")
    app.run(debug=False, use_reloader=False, port=5000, threaded=True)
