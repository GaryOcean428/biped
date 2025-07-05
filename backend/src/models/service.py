from datetime import datetime

from sqlalchemy import Numeric

from . import db


class ServiceCategory(db.Model):
    """Service categories (e.g., Plumbing, Electrical, Carpentry)"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(100), nullable=True)  # Icon name or URL
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    # Parent-child relationship for subcategories
    parent_id = db.Column(
        db.Integer, db.ForeignKey("service_category.id"), nullable=True
    )
    children = db.relationship(
        "ServiceCategory", backref=db.backref("parent", remote_side=[id])
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    services = db.relationship(
        "Service", backref="category", cascade="all, delete-orphan"
    )
    provider_services = db.relationship(
        "ProviderService", backref="category", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ServiceCategory {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "icon": self.icon,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "parent_id": self.parent_id,
            "children": (
                [child.to_dict() for child in self.children] if self.children else []
            ),
        }


class Service(db.Model):
    """Specific services within categories"""

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("service_category.id"), nullable=False
    )
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Pricing information
    typical_price_min = db.Column(Numeric(8, 2), nullable=True)
    typical_price_max = db.Column(Numeric(8, 2), nullable=True)
    price_unit = db.Column(db.String(20), nullable=True)  # 'hour', 'job', 'sqm', etc.

    # Service characteristics
    typical_duration_hours = db.Column(db.Float, nullable=True)
    complexity_level = db.Column(
        db.String(20), nullable=True
    )  # 'basic', 'intermediate', 'advanced'
    requires_license = db.Column(db.Boolean, default=False)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    provider_services = db.relationship(
        "ProviderService", backref="service", cascade="all, delete-orphan"
    )
    jobs = db.relationship("Job", backref="service", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Service {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "typical_price_min": (
                float(self.typical_price_min) if self.typical_price_min else None
            ),
            "typical_price_max": (
                float(self.typical_price_max) if self.typical_price_max else None
            ),
            "price_unit": self.price_unit,
            "typical_duration_hours": self.typical_duration_hours,
            "complexity_level": self.complexity_level,
            "requires_license": self.requires_license,
            "is_active": self.is_active,
        }


class ProviderService(db.Model):
    """Services offered by specific providers"""

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(
        db.Integer, db.ForeignKey("provider_profile.id"), nullable=False
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey("service_category.id"), nullable=False
    )
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=False)

    # Provider-specific pricing
    hourly_rate = db.Column(Numeric(8, 2), nullable=True)
    fixed_price = db.Column(Numeric(8, 2), nullable=True)
    minimum_charge = db.Column(Numeric(8, 2), nullable=True)

    # Service details
    description = db.Column(db.Text, nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)

    # Availability
    is_available = db.Column(db.Boolean, default=True)
    lead_time_days = db.Column(db.Integer, default=1)

    # Performance metrics
    jobs_completed = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<ProviderService {self.provider_id}-{self.service_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "category_id": self.category_id,
            "service_id": self.service_id,
            "category_name": self.category.name if self.category else None,
            "service_name": self.service.name if self.service else None,
            "hourly_rate": float(self.hourly_rate) if self.hourly_rate else None,
            "fixed_price": float(self.fixed_price) if self.fixed_price else None,
            "minimum_charge": (
                float(self.minimum_charge) if self.minimum_charge else None
            ),
            "description": self.description,
            "experience_years": self.experience_years,
            "is_available": self.is_available,
            "lead_time_days": self.lead_time_days,
            "jobs_completed": self.jobs_completed,
            "average_rating": self.average_rating,
        }


class PortfolioItem(db.Model):
    """Portfolio items for service providers"""

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(
        db.Integer, db.ForeignKey("provider_profile.id"), nullable=False
    )
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Images
    before_image = db.Column(db.String(255), nullable=True)
    after_image = db.Column(db.String(255), nullable=True)
    additional_images = db.Column(db.JSON, nullable=True)  # Array of image URLs

    # Project details
    project_cost = db.Column(Numeric(10, 2), nullable=True)
    project_duration_days = db.Column(db.Integer, nullable=True)
    completion_date = db.Column(db.Date, nullable=True)

    # Display settings
    is_featured = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<PortfolioItem {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "service_id": self.service_id,
            "service_name": self.service.name if self.service else None,
            "title": self.title,
            "description": self.description,
            "before_image": self.before_image,
            "after_image": self.after_image,
            "additional_images": self.additional_images,
            "project_cost": float(self.project_cost) if self.project_cost else None,
            "project_duration_days": self.project_duration_days,
            "completion_date": (
                self.completion_date.isoformat() if self.completion_date else None
            ),
            "is_featured": self.is_featured,
            "is_public": self.is_public,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
