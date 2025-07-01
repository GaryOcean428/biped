import sys
import os
sys.path.insert(0, '/home/ubuntu/tradehub_backend')

from src.main import app, db
from src.models.service import ServiceCategory, Service

with app.app_context():
    # Sample services for each category
    services_data = [
        # Plumbing (category_id: 1)
        {'category_id': 1, 'name': 'Blocked Drain Cleaning', 'slug': 'blocked-drain-cleaning', 'description': 'Clear blocked drains and pipes', 'typical_price_min': 150, 'typical_price_max': 300, 'price_unit': 'job', 'typical_duration_hours': 2},
        {'category_id': 1, 'name': 'Tap Installation/Repair', 'slug': 'tap-installation-repair', 'description': 'Install or repair taps and faucets', 'typical_price_min': 100, 'typical_price_max': 250, 'price_unit': 'job', 'typical_duration_hours': 1.5},
        {'category_id': 1, 'name': 'Toilet Repair', 'slug': 'toilet-repair', 'description': 'Fix toilet issues and leaks', 'typical_price_min': 120, 'typical_price_max': 280, 'price_unit': 'job', 'typical_duration_hours': 2},
        
        # Electrical (category_id: 2)
        {'category_id': 2, 'name': 'Power Point Installation', 'slug': 'power-point-installation', 'description': 'Install new power outlets', 'typical_price_min': 150, 'typical_price_max': 300, 'price_unit': 'job', 'typical_duration_hours': 2, 'requires_license': True},
        {'category_id': 2, 'name': 'Light Fixture Installation', 'slug': 'light-fixture-installation', 'description': 'Install ceiling lights and fixtures', 'typical_price_min': 100, 'typical_price_max': 250, 'price_unit': 'job', 'typical_duration_hours': 1.5, 'requires_license': True},
        {'category_id': 2, 'name': 'Electrical Fault Finding', 'slug': 'electrical-fault-finding', 'description': 'Diagnose and fix electrical problems', 'typical_price_min': 200, 'typical_price_max': 400, 'price_unit': 'job', 'typical_duration_hours': 3, 'requires_license': True},
        
        # Carpentry (category_id: 3)
        {'category_id': 3, 'name': 'Custom Shelving', 'slug': 'custom-shelving', 'description': 'Build custom shelves and storage', 'typical_price_min': 200, 'typical_price_max': 500, 'price_unit': 'job', 'typical_duration_hours': 4},
        {'category_id': 3, 'name': 'Door Installation', 'slug': 'door-installation', 'description': 'Install interior and exterior doors', 'typical_price_min': 300, 'typical_price_max': 600, 'price_unit': 'job', 'typical_duration_hours': 3},
        
        # Painting (category_id: 4)
        {'category_id': 4, 'name': 'Interior House Painting', 'slug': 'interior-house-painting', 'description': 'Paint interior walls and ceilings', 'typical_price_min': 30, 'typical_price_max': 60, 'price_unit': 'sqm', 'typical_duration_hours': 8},
        {'category_id': 4, 'name': 'Exterior House Painting', 'slug': 'exterior-house-painting', 'description': 'Paint exterior walls and trim', 'typical_price_min': 40, 'typical_price_max': 80, 'price_unit': 'sqm', 'typical_duration_hours': 12},
        
        # Landscaping (category_id: 5)
        {'category_id': 5, 'name': 'Garden Design', 'slug': 'garden-design', 'description': 'Design and plan garden layouts', 'typical_price_min': 500, 'typical_price_max': 2000, 'price_unit': 'job', 'typical_duration_hours': 8},
        {'category_id': 5, 'name': 'Lawn Mowing', 'slug': 'lawn-mowing', 'description': 'Regular lawn maintenance', 'typical_price_min': 50, 'typical_price_max': 150, 'price_unit': 'job', 'typical_duration_hours': 2},
        
        # Cleaning (category_id: 6)
        {'category_id': 6, 'name': 'House Cleaning', 'slug': 'house-cleaning', 'description': 'Regular house cleaning service', 'typical_price_min': 30, 'typical_price_max': 50, 'price_unit': 'hour', 'typical_duration_hours': 3},
        {'category_id': 6, 'name': 'End of Lease Cleaning', 'slug': 'end-of-lease-cleaning', 'description': 'Deep cleaning for rental properties', 'typical_price_min': 200, 'typical_price_max': 500, 'price_unit': 'job', 'typical_duration_hours': 6},
        
        # Roofing (category_id: 7)
        {'category_id': 7, 'name': 'Roof Repair', 'slug': 'roof-repair', 'description': 'Fix roof leaks and damage', 'typical_price_min': 300, 'typical_price_max': 1000, 'price_unit': 'job', 'typical_duration_hours': 4},
        {'category_id': 7, 'name': 'Gutter Cleaning', 'slug': 'gutter-cleaning', 'description': 'Clean and maintain gutters', 'typical_price_min': 150, 'typical_price_max': 400, 'price_unit': 'job', 'typical_duration_hours': 3},
        
        # Flooring (category_id: 8)
        {'category_id': 8, 'name': 'Timber Flooring Installation', 'slug': 'timber-flooring-installation', 'description': 'Install hardwood floors', 'typical_price_min': 80, 'typical_price_max': 150, 'price_unit': 'sqm', 'typical_duration_hours': 8},
        {'category_id': 8, 'name': 'Carpet Installation', 'slug': 'carpet-installation', 'description': 'Install new carpeting', 'typical_price_min': 30, 'typical_price_max': 80, 'price_unit': 'sqm', 'typical_duration_hours': 4},
    ]
    
    # Check if services already exist
    if Service.query.count() == 0:
        for service_data in services_data:
            service = Service(**service_data)
            db.session.add(service)
        
        db.session.commit()
        print(f"Added {len(services_data)} services to the database")
    else:
        print("Services already exist in the database")
        
    # Print service count
    print(f"Total services in database: {Service.query.count()}")
