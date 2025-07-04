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

# Import optional dependencies with fallbacks
try:
    from flask_caching import Cache
except ImportError:
    print("⚠️ flask_caching not installed, caching disabled")
    Cache = None

try:
    from flask_compress import Compress
except ImportError:
    print("⚠️ flask_compress not installed, compression disabled")
    Compress = None

try:
    from flask_cors import CORS
except ImportError:
    print("⚠️ flask_cors not installed, CORS disabled")
    CORS = None

try:
    from flask_migrate import Migrate
except ImportError:
    print("⚠️ flask_migrate not installed, migrations disabled")
    Migrate = None

# Import core models
from src.models.user import CustomerProfile, ProviderProfile, User, db

# Import models with error handling
try:
    from src.models.admin import Admin, AdminAction
    from src.models.job import Job, JobMessage, JobMilestone, Quote
    from src.models.payment import Dispute, Payment, StripeAccount, Transfer
    from src.models.review import Message, Notification, Review
    from src.models.service import PortfolioItem, ProviderService, Service, ServiceCategory
except ImportError as e:
    print(f"⚠️ Error importing models: {e}")

# Import route blueprints with error handling
try:
    from src.routes.unified_auth import auth_bp
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
    
    # Import optional route blueprints
    try:
        from src.routes.admin import admin_bp
    except ImportError:
        print("⚠️ admin_bp not available")
        admin_bp = None
        
    try:
        from src.routes.ai import ai_bp
    except ImportError:
        print("⚠️ ai_bp not available")
        ai_bp = None
        
    try:
        from src.routes.analytics import analytics_bp
    except ImportError:
        print("⚠️ analytics_bp not available")
        analytics_bp = None
        
    try:
        from src.routes.websocket import init_socketio, websocket_bp
    except ImportError:
        print("⚠️ websocket_bp not available")
        init_socketio = None
        websocket_bp = None
except ImportError as e:
    print(f"⚠️ Error importing route blueprints: {e}")

# Import optional services with fallbacks
try:
    from src.services.data_pipeline import create_data_services
except ImportError:
    print("⚠️ data_pipeline not available")
    create_data_services = None

try:
    from src.utils.performance import TradingCacheService, configure_performance
except ImportError:
    print("⚠️ performance utils not available")
    TradingCacheService = None
    configure_performance = None

try:
    from src.utils.redis_client import redis_client
except ImportError:
    print("⚠️ redis_client not available")
    redis_client = None

# Import enhanced security and performance modules
try:
    from src.utils.security import SecurityConfig, SecurityEnhancer
except ImportError:
    print("⚠️ security utils not available")
    SecurityConfig = None
    SecurityEnhancer = None

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

# Initialize migrations if available
if Migrate:
    migrate = Migrate(app, db)
else:
    migrate = None
    print("⚠️ Migrations disabled due to missing flask_migrate")

# Initialize caching if available
if Cache:
    cache = Cache(app)
else:
    cache = None
    print("⚠️ Caching disabled due to missing flask_caching")

# Initialize compression if available
if Compress:
    compress = Compress(app)
else:
    compress = None
    print("⚠️ Compression disabled due to missing flask_compress")

# Initialize CORS if available
if CORS:
    CORS(
        app,
        origins=os.environ.get("CORS_ORIGINS", "*").split(","),
        allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-CSRF-Token"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        supports_credentials=True
    )
    print("✅ CORS initialized")
else:
    print("⚠️ CORS disabled due to missing flask_cors")

# Configure performance optimizations if available
if configure_performance and hasattr(app.config, "PERFORMANCE_CONFIG"):
    configure_performance(app)
    print("✅ Performance optimizations configured")

# Initialize database with app and set up migrations (check if already initialized)
if not hasattr(app, "extensions") or "sqlalchemy" not in app.extensions:
    db.init_app(app)
    print("✅ Database initialized with app")
else:
    print("✅ Database already initialized, skipping")

