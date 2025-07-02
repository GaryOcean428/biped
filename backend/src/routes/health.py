"""
Health monitoring endpoints for TradeHub Platform
Provides comprehensive health checks and monitoring capabilities
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from src.models.user import db, User
from src.models.job import Job
from src.models.service import ServiceCategory
from src.utils.error_handling import handle_errors, app_logger
from src.utils.rate_limiting import api_rate_limit
import os
import sys
import psutil
import time

health_bp = Blueprint('health', __name__)

# Global health metrics
health_metrics = {
    'start_time': datetime.utcnow(),
    'request_count': 0,
    'error_count': 0,
    'last_error': None
}


@health_bp.before_request
def track_request():
    """Track request metrics"""
    health_metrics['request_count'] += 1


@health_bp.route('/health', methods=['GET'])
@api_rate_limit
def health_check():
    """Basic health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'TradeHub Platform API',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'uptime_seconds': (datetime.utcnow() - health_metrics['start_time']).total_seconds()
        }), 200
    except Exception as e:
        health_metrics['error_count'] += 1
        health_metrics['last_error'] = str(e)
        app_logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Health check failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@health_bp.route('/health/detailed', methods=['GET'])
@api_rate_limit
@handle_errors(app_logger)
def detailed_health_check():
    """Detailed health check with system metrics"""
    try:
        # Database health check
        db_healthy = True
        db_latency = None
        db_error = None
        
        try:
            start_time = time.time()
            db.session.execute('SELECT 1')
            db_latency = round((time.time() - start_time) * 1000, 2)  # ms
        except Exception as e:
            db_healthy = False
            db_error = str(e)
            app_logger.error(f"Database health check failed: {e}")
        
        # System metrics
        system_metrics = {}
        try:
            system_metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except Exception as e:
            app_logger.warning(f"Could not get system metrics: {e}")
        
        # Application metrics
        uptime = datetime.utcnow() - health_metrics['start_time']
        
        # Data integrity checks
        data_checks = {}
        try:
            data_checks = {
                'total_users': User.query.count(),
                'active_users': User.query.filter_by(is_active=True).count(),
                'total_jobs': Job.query.count(),
                'service_categories': ServiceCategory.query.count()
            }
        except Exception as e:
            app_logger.error(f"Data integrity check failed: {e}")
            data_checks['error'] = str(e)
        
        # Overall health status
        overall_status = 'healthy'
        if not db_healthy:
            overall_status = 'unhealthy'
        elif system_metrics.get('cpu_percent', 0) > 90 or system_metrics.get('memory_percent', 0) > 90:
            overall_status = 'degraded'
        elif health_metrics['error_count'] > 100:  # Too many errors
            overall_status = 'degraded'
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'TradeHub Platform API',
            'version': '1.0.0',
            'uptime': {
                'seconds': uptime.total_seconds(),
                'human_readable': str(uptime).split('.')[0]  # Remove microseconds
            },
            'database': {
                'healthy': db_healthy,
                'latency_ms': db_latency,
                'error': db_error
            },
            'system': system_metrics,
            'application': {
                'request_count': health_metrics['request_count'],
                'error_count': health_metrics['error_count'],
                'error_rate': round(health_metrics['error_count'] / max(health_metrics['request_count'], 1) * 100, 2),
                'last_error': health_metrics['last_error'],
                'python_version': sys.version
            },
            'data_integrity': data_checks
        }), 200
        
    except Exception as e:
        health_metrics['error_count'] += 1
        health_metrics['last_error'] = str(e)
        app_logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Detailed health check failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@health_bp.route('/health/ready', methods=['GET'])
@api_rate_limit
def readiness_check():
    """Readiness check for load balancers"""
    try:
        # Check if essential services are ready
        ready = True
        checks = {}
        
        # Database readiness
        try:
            db.session.execute('SELECT 1')
            checks['database'] = 'ready'
        except Exception as e:
            ready = False
            checks['database'] = f'not ready: {str(e)}'
        
        # Check if essential data exists
        try:
            if ServiceCategory.query.count() == 0:
                ready = False
                checks['service_categories'] = 'not ready: no service categories'
            else:
                checks['service_categories'] = 'ready'
        except Exception as e:
            ready = False
            checks['service_categories'] = f'not ready: {str(e)}'
        
        status_code = 200 if ready else 503
        return jsonify({
            'ready': ready,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }), status_code
        
    except Exception as e:
        app_logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'ready': False,
            'error': 'Readiness check failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@health_bp.route('/health/live', methods=['GET'])
@api_rate_limit
def liveness_check():
    """Liveness check for container orchestration"""
    try:
        # Simple liveness check - if we can respond, we're alive
        return jsonify({
            'alive': True,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'TradeHub Platform API'
        }), 200
    except Exception as e:
        app_logger.error(f"Liveness check failed: {e}")
        return jsonify({
            'alive': False,
            'error': 'Liveness check failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@health_bp.route('/health/metrics', methods=['GET'])
@api_rate_limit
@handle_errors(app_logger)
def metrics_endpoint():
    """Metrics endpoint for monitoring systems"""
    try:
        uptime = datetime.utcnow() - health_metrics['start_time']
        
        # Get database metrics
        db_metrics = {}
        try:
            db_metrics = {
                'total_users': User.query.count(),
                'active_users': User.query.filter_by(is_active=True).count(),
                'total_jobs': Job.query.count(),
                'recent_jobs': Job.query.filter(
                    Job.created_at > datetime.utcnow() - timedelta(days=7)
                ).count()
            }
        except Exception as e:
            app_logger.error(f"Database metrics failed: {e}")
            db_metrics['error'] = str(e)
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'requests': {
                'total': health_metrics['request_count'],
                'errors': health_metrics['error_count'],
                'error_rate': round(health_metrics['error_count'] / max(health_metrics['request_count'], 1) * 100, 2)
            },
            'database': db_metrics,
            'system': {
                'python_version': sys.version,
                'platform': sys.platform
            }
        }), 200
        
    except Exception as e:
        health_metrics['error_count'] += 1
        health_metrics['last_error'] = str(e)
        app_logger.error(f"Metrics endpoint failed: {e}")
        return jsonify({
            'error': 'Metrics collection failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# Error handler for health blueprint
@health_bp.errorhandler(Exception)
def handle_health_error(error):
    """Handle errors in health endpoints"""
    health_metrics['error_count'] += 1
    health_metrics['last_error'] = str(error)
    app_logger.error(f"Health endpoint error: {error}")
    
    return jsonify({
        'error': 'Health check failed',
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'unhealthy'
    }), 503