"""
Utilities package initialization
"""

from .validation import InputValidator

# Create convenience functions
validate_email = InputValidator.validate_email
validate_password = InputValidator.validate_password
validate_required_fields = InputValidator.validate_required_fields

__all__ = [
    'InputValidator',
    'validate_email',
    'validate_password', 
    'validate_required_fields'
]

