"""
Input validation utilities for TradeHub Platform
Provides comprehensive validation for API endpoints to prevent security vulnerabilities
"""
import re
from typing import Dict, Any, List, Tuple, Optional
from flask import request


class InputValidator:
    """Comprehensive input validation utility"""
    
    # Common regex patterns
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^\+?1?-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$'
    PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate that all required fields are present and not empty"""
        if not isinstance(data, dict):
            return False, "Invalid data format - expected JSON object"
        
        for field in required_fields:
            if field not in data or data[field] is None or str(data[field]).strip() == '':
                return False, f"Field '{field}' is required"
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email format"""
        if not email or not isinstance(email, str):
            return False, "Email is required"
        
        if len(email) > 254:  # RFC 5321 limit
            return False, "Email address too long"
        
        if not re.match(InputValidator.EMAIL_PATTERN, email.strip()):
            return False, "Invalid email format"
        
        return True, None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, Optional[str]]:
        """Validate password strength"""
        if not password or not isinstance(password, str):
            return False, "Password is required"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:  # Prevent DoS
            return False, "Password too long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, None
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
        """Validate phone number format"""
        if not phone or not isinstance(phone, str):
            return False, "Phone number is required"
        
        phone = phone.strip()
        if not re.match(InputValidator.PHONE_PATTERN, phone):
            return False, "Invalid phone number format"
        
        return True, None
    
    @staticmethod
    def validate_string_length(text: str, field_name: str, min_length: int = 0, max_length: int = 255) -> Tuple[bool, Optional[str]]:
        """Validate string length"""
        if not isinstance(text, str):
            return False, f"{field_name} must be a string"
        
        text = text.strip()
        if len(text) < min_length:
            return False, f"{field_name} must be at least {min_length} characters long"
        
        if len(text) > max_length:
            return False, f"{field_name} must be no more than {max_length} characters long"
        
        return True, None
    
    @staticmethod
    def validate_user_type(user_type: str) -> Tuple[bool, Optional[str]]:
        """Validate user type"""
        valid_types = ['customer', 'provider']
        if user_type not in valid_types:
            return False, f"User type must be one of: {', '.join(valid_types)}"
        return True, None
    
    @staticmethod
    def validate_numeric_range(value: Any, field_name: str, min_val: float = None, max_val: float = None) -> Tuple[bool, Optional[str]]:
        """Validate numeric value within range"""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"
        
        if min_val is not None and num_value < min_val:
            return False, f"{field_name} must be at least {min_val}"
        
        if max_val is not None and num_value > max_val:
            return False, f"{field_name} must be no more than {max_val}"
        
        return True, None
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Basic HTML sanitization to prevent XSS"""
        if not isinstance(text, str):
            return str(text)
        
        # Remove potentially dangerous HTML tags
        dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<link', '<meta', '<style']
        sanitized = text
        
        for tag in dangerous_tags:
            sanitized = re.sub(f'{tag}[^>]*>', '', sanitized, flags=re.IGNORECASE)
        
        # Remove javascript: protocols
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def get_request_json() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Safely get JSON from request with validation"""
        try:
            if not request.is_json:
                return None, "Content-Type must be application/json"
            
            data = request.get_json()
            if data is None:
                return None, "Invalid JSON format"
            
            if not isinstance(data, dict):
                return None, "Request body must be a JSON object"
            
            return data, None
        except Exception as e:
            return None, f"Failed to parse JSON: {str(e)}"


def validate_registration_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Complete validation for user registration data"""
    validator = InputValidator()
    
    # Check required fields
    required_fields = ['email', 'password', 'first_name', 'last_name', 'user_type']
    is_valid, error = validator.validate_required_fields(data, required_fields)
    if not is_valid:
        return False, error
    
    # Validate email
    is_valid, error = validator.validate_email(data['email'])
    if not is_valid:
        return False, error
    
    # Validate password
    is_valid, error = validator.validate_password(data['password'])
    if not is_valid:
        return False, error
    
    # Validate names
    for field in ['first_name', 'last_name']:
        is_valid, error = validator.validate_string_length(data[field], field, 1, 50)
        if not is_valid:
            return False, error
    
    # Validate user type
    is_valid, error = validator.validate_user_type(data['user_type'])
    if not is_valid:
        return False, error
    
    # Sanitize text fields
    for field in ['first_name', 'last_name']:
        data[field] = validator.sanitize_html(data[field])
    
    return True, None