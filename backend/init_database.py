#!/usr/bin/env python3
"""
Database Initialization Script for Biped Platform
Creates all tables and default data for development and production
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.models.user import db, User, CustomerProfile, ProviderProfile
from src.models.admin import Admin
from src.models.service import ServiceCategory, Service

def init_database():
    """Initialize database with tables and default data"""
    with app.app_context():
        try:
            print("🔄 Initializing database...")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Create default admin user
            admin = Admin.query.filter_by(email='admin@biped.app').first()
            if not admin:
                admin = Admin(
                    username='admin',
                    email='admin@biped.app',
                    first_name='Admin',
                    last_name='User',
                    role='super_admin',
                    is_super_admin=True,
                    is_active=True
                )
                # Use environment variable for admin password, generate secure random if not set
                admin_password = os.environ.get('ADMIN_PASSWORD')
                if not admin_password:
                    import secrets
                    admin_password = secrets.token_urlsafe(32)
                    print("⚠️ ADMIN_PASSWORD not set. Generated random password. Set ADMIN_PASSWORD environment variable for production.")
                
                admin.set_password(admin_password)
                db.session.add(admin)
                print("✅ Default admin user created")
            else:
                print("✅ Admin user already exists")
            
            # Create developer user for testing
            dev_user = User.query.filter_by(email='dev@biped.app').first()
            if not dev_user:
                dev_user = User(
                    email='dev@biped.app',
                    first_name='Developer',
                    last_name='User',
                    user_type='customer',
                    is_active=True,
                    is_verified=True
                )
                dev_user.set_password('dev_biped_2025')
                db.session.add(dev_user)
                print("✅ Developer user created")
            else:
                print("✅ Developer user already exists")
            
            # Create test customer user
            test_customer = User.query.filter_by(email='customer@test.com').first()
            if not test_customer:
                test_customer = User(
                    email='customer@test.com',
                    first_name='Test',
                    last_name='Customer',
                    phone='555-0123',
                    street_address='123 Test Street',
                    city='Test City',
                    state='Test State',
                    postcode='12345',
                    user_type='customer',
                    is_active=True,
                    is_verified=True
                )
                test_customer.set_password('TestPassword123')
                db.session.add(test_customer)
                db.session.flush()  # Get the user ID
                
                # Create customer profile
                customer_profile = CustomerProfile(
                    user_id=test_customer.id,
                    preferred_contact_method='email',
                    total_jobs_posted=0,
                    total_spent=0.00
                )
                db.session.add(customer_profile)
                print("✅ Test customer user created")
            else:
                print("✅ Test customer user already exists")
            
            # Create test provider user
            test_provider = User.query.filter_by(email='provider@test.com').first()
            if not test_provider:
                test_provider = User(
                    email='provider@test.com',
                    first_name='Test',
                    last_name='Provider',
                    phone='555-0456',
                    street_address='456 Provider Street',
                    city='Provider City',
                    state='Provider State',
                    postcode='67890',
                    user_type='provider',
                    is_active=True,
                    is_verified=True
                )
                test_provider.set_password('TestPassword123')
                db.session.add(test_provider)
                db.session.flush()  # Get the user ID
                
                # Create provider profile
                provider_profile = ProviderProfile(
                    user_id=test_provider.id,
                    business_name='Test Provider Services',
                    abn='12345678901',
                    years_experience=5,
                    hourly_rate=75.00,
                    service_radius=50,
                    is_available=True,
                    total_jobs_completed=0,
                    total_earnings=0.00,
                    average_rating=0.0
                )
                db.session.add(provider_profile)
                print("✅ Test provider user created")
            else:
                print("✅ Test provider user already exists")
            
            # Create default service categories
            categories = [
                ('Construction & Renovation', 'construction-renovation'),
                ('Plumbing & Electrical', 'plumbing-electrical'),
                ('Tech & Digital', 'tech-digital'),
                ('Automotive', 'automotive'),
                ('Landscaping', 'landscaping'),
                ('Cleaning & Maintenance', 'cleaning-maintenance')
            ]
            
            for category_name, category_slug in categories:
                category = ServiceCategory.query.filter_by(name=category_name).first()
                if not category:
                    category = ServiceCategory(
                        name=category_name,
                        slug=category_slug,
                        description=f'Professional {category_name.lower()} services',
                        is_active=True
                    )
                    db.session.add(category)
            
            print("✅ Default service categories created")
            
            # Commit all changes
            db.session.commit()
            print("✅ Database initialization completed successfully")
            
            # Print summary
            user_count = User.query.count()
            admin_count = Admin.query.count()
            category_count = ServiceCategory.query.count()
            
            print(f"\n📊 Database Summary:")
            print(f"   Users: {user_count}")
            print(f"   Admins: {admin_count}")
            print(f"   Service Categories: {category_count}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database initialization failed: {e}")
            raise

if __name__ == '__main__':
    init_database()

