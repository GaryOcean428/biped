from datetime import datetime

from flask import Blueprint, jsonify, request, session
from src.models.user import CustomerProfile, ProviderProfile, User, db

user_bp = Blueprint("user", __name__)


@user_bp.route("/", methods=["GET"])
def get_users():
    """Get all users (admin only or limited public info)"""
    try:
        # For now, return limited public info for providers only
        providers = User.query.filter_by(user_type="provider", is_active=True).all()

        result = []
        for user in providers:
            if user.provider_profile:
                result.append(
                    {
                        "id": user.id,
                        "name": user.get_full_name(),
                        "business_name": user.provider_profile.business_name,
                        "city": user.city,
                        "state": user.state,
                        "average_rating": user.provider_profile.average_rating,
                        "total_jobs_completed": user.provider_profile.total_jobs_completed,
                        "profile_image": user.profile_image,
                    }
                )

        return jsonify({"providers": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Get user profile"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if not user.is_active:
            return jsonify({"error": "User not available"}), 404

        # Get profile data
        profile_data = None
        if user.user_type == "customer" and user.customer_profile:
            profile_data = user.customer_profile.to_dict()
        elif user.user_type == "provider" and user.provider_profile:
            profile_data = user.provider_profile.to_dict()

        # Public user info
        user_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.get_full_name(),
            "user_type": user.user_type,
            "city": user.city,
            "state": user.state,
            "profile_image": user.profile_image,
            "bio": user.bio,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

        return jsonify({"user": user_data, "profile": profile_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user_bp.route("/profile", methods=["GET"])
def get_my_profile():
    """Get current user's full profile"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get profile data
        profile_data = None
        if user.user_type == "customer" and user.customer_profile:
            profile_data = user.customer_profile.to_dict()
        elif user.user_type == "provider" and user.provider_profile:
            profile_data = user.provider_profile.to_dict()

        return jsonify({"user": user.to_dict(), "profile": profile_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user_bp.route("/profile", methods=["PUT"])
def update_profile():
    """Update current user's profile"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()

        # Update user fields
        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]
        if "phone" in data:
            user.phone = data["phone"]
        if "street_address" in data:
            user.street_address = data["street_address"]
        if "city" in data:
            user.city = data["city"]
        if "state" in data:
            user.state = data["state"]
        if "postcode" in data:
            user.postcode = data["postcode"]
        if "bio" in data:
            user.bio = data["bio"]
        if "profile_image" in data:
            user.profile_image = data["profile_image"]

        user.updated_at = datetime.utcnow()

        # Update profile based on user type
        if user.user_type == "customer" and user.customer_profile:
            profile = user.customer_profile
            if "preferred_contact_method" in data:
                profile.preferred_contact_method = data["preferred_contact_method"]
            if "notification_preferences" in data:
                profile.notification_preferences = data["notification_preferences"]
            profile.updated_at = datetime.utcnow()

        elif user.user_type == "provider" and user.provider_profile:
            profile = user.provider_profile
            if "business_name" in data:
                profile.business_name = data["business_name"]
            if "abn" in data:
                profile.abn = data["abn"]
            if "license_number" in data:
                profile.license_number = data["license_number"]
            if "insurance_policy" in data:
                profile.insurance_policy = data["insurance_policy"]
            if "years_experience" in data:
                profile.years_experience = data["years_experience"]
            if "hourly_rate" in data:
                profile.hourly_rate = data["hourly_rate"]
            if "service_radius" in data:
                profile.service_radius = data["service_radius"]
            if "is_available" in data:
                profile.is_available = data["is_available"]
            if "availability_schedule" in data:
                profile.availability_schedule = data["availability_schedule"]
            if "auto_accept_jobs" in data:
                profile.auto_accept_jobs = data["auto_accept_jobs"]
            profile.updated_at = datetime.utcnow()

        db.session.commit()

        # Get updated profile data
        profile_data = None
        if user.user_type == "customer" and user.customer_profile:
            profile_data = user.customer_profile.to_dict()
        elif user.user_type == "provider" and user.provider_profile:
            profile_data = user.provider_profile.to_dict()

        return (
            jsonify(
                {
                    "message": "Profile updated successfully",
                    "user": user.to_dict(),
                    "profile": profile_data,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@user_bp.route("/dashboard", methods=["GET"])
def get_dashboard():
    """Get dashboard data for current user"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        from src.models.job import Job, JobStatus
        from src.models.review import Message, Notification, Review

        dashboard_data = {}

        if user.user_type == "customer":
            # Customer dashboard
            dashboard_data = {
                "total_jobs_posted": Job.query.filter_by(customer_id=user_id).count(),
                "active_jobs": Job.query.filter_by(customer_id=user_id, is_active=True)
                .filter(
                    Job.status.in_(
                        [
                            JobStatus.POSTED,
                            JobStatus.MATCHED,
                            JobStatus.ACCEPTED,
                            JobStatus.IN_PROGRESS,
                        ]
                    )
                )
                .count(),
                "completed_jobs": Job.query.filter_by(
                    customer_id=user_id, status=JobStatus.COMPLETED
                ).count(),
                "pending_reviews": Review.query.join(Job)
                .filter(
                    Job.customer_id == user_id,
                    Job.status == JobStatus.COMPLETED,
                    ~Review.query.filter_by(reviewer_id=user_id).exists(),
                )
                .count(),
                "unread_messages": Message.query.filter_by(
                    recipient_id=user_id, is_read=False
                ).count(),
                "recent_jobs": [
                    job.to_dict()
                    for job in Job.query.filter_by(customer_id=user_id)
                    .order_by(Job.created_at.desc())
                    .limit(5)
                    .all()
                ],
            }

        elif user.user_type == "provider":
            # Provider dashboard
            provider = user.provider_profile
            if provider:
                dashboard_data = {
                    "total_jobs_completed": provider.total_jobs_completed,
                    "total_earnings": (
                        float(provider.total_earnings)
                        if provider.total_earnings
                        else 0.0
                    ),
                    "average_rating": provider.average_rating,
                    "active_jobs": Job.query.filter_by(assigned_provider_id=user_id)
                    .filter(Job.status.in_([JobStatus.ACCEPTED, JobStatus.IN_PROGRESS]))
                    .count(),
                    "available_jobs": Job.query.filter(
                        Job.status == JobStatus.POSTED,
                        Job.postcode == user.postcode,  # Simple location filter
                    ).count(),
                    "pending_quotes": Job.query.filter_by(
                        status=JobStatus.MATCHED
                    ).count(),
                    "unread_messages": Message.query.filter_by(
                        recipient_id=user_id, is_read=False
                    ).count(),
                    "recent_jobs": [
                        job.to_dict()
                        for job in Job.query.filter_by(assigned_provider_id=user_id)
                        .order_by(Job.created_at.desc())
                        .limit(5)
                        .all()
                    ],
                }

        # Common data
        dashboard_data["unread_notifications"] = Notification.query.filter_by(
            user_id=user_id, is_read=False
        ).count()

        return jsonify({"dashboard": dashboard_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user_bp.route("/search", methods=["GET"])
def search_users():
    """Search for users (providers)"""
    try:
        query = request.args.get("q", "").strip()
        location = request.args.get("location", "").strip()
        user_type = request.args.get("type", "provider")
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)

        # Build query
        users_query = User.query.filter_by(user_type=user_type, is_active=True)

        # Search by name or business name
        if query:
            if user_type == "provider":
                users_query = users_query.join(ProviderProfile).filter(
                    db.or_(
                        User.first_name.ilike(f"%{query}%"),
                        User.last_name.ilike(f"%{query}%"),
                        ProviderProfile.business_name.ilike(f"%{query}%"),
                    )
                )
            else:
                users_query = users_query.filter(
                    db.or_(
                        User.first_name.ilike(f"%{query}%"),
                        User.last_name.ilike(f"%{query}%"),
                    )
                )

        # Filter by location
        if location:
            users_query = users_query.filter(
                db.or_(
                    User.city.ilike(f"%{location}%"),
                    User.postcode.ilike(f"%{location}%"),
                )
            )

        # Paginate
        pagination = users_query.paginate(page=page, per_page=per_page, error_out=False)

        # Format results
        results = []
        for user in pagination.items:
            user_data = {
                "id": user.id,
                "name": user.get_full_name(),
                "user_type": user.user_type,
                "city": user.city,
                "state": user.state,
                "profile_image": user.profile_image,
            }

            if user.user_type == "provider" and user.provider_profile:
                user_data.update(
                    {
                        "business_name": user.provider_profile.business_name,
                        "average_rating": user.provider_profile.average_rating,
                        "total_jobs_completed": user.provider_profile.total_jobs_completed,
                        "hourly_rate": (
                            float(user.provider_profile.hourly_rate)
                            if user.provider_profile.hourly_rate
                            else None
                        ),
                    }
                )

            results.append(user_data)

        return (
            jsonify(
                {
                    "users": results,
                    "pagination": {
                        "page": pagination.page,
                        "pages": pagination.pages,
                        "per_page": pagination.per_page,
                        "total": pagination.total,
                        "has_next": pagination.has_next,
                        "has_prev": pagination.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
