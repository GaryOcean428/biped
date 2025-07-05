from datetime import date, datetime

from flask import Blueprint, jsonify, request, session
from sqlalchemy import and_, or_

from src.models.job import Job, JobMessage, JobMilestone, JobStatus, Quote
from src.models.service import Service
from src.models.user import ProviderProfile, User, db

job_bp = Blueprint("job", __name__)


@job_bp.route("/", methods=["POST"])
def create_job():
    """Create a new job posting"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        user = User.query.get(user_id)
        if not user or user.user_type != "customer":
            return jsonify({"error": "Customer access required"}), 403

        data = request.get_json()

        # Validate required fields
        required_fields = [
            "service_id",
            "title",
            "description",
            "street_address",
            "city",
            "state",
            "postcode",
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        # Validate service exists
        service = Service.query.get(data["service_id"])
        if not service:
            return jsonify({"error": "Service not found"}), 404

        # Create job
        job = Job(
            customer_id=user_id,
            service_id=data["service_id"],
            title=data["title"],
            description=data["description"],
            street_address=data["street_address"],
            city=data["city"],
            state=data["state"],
            postcode=data["postcode"],
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            preferred_start_date=(
                datetime.strptime(data["preferred_start_date"], "%Y-%m-%d").date()
                if data.get("preferred_start_date")
                else None
            ),
            preferred_end_date=(
                datetime.strptime(data["preferred_end_date"], "%Y-%m-%d").date()
                if data.get("preferred_end_date")
                else None
            ),
            is_urgent=data.get("is_urgent", False),
            is_flexible_timing=data.get("is_flexible_timing", True),
            budget_min=data.get("budget_min"),
            budget_max=data.get("budget_max"),
            budget_type=data.get("budget_type", "negotiable"),
            property_type=data.get("property_type", "residential"),
            access_requirements=data.get("access_requirements"),
            special_requirements=data.get("special_requirements"),
            images=data.get("images", []),
            documents=data.get("documents", []),
            status=JobStatus.DRAFT if data.get("save_draft") else JobStatus.POSTED,
            posted_at=datetime.utcnow() if not data.get("save_draft") else None,
        )

        db.session.add(job)
        db.session.commit()

        return (
            jsonify({"message": "Job created successfully", "job": job.to_dict()}),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@job_bp.route("/", methods=["GET"])
def get_jobs():
    """Get jobs (filtered by user type and parameters)"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Query parameters
        status = request.args.get("status")
        service_id = request.args.get("service_id", type=int)
        postcode = request.args.get("postcode")
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)

        # Build query based on user type
        if user.user_type == "customer":
            # Customers see their own jobs
            query = Job.query.filter_by(customer_id=user_id)
        else:
            # Providers see available jobs in their area and services
            provider = user.provider_profile
            if not provider:
                return jsonify({"error": "Provider profile not found"}), 404

            # Get provider's service IDs
            from src.models.service import ProviderService

            provider_service_ids = [
                ps.service_id for ps in provider.services if ps.is_available
            ]

            if not provider_service_ids:
                return jsonify({"jobs": [], "pagination": {}}), 200

            query = Job.query.filter(
                and_(
                    Job.service_id.in_(provider_service_ids),
                    Job.status.in_([JobStatus.POSTED, JobStatus.MATCHED]),
                    Job.is_active == True,
                    Job.assigned_provider_id.is_(None),  # Not yet assigned
                )
            )

            # Filter by location (within service radius)
            if user.postcode:
                query = query.filter(Job.postcode == user.postcode)

        # Apply filters
        if status:
            try:
                status_enum = JobStatus(status)
                query = query.filter(Job.status == status_enum)
            except ValueError:
                return jsonify({"error": "Invalid status"}), 400

        if service_id:
            query = query.filter(Job.service_id == service_id)

        if postcode:
            query = query.filter(Job.postcode == postcode)

        # Order by creation date (newest first)
        query = query.order_by(Job.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "jobs": [job.to_dict() for job in pagination.items],
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


@job_bp.route("/<int:job_id>", methods=["GET"])
def get_job(job_id):
    """Get job details"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        user = User.query.get(user_id)

        # Check access permissions
        if user.user_type == "customer" and job.customer_id != user_id:
            return jsonify({"error": "Access denied"}), 403
        elif (
            user.user_type == "provider"
            and job.assigned_provider_id != user_id
            and job.status not in [JobStatus.POSTED, JobStatus.MATCHED]
        ):
            return jsonify({"error": "Access denied"}), 403

        # Get quotes if user is customer or assigned provider
        quotes = []
        if user.user_type == "customer" or job.assigned_provider_id == user_id:
            quotes = (
                Quote.query.filter_by(job_id=job_id, is_active=True)
                .order_by(Quote.price)
                .all()
            )

        # Get messages
        messages = (
            JobMessage.query.filter_by(job_id=job_id)
            .order_by(JobMessage.created_at)
            .all()
        )

        # Get milestones
        milestones = (
            JobMilestone.query.filter_by(job_id=job_id)
            .order_by(JobMilestone.sort_order)
            .all()
        )

        return (
            jsonify(
                {
                    "job": job.to_dict(),
                    "quotes": [quote.to_dict() for quote in quotes],
                    "messages": [message.to_dict() for message in messages],
                    "milestones": [milestone.to_dict() for milestone in milestones],
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@job_bp.route("/<int:job_id>/quote", methods=["POST"])
def create_quote():
    """Create a quote for a job"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        user = User.query.get(user_id)
        if not user or user.user_type != "provider":
            return jsonify({"error": "Provider access required"}), 403

        job_id = request.view_args["job_id"]
        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job.status not in [JobStatus.POSTED, JobStatus.MATCHED]:
            return jsonify({"error": "Job is not available for quotes"}), 400

        # Check if provider already quoted
        existing_quote = Quote.query.filter_by(
            job_id=job_id, provider_id=user_id
        ).first()
        if existing_quote:
            return jsonify({"error": "You have already quoted for this job"}), 409

        data = request.get_json()

        # Validate required fields
        if not data.get("price"):
            return jsonify({"error": "Price is required"}), 400

        # Create quote
        quote = Quote(
            job_id=job_id,
            provider_id=user_id,
            price=data["price"],
            description=data.get("description"),
            estimated_start_date=(
                datetime.strptime(data["estimated_start_date"], "%Y-%m-%d").date()
                if data.get("estimated_start_date")
                else None
            ),
            estimated_completion_date=(
                datetime.strptime(data["estimated_completion_date"], "%Y-%m-%d").date()
                if data.get("estimated_completion_date")
                else None
            ),
            estimated_duration_days=data.get("estimated_duration_days"),
            includes_materials=data.get("includes_materials", False),
            warranty_period_months=data.get("warranty_period_months"),
            payment_terms=data.get("payment_terms"),
            valid_until=(
                datetime.strptime(data["valid_until"], "%Y-%m-%d %H:%M:%S")
                if data.get("valid_until")
                else None
            ),
        )

        db.session.add(quote)

        # Update job status to MATCHED if it was POSTED
        if job.status == JobStatus.POSTED:
            job.status = JobStatus.MATCHED

        db.session.commit()

        return (
            jsonify(
                {"message": "Quote created successfully", "quote": quote.to_dict()}
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@job_bp.route("/<int:job_id>/quotes/<int:quote_id>/accept", methods=["POST"])
def accept_quote(job_id, quote_id):
    """Accept a quote for a job"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job.customer_id != user_id:
            return jsonify({"error": "Only job owner can accept quotes"}), 403

        quote = Quote.query.get(quote_id)
        if not quote or quote.job_id != job_id:
            return jsonify({"error": "Quote not found"}), 404

        if job.status != JobStatus.MATCHED:
            return jsonify({"error": "Job is not in a state to accept quotes"}), 400

        # Accept the quote
        quote.is_accepted = True

        # Update job
        job.assigned_provider_id = quote.provider_id
        job.agreed_price = quote.price
        job.status = JobStatus.ACCEPTED
        job.accepted_at = datetime.utcnow()

        # Deactivate other quotes
        other_quotes = Quote.query.filter(
            and_(Quote.job_id == job_id, Quote.id != quote_id)
        ).all()
        for other_quote in other_quotes:
            other_quote.is_active = False

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Quote accepted successfully",
                    "job": job.to_dict(),
                    "quote": quote.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@job_bp.route("/<int:job_id>/start", methods=["POST"])
def start_job(job_id):
    """Start a job (provider action)"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job.assigned_provider_id != user_id:
            return jsonify({"error": "Only assigned provider can start the job"}), 403

        if job.status != JobStatus.ACCEPTED:
            return jsonify({"error": "Job must be accepted before starting"}), 400

        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.utcnow()

        db.session.commit()

        return (
            jsonify({"message": "Job started successfully", "job": job.to_dict()}),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@job_bp.route("/<int:job_id>/complete", methods=["POST"])
def complete_job(job_id):
    """Complete a job (provider action)"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job.assigned_provider_id != user_id:
            return (
                jsonify({"error": "Only assigned provider can complete the job"}),
                403,
            )

        if job.status != JobStatus.IN_PROGRESS:
            return jsonify({"error": "Job must be in progress to complete"}), 400

        data = request.get_json()

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.final_price = data.get("final_price", job.agreed_price)

        # Calculate commission (5% default)
        if job.final_price:
            provider = User.query.get(job.assigned_provider_id).provider_profile
            commission_rate = provider.commission_rate if provider else 0.05
            job.commission_amount = float(job.final_price) * commission_rate

        db.session.commit()

        return (
            jsonify({"message": "Job completed successfully", "job": job.to_dict()}),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@job_bp.route("/<int:job_id>/messages", methods=["POST"])
def send_job_message(job_id):
    """Send a message related to a job"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        # Check if user is involved in this job
        if job.customer_id != user_id and job.assigned_provider_id != user_id:
            return jsonify({"error": "Access denied"}), 403

        data = request.get_json()

        if not data.get("message"):
            return jsonify({"error": "Message is required"}), 400

        message = JobMessage(
            job_id=job_id,
            sender_id=user_id,
            message=data["message"],
            attachments=data.get("attachments", []),
        )

        db.session.add(message)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Message sent successfully",
                    "job_message": message.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
