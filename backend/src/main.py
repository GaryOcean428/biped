"""
Biped Platform - Production WSGI Application
Properly configured for Railway deployment with Gunicorn
"""

import logging
import os

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO
from sqlalchemy.exc import IntegrityError

from src.utils.error_handling import ErrorHandler

# Import security utilities
from src.utils.security import SecurityConfig, SecurityEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory pattern for production deployment"""

    app = Flask(__name__, static_folder="static", template_folder="static/templates")

    # Configuration - Secure secret management
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        if os.environ.get("ENVIRONMENT") == "production":
            raise ValueError(
                "SECRET_KEY environment variable is required in production"
            )
        else:
            # Generate a random secret for development
            import secrets

            secret_key = secrets.token_hex(32)
            logger.warning(
                "⚠️  Using auto-generated secret key for development. Set SECRET_KEY environment variable."
            )

    app.config["SECRET_KEY"] = secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }

    jwt_secret_key = os.environ.get("JWT_SECRET_KEY", secret_key)
    app.config["JWT_SECRET_KEY"] = jwt_secret_key

    # Secure CORS configuration - restrict to specific domains in production
    allowed_origins = [
        "https://home.biped.app",
        "https://biped.app",
        "https://www.biped.app",
    ]
    # Allow localhost for development
    if (
        app.config.get("ENV") == "development"
        or os.environ.get("ENVIRONMENT") == "development"
    ):
        allowed_origins.extend(
            [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
            ]
        )

    # CORS configuration with security restrictions
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
            },
            r"/*": {"origins": allowed_origins, "supports_credentials": True},
        },
    )

    # Add essential security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:;"
        )

        # Only add HSTS in production with HTTPS
        if os.environ.get("ENVIRONMENT") == "production" and request.is_secure:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        return response

    # Initialize extensions
    from src.models import db

    db.init_app(app)

    # Initialize rate limiter
    from src.utils.rate_limiting import limiter

    limiter.init_app(app)

    # Initialize security enhancements
    try:
        security_config = SecurityConfig()
        security_enhancer = SecurityEnhancer(app, security_config)
        logger.info("✅ Security enhancements initialized")
    except Exception as e:
        logger.warning(f"⚠️ Security setup failed: {e}")

    # Set up error handling
    error_handler = ErrorHandler()
    app.logger = error_handler.setup_logging()

    # Initialize Redis
    redis_client = None
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis

            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")

    # Initialize SocketIO for production
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode="threading",
        logger=False,
        engineio_logger=False,
    )

    # Create database tables and initial data
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Database tables created")

            # Create default admin user if not exists
            from src.models import Admin

            if not Admin.query.filter_by(username="admin").first():
                import secrets

                from werkzeug.security import generate_password_hash

                # Get admin password from environment or generate secure one
                admin_password = os.environ.get("ADMIN_PASSWORD")
                if not admin_password:
                    admin_password = secrets.token_urlsafe(16)
                    logger.warning(f"⚠️  Generated admin password: {admin_password}")
                    logger.warning(
                        "⚠️  Set ADMIN_PASSWORD environment variable to use a custom password"
                    )

                admin = Admin(
                    username="admin",
                    email="admin@biped.app",
                    password_hash=generate_password_hash(admin_password),
                    first_name="Admin",
                    last_name="User",
                    role="super_admin",
                    is_active=True,
                    is_super_admin=True,
                )
                db.session.add(admin)
                db.session.commit()
                logger.info("✅ Default admin user created")

            # Initialize sample data for services and categories
            from werkzeug.security import generate_password_hash

            from src.models import CustomerProfile, Service, ServiceCategory, User

            # Create service categories if they don't exist
            if ServiceCategory.query.count() == 0:
                categories_data = [
                    {
                        "name": "Construction & Renovation",
                        "slug": "construction-renovation",
                        "description": "General contractors, carpenters, painters, and renovation specialists",
                    },
                    {
                        "name": "Plumbing & Electrical",
                        "slug": "plumbing-electrical",
                        "description": "Licensed plumbers, electricians, and HVAC specialists",
                    },
                    {
                        "name": "Tech & Digital",
                        "slug": "tech-digital",
                        "description": "Web developers, designers, IT support, and digital marketing",
                    },
                    {
                        "name": "Automotive",
                        "slug": "automotive",
                        "description": "Mechanics, auto electricians, and vehicle specialists",
                    },
                    {
                        "name": "Landscaping",
                        "slug": "landscaping",
                        "description": "Gardeners, landscapers, and outdoor maintenance specialists",
                    },
                    {
                        "name": "Cleaning & Maintenance",
                        "slug": "cleaning-maintenance",
                        "description": "Professional cleaners, maintenance, and facility management",
                    },
                ]

                for cat_data in categories_data:
                    category = ServiceCategory(**cat_data)
                    db.session.add(category)

                db.session.commit()
                logger.info("✅ Service categories created")

                # Create sample services
                services_data = [
                    {
                        "category_id": 1,
                        "name": "Kitchen Renovation",
                        "slug": "kitchen-renovation",
                        "typical_price_min": 5000,
                        "typical_price_max": 25000,
                        "price_unit": "job",
                    },
                    {
                        "category_id": 1,
                        "name": "Bathroom Renovation",
                        "slug": "bathroom-renovation",
                        "typical_price_min": 3000,
                        "typical_price_max": 15000,
                        "price_unit": "job",
                    },
                    {
                        "category_id": 1,
                        "name": "House Painting",
                        "slug": "house-painting",
                        "typical_price_min": 2000,
                        "typical_price_max": 8000,
                        "price_unit": "job",
                    },
                    {
                        "category_id": 2,
                        "name": "Plumbing Repair",
                        "slug": "plumbing-repair",
                        "typical_price_min": 100,
                        "typical_price_max": 500,
                        "price_unit": "job",
                    },
                    {
                        "category_id": 2,
                        "name": "Electrical Installation",
                        "slug": "electrical-installation",
                        "typical_price_min": 150,
                        "typical_price_max": 1000,
                        "price_unit": "job",
                    },
                    {
                        "category_id": 3,
                        "name": "Website Development",
                        "slug": "website-development",
                        "typical_price_min": 1000,
                        "typical_price_max": 10000,
                        "price_unit": "job",
                    },
                    {
                        "category_id": 3,
                        "name": "IT Support",
                        "slug": "it-support",
                        "typical_price_min": 80,
                        "typical_price_max": 200,
                        "price_unit": "hour",
                    },
                    {
                        "category_id": 4,
                        "name": "Car Service",
                        "slug": "car-service",
                        "typical_price_min": 200,
                        "typical_price_max": 800,
                        "price_unit": "job",
                    },
                    {
                        "category_id": 5,
                        "name": "Garden Maintenance",
                        "slug": "garden-maintenance",
                        "typical_price_min": 50,
                        "typical_price_max": 200,
                        "price_unit": "hour",
                    },
                    {
                        "category_id": 6,
                        "name": "House Cleaning",
                        "slug": "house-cleaning",
                        "typical_price_min": 80,
                        "typical_price_max": 300,
                        "price_unit": "job",
                    },
                ]

                for service_data in services_data:
                    service = Service(**service_data)
                    db.session.add(service)

                db.session.commit()
                logger.info("✅ Sample services created")

            # Create sample customer if doesn't exist
            if not User.query.filter_by(email="customer@biped.app").first():
                sample_user = User(
                    email="customer@biped.app",
                    password_hash=generate_password_hash("password123"),
                    first_name="John",
                    last_name="Doe",
                    phone="+61400000000",
                    street_address="123 Test Street",
                    city="Sydney",
                    state="NSW",
                    postcode="2000",
                    user_type="customer",
                    is_active=True,
                    is_verified=True,
                )
                db.session.add(sample_user)
                db.session.commit()

                customer_profile = CustomerProfile(
                    user_id=sample_user.id,
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
        from src.routes import (
            admin_bp,
            advanced_search_bp,
            ai_bp,
            auth_bp,
            dashboard_bp,
            health_bp,
            jobs_bp,
            jobs_api_bp,
            payment_bp,
        )

        logger.info("✅ Blueprints imported successfully")

        app.register_blueprint(health_bp)
        logger.info("✅ Health blueprint registered")

        app.register_blueprint(auth_bp)  # auth_bp already has /api/auth prefix
        logger.info("✅ Auth blueprint registered")

        app.register_blueprint(admin_bp, url_prefix="/admin")
        logger.info("✅ Admin blueprint registered")

        app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
        logger.info("✅ Dashboard blueprint registered")

        app.register_blueprint(jobs_bp)
        logger.info("✅ Jobs blueprint registered")

        app.register_blueprint(jobs_api_bp)
        logger.info("✅ Jobs API blueprint registered")

        app.register_blueprint(payment_bp, url_prefix="/api/payments")
        logger.info("✅ Payment blueprint registered")

        app.register_blueprint(advanced_search_bp)
        logger.info("✅ Advanced Search blueprint registered")

        app.register_blueprint(ai_bp)
        logger.info("✅ AI blueprint registered")

        logger.info("✅ All blueprints registered successfully")

    except ImportError as e:
        logger.warning(f"⚠️ Blueprint import error: {e}")
    except Exception as e:
        logger.error(f"❌ Blueprint registration error: {e}")

    # Root routes
    @app.route("/")
    def index():
        """Landing page"""
        try:
            return render_template("landing.html")
        except Exception:
            return jsonify(
                {
                    "message": "🚀 Biped Platform Running",
                    "status": "healthy",
                    "version": "2.0",
                    "redis": bool(redis_client),
                }
            )

    @app.route("/health")
    def health():
        """Health check endpoint for Railway"""
        return jsonify(
            {
                "status": "healthy",
                "redis": bool(redis_client),
                "database": bool(app.config.get("SQLALCHEMY_DATABASE_URI")),
                "version": "2.0",
            }
        )

    # Additional page routes to fix 404 errors
    @app.route("/dashboard")
    def dashboard():
        """Customer dashboard"""
        try:
            return render_template("dashboard.html")
        except Exception:
            # Fallback to serving the static file directly
            return app.send_static_file("dashboard.html")

    @app.route("/provider-dashboard")
    def provider_dashboard():
        """Provider dashboard"""
        try:
            return render_template("provider-dashboard.html")
        except Exception:
            # Fallback to serving the static file directly
            return app.send_static_file("provider-dashboard.html")

    @app.route("/jobs")
    def jobs():
        """Job listings page"""
        try:
            return render_template("job-posting.html")
        except Exception:
            # Fallback to serving the static file directly
            return app.send_static_file("job-posting.html")

    @app.route("/post-job")
    def post_job():
        """Job posting page"""
        try:
            return render_template("post_job.html")
        except Exception:
            # Fallback to serving the static file directly
            return app.send_static_file("post_job.html")

    @app.route("/about")
    def about():
        """About page"""
        try:
            return render_template("about.html")
        except Exception:
            # Fallback to serving the static file directly
            return app.send_static_file("about.html")

    @app.route("/contact")
    def contact():
        """Contact page"""
        try:
            return render_template("contact.html")
        except Exception:
            # Fallback to serving the static file directly
            return app.send_static_file("contact.html")

    @app.route("/privacy")
    def privacy():
        """Privacy policy page"""
        try:
            return render_template("privacy.html")
        except Exception:
            # Fallback to serving the static file directly
            return app.send_static_file("privacy.html")

    @app.route("/terms")
    def terms():
        """Terms of service page"""
        try:
            return render_template("terms.html")
        except Exception:
            # Fallback to serving the static file directly
            return app.send_static_file("terms.html")

    # Enhanced Error handlers with custom pages and security
    @app.errorhandler(404)
    def not_found(error):
        # Check if request is from API or browser
        if (
            request.path.startswith("/api/")
            or request.headers.get("Content-Type") == "application/json"
            or "application/json" in request.headers.get("Accept", "")
        ):
            return (
                jsonify(
                    {
                        "error": "Page not found",
                        "message": "The requested resource could not be found",
                        "status_code": 404,
                    }
                ),
                404,
            )
        else:
            try:
                return render_template("errors/404.html"), 404
            except Exception:
                return (
                    jsonify(
                        {
                            "error": "Page not found",
                            "message": "The requested resource could not be found",
                            "status_code": 404,
                        }
                    ),
                    404,
                )

    @app.errorhandler(403)
    def forbidden(error):
        # Check if request is from API or browser
        if (
            request.path.startswith("/api/")
            or request.headers.get("Content-Type") == "application/json"
            or "application/json" in request.headers.get("Accept", "")
        ):
            return (
                jsonify(
                    {
                        "error": "Access forbidden",
                        "message": "You do not have permission to access this resource",
                        "status_code": 403,
                    }
                ),
                403,
            )
        else:
            try:
                return render_template("errors/403.html"), 403
            except Exception:
                return (
                    jsonify(
                        {
                            "error": "Access forbidden",
                            "message": "You do not have permission to access this resource",
                            "status_code": 403,
                        }
                    ),
                    403,
                )

    @app.errorhandler(500)
    def internal_error(error):
        # Log the error for debugging
        app.logger.error(f"Server Error: {error}", exc_info=True)

        # Check if request is from API or browser
        if (
            request.path.startswith("/api/")
            or request.headers.get("Content-Type") == "application/json"
            or "application/json" in request.headers.get("Accept", "")
        ):
            return (
                jsonify(
                    {
                        "error": "Internal server error",
                        "message": "An unexpected error occurred. Please try again later.",
                        "status_code": 500,
                    }
                ),
                500,
            )
        else:
            try:
                return render_template("errors/500.html"), 500
            except Exception:
                return (
                    jsonify(
                        {
                            "error": "Internal server error",
                            "message": "An unexpected error occurred. Please try again later.",
                            "status_code": 500,
                        }
                    ),
                    500,
                )

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return (
            jsonify(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "status_code": 429,
                }
            ),
            429,
        )

    logger.info("🚀 Biped Platform initialized successfully")
    return app


# Create the application instance
app = create_app()

# For development only - production uses Gunicorn
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🔧 Development mode - starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
