from datetime import datetime

from flask import Blueprint, jsonify, request, session
from src.models.job import Job, JobStatus
from src.models.review import Review
from src.models.user import User, db

review_bp = Blueprint("review", __name__)


@review_bp.route("/", methods=["POST"])
def create_review():
    """Create a review for a completed job"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        data = request.get_json()

        # Validate required fields
        required_fields = ["job_id", "reviewee_id", "overall_rating"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        # Validate rating
        if not (1 <= data["overall_rating"] <= 5):
            return jsonify({"error": "Overall rating must be between 1 and 5"}), 400

        # Get job
        job = Job.query.get(data["job_id"])
        if not job:
            return jsonify({"error": "Job not found"}), 404

        # Check if job is completed
        if job.status != JobStatus.COMPLETED:
            return jsonify({"error": "Can only review completed jobs"}), 400

        # Check if user is involved in this job
        if job.customer_id != user_id and job.assigned_provider_id != user_id:
            return jsonify({"error": "You can only review jobs you were involved in"}), 403

        # Check if reviewee is the other party
        if data["reviewee_id"] == user_id:
            return jsonify({"error": "Cannot review yourself"}), 400

        if job.customer_id == user_id and data["reviewee_id"] != job.assigned_provider_id:
            return jsonify({"error": "Invalid reviewee"}), 400

        if job.assigned_provider_id == user_id and data["reviewee_id"] != job.customer_id:
            return jsonify({"error": "Invalid reviewee"}), 400

        # Check if review already exists
        existing_review = Review.query.filter_by(
            job_id=data["job_id"], reviewer_id=user_id, reviewee_id=data["reviewee_id"]
        ).first()

        if existing_review:
            return jsonify({"error": "Review already exists for this job"}), 409

        # Create review
        review = Review(
            job_id=data["job_id"],
            reviewer_id=user_id,
            reviewee_id=data["reviewee_id"],
            overall_rating=data["overall_rating"],
            quality_rating=data.get("quality_rating"),
            communication_rating=data.get("communication_rating"),
            timeliness_rating=data.get("timeliness_rating"),
            professionalism_rating=data.get("professionalism_rating"),
            value_rating=data.get("value_rating"),
            title=data.get("title"),
            comment=data.get("comment"),
            would_recommend=data.get("would_recommend"),
            would_hire_again=data.get("would_hire_again"),
        )

        db.session.add(review)

        # Update reviewee's average rating
        reviewee = User.query.get(data["reviewee_id"])
        if reviewee and reviewee.user_type == "provider" and reviewee.provider_profile:
            # Calculate new average rating
            all_reviews = Review.query.filter_by(reviewee_id=data["reviewee_id"]).all()
            if all_reviews:
                total_rating = sum([r.overall_rating for r in all_reviews]) + data["overall_rating"]
                count = len(all_reviews) + 1
                reviewee.provider_profile.average_rating = total_rating / count

        db.session.commit()

        return jsonify({"message": "Review created successfully", "review": review.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@review_bp.route("/user/<int:user_id>", methods=["GET"])
def get_user_reviews(user_id):
    """Get reviews for a specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Query parameters
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 50)

        # Get reviews where user is the reviewee
        query = Review.query.filter_by(reviewee_id=user_id, is_public=True).order_by(
            Review.created_at.desc()
        )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Calculate review statistics
        all_reviews = Review.query.filter_by(reviewee_id=user_id, is_public=True).all()

        stats = {
            "total_reviews": len(all_reviews),
            "average_rating": 0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        }

        if all_reviews:
            stats["average_rating"] = sum([r.overall_rating for r in all_reviews]) / len(
                all_reviews
            )
            for review in all_reviews:
                stats["rating_distribution"][review.overall_rating] += 1

        return (
            jsonify(
                {
                    "reviews": [review.to_dict() for review in pagination.items],
                    "pagination": {
                        "page": pagination.page,
                        "pages": pagination.pages,
                        "per_page": pagination.per_page,
                        "total": pagination.total,
                        "has_next": pagination.has_next,
                        "has_prev": pagination.has_prev,
                    },
                    "stats": stats,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@review_bp.route("/<int:review_id>", methods=["GET"])
def get_review(review_id):
    """Get a specific review"""
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({"error": "Review not found"}), 404

        if not review.is_public:
            # Check if current user is involved
            user_id = session.get("user_id")
            if user_id not in [review.reviewer_id, review.reviewee_id]:
                return jsonify({"error": "Review is private"}), 403

        return jsonify({"review": review.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@review_bp.route("/<int:review_id>/respond", methods=["POST"])
def respond_to_review(review_id):
    """Respond to a review (reviewee only)"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        review = Review.query.get(review_id)
        if not review:
            return jsonify({"error": "Review not found"}), 404

        if review.reviewee_id != user_id:
            return jsonify({"error": "Only the reviewee can respond to this review"}), 403

        if review.response:
            return jsonify({"error": "Response already exists"}), 409

        data = request.get_json()

        if not data.get("response"):
            return jsonify({"error": "Response is required"}), 400

        review.response = data["response"]
        review.response_date = datetime.utcnow()

        db.session.commit()

        return jsonify({"message": "Response added successfully", "review": review.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@review_bp.route("/my-reviews", methods=["GET"])
def get_my_reviews():
    """Get current user's reviews (given and received)"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        review_type = request.args.get("type", "received")  # 'given' or 'received'
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 50)

        if review_type == "given":
            query = Review.query.filter_by(reviewer_id=user_id)
        else:
            query = Review.query.filter_by(reviewee_id=user_id)

        query = query.order_by(Review.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "reviews": [review.to_dict() for review in pagination.items],
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


@review_bp.route("/pending", methods=["GET"])
def get_pending_reviews():
    """Get jobs that can be reviewed by current user"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        # Get completed jobs where user was involved but hasn't reviewed yet
        completed_jobs = Job.query.filter(
            Job.status == JobStatus.COMPLETED,
            (Job.customer_id == user_id) | (Job.assigned_provider_id == user_id),
        ).all()

        pending_reviews = []
        for job in completed_jobs:
            # Determine who to review
            reviewee_id = (
                job.assigned_provider_id if job.customer_id == user_id else job.customer_id
            )

            if reviewee_id:
                # Check if review already exists
                existing_review = Review.query.filter_by(
                    job_id=job.id, reviewer_id=user_id, reviewee_id=reviewee_id
                ).first()

                if not existing_review:
                    reviewee = User.query.get(reviewee_id)
                    pending_reviews.append(
                        {
                            "job": job.to_dict(),
                            "reviewee": {
                                "id": reviewee.id,
                                "name": reviewee.get_full_name(),
                                "user_type": reviewee.user_type,
                            },
                        }
                    )

        return jsonify({"pending_reviews": pending_reviews}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
