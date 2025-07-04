"""
Comprehensive Error Boundary System for Biped Platform
Provides centralized error handling, logging, and user-friendly error responses
"""

import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, Tuple

from flask import current_app, jsonify, request


class ErrorBoundary:
    """Centralized error boundary for handling application errors"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Handle errors with proper logging and user-friendly responses

        Args:
            error: The exception that occurred
            context: Additional context information

        Returns:
            Tuple of (error_response, status_code)
        """
        # Extract error information
        error_type = type(error).__name__
        error_message = str(error)
        error_traceback = traceback.format_exc()

        # Create error context
        error_context = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "request_method": getattr(request, "method", "Unknown"),
            "request_url": getattr(request, "url", "Unknown"),
            "user_agent": str(getattr(request, "user_agent", "Unknown")),
            "remote_addr": getattr(request, "remote_addr", "Unknown"),
        }

        if context:
            error_context.update(context)

        # Log the error
        self.logger.error(
            f"Error in {error_context['request_method']} {error_context['request_url']}: "
            f"{error_type}: {error_message}",
            extra={"error_context": error_context, "traceback": error_traceback},
        )

        # Determine response based on error type
        if isinstance(error, ValidationError):
            return self._handle_validation_error(error, error_context)
        elif isinstance(error, AuthenticationError):
            return self._handle_authentication_error(error, error_context)
        elif isinstance(error, AuthorizationError):
            return self._handle_authorization_error(error, error_context)
        elif isinstance(error, NotFoundError):
            return self._handle_not_found_error(error, error_context)
        elif isinstance(error, RateLimitError):
            return self._handle_rate_limit_error(error, error_context)
        elif isinstance(error, DatabaseError):
            return self._handle_database_error(error, error_context)
        elif isinstance(error, ExternalServiceError):
            return self._handle_external_service_error(error, error_context)
        else:
            return self._handle_generic_error(error, error_context)

    def _handle_validation_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Handle validation errors"""
        return {
            "error": "validation_error",
            "message": "Invalid input data",
            "details": str(error),
            "timestamp": context["timestamp"],
        }, 400

    def _handle_authentication_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Handle authentication errors"""
        return {
            "error": "authentication_error",
            "message": "Authentication required",
            "details": "Please log in to access this resource",
            "timestamp": context["timestamp"],
        }, 401

    def _handle_authorization_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Handle authorization errors"""
        return {
            "error": "authorization_error",
            "message": "Access denied",
            "details": "You don't have permission to access this resource",
            "timestamp": context["timestamp"],
        }, 403

    def _handle_not_found_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Handle not found errors"""
        return {
            "error": "not_found",
            "message": "Resource not found",
            "details": str(error),
            "timestamp": context["timestamp"],
        }, 404

    def _handle_rate_limit_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Handle rate limit errors"""
        return {
            "error": "rate_limit_exceeded",
            "message": "Too many requests",
            "details": "Please wait before making another request",
            "timestamp": context["timestamp"],
        }, 429

    def _handle_database_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Handle database errors"""
        return {
            "error": "database_error",
            "message": "Database operation failed",
            "details": "Please try again later",
            "timestamp": context["timestamp"],
        }, 500

    def _handle_external_service_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Handle external service errors"""
        return {
            "error": "external_service_error",
            "message": "External service unavailable",
            "details": "Please try again later",
            "timestamp": context["timestamp"],
        }, 503

    def _handle_generic_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Handle generic errors"""
        # Don't expose internal error details in production
        if current_app.config.get("DEBUG", False):
            details = str(error)
        else:
            details = "An unexpected error occurred"

        return {
            "error": "internal_error",
            "message": "Internal server error",
            "details": details,
            "timestamp": context["timestamp"],
        }, 500


# Custom Exception Classes
class ValidationError(Exception):
    """Raised when input validation fails"""

    pass


class AuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class AuthorizationError(Exception):
    """Raised when authorization fails"""

    pass


class NotFoundError(Exception):
    """Raised when a resource is not found"""

    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""

    pass


class DatabaseError(Exception):
    """Raised when database operations fail"""

    pass


class ExternalServiceError(Exception):
    """Raised when external service calls fail"""

    pass


# Decorator for automatic error handling
def handle_errors(context: Optional[Dict[str, Any]] = None):
    """
    Decorator to automatically handle errors in route functions

    Args:
        context: Additional context to include in error logs
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            error_boundary = ErrorBoundary()
            try:
                return f(*args, **kwargs)
            except Exception as e:
                error_response, status_code = error_boundary.handle_error(e, context)
                return jsonify(error_response), status_code

        return decorated_function

    return decorator


# Global error boundary instance
error_boundary = ErrorBoundary()


def register_error_handlers(app):
    """Register global error handlers for the Flask app"""

    @app.errorhandler(400)
    def handle_bad_request(error):
        response, status_code = error_boundary.handle_error(
            ValidationError("Bad request"), {"error_code": 400}
        )
        return jsonify(response), status_code

    @app.errorhandler(401)
    def handle_unauthorized(error):
        response, status_code = error_boundary.handle_error(
            AuthenticationError("Unauthorized"), {"error_code": 401}
        )
        return jsonify(response), status_code

    @app.errorhandler(403)
    def handle_forbidden(error):
        response, status_code = error_boundary.handle_error(
            AuthorizationError("Forbidden"), {"error_code": 403}
        )
        return jsonify(response), status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        response, status_code = error_boundary.handle_error(
            NotFoundError("Not found"), {"error_code": 404}
        )
        return jsonify(response), status_code

    @app.errorhandler(429)
    def handle_rate_limit(error):
        response, status_code = error_boundary.handle_error(
            RateLimitError("Rate limit exceeded"), {"error_code": 429}
        )
        return jsonify(response), status_code

    @app.errorhandler(500)
    def handle_internal_error(error):
        response, status_code = error_boundary.handle_error(
            Exception("Internal server error"), {"error_code": 500}
        )
        return jsonify(response), status_code

    @app.errorhandler(503)
    def handle_service_unavailable(error):
        response, status_code = error_boundary.handle_error(
            ExternalServiceError("Service unavailable"), {"error_code": 503}
        )
        return jsonify(response), status_code
