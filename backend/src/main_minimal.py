"""
Biped Platform - Minimal Secure Version
Production-ready Flask app with critical security fixes applied
"""

import logging
import os
import secrets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_app():
    """Minimal secure application factory"""

    # Check if we have Flask available
    try:
        from flask import Flask, jsonify, render_template, request
        from flask_cors import CORS
    except ImportError as e:
        logger.error(f"Missing required dependencies: {e}")
        logger.error("Please install: pip install flask flask-cors")
        raise

    app = Flask(__name__, static_folder="static", template_folder="static/templates")

    # SECURE Configuration - No hard-coded secrets
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        if os.environ.get("ENVIRONMENT") == "production":
            raise ValueError(
                "SECRET_KEY environment variable is required in production"
            )
        else:
            # Use a consistent development secret key
            secret_key = "dev-secret-key-change-in-production-" + secrets.token_hex(16)
            logger.warning(
                "⚠️  Using development secret key. Set SECRET_KEY environment variable for production."
            )

    app.config["SECRET_KEY"] = secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Secure CORS configuration
    allowed_origins = [
        "https://home.biped.app",
        "https://biped.app",
        "https://www.biped.app",
    ]

    # Allow localhost only in development
    if os.environ.get("ENVIRONMENT") != "production":
        allowed_origins.extend(
            [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
            ]
        )

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
            }
        },
    )

    # CRITICAL: Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        """Add essential security headers"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:;"
        )

        # Add HSTS only in production with HTTPS
        if os.environ.get("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        return response

    # Basic health check endpoint
    @app.route("/api/health")
    def health_check():
        """Health check endpoint"""
        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0-secure",
                "environment": os.environ.get("ENVIRONMENT", "development"),
            }
        )

    # Basic landing page
    @app.route("/")
    def index():
        """Landing page"""
        return jsonify(
            {
                "message": "Biped Platform - Secure Version",
                "status": "running",
                "timestamp": datetime.utcnow().isoformat(),
                "security": "enabled",
            }
        )

    # Error handling
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    logger.info("✅ Biped minimal secure app created successfully")
    logger.info(f"✅ Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    logger.info(f"✅ Secret key configured: {'Yes' if secret_key else 'No'}")
    logger.info(f"✅ CORS origins: {len(allowed_origins)} configured")

    return app


# Production WSGI application
app = create_app()

if __name__ == "__main__":
    # Development server
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("ENVIRONMENT") != "production"

    logger.info(f"🚀 Starting Biped app on port {port}")
    logger.info("🔒 Security headers: enabled")
    logger.info("🛡️  CORS protection: enabled")

    app.run(host="0.0.0.0", port=port, debug=debug)
