import secrets
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

# Import db from models package to avoid circular imports
from . import db


class Admin(db.Model):
    """Admin user model for platform administration"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    # Admin permissions
    role = db.Column(db.String(20), default="admin")  # admin, super_admin
    permissions = db.Column(db.JSON, nullable=True)  # Specific permissions

    # Status and security
    is_active = db.Column(db.Boolean, default=True)
    is_super_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Session management
    session_token = db.Column(db.String(255), nullable=True)
    session_expires = db.Column(db.DateTime, nullable=True)

    # Audit trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    created_admins = db.relationship(
        "Admin", backref=db.backref("creator", remote_side=[id])
    )

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def generate_session_token(self):
        """Generate a new session token"""
        self.session_token = secrets.token_urlsafe(32)
        self.session_expires = datetime.utcnow().replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        return self.session_token

    def is_session_valid(self):
        """Check if current session is valid"""
        if not self.session_token or not self.session_expires:
            return False
        return datetime.utcnow() < self.session_expires

    def clear_session(self):
        """Clear current session"""
        self.session_token = None
        self.session_expires = None

    def is_locked(self):
        """Check if account is locked"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until

    def lock_account(self, minutes=30):
        """Lock account for specified minutes"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        self.login_attempts = 0

    def unlock_account(self):
        """Unlock account"""
        self.locked_until = None
        self.login_attempts = 0

    def increment_login_attempts(self):
        """Increment failed login attempts"""
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.lock_account()

    def reset_login_attempts(self):
        """Reset login attempts on successful login"""
        self.login_attempts = 0
        self.last_login = datetime.utcnow()

    def get_full_name(self):
        """Get admin's full name"""
        return f"{self.first_name} {self.last_name}"

    def has_permission(self, permission):
        """Check if admin has specific permission"""
        if self.is_super_admin:
            return True

        if not self.permissions:
            return False

        return permission in self.permissions

    def get_default_permissions(self):
        """Get default permissions for admin role"""
        if self.role == "super_admin":
            return [
                "user_management",
                "service_management",
                "job_management",
                "review_management",
                "payment_management",
                "analytics",
                "admin_management",
                "system_settings",
            ]
        else:
            return [
                "user_management",
                "service_management",
                "job_management",
                "review_management",
                "analytics",
            ]

    def __repr__(self):
        return f"<Admin {self.username}>"

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.get_full_name(),
            "role": self.role,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "is_super_admin": self.is_super_admin,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_locked": self.is_locked(),
        }

        if include_sensitive:
            data.update(
                {
                    "login_attempts": self.login_attempts,
                    "locked_until": (
                        self.locked_until.isoformat() if self.locked_until else None
                    ),
                    "session_expires": (
                        self.session_expires.isoformat()
                        if self.session_expires
                        else None
                    ),
                }
            )

        return data


class AdminAction(db.Model):
    """Audit log for admin actions"""

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=False)
    action = db.Column(
        db.String(100), nullable=False
    )  # e.g., 'user_created', 'job_deleted'
    target_type = db.Column(
        db.String(50), nullable=True
    )  # e.g., 'user', 'job', 'service'
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.JSON, nullable=True)  # Additional action details
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    admin = db.relationship("Admin", backref="actions")

    def __repr__(self):
        return f"<AdminAction {self.action} by {self.admin_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "admin_name": self.admin.get_full_name() if self.admin else None,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
