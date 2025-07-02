"""
Health Check Routes for Railway Deployment
Provides comprehensive system status for debugging
"""

from flask import Blueprint, jsonify
import sys
import os
from datetime import datetime
from ..utils.redis_client import redis_client
from ..models.user import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check for Railway deployment"""
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0',
        'environment': os.environ.get('ENVIRONMENT', 'development'),
        'checks': {}
    }
    
    # Check Python dependencies
    try:
        import pandas
        import numpy
        import sklearn
        import matplotlib
        import seaborn
        import plotly
        health_status['checks']['dependencies'] = {
            'status': 'healthy',
            'pandas': pandas.__version__,
            'numpy': numpy.__version__,
            'sklearn': sklearn.__version__,
            'matplotlib': matplotlib.__version__,
            'seaborn': seaborn.__version__,
            'plotly': plotly.__version__
        }
    except ImportError as e:
        health_status['checks']['dependencies'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Check Redis connection
    try:
        if redis_client and redis_client.is_connected():
            redis_client.redis_client.ping()
            health_status['checks']['redis'] = {
                'status': 'healthy',
                'connected': True,
                'url': os.environ.get('REDIS_URL', 'not_set')[:20] + '...' if os.environ.get('REDIS_URL') else 'not_set'
            }
        else:
            health_status['checks']['redis'] = {
                'status': 'degraded',
                'connected': False,
                'message': 'Redis not available, running in degraded mode'
            }
    except Exception as e:
        health_status['checks']['redis'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Check database connection
    try:
        # Test database connection using SQLAlchemy
        db.session.execute(db.text('SELECT 1')).scalar()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'connected': True,
            'url': os.environ.get('DATABASE_URL', 'not_set')[:30] + '...' if os.environ.get('DATABASE_URL') else 'not_set'
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'connected': False,
            'error': str(e)
        }
    
    # System information
    health_status['system'] = {
        'python_version': sys.version,
        'platform': sys.platform,
        'working_directory': os.getcwd(),
        'environment_variables': {
            'PORT': os.environ.get('PORT', 'not_set'),
            'ENVIRONMENT': os.environ.get('ENVIRONMENT', 'not_set'),
            'DEBUG': os.environ.get('DEBUG', 'not_set'),
            'DATA_DIR': os.environ.get('DATA_DIR', 'not_set'),
            'PYTHONPATH': os.environ.get('PYTHONPATH', 'not_set')
        }
    }
    
    # Determine overall status
    if any(check.get('status') == 'unhealthy' for check in health_status['checks'].values()):
        health_status['status'] = 'unhealthy'
        status_code = 503
    elif any(check.get('status') == 'degraded' for check in health_status['checks'].values()):
        health_status['status'] = 'degraded'
        status_code = 200
    else:
        status_code = 200
    
    return jsonify(health_status), status_code

@health_bp.route('/health/simple', methods=['GET'])
def simple_health_check():
    """Simple health check for Railway health monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@health_bp.route('/health/dependencies', methods=['GET'])
def dependencies_check():
    """Check all Python dependencies"""
    dependencies = {}
    
    required_packages = [
        'pandas', 'numpy', 'sklearn', 'matplotlib', 'seaborn', 'plotly',
        'flask', 'redis', 'celery', 'gunicorn', 'psycopg2', 'sqlalchemy'
    ]
    
    for package in required_packages:
        try:
            module = __import__(package)
            dependencies[package] = {
                'status': 'available',
                'version': getattr(module, '__version__', 'unknown')
            }
        except ImportError:
            dependencies[package] = {
                'status': 'missing',
                'error': f'Module {package} not found'
            }
    
    return jsonify({
        'dependencies': dependencies,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

