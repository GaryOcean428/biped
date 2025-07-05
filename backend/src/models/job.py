from datetime import datetime
from enum import Enum

from sqlalchemy import Numeric
from . import db


class JobStatus(Enum):
    DRAFT = "draft"
    POSTED = "posted"
    MATCHED = "matched"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class Job(db.Model):
    """Job postings from customers"""

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=False)
    assigned_provider_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )

    # Job details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Location
    street_address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    postcode = db.Column(db.String(10), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # Timing
    preferred_start_date = db.Column(db.Date, nullable=True)
    preferred_end_date = db.Column(db.Date, nullable=True)
    is_urgent = db.Column(db.Boolean, default=False)
    is_flexible_timing = db.Column(db.Boolean, default=True)

    # Budget
    budget_min = db.Column(Numeric(10, 2), nullable=True)
    budget_max = db.Column(Numeric(10, 2), nullable=True)
    budget_type = db.Column(
        db.String(20), nullable=True
    )  # 'fixed', 'hourly', 'negotiable'

    # Job characteristics
    property_type = db.Column(
        db.String(20), nullable=False
    )  # 'residential', 'commercial'
    access_requirements = db.Column(db.Text, nullable=True)
    special_requirements = db.Column(db.Text, nullable=True)

    # Attachments
    images = db.Column(db.JSON, nullable=True)  # Array of image URLs
    documents = db.Column(db.JSON, nullable=True)  # Array of document URLs

    # Status and workflow
    status = db.Column(db.Enum(JobStatus), default=JobStatus.DRAFT, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Pricing and payment
    agreed_price = db.Column(Numeric(10, 2), nullable=True)
    final_price = db.Column(Numeric(10, 2), nullable=True)
    commission_amount = db.Column(Numeric(8, 2), nullable=True)

    # Dates
    posted_at = db.Column(db.DateTime, nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    customer = db.relationship(
        "User", foreign_keys=[customer_id], backref="posted_jobs"
    )
    assigned_provider = db.relationship(
        "User", foreign_keys=[assigned_provider_id], backref="assigned_jobs"
    )
    quotes = db.relationship("Quote", backref="job", cascade="all, delete-orphan")
    messages = db.relationship(
        "JobMessage", backref="job", cascade="all, delete-orphan"
    )
    milestones = db.relationship(
        "JobMilestone", backref="job", cascade="all, delete-orphan"
    )
    reviews = db.relationship("Review", backref="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job {self.title}>"

    def get_estimated_price(self):
        """Get estimated price based on service and job details"""
        if (
            self.service
            and self.service.typical_price_min
            and self.service.typical_price_max
        ):
            return {
                "min": float(self.service.typical_price_min),
                "max": float(self.service.typical_price_max),
                "unit": self.service.price_unit,
            }
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "service_id": self.service_id,
            "assigned_provider_id": self.assigned_provider_id,
            "title": self.title,
            "description": self.description,
            "street_address": self.street_address,
            "city": self.city,
            "state": self.state,
            "postcode": self.postcode,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "preferred_start_date": (
                self.preferred_start_date.isoformat()
                if self.preferred_start_date
                else None
            ),
            "preferred_end_date": (
                self.preferred_end_date.isoformat() if self.preferred_end_date else None
            ),
            "is_urgent": self.is_urgent,
            "is_flexible_timing": self.is_flexible_timing,
            "budget_min": float(self.budget_min) if self.budget_min else None,
            "budget_max": float(self.budget_max) if self.budget_max else None,
            "budget_type": self.budget_type,
            "property_type": self.property_type,
            "access_requirements": self.access_requirements,
            "special_requirements": self.special_requirements,
            "images": self.images,
            "documents": self.documents,
            "status": self.status.value if self.status else None,
            "is_active": self.is_active,
            "agreed_price": float(self.agreed_price) if self.agreed_price else None,
            "final_price": float(self.final_price) if self.final_price else None,
            "commission_amount": (
                float(self.commission_amount) if self.commission_amount else None
            ),
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "estimated_price": self.get_estimated_price(),
            "service_name": self.service.name if self.service else None,
            "customer_name": self.customer.get_full_name() if self.customer else None,
            "provider_name": (
                self.assigned_provider.get_full_name()
                if self.assigned_provider
                else None
            ),
        }


class Quote(db.Model):
    """Quotes from providers for jobs"""

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Quote details
    price = db.Column(Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Timeline
    estimated_start_date = db.Column(db.Date, nullable=True)
    estimated_completion_date = db.Column(db.Date, nullable=True)
    estimated_duration_days = db.Column(db.Integer, nullable=True)

    # Terms
    includes_materials = db.Column(db.Boolean, default=False)
    warranty_period_months = db.Column(db.Integer, nullable=True)
    payment_terms = db.Column(db.Text, nullable=True)

    # Status
    is_accepted = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    # Validity
    valid_until = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    provider = db.relationship("User", backref="quotes")

    def __repr__(self):
        return f"<Quote {self.id} - ${self.price}>"

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "provider_id": self.provider_id,
            "price": float(self.price),
            "description": self.description,
            "estimated_start_date": (
                self.estimated_start_date.isoformat()
                if self.estimated_start_date
                else None
            ),
            "estimated_completion_date": (
                self.estimated_completion_date.isoformat()
                if self.estimated_completion_date
                else None
            ),
            "estimated_duration_days": self.estimated_duration_days,
            "includes_materials": self.includes_materials,
            "warranty_period_months": self.warranty_period_months,
            "payment_terms": self.payment_terms,
            "is_accepted": self.is_accepted,
            "is_active": self.is_active,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "provider_name": self.provider.get_full_name() if self.provider else None,
            "provider_rating": (
                self.provider.provider_profile.average_rating
                if self.provider and self.provider.provider_profile
                else None
            ),
        }


class JobMilestone(db.Model):
    """Project milestones for tracking progress"""

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Progress
    is_completed = db.Column(db.Boolean, default=False)
    completion_percentage = db.Column(db.Integer, default=0)

    # Timing
    planned_date = db.Column(db.Date, nullable=True)
    completed_date = db.Column(db.Date, nullable=True)

    # Payment
    payment_amount = db.Column(Numeric(8, 2), nullable=True)
    is_payment_released = db.Column(db.Boolean, default=False)

    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<JobMilestone {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "title": self.title,
            "description": self.description,
            "is_completed": self.is_completed,
            "completion_percentage": self.completion_percentage,
            "planned_date": (
                self.planned_date.isoformat() if self.planned_date else None
            ),
            "completed_date": (
                self.completed_date.isoformat() if self.completed_date else None
            ),
            "payment_amount": (
                float(self.payment_amount) if self.payment_amount else None
            ),
            "is_payment_released": self.is_payment_released,
            "sort_order": self.sort_order,
        }


class JobMessage(db.Model):
    """Messages related to specific jobs"""

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    message = db.Column(db.Text, nullable=False)
    attachments = db.Column(db.JSON, nullable=True)  # Array of file URLs

    is_read = db.Column(db.Boolean, default=False)
    is_system_message = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sender = db.relationship("User", backref="job_messages")

    def __repr__(self):
        return f"<JobMessage {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "sender_id": self.sender_id,
            "message": self.message,
            "attachments": self.attachments,
            "is_read": self.is_read,
            "is_system_message": self.is_system_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sender_name": self.sender.get_full_name() if self.sender else None,
        }
