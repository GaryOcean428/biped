"""
Rate Limiting for Biped Platform
Uses Flask-Limiter for robust rate limiting with backward compatibility
"""

import logging

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# Create Flask-Limiter instance
# Will be initialized with app in main.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://",  # Use memory storage for simplicity
    strategy="fixed-window",
)

# For backward compatibility - alias the limiter
rate_limiter = limiter
