#!/usr/bin/env python3
"""
Database initialization script for TradeHub
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import app, db
from models.user import User
from models.service import ServiceCategory, Service, ProviderService, PortfolioItem
from models.job import Job, Quote, JobMilestone
from models.review import Review

def init_database():
    """Initialize the database with all tables and sample data"""
    with app.app_context():
        # Drop all tables and recreate
        logger.info("Dropping existing tables...")
        db.drop_all()
        
        logger.info("Creating all tables...")
        db.create_all()
        
        # Create service categories
        logger.info("Creating service categories...")
        categories = [
            ServiceCategory(name="Plumbing", description="Water, drainage, and pipe services", icon="🔧"),
            ServiceCategory(name="Electrical", description="Electrical installations and repairs", icon="⚡"),
            ServiceCategory(name="Carpentry", description="Wood work and furniture", icon="🔨"),
            ServiceCategory(name="Painting", description="Interior and exterior painting", icon="🎨"),
            ServiceCategory(name="Cleaning", description="Home and office cleaning services", icon="🧽"),
            ServiceCategory(name="Gardening", description="Landscaping and garden maintenance", icon="🌱"),
            ServiceCategory(name="Handyman", description="General repairs and maintenance", icon="🛠️"),
            ServiceCategory(name="Roofing", description="Roof repairs and installations", icon="🏠")
        ]
        
        for category in categories:
            db.session.add(category)
        
        db.session.commit()
        logger.info("Database initialized successfully!")
        
        # Log table info
        logger.info("Created tables:")
        for table in db.metadata.tables.keys():
            logger.info(f"  - {table}")

if __name__ == "__main__":
    init_database()

