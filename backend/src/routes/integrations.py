"""
Integration Routes for N8N and Flowise Connectivity
Connects Biped platform with anythingllm project automation
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from functools import wraps

import requests
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from src.models.financial import PlatformRevenue
from src.models.user import User, db

integrations_bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")

# Configuration for anythingllm project services
ANYTHINGLLM_BASE_URL = "https://anythingllm.up.railway.app"
N8N_WEBHOOK_BASE = f"{ANYTHINGLLM_BASE_URL}/webhook"
FLOWISE_API_BASE = f"{ANYTHINGLLM_BASE_URL}/api/v1/prediction"

# Webhook security (you should set this as an environment variable)
WEBHOOK_SECRET = "biped-webhook-secret-2025"


def verify_webhook_signature(f):
    """Decorator to verify webhook signatures"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get("X-Webhook-Signature")
        if not signature:
            return jsonify({"error": "Missing signature"}), 401

        payload = request.get_data()
        expected_signature = hmac.new(
            WEBHOOK_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return jsonify({"error": "Invalid signature"}), 401

        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# N8N WORKFLOW TRIGGERS
# ============================================================================


@integrations_bp.route("/n8n/trigger/<workflow_name>", methods=["POST"])
@login_required
def trigger_n8n_workflow(workflow_name):
    """Trigger specific N8N workflow"""
    try:
        data = request.get_json()

        # Add user context
        workflow_data = {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "user_name": current_user.name,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "biped-platform",
            "workflow": workflow_name,
            "data": data,
        }

        # Send to N8N webhook
        webhook_url = f"{N8N_WEBHOOK_BASE}/{workflow_name}"
        response = requests.post(webhook_url, json=workflow_data, timeout=30)

        if response.status_code == 200:
            return jsonify(
                {
                    "success": True,
                    "message": f"Workflow {workflow_name} triggered successfully",
                    "workflow_id": response.json().get("executionId"),
                }
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Workflow trigger failed: {response.status_code}",
                    }
                ),
                500,
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@integrations_bp.route("/n8n/workflows", methods=["GET"])
@login_required
def get_available_workflows():
    """Get list of available N8N workflows"""
    try:
        # Predefined workflows for Biped platform
        workflows = [
            {
                "name": "lead_generation",
                "description": "Automated lead generation and nurturing",
                "triggers": ["new_user_registration", "job_posted", "provider_signup"],
            },
            {
                "name": "email_marketing",
                "description": "Email marketing campaigns and sequences",
                "triggers": ["welcome_sequence", "job_completion", "invoice_reminder"],
            },
            {
                "name": "social_media_automation",
                "description": "Automated social media posting and engagement",
                "triggers": ["job_showcase", "provider_highlight", "success_story"],
            },
            {
                "name": "customer_communication",
                "description": "Automated customer communication workflows",
                "triggers": ["job_updates", "payment_reminders", "feedback_requests"],
            },
            {
                "name": "provider_onboarding",
                "description": "Automated provider onboarding and training",
                "triggers": ["new_provider", "verification_complete", "first_job"],
            },
            {
                "name": "quality_assurance",
                "description": "Automated quality checks and follow-ups",
                "triggers": ["job_completion", "quality_issue", "customer_complaint"],
            },
            {
                "name": "financial_automation",
                "description": "Automated financial processes and reporting",
                "triggers": [
                    "invoice_generated",
                    "payment_received",
                    "expense_recorded",
                ],
            },
            {
                "name": "market_analysis",
                "description": "Automated market research and competitive analysis",
                "triggers": ["weekly_analysis", "competitor_update", "pricing_review"],
            },
        ]

        return jsonify(
            {"success": True, "workflows": workflows, "total_count": len(workflows)}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# FLOWISE AI INTEGRATION
# ============================================================================


@integrations_bp.route("/flowise/chat/<chatflow_id>", methods=["POST"])
@login_required
def flowise_chat(chatflow_id):
    """Send message to Flowise chatflow"""
    try:
        data = request.get_json()
        question = data.get("question", "")

        if not question:
            return jsonify({"success": False, "error": "Question is required"}), 400

        # Prepare payload for Flowise
        payload = {
            "question": question,
            "overrideConfig": data.get("config", {}),
            "history": data.get("history", []),
            "uploads": data.get("uploads", []),
        }

        # Add user context
        user_context = f"""
        User Context:
        - User ID: {current_user.id}
        - Name: {current_user.name}
        - Email: {current_user.email}
        - User Type: {getattr(current_user, 'user_type', 'customer')}
        
        Question: {question}
        """

        payload["question"] = user_context

        # Send to Flowise
        flowise_url = f"{FLOWISE_API_BASE}/{chatflow_id}"
        response = requests.post(flowise_url, json=payload, timeout=60)

        if response.status_code == 200:
            ai_response = response.json()

            # Log the interaction
            log_ai_interaction(current_user.id, chatflow_id, question, ai_response)

            return jsonify(
                {
                    "success": True,
                    "response": ai_response.get("text", ""),
                    "sources": ai_response.get("sourceDocuments", []),
                    "chatflow_id": chatflow_id,
                }
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Flowise request failed: {response.status_code}",
                    }
                ),
                500,
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@integrations_bp.route("/flowise/chatflows", methods=["GET"])
@login_required
def get_available_chatflows():
    """Get list of available Flowise chatflows"""
    try:
        # Predefined chatflows for Biped platform
        chatflows = [
            {
                "id": "customer-support",
                "name": "Customer Support Assistant",
                "description": "AI assistant for customer support and general inquiries",
                "use_cases": [
                    "General questions",
                    "Platform navigation",
                    "Troubleshooting",
                ],
            },
            {
                "id": "quote-generator",
                "name": "Smart Quote Generator",
                "description": "AI-powered quote generation and pricing assistance",
                "use_cases": ["Project quotes", "Pricing analysis", "Cost estimation"],
            },
            {
                "id": "job-analyzer",
                "name": "Job Requirements Analyzer",
                "description": "Analyze job requirements and suggest optimal approaches",
                "use_cases": ["Job analysis", "Skill matching", "Timeline estimation"],
            },
            {
                "id": "business-advisor",
                "name": "Business Growth Advisor",
                "description": "AI advisor for business growth and optimization",
                "use_cases": [
                    "Business strategy",
                    "Growth planning",
                    "Market insights",
                ],
            },
            {
                "id": "compliance-checker",
                "name": "Compliance and Safety Checker",
                "description": "Check compliance requirements and safety standards",
                "use_cases": ["Safety compliance", "Building codes", "Regulations"],
            },
            {
                "id": "material-sourcing",
                "name": "Materials Sourcing Assistant",
                "description": "AI assistant for materials sourcing and procurement",
                "use_cases": [
                    "Material recommendations",
                    "Supplier suggestions",
                    "Cost optimization",
                ],
            },
            {
                "id": "project-planner",
                "name": "Project Planning Assistant",
                "description": "AI-powered project planning and scheduling",
                "use_cases": [
                    "Project timelines",
                    "Resource planning",
                    "Risk assessment",
                ],
            },
            {
                "id": "financial-advisor",
                "name": "Financial Management Advisor",
                "description": "AI advisor for financial planning and management",
                "use_cases": [
                    "Financial planning",
                    "Tax optimization",
                    "Cash flow management",
                ],
            },
        ]

        return jsonify(
            {"success": True, "chatflows": chatflows, "total_count": len(chatflows)}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# WEBHOOK ENDPOINTS (for receiving data from N8N/Flowise)
# ============================================================================


@integrations_bp.route("/webhooks/n8n/<workflow_name>", methods=["POST"])
@verify_webhook_signature
def receive_n8n_webhook(workflow_name):
    """Receive webhook from N8N workflow completion"""
    try:
        data = request.get_json()

        # Process different workflow results
        if workflow_name == "lead_generation":
            process_lead_generation_result(data)
        elif workflow_name == "email_marketing":
            process_email_marketing_result(data)
        elif workflow_name == "social_media_automation":
            process_social_media_result(data)
        elif workflow_name == "financial_automation":
            process_financial_automation_result(data)

        return jsonify(
            {
                "success": True,
                "message": f"Webhook {workflow_name} processed successfully",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@integrations_bp.route("/webhooks/flowise/feedback", methods=["POST"])
@verify_webhook_signature
def receive_flowise_feedback():
    """Receive feedback from Flowise interactions"""
    try:
        data = request.get_json()

        # Process AI interaction feedback
        process_ai_feedback(data)

        return jsonify(
            {"success": True, "message": "Flowise feedback processed successfully"}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# AUTOMATION MANAGEMENT
# ============================================================================


@integrations_bp.route("/automation/status", methods=["GET"])
@login_required
def get_automation_status():
    """Get status of all automation systems"""
    try:
        # Check N8N status
        n8n_status = check_n8n_status()

        # Check Flowise status
        flowise_status = check_flowise_status()

        # Get recent automation activities
        recent_activities = get_recent_automation_activities(current_user.id)

        return jsonify(
            {
                "success": True,
                "status": {
                    "n8n": n8n_status,
                    "flowise": flowise_status,
                    "overall": (
                        "healthy"
                        if n8n_status["healthy"] and flowise_status["healthy"]
                        else "degraded"
                    ),
                },
                "recent_activities": recent_activities,
                "last_updated": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@integrations_bp.route("/automation/configure", methods=["POST"])
@login_required
def configure_automation():
    """Configure automation settings for user"""
    try:
        data = request.get_json()

        # Update user automation preferences
        user_preferences = {
            "email_notifications": data.get("email_notifications", True),
            "sms_notifications": data.get("sms_notifications", False),
            "auto_quote_generation": data.get("auto_quote_generation", True),
            "auto_invoice_reminders": data.get("auto_invoice_reminders", True),
            "social_media_posting": data.get("social_media_posting", False),
            "lead_nurturing": data.get("lead_nurturing", True),
            "quality_monitoring": data.get("quality_monitoring", True),
        }

        # Save preferences (you might want to create a UserPreferences model)
        # For now, we'll store in user profile
        current_user.automation_preferences = user_preferences
        db.session.commit()

        # Trigger N8N workflow to update automation settings
        trigger_workflow_update(
            "user_preferences_updated",
            {"user_id": current_user.id, "preferences": user_preferences},
        )

        return jsonify(
            {
                "success": True,
                "message": "Automation settings updated successfully",
                "preferences": user_preferences,
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def log_ai_interaction(user_id, chatflow_id, question, response):
    """Log AI interaction for analytics"""
    try:
        # You might want to create an AIInteraction model for this
        interaction_data = {
            "user_id": user_id,
            "chatflow_id": chatflow_id,
            "question": question,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # For now, we'll trigger an N8N workflow to log this
        trigger_workflow_update("ai_interaction_logged", interaction_data)

    except Exception as e:
        print(f"Failed to log AI interaction: {e}")


def check_n8n_status():
    """Check N8N service health"""
    try:
        response = requests.get(f"{ANYTHINGLLM_BASE_URL}/healthz", timeout=10)
        return {
            "healthy": response.status_code == 200,
            "status_code": response.status_code,
            "last_checked": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "last_checked": datetime.utcnow().isoformat(),
        }


def check_flowise_status():
    """Check Flowise service health"""
    try:
        response = requests.get(f"{FLOWISE_API_BASE}/health", timeout=10)
        return {
            "healthy": response.status_code == 200,
            "status_code": response.status_code,
            "last_checked": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "last_checked": datetime.utcnow().isoformat(),
        }


def get_recent_automation_activities(user_id):
    """Get recent automation activities for user"""
    # This would query a log table or external service
    # For now, return mock data
    return [
        {
            "type": "email_sent",
            "description": "Welcome email sent to new customer",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        },
        {
            "type": "quote_generated",
            "description": "AI quote generated for kitchen renovation",
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "status": "success",
        },
    ]


def trigger_workflow_update(workflow_name, data):
    """Trigger N8N workflow update"""
    try:
        webhook_url = f"{N8N_WEBHOOK_BASE}/{workflow_name}"
        requests.post(webhook_url, json=data, timeout=10)
    except Exception as e:
        print(f"Failed to trigger workflow update: {e}")


def process_lead_generation_result(data):
    """Process lead generation workflow result"""
    # Implementation for processing lead generation results
    pass


def process_email_marketing_result(data):
    """Process email marketing workflow result"""
    # Implementation for processing email marketing results
    pass


def process_social_media_result(data):
    """Process social media automation result"""
    # Implementation for processing social media results
    pass


def process_financial_automation_result(data):
    """Process financial automation result"""
    # Implementation for processing financial automation results
    pass


def process_ai_feedback(data):
    """Process AI interaction feedback"""
    # Implementation for processing AI feedback
    pass
