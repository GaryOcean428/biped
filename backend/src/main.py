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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # CORS configuration
    CORS(app, resources={r"/*": {"origins": "*"}})
    
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
                
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
    
    # Register blueprints
    try:
        from src.routes import auth_bp, admin_bp, dashboard_bp, health_bp
        from src.routes.integration import integration_bp
        
        app.register_blueprint(health_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        app.register_blueprint(integration_bp)
        
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
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    logger.info("🚀 Biped Platform initialized successfully")
    return app

# Create the application instance
app = create_app()

# For development only - production uses Gunicorn
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🔧 Development mode - starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

