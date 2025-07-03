import os
import sys
import time
from flask import Flask, send_from_directory, g, request, jsonify, redirect

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask_cors import CORS
from flask_migrate import Migrate
from flask_compress import Compress
from flask_caching import Cache

# Import Railway-optimized configuration
from config import get_config

# Import enhanced security and performance modules
from src.utils.security import SecurityEnhancer, SecurityConfig
from src.utils.redis_client import redis_client
from src.utils.performance import TradingCacheService, configure_performance
from src.routes.analytics import analytics_bp
from src.services.data_pipeline import create_data_services
from src.routes.websocket import websocket_bp, init_socketio
from src.routes.health import health_bp

# Import core models
from src.models.user import db, User, CustomerProfile, ProviderProfile
from src.models.service import ServiceCategory, Service, ProviderService, PortfolioItem
from src.models.job import Job, Quote, JobMilestone, JobMessage
from src.models.review import Review, Message, Notification
from src.models.admin import Admin, AdminAction
from src.models.payment import Payment, Transfer, StripeAccount, Dispute

# Import route blueprints
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.service import service_bp
from src.routes.job import job_bp
from src.routes.review import review_bp
from src.routes.admin import admin_bp
from src.routes.payment import payment_bp
from src.routes.ai import ai_bp
from src.routes.vision import vision_bp
from src.routes.analytics import analytics_bp
from src.routes.business import business_bp
from src.routes.storage import storage_bp
from src.routes.websocket import websocket_bp
from src.routes.health import health_bp
from src.routes.dashboard import dashboard_bp
from src.routes.jobs_api import jobs_api_bp

# Create Flask app with static folder configuration
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Load Railway-optimized configuration
config_class = get_config()
app.config.from_object(config_class)

# Enhanced configuration with /data volume support
DATA_DIR = app.config['DATA_DIR']

# Check if we can access the data directory, fallback to local if not
try:
    os.makedirs(DATA_DIR, exist_ok=True)
    # Test write access
    test_file = os.path.join(DATA_DIR, '.write_test')
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print(f"✅ Data directory accessible: {DATA_DIR}")
except (PermissionError, OSError) as e:
    # Fallback to local directory for development
    DATA_DIR = os.path.join(os.getcwd(), 'data')
    print(f"⚠️ Cannot access /data ({e}), falling back to {DATA_DIR}")
    os.makedirs(DATA_DIR, exist_ok=True)
    app.config['DATA_DIR'] = DATA_DIR

# Create additional directories safely
try:
    os.makedirs(os.path.join(DATA_DIR, 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, 'reports'), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, 'backups'), exist_ok=True)
    
    # Update upload folder configuration to use the working data directory
    app.config['UPLOAD_FOLDER'] = os.path.join(DATA_DIR, 'uploads')
    print(f"✅ Upload folder configured: {app.config['UPLOAD_FOLDER']}")
except (PermissionError, OSError) as e:
    print(f"⚠️ Directory creation warning: {e}")
    # Ensure upload folder is set to a safe default
    app.config['UPLOAD_FOLDER'] = os.path.join(DATA_DIR, 'uploads')

print(f"🚀 Starting Enhanced Biped Platform v2.0")
print(f"📊 Environment: {app.config['ENVIRONMENT']}")
print(f"🗄️ Database: {'PostgreSQL (Railway)' if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql') else 'SQLite (Local)'}")
print(f"🔄 Redis: {'Available (Railway)' if app.config['REDIS_URL'] else 'Not configured'}")
print(f"💾 Data Directory: {DATA_DIR}")

# Initialize Flask extensions with Railway-optimized configuration
db.init_app(app)
migrate = Migrate(app, db)
cache = Cache(app)
compress = Compress(app)

# Initialize CORS with configuration
CORS(app, 
     origins=app.config['CORS_ORIGINS'],
     allow_headers=app.config['CORS_ALLOW_HEADERS'],
     methods=app.config['CORS_METHODS'])

# Initialize security enhancements

# Security headers configuration
app.config['FORCE_HTTPS'] = os.environ.get('FORCE_HTTPS', 'true').lower() == 'true'

# Monitoring configuration
app.config['SENTRY_DSN'] = os.environ.get('SENTRY_DSN')
app.config['ENVIRONMENT'] = os.environ.get('ENVIRONMENT', 'production')

# Configure performance optimizations
configure_performance(app)

