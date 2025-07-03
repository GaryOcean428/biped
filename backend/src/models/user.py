from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    """Base user model for both customers and service providers"""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    user_type = db.Column(db.String(20), nullable=False)  # 'customer' or 'provider'
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Address information
    street_address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    postcode = db.Column(db.String(10), nullable=True)

    # Profile information
    profile_image = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)

    # Relationships
    customer_profile = db.relationship(
        "CustomerProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    provider_profile = db.relationship(
        "ProviderProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    sent_messages = db.relationship(
        "Message", foreign_keys="Message.sender_id", backref="sender", cascade="all, delete-orphan"
    )
    received_messages = db.relationship(
        "Message",
        foreign_keys="Message.recipient_id",
        backref="recipient",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email}>"

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.get_full_name(),
            "phone": self.phone,
            "user_type": self.user_type,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "street_address": self.street_address,
            "city": self.city,
            "state": self.state,
            "postcode": self.postcode,
            "profile_image": self.profile_image,
            "bio": self.bio,
        }


class CustomerProfile(db.Model):
    """Extended profile for customers"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Preferences
    preferred_contact_method = db.Column(db.String(20), default="email")  # email, phone, app
    notification_preferences = db.Column(db.JSON, nullable=True)

    # History and stats
    total_jobs_posted = db.Column(db.Integer, default=0)
    total_spent = db.Column(Numeric(10, 2), default=0.00)
    average_rating_given = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "preferred_contact_method": self.preferred_contact_method,
            "notification_preferences": self.notification_preferences,
            "total_jobs_posted": self.total_jobs_posted,
            "total_spent": float(self.total_spent) if self.total_spent else 0.0,
            "average_rating_given": self.average_rating_given,
        }


class ProviderProfile(db.Model):
    """Extended profile for service providers"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Business information
    business_name = db.Column(db.String(200), nullable=True)
    abn = db.Column(db.String(20), nullable=True)
    license_number = db.Column(db.String(50), nullable=True)
    insurance_policy = db.Column(db.String(100), nullable=True)

    # Verification status
    is_abn_verified = db.Column(db.Boolean, default=False)
    is_license_verified = db.Column(db.Boolean, default=False)
    is_insurance_verified = db.Column(db.Boolean, default=False)
    is_background_checked = db.Column(db.Boolean, default=False)

    # Service information
    years_experience = db.Column(db.Integer, nullable=True)
    hourly_rate = db.Column(Numeric(8, 2), nullable=True)
    service_radius = db.Column(db.Integer, default=25)  # km

    # Availability
    is_available = db.Column(db.Boolean, default=True)
    availability_schedule = db.Column(db.JSON, nullable=True)  # Weekly schedule

    # Performance metrics
    total_jobs_completed = db.Column(db.Integer, default=0)
    total_earnings = db.Column(Numeric(10, 2), default=0.00)
    average_rating = db.Column(db.Float, default=0.0)
    response_time_hours = db.Column(db.Float, default=24.0)
    completion_rate = db.Column(db.Float, default=0.0)

    # Platform settings
    commission_rate = db.Column(db.Float, default=0.05)  # 5% default
    auto_accept_jobs = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    services = db.relationship("ProviderService", backref="provider", cascade="all, delete-orphan")
    portfolio_items = db.relationship(
        "PortfolioItem", backref="provider", cascade="all, delete-orphan"
    )

    def get_verification_score(self):
        """Calculate verification score as percentage"""
        checks = [
            self.is_abn_verified,
            self.is_license_verified,
            self.is_insurance_verified,
            self.is_background_checked,
        ]
        return (sum(checks) / len(checks)) * 100

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "business_name": self.business_name,
            "abn": self.abn,
            "license_number": self.license_number,
            "insurance_policy": self.insurance_policy,
            "is_abn_verified": self.is_abn_verified,
            "is_license_verified": self.is_license_verified,
            "is_insurance_verified": self.is_insurance_verified,
            "is_background_checked": self.is_background_checked,
            "verification_score": self.get_verification_score(),
            "years_experience": self.years_experience,
            "hourly_rate": float(self.hourly_rate) if self.hourly_rate else None,
            "service_radius": self.service_radius,
            "is_available": self.is_available,
            "availability_schedule": self.availability_schedule,
            "total_jobs_completed": self.total_jobs_completed,
            "total_earnings": float(self.total_earnings) if self.total_earnings else 0.0,
            "average_rating": self.average_rating,
            "response_time_hours": self.response_time_hours,
            "completion_rate": self.completion_rate,
            "commission_rate": self.commission_rate,
            "auto_accept_jobs": self.auto_accept_jobs,
        }
