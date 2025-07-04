"""
User Management Routes
======================

This module provides comprehensive user management endpoints that work
with the UserService layer to handle all user operations.
"""

from flask import Blueprint, jsonify, request, session
from src.routes.unified_auth import admin_required, login_required, role_required
from src.services.user_service import RoleBasedAccessControl, UserService
from src.utils.error_handling import handle_error
from src.utils.rate_limiting import limiter
from src.utils.validation import validate_required_fields

# Create blueprint
user_mgmt_bp = Blueprint("user_management", __name__, url_prefix="/api/users")

# ===================================
# USER PROFILE ROUTES
# ===================================


@user_mgmt_bp.route("/profile", methods=["GET"])
@login_required
def get_profile():
    """Get current user's profile"""
    try:
        user_id = session.get("user_id") or session.get("admin_id")
        user_type = "admin" if "admin_id" in session else "user"

        user_data = UserService.get_user_by_id(user_id, user_type)
        if not user_data:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user_data), 200

    except Exception as e:
        return handle_error(e)


@user_mgmt_bp.route("/profile", methods=["PUT"])
@login_required
@limiter.limit("10 per minute")
def update_profile():
    """Update current user's profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_id = session.get("user_id") or session.get("admin_id")
        user_type = "admin" if "admin_id" in session else "user"

        updated_user = UserService.update_user_profile(user_id, data, user_type)

        return (
            jsonify({"message": "Profile updated successfully", "user": updated_user}),
            200,
        )

    except Exception as e:
        return handle_error(e)


@user_mgmt_bp.route("/settings", methods=["PUT"])
@login_required
@limiter.limit("10 per minute")
def update_settings():
    """Update user settings and preferences"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_id = session.get("user_id") or session.get("admin_id")
        user_type = "admin" if "admin_id" in session else "user"

        # Extract settings-specific data
        settings_data = {}
        if "language" in data:
            settings_data["language"] = data["language"]
        if "timezone" in data:
            settings_data["timezone"] = data["timezone"]
        if "notification_preferences" in data:
            settings_data["notification_preferences"] = data["notification_preferences"]

        updated_user = UserService.update_user_profile(
            user_id, settings_data, user_type
        )

        return (
            jsonify({"message": "Settings updated successfully", "user": updated_user}),
            200,
        )

    except Exception as e:
        return handle_error(e)


@user_mgmt_bp.route("/notifications", methods=["PUT"])
@login_required
@limiter.limit("10 per minute")
def update_notifications():
    """Update notification preferences"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_id = session.get("user_id") or session.get("admin_id")
        user_type = "admin" if "admin_id" in session else "user"

        # Update notification preferences
        notification_data = {"notification_preferences": data}

        updated_user = UserService.update_user_profile(
            user_id, notification_data, user_type
        )

        return (
            jsonify(
                {
                    "message": "Notification preferences updated successfully",
                    "user": updated_user,
                }
            ),
            200,
        )

    except Exception as e:
        return handle_error(e)


# ===================================
# DASHBOARD ROUTES
# ===================================


@user_mgmt_bp.route("/dashboard", methods=["GET"])
@login_required
def get_dashboard_data():
    """Get dashboard data for current user"""
    try:
        user_id = session.get("user_id") or session.get("admin_id")
        user_type = "admin" if "admin_id" in session else "user"

        dashboard_data = UserService.get_user_dashboard_data(user_id, user_type)

        return jsonify(dashboard_data), 200

    except Exception as e:
        return handle_error(e)


# ===================================
# ADMIN USER MANAGEMENT ROUTES
# ===================================


@user_mgmt_bp.route("/list", methods=["GET"])
@admin_required
def get_users_list():
    """Get paginated list of users (admin only)"""
    try:
        # Get query parameters
        page = request.args.get("page", 1, type=int)
        per_page = min(
            request.args.get("per_page", 20, type=int), 100
        )  # Max 100 per page

        # Build filters
        filters = {}
        if request.args.get("user_type"):
            filters["user_type"] = request.args.get("user_type")
        if request.args.get("is_active") is not None:
            filters["is_active"] = request.args.get("is_active").lower() == "true"
        if request.args.get("search"):
            filters["search"] = request.args.get("search")

        users_data = UserService.get_users_list(filters, page, per_page)

        return jsonify(users_data), 200

    except Exception as e:
        return handle_error(e)


@user_mgmt_bp.route("/<int:user_id>", methods=["GET"])
@admin_required
def get_user_by_id(user_id):
    """Get specific user by ID (admin only)"""
    try:
        user_data = UserService.get_user_by_id(user_id)
        if not user_data:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user_data), 200

    except Exception as e:
        return handle_error(e)


@user_mgmt_bp.route("/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status (admin only)"""
    try:
        admin_id = session.get("admin_id")
        result = UserService.toggle_user_status(user_id, admin_id)

        return (
            jsonify(
                {
                    "message": f'User {result["status"]} successfully',
                    "user": result["user"],
                }
            ),
            200,
        )

    except Exception as e:
        return handle_error(e)


