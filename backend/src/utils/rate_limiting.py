"""
Rate limiting utilities for TradeHub Platform
Provides basic rate limiting to protect API endpoints from abuse
"""

import hashlib
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, Optional

from flask import g, jsonify, request


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        # In-memory storage for rate limiting (use Redis in production)
        self.requests = {}

    def _get_client_id(self) -> str:
        """Get unique client identifier"""
        # Use IP address as identifier (enhance with user ID when available)
        client_ip = request.remote_addr or "unknown"
        return hashlib.md5(client_ip.encode()).hexdigest()

    def _clean_old_requests(self, client_id: str, window_start: datetime):
        """Remove requests older than the time window"""
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id] if req_time > window_start
            ]

    def is_allowed(self, max_requests: int = 100, window_minutes: int = 15) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)
        client_id = self._get_client_id()

        # Clean old requests
        self._clean_old_requests(client_id, window_start)

        # Initialize client if not exists
        if client_id not in self.requests:
            self.requests[client_id] = []

        # Check if limit exceeded
        if len(self.requests[client_id]) >= max_requests:
            return False

        # Add current request
        self.requests[client_id].append(now)
        return True

    def get_remaining_requests(self, max_requests: int = 100, window_minutes: int = 15) -> int:
        """Get number of remaining requests in current window"""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)
        client_id = self._get_client_id()

        self._clean_old_requests(client_id, window_start)

        if client_id not in self.requests:
            return max_requests

        return max(0, max_requests - len(self.requests[client_id]))


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 100, window_minutes: int = 15):
    """
    Decorator for rate limiting endpoints

    Args:
        max_requests: Maximum number of requests allowed in the window
        window_minutes: Time window in minutes
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not rate_limiter.is_allowed(max_requests, window_minutes):
                return (
                    jsonify(
                        {
                            "error": "Rate limit exceeded",
                            "message": f"Maximum {max_requests} requests per {window_minutes} minutes allowed",
                            "retry_after": window_minutes * 60,  # seconds
                        }
                    ),
                    429,
                )

            # Add rate limit headers
            remaining = rate_limiter.get_remaining_requests(max_requests, window_minutes)
            response = f(*args, **kwargs)

            # Add headers if response is a tuple (response, status_code)
            if isinstance(response, tuple):
                response_data, status_code = response
                if hasattr(response_data, "headers"):
                    response_data.headers["X-RateLimit-Limit"] = str(max_requests)
                    response_data.headers["X-RateLimit-Remaining"] = str(remaining)
                    response_data.headers["X-RateLimit-Reset"] = str(window_minutes * 60)
                return response_data, status_code

            return response

        return decorated_function

    return decorator


# Common rate limit configurations
def strict_rate_limit(f):
    """Strict rate limiting: 30 requests per 10 minutes"""
    return rate_limit(30, 10)(f)


def auth_rate_limit(f):
    """Authentication rate limiting: 10 requests per 5 minutes"""
    return rate_limit(10, 5)(f)


def api_rate_limit(f):
    """General API rate limiting: 100 requests per 15 minutes"""
    return rate_limit(100, 15)(f)
