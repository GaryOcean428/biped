import os
import sys
import time

from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_from_directory,
    url_for,
)

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Railway-optimized configuration
from config import get_config
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS
from flask_migrate import Migrate
from src.models.admin import Admin, AdminAction
from src.models.job import Job, JobMessage, JobMilestone, Quote
from src.models.payment import Dispute, Payment, StripeAccount, Transfer
from src.models.review import Message, Notification, Review
from src.models.service import PortfolioItem, ProviderService, Service, ServiceCategory

# Import core models
from src.models.user import CustomerProfile, ProviderProfile, User, db
from src.routes.admin import admin_bp
from src.routes.ai import ai_bp
from src.routes.analytics import analytics_bp

# Import route blueprints
from src.routes.auth import auth_bp
from src.routes.admin_auth import admin_auth_bp
from src.routes.dev_auth import dev_auth_bp
from src.routes.business import business_bp
from src.routes.dashboard import dashboard_bp
from src.routes.health import health_bp
from src.routes.job import job_bp
from src.routes.jobs_api import jobs_api_bp
from src.routes.payment import payment_bp
from src.routes.review import review_bp
from src.routes.service import service_bp
from src.routes.storage import storage_bp
from src.routes.user import user_bp
from src.routes.vision import vision_bp
from src.routes.websocket import init_socketio, websocket_bp
from src.services.data_pipeline import create_data_services
from src.utils.performance import TradingCacheService, configure_performance
from src.utils.redis_client import redis_client

# Import enhanced security and performance modules
from src.utils.security import SecurityConfig, SecurityEnhancer

# Create Flask app with static folder configuration
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))

# Load Railway-optimized configuration
config_class = get_config()
app.config.from_object(config_class)

# Enhanced configuration with /data volume support
DATA_DIR = app.config.get("DATA_DIR", os.path.join(os.getcwd(), "data"))

# Check if we can access the data directory, fallback to local if not
try:
    os.makedirs(DATA_DIR, exist_ok=True)
    # Test write access
    test_file = os.path.join(DATA_DIR, ".write_test")
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
    print(f"✅ Data directory accessible: {DATA_DIR}")
except (PermissionError, OSError) as e:
    # Fallback to local directory for development
    DATA_DIR = os.path.join(os.getcwd(), "data")
    print(f"⚠️ Cannot access /data ({e}), falling back to {DATA_DIR}")
    os.makedirs(DATA_DIR, exist_ok=True)
    app.config["DATA_DIR"] = DATA_DIR

# Create additional directories safely
try:
    os.makedirs(os.path.join(DATA_DIR, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "reports"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "backups"), exist_ok=True)

    # Update upload folder configuration to use the working data directory
    app.config["UPLOAD_FOLDER"] = os.path.join(DATA_DIR, "uploads")
    print(f"✅ Upload folder configured: {app.config['UPLOAD_FOLDER']}")
except (PermissionError, OSError) as e:
    print(f"⚠️ Directory creation warning: {e}")
    # Ensure upload folder is set to a safe default
    app.config["UPLOAD_FOLDER"] = os.path.join(DATA_DIR, "uploads")

print(f"🚀 Starting Enhanced Biped Platform v2.0")
print(f"📊 Environment: {app.config.get('ENVIRONMENT', 'development')}")
print(f"🗄️ Database: {'PostgreSQL (Railway)' if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('postgresql') else 'SQLite (Local)'}")
print(f"🔄 Redis: {'Available (Railway)' if app.config.get('REDIS_URL') else 'Not configured'}")
print(f"💾 Data Directory: {DATA_DIR}")

# Initialize Flask extensions with Railway-optimized configuration
db.init_app(app)
migrate = Migrate(app, db)
cache = Cache(app)
compress = Compress(app)

# Initialize CORS with configuration
CORS(
    app,
    origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-CSRF-Token"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    supports_credentials=True
)

# Configure performance optimizations
if hasattr(app.config, "PERFORMANCE_CONFIG"):
    configure_performance(app)

# Initialize database with app and set up migrations (check if already initialized)
if not hasattr(app, "extensions") or "sqlalchemy" not in app.extensions:
    db.init_app(app)
    print("✅ Database initialized with app")
else:
    print("✅ Database already initialized, skipping")

migrate = Migrate(app, db)

# Initialize caching
cache = Cache(app)
trading_cache = TradingCacheService(app) if "TradingCacheService" in globals() else None

# Initialize compression
Compress(app)

# Initialize security enhancements
security_config = SecurityConfig() if "SecurityConfig" in globals() else None
security_enhancer = SecurityEnhancer(app, security_config) if "SecurityEnhancer" in globals() else None

# Initialize WebSocket support
socketio = init_socketio(app) if "init_socketio" in globals() else None

# Cache busting configuration
CACHE_BUST = os.environ.get("CACHE_BUST", str(int(time.time())))


# Make security enhancer available in request context
@app.before_request
def before_request():
    if security_enhancer:
        g.security_enhancer = security_enhancer
    if trading_cache:
        g.cache_service = trading_cache
    g.start_time = time.time()
    g.cache_bust = CACHE_BUST

    # Log request for monitoring
    if not request.path.startswith("/static"):
        print(f"Request: {request.method} {request.path} from {request.remote_addr}")


