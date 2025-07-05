"""
Routes package initialization
Exports all route blueprints
"""

from .admin import admin_bp
from .ai import ai_bp
from .dashboard import dashboard_bp
from .health import health_bp
from .jobs import jobs_bp
from .jobs_api import jobs_api_bp
from .legal import legal_bp

# Import all blueprints
from .unified_auth import auth_bp

# Create aliases for backward compatibility
auth = auth_bp

# Export all blueprints
__all__ = [
    "auth_bp",
    "auth",  # alias
    "admin_bp",
    "dashboard_bp",
    "health_bp",
    "jobs_bp",
    "jobs_api_bp",
    "legal_bp",
    "ai_bp",
]
