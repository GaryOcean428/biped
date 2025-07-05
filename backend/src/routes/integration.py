"""
Cross-Service Integration API
Provides endpoints for ReactCRM and Email Service integration
"""

import os

import requests
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

from src.models import CustomerProfile, ProviderProfile, User, db
from src.utils.rate_limiting import limiter
from src.utils.validation import validate_email

integration_bp = Blueprint("integration", __name__, url_prefix="/api/integration")

# Service URLs from environment
REACTCRM_URL = os.environ.get(
    "REACTCRM_URL", "https://reactcrm-production.up.railway.app"
)
EMAIL_SERVICE_URL = os.environ.get(
    "EMAIL_SERVICE_URL", "https://email-service.up.railway.app"
)


@integration_bp.route("/health", methods=["GET"])
def integration_health():
    """Health check for integration services"""
    return jsonify(
        {
            "status": "healthy",
            "services": {
                "biped": "active",
                "reactcrm": REACTCRM_URL,
                "email_service": EMAIL_SERVICE_URL,
            },
        }
    )


@integration_bp.route("/sync-user", methods=["POST"])
@limiter.limit("10 per minute")
@cross_origin()
def sync_user_to_crm():
    """Sync user data to ReactCRM"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id required"}), 400

        # Get user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Prepare user data for CRM
        crm_data = {
            "id": user.id,
            "email": user.email,
            "user_type": user.user_type,
            "created_at": user.created_at.isoformat(),
            "is_active": user.is_active,
        }

        # Add profile data based on user type
        if user.user_type == "customer":
            profile = CustomerProfile.query.filter_by(user_id=user.id).first()
            if profile:
                crm_data.update(
                    {
                        "first_name": profile.first_name,
                        "last_name": profile.last_name,
                        "phone": profile.phone,
                        "address": profile.address,
                    }
                )
        elif user.user_type == "provider":
            profile = ProviderProfile.query.filter_by(user_id=user.id).first()
            if profile:
                crm_data.update(
                    {
                        "business_name": profile.business_name,
                        "phone": profile.phone,
                        "address": profile.address,
                        "services": profile.services,
                    }
                )

        # Send to ReactCRM
        try:
            response = requests.post(
                f"{REACTCRM_URL}/api/users/sync", json=crm_data, timeout=10
            )

            if response.status_code == 200:
                return jsonify({"status": "synced", "crm_response": response.json()})
            else:
                return (
                    jsonify(
                        {"error": "CRM sync failed", "status": response.status_code}
                    ),
                    500,
                )

        except requests.RequestException as e:
            return jsonify({"error": f"CRM connection failed: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integration_bp.route("/send-email", methods=["POST"])
@limiter.limit("20 per minute")
@cross_origin()
def send_email():
    """Send email via Email Service"""
    try:
        data = request.get_json()

        required_fields = ["to", "subject", "template"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        # Validate email
        if not validate_email(data["to"]):
            return jsonify({"error": "Invalid email address"}), 400

        # Prepare email data
        email_data = {
            "to": data["to"],
            "subject": data["subject"],
            "template": data["template"],
            "data": data.get("data", {}),
            "from_service": "biped",
        }

        # Send to Email Service
        try:
            response = requests.post(
                f"{EMAIL_SERVICE_URL}/api/send", json=email_data, timeout=15
            )

            if response.status_code == 200:
                return jsonify({"status": "sent", "email_response": response.json()})
            else:
                return (
                    jsonify(
                        {"error": "Email send failed", "status": response.status_code}
                    ),
                    500,
                )

        except requests.RequestException as e:
            return jsonify({"error": f"Email service connection failed: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integration_bp.route("/webhook/crm", methods=["POST"])
@cross_origin()
def crm_webhook():
    """Receive webhooks from ReactCRM"""
    try:
        data = request.get_json()
        event_type = data.get("event")

        if event_type == "user_updated":
            # Handle user update from CRM
            user_data = data.get("user")
            user = User.query.get(user_data.get("id"))

            if user:
                # Update user data from CRM
                if "email" in user_data:
                    user.email = user_data["email"]
                if "is_active" in user_data:
                    user.is_active = user_data["is_active"]

                db.session.commit()
                return jsonify({"status": "updated"})
            else:
                return jsonify({"error": "User not found"}), 404

        elif event_type == "lead_created":
            # Handle new lead from CRM
            lead_data = data.get("lead")

            # Create customer profile for lead
            user = User(email=lead_data["email"], user_type="customer", is_active=True)
            db.session.add(user)
            db.session.flush()

            profile = CustomerProfile(
                user_id=user.id,
                first_name=lead_data.get("first_name", ""),
                last_name=lead_data.get("last_name", ""),
                phone=lead_data.get("phone", ""),
                address=lead_data.get("address", ""),
            )
            db.session.add(profile)
            db.session.commit()

            return jsonify({"status": "lead_created", "user_id": user.id})

        return jsonify({"status": "processed"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integration_bp.route("/stats", methods=["GET"])
@cross_origin()
def integration_stats():
    """Get integration statistics"""
    try:
        stats = {
            "total_users": User.query.count(),
            "customers": User.query.filter_by(user_type="customer").count(),
            "providers": User.query.filter_by(user_type="provider").count(),
            "active_users": User.query.filter_by(is_active=True).count(),
            "services_connected": {
                "reactcrm": REACTCRM_URL,
                "email_service": EMAIL_SERVICE_URL,
            },
        }

        return jsonify(stats)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
