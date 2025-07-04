#!/usr/bin/env python3
"""
Initialize sample data for Biped Platform
Creates service categories and services for testing
"""

import os
import sys
sys.path.append('/app/backend')
sys.path.append('/app')

from src.models import db, ServiceCategory, Service, User, CustomerProfile
from src.main import create_app
from werkzeug.security import generate_password_hash

def init_sample_data():
    """Initialize sample service categories and services"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Initializing sample data...")
        
        # Create service categories
        categories_data = [
            {
                'name': 'Construction & Renovation',
                'slug': 'construction-renovation',
                'description': 'General contractors, carpenters, painters, and renovation specialists',
                'icon': 'construction'
            },
            {
                'name': 'Plumbing & Electrical',
                'slug': 'plumbing-electrical',
                'description': 'Licensed plumbers, electricians, and HVAC specialists',
                'icon': 'plumbing'
            },
            {
                'name': 'Tech & Digital',
                'slug': 'tech-digital',
                'description': 'Web developers, designers, IT support, and digital marketing',
                'icon': 'computer'
            },
            {
                'name': 'Automotive',
                'slug': 'automotive',
                'description': 'Mechanics, auto electricians, and vehicle specialists',
                'icon': 'car'
            },
            {
                'name': 'Landscaping',
                'slug': 'landscaping',
                'description': 'Gardeners, landscapers, and outdoor maintenance specialists',
                'icon': 'tree'
            },
            {
                'name': 'Cleaning & Maintenance',
                'slug': 'cleaning-maintenance',
                'description': 'Professional cleaners, maintenance, and facility management',
                'icon': 'cleaning'
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            category = ServiceCategory.query.filter_by(slug=cat_data['slug']).first()
            if not category:
                category = ServiceCategory(**cat_data)
                db.session.add(category)
                print(f"✅ Created category: {cat_data['name']}")
            categories[cat_data['slug']] = category
        
        db.session.commit()
        
        # Create services
        services_data = [
            # Construction & Renovation
            {
                'category_slug': 'construction-renovation',
                'name': 'Kitchen Renovation',
                'slug': 'kitchen-renovation',
                'description': 'Complete kitchen renovation including cabinets, countertops, and appliances',
                'typical_price_min': 5000,
                'typical_price_max': 25000,
                'price_unit': 'job'
            },
            {
                'category_slug': 'construction-renovation',
                'name': 'Bathroom Renovation',
                'slug': 'bathroom-renovation',
                'description': 'Full bathroom renovation including tiling, fixtures, and plumbing',
                'typical_price_min': 3000,
                'typical_price_max': 15000,
                'price_unit': 'job'
            },
            {
                'category_slug': 'construction-renovation',
                'name': 'House Painting',
                'slug': 'house-painting',
                'description': 'Interior and exterior house painting services',
                'typical_price_min': 2000,
                'typical_price_max': 8000,
                'price_unit': 'job'
            },
            
            # Plumbing & Electrical
            {
                'category_slug': 'plumbing-electrical',
                'name': 'Plumbing Repair',
                'slug': 'plumbing-repair',
                'description': 'General plumbing repairs and maintenance',
                'typical_price_min': 100,
                'typical_price_max': 500,
                'price_unit': 'job'
            },
            {
                'category_slug': 'plumbing-electrical',
                'name': 'Electrical Installation',
                'slug': 'electrical-installation',
                'description': 'Electrical wiring, outlets, and fixture installation',
                'typical_price_min': 150,
                'typical_price_max': 1000,
                'price_unit': 'job'
            },
            
            # Tech & Digital
            {
                'category_slug': 'tech-digital',
                'name': 'Website Development',
                'slug': 'website-development',
                'description': 'Custom website design and development',
                'typical_price_min': 1000,
                'typical_price_max': 10000,
                'price_unit': 'job'
            },
            {
                'category_slug': 'tech-digital',
                'name': 'IT Support',
                'slug': 'it-support',
                'description': 'Computer repair and IT support services',
                'typical_price_min': 80,
                'typical_price_max': 200,
                'price_unit': 'hour'
            },
            
            # Automotive
            {
                'category_slug': 'automotive',
                'name': 'Car Service',
                'slug': 'car-service',
                'description': 'Regular car servicing and maintenance',
                'typical_price_min': 200,
                'typical_price_max': 800,
                'price_unit': 'job'
            },
            
            # Landscaping
            {
                'category_slug': 'landscaping',
                'name': 'Garden Maintenance',
                'slug': 'garden-maintenance',
                'description': 'Regular garden maintenance and landscaping',
                'typical_price_min': 50,
                'typical_price_max': 200,
                'price_unit': 'hour'
            },
            
            # Cleaning & Maintenance
            {
                'category_slug': 'cleaning-maintenance',
                'name': 'House Cleaning',
                'slug': 'house-cleaning',
                'description': 'Professional house cleaning services',
                'typical_price_min': 80,
                'typical_price_max': 300,
                'price_unit': 'job'
            }
        ]
        
        for service_data in services_data:
            category = categories[service_data['category_slug']]
            service = Service.query.filter_by(slug=service_data['slug']).first()
            if not service:
                service_data['category_id'] = category.id
                del service_data['category_slug']
                service = Service(**service_data)
                db.session.add(service)
                print(f"✅ Created service: {service_data['name']}")
        
        db.session.commit()
        
        # Create a sample customer user
        sample_user = User.query.filter_by(email='customer@biped.app').first()
        if not sample_user:
            sample_user = User(
                email='customer@biped.app',
                password_hash=generate_password_hash('password123'),
                user_type='customer',
                is_active=True,
                is_verified=True
            )
            db.session.add(sample_user)
            db.session.commit()
            
            # Create customer profile
            customer_profile = CustomerProfile(
                user_id=sample_user.id,
                first_name='John',
                last_name='Doe',
                phone='+61400000000',
                street_address='123 Test Street',
                city='Sydney',
                state='NSW',
                postcode='2000'
            )
            db.session.add(customer_profile)
            db.session.commit()
            print(f"✅ Created sample customer: customer@biped.app")
        
        print("🎉 Sample data initialization complete!")

if __name__ == '__main__':
    init_sample_data()

