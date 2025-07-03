import os
import sys
import time
from flask import Flask, send_from_directory, g, request, jsonify, redirect, url_for, render_template_string

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

# Cache busting configuration
CACHE_BUST = os.environ.get('CACHE_BUST', str(int(time.time())))

# Make security enhancer available in request context
@app.before_request
def before_request():
    g.security_enhancer = security_enhancer
    g.cache_service = trading_cache
    g.start_time = time.time()
    g.cache_bust = CACHE_BUST
    
    # Log request for monitoring
    if not request.path.startswith('/static'):
        print(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def after_request(response):
    # Add cache busting headers for static files
    if request.path.startswith('/static') or request.path.endswith(('.css', '.js', '.png', '.jpg', '.ico')):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['ETag'] = f'"{CACHE_BUST}"'
    
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

# MAIN APPLICATION ROUTES - FIXED ROUTING SYSTEM

@app.route('/')
def root():
    """Serve the main trades marketplace application"""
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    
    # Try to serve the main application interface
    main_app_files = [
        'dashboard-enhanced.html',
        'index.html', 
        'dashboard.html'
    ]
    
    for filename in main_app_files:
        file_path = os.path.join(static_folder_path, filename)
        if os.path.exists(file_path):
            print(f"✅ Serving main app from: {filename}")
            response = send_from_directory(static_folder_path, filename)
            # Add cache busting headers
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
    
    # Fallback: Create a simple redirect to dashboard
    print("⚠️ No main app file found, redirecting to dashboard")
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    """Serve the provider dashboard"""
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    
    dashboard_files = [
        'dashboard-enhanced.html',
        'dashboard.html'
    ]
    
    for filename in dashboard_files:
        file_path = os.path.join(static_folder_path, filename)
        if os.path.exists(file_path):
            print(f"✅ Serving dashboard from: {filename}")
            response = send_from_directory(static_folder_path, filename)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response
    
    return jsonify({'error': 'Dashboard not found'}), 404

@app.route('/jobs')
def jobs():
    """Serve the job posting interface"""
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    
    job_files = [
        'enhanced-job-posting.html',
        'jobs.html'
    ]
    
    for filename in job_files:
        file_path = os.path.join(static_folder_path, filename)
        if os.path.exists(file_path):
            response = send_from_directory(static_folder_path, filename)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response
    
    return jsonify({'error': 'Jobs interface not found'}), 404

@app.route('/providers')
def providers():
    """Serve the provider interface"""
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    
    provider_files = [
        'provider-dashboard.html',
        'providers.html'
    ]
    
    for filename in provider_files:
        file_path = os.path.join(static_folder_path, filename)
        if os.path.exists(file_path):
            response = send_from_directory(static_folder_path, filename)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response
    
    return jsonify({'error': 'Provider interface not found'}), 404

@app.route('/admin')
def admin():
    """Serve the admin dashboard"""
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    
    admin_files = [
        'admin.html'
    ]
    
    for filename in admin_files:
        file_path = os.path.join(static_folder_path, filename)
        if os.path.exists(file_path):
            response = send_from_directory(static_folder_path, filename)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response
    
    return jsonify({'error': 'Admin interface not found'}), 404

# Static file serving with cache busting
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files with cache busting"""
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    
    try:
        response = send_from_directory(static_folder_path, filename)
        
        # Add cache busting headers
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['ETag'] = f'"{CACHE_BUST}"'
        
        # Set proper MIME types
        if filename.endswith('.js'):
            response.headers['Content-Type'] = 'text/javascript'
        elif filename.endswith('.css'):
            response.headers['Content-Type'] = 'text/css'
        elif filename.endswith('.json'):
            response.headers['Content-Type'] = 'application/json'
        elif filename.endswith('.ico'):
            response.headers['Content-Type'] = 'image/x-icon'
        elif filename.endswith('.png'):
            response.headers['Content-Type'] = 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            response.headers['Content-Type'] = 'image/jpeg'
        elif filename.endswith('.svg'):
            response.headers['Content-Type'] = 'image/svg+xml'
        
        return response
        
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

# API status endpoint
@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'operational',
        'version': '2.0',
        'platform': 'Biped Trades Marketplace',
        'cache_bust': CACHE_BUST,
        'timestamp': int(time.time())
    })

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

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors by redirecting to main app"""
    # For API routes, return JSON error
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # For other routes, redirect to main app
    return redirect('/')

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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=False)

