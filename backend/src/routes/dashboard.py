from flask import Blueprint, jsonify, session, request
from src.models.user import db, User, ProviderProfile, CustomerProfile
from src.models.job import Job, Quote, JobStatus
from src.models.service import Service, ServiceCategory, ProviderService
from src.models.review import Review
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get overall platform statistics for dashboard"""
    try:
        # Get basic platform stats
        total_jobs = Job.query.count()
        active_jobs = Job.query.filter(Job.status.in_([JobStatus.POSTED, JobStatus.MATCHED, JobStatus.ACCEPTED, JobStatus.IN_PROGRESS])).count()
        completed_jobs = Job.query.filter_by(status=JobStatus.COMPLETED).count()
        total_providers = User.query.filter_by(user_type='provider', is_active=True).count()
        total_customers = User.query.filter_by(user_type='customer', is_active=True).count()
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_jobs = Job.query.filter(Job.created_at >= thirty_days_ago).count()
        recent_signups = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        # Get service categories with job counts
        service_stats = db.session.query(
            ServiceCategory.name,
            func.count(Job.id).label('job_count')
        ).join(Service).join(Job).group_by(ServiceCategory.id, ServiceCategory.name).all()
        
        # Get top providers by rating
        top_providers = db.session.query(
            User.first_name,
            User.last_name,
            ProviderProfile.business_name,
            ProviderProfile.average_rating,
            ProviderProfile.total_jobs_completed
        ).join(ProviderProfile).filter(
            User.user_type == 'provider',
            User.is_active == True,
            ProviderProfile.total_jobs_completed > 0
        ).order_by(desc(ProviderProfile.average_rating)).limit(5).all()
        
        return jsonify({
            'platform_stats': {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'completed_jobs': completed_jobs,
                'total_providers': total_providers,
                'total_customers': total_customers,
                'recent_jobs_30d': recent_jobs,
                'recent_signups_30d': recent_signups
            },
            'service_stats': [
                {'category': stat.name, 'job_count': stat.job_count}
                for stat in service_stats
            ],
            'top_providers': [
                {
                    'name': f"{provider.first_name} {provider.last_name}",
                    'business_name': provider.business_name,
                    'rating': float(provider.average_rating) if provider.average_rating else 0.0,
                    'jobs_completed': provider.total_jobs_completed
                }
                for provider in top_providers
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/recent-activity', methods=['GET'])
def get_recent_activity():
    """Get recent platform activity for dashboard"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Get recent jobs with customer and provider info
        recent_jobs = db.session.query(
            Job.id,
            Job.title,
            Job.status,
            Job.created_at,
            Job.posted_at,
            Job.completed_at,
            User.first_name.label('customer_first_name'),
            User.last_name.label('customer_last_name'),
            Service.name.label('service_name'),
            ServiceCategory.name.label('category_name')
        ).join(User, Job.customer_id == User.id)\
         .join(Service, Job.service_id == Service.id)\
         .join(ServiceCategory, Service.category_id == ServiceCategory.id)\
         .order_by(desc(Job.created_at))\
         .limit(limit).all()
        
        # Get recent reviews
        recent_reviews = db.session.query(
            Review.id,
            Review.rating,
            Review.comment,
            Review.created_at,
            User.first_name.label('customer_first_name'),
            User.last_name.label('customer_last_name'),
            Job.title.label('job_title')
        ).join(User, Review.customer_id == User.id)\
         .join(Job, Review.job_id == Job.id)\
         .order_by(desc(Review.created_at))\
         .limit(5).all()
        
        activity_feed = []
        
        # Add jobs to activity feed
        for job in recent_jobs:
            activity_feed.append({
                'type': 'job',
                'id': job.id,
                'title': job.title,
                'description': f"New {job.category_name.lower()} job posted by {job.customer_first_name} {job.customer_last_name}",
                'service': job.service_name,
                'category': job.category_name,
                'status': job.status.value if job.status else 'unknown',
                'timestamp': job.created_at.isoformat() if job.created_at else None,
                'customer_name': f"{job.customer_first_name} {job.customer_last_name}"
            })
        
        # Add reviews to activity feed
        for review in recent_reviews:
            activity_feed.append({
                'type': 'review',
                'id': review.id,
                'title': f"{review.rating}-star review",
                'description': f"{review.customer_first_name} {review.customer_last_name} reviewed '{review.job_title}'",
                'rating': review.rating,
                'comment': review.comment[:100] + '...' if review.comment and len(review.comment) > 100 else review.comment,
                'timestamp': review.created_at.isoformat() if review.created_at else None,
                'customer_name': f"{review.customer_first_name} {review.customer_last_name}"
            })
        
        # Sort by timestamp
        activity_feed.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        return jsonify({
            'activity': activity_feed[:limit]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/service-categories', methods=['GET'])
def get_service_categories():
    """Get service categories with statistics"""
    try:
        categories = db.session.query(
            ServiceCategory.id,
            ServiceCategory.name,
            ServiceCategory.slug,
            ServiceCategory.description,
            ServiceCategory.icon,
            func.count(Job.id).label('total_jobs'),
            func.count(ProviderService.id).label('total_providers')
        ).outerjoin(Service, ServiceCategory.id == Service.category_id)\
         .outerjoin(Job, Service.id == Job.service_id)\
         .outerjoin(ProviderService, ServiceCategory.id == ProviderService.category_id)\
         .filter(ServiceCategory.is_active == True)\
         .group_by(ServiceCategory.id)\
         .order_by(ServiceCategory.sort_order, ServiceCategory.name).all()
        
        return jsonify({
            'categories': [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'slug': cat.slug,
                    'description': cat.description,
                    'icon': cat.icon,
                    'total_jobs': cat.total_jobs or 0,
                    'total_providers': cat.total_providers or 0
                }
                for cat in categories
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/user-stats/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    """Get statistics for a specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        stats = {}
        
        if user.user_type == 'customer':
            # Customer statistics
            customer_profile = user.customer_profile
            total_jobs = Job.query.filter_by(customer_id=user_id).count()
            active_jobs = Job.query.filter_by(customer_id=user_id).filter(
                Job.status.in_([JobStatus.POSTED, JobStatus.MATCHED, JobStatus.ACCEPTED, JobStatus.IN_PROGRESS])
            ).count()
            completed_jobs = Job.query.filter_by(customer_id=user_id, status=JobStatus.COMPLETED).count()
            
            stats = {
                'user_type': 'customer',
                'total_jobs_posted': total_jobs,
                'active_jobs': active_jobs,
                'completed_jobs': completed_jobs,
                'total_spent': float(customer_profile.total_spent) if customer_profile and customer_profile.total_spent else 0.0,
                'average_rating_given': customer_profile.average_rating_given if customer_profile else 0.0
            }
            
        elif user.user_type == 'provider':
            # Provider statistics
            provider_profile = user.provider_profile
            if provider_profile:
                stats = {
                    'user_type': 'provider',
                    'total_jobs_completed': provider_profile.total_jobs_completed,
                    'total_earnings': float(provider_profile.total_earnings) if provider_profile.total_earnings else 0.0,
                    'average_rating': provider_profile.average_rating,
                    'response_time_hours': provider_profile.response_time_hours,
                    'completion_rate': provider_profile.completion_rate,
                    'verification_score': provider_profile.get_verification_score(),
                    'is_available': provider_profile.is_available,
                    'service_radius': provider_profile.service_radius
                }
        
        return jsonify({
            'user': user.to_dict(),
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/financial-summary', methods=['GET'])
def get_financial_summary():
    """Get financial summary for platform dashboard"""
    try:
        # Calculate total platform revenue (completed jobs)
        completed_jobs = Job.query.filter_by(status=JobStatus.COMPLETED).all()
        total_revenue = sum(float(job.final_price or 0) for job in completed_jobs)
        total_commission = sum(float(job.commission_amount or 0) for job in completed_jobs)
        
        # Get monthly revenue for the last 12 months
        monthly_revenue = []
        for i in range(12):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_jobs = Job.query.filter(
                Job.status == JobStatus.COMPLETED,
                Job.completed_at >= month_start,
                Job.completed_at <= month_end
            ).all()
            
            month_total = sum(float(job.final_price or 0) for job in month_jobs)
            monthly_revenue.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': month_total,
                'jobs_count': len(month_jobs)
            })
        
        monthly_revenue.reverse()  # Show oldest to newest
        
        return jsonify({
            'financial_summary': {
                'total_revenue': total_revenue,
                'total_commission': total_commission,
                'completed_jobs_count': len(completed_jobs),
                'average_job_value': total_revenue / len(completed_jobs) if completed_jobs else 0,
                'monthly_revenue': monthly_revenue
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

