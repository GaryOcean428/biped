import os
import sys
import time
from flask import Flask, send_from_directory, g, request, jsonify

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask_cors import CORS
from flask_migrate import Migrate
from flask_compress import Compress
from flask_caching import Cache

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

# Import enhanced routes
from src.routes.user import user_bp
from src.routes.auth import auth_bp
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

# Import Flask and other dependencies
import os

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Enhanced configuration with /data volume support
DATA_DIR = os.environ.get('DATA_DIR', '/data')

# Check if we can access the data directory, fallback to local if not
try:
    os.makedirs(DATA_DIR, exist_ok=True)
    # Test write access
    test_file = os.path.join(DATA_DIR, '.write_test')
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
except (PermissionError, OSError):
    # Fallback to local directory for development
    DATA_DIR = os.path.join(os.getcwd(), 'data')
    print(f"Warning: Cannot access /data, falling back to {DATA_DIR}")
    os.makedirs(DATA_DIR, exist_ok=True)

# Enhanced database configuration
if os.environ.get('DATABASE_URL'):
    # Use Railway PostgreSQL if available
    database_url = os.environ.get('DATABASE_URL')
    # Fix postgres:// to postgresql:// for SQLAlchemy compatibility
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Use SQLite in /data volume for persistence
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATA_DIR}/biped.db'

# Security configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'biped-production-secret-key-2025')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Will be set by SecurityEnhancer

# Redis configuration
app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Cache configuration
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = app.config['REDIS_URL']

# File upload configuration using /data volume
app.config['UPLOAD_FOLDER'] = os.path.join(DATA_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Security headers configuration
app.config['FORCE_HTTPS'] = os.environ.get('FORCE_HTTPS', 'true').lower() == 'true'

# Monitoring configuration
app.config['SENTRY_DSN'] = os.environ.get('SENTRY_DSN')
app.config['ENVIRONMENT'] = os.environ.get('ENVIRONMENT', 'production')

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'logs'), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'backups'), exist_ok=True)

# Configure performance optimizations
configure_performance(app)

# Initialize database with migrations
db.init_app(app)
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
app.register_blueprint(review_bp, url_prefix='/api/reviews')
app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp, url_prefix='/api/payments')
app.register_blueprint(ai_bp)
app.register_blueprint(vision_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(business_bp)
app.register_blueprint(storage_bp)
app.register_blueprint(websocket_bp, url_prefix='/api/ws')
app.register_blueprint(health_bp, url_prefix='/api')

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

@app.route('/dashboard')
def enhanced_dashboard():
    """Serve the enhanced dashboard"""
    return send_from_directory('static', 'dashboard-enhanced.html')

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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    """Enhanced static file serving"""
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        # Check for enhanced dashboard
        if path.startswith('dashboard'):
            dashboard_path = os.path.join(static_folder_path, 'dashboard-enhanced.html')
            if os.path.exists(dashboard_path):
                return send_from_directory(static_folder_path, 'dashboard-enhanced.html')
        
        # Default to index
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

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

