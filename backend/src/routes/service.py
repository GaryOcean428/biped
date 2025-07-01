from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, ProviderProfile
from src.models.service import ServiceCategory, Service, ProviderService, PortfolioItem
from sqlalchemy import or_, and_

service_bp = Blueprint('service', __name__)

@service_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all service categories"""
    try:
        categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.sort_order).all()
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@service_bp.route('/categories/<int:category_id>/services', methods=['GET'])
def get_services_by_category(category_id):
    """Get all services in a category"""
    try:
        category = ServiceCategory.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        services = Service.query.filter_by(category_id=category_id, is_active=True).all()
        return jsonify({
            'category': category.to_dict(),
            'services': [service.to_dict() for service in services]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@service_bp.route('/search', methods=['GET'])
def search_services():
    """Search for services and providers"""
    try:
        query = request.args.get('q', '').strip()
        category_id = request.args.get('category_id', type=int)
        postcode = request.args.get('postcode', '').strip()
        max_price = request.args.get('max_price', type=float)
        min_rating = request.args.get('min_rating', type=float, default=0)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build base query for provider services
        provider_services_query = db.session.query(ProviderService).join(ProviderProfile).join(User)
        
        # Filter by category
        if category_id:
            provider_services_query = provider_services_query.filter(ProviderService.category_id == category_id)
        
        # Filter by search query
        if query:
            provider_services_query = provider_services_query.join(Service).filter(
                or_(
                    Service.name.ilike(f'%{query}%'),
                    Service.description.ilike(f'%{query}%'),
                    ProviderService.description.ilike(f'%{query}%'),
                    User.first_name.ilike(f'%{query}%'),
                    User.last_name.ilike(f'%{query}%'),
                    ProviderProfile.business_name.ilike(f'%{query}%')
                )
            )
        
        # Filter by location (postcode)
        if postcode:
            provider_services_query = provider_services_query.filter(User.postcode == postcode)
        
        # Filter by price
        if max_price:
            provider_services_query = provider_services_query.filter(
                or_(
                    ProviderService.hourly_rate <= max_price,
                    ProviderService.fixed_price <= max_price
                )
            )
        
        # Filter by rating
        if min_rating > 0:
            provider_services_query = provider_services_query.filter(ProviderService.average_rating >= min_rating)
        
        # Filter active providers and services
        provider_services_query = provider_services_query.filter(
            and_(
                ProviderService.is_available == True,
                ProviderProfile.is_available == True,
                User.is_active == True
            )
        )
        
        # Order by rating and jobs completed
        provider_services_query = provider_services_query.order_by(
            ProviderService.average_rating.desc(),
            ProviderService.jobs_completed.desc()
        )
        
        # Paginate results
        pagination = provider_services_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format results
        results = []
        for provider_service in pagination.items:
            provider = provider_service.provider
            user = provider.user
            
            result = {
                'provider_service': provider_service.to_dict(),
                'provider': provider.to_dict(),
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name(),
                    'profile_image': user.profile_image,
                    'city': user.city,
                    'state': user.state,
                    'postcode': user.postcode
                }
            }
            results.append(result)
        
        return jsonify({
            'results': results,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@service_bp.route('/providers/<int:provider_id>', methods=['GET'])
def get_provider_details(provider_id):
    """Get detailed provider information"""
    try:
        provider = ProviderProfile.query.get(provider_id)
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        user = provider.user
        if not user.is_active:
            return jsonify({'error': 'Provider not available'}), 404
        
        # Get provider services
        services = ProviderService.query.filter_by(provider_id=provider_id, is_available=True).all()
        
        # Get portfolio items
        portfolio = PortfolioItem.query.filter_by(
            provider_id=provider_id, 
            is_public=True
        ).order_by(PortfolioItem.is_featured.desc(), PortfolioItem.sort_order).all()
        
        # Get recent reviews
        from src.models.review import Review
        reviews = Review.query.filter_by(
            reviewee_id=user.id, 
            is_public=True
        ).order_by(Review.created_at.desc()).limit(10).all()
        
        return jsonify({
            'provider': provider.to_dict(),
            'user': user.to_dict(),
            'services': [service.to_dict() for service in services],
            'portfolio': [item.to_dict() for item in portfolio],
            'reviews': [review.to_dict() for review in reviews]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@service_bp.route('/provider/services', methods=['GET'])
def get_my_services():
    """Get current provider's services"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user or user.user_type != 'provider':
            return jsonify({'error': 'Provider access required'}), 403
        
        provider = user.provider_profile
        if not provider:
            return jsonify({'error': 'Provider profile not found'}), 404
        
        services = ProviderService.query.filter_by(provider_id=provider.id).all()
        
        return jsonify({
            'services': [service.to_dict() for service in services]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@service_bp.route('/provider/services', methods=['POST'])
def add_provider_service():
    """Add a new service for the current provider"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user or user.user_type != 'provider':
            return jsonify({'error': 'Provider access required'}), 403
        
        provider = user.provider_profile
        if not provider:
            return jsonify({'error': 'Provider profile not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['category_id', 'service_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if service already exists for this provider
        existing = ProviderService.query.filter_by(
            provider_id=provider.id,
            service_id=data['service_id']
        ).first()
        
        if existing:
            return jsonify({'error': 'Service already added'}), 409
        
        # Create new provider service
        provider_service = ProviderService(
            provider_id=provider.id,
            category_id=data['category_id'],
            service_id=data['service_id'],
            hourly_rate=data.get('hourly_rate'),
            fixed_price=data.get('fixed_price'),
            minimum_charge=data.get('minimum_charge'),
            description=data.get('description'),
            experience_years=data.get('experience_years'),
            lead_time_days=data.get('lead_time_days', 1)
        )
        
        db.session.add(provider_service)
        db.session.commit()
        
        return jsonify({
            'message': 'Service added successfully',
            'service': provider_service.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@service_bp.route('/provider/services/<int:service_id>', methods=['PUT'])
def update_provider_service(service_id):
    """Update a provider service"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user or user.user_type != 'provider':
            return jsonify({'error': 'Provider access required'}), 403
        
        provider = user.provider_profile
        if not provider:
            return jsonify({'error': 'Provider profile not found'}), 404
        
        provider_service = ProviderService.query.filter_by(
            id=service_id,
            provider_id=provider.id
        ).first()
        
        if not provider_service:
            return jsonify({'error': 'Service not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'hourly_rate' in data:
            provider_service.hourly_rate = data['hourly_rate']
        if 'fixed_price' in data:
            provider_service.fixed_price = data['fixed_price']
        if 'minimum_charge' in data:
            provider_service.minimum_charge = data['minimum_charge']
        if 'description' in data:
            provider_service.description = data['description']
        if 'experience_years' in data:
            provider_service.experience_years = data['experience_years']
        if 'is_available' in data:
            provider_service.is_available = data['is_available']
        if 'lead_time_days' in data:
            provider_service.lead_time_days = data['lead_time_days']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Service updated successfully',
            'service': provider_service.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@service_bp.route('/estimate', methods=['POST'])
def get_price_estimate():
    """Get price estimate for a service"""
    try:
        data = request.get_json()
        
        service_id = data.get('service_id')
        postcode = data.get('postcode')
        
        if not service_id:
            return jsonify({'error': 'service_id is required'}), 400
        
        service = Service.query.get(service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        # Get provider services for this service
        query = ProviderService.query.filter_by(service_id=service_id, is_available=True)
        
        # Filter by location if provided
        if postcode:
            query = query.join(ProviderProfile).join(User).filter(User.postcode == postcode)
        
        provider_services = query.all()
        
        # Calculate price estimates
        prices = []
        for ps in provider_services:
            if ps.hourly_rate:
                prices.append(float(ps.hourly_rate))
            if ps.fixed_price:
                prices.append(float(ps.fixed_price))
        
        if prices:
            estimate = {
                'min_price': min(prices),
                'max_price': max(prices),
                'average_price': sum(prices) / len(prices),
                'provider_count': len(provider_services),
                'service_name': service.name,
                'typical_duration_hours': service.typical_duration_hours
            }
        else:
            # Fall back to service defaults
            estimate = {
                'min_price': float(service.typical_price_min) if service.typical_price_min else None,
                'max_price': float(service.typical_price_max) if service.typical_price_max else None,
                'average_price': None,
                'provider_count': 0,
                'service_name': service.name,
                'typical_duration_hours': service.typical_duration_hours
            }
        
        return jsonify({'estimate': estimate}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

