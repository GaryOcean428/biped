import os
import sys
import time
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

# Import all models
from src.models.user import db, User, CustomerProfile, ProviderProfile
from src.models.service import ServiceCategory, Service, ProviderService, PortfolioItem
from src.models.job import Job, Quote, JobMilestone, JobMessage
from src.models.review import Review, Message, Notification
from src.models.admin import Admin, AdminAction
from src.models.payment import Payment, Transfer, StripeAccount, Dispute

# Import routes
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
from src.routes.health import health_bp

# Import new performance and security utilities
from src.utils.security import security_headers, performance_monitor
from src.utils.performance import response_cache, compression_middleware, static_optimizer
from src.utils.config import config_manager

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Apply advanced configuration
flask_config = config_manager.get_flask_config()
app.config.update(flask_config)

# Log configuration validation issues
config_issues = config_manager.validate_config()
if config_issues:
    app.logger.warning(f"Configuration issues detected: {config_issues}")

# Enable CORS for all routes
CORS(app, origins="*")

# Register blueprints
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
app.register_blueprint(health_bp, url_prefix='/api')


# Security and Performance Middleware
@app.after_request
def apply_security_headers(response):
    """Apply security headers to all responses"""
    return security_headers.apply_security_headers(response)


@app.after_request
def apply_compression(response):
    """Apply response compression for large responses"""
    return compression_middleware.compress_response(response)


@app.before_request
def monitor_request_start():
    """Monitor request start time for performance tracking"""
    g.start_time = time.time()


@app.after_request
def monitor_request_end(response):
    """Monitor request completion and record metrics"""
    if hasattr(g, 'start_time'):
        response_time = time.time() - g.start_time
        performance_monitor.record_request(response_time, response.status_code)
    return response

# Database initialization (configuration handled by config_manager)
db.init_app(app)

# Create all tables
with app.app_context():
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
    
    # Create default admin user if none exists
    if Admin.query.count() == 0:
        admin = Admin(
            username='admin',
            email='admin@tradehub.com',
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
        print("Default admin user created: admin / admin123")

@app.route('/admin')
def admin_dashboard():
    """Serve the admin dashboard"""
    print("Admin route accessed - serving admin.html")
    return send_from_directory('static', 'admin.html')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'message': 'Biped Platform API is running', 'version': '1.0.0'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8180))
    app.run(host='0.0.0.0', port=port, debug=False)