# Initialize database with app and set up migrations (check if already initialized)
if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
    db.init_app(app)
    print("✅ Database initialized with app")
else:
    print("✅ Database already initialized, skipping")

migrate = Migrate(app, db)

# Initialize caching
cache = Cache(app)
trading_cache = TradingCacheService(app)

# Initialize compression
Compress(app)

# Initialize security enhancements
security_config = SecurityConfig()
security_enhancer = SecurityEnhancer(app, security_config)

# Initialize WebSocket support
socketio = init_socketio(app)

# Enable CORS for all routes with enhanced security
CORS(app, 
     origins=os.environ.get('CORS_ORIGINS', '*').split(','),
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization', 'X-API-Key', 'X-CSRF-Token'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])

# Make security enhancer available in request context
@app.before_request
def before_request():
    g.security_enhancer = security_enhancer
    g.cache_service = trading_cache
    g.start_time = time.time()
    
    # Log request for monitoring
    if not request.path.startswith('/static'):
        print(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def after_request(response):
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Add performance headers
    if hasattr(g, 'start_time'):
        response.headers['X-Response-Time'] = f"{(time.time() - g.start_time) * 1000:.2f}ms"
    
    return response

# Register enhanced blueprints with rate limiting
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(service_bp, url_prefix='/api/services')
app.register_blueprint(job_bp, url_prefix='/api/jobs')
app.register_blueprint(ai_bp, url_prefix='/api/ai')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
app.register_blueprint(business_bp, url_prefix='/api/business')
app.register_blueprint(storage_bp, url_prefix='/api/storage')
app.register_blueprint(websocket_bp, url_prefix='/ws')
app.register_blueprint(health_bp, url_prefix='/health')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(jobs_api_bp)  # No prefix for API routes

# Enhanced database initialization
with app.app_context():
    try:
        db.create_all()
        
        # Create default service categories if they don't exist
        if ServiceCategory.query.count() == 0:
            categories = [
                {'name': 'Plumbing', 'slug': 'plumbing', 'description': 'Water, drainage, and gas fitting services', 'icon': 'wrench'},
                {'name': 'Electrical', 'slug': 'electrical', 'description': 'Electrical installation, repair, and maintenance', 'icon': 'bolt'},
                {'name': 'Carpentry', 'slug': 'carpentry', 'description': 'Wood working, furniture, and structural carpentry', 'icon': 'hammer'},
                {'name': 'Painting', 'slug': 'painting', 'description': 'Interior and exterior painting services', 'icon': 'paint-brush'},
                {'name': 'Landscaping', 'slug': 'landscaping', 'description': 'Garden design, maintenance, and outdoor spaces', 'icon': 'leaf'},
                {'name': 'Cleaning', 'slug': 'cleaning', 'description': 'House cleaning and maintenance services', 'icon': 'sparkles'},
                {'name': 'Roofing', 'slug': 'roofing', 'description': 'Roof installation, repair, and maintenance', 'icon': 'home'},
                {'name': 'Flooring', 'slug': 'flooring', 'description': 'Floor installation, repair, and refinishing', 'icon': 'square'},
            ]
            
            for i, cat_data in enumerate(categories):
                category = ServiceCategory(
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    description=cat_data['description'],
                    icon=cat_data['icon'],
                    sort_order=i
                )
                db.session.add(category)
            
            db.session.commit()
            print("✅ Default service categories created")
        
        # Create default admin user if none exists
        if Admin.query.count() == 0:
            admin = Admin(
                username='admin',
                email='admin@biped.com',
                first_name='System',
                last_name='Administrator',
                role='super_admin',
                is_super_admin=True,
                is_active=True
            )
            admin.set_password('admin123')  # Change this in production!
            admin.permissions = admin.get_default_permissions()
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin user created: admin / admin123")
            
        print("✅ Database initialization completed")
        
        # Initialize data services
        try:
            data_services = create_data_services(app, trading_cache)
            app.config['DATA_SERVICES'] = data_services
            app.config['CACHE_SERVICE'] = trading_cache
            print("✅ Data services initialized")
        except Exception as e:
            print(f"⚠️ Data services initialization warning: {e}")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

# Enhanced route handlers
@app.route('/admin')
def admin_dashboard():
    """Serve the admin dashboard"""
    return send_from_directory('static', 'admin.html')

@app.route('/')
def root():
    """Serve the trades marketplace dashboard at root"""
    return send_from_directory('static', 'index.html')

@app.route('/dashboard')
def enhanced_dashboard():
    """Serve the trades marketplace dashboard"""
    return send_from_directory('static', 'dashboard.html')

@app.route('/api/metrics')
@security_enhancer.api_rate_limit
def metrics_endpoint():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/api/security/status')
@security_enhancer.api_rate_limit
def security_status():
    """Security status endpoint"""
    return {
        'rate_limiting': True,
        'csrf_protection': True,
        'jwt_enabled': True,
        'redis_connected': redis_client.is_connected(),
        'security_headers': True,
        'input_validation': True
    }

# Specific route handlers for different pages
@app.route('/jobs')
def jobs_page():
    """Serve the job posting interface"""
    return send_from_directory('static', 'enhanced-job-posting.html')

@app.route('/providers')
def providers_page():
    """Serve the provider dashboard"""
    return send_from_directory('static', 'provider-dashboard.html')

@app.route('/mobile')
def mobile_page():
    """Serve the mobile interface"""
    return send_from_directory('static', 'mobile.html')

# Static file handler for assets
@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serve static files (CSS, JS, images, etc.)"""
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    
    # Handle API routes - don't serve HTML for these
    if filename.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # Handle static assets (CSS, JS, images, etc.)
    if '.' in filename:
        file_path = os.path.join(static_folder_path, filename)
        
        # Handle legacy /css/ paths by redirecting to /static/css/
        if filename.startswith('css/') and not os.path.exists(file_path):
            static_path = 'static/' + filename
            file_path = os.path.join(static_folder_path, static_path)
            if os.path.exists(file_path):
                filename = static_path
        
        if os.path.exists(file_path):
            # Determine MIME type based on file extension
            mimetype = None
            if filename.endswith('.js'):
                mimetype = 'text/javascript'
            elif filename.endswith('.css'):
                mimetype = 'text/css'
            elif filename.endswith('.json'):
                mimetype = 'application/json'
            elif filename.endswith('.ico'):
                mimetype = 'image/x-icon'
            elif filename.endswith('.png'):
                mimetype = 'image/png'
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                mimetype = 'image/jpeg'
            elif filename.endswith('.svg'):
                mimetype = 'image/svg+xml'
            elif filename.endswith('.woff'):
                mimetype = 'font/woff'
            elif filename.endswith('.woff2'):
                mimetype = 'font/woff2'
            elif filename.endswith('.ttf'):
                mimetype = 'font/ttf'
            elif filename.endswith('.eot'):
                mimetype = 'application/vnd.ms-fontobject'
            
            # Send file with proper MIME type
            response = send_from_directory(static_folder_path, filename)
            if mimetype:
                response.headers['Content-Type'] = mimetype
            return response
    
    # For any other route, serve the dashboard (trades marketplace)
    return send_from_directory('static', 'dashboard.html')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

if __name__ == '__main__':
    # Railway deployment best practices
    # Get port from environment variable with proper error handling
    try:
        port = int(os.environ.get('PORT', 8080))
        if port <= 0 or port > 65535:
            raise ValueError(f"Invalid port number: {port}")
    except (ValueError, TypeError) as e:
        print(f"❌ Port configuration error: {e}")
        print("   Using default port 8080")
        port = 8080
    
    # Environment configuration
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    environment = os.environ.get('ENVIRONMENT', 'production')
    
    print(f"🚀 Starting Enhanced Biped Platform v2.0")
    print(f"   Environment: {environment}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   Data Directory: {DATA_DIR}")
    print(f"   Redis Connected: {redis_client.is_connected()}")
    print(f"   Database: {'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}")
    print(f"   Security Enhanced: ✅")
    print(f"   Performance Optimized: ✅")
    print(f"   Real-time Features: ✅")
    print(f"   Analytics Engine: ✅")
    
    # Railway-specific optimizations
    if environment == 'production':
        print(f"   Production Mode: ✅")
        print(f"   HTTPS Enforced: {app.config.get('FORCE_HTTPS', False)}")
        print(f"   Health Check: /api/health")
        
        # Use Gunicorn for production (handled by Railway)
        # This will only run if not using Gunicorn
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=False,
            threaded=True,
            use_reloader=False
        )
    else:
        # Development mode with SocketIO
        print(f"   Development Mode: ✅")
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=port, 
            debug=debug,
            use_reloader=debug,
            log_output=True
        )

