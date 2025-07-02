import os
import sys
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

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tradehub-secret-key-change-in-production')

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

# Database configuration - support both PostgreSQL (Railway) and SQLite (local)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Railway PostgreSQL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    return {'status': 'healthy', 'message': 'TradeHub API is running'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8180))
    app.run(host='0.0.0.0', port=port, debug=False)

