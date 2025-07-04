"""
Models package initialization
Exports all models and database instance
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize database instance
db = SQLAlchemy()

# Import all models to ensure they're registered
from .admin import Admin, AdminAction
from .user import User, CustomerProfile, ProviderProfile
from .service import Service, ServiceCategory, ProviderService, PortfolioItem
from .job import Job, Quote, JobMilestone, JobMessage
from .payment import Payment, StripeAccount, Transfer, Dispute
from .review import Review, Message, Notification
from .financial import Invoice, FinancialQuote, Expense, PlatformRevenue, FinancialReport

# Export commonly used items
__all__ = [
    'db',
    'Admin',
    'AdminAction',
    'User', 
    'CustomerProfile',
    'ProviderProfile',
    'Service',
    'ServiceCategory', 
    'ProviderService',
    'PortfolioItem',
    'Job',
    'Quote',
    'JobMilestone',
    'JobMessage',
    'Payment',
    'StripeAccount',
    'Transfer',
    'Dispute',
    'Review',
    'Message',
    'Notification',
    'Invoice',
    'FinancialQuote',
    'Expense',
    'PlatformRevenue',
    'FinancialReport'
]

