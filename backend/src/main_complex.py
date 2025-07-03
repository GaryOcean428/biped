import os
import sys
import time

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, g, send_from_directory
from flask_cors import CORS

# Import only the models that are actually used
from src.models.service import ServiceCategory
from src.models.user import db
from src.models.admin import Admin

# Import routes
from src.routes.admin import admin_bp
from src.routes.admin_auth import admin_auth_bp
from src.routes.advanced_search import advanced_search_bp
from src.routes.ai import ai_bp
from src.routes.analytics import analytics_bp
from src.routes.auth import auth_bp
from src.routes.business import business_bp
from src.routes.communication import communication_bp
from src.routes.dashboard import dashboard_bp
from src.routes.financial import financial_bp
from src.routes.health import health_bp
from src.routes.integrations import integrations_bp
from src.routes.job import job_bp
from src.routes.notifications import notifications_bp
from src.routes.payment import payment_bp
from src.routes.real_estate import real_estate_bp
from src.routes.review import review_bp
from src.routes.service import service_bp
from src.routes.smart_matching import smart_matching_bp
from src.routes.user import user_bp
from src.routes.vision import vision_bp

from src.utils.config import config_manager
from src.utils.error_boundaries import register_error_handlers
from src.utils.performance import (
    CompressionMiddleware,
    PerformanceMonitor,
    ResponseCache,
    StaticAssetOptimizer,
)
from src.utils.security import SecurityEnhancer

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))

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
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(service_bp, url_prefix="/api/services")
app.register_blueprint(job_bp, url_prefix="/api/jobs")
app.register_blueprint(review_bp, url_prefix="/api/reviews")
app.register_blueprint(admin_bp)
app.register_blueprint(admin_auth_bp, url_prefix="/api/admin")
app.register_blueprint(payment_bp, url_prefix="/api/payments")
app.register_blueprint(ai_bp)
app.register_blueprint(vision_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(business_bp)
app.register_blueprint(financial_bp)
app.register_blueprint(integrations_bp)
app.register_blueprint(real_estate_bp)
app.register_blueprint(health_bp, url_prefix="/api")
app.register_blueprint(dashboard_bp)
app.register_blueprint(smart_matching_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(advanced_search_bp)
app.register_blueprint(communication_bp, url_prefix="/api/communication")

# Initialize utility instances
security_enhancer = SecurityEnhancer(app)
compression_middleware = CompressionMiddleware()
performance_monitor = PerformanceMonitor()


# Security and Performance Middleware
@app.after_request
def apply_security_headers(response):
    """Apply security headers to all responses"""
    return security_enhancer.apply_security_headers(response)


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
    if hasattr(g, "start_time"):
        response_time = time.time() - g.start_time
        performance_monitor.record_request(response_time, response.status_code)
    return response


# Database initialization (configuration handled by config_manager)
db.init_app(app)

# Register global error handlers
register_error_handlers(app)

# Create all tables
with app.app_context():
    db.create_all()

    # Create default service categories if they don't exist
    if ServiceCategory.query.count() == 0:
        categories = [
            {
                "name": "Plumbing",
                "slug": "plumbing",
                "description": "Water, drainage, and gas fitting services",
                "icon": "wrench",
            },
            {
                "name": "Electrical",
                "slug": "electrical",
                "description": "Electrical installation, repair, and maintenance",
                "icon": "bolt",
            },
            {
                "name": "Carpentry",
                "slug": "carpentry",
                "description": "Wood working, furniture, and structural carpentry",
                "icon": "hammer",
            },
            {
                "name": "Painting",
                "slug": "painting",
                "description": "Interior and exterior painting services",
                "icon": "paint-brush",
            },
            {
                "name": "Landscaping",
                "slug": "landscaping",
                "description": "Garden design, maintenance, and outdoor spaces",
                "icon": "leaf",
            },
            {
                "name": "Cleaning",
                "slug": "cleaning",
                "description": "House cleaning and maintenance services",
                "icon": "sparkles",
            },
            {
                "name": "Roofing",
                "slug": "roofing",
                "description": "Roof installation, repair, and maintenance",
                "icon": "home",
            },
            {
                "name": "Flooring",
                "slug": "flooring",
                "description": "Floor installation, repair, and refinishing",
                "icon": "square",
            },
        ]

        for i, cat_data in enumerate(categories):
            category = ServiceCategory(
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                icon=cat_data["icon"],
                sort_order=i,
            )
            db.session.add(category)

        db.session.commit()

    # Create default admin user if none exists
    if Admin.query.count() == 0:
        admin = Admin(
            username="admin",
            email="admin@tradehub.com",
            first_name="System",
            last_name="Administrator",
            role="super_admin",
            is_super_admin=True,
            is_active=True,
        )
        admin.set_password("admin123")  # Change this in production!
        admin.permissions = admin.get_default_permissions()
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: admin / admin123")


@app.route("/admin")
def admin_dashboard():
    """Serve the admin dashboard"""
    print("Admin route accessed - serving admin.html")
    return send_from_directory("static", "admin.html")


@app.route("/dashboard")
def dashboard():
    """Serve the user dashboard"""
    return send_from_directory("static", "dashboard.html")


@app.route("/post-job")
def post_job():
    """Serve the job posting form"""
    return send_from_directory("static", "job-posting.html")


@app.route("/admin-login")
def admin_login_page():
    """Serve the admin login page"""
    return send_from_directory("static", "admin-login.html")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_static(path):
    """Serve static files with proper routing"""
    static_folder_path = os.path.join(os.path.dirname(__file__), "static")

    # Handle specific routes
    if path == "dashboard":
        return send_from_directory(static_folder_path, "dashboard.html")
    elif path == "admin":
        return send_from_directory(static_folder_path, "admin.html")
    elif path == "admin-login":
        return send_from_directory(static_folder_path, "admin-login.html")
    elif path == "post-job":
        return send_from_directory(static_folder_path, "job-posting.html")
    elif path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        # Always serve landing page for root and unknown paths
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, "index.html")
        else:
            return "index.html not found", 404


if __name__ == "__main__":
    # Get port from environment variable, default to 8080
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting Biped Platform on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

