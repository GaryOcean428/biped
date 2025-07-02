"""
Security utilities for TradeHub Platform
Provides enterprise-grade security features including headers, CSRF protection, and JWT enhancements
"""
from functools import wraps
from flask import request, jsonify, current_app
import secrets
import hashlib
import time
from typing import Dict, Optional, Any
import jwt
from datetime import datetime, timedelta, timezone


class SecurityHeaders:
    """Security headers middleware for enhanced protection"""
    
    @staticmethod
    def apply_security_headers(response):
        """Apply comprehensive security headers to response"""
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        # Additional security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS - only in production with HTTPS
        if current_app.config.get('HTTPS_ENABLED', False):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class CSRFProtection:
    """CSRF protection for forms and API endpoints"""
    
    def __init__(self):
        self.tokens = {}  # In production, use Redis or database
        self.token_expiry = 3600  # 1 hour
    
    def generate_token(self, user_id: str = None) -> str:
        """Generate CSRF token for user/session"""
        token = secrets.token_urlsafe(32)
        key = user_id or request.remote_addr or 'anonymous'
        
        self.tokens[key] = {
            'token': token,
            'expires': time.time() + self.token_expiry
        }
        
        return token
    
    def validate_token(self, token: str, user_id: str = None) -> bool:
        """Validate CSRF token"""
        if not token:
            return False
        
        key = user_id or request.remote_addr or 'anonymous'
        
        if key not in self.tokens:
            return False
        
        stored_data = self.tokens[key]
        
        # Check expiry
        if time.time() > stored_data['expires']:
            del self.tokens[key]
            return False
        
        # Validate token
        return secrets.compare_digest(stored_data['token'], token)
    
    def require_csrf_token(self, f):
        """Decorator to require CSRF token for endpoint"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            
            if not self.validate_token(token):
                return jsonify({'error': 'Invalid CSRF token'}), 403
            
            return f(*args, **kwargs)
        return decorated_function


class EnhancedJWT:
    """Enhanced JWT utilities with security best practices"""
    
    @staticmethod
    def generate_token(user_id: str, user_type: str, expires_in: int = 3600) -> str:
        """Generate JWT token with enhanced security"""
        now = datetime.now(timezone.utc)
        payload = {
            'user_id': user_id,
            'user_type': user_type,
            'iat': now,
            'exp': now + timedelta(seconds=expires_in),
            'jti': secrets.token_urlsafe(16),  # JWT ID for revocation
            'aud': 'tradehub-api',  # Audience
            'iss': 'tradehub-platform'  # Issuer
        }
        
        secret = current_app.config.get('JWT_SECRET_KEY', current_app.config['SECRET_KEY'])
        return jwt.encode(payload, secret, algorithm='HS256')
    
    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token with enhanced checks"""
        try:
            secret = current_app.config.get('JWT_SECRET_KEY', current_app.config['SECRET_KEY'])
            payload = jwt.decode(
                token, 
                secret, 
                algorithms=['HS256'],
                audience='tradehub-api',
                issuer='tradehub-platform'
            )
            
            # Additional validation
            if 'user_id' not in payload or 'user_type' not in payload:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def require_auth(allowed_types: list = None):
        """Decorator to require JWT authentication"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                token = request.headers.get('Authorization')
                
                if not token or not token.startswith('Bearer '):
                    return jsonify({'error': 'Authentication required'}), 401
                
                token = token.split(' ')[1]
                payload = EnhancedJWT.validate_token(token)
                
                if not payload:
                    return jsonify({'error': 'Invalid token'}), 401
                
                if allowed_types and payload.get('user_type') not in allowed_types:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Add user info to request context
                request.current_user = payload
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator


class InputSanitizer:
    """Advanced input sanitization beyond basic validation"""
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """Sanitize input to prevent SQL injection attempts"""
        if not isinstance(value, str):
            return str(value)
        
        # Remove common SQL injection patterns
        dangerous_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(--|\#|\/\*|\*\/)',
            r'(\bOR\b.*\b=\b|\bAND\b.*\b=\b)',
            r'(\bSCRIPT\b|\bEXEC\b|\bEXECUTE\b)'
        ]
        
        import re
        sanitized = value
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_file_path(path: str) -> str:
        """Sanitize file path to prevent directory traversal"""
        if not isinstance(path, str):
            return ''
        
        # Remove directory traversal attempts
        sanitized = path.replace('..', '').replace('\\', '').replace('//', '/')
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        return sanitized.strip()


# Global instances
security_headers = SecurityHeaders()
csrf_protection = CSRFProtection()
input_sanitizer = InputSanitizer()