import logging

from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.routes.admin_auth import require_admin_auth
from src.services.email_client import enhanced_notification_service

logger = logging.getLogger(__name__)

communication_bp = Blueprint("communication", __name__)


@communication_bp.route("/send-email", methods=["POST"])
@require_admin_auth
def send_email():
    """Send custom email (admin only)"""
    try:
        data = request.get_json()
        to_emails = data.get("to_emails", [])
        subject = data.get("subject", "")
        html_content = data.get("html_content", "")
        text_content = data.get("text_content")

        if not to_emails or not subject or not html_content:
            return jsonify({"error": "Missing required fields"}), 400

        success = enhanced_notification_service.email_client.send_email(
            to_emails, subject, html_content, text_content
        )

        if success:
            return jsonify({"message": "Email sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send email"}), 500

    except Exception as e:
        logger.error(f"Email sending error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/send-sms", methods=["POST"])
@require_admin_auth
def send_sms():
    """Send custom SMS (admin only)"""
    try:
        data = request.get_json()
        to_phone = data.get("to_phone", "")
        message = data.get("message", "")

        if not to_phone or not message:
            return jsonify({"error": "Missing required fields"}), 400

        success = enhanced_notification_service.send_sms_notification(to_phone, message)

        if success:
            return jsonify({"message": "SMS sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send SMS"}), 500

    except Exception as e:
        logger.error(f"SMS sending error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/send-welcome-email", methods=["POST"])
def send_welcome_email():
    """Send welcome email to new user"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID required"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        success = enhanced_notification_service.send_welcome_email(user.email, user.get_full_name())

        if success:
            return jsonify({"message": "Welcome email sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send welcome email"}), 500

    except Exception as e:
        logger.error(f"Welcome email error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/send-job-notification", methods=["POST"])
def send_job_notification():
    """Send job notification to providers"""
    try:
        data = request.get_json()
        provider_id = data.get("provider_id")
        job_title = data.get("job_title", "")
        job_id = data.get("job_id", "")

        if not provider_id or not job_title or not job_id:
            return jsonify({"error": "Missing required fields"}), 400

        provider = User.query.get(provider_id)
        if not provider:
            return jsonify({"error": "Provider not found"}), 404

        success = enhanced_notification_service.send_job_notification(
            provider.email, provider.get_full_name(), job_title, job_id
        )

        if success:
            return jsonify({"message": "Job notification sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send job notification"}), 500

    except Exception as e:
        logger.error(f"Job notification error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/send-quote-notification", methods=["POST"])
def send_quote_notification():
    """Send quote notification to customer"""
    try:
        data = request.get_json()
        customer_id = data.get("customer_id")
        provider_name = data.get("provider_name", "")
        job_title = data.get("job_title", "")
        quote_amount = data.get("quote_amount", 0)

        if not customer_id or not provider_name or not job_title:
            return jsonify({"error": "Missing required fields"}), 400

        customer = User.query.get(customer_id)
        if not customer:
            return jsonify({"error": "Customer not found"}), 404

        success = enhanced_notification_service.send_quote_notification(
            customer.email, customer.get_full_name(), provider_name, job_title, quote_amount
        )

        if success:
            return jsonify({"message": "Quote notification sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send quote notification"}), 500

    except Exception as e:
        logger.error(f"Quote notification error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/send-payment-confirmation", methods=["POST"])
def send_payment_confirmation():
    """Send payment confirmation email"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        amount = data.get("amount", 0)
        job_title = data.get("job_title", "")

        if not user_id or not amount or not job_title:
            return jsonify({"error": "Missing required fields"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        success = enhanced_notification_service.send_payment_confirmation_email(
            user.email, user.get_full_name(), amount, job_title
        )

        if success:
            return jsonify({"message": "Payment confirmation sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send payment confirmation"}), 500

    except Exception as e:
        logger.error(f"Payment confirmation error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/test-email", methods=["POST"])
@require_admin_auth
def test_email():
    """Test email configuration (admin only)"""
    try:
        data = request.get_json()
        test_email = data.get("test_email", "test@example.com")

        success = enhanced_notification_service.email_client.send_email(
            [test_email],
            "Biped Email Test",
            "<h1>Email Test Successful!</h1><p>Your email configuration is working correctly.</p>",
            "Email Test Successful! Your email configuration is working correctly.",
        )

        if success:
            return jsonify({"message": "Test email sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send test email"}), 500

    except Exception as e:
        logger.error(f"Test email error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/test-sms", methods=["POST"])
@require_admin_auth
def test_sms():
    """Test SMS configuration (admin only)"""
    try:
        data = request.get_json()
        test_phone = data.get("test_phone", "+1234567890")

        success = enhanced_notification_service.send_sms_notification(
            test_phone, "Biped SMS Test: Your SMS configuration is working correctly!"
        )

        if success:
            return jsonify({"message": "Test SMS sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send test SMS"}), 500

    except Exception as e:
        logger.error(f"Test SMS error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/config", methods=["GET"])
@require_admin_auth
def get_communication_config():
    """Get communication service configuration status (admin only)"""
    try:
        import os

        # Get email service status
        email_status = enhanced_notification_service.test_email_service()

        config_status = {
            "email": {
                "service_type": email_status["service_type"],
                "connected": email_status["connected"],
                "provider": email_status.get("provider", "unknown"),
                "url": email_status.get("url", "N/A"),
                "from_email": os.getenv("FROM_EMAIL", "noreply@biped.com"),
            },
            "sms": {
                "provider": os.getenv("SMS_PROVIDER", "twilio"),
                "configured": bool(
                    os.getenv("TWILIO_ACCOUNT_SID")
                    and os.getenv("TWILIO_AUTH_TOKEN")
                    and os.getenv("TWILIO_PHONE_NUMBER")
                ),
            },
        }

        return jsonify({"config": config_status}), 200

    except Exception as e:
        logger.error(f"Config retrieval error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/update-config", methods=["POST"])
@require_admin_auth
def update_communication_config():
    """Update communication service configuration (admin only)"""
    try:
        data = request.get_json()

        # Note: In production, these should be stored securely (e.g., environment variables, secrets manager)
        # This is a simplified implementation for demonstration

        config_updates = []

        if "email" in data:
            email_config = data["email"]
            if "sendgrid_api_key" in email_config:
                os.environ["SENDGRID_API_KEY"] = email_config["sendgrid_api_key"]
                config_updates.append("SendGrid API key")

            if "smtp_username" in email_config:
                os.environ["SMTP_USERNAME"] = email_config["smtp_username"]
                config_updates.append("SMTP username")

            if "smtp_password" in email_config:
                os.environ["SMTP_PASSWORD"] = email_config["smtp_password"]
                config_updates.append("SMTP password")

        if "sms" in data:
            sms_config = data["sms"]
            if "twilio_account_sid" in sms_config:
                os.environ["TWILIO_ACCOUNT_SID"] = sms_config["twilio_account_sid"]
                config_updates.append("Twilio Account SID")

            if "twilio_auth_token" in sms_config:
                os.environ["TWILIO_AUTH_TOKEN"] = sms_config["twilio_auth_token"]
                config_updates.append("Twilio Auth Token")

            if "twilio_phone_number" in sms_config:
                os.environ["TWILIO_PHONE_NUMBER"] = sms_config["twilio_phone_number"]
                config_updates.append("Twilio Phone Number")

        return (
            jsonify({"message": "Configuration updated successfully", "updated": config_updates}),
            200,
        )

    except Exception as e:
        logger.error(f"Config update error: {str(e)}")
        return jsonify({"error": str(e)}), 500
