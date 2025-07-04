"""
Models package initialization
Exports all models and database instance
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize database instance
db = SQLAlchemy()

# Import all models to ensure they're registered
from .admin import Admin, AdminAction
from .financial import (
    Expense,
    FinancialQuote,
    FinancialReport,
    Invoice,
    PlatformRevenue,
)
from .job import Job, JobMessage, JobMilestone, Quote
from .payment import Dispute, Payment, StripeAccount, Transfer
from .review import Message, Notification, Review
from .service import PortfolioItem, ProviderService, Service, ServiceCategory
from .user import CustomerProfile, ProviderProfile, User

# Export commonly used items
__all__ = [
    "db",
    "Admin",
    "AdminAction",
    "User",
    "CustomerProfile",
    "ProviderProfile",
    "Service",
    "ServiceCategory",
    "ProviderService",
    "PortfolioItem",
    "Job",
    "Quote",
    "JobMilestone",
    "JobMessage",
    "Payment",
    "StripeAccount",
    "Transfer",
    "Dispute",
    "Review",
    "Message",
    "Notification",
    "Invoice",
    "FinancialQuote",
    "Expense",
    "PlatformRevenue",
    "FinancialReport",
]
