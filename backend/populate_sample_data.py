#!/usr/bin/env python3
"""
Populate the Biped platform database with realistic sample data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.main import app
from src.models.user import db, User, CustomerProfile, ProviderProfile
from src.models.service import ServiceCategory, Service, ProviderService, PortfolioItem
from src.models.job import Job, Quote, JobMilestone, JobMessage, JobStatus
from src.models.review import Review, Message, Notification
from src.models.admin import Admin, AdminAction
from src.models.payment import Payment, Transfer, StripeAccount, Dispute
from src.models.financial import Invoice, FinancialQuote, Expense, PlatformRevenue, FinancialReport
from datetime import datetime, timedelta
from decimal import Decimal
import random

def create_sample_users():
    """Create sample users (customers and providers)"""
    print("Creating sample users...")
    
    # Sample customers
    customers = [
        {
            'email': 'john.smith@email.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'phone': '+61412345678',
            'user_type': 'customer',
            'city': 'Sydney',
            'state': 'NSW',
            'postcode': '2000'
        },
        {
            'email': 'sarah.jones@email.com',
            'first_name': 'Sarah',
            'last_name': 'Jones',
            'phone': '+61423456789',
            'user_type': 'customer',
            'city': 'Melbourne',
            'state': 'VIC',
            'postcode': '3000'
        },
        {
            'email': 'mike.wilson@email.com',
            'first_name': 'Mike',
            'last_name': 'Wilson',
            'phone': '+61434567890',
            'user_type': 'customer',
            'city': 'Brisbane',
            'state': 'QLD',
            'postcode': '4000'
        }
    ]
    
    # Sample providers
    providers = [
        {
            'email': 'dave.plumber@tradies.com',
            'first_name': 'Dave',
            'last_name': 'Thompson',
            'phone': '+61445678901',
            'user_type': 'provider',
            'city': 'Sydney',
            'state': 'NSW',
            'postcode': '2010',
            'bio': 'Licensed plumber with 15+ years experience. Specializing in residential and commercial plumbing.'
        },
        {
            'email': 'lisa.electrician@tradies.com',
            'first_name': 'Lisa',
            'last_name': 'Chen',
            'phone': '+61456789012',
            'user_type': 'provider',
            'city': 'Melbourne',
            'state': 'VIC',
            'postcode': '3010',
            'bio': 'Certified electrician specializing in home automation and solar installations.'
        },
        {
            'email': 'tom.carpenter@tradies.com',
            'first_name': 'Tom',
            'last_name': 'Anderson',
            'phone': '+61467890123',
            'user_type': 'provider',
            'city': 'Brisbane',
            'state': 'QLD',
            'postcode': '4010',
            'bio': 'Master carpenter with expertise in custom furniture and home renovations.'
        },
        {
            'email': 'emma.painter@tradies.com',
            'first_name': 'Emma',
            'last_name': 'Davis',
            'phone': '+61478901234',
            'user_type': 'provider',
            'city': 'Perth',
            'state': 'WA',
            'postcode': '6000',
            'bio': 'Professional painter specializing in interior and exterior residential painting.'
        }
    ]
    
    created_users = []
    
    # Create customers
    for customer_data in customers:
        user = User(**customer_data)
        user.set_password('password123')
        user.is_verified = True
        db.session.add(user)
        db.session.flush()  # Get the ID
        
        # Create customer profile
        profile = CustomerProfile(
            user_id=user.id,
            preferred_contact_method='phone',
            total_jobs_posted=random.randint(1, 5),
            total_spent=Decimal(str(random.randint(500, 3000))),
            average_rating_given=round(random.uniform(4.0, 5.0), 1)
        )
        db.session.add(profile)
        created_users.append(user)
    
    # Create providers
    for provider_data in providers:
        user = User(**provider_data)
        user.set_password('password123')
        user.is_verified = True
        db.session.add(user)
        db.session.flush()  # Get the ID
        
        # Create provider profile
        profile = ProviderProfile(
            user_id=user.id,
            business_name=f"{user.first_name}'s {random.choice(['Services', 'Solutions', 'Trades', 'Works'])}",
            abn=f"{random.randint(10000000000, 99999999999)}",
            license_number=f"LIC{random.randint(100000, 999999)}",
            insurance_policy=f"INS{random.randint(100000, 999999)}",
            is_abn_verified=True,
            is_license_verified=True,
            is_insurance_verified=True,
            is_background_checked=True,
            hourly_rate=Decimal(str(random.randint(50, 150))),
            years_experience=random.randint(5, 20),
            service_radius=random.randint(20, 50),
            is_available=True,
            total_jobs_completed=random.randint(50, 200),
            total_earnings=Decimal(str(random.randint(10000, 50000))),
            average_rating=round(random.uniform(4.2, 5.0), 1),
            response_time_hours=round(random.uniform(1.0, 6.0), 1),
            completion_rate=round(random.uniform(0.85, 1.0), 2)
        )
        db.session.add(profile)
        created_users.append(user)
    
    db.session.commit()
    print(f"Created {len(created_users)} users")
    return created_users

def create_sample_jobs():
    """Create sample jobs"""
    print("Creating sample jobs...")
    
    # Get some users
    customers = User.query.filter_by(user_type='customer').all()
    providers = User.query.filter_by(user_type='provider').all()
    categories = ServiceCategory.query.all()
    
    if not customers or not providers or not categories:
        print("Need users and categories first")
        return []
    
    sample_jobs = [
        {
            'title': 'Kitchen Sink Repair',
            'description': 'Kitchen sink is leaking and needs urgent repair. Located under the sink.',
            'budget_min': 150,
            'budget_max': 300,
            'urgency': 'asap',
            'street_address': '123 Main Street',
            'city': 'Sydney',
            'state': 'NSW',
            'postcode': '2000'
        },
        {
            'title': 'Bathroom Light Installation',
            'description': 'Need to install new LED lights in bathroom. 3 downlights required.',
            'budget_min': 200,
            'budget_max': 400,
            'urgency': 'week',
            'street_address': '456 Collins Street',
            'city': 'Melbourne',
            'state': 'VIC',
            'postcode': '3000'
        },
        {
            'title': 'Custom Bookshelf Build',
            'description': 'Looking for a custom built-in bookshelf for living room. 2m wide x 2.5m high.',
            'budget_min': 800,
            'budget_max': 1500,
            'urgency': 'month',
            'street_address': '789 Queen Street',
            'city': 'Brisbane',
            'state': 'QLD',
            'postcode': '4000'
        },
        {
            'title': 'House Exterior Painting',
            'description': 'Full exterior house painting required. 3 bedroom house, weatherboard.',
            'budget_min': 3000,
            'budget_max': 5000,
            'urgency': 'flexible',
            'street_address': '321 King Street',
            'city': 'Perth',
            'state': 'WA',
            'postcode': '6000'
        }
    ]
    
    created_jobs = []
    
    for i, job_data in enumerate(sample_jobs):
        customer = customers[i % len(customers)]
        category = categories[i % len(categories)]
        
        job = Job(
            customer_id=customer.id,
            service_id=category.id,  # Using category ID as service ID for now
            title=job_data['title'],
            description=job_data['description'],
            street_address=job_data['street_address'],
            city=job_data['city'],
            state=job_data['state'],
            postcode=job_data['postcode'],
            budget_min=Decimal(str(job_data['budget_min'])),
            budget_max=Decimal(str(job_data['budget_max'])),
            budget_type='fixed',
            property_type='residential',
            is_urgent=job_data['urgency'] == 'asap',
            is_flexible_timing=job_data['urgency'] == 'flexible',
            status=JobStatus.POSTED,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        
        # Assign some jobs to providers
        if random.choice([True, False]):
            provider = random.choice(providers)
            job.assigned_provider_id = provider.id
            job.status = random.choice([JobStatus.ACCEPTED, JobStatus.IN_PROGRESS, JobStatus.COMPLETED])
        
        db.session.add(job)
        created_jobs.append(job)
    
    db.session.commit()
    print(f"Created {len(created_jobs)} jobs")
    return created_jobs

def create_sample_financial_data():
    """Create sample financial data"""
    print("Creating sample financial data...")
    
    users = User.query.all()
    jobs = Job.query.all()
    
    if not users or not jobs:
        print("Need users and jobs first")
        return
    
    # Create sample invoices
    for i in range(5):
        user = random.choice(users)
        job = random.choice(jobs)
        
        invoice = Invoice(
            user_id=user.id,
            job_id=job.id,
            invoice_number=f"INV-{2025}{str(i+1).zfill(4)}",
            client_name=user.get_full_name(),
            client_email=user.email,
            client_address=f"{user.street_address}, {user.city}, {user.state} {user.postcode}" if user.street_address else f"{user.city}, {user.state}",
            client_phone=user.phone,
            issue_date=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
            due_date=datetime.utcnow() + timedelta(days=30),
            subtotal=Decimal(str(random.randint(500, 2000))),
            tax_rate=Decimal('10.00'),
            status='paid' if random.choice([True, False]) else 'sent',
            line_items=[
                {
                    'description': f'Service for {job.title}',
                    'quantity': 1,
                    'rate': random.randint(500, 2000),
                    'amount': random.randint(500, 2000)
                }
            ]
        )
        invoice.tax_amount = invoice.subtotal * invoice.tax_rate / 100
        invoice.total_amount = invoice.subtotal + invoice.tax_amount
        
        db.session.add(invoice)
    
    # Create sample platform revenue records
    for i in range(10):
        provider = random.choice([u for u in users if u.user_type == 'provider'])
        customer = random.choice([u for u in users if u.user_type == 'customer'])
        
        revenue = PlatformRevenue(
            provider_id=provider.id,
            customer_id=customer.id,
            transaction_type='commission',
            source_type='job',
            source_id=1,  # Dummy source ID
            gross_amount=Decimal(str(random.randint(200, 1500))),
            commission_rate=Decimal('8.5'),  # 8.5% commission
            payment_status='completed',
            payment_date=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
        )
        revenue.commission_amount = revenue.gross_amount * revenue.commission_rate / 100
        revenue.net_amount = revenue.gross_amount - revenue.commission_amount
        
        db.session.add(revenue)
    
    db.session.commit()
    print("Created sample financial data")

def create_sample_reviews():
    """Create sample reviews"""
    print("Creating sample reviews...")
    
    customers = User.query.filter_by(user_type='customer').all()
    providers = User.query.filter_by(user_type='provider').all()
    jobs = Job.query.filter(Job.status == 'completed').all()
    
    if not customers or not providers:
        print("Need users first")
        return
    
    sample_reviews = [
        {
            'rating': 5,
            'comment': 'Excellent work! Dave was professional, punctual, and fixed the issue quickly. Highly recommended!'
        },
        {
            'rating': 4,
            'comment': 'Good quality work. Lisa was knowledgeable and explained everything clearly. Minor delay but overall satisfied.'
        },
        {
            'rating': 5,
            'comment': 'Outstanding craftsmanship! Tom built exactly what we wanted. Attention to detail was impressive.'
        },
        {
            'rating': 4,
            'comment': 'Great painting job. Emma was neat and tidy, and the finish looks fantastic. Would hire again.'
        }
    ]
    
    for i, review_data in enumerate(sample_reviews[:len(providers)]):
        if i < len(customers) and i < len(jobs):  # Ensure we have both customer and job
            review = Review(
                reviewer_id=customers[i].id,
                reviewee_id=providers[i].id,
                job_id=jobs[i].id,
                overall_rating=review_data['rating'],
                quality_rating=review_data['rating'],
                communication_rating=review_data['rating'],
                timeliness_rating=review_data['rating'],
                professionalism_rating=review_data['rating'],
                value_rating=review_data['rating'],
                comment=review_data['comment'],
                would_recommend=review_data['rating'] >= 4,
                would_hire_again=review_data['rating'] >= 4,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            db.session.add(review)
    
    db.session.commit()
    print("Created sample reviews")

def main():
    """Main function to populate all sample data"""
    print("🚀 Populating Biped platform with sample data...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if data already exists
        if User.query.count() > 1:  # More than just admin
            print("Sample data already exists. Skipping...")
            return
        
        # Create sample data
        users = create_sample_users()
        jobs = create_sample_jobs()
        create_sample_financial_data()
        create_sample_reviews()
        
        print("✅ Sample data population complete!")
        print(f"Created:")
        print(f"  - {User.query.count()} users")
        print(f"  - {Job.query.count()} jobs")
        print(f"  - {Invoice.query.count()} invoices")
        print(f"  - {PlatformRevenue.query.count()} revenue records")
        print(f"  - {Review.query.count()} reviews")

if __name__ == '__main__':
    main()

