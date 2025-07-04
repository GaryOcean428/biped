"""
Unified Authentication Routes
============================

This module consolidates all authentication functionality for different user types
(customer, provider, admin, developer) into a single, maintainable route file.
"""

import os
import time
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request, session

# Import models
from src.models.admin import Admin
from src.models.user import CustomerProfile, ProviderProfile, User, db

# Import utilities
from src.utils.error_handling import handle_error
from src.utils.rate_limiting import limiter
from src.utils.validation import (
    validate_email,
    validate_password,
    validate_required_fields,
)
from werkzeug.security import check_password_hash, generate_password_hash

# Create blueprint
auth_bp = Blueprint("unified_auth", __name__, url_prefix="/api/auth")

# ===================================
# AUTHENTICATION DECORATORS
# ===================================


def login_required(f):
    """Decorator to require authentication for routes"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session and "admin_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator to require admin authentication"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            return jsonify({"error": "Admin authentication required"}), 401
        return f(*args, **kwargs)

    return decorated_function


def role_required(allowed_roles):
    """Decorator to require specific user roles"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user or user.get("user_type") not in allowed_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# ===================================
# UTILITY FUNCTIONS
# ===================================


def get_current_user():
    """Get current authenticated user"""
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user and user.is_active:
            # Get profile based on user type
            profile = None
            if user.user_type == "customer":
                profile = CustomerProfile.query.filter_by(user_id=user.id).first()
            elif user.user_type == "provider":
                profile = ProviderProfile.query.filter_by(user_id=user.id).first()

            return {
                "user": user.to_dict(),
                "profile": profile.to_dict() if profile else None,
            }
    return None


def get_current_admin():
    """Get current authenticated admin"""
    if "admin_id" in session:
        admin = Admin.query.get(session["admin_id"])
        if admin and admin.is_active:
            return admin.to_dict()
    return None


def create_user_session(user):
    """Create user session"""
    session["user_id"] = user.id
    session["user_type"] = user.user_type
    session["logged_in_at"] = time.time()

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()


def create_admin_session(admin):
    """Create admin session"""
    session["admin_id"] = admin.id
    session["admin_role"] = admin.role
    session["logged_in_at"] = time.time()

    # Update last login
    admin.last_login = datetime.utcnow()
    db.session.commit()


def clear_session():
    """Clear all session data"""
    session.clear()


def log_auth_attempt(email, success, user_type="user", ip_address=None):
    """Log authentication attempts for security monitoring"""
    try:
        # In a production environment, you might want to log to a file or database
        current_app.logger.info(
            f"Auth attempt: {email} ({user_type}) - {'SUCCESS' if success else 'FAILED'} from {ip_address}"
        )
    except Exception as e:
        current_app.logger.error(f"Failed to log auth attempt: {e}")


