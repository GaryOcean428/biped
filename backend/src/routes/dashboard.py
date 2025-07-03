"""
Dashboard API routes for Biped platform
Provides real-time statistics and analytics
"""

from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, func
from src.models.financial import Invoice, PlatformRevenue
from src.models.job import Job, JobStatus
from src.models.review import Review
from src.models.service import ServiceCategory
from src.models.user import CustomerProfile, ProviderProfile, User, db

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/stats", methods=["GET"])
def get_dashboard_stats():
    """Get overall platform statistics"""
    try:
        # Get basic counts
        total_jobs = Job.query.count()
        total_users = User.query.count()
        total_providers = User.query.filter_by(user_type="provider").count()
        total_customers = User.query.filter_by(user_type="customer").count()

        # Get active jobs (not completed, cancelled, or disputed)
        active_jobs = Job.query.filter(
            Job.status.in_(
                [JobStatus.POSTED, JobStatus.MATCHED, JobStatus.ACCEPTED, JobStatus.IN_PROGRESS]
            )
        ).count()

        # Get completed jobs
        completed_jobs = Job.query.filter_by(status=JobStatus.COMPLETED).count()

        # Get total revenue (sum of all completed platform revenue)
        total_revenue = db.session.query(func.sum(PlatformRevenue.commission_amount)).filter(
            PlatformRevenue.payment_status == "completed"
        ).scalar() or Decimal("0")

        # Get average rating
        avg_rating = db.session.query(func.avg(Review.overall_rating)).scalar() or 0.0

        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_jobs = Job.query.filter(Job.created_at >= thirty_days_ago).count()
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()

        # Get monthly revenue (last 30 days)
        monthly_revenue = db.session.query(func.sum(PlatformRevenue.commission_amount)).filter(
            and_(
                PlatformRevenue.payment_status == "completed",
                PlatformRevenue.created_at >= thirty_days_ago,
            )
        ).scalar() or Decimal("0")

        return jsonify(
            {
                "success": True,
                "data": {
                    "total_jobs": total_jobs,
                    "active_jobs": active_jobs,
                    "completed_jobs": completed_jobs,
                    "total_users": total_users,
                    "total_providers": total_providers,
                    "total_customers": total_customers,
                    "total_revenue": float(total_revenue),
                    "monthly_revenue": float(monthly_revenue),
                    "average_rating": round(float(avg_rating), 1) if avg_rating else 0.0,
                    "recent_jobs": recent_jobs,
                    "recent_users": recent_users,
                    "last_updated": datetime.utcnow().isoformat(),
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/jobs/recent", methods=["GET"])
def get_recent_jobs():
    """Get recent jobs with details"""
    try:
        limit = request.args.get("limit", 10, type=int)

        jobs = Job.query.order_by(Job.created_at.desc()).limit(limit).all()

        jobs_data = []
        for job in jobs:
            customer = User.query.get(job.customer_id)
            provider = (
                User.query.get(job.assigned_provider_id) if job.assigned_provider_id else None
            )

            jobs_data.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "description": (
                        job.description[:100] + "..."
                        if len(job.description) > 100
                        else job.description
                    ),
                    "status": job.status.value if hasattr(job.status, "value") else str(job.status),
                    "budget_min": float(job.budget_min) if job.budget_min else None,
                    "budget_max": float(job.budget_max) if job.budget_max else None,
                    "location": f"{job.city}, {job.state}",
                    "customer": {
                        "name": customer.get_full_name() if customer else "Unknown",
                        "email": customer.email if customer else None,
                    },
                    "provider": (
                        {
                            "name": provider.get_full_name() if provider else None,
                            "email": provider.email if provider else None,
                        }
                        if provider
                        else None
                    ),
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "is_urgent": job.is_urgent,
                }
            )

        return jsonify({"success": True, "data": jobs_data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/revenue/chart", methods=["GET"])
def get_revenue_chart():
    """Get revenue data for charts"""
    try:
        days = request.args.get("days", 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get daily revenue for the period
        daily_revenue = (
            db.session.query(
                func.date(PlatformRevenue.created_at).label("date"),
                func.sum(PlatformRevenue.commission_amount).label("revenue"),
            )
            .filter(
                and_(
                    PlatformRevenue.payment_status == "completed",
                    PlatformRevenue.created_at >= start_date,
                )
            )
            .group_by(func.date(PlatformRevenue.created_at))
            .all()
        )

        # Format data for charts
        chart_data = []
        for record in daily_revenue:
            chart_data.append({"date": record.date.isoformat(), "revenue": float(record.revenue)})

        return jsonify({"success": True, "data": chart_data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/providers/top", methods=["GET"])
def get_top_providers():
    """Get top performing providers"""
    try:
        limit = request.args.get("limit", 5, type=int)

        # Get providers with their stats
        providers = (
            db.session.query(
                User,
                ProviderProfile,
                func.count(Job.id).label("job_count"),
                func.avg(Review.overall_rating).label("avg_rating"),
            )
            .join(ProviderProfile, User.id == ProviderProfile.user_id)
            .outerjoin(Job, User.id == Job.assigned_provider_id)
            .outerjoin(Review, User.id == Review.reviewee_id)
            .filter(User.user_type == "provider")
            .group_by(User.id)
            .order_by(func.avg(Review.overall_rating).desc())
            .limit(limit)
            .all()
        )

        providers_data = []
        for user, profile, job_count, avg_rating in providers:
            providers_data.append(
                {
                    "id": user.id,
                    "name": user.get_full_name(),
                    "business_name": profile.business_name,
                    "email": user.email,
                    "location": f"{user.city}, {user.state}" if user.city else None,
                    "job_count": job_count or 0,
                    "avg_rating": round(float(avg_rating), 1) if avg_rating else 0.0,
                    "hourly_rate": float(profile.hourly_rate) if profile.hourly_rate else None,
                    "years_experience": profile.years_experience,
                    "is_available": profile.is_available,
                    "total_earnings": (
                        float(profile.total_earnings) if profile.total_earnings else 0.0
                    ),
                }
            )

        return jsonify({"success": True, "data": providers_data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/categories/stats", methods=["GET"])
def get_category_stats():
    """Get job statistics by category"""
    try:
        # Get job counts by service category
        category_stats = (
            db.session.query(
                ServiceCategory.name,
                func.count(Job.id).label("job_count"),
                func.avg(Job.budget_max).label("avg_budget"),
            )
            .join(Job, ServiceCategory.id == Job.service_id)
            .group_by(ServiceCategory.id)
            .all()
        )

        stats_data = []
        for name, job_count, avg_budget in category_stats:
            stats_data.append(
                {
                    "category": name,
                    "job_count": job_count or 0,
                    "avg_budget": round(float(avg_budget), 2) if avg_budget else 0.0,
                }
            )

        return jsonify({"success": True, "data": stats_data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
