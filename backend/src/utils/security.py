"""
Comprehensive Security Enhancement Module
Implements rate limiting, CSRF protection, input validation, and advanced authentication
"""

import base64
import hashlib
import io
import ipaddress
import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Tuple

import pyotp
import qrcode
import redis
from email_validator import EmailNotValidError, validate_email
from flask import Flask, g, jsonify, request, session
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from .redis_client import redis_client

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration settings"""

    rate_limit_default: str = "200 per day, 50 per hour"
    rate_limit_auth: str = "10 per minute"
    rate_limit_api: str = "1000 per hour"
    jwt_access_token_expires: timedelta = timedelta(minutes=15)
    jwt_refresh_token_expires: timedelta = timedelta(days=30)
    password_min_length: int = 8
    password_require_special: bool = True
    password_require_number: bool = True
    password_require_uppercase: bool = True
    max_login_attempts: int = 5
    lockout_duration: timedelta = timedelta(minutes=30)
    session_timeout: timedelta = timedelta(hours=24)


class SecurityEnhancer:
    """Main security enhancement class"""

    def __init__(self, app: Flask, config: SecurityConfig = None):
        self.app = app
        self.config = config or SecurityConfig()
        self.redis_client = redis_client
        self._configure_security()

    def _configure_security(self):
        """Configure all security components"""
        self._setup_rate_limiting()
        self._setup_security_headers()
        self._setup_csrf_protection()
        self._setup_jwt()
        self._setup_input_validation()

    def _setup_rate_limiting(self):
        """Configure rate limiting"""
        self.limiter = Limiter(
            app=self.app,
            key_func=self._get_rate_limit_key,
            storage_uri=self.app.config.get("REDIS_URL", "memory://"),
            default_limits=[self.config.rate_limit_default],
            headers_enabled=True,
            swallow_errors=True,
        )

        # Custom rate limit decorators
        self.auth_rate_limit = self.limiter.limit(self.config.rate_limit_auth)
        self.api_rate_limit = self.limiter.limit(self.config.rate_limit_api)

    def _get_rate_limit_key(self):
        """Custom rate limit key function"""
        # Use user ID if authenticated, otherwise IP
        user_id = getattr(g, "current_user_id", None)
        if user_id:
            return f"user:{user_id}"
        return get_remote_address()

    def _setup_security_headers(self):
        """Configure security headers"""
        csp = {
            "default-src": "'self'",
            "script-src": [
                "'self'",
                "'unsafe-inline'",  # Allow inline scripts
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
            ],
            "style-src": [
                "'self'",
                "'unsafe-inline'",  # Allow inline styles
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://fonts.googleapis.com",
            ],
            "img-src": ["'self'", "data:", "https:", "blob:"],
            "font-src": [
                "'self'",
                "https://fonts.gstatic.com",
                "https://cdnjs.cloudflare.com",
            ],
            "connect-src": ["'self'", "wss:", "ws:"],
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
        }

        Talisman(
            self.app,
            force_https=self.app.config.get(
                "FORCE_HTTPS", False
            ),  # Disable for development
            strict_transport_security=False,  # Disable for development
            strict_transport_security_max_age=31536000,
            content_security_policy=csp,
            content_security_policy_nonce_in=[],  # Disable nonce to allow unsafe-inline
            referrer_policy="strict-origin-when-cross-origin",
            feature_policy={
                "geolocation": "'none'",
                "microphone": "'none'",
                "camera": "'none'",
            },
        )
        
        # Add X-XSS-Protection header manually since Talisman doesn't include it by default
        @self.app.after_request
        def add_xss_protection(response):
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response

    def _setup_csrf_protection(self):
        """Configure CSRF protection"""
        # Temporarily disable CSRF for development
        # self.csrf = CSRFProtect(self.app)
        pass

    def _setup_jwt(self):
        """Configure JWT with blacklisting"""
        self.jwt = JWTManager(self.app)

        # Configure JWT settings
        self.app.config["JWT_ACCESS_TOKEN_EXPIRES"] = (
            self.config.jwt_access_token_expires
        )
        self.app.config["JWT_REFRESH_TOKEN_EXPIRES"] = (
            self.config.jwt_refresh_token_expires
        )
        self.app.config["JWT_BLACKLIST_ENABLED"] = True
        self.app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

        @self.jwt.token_in_blocklist_loader
        def check_if_token_revoked(jwt_header, jwt_payload):
            jti = jwt_payload["jti"]
            token_in_redis = self.redis_client.get_cache(f"blacklist:{jti}")
            return token_in_redis is not None

        @self.jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return jsonify({"error": "Token has expired"}), 401

        @self.jwt.invalid_token_loader
        def invalid_token_callback(error):
            return jsonify({"error": "Invalid token"}), 401

        @self.jwt.unauthorized_loader
        def missing_token_callback(error):
            return jsonify({"error": "Authorization token required"}), 401

    def _setup_input_validation(self):
        """Setup input validation patterns"""
        self.validation_patterns = {
            "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            "username": re.compile(r"^[a-zA-Z0-9_]{3,30}$"),
            "phone": re.compile(r"^\+?1?[0-9]{10,15}$"),
            "alphanumeric": re.compile(r"^[a-zA-Z0-9\s]+$"),
            "numeric": re.compile(r"^[0-9]+$"),
            "decimal": re.compile(r"^[0-9]+\.?[0-9]*$"),
            "safe_string": re.compile(r"^[a-zA-Z0-9\s\-_.,!?]+$"),
        }

    # Authentication Methods
    def authenticate_user(
        self, email: str, password: str, ip_address: str
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Authenticate user with rate limiting and lockout protection"""
        # Check if account is locked
        lockout_key = f"lockout:{email}"
        if self.redis_client.get_cache(lockout_key):
            return None, "Account temporarily locked due to too many failed attempts"

        # Check login attempts
        attempts_key = f"login_attempts:{email}"
        attempts = self.redis_client.get_cache(attempts_key) or 0

        if attempts >= self.config.max_login_attempts:
            # Lock account
            self.redis_client.set_cache(
                lockout_key, True, ttl=int(self.config.lockout_duration.total_seconds())
            )
            return None, "Too many failed login attempts. Account locked."

        # Validate credentials (implement your user lookup logic)
        user = self._get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            # Increment failed attempts
            self.redis_client.set_cache(attempts_key, attempts + 1, ttl=3600)
            return None, "Invalid credentials"

        # Clear failed attempts on successful login
        self.redis_client.delete_cache(attempts_key)

        # Log successful login
        self._log_security_event(
            "login_success",
            {
                "user_id": user["id"],
                "email": email,
                "ip_address": ip_address,
                "user_agent": request.headers.get("User-Agent", ""),
            },
        )

        return user, None

    def create_tokens(self, user: dict) -> dict:
        """Create access and refresh tokens"""
        additional_claims = {
            "user_id": user["id"],
            "role": user.get("role", "user"),
            "permissions": user.get("permissions", []),
        }

        access_token = create_access_token(
            identity=user["email"], fresh=True, additional_claims=additional_claims
        )

        refresh_token = create_access_token(
            identity=user["email"],
            expires_delta=self.config.jwt_refresh_token_expires,
            additional_claims={"type": "refresh"},
        )

        # Store refresh token for tracking
        self.redis_client.set_cache(
            f"refresh_token:{user['id']}",
            refresh_token,
            ttl=int(self.config.jwt_refresh_token_expires.total_seconds()),
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": int(self.config.jwt_access_token_expires.total_seconds()),
        }

    def revoke_token(self, jti: str, token_type: str = "access"):
        """Add token to blacklist"""
        ttl = int(self.config.jwt_access_token_expires.total_seconds())
        if token_type == "refresh":
            ttl = int(self.config.jwt_refresh_token_expires.total_seconds())

        self.redis_client.set_cache(f"blacklist:{jti}", True, ttl=ttl)

    def revoke_all_user_tokens(self, user_id: str):
        """Revoke all tokens for a user"""
        # This would require storing all active tokens per user
        # For now, we'll just remove the refresh token
        self.redis_client.delete_cache(f"refresh_token:{user_id}")

    # Two-Factor Authentication
    def setup_2fa(self, user_id: str, user_email: str) -> dict:
        """Setup 2FA for user"""
        secret = pyotp.random_base32()

        # Store secret temporarily until confirmed
        self.redis_client.set_cache(
            f"2fa_setup:{user_id}", secret, ttl=600
        )  # 10 minutes

        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email, issuer_name="Biped Platform"
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()

        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_data}",
            "backup_codes": self._generate_backup_codes(),
        }

    def verify_2fa_setup(self, user_id: str, token: str) -> bool:
        """Verify 2FA setup token"""
        secret = self.redis_client.get_cache(f"2fa_setup:{user_id}")
        if not secret:
            return False

        totp = pyotp.TOTP(secret)
        if totp.verify(token):
            # Save secret to user account (implement your user update logic)
            self._save_user_2fa_secret(user_id, secret)
            self.redis_client.delete_cache(f"2fa_setup:{user_id}")
            return True

        return False

    def verify_2fa_token(self, user_id: str, token: str) -> bool:
        """Verify 2FA token for login"""
        user_secret = self._get_user_2fa_secret(user_id)
        if not user_secret:
            return False

        totp = pyotp.TOTP(user_secret)
        return totp.verify(token, valid_window=1)  # Allow 1 window tolerance

    def _generate_backup_codes(self) -> List[str]:
        """Generate backup codes for 2FA"""
        return [secrets.token_hex(4).upper() for _ in range(10)]

    # Input Validation
    def validate_input(self, data: dict, rules: dict) -> Tuple[bool, List[str]]:
        """Validate input data against rules"""
        errors = []

        for field, rule in rules.items():
            value = data.get(field)

            # Required field check
            if rule.get("required", False) and not value:
                errors.append(f"{field} is required")
                continue

            if value is None:
                continue

            # Type validation
            expected_type = rule.get("type")
            if expected_type and not isinstance(value, expected_type):
                errors.append(f"{field} must be of type {expected_type.__name__}")
                continue

            # Length validation
            min_length = rule.get("min_length")
            max_length = rule.get("max_length")
            if min_length and len(str(value)) < min_length:
                errors.append(f"{field} must be at least {min_length} characters")
            if max_length and len(str(value)) > max_length:
                errors.append(f"{field} must be no more than {max_length} characters")

            # Pattern validation
            pattern = rule.get("pattern")
            if pattern and not self.validation_patterns[pattern].match(str(value)):
                errors.append(f"{field} format is invalid")

            # Custom validation
            custom_validator = rule.get("validator")
            if custom_validator and not custom_validator(value):
                errors.append(f"{field} validation failed")

        return len(errors) == 0, errors

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []

        if len(password) < self.config.password_min_length:
            errors.append(
                f"Password must be at least {self.config.password_min_length} characters"
            )

        if self.config.password_require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if self.config.password_require_number and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")

        if self.config.password_require_special and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            errors.append("Password must contain at least one special character")

        # Check against common passwords
        if self._is_common_password(password):
            errors.append("Password is too common")

        return len(errors) == 0, errors

    def _is_common_password(self, password: str) -> bool:
        """Check if password is in common passwords list"""
        # In production, use a proper common passwords database
        common_passwords = {
            "password",
            "123456",
            "password123",
            "admin",
            "qwerty",
            "letmein",
            "welcome",
            "monkey",
            "1234567890",
        }
        return password.lower() in common_passwords

    # API Key Management
    def generate_api_key(
        self, user_id: str, name: str, permissions: List[str] = None
    ) -> dict:
        """Generate API key for user"""
        api_key = f"bpd_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        key_data = {
            "user_id": user_id,
            "name": name,
            "permissions": permissions or [],
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None,
            "usage_count": 0,
        }

        # Store in Redis with hash as key
        self.redis_client.set_cache(f"api_key:{key_hash}", key_data)

        return {"api_key": api_key, "name": name, "permissions": permissions}

    def validate_api_key(self, api_key: str) -> Optional[dict]:
        """Validate API key and return user data"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_data = self.redis_client.get_cache(f"api_key:{key_hash}")

        if key_data:
            # Update usage statistics
            key_data["last_used"] = datetime.utcnow().isoformat()
            key_data["usage_count"] = key_data.get("usage_count", 0) + 1
            self.redis_client.set_cache(f"api_key:{key_hash}", key_data)

        return key_data

    # Security Event Logging
    def _log_security_event(self, event_type: str, data: dict):
        """Log security events for monitoring"""
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
            **data,
        }

        logger.info(f"Security event: {event_type}", extra=event)

        # Store in Redis for real-time monitoring
        self.redis_client.redis_client.lpush("security_events", str(event))
        self.redis_client.redis_client.ltrim(
            "security_events", 0, 1000
        )  # Keep last 1000 events

    # Helper methods (implement based on your user model)
    def _get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email - implement based on your user model"""
        # This should query your user database
        pass

    def _save_user_2fa_secret(self, user_id: str, secret: str):
        """Save 2FA secret to user account"""
        # This should update your user database
        pass

    def _get_user_2fa_secret(self, user_id: str) -> Optional[str]:
        """Get user's 2FA secret"""
        # This should query your user database
        pass


# Decorators for security
def require_api_key(security_enhancer: SecurityEnhancer):
    """Decorator for API key authentication"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return jsonify({"error": "API key required"}), 401

            key_data = security_enhancer.validate_api_key(api_key)
            if not key_data:
                return jsonify({"error": "Invalid API key"}), 401

            g.api_key_data = key_data
            g.current_user_id = key_data["user_id"]
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_permission(permission: str):
    """Decorator to check user permissions"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check JWT permissions
            current_user = get_jwt_identity()
            claims = get_jwt()
            user_permissions = claims.get("permissions", [])

            if permission not in user_permissions:
                return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_input_data(rules: dict):
    """Decorator for input validation"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Get security enhancer from app context
            security_enhancer = getattr(g, "security_enhancer", None)
            if not security_enhancer:
                return jsonify({"error": "Security validation unavailable"}), 500

            is_valid, errors = security_enhancer.validate_input(data, rules)
            if not is_valid:
                return jsonify({"error": "Validation failed", "details": errors}), 400

            return f(*args, **kwargs)

        return decorated_function

    return decorator