# ===================================
# AUTHENTICATION ROUTES
# ===================================


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """Unified login endpoint for all user types"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["email", "password"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        user_type = data.get("user_type", "auto")  # auto-detect if not specified

        # Validate email format
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        ip_address = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)

        # Try to authenticate based on user_type
        if user_type == "admin" or user_type == "auto":
            admin = Admin.query.filter_by(email=email).first()
            if admin and admin.check_password(password):
                if not admin.is_active:
                    log_auth_attempt(email, False, "admin", ip_address)
                    return jsonify({"error": "Account is deactivated"}), 401

                create_admin_session(admin)
                log_auth_attempt(email, True, "admin", ip_address)

                return (
                    jsonify(
                        {
                            "message": "Admin login successful",
                            "user_type": "admin",
                            "admin": admin.to_dict(),
                            "redirect_url": "/admin",
                        }
                    ),
                    200,
                )

        if user_type == "developer" or user_type == "auto":
            # Check for developer account (special admin role)
            dev_admin = Admin.query.filter_by(email=email, role="developer").first()
            if dev_admin and dev_admin.check_password(password):
                if not dev_admin.is_active:
                    log_auth_attempt(email, False, "developer", ip_address)
                    return jsonify({"error": "Account is deactivated"}), 401

                create_admin_session(dev_admin)
                log_auth_attempt(email, True, "developer", ip_address)

                return (
                    jsonify(
                        {
                            "message": "Developer login successful",
                            "user_type": "developer",
                            "admin": dev_admin.to_dict(),
                            "redirect_url": "/dev-dashboard",
                        }
                    ),
                    200,
                )

        # Try regular user authentication
        if user_type in ["customer", "provider", "auto"]:
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                if not user.is_active:
                    log_auth_attempt(email, False, user.user_type, ip_address)
                    return jsonify({"error": "Account is deactivated"}), 401

                create_user_session(user)
                log_auth_attempt(email, True, user.user_type, ip_address)

                # Get user profile
                profile = None
                if user.user_type == "customer":
                    profile = CustomerProfile.query.filter_by(user_id=user.id).first()
                elif user.user_type == "provider":
                    profile = ProviderProfile.query.filter_by(user_id=user.id).first()

                redirect_url = "/dashboard"
                if user.user_type == "provider":
                    redirect_url = "/provider-dashboard"

                return (
                    jsonify(
                        {
                            "message": "Login successful",
                            "user_type": user.user_type,
                            "user": user.to_dict(),
                            "profile": profile.to_dict() if profile else None,
                            "redirect_url": redirect_url,
                        }
                    ),
                    200,
                )

        # No valid authentication found
        log_auth_attempt(email, False, user_type, ip_address)
        return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return handle_error(e)


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("3 per minute")
def register():
    """Unified registration endpoint for customers and providers"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["email", "password", "first_name", "last_name", "user_type"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        user_type = data["user_type"]

        # Validate inputs
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        if not validate_password(password):
            return (
                jsonify({"error": "Password must be at least 8 characters long"}),
                400,
            )

        if user_type not in ["customer", "provider"]:
            return jsonify({"error": "Invalid user type"}), 400

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "Email already registered"}), 409

        # Check if admin exists with same email
        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            return jsonify({"error": "Email already registered"}), 409

        # Create new user
        user = User(
            email=email,
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
            user_type=user_type,
            phone=data.get("phone", "").strip(),
            street_address=data.get("street_address", "").strip(),
            city=data.get("city", "").strip(),
            state=data.get("state", "").strip(),
            postcode=data.get("postcode", "").strip(),
            is_active=True,
            is_verified=False,  # Email verification required
        )
        user.set_password(password)

        db.session.add(user)
        db.session.flush()  # Get user ID

        # Create user profile based on type
        if user_type == "customer":
            profile = CustomerProfile(
                user_id=user.id,
                preferred_contact_method=data.get("preferred_contact_method", "email"),
            )
        else:  # provider
            profile = ProviderProfile(
                user_id=user.id,
                business_name=data.get("business_name", "").strip(),
                abn=data.get("abn", "").strip(),
                years_experience=data.get("years_experience", 0),
                hourly_rate=data.get("hourly_rate", 0.0),
            )

        db.session.add(profile)
        db.session.commit()

        # Create session for new user
        create_user_session(user)

        current_app.logger.info(f"New {user_type} registered: {email}")

        return (
            jsonify(
                {
                    "message": "Registration successful",
                    "user_type": user_type,
                    "user": user.to_dict(),
                    "profile": profile.to_dict(),
                    "redirect_url": (
                        "/dashboard"
                        if user_type == "customer"
                        else "/provider-dashboard"
                    ),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {e}")
        return handle_error(e)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Unified logout endpoint"""
    try:
        user_id = session.get("user_id")
        admin_id = session.get("admin_id")

        if user_id:
            current_app.logger.info(f"User {user_id} logged out")
        elif admin_id:
            current_app.logger.info(f"Admin {admin_id} logged out")

        clear_session()

        return jsonify({"message": "Logout successful"}), 200

    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        return handle_error(e)


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user_info():
    """Get current authenticated user information"""
    try:
        # Check if it's an admin session
        admin = get_current_admin()
        if admin:
            return jsonify({"user_type": "admin", "admin": admin}), 200

        # Check if it's a user session
        user_data = get_current_user()
        if user_data:
            return (
                jsonify(
                    {
                        "user_type": user_data["user"]["user_type"],
                        "user": user_data["user"],
                        "profile": user_data["profile"],
                    }
                ),
                200,
            )

        return jsonify({"error": "No authenticated user found"}), 401

    except Exception as e:
        current_app.logger.error(f"Get current user error: {e}")
        return handle_error(e)


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Change password for authenticated user"""
    try:
        data = request.get_json()

        required_fields = ["current_password", "new_password"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        current_password = data["current_password"]
        new_password = data["new_password"]

        if not validate_password(new_password):
            return (
                jsonify({"error": "New password must be at least 8 characters long"}),
                400,
            )

        # Check if it's an admin
        if "admin_id" in session:
            admin = Admin.query.get(session["admin_id"])
            if not admin or not admin.check_password(current_password):
                return jsonify({"error": "Current password is incorrect"}), 400

            admin.set_password(new_password)
            db.session.commit()

            current_app.logger.info(f"Admin {admin.id} changed password")

        # Check if it's a user
        elif "user_id" in session:
            user = User.query.get(session["user_id"])
            if not user or not user.check_password(current_password):
                return jsonify({"error": "Current password is incorrect"}), 400

            user.set_password(new_password)
            db.session.commit()

            current_app.logger.info(f"User {user.id} changed password")

        else:
            return jsonify({"error": "No authenticated user found"}), 401

        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Change password error: {e}")
        return handle_error(e)


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    """Verify user email address"""
    try:
        data = request.get_json()

        required_fields = ["token"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        # In a real implementation, you would verify the token
        # For now, we'll just mark the current user as verified
        if "user_id" in session:
            user = User.query.get(session["user_id"])
            if user:
                user.is_verified = True
                user.email_verified_at = datetime.utcnow()
                db.session.commit()

                return jsonify({"message": "Email verified successfully"}), 200

        return jsonify({"error": "Invalid verification token"}), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Email verification error: {e}")
        return handle_error(e)


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("3 per hour")
def forgot_password():
    """Request password reset"""
    try:
        data = request.get_json()

        required_fields = ["email"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        email = data["email"].lower().strip()

        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        # Check if user exists (don't reveal if email exists or not)
        user = User.query.filter_by(email=email).first()
        admin = Admin.query.filter_by(email=email).first()

        if user or admin:
            # In a real implementation, you would send a password reset email
            current_app.logger.info(f"Password reset requested for: {email}")

        # Always return success to prevent email enumeration
        return (
            jsonify(
                {
                    "message": "If an account with that email exists, a password reset link has been sent"
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Forgot password error: {e}")
        return handle_error(e)


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()

        required_fields = ["token", "new_password"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        new_password = data["new_password"]

        if not validate_password(new_password):
            return (
                jsonify({"error": "Password must be at least 8 characters long"}),
                400,
            )

        # In a real implementation, you would verify the reset token
        # and update the user's password

        return jsonify({"message": "Password reset successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"Reset password error: {e}")
        return handle_error(e)


# ===================================
# ADMIN-SPECIFIC ROUTES
# ===================================


@auth_bp.route("/admin/users", methods=["GET"])
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        return jsonify({"users": [user.to_dict() for user in users]}), 200

    except Exception as e:
        current_app.logger.error(f"Get users error: {e}")
        return handle_error(e)


@auth_bp.route("/admin/users/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active
        db.session.commit()

        status = "activated" if user.is_active else "deactivated"
        current_app.logger.info(f"Admin {session['admin_id']} {status} user {user_id}")

        return (
            jsonify({"message": f"User {status} successfully", "user": user.to_dict()}),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle user status error: {e}")
        return handle_error(e)


# ===================================
# SESSION MANAGEMENT
# ===================================


@auth_bp.before_app_request
def load_logged_in_user():
    """Load user information into g for each request"""
    g.current_user = get_current_user()
    g.current_admin = get_current_admin()


@auth_bp.route("/session/check", methods=["GET"])
def check_session():
    """Check if session is valid"""
    try:
        if "user_id" in session or "admin_id" in session:
            # Check session timeout (24 hours)
            logged_in_at = session.get("logged_in_at", 0)
            if time.time() - logged_in_at > 86400:  # 24 hours
                clear_session()
                return jsonify({"valid": False, "reason": "Session expired"}), 401

            return jsonify({"valid": True}), 200

        return jsonify({"valid": False, "reason": "No active session"}), 401

    except Exception as e:
        current_app.logger.error(f"Session check error: {e}")
        return jsonify({"valid": False, "reason": "Session error"}), 500
