from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import os

admin_auth_bp = Blueprint('admin_auth', __name__)

# Platform owner email - this should be configurable
PLATFORM_OWNER_EMAIL = "braden.lang77@gmail.com"

@admin_auth_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login endpoint for platform owner"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Check if this is the platform owner email
        if email != PLATFORM_OWNER_EMAIL:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Find the user in the database
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'Admin account not found'}), 404
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user has admin privileges (you might want to add an is_admin field)
        if user.email != PLATFORM_OWNER_EMAIL:
            return jsonify({'error': 'Insufficient privileges'}), 403
        
        # Create admin session
        session['admin_user_id'] = user.id
        session['admin_email'] = user.email
        session['is_admin'] = True
        session['admin_login_time'] = datetime.utcnow().isoformat()
        
        # Set session timeout based on remember_me
        if remember_me:
            session.permanent = True
        else:
            session.permanent = False
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Admin login successful',
            'admin': {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
                'login_time': session['admin_login_time']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_auth_bp.route('/logout', methods=['POST'])
def admin_logout():
    """Admin logout endpoint"""
    try:
        # Clear admin session
        session.pop('admin_user_id', None)
        session.pop('admin_email', None)
        session.pop('is_admin', None)
        session.pop('admin_login_time', None)
        
        return jsonify({'message': 'Admin logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_auth_bp.route('/me', methods=['GET'])
def admin_me():
    """Get current admin user info"""
    try:
        admin_user_id = session.get('admin_user_id')
        is_admin = session.get('is_admin', False)
        
        if not admin_user_id or not is_admin:
            return jsonify({'error': 'Not authenticated as admin'}), 401
        
        user = User.query.get(admin_user_id)
        if not user or user.email != PLATFORM_OWNER_EMAIL:
            return jsonify({'error': 'Admin user not found'}), 404
        
        return jsonify({
            'admin': {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
                'login_time': session.get('admin_login_time'),
                'is_platform_owner': user.email == PLATFORM_OWNER_EMAIL
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_auth_bp.route('/stats', methods=['GET'])
def admin_stats():
    """Get platform statistics for admin dashboard"""
    try:
        admin_user_id = session.get('admin_user_id')
        is_admin = session.get('is_admin', False)
        
        if not admin_user_id or not is_admin:
            return jsonify({'error': 'Not authenticated as admin'}), 401
        
        # Get platform statistics
        from src.models.job import Job, JobStatus
        from src.models.financial import Invoice, Payment
        from sqlalchemy import func, and_
        
        # User statistics
        total_users = User.query.count()
        customers = User.query.filter_by(user_type='customer').count()
        providers = User.query.filter_by(user_type='provider').count()
        
        # Job statistics
        total_jobs = Job.query.count()
        active_jobs = Job.query.filter(Job.status.in_([
            JobStatus.POSTED, JobStatus.MATCHED, JobStatus.ACCEPTED, JobStatus.IN_PROGRESS
        ])).count()
        completed_jobs = Job.query.filter_by(status=JobStatus.COMPLETED).count()
        
        # Revenue statistics
        total_revenue = db.session.query(func.sum(Job.final_price)).filter(
            Job.status == JobStatus.COMPLETED
        ).scalar() or 0
        
        platform_commission = db.session.query(func.sum(Job.commission_amount)).filter(
            Job.status == JobStatus.COMPLETED
        ).scalar() or 0
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_jobs = Job.query.filter(Job.created_at >= thirty_days_ago).count()
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        # Monthly revenue trend (last 6 months)
        revenue_trend = []
        for i in range(6):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            month_revenue = db.session.query(func.sum(Job.commission_amount)).filter(
                and_(
                    Job.completed_at >= month_start,
                    Job.completed_at <= month_end,
                    Job.status == JobStatus.COMPLETED
                )
            ).scalar() or 0
            
            revenue_trend.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': float(month_revenue)
            })
        
        revenue_trend.reverse()  # Show oldest to newest
        
        return jsonify({
            'stats': {
                'users': {
                    'total': total_users,
                    'customers': customers,
                    'providers': providers,
                    'recent': recent_users
                },
                'jobs': {
                    'total': total_jobs,
                    'active': active_jobs,
                    'completed': completed_jobs,
                    'recent': recent_jobs
                },
                'revenue': {
                    'total': float(total_revenue),
                    'commission': float(platform_commission),
                    'trend': revenue_trend
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        admin_user_id = session.get('admin_user_id')
        is_admin = session.get('is_admin', False)
        
        if not admin_user_id or not is_admin:
            return jsonify({'error': 'Admin authentication required'}), 401
        
        # Verify admin user still exists and is valid
        user = User.query.get(admin_user_id)
        if not user or user.email != PLATFORM_OWNER_EMAIL:
            return jsonify({'error': 'Invalid admin session'}), 401
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