# Initialize database tables and default data
def init_production_database():
    """Initialize database with tables and default data for production"""
    try:
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # Import models here to avoid circular imports
        from src.models.admin import Admin
        from src.models.service import ServiceCategory
        
        # Check if admin user exists
        admin = Admin.query.filter_by(email='admin@biped.app').first()
        if not admin:
            admin = Admin(
                username='admin',
                email='admin@biped.app',
                first_name='Admin',
                last_name='User',
                role='super_admin',
                is_super_admin=True,
                is_active=True
            )
            admin.set_password('biped_admin_2025')
            db.session.add(admin)
            print("✅ Default admin user created")
        
        # Create default service categories
        categories = [
            ('Construction & Renovation', 'construction-renovation'),
            ('Plumbing & Electrical', 'plumbing-electrical'),
            ('Tech & Digital', 'tech-digital'),
            ('Automotive', 'automotive'),
            ('Landscaping', 'landscaping'),
            ('Cleaning & Maintenance', 'cleaning-maintenance')
        ]
        
        for category_name, category_slug in categories:
            category = ServiceCategory.query.filter_by(name=category_name).first()
            if not category:
                category = ServiceCategory(
                    name=category_name,
                    slug=category_slug,
                    description=f'Professional {category_name.lower()} services',
                    is_active=True
                )
                db.session.add(category)
        
        # Commit all changes
        db.session.commit()
        print("✅ Production database initialized successfully")
        
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Database initialization error: {e}")

# Run database initialization
with app.app_context():
    init_production_database()

# Initialize caching service if available
trading_cache = TradingCacheService(app) if TradingCacheService else None
if trading_cache:
    print("✅ Trading cache service initialized")

# Initialize security enhancements if available
security_config = SecurityConfig() if SecurityConfig else None
security_enhancer = SecurityEnhancer(app, security_config) if SecurityEnhancer and security_config else None
if security_enhancer:
    print("✅ Security enhancements initialized")

# Initialize WebSocket support if available
socketio = init_socketio(app) if init_socketio else None
if socketio:
    print("✅ WebSocket support initialized")

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
app.register_blueprint(auth_bp)  # Unified auth handles all authentication
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(service_bp, url_prefix="/api/services")
app.register_blueprint(job_bp, url_prefix="/api/jobs")
app.register_blueprint(payment_bp, url_prefix="/api/payments")
app.register_blueprint(review_bp, url_prefix="/api/reviews")
app.register_blueprint(storage_bp, url_prefix="/api/storage")
app.register_blueprint(health_bp, url_prefix="/health")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(business_bp, url_prefix="/api/business")
app.register_blueprint(jobs_api_bp, url_prefix="/api/jobs-api")
app.register_blueprint(vision_bp, url_prefix="/api/vision")

# Register optional blueprints if available
if admin_bp:
    app.register_blueprint(admin_bp, url_prefix="/api/admin-panel")
if ai_bp:
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
if analytics_bp:
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
if websocket_bp:
    app.register_blueprint(websocket_bp, url_prefix="/api/ws")

# Basic routes
@app.route('/')
def index():
    """Serve the landing page"""
    return send_from_directory('static', 'landing.html')

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

@app.route('/dashboard')
def dashboard():
    """Serve the dashboard page"""
    return send_from_directory('static', 'dashboard.html')

@app.route('/admin')
def admin():
    """Serve the admin dashboard page"""
    return send_from_directory('static', 'admin.html')

# Catch-all route for static files
@app.route('/<path:path>')
def serve_static_files(path):
    """Serve static files or fallback to index.html for SPA routing"""
    # Check if the path exists as a static file
    static_path = os.path.join(app.static_folder, path)
    if os.path.isfile(static_path):
        return send_from_directory(app.static_folder, path)
    
    # Check if it's a known HTML route
    if path in ['profile', 'billing', 'settings', 'admin-login', 'dev-login', 'dashboard', 'admin']:
        return send_from_directory(app.static_folder, f"{path}.html")
    
    # Fallback to landing page for SPA routing
    return send_from_directory(app.static_folder, 'landing.html')

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({"status": "ok", "timestamp": time.time()})

if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        
    # Start the Flask application
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