@user_mgmt_bp.route("/<int:user_id>/profile", methods=["PUT"])
@admin_required
def update_user_profile_admin(user_id):
    """Update user profile (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        updated_user = UserService.update_user_profile(user_id, data)

        return (
            jsonify(
                {"message": "User profile updated successfully", "user": updated_user}
            ),
            200,
        )

    except Exception as e:
        return handle_error(e)


# ===================================
# USER TYPE SPECIFIC ROUTES
# ===================================


@user_mgmt_bp.route("/providers", methods=["GET"])
@role_required(["admin", "customer"])
def get_providers():
    """Get list of providers"""
    try:
        filters = {"user_type": "provider", "is_active": True}

        # Add search if provided
        if request.args.get("search"):
            filters["search"] = request.args.get("search")

        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 50)

        providers_data = UserService.get_users_list(filters, page, per_page)

        return jsonify(providers_data), 200

    except Exception as e:
        return handle_error(e)


@user_mgmt_bp.route("/customers", methods=["GET"])
@role_required(["admin", "provider"])
def get_customers():
    """Get list of customers"""
    try:
        filters = {"user_type": "customer", "is_active": True}

        # Add search if provided
        if request.args.get("search"):
            filters["search"] = request.args.get("search")

        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 50)

        customers_data = UserService.get_users_list(filters, page, per_page)

        return jsonify(customers_data), 200

    except Exception as e:
        return handle_error(e)


# ===================================
# PERMISSIONS AND ROLES
# ===================================


@user_mgmt_bp.route("/permissions", methods=["GET"])
@login_required
def get_user_permissions():
    """Get current user's permissions"""
    try:
        user_type = session.get("user_type", "customer")
        if "admin_id" in session:
            admin_id = session.get("admin_id")
            admin_data = UserService.get_user_by_id(admin_id, "admin")
            if admin_data and admin_data["user"]["role"] == "developer":
                user_type = "developer"
            else:
                user_type = "admin"

        permissions = RoleBasedAccessControl.get_user_permissions(user_type)

        return jsonify({"user_type": user_type, "permissions": permissions}), 200

    except Exception as e:
        return handle_error(e)


@user_mgmt_bp.route("/check-permission", methods=["POST"])
@login_required
def check_permission():
    """Check if current user has specific permission"""
    try:
        data = request.get_json()

        required_fields = ["permission"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        user_type = session.get("user_type", "customer")
        if "admin_id" in session:
            admin_id = session.get("admin_id")
            admin_data = UserService.get_user_by_id(admin_id, "admin")
            if admin_data and admin_data["user"]["role"] == "developer":
                user_type = "developer"
            else:
                user_type = "admin"

        has_permission = RoleBasedAccessControl.has_permission(
            user_type, data["permission"]
        )

        return (
            jsonify(
                {
                    "has_permission": has_permission,
                    "user_type": user_type,
                    "permission": data["permission"],
                }
            ),
            200,
        )

    except Exception as e:
        return handle_error(e)


# ===================================
# EMAIL VERIFICATION
# ===================================


@user_mgmt_bp.route("/verify-email", methods=["POST"])
@login_required
def verify_email():
    """Verify user email"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User authentication required"}), 401

        success = UserService.verify_user_email(user_id)

        if success:
            return jsonify({"message": "Email verified successfully"}), 200
        else:
            return jsonify({"error": "Email verification failed"}), 400

    except Exception as e:
        return handle_error(e)


# ===================================
# USER STATISTICS (ADMIN)
# ===================================


@user_mgmt_bp.route("/statistics", methods=["GET"])
@admin_required
def get_user_statistics():
    """Get user statistics (admin only)"""
    try:
        from sqlalchemy import func
        from src.models.user import User

        # Get basic counts
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        verified_users = User.query.filter_by(is_verified=True).count()

        # Get counts by user type
        user_type_counts = (
            db.session.query(User.user_type, func.count(User.id).label("count"))
            .group_by(User.user_type)
            .all()
        )

        # Get recent registrations (last 30 days)
        from datetime import datetime, timedelta

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = User.query.filter(
            User.created_at >= thirty_days_ago
        ).count()

        statistics = {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "recent_registrations": recent_registrations,
            "user_types": {row.user_type: row.count for row in user_type_counts},
        }

        return jsonify(statistics), 200

    except Exception as e:
        return handle_error(e)


# ===================================
# BULK OPERATIONS (ADMIN)
# ===================================


@user_mgmt_bp.route("/bulk-update", methods=["POST"])
@admin_required
@limiter.limit("5 per minute")
def bulk_update_users():
    """Bulk update users (admin only)"""
    try:
        data = request.get_json()

        required_fields = ["user_ids", "action"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        user_ids = data["user_ids"]
        action = data["action"]
        admin_id = session.get("admin_id")

        if not isinstance(user_ids, list) or not user_ids:
            return jsonify({"error": "user_ids must be a non-empty list"}), 400

        results = []

        if action == "activate":
            for user_id in user_ids:
                try:
                    result = UserService.toggle_user_status(user_id, admin_id)
                    if result["user"]["is_active"]:
                        results.append({"user_id": user_id, "status": "activated"})
                    else:
                        # If user was already active, toggle again to keep them active
                        UserService.toggle_user_status(user_id, admin_id)
                        results.append({"user_id": user_id, "status": "already_active"})
                except Exception as e:
                    results.append(
                        {"user_id": user_id, "status": "error", "error": str(e)}
                    )

        elif action == "deactivate":
            for user_id in user_ids:
                try:
                    result = UserService.toggle_user_status(user_id, admin_id)
                    if not result["user"]["is_active"]:
                        results.append({"user_id": user_id, "status": "deactivated"})
                    else:
                        # If user was already inactive, toggle again to keep them inactive
                        UserService.toggle_user_status(user_id, admin_id)
                        results.append(
                            {"user_id": user_id, "status": "already_inactive"}
                        )
                except Exception as e:
                    results.append(
                        {"user_id": user_id, "status": "error", "error": str(e)}
                    )

        else:
            return (
                jsonify(
                    {"error": "Invalid action. Supported actions: activate, deactivate"}
                ),
                400,
            )

        return jsonify({"message": f"Bulk {action} completed", "results": results}), 200

    except Exception as e:
        return handle_error(e)
