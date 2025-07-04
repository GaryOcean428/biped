import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, jsonify, request, session

from ..models.admin import Admin, AdminAction, db
from ..models.job import Job
from ..models.review import Review
from ..models.service import Service, ServiceCategory
from ..models.user import CustomerProfile, ProviderProfile, User

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorator to require admin authentication"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session for admin token
        admin_token = session.get("admin_token")
        if not admin_token:
            return jsonify({"error": "Admin authentication required"}), 401

        # Find admin by session token
        admin = Admin.query.filter_by(session_token=admin_token).first()
        if not admin or not admin.is_session_valid() or not admin.is_active:
            session.pop("admin_token", None)
            return jsonify({"error": "Invalid or expired admin session"}), 401

        # Check if account is locked
        if admin.is_locked():
            return jsonify({"error": "Admin account is locked"}), 403

        # Add admin to request context
        request.current_admin = admin
        return f(*args, **kwargs)

    return decorated_function


def permission_required(permission):
    """Decorator to require specific admin permission"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            admin = getattr(request, "current_admin", None)
            if not admin or not admin.has_permission(permission):
                return jsonify({"error": f"Permission required: {permission}"}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_admin_action(action, target_type=None, target_id=None, details=None):
    """Log admin action for audit trail"""
    try:
        admin = getattr(request, "current_admin", None)
        if admin:
            admin_action = AdminAction(
                admin_id=admin.id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent", "")[:500],
            )
            db.session.add(admin_action)
            db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")


# Authentication Routes
@admin_bp.route("/login", methods=["POST"])
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        # Find admin by username or email
        admin = Admin.query.filter(
            (Admin.username == username) | (Admin.email == username)
        ).first()

        if not admin:
            return jsonify({"error": "Invalid credentials"}), 401

        # Check if account is locked
        if admin.is_locked():
            return (
                jsonify({"error": "Account is locked due to too many failed attempts"}),
                403,
            )

        # Check if account is active
        if not admin.is_active:
            return jsonify({"error": "Account is deactivated"}), 403

        # Verify password
        if not admin.check_password(password):
            admin.increment_login_attempts()
            db.session.commit()
            return jsonify({"error": "Invalid credentials"}), 401

        # Successful login
        admin.reset_login_attempts()
        token = admin.generate_session_token()
        db.session.commit()

        # Store token in session
        session["admin_token"] = token
        session.permanent = True

        # Log login action
        log_admin_action("admin_login")

        return (
            jsonify(
                {
                    "message": "Login successful",
                    "admin": admin.to_dict(),
                    "token": token,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return jsonify({"error": "Login failed"}), 500


@admin_bp.route("/logout", methods=["POST"])
@admin_required
def admin_logout():
    """Admin logout endpoint"""
    try:
        admin = request.current_admin
        admin.clear_session()
        db.session.commit()

        # Clear session
        session.pop("admin_token", None)

        # Log logout action
        log_admin_action("admin_logout")

        return jsonify({"message": "Logout successful"}), 200

    except Exception as e:
        logger.error(f"Admin logout error: {e}")
        return jsonify({"error": "Logout failed"}), 500


@admin_bp.route("/me", methods=["GET"])
@admin_required
def get_admin_profile():
    """Get current admin profile"""
    try:
        admin = request.current_admin
        return jsonify({"admin": admin.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get admin profile error: {e}")
        return jsonify({"error": "Failed to get profile"}), 500


# User Management Routes
@admin_bp.route("/users", methods=["GET"])
@admin_required
@permission_required("user_management")
def get_users():
    """Get all users with pagination and filtering"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        user_type = request.args.get("user_type")
        search = request.args.get("search")

        query = User.query

        # Apply filters
        if user_type:
            query = query.filter(User.user_type == user_type)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.first_name.ilike(search_term))
                | (User.last_name.ilike(search_term))
                | (User.email.ilike(search_term))
            )

        # Paginate results
        users = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "users": [user.to_dict() for user in users.items],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": users.total,
                        "pages": users.pages,
                        "has_next": users.has_next,
                        "has_prev": users.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({"error": "Failed to get users"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
@permission_required("user_management")
def get_user(user_id):
    """Get specific user details"""
    try:
        user = User.query.get_or_404(user_id)

        user_data = user.to_dict()

        # Add profile data
        if user.user_type == "customer" and user.customer_profile:
            user_data["profile"] = user.customer_profile.to_dict()
        elif user.user_type == "provider" and user.provider_profile:
            user_data["profile"] = user.provider_profile.to_dict()

        return jsonify({"user": user_data}), 200

    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({"error": "Failed to get user"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
@permission_required("user_management")
def update_user(user_id):
    """Update user details"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()

        # Update allowed fields
        allowed_fields = [
            "first_name",
            "last_name",
            "phone",
            "is_verified",
            "is_active",
        ]
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])

        user.updated_at = datetime.utcnow()
        db.session.commit()

        # Log action
        log_admin_action("user_updated", "user", user_id, data)

        return (
            jsonify({"message": "User updated successfully", "user": user.to_dict()}),
            200,
        )

    except Exception as e:
        logger.error(f"Update user error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update user"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
@permission_required("user_management")
def delete_user(user_id):
    """Delete user account"""
    try:
        user = User.query.get_or_404(user_id)

        # Store user data for logging
        user_data = user.to_dict()

        db.session.delete(user)
        db.session.commit()

        # Log action
        log_admin_action("user_deleted", "user", user_id, user_data)

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Delete user error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete user"}), 500


# Service Management Routes
@admin_bp.route("/services", methods=["GET"])
@admin_required
@permission_required("service_management")
def get_services():
    """Get all services and categories"""
    try:
        categories = ServiceCategory.query.all()
        services = Service.query.all()

        return (
            jsonify(
                {
                    "categories": [cat.to_dict() for cat in categories],
                    "services": [service.to_dict() for service in services],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get services error: {e}")
        return jsonify({"error": "Failed to get services"}), 500


@admin_bp.route("/services", methods=["POST"])
@admin_required
@permission_required("service_management")
def create_service():
    """Create new service"""
    try:
        data = request.get_json()

        service = Service(
            name=data["name"],
            category_id=data["category_id"],
            description=data.get("description"),
            base_price=data.get("base_price"),
            price_unit=data.get("price_unit", "fixed"),
            is_active=data.get("is_active", True),
        )

        db.session.add(service)
        db.session.commit()

        # Log action
        log_admin_action("service_created", "service", service.id, data)

        return (
            jsonify(
                {
                    "message": "Service created successfully",
                    "service": service.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Create service error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create service"}), 500


# Job Management Routes
@admin_bp.route("/jobs", methods=["GET"])
@admin_required
@permission_required("job_management")
def get_jobs():
    """Get all jobs with pagination and filtering"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")

        query = Job.query

        if status:
            query = query.filter(Job.status == status)

        jobs = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "jobs": [job.to_dict() for job in jobs.items],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": jobs.total,
                        "pages": jobs.pages,
                        "has_next": jobs.has_next,
                        "has_prev": jobs.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get jobs error: {e}")
        return jsonify({"error": "Failed to get jobs"}), 500


# Analytics Routes
@admin_bp.route("/analytics/dashboard", methods=["GET"])
@admin_required
@permission_required("analytics")
def get_dashboard_analytics():
    """Get dashboard analytics data"""
    try:
        # Get basic counts
        total_users = User.query.count()
        total_customers = User.query.filter_by(user_type="customer").count()
        total_providers = User.query.filter_by(user_type="provider").count()
        total_jobs = Job.query.count()
        total_services = Service.query.count()

        # Get recent activity
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()

        return (
            jsonify(
                {
                    "totals": {
                        "users": total_users,
                        "customers": total_customers,
                        "providers": total_providers,
                        "jobs": total_jobs,
                        "services": total_services,
                    },
                    "recent_activity": {
                        "users": [user.to_dict() for user in recent_users],
                        "jobs": [job.to_dict() for job in recent_jobs],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get analytics error: {e}")
        return jsonify({"error": "Failed to get analytics"}), 500


# Admin Management Routes (Super Admin only)
@admin_bp.route("/admins", methods=["GET"])
@admin_required
@permission_required("admin_management")
def get_admins():
    """Get all admin users"""
    try:
        admins = Admin.query.all()
        return jsonify({"admins": [admin.to_dict() for admin in admins]}), 200

    except Exception as e:
        logger.error(f"Get admins error: {e}")
        return jsonify({"error": "Failed to get admins"}), 500


@admin_bp.route("/admins", methods=["POST"])
@admin_required
@permission_required("admin_management")
def create_admin():
    """Create new admin user"""
    try:
        data = request.get_json()

        # Check if username or email already exists
        existing = Admin.query.filter(
            (Admin.username == data["username"]) | (Admin.email == data["email"])
        ).first()

        if existing:
            return jsonify({"error": "Username or email already exists"}), 400

        admin = Admin(
            username=data["username"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role=data.get("role", "admin"),
            is_super_admin=data.get("is_super_admin", False),
            created_by=request.current_admin.id,
        )

        admin.set_password(data["password"])
        admin.permissions = admin.get_default_permissions()

        db.session.add(admin)
        db.session.commit()

        # Log action
        log_admin_action(
            "admin_created",
            "admin",
            admin.id,
            {"username": admin.username, "email": admin.email, "role": admin.role},
        )

        return (
            jsonify(
                {"message": "Admin created successfully", "admin": admin.to_dict()}
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Create admin error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create admin"}), 500


# Health check for admin API
@admin_bp.route("/health", methods=["GET"])
def admin_health():
    """Admin API health check"""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "TradeHub Admin API",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
        200,
    )
