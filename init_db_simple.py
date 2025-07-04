#!/usr/bin/env python3
"""
Database initialization script for Biped platform
"""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask

# Initialize the models package first
from src.models import db

# Create minimal Flask app for database initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biped_test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the existing db instance with this app
db.init_app(app)

# Import all models to register them
from src.models import *

if __name__ == '__main__':
    with app.app_context():
        print("Creating database tables...")
        
        # Import each model explicitly to ensure they're registered
        from src.models.user import User, CustomerProfile, ProviderProfile
        from src.models.service import ServiceCategory, Service, ProviderService, PortfolioItem
        from src.models.job import Job, Quote, JobMilestone, JobMessage
        from src.models.admin import Admin, AdminAction
        from src.models.payment import Payment, StripeAccount, Transfer, Dispute
        from src.models.review import Review, Message, Notification
        from src.models.financial import Invoice, FinancialQuote, Expense, PlatformRevenue, FinancialReport
        
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"DB metadata tables: {list(db.metadata.tables.keys())}")
        
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Check if tables were created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")
        
        # Also check the database file size
        import os
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"Database file size: {size} bytes")
        elif os.path.exists(f"instance/{db_path}"):
            size = os.path.getsize(f"instance/{db_path}")
            print(f"Database file size: {size} bytes")