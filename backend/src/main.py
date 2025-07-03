import os
import sys
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))

# Configure CORS
CORS(app, origins=["*"], supports_credentials=True)

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Simple error handler
@app.errorhandler(500)
def handle_internal_error(error):
    return jsonify({"error": "Internal server error", "message": str(error)}), 500

@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({"error": "Not found", "message": "Resource not found"}), 404

# Basic routes
@app.route('/')
def index():
    """Serve the main landing page"""
    return send_from_directory('static', 'index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({"status": "healthy", "message": "Biped platform is running"}), 200

@app.route('/admin')
def admin():
    """Serve the admin interface"""
    return send_from_directory('static', 'admin.html')

@app.route('/dashboard')
def dashboard():
    """Serve the user dashboard"""
    return send_from_directory('static', 'dashboard.html')

@app.route('/post-job')
def post_job():
    """Serve the job posting form"""
    return send_from_directory('static', 'job-posting.html')

@app.route('/admin-login')
def admin_login():
    """Serve the admin login page"""
    return send_from_directory('static', 'admin-login.html')

# Catch-all route for SPA routing
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """Handle SPA routing"""
    # Handle specific routes
    if path in ['dashboard', 'admin', 'post-job', 'admin-login']:
        return send_from_directory('static', f'{path}.html')
    elif path.endswith('.js') or path.endswith('.css') or path.endswith('.html'):
        return send_from_directory('static', path)
    else:
        # Default to landing page for unknown routes
        return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

