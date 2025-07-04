"""
Job Management Routes
Handles job posting, browsing, and management
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request
from flask_cors import cross_origin
from src.models import Job, Service, ServiceCategory, User, db
from src.utils.rate_limiting import limiter
from src.utils.validation import validate_required_fields

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/post-job", methods=["GET"])
def post_job_page():
    """Serve the job posting page"""
    try:
        # Get service categories for the form
        categories = []
        try:
            categories = ServiceCategory.query.all()
        except Exception as db_error:
            logging.warning(
                f"Database query failed, using empty categories: {db_error}"
            )
            categories = []

        try:
            return render_template("post_job.html", categories=categories)
        except Exception as template_error:
            logging.warning(f"Template rendering failed: {template_error}")
            # Fallback to simple HTML response
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Post a Job - Biped</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
                <h1>Post a Job</h1>
                <p>Job posting functionality is being set up. Please check back soon!</p>
                <a href="/">← Back to Home</a>
            </body>
            </html>
            """
    except Exception as e:
        logging.error(f"Error loading post job page: {e}")
        return (
            f"<h1>Error</h1><p>Unable to load job posting page: {str(e)}</p><a href='/'>← Back to Home</a>",
            500,
        )


@jobs_bp.route("/api/jobs", methods=["POST"])
@limiter.limit("5 per minute")
@cross_origin()
def create_job():
    """Create a new job posting"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["title", "description", "category_id", "budget", "location"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        # Create new job
        job = Job(
            title=data["title"],
            description=data["description"],
            service_id=data["category_id"],  # Using service_id to match model
            budget_min=float(data["budget"]),
            budget_max=float(data["budget"]),
            budget_type="fixed",
            street_address=data["location"],  # Using street_address for location
            city=data["location"],
            state="NSW",  # Default state
            postcode="2000",  # Default postcode
            property_type="residential",  # Default property type
            is_urgent=(data.get("urgency") == "asap"),
            special_requirements=data.get("requirements", ""),
            customer_id=data.get("customer_id", 1),  # Default customer for demo
            status="posted",
            posted_at=datetime.utcnow(),
        )

        db.session.add(job)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "job_id": job.id,
                    "message": "Job posted successfully!",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating job: {e}")
        return jsonify({"error": "Failed to create job. Please try again."}), 500


@jobs_bp.route("/api/jobs", methods=["GET"])
@cross_origin()
def get_jobs():
    """Get list of jobs with filtering"""
    try:
        # Get query parameters
        category_id = request.args.get("category_id", type=int)
        location = request.args.get("location")
        min_budget = request.args.get("min_budget", type=float)
        max_budget = request.args.get("max_budget", type=float)
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)

        # Build query
        query = Job.query.filter_by(status="posted")

        if category_id:
            # Join with Service to filter by category
            query = query.join(Service).filter(Service.category_id == category_id)
        if location:
            query = query.filter(Job.street_address.ilike(f"%{location}%"))
        if min_budget:
            query = query.filter(Job.budget_min >= min_budget)
        if max_budget:
            query = query.filter(Job.budget_max <= max_budget)

        # Order by creation date (newest first)
        query = query.order_by(Job.created_at.desc())

        # Paginate
        jobs = query.paginate(page=page, per_page=per_page, error_out=False)

        # Format response
        job_list = []
        for job in jobs.items:
            job_data = {
                "id": job.id,
                "title": job.title,
                "description": (
                    job.description[:200] + "..."
                    if len(job.description) > 200
                    else job.description
                ),
                "budget_min": float(job.budget_min) if job.budget_min else None,
                "budget_max": float(job.budget_max) if job.budget_max else None,
                "location": job.street_address,
                "is_urgent": job.is_urgent,
                "created_at": job.created_at.isoformat(),
                "service_name": job.service.name if job.service else None,
                "category_name": (
                    job.service.category.name
                    if job.service and job.service.category
                    else None
                ),
            }
            job_list.append(job_data)

        return jsonify(
            {
                "jobs": job_list,
                "pagination": {
                    "page": jobs.page,
                    "pages": jobs.pages,
                    "per_page": jobs.per_page,
                    "total": jobs.total,
                    "has_next": jobs.has_next,
                    "has_prev": jobs.has_prev,
                },
            }
        )

    except Exception as e:
        logging.error(f"Error fetching jobs: {e}")
        return jsonify({"error": "Failed to fetch jobs. Please try again."}), 500


@jobs_bp.route("/api/jobs/<int:job_id>", methods=["GET"])
@cross_origin()
def get_job(job_id):
    """Get detailed job information"""
    try:
        job = Job.query.get_or_404(job_id)

        job_data = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "budget_min": float(job.budget_min) if job.budget_min else None,
            "budget_max": float(job.budget_max) if job.budget_max else None,
            "location": job.street_address,
            "is_urgent": job.is_urgent,
            "special_requirements": job.special_requirements,
            "status": (
                job.status.value if hasattr(job.status, "value") else str(job.status)
            ),
            "created_at": job.created_at.isoformat(),
            "service": (
                {
                    "id": job.service.id,
                    "name": job.service.name,
                    "category_id": job.service.category_id,
                    "category_name": (
                        job.service.category.name if job.service.category else None
                    ),
                }
                if job.service
                else None
            ),
            "customer": (
                {
                    "id": job.customer.id,
                    "name": (
                        f"{job.customer.customer_profile.first_name} {job.customer.customer_profile.last_name}"
                        if job.customer and job.customer.customer_profile
                        else "Anonymous"
                    ),
                }
                if job.customer
                else None
            ),
        }

        return jsonify(job_data)

    except Exception as e:
        logging.error(f"Error fetching job {job_id}: {e}")
        return jsonify({"error": "Job not found."}), 404


@jobs_bp.route("/browse-jobs", methods=["GET"])
def browse_jobs_page():
    """Serve the job browsing page"""
    try:
        categories = ServiceCategory.query.all()
        return render_template("browse_jobs.html", categories=categories)
    except Exception as e:
        logging.error(f"Error loading browse jobs page: {e}")
        return (
            render_template(
                "error.html",
                error="Unable to load job browsing page. Please try again.",
            ),
            500,
        )


@jobs_bp.route("/jobs/<int:job_id>", methods=["GET"])
def job_detail_page(job_id):
    """Serve the job detail page"""
    try:
        job = Job.query.get_or_404(job_id)
        return render_template("job_detail.html", job=job)
    except Exception as e:
        logging.error(f"Error loading job detail page: {e}")
        return render_template("error.html", error="Job not found."), 404
