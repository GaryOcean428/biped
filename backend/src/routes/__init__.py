"""
Routes package initialization
Exports all route blueprints
"""

# Import all blueprints
from .unified_auth import auth_bp
from .admin import admin_bp  
from .dashboard import dashboard_bp
from .health import health_bp

# Create aliases for backward compatibility
auth = auth_bp

# Export all blueprints
__all__ = [
    'auth_bp',
    'auth',  # alias
    'admin_bp',
    'dashboard_bp', 
    'health_bp'
]

