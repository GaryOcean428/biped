"""
Input Validation and Sanitization Utilities for Biped Platform
Provides secure input handling to prevent XSS, SQL injection, and other attacks
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # Common patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 format
    POSTCODE_AU_PATTERN = re.compile(r'^\d{4}$')  # Australian postcodes
    
    # Allowed characters for different input types
    SAFE_TEXT_CHARS = re.compile(r'^[a-zA-Z0-9\s\.,!?\-\'\"()]+$')
    SAFE_NAME_CHARS = re.compile(r'^[a-zA-Z\s\-\'\.]+$')
    ALPHANUMERIC_ONLY = re.compile(r'^[a-zA-Z0-9]+$')
    
    # Maximum lengths for different fields
    MAX_LENGTHS = {
        'name': 100,
        'email': 255,
        'phone': 20,
        'address': 255,
        'description': 2000,
        'title': 200,
        'message': 1000
    }
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove potentially dangerous HTML/script content"""
        if not isinstance(text, str):
            return str(text)
        
        # Escape HTML entities
        sanitized = html.escape(text)
        
        # Remove any remaining script tags or javascript
        script_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<\s*iframe',
            r'<\s*object',
            r'<\s*embed'
        ]
        
        for pattern in script_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > InputValidator.MAX_LENGTHS['email']:
            return False
        return bool(InputValidator.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number (Australian format preferred)"""
        if not phone:
            return False
        
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Australian mobile: starts with 04 or +614
        au_mobile = re.match(r'^(\+61|0)?4\d{8}$', cleaned)
        # Australian landline: starts with 0[2-8] or +61[2-8]
        au_landline = re.match(r'^(\+61|0)?[2-8]\d{8}$', cleaned)
        
        return bool(au_mobile or au_landline or InputValidator.PHONE_PATTERN.match(cleaned))
    
    @staticmethod
    def validate_postcode(postcode: str) -> bool:
        """Validate Australian postcode"""
        if not postcode:
            return False
        return bool(InputValidator.POSTCODE_AU_PATTERN.match(postcode.strip()))
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate person/business name"""
        if not name or len(name) > InputValidator.MAX_LENGTHS['name']:
            return False
        return bool(InputValidator.SAFE_NAME_CHARS.match(name.strip()))
    
    @staticmethod
    def validate_text_content(text: str, field_type: str = 'description') -> bool:
        """Validate general text content"""
        if not text:
            return False
        
        max_length = InputValidator.MAX_LENGTHS.get(field_type, 1000)
        if len(text) > max_length:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'on\w+\s*=',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and safety"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Only allow http/https
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Block localhost and private IPs in production
            blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '10.', '172.', '192.168.']
            if any(parsed.netloc.startswith(host) for host in blocked_hosts):
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def validate_job_budget(budget_min: Union[int, float], budget_max: Union[int, float]) -> bool:
        """Validate job budget range"""
        try:
            min_val = float(budget_min)
            max_val = float(budget_max)
            
            # Reasonable budget ranges for Australian market
            if min_val < 0 or max_val < 0:
                return False
            
            if min_val > max_val:
                return False
            
            # Maximum reasonable budget (can be adjusted)
            if max_val > 100000:  # $100k max
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def validate_job_posting(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete job posting data"""
        errors = {}
        
        # Required fields
        required_fields = ['title', 'description', 'category', 'location']
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f"{field.title()} is required"
        
        # Validate specific fields
        if 'title' in data:
            if not cls.validate_text_content(data['title'], 'title'):
                errors['title'] = "Invalid title format"
        
        if 'description' in data:
            if not cls.validate_text_content(data['description'], 'description'):
                errors['description'] = "Invalid description format"
        
        if 'budget_min' in data and 'budget_max' in data:
            if not cls.validate_job_budget(data['budget_min'], data['budget_max']):
                errors['budget'] = "Invalid budget range"
        
        if 'email' in data:
            if not cls.validate_email(data['email']):
                errors['email'] = "Invalid email format"
        
        if 'phone' in data:
            if not cls.validate_phone(data['phone']):
                errors['phone'] = "Invalid phone number format"
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'sanitized_data': {
                key: cls.sanitize_html(value) if isinstance(value, str) else value
                for key, value in data.items()
            }
        }
    
    @classmethod
    def validate_user_registration(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user registration data"""
        errors = {}
        
        # Required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f"{field.replace('_', ' ').title()} is required"
        
        # Validate specific fields
        if 'email' in data:
            if not cls.validate_email(data['email']):
                errors['email'] = "Invalid email format"
        
        if 'first_name' in data:
            if not cls.validate_name(data['first_name']):
                errors['first_name'] = "Invalid first name format"
        
        if 'last_name' in data:
            if not cls.validate_name(data['last_name']):
                errors['last_name'] = "Invalid last name format"
        
        if 'phone' in data and data['phone']:
            if not cls.validate_phone(data['phone']):
                errors['phone'] = "Invalid phone number format"
        
        if 'password' in data:
            password_validation = cls.validate_password_strength(data['password'])
            if not password_validation['valid']:
                errors['password'] = password_validation['message']
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'sanitized_data': {
                key: cls.sanitize_html(value) if isinstance(value, str) and key != 'password' else value
                for key, value in data.items()
            }
        }
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        if not password:
            return {'valid': False, 'message': 'Password is required'}
        
        if len(password) < 8:
            return {'valid': False, 'message': 'Password must be at least 8 characters long'}
        
        if len(password) > 128:
            return {'valid': False, 'message': 'Password must be less than 128 characters'}
        
        # Check for at least one of each type
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        strength_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength_score < 3:
            return {
                'valid': False, 
                'message': 'Password must contain at least 3 of: uppercase, lowercase, numbers, special characters'
            }
        
        # Check for common weak passwords
        common_weak = ['password', '12345678', 'qwerty123', 'abc123456']
        if password.lower() in common_weak:
            return {'valid': False, 'message': 'Password is too common'}
        
        return {'valid': True, 'message': 'Password is strong', 'strength': strength_score}

# Convenience function for quick validation
def validate_and_sanitize(data: Dict[str, Any], validation_type: str = 'general') -> Dict[str, Any]:
    """Quick validation and sanitization wrapper"""
    
    if validation_type == 'job_posting':
        return InputValidator.validate_job_posting(data)
    elif validation_type == 'user_registration':
        return InputValidator.validate_user_registration(data)
    else:
        # General sanitization
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = InputValidator.sanitize_html(value)
            else:
                sanitized[key] = value
        
        return {
            'valid': True,
            'errors': {},
            'sanitized_data': sanitized
        }