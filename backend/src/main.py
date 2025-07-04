"""
Biped Platform - Production WSGI Application
Properly configured for Railway deployment with Gunicorn
"""

import os
import logging
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern for production deployment"""
    
    app = Flask(__name__, 
                static_folder='static',
                template_folder='static')
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    # Use SQLite for development if no DATABASE_URL is provided
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///biped_dev.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # CORS configuration
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Security configuration
    try:
        from src.utils.security import SecurityEnhancer
        security = SecurityEnhancer(app)
        logger.info("✅ Security enhancements configured")
    except ImportError as e:
        logger.warning(f"⚠️ Security module not available: {e}")
        # Add basic security headers manually
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            return response
    
    # Initialize extensions
    from src.models import db
    db.init_app(app)
    
    # Initialize Redis
    redis_client = None
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        try:
            import redis
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
    
    # Initialize SocketIO for production
    socketio = SocketIO(app, 
                       cors_allowed_origins="*", 
                       async_mode='threading',
                       logger=False,
                       engineio_logger=False)
    
    # Create database tables and initial data
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Database tables created")
            
            # Create default admin user if not exists
            from src.models import Admin
            if not Admin.query.filter_by(username='admin').first():
                from werkzeug.security import generate_password_hash
                admin = Admin(
                    username='admin',
                    email='admin@biped.app',
                    password_hash=generate_password_hash('biped_admin_2025'),
                    first_name='Admin',
                    last_name='User',
                    role='super_admin',
                    is_active=True,
                    is_super_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                logger.info("✅ Default admin user created")
            
            # Initialize sample data for services and categories
            from src.models import ServiceCategory, Service, User, CustomerProfile
            from werkzeug.security import generate_password_hash
            
            # Create service categories if they don't exist
            if ServiceCategory.query.count() == 0:
                categories_data = [
                    {'name': 'Construction & Renovation', 'slug': 'construction-renovation', 'description': 'General contractors, carpenters, painters, and renovation specialists'},
                    {'name': 'Plumbing & Electrical', 'slug': 'plumbing-electrical', 'description': 'Licensed plumbers, electricians, and HVAC specialists'},
                    {'name': 'Tech & Digital', 'slug': 'tech-digital', 'description': 'Web developers, designers, IT support, and digital marketing'},
                    {'name': 'Automotive', 'slug': 'automotive', 'description': 'Mechanics, auto electricians, and vehicle specialists'},
                    {'name': 'Landscaping', 'slug': 'landscaping', 'description': 'Gardeners, landscapers, and outdoor maintenance specialists'},
                    {'name': 'Cleaning & Maintenance', 'slug': 'cleaning-maintenance', 'description': 'Professional cleaners, maintenance, and facility management'}
                ]
                
                for cat_data in categories_data:
                    category = ServiceCategory(**cat_data)
                    db.session.add(category)
                
                db.session.commit()
                logger.info("✅ Service categories created")
                
                # Create sample services
                services_data = [
                    {'category_id': 1, 'name': 'Kitchen Renovation', 'slug': 'kitchen-renovation', 'typical_price_min': 5000, 'typical_price_max': 25000, 'price_unit': 'job'},
                    {'category_id': 1, 'name': 'Bathroom Renovation', 'slug': 'bathroom-renovation', 'typical_price_min': 3000, 'typical_price_max': 15000, 'price_unit': 'job'},
                    {'category_id': 1, 'name': 'House Painting', 'slug': 'house-painting', 'typical_price_min': 2000, 'typical_price_max': 8000, 'price_unit': 'job'},
                    {'category_id': 2, 'name': 'Plumbing Repair', 'slug': 'plumbing-repair', 'typical_price_min': 100, 'typical_price_max': 500, 'price_unit': 'job'},
                    {'category_id': 2, 'name': 'Electrical Installation', 'slug': 'electrical-installation', 'typical_price_min': 150, 'typical_price_max': 1000, 'price_unit': 'job'},
                    {'category_id': 3, 'name': 'Website Development', 'slug': 'website-development', 'typical_price_min': 1000, 'typical_price_max': 10000, 'price_unit': 'job'},
                    {'category_id': 3, 'name': 'IT Support', 'slug': 'it-support', 'typical_price_min': 80, 'typical_price_max': 200, 'price_unit': 'hour'},
                    {'category_id': 4, 'name': 'Car Service', 'slug': 'car-service', 'typical_price_min': 200, 'typical_price_max': 800, 'price_unit': 'job'},
                    {'category_id': 5, 'name': 'Garden Maintenance', 'slug': 'garden-maintenance', 'typical_price_min': 50, 'typical_price_max': 200, 'price_unit': 'hour'},
                    {'category_id': 6, 'name': 'House Cleaning', 'slug': 'house-cleaning', 'typical_price_min': 80, 'typical_price_max': 300, 'price_unit': 'job'}
                ]
                
                for service_data in services_data:
                    service = Service(**service_data)
                    db.session.add(service)
                
                db.session.commit()
                logger.info("✅ Sample services created")
            
            # Create sample customer if doesn't exist
            if not User.query.filter_by(email='customer@biped.app').first():
                sample_user = User(
                    email='customer@biped.app',
                    password_hash=generate_password_hash('password123'),
                    user_type='customer',
                    is_active=True,
                    is_verified=True
                )
                db.session.add(sample_user)
                db.session.commit()
                
                customer_profile = CustomerProfile(
                    user_id=sample_user.id,
                    first_name='John',
                    last_name='Doe',
                    phone='+61400000000',
                    street_address='123 Test Street',
                    city='Sydney',
                    state='NSW',
                    postcode='2000'
                )
                db.session.add(customer_profile)
                db.session.commit()
                logger.info("✅ Sample customer created")
                
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            # Don't fail the app startup due to database issues
            pass
    
    # Register blueprints
    try:
        from src.routes import auth_bp, admin_bp, dashboard_bp, health_bp, jobs_bp
        from src.routes.integration import integration_bp
        
        app.register_blueprint(health_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        app.register_blueprint(integration_bp)
        app.register_blueprint(jobs_bp)
        
        logger.info("✅ Blueprints registered successfully")
        
    except ImportError as e:
        logger.warning(f"⚠️ Blueprint import error: {e}")
    
    # Root routes
    @app.route('/')
    def index():
        """Landing page"""
        try:
            return render_template('landing.html')
        except:
            return jsonify({
                'message': '🚀 Biped Platform Running',
                'status': 'healthy',
                'version': '2.0',
                'redis': bool(redis_client)
            })
    
    @app.route('/health')
    def health():
        """Health check endpoint for Railway"""
        return jsonify({
            'status': 'healthy',
            'redis': bool(redis_client),
            'database': bool(app.config.get('SQLALCHEMY_DATABASE_URI')),
            'version': '2.0'
        })
    
    # Legal compliance routes
    @app.route('/privacy')
    def privacy_policy():
        """Privacy Policy page"""
        from datetime import datetime
        return render_template('privacy.html', current_date=datetime.now().strftime('%B %d, %Y'))
    
    @app.route('/terms')
    def terms_of_service():
        """Terms of Service page"""
        from datetime import datetime
        return render_template('terms.html', current_date=datetime.now().strftime('%B %d, %Y'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Custom 404 error page"""
        try:
            return render_template('404.html'), 404
        except:
            return jsonify({'error': 'Not found', 'status_code': 404}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Custom 500 error page"""
        try:
            import uuid
            from datetime import datetime
            error_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            logger.error(f"Internal server error {error_id}: {error}")
            return render_template('500.html', error_id=error_id, timestamp=timestamp), 500
        except:
            return jsonify({'error': 'Internal server error', 'status_code': 500}), 500
    
    logger.info("🚀 Biped Platform initialized successfully")
    return app

# Create the application instance
app = create_app()

# For development only - production uses Gunicorn
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🔧 Development mode - starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

