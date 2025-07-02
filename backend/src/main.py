import os
import sys
import time
from flask import Flask, send_from_directory, g

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask_cors import CORS

# Import core models only
from src.models.user import db, User, CustomerProfile, ProviderProfile
from src.models.service import ServiceCategory, Service, ProviderService, PortfolioItem
from src.models.job import Job, Quote, JobMilestone, JobMessage
from src.models.review import Review, Message, Notification
from src.models.admin import Admin, AdminAction
from src.models.payment import Payment, Transfer, StripeAccount, Dispute

# Import core routes only
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

# Create health blueprint
from flask import Blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'message': 'Biped Platform API is running', 'version': '1.0.0'}

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Basic configuration with /data volume support
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

# Database configuration - use /data volume for persistence
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

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'biped-production-secret-key-2025')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration using /data volume
app.config['UPLOAD_FOLDER'] = os.path.join(DATA_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'logs'), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'backups'), exist_ok=True)

# Enable CORS for all routes
CORS(app, origins="*")

# Register core blueprints
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
app.register_blueprint(health_bp, url_prefix='/api')

# Database initialization
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

if __name__ == '__main__':
    # Get port from environment variable, default to 8080
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting Biped Platform on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