@app.after_request
def after_request(response):
    # Add cache busting headers for static files
    if request.path.startswith("/static") or request.path.endswith(
        (".css", ".js", ".png", ".jpg", ".ico")
    ):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["ETag"] = f'"{CACHE_BUST}"'

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Add performance headers
    if hasattr(g, "start_time"):
        response.headers["X-Response-Time"] = f"{(time.time() - g.start_time) * 1000:.2f}ms"

    # Add CORS headers for authentication
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response


# Register enhanced blueprints with rate limiting
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(admin_auth_bp, url_prefix="/api/admin")
app.register_blueprint(dev_auth_bp, url_prefix="/api/auth")
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(service_bp, url_prefix="/api/services")
app.register_blueprint(job_bp, url_prefix="/api/jobs")
app.register_blueprint(payment_bp, url_prefix="/api/payments")
app.register_blueprint(review_bp, url_prefix="/api/reviews")
app.register_blueprint(ai_bp, url_prefix="/api/ai")
app.register_blueprint(vision_bp, url_prefix="/api/vision")
app.register_blueprint(health_bp, url_prefix="/api/health")
app.register_blueprint(storage_bp, url_prefix="/api/storage")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(business_bp, url_prefix="/api/business")
app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
app.register_blueprint(admin_bp, url_prefix="/api/admin/platform")
app.register_blueprint(jobs_api_bp, url_prefix="/api/v1/jobs")
app.register_blueprint(websocket_bp, url_prefix="/api/ws")

# Basic routes
@app.route('/')
def index():
    """Serve the PUBLIC landing page - NOT the dashboard"""
    # EXPLICIT OVERRIDE - Force serving the correct landing page
    # This ensures the root URL always shows the public landing page
    return send_from_directory('static', 'landing.html')

@app.route('/landing')
def landing():
    """Explicit landing page route"""
    return send_from_directory('static', 'landing.html')

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

@app.route('/profile')
def profile():
    """Serve the user profile page"""
    return send_from_directory('static', 'profile.html')

@app.route('/billing')
def billing():
    """Serve the billing page"""
    return send_from_directory('static', 'billing.html')

@app.route('/settings')
def settings():
    """Serve the settings page"""
    return send_from_directory('static', 'settings.html')

@app.route('/admin-login')
def admin_login():
    """Serve the admin login page"""
    return send_from_directory('static', 'admin-login.html')

@app.route('/dev-login')
def dev_login():
    """Serve the developer login page"""
    return send_from_directory('static', 'dev-login.html')

# Static file serving for other paths
@app.route('/<path:path>')
def serve_static_files(path):
    """Handle static files and other routes"""
    # Handle specific HTML routes
    if path in ['dashboard', 'admin', 'post-job', 'admin-login', 'dev-login', 'profile', 'billing', 'settings']:
        return send_from_directory('static', f'{path}.html')
    # Handle static files (CSS, JS, images)
    elif path.endswith('.js') or path.endswith('.css') or path.endswith('.html') or path.endswith('.png') or path.endswith('.jpg') or path.endswith('.ico'):
        return send_from_directory('static', path)
    # For unknown routes, redirect to landing page
    else:
        return send_from_directory('static', 'landing.html')

# Initialize database tables and default data
def init_db():
    """Initialize database tables and default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we need to create default data
        if ServiceCategory.query.count() == 0:
            print("Creating default service categories...")
            categories = [
                ServiceCategory(name="Construction & Renovation", description="General contractors, carpenters, painters, and renovation specialists"),
                ServiceCategory(name="Plumbing & Electrical", description="Licensed plumbers, electricians, and HVAC specialists"),
                ServiceCategory(name="Tech & Digital", description="Web developers, designers, IT support, and digital marketing"),
                ServiceCategory(name="Automotive", description="Mechanics, auto electricians, and vehicle specialists"),
                ServiceCategory(name="Landscaping", description="Gardeners, landscapers, and outdoor maintenance specialists"),
                ServiceCategory(name="Cleaning & Maintenance", description="Professional cleaners, maintenance, and facility management"),
            ]
            db.session.add_all(categories)
            db.session.commit()
            print(f"Created {len(categories)} service categories")
        
        # Check if we need to create admin user
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@biped.app")
        if User.query.filter_by(email=admin_email).count() == 0:
            print(f"Creating admin user: {admin_email}")
            admin_user = User(
                email=admin_email,
                first_name="Admin",
                last_name="User",
                user_type="admin",
                is_active=True,
                is_verified=True
            )
            admin_user.set_password(os.environ.get("ADMIN_PASSWORD", "biped_admin_2025"))
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created admin user with ID: {admin_user.id}")

# Initialize database on startup
with app.app_context():
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    if socketio:
        socketio.run(app, host='0.0.0.0', port=port, debug=debug)
    else:
        app.run(host='0.0.0.0', port=port, debug=debug)

