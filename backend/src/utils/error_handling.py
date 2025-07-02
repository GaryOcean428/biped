"""
Error handling utilities for TradeHub Platform
Provides consistent error handling and logging across the application
"""
import logging
import traceback
from functools import wraps
from flask import jsonify, request, current_app
from typing import Dict, Any, Optional, Tuple


class ErrorHandler:
    """Centralized error handling utility"""
    
    @staticmethod
    def setup_logging():
        """Configure application logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('app.log', mode='a')
            ]
        )
        
        # Create logger for the application
        logger = logging.getLogger('tradehub')
        return logger
    
    @staticmethod
    def log_error(logger: logging.Logger, error: Exception, context: str = ""):
        """Log error with context information"""
        error_msg = f"{context}: {str(error)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
    
    @staticmethod
    def create_error_response(message: str, status_code: int = 500, error_type: str = "error") -> Tuple[Dict[str, Any], int]:
        """Create standardized error response"""
        return {
            'error': message,
            'error_type': error_type,
            'timestamp': request.method + ' ' + request.path if request else 'unknown',
            'status_code': status_code
        }, status_code
    
    @staticmethod
    def handle_validation_error(error_message: str) -> Tuple[Dict[str, Any], int]:
        """Handle validation errors"""
        return ErrorHandler.create_error_response(
            error_message, 
            400, 
            "validation_error"
        )
    
    @staticmethod
    def handle_authentication_error(error_message: str = "Authentication required") -> Tuple[Dict[str, Any], int]:
        """Handle authentication errors"""
        return ErrorHandler.create_error_response(
            error_message, 
            401, 
            "authentication_error"
        )
    
    @staticmethod
    def handle_authorization_error(error_message: str = "Insufficient permissions") -> Tuple[Dict[str, Any], int]:
        """Handle authorization errors"""
        return ErrorHandler.create_error_response(
            error_message, 
            403, 
            "authorization_error"
        )
    
    @staticmethod
    def handle_not_found_error(resource: str = "Resource") -> Tuple[Dict[str, Any], int]:
        """Handle not found errors"""
        return ErrorHandler.create_error_response(
            f"{resource} not found", 
            404, 
            "not_found_error"
        )
    
    @staticmethod
    def handle_server_error(error_message: str = "Internal server error") -> Tuple[Dict[str, Any], int]:
        """Handle server errors"""
        return ErrorHandler.create_error_response(
            error_message, 
            500, 
            "server_error"
        )


def handle_errors(logger: Optional[logging.Logger] = None):
    """
    Decorator to handle errors in API endpoints
    
    Args:
        logger: Optional logger instance
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ValueError as e:
                if logger:
                    ErrorHandler.log_error(logger, e, f"Validation error in {f.__name__}")
                return jsonify(ErrorHandler.handle_validation_error(str(e))[0]), 400
            except PermissionError as e:
                if logger:
                    ErrorHandler.log_error(logger, e, f"Permission error in {f.__name__}")
                return jsonify(ErrorHandler.handle_authorization_error(str(e))[0]), 403
            except FileNotFoundError as e:
                if logger:
                    ErrorHandler.log_error(logger, e, f"Not found error in {f.__name__}")
                return jsonify(ErrorHandler.handle_not_found_error(str(e))[0]), 404
            except Exception as e:
                if logger:
                    ErrorHandler.log_error(logger, e, f"Unexpected error in {f.__name__}")
                return jsonify(ErrorHandler.handle_server_error("An unexpected error occurred")[0]), 500
        return decorated_function
    return decorator


def create_success_response(data: Any, message: str = "Success", status_code: int = 200) -> Tuple[Dict[str, Any], int]:
    """Create standardized success response"""
    return {
        'success': True,
        'message': message,
        'data': data,
        'timestamp': request.method + ' ' + request.path if request else 'unknown'
    }, status_code


# Global logger instance
app_logger = ErrorHandler.setup_logging()