import os
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from werkzeug.security import check_password_hash

dev_auth_bp = Blueprint("dev_auth", __name__)

# Developer credentials - these should be configurable
DEV_EMAIL = os.environ.get("DEV_EMAIL", "dev@biped.app")
DEV_ACCESS_KEY = os.environ.get("DEV_ACCESS_KEY", "dev_biped_2025")


@dev_auth_bp.route("/dev-login", methods=["POST"])
def dev_login():
    """Developer login endpoint for platform developers"""
    try:
        data = request.get_json()
        email = data.get("email", "").lower().strip()
        password = data.get("password", "")
        access_key = data.get("access_key", "")

        if not email or not password or not access_key:
            return jsonify({"error": "Email, password, and access key are required"}), 400

        # Check if this is the developer email
        if email != DEV_EMAIL:
            return jsonify({"error": "Unauthorized access"}), 403

        # Check if the access key is valid
        if access_key != DEV_ACCESS_KEY:
            return jsonify({"error": "Invalid developer access key"}), 403

        # Find the user in the database
        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"error": "Developer account not found"}), 404

        # Verify password
        if not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Create developer session
        session["dev_user_id"] = user.id
        session["dev_email"] = user.email
        session["is_developer"] = True
        session["dev_login_time"] = datetime.utcnow().isoformat()
        session.permanent = True  # Developer sessions are longer

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Developer login successful",
                    "developer": {
                        "id": user.id,
                        "email": user.email,
                        "name": user.get_full_name(),
                        "login_time": session["dev_login_time"],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dev_auth_bp.route("/dev-logout", methods=["POST"])
def dev_logout():
    """Developer logout endpoint"""
    try:
        # Clear developer session
        session.pop("dev_user_id", None)
        session.pop("dev_email", None)
        session.pop("is_developer", None)
        session.pop("dev_login_time", None)

        return jsonify({"message": "Developer logout successful"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dev_auth_bp.route("/dev-me", methods=["GET"])
def dev_me():
    """Get current developer user info"""
    try:
        dev_user_id = session.get("dev_user_id")
        is_developer = session.get("is_developer", False)

        if not dev_user_id or not is_developer:
            return jsonify({"error": "Not authenticated as developer"}), 401

        user = User.query.get(dev_user_id)
        if not user or user.email != DEV_EMAIL:
            return jsonify({"error": "Developer user not found"}), 404

        return (
            jsonify(
                {
                    "developer": {
                        "id": user.id,
                        "email": user.email,
                        "name": user.get_full_name(),
                        "login_time": session.get("dev_login_time"),
                        "access_level": "full",
                    }
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def require_dev_auth(f):
    """Decorator to require developer authentication"""

    def decorated_function(*args, **kwargs):
        dev_user_id = session.get("dev_user_id")
        is_developer = session.get("is_developer", False)

        if not dev_user_id or not is_developer:
            return jsonify({"error": "Developer authentication required"}), 401

        # Verify developer user still exists and is valid
        user = User.query.get(dev_user_id)
        if not user or user.email != DEV_EMAIL:
            return jsonify({"error": "Invalid developer session"}), 401

        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function

