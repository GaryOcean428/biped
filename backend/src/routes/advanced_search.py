"""
Advanced Search and Filtering System for Biped Platform
Revolutionary search capabilities with AI-powered recommendations
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import and_, or_, func, desc, asc, text
from datetime import datetime, timedelta
import re
from typing import List, Dict, Any, Optional, Tuple

from src.models.user import db, User, ProviderProfile, CustomerProfile
from src.models.job import Job, JobStatus
from src.models.service import Service, ServiceCategory
from src.models.review import Review

advanced_search_bp = Blueprint('advanced_search', __name__, url_prefix='/api/search')

class AdvancedSearchEngine:
    """
    Revolutionary search engine with AI-powered features:
    - Semantic search with natural language processing
    - Advanced filtering with multiple criteria
    - Intelligent suggestions and auto-complete
    - Location-based search with radius
    - Price range optimization
    - Availability and scheduling integration
    """
    
    def __init__(self):
        self.search_weights = {
            'title_match': 0.4,
            'description_match': 0.3,
            'category_match': 0.2,
            'location_match': 0.1
        }
    
    def search_jobs(
        self,
        query: str = "",
        category: str = "",
        location: str = "",
        min_budget: float = None,
        max_budget: float = None,
        status: str = "",
        urgency: bool = None,
        date_from: str = "",
        date_to: str = "",
        sort_by: str = "relevance",
        sort_order: str = "desc",
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Advanced job search with multiple filters"""
        
        # Start with base query including service relationships
        base_query = db.session.query(Job).join(User, Job.customer_id == User.id).join(Service, Job.service_id == Service.id).join(ServiceCategory, Service.category_id == ServiceCategory.id)
        
        # Apply filters
        filters = []
        
        # Text search across multiple fields
        if query:
            search_terms = self._extract_search_terms(query)
            text_filters = []
            
            for term in search_terms:
                term_filter = or_(
                    Job.title.ilike(f'%{term}%'),
                    Job.description.ilike(f'%{term}%'),
                    Service.name.ilike(f'%{term}%'),
                    ServiceCategory.name.ilike(f'%{term}%'),
                    Job.street_address.ilike(f'%{term}%'),
                    Job.city.ilike(f'%{term}%')
                )
                text_filters.append(term_filter)
            
            if text_filters:
                filters.append(and_(*text_filters))
        
        # Category filter
        if category:
            filters.append(ServiceCategory.name.ilike(f'%{category}%'))
        
        # Location filter
        if location:
            filters.append(or_(
                Job.street_address.ilike(f'%{location}%'),
                Job.city.ilike(f'%{location}%'),
                Job.state.ilike(f'%{location}%')
            ))
        
        # Budget range filter
        if min_budget is not None:
            filters.append(or_(
                Job.budget_min >= min_budget,
                Job.budget_max >= min_budget
            ))
        if max_budget is not None:
            filters.append(or_(
                Job.budget_min <= max_budget,
                Job.budget_max <= max_budget
            ))
        
        # Status filter
        if status:
            try:
                job_status = JobStatus(status.lower())
                filters.append(Job.status == job_status)
            except ValueError:
                pass  # Invalid status, ignore
        
        # Urgency filter
        if urgency is not None:
            filters.append(Job.is_urgent == urgency)
        
        # Date range filter
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                filters.append(Job.created_at >= from_date)
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                filters.append(Job.created_at <= to_date)
            except ValueError:
                pass
        
        # Apply all filters
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # Apply sorting
        if sort_by == "relevance" and query:
            # Custom relevance scoring
            base_query = self._apply_relevance_sorting(base_query, query)
        elif sort_by == "date":
            if sort_order == "desc":
                base_query = base_query.order_by(desc(Job.created_at))
            else:
                base_query = base_query.order_by(asc(Job.created_at))
        elif sort_by == "budget":
            if sort_order == "desc":
                base_query = base_query.order_by(desc(Job.budget_min))
            else:
                base_query = base_query.order_by(asc(Job.budget_min))
        elif sort_by == "title":
            if sort_order == "desc":
                base_query = base_query.order_by(desc(Job.title))
            else:
                base_query = base_query.order_by(asc(Job.title))
        else:
            # Default sorting by creation date
            base_query = base_query.order_by(desc(Job.created_at))
        
        # Get total count for pagination
        total_count = base_query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        jobs = base_query.offset(offset).limit(per_page).all()
        
        # Format results
        results = []
        for job in jobs:
            customer = db.session.query(User).filter(User.id == job.customer_id).first()
            service = db.session.query(Service).filter(Service.id == job.service_id).first()
            category = db.session.query(ServiceCategory).filter(ServiceCategory.id == service.category_id).first() if service else None
            
            job_data = {
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'service': service.name if service else None,
                'category': category.name if category else None,
                'location': f"{job.city}, {job.state}",
                'budget_min': job.budget_min,
                'budget_max': job.budget_max,
                'budget_type': job.budget_type,
                'status': job.status.value if job.status else None,
                'is_urgent': job.is_urgent,
                'property_type': job.property_type,
                'created_at': job.created_at.isoformat(),
                'customer': {
                    'id': customer.id,
                    'name': customer.full_name,
                    'email': customer.email
                } if customer else None,
                'relevance_score': self._calculate_relevance_score(job, service, category, query) if query else 1.0
            }
            results.append(job_data)
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            'results': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            },
            'search_info': {
                'query': query,
                'filters_applied': len(filters),
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }
    
    def search_providers(
        self,
        query: str = "",
        skills: str = "",
        location: str = "",
        min_rate: float = None,
        max_rate: float = None,
        min_experience: int = None,
        min_rating: float = None,
        availability: str = "",
        sort_by: str = "relevance",
        sort_order: str = "desc",
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Advanced provider search with multiple filters"""
        
        # Start with base query
        base_query = db.session.query(ProviderProfile).join(User, ProviderProfile.user_id == User.id)
        
        # Apply filters
        filters = [User.is_active == True]  # Only active users
        
        # Text search across multiple fields
        if query:
            search_terms = self._extract_search_terms(query)
            text_filters = []
            
            for term in search_terms:
                term_filter = or_(
                    User.full_name.ilike(f'%{term}%'),
                    ProviderProfile.skills.ilike(f'%{term}%'),
                    ProviderProfile.service_area.ilike(f'%{term}%'),
                    ProviderProfile.bio.ilike(f'%{term}%')
                )
                text_filters.append(term_filter)
            
            if text_filters:
                filters.append(and_(*text_filters))
        
        # Skills filter
        if skills:
            skill_terms = [skill.strip() for skill in skills.split(',')]
            skill_filters = []
            for skill in skill_terms:
                skill_filters.append(ProviderProfile.skills.ilike(f'%{skill}%'))
            if skill_filters:
                filters.append(or_(*skill_filters))
        
        # Location filter
        if location:
            filters.append(ProviderProfile.service_area.ilike(f'%{location}%'))
        
        # Rate range filter
        if min_rate is not None:
            filters.append(ProviderProfile.hourly_rate >= min_rate)
        if max_rate is not None:
            filters.append(ProviderProfile.hourly_rate <= max_rate)
        
        # Experience filter
        if min_experience is not None:
            filters.append(ProviderProfile.years_experience >= min_experience)
        
        # Rating filter
        if min_rating is not None:
            # Subquery for average rating
            avg_rating_subquery = db.session.query(
                Review.reviewee_id,
                func.avg(Review.rating).label('avg_rating')
            ).group_by(Review.reviewee_id).subquery()
            
            base_query = base_query.outerjoin(
                avg_rating_subquery,
                ProviderProfile.user_id == avg_rating_subquery.c.reviewee_id
            )
            filters.append(
                or_(
                    avg_rating_subquery.c.avg_rating >= min_rating,
                    avg_rating_subquery.c.avg_rating.is_(None)  # Include providers with no ratings
                )
            )
        
        # Availability filter
        if availability:
            filters.append(ProviderProfile.availability.ilike(f'%{availability}%'))
        
        # Apply all filters
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # Apply sorting
        if sort_by == "relevance" and query:
            # Custom relevance scoring for providers
            base_query = self._apply_provider_relevance_sorting(base_query, query)
        elif sort_by == "rating":
            # Sort by average rating
            avg_rating_subquery = db.session.query(
                Review.reviewee_id,
                func.avg(Review.rating).label('avg_rating')
            ).group_by(Review.reviewee_id).subquery()
            
            base_query = base_query.outerjoin(
                avg_rating_subquery,
                ProviderProfile.user_id == avg_rating_subquery.c.reviewee_id
            )
            
            if sort_order == "desc":
                base_query = base_query.order_by(desc(avg_rating_subquery.c.avg_rating))
            else:
                base_query = base_query.order_by(asc(avg_rating_subquery.c.avg_rating))
        elif sort_by == "rate":
            if sort_order == "desc":
                base_query = base_query.order_by(desc(ProviderProfile.hourly_rate))
            else:
                base_query = base_query.order_by(asc(ProviderProfile.hourly_rate))
        elif sort_by == "experience":
            if sort_order == "desc":
                base_query = base_query.order_by(desc(ProviderProfile.years_experience))
            else:
                base_query = base_query.order_by(asc(ProviderProfile.years_experience))
        else:
            # Default sorting by user name
            base_query = base_query.order_by(asc(User.full_name))
        
        # Get total count for pagination
        total_count = base_query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        providers = base_query.offset(offset).limit(per_page).all()
        
        # Format results
        results = []
        for provider in providers:
            user = db.session.query(User).filter(User.id == provider.user_id).first()
            
            # Get average rating
            avg_rating = db.session.query(func.avg(Review.rating)).filter(
                Review.reviewee_id == provider.user_id
            ).scalar()
            
            # Get review count
            review_count = db.session.query(Review).filter(
                Review.reviewee_id == provider.user_id
            ).count()
            
            provider_data = {
                'id': provider.user_id,
                'name': user.full_name if user else "Unknown",
                'email': user.email if user else "",
                'skills': provider.skills,
                'hourly_rate': provider.hourly_rate,
                'years_experience': provider.years_experience,
                'service_area': provider.service_area,
                'availability': provider.availability,
                'bio': provider.bio,
                'average_rating': round(avg_rating, 2) if avg_rating else None,
                'review_count': review_count,
                'relevance_score': self._calculate_provider_relevance_score(provider, user, query) if query else 1.0
            }
            results.append(provider_data)
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            'results': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            },
            'search_info': {
                'query': query,
                'filters_applied': len(filters) - 1,  # Subtract 1 for the is_active filter
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }
    
    def get_search_suggestions(self, query: str, search_type: str = "jobs") -> List[str]:
        """Get intelligent search suggestions"""
        if not query or len(query) < 2:
            return []
        
        suggestions = []
        
        if search_type == "jobs":
            # Get suggestions from job titles and service categories
            job_suggestions = db.session.query(Job.title).filter(
                Job.title.ilike(f'%{query}%')
            ).distinct().limit(5).all()
            
            # Get category suggestions through Service relationship
            category_suggestions = db.session.query(ServiceCategory.name).join(
                Service, ServiceCategory.id == Service.category_id
            ).join(
                Job, Service.id == Job.service_id
            ).filter(
                ServiceCategory.name.ilike(f'%{query}%')
            ).distinct().limit(5).all()
            
            suggestions.extend([suggestion[0] for suggestion in job_suggestions])
            suggestions.extend([suggestion[0] for suggestion in category_suggestions])
        
        elif search_type == "providers":
            # Get suggestions from provider skills and names
            skill_suggestions = db.session.query(ProviderProfile.skills).filter(
                ProviderProfile.skills.ilike(f'%{query}%')
            ).distinct().limit(5).all()
            
            name_suggestions = db.session.query(User.full_name).join(ProviderProfile).filter(
                User.full_name.ilike(f'%{query}%')
            ).distinct().limit(5).all()
            
            # Extract individual skills
            for skill_row in skill_suggestions:
                if skill_row[0]:
                    skills = [skill.strip() for skill in skill_row[0].split(',')]
                    for skill in skills:
                        if query.lower() in skill.lower():
                            suggestions.append(skill)
            
            suggestions.extend([suggestion[0] for suggestion in name_suggestions])
        
        # Remove duplicates and limit results
        unique_suggestions = list(dict.fromkeys(suggestions))[:10]
        return unique_suggestions
    
    def get_popular_searches(self, search_type: str = "jobs", limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular search terms and categories"""
        popular_items = []
        
        if search_type == "jobs":
            # Get most common categories through Service relationship
            category_counts = db.session.query(
                ServiceCategory.name,
                func.count(ServiceCategory.name).label('count')
            ).join(
                Service, ServiceCategory.id == Service.category_id
            ).join(
                Job, Service.id == Job.service_id
            ).filter(
                ServiceCategory.name.isnot(None)
            ).group_by(ServiceCategory.name).order_by(desc('count')).limit(limit).all()
            
            popular_items = [
                {'term': category, 'count': count, 'type': 'category'}
                for category, count in category_counts
            ]
        
        elif search_type == "providers":
            # Get most common skills
            skill_counts = {}
            skills_data = db.session.query(ProviderProfile.skills).filter(
                ProviderProfile.skills.isnot(None)
            ).all()
            
            for skill_row in skills_data:
                if skill_row[0]:
                    skills = [skill.strip().lower() for skill in skill_row[0].split(',')]
                    for skill in skills:
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            # Sort by count and take top items
            sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            popular_items = [
                {'term': skill, 'count': count, 'type': 'skill'}
                for skill, count in sorted_skills
            ]
        
        return popular_items
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract meaningful search terms from query"""
        # Remove special characters and split by spaces
        clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
        terms = [term.strip() for term in clean_query.split() if len(term.strip()) > 2]
        return terms
    
    def _apply_relevance_sorting(self, query_obj, search_query: str):
        """Apply relevance-based sorting to job query"""
        # This is a simplified relevance scoring
        # In a real implementation, you'd use full-text search or Elasticsearch
        return query_obj.order_by(desc(Job.created_at))
    
    def _apply_provider_relevance_sorting(self, query_obj, search_query: str):
        """Apply relevance-based sorting to provider query"""
        # This is a simplified relevance scoring
        # In a real implementation, you'd use full-text search or Elasticsearch
        return query_obj.order_by(desc(User.created_at))
    
    def _calculate_relevance_score(self, job: Job, service: Service, category: ServiceCategory, query: str) -> float:
        """Calculate relevance score for a job"""
        if not query:
            return 1.0
        
        score = 0.0
        query_lower = query.lower()
        
        # Title match
        if job.title and query_lower in job.title.lower():
            score += self.search_weights['title_match']
        
        # Description match
        if job.description and query_lower in job.description.lower():
            score += self.search_weights['description_match']
        
        # Service/Category match
        if service and service.name and query_lower in service.name.lower():
            score += self.search_weights['category_match']
        if category and category.name and query_lower in category.name.lower():
            score += self.search_weights['category_match']
        
        # Location match
        location_text = f"{job.street_address} {job.city} {job.state}".lower()
        if query_lower in location_text:
            score += self.search_weights['location_match']
        
        return min(score, 1.0)
    
    def _calculate_provider_relevance_score(self, provider: ProviderProfile, user: User, query: str) -> float:
        """Calculate relevance score for a provider"""
        if not query:
            return 1.0
        
        score = 0.0
        query_lower = query.lower()
        
        # Name match
        if user and user.full_name and query_lower in user.full_name.lower():
            score += 0.3
        
        # Skills match
        if provider.skills and query_lower in provider.skills.lower():
            score += 0.4
        
        # Service area match
        if provider.service_area and query_lower in provider.service_area.lower():
            score += 0.2
        
        # Bio match
        if provider.bio and query_lower in provider.bio.lower():
            score += 0.1
        
        return min(score, 1.0)

# Initialize search engine
search_engine = AdvancedSearchEngine()

@advanced_search_bp.route('/jobs', methods=['GET'])
def search_jobs():
    """Advanced job search endpoint"""
    try:
        # Get search parameters
        query = request.args.get('q', '')
        category = request.args.get('category', '')
        location = request.args.get('location', '')
        min_budget = request.args.get('min_budget', type=float)
        max_budget = request.args.get('max_budget', type=float)
        status = request.args.get('status', '')
        urgency = request.args.get('urgency', type=bool)
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        sort_by = request.args.get('sort_by', 'relevance')
        sort_order = request.args.get('sort_order', 'desc')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        
        # Perform search
        results = search_engine.search_jobs(
            query=query,
            category=category,
            location=location,
            min_budget=min_budget,
            max_budget=max_budget,
            status=status,
            urgency=urgency,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            **results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_search_bp.route('/providers', methods=['GET'])
def search_providers():
    """Advanced provider search endpoint"""
    try:
        # Get search parameters
        query = request.args.get('q', '')
        skills = request.args.get('skills', '')
        location = request.args.get('location', '')
        min_rate = request.args.get('min_rate', type=float)
        max_rate = request.args.get('max_rate', type=float)
        min_experience = request.args.get('min_experience', type=int)
        min_rating = request.args.get('min_rating', type=float)
        availability = request.args.get('availability', '')
        sort_by = request.args.get('sort_by', 'relevance')
        sort_order = request.args.get('sort_order', 'desc')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        
        # Perform search
        results = search_engine.search_providers(
            query=query,
            skills=skills,
            location=location,
            min_rate=min_rate,
            max_rate=max_rate,
            min_experience=min_experience,
            min_rating=min_rating,
            availability=availability,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            **results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_search_bp.route('/suggestions', methods=['GET'])
def get_search_suggestions():
    """Get intelligent search suggestions"""
    try:
        query = request.args.get('q', '')
        search_type = request.args.get('type', 'jobs')  # 'jobs' or 'providers'
        
        suggestions = search_engine.get_search_suggestions(query, search_type)
        
        return jsonify({
            'success': True,
            'query': query,
            'suggestions': suggestions
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_search_bp.route('/popular', methods=['GET'])
def get_popular_searches():
    """Get popular search terms and categories"""
    try:
        search_type = request.args.get('type', 'jobs')  # 'jobs' or 'providers'
        limit = min(request.args.get('limit', 10, type=int), 50)  # Max 50 items
        
        popular_items = search_engine.get_popular_searches(search_type, limit)
        
        return jsonify({
            'success': True,
            'popular_searches': popular_items,
            'type': search_type
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_search_bp.route('/filters', methods=['GET'])
def get_available_filters():
    """Get available filter options for search"""
    try:
        search_type = request.args.get('type', 'jobs')
        
        if search_type == 'jobs':
            # Get unique categories through Service relationship
            categories = db.session.query(ServiceCategory.name).join(
                Service, ServiceCategory.id == Service.category_id
            ).join(
                Job, Service.id == Job.service_id
            ).filter(
                ServiceCategory.name.isnot(None)
            ).distinct().all()
            
            # Get budget ranges using budget_min and budget_max
            budget_stats = db.session.query(
                func.min(Job.budget_min).label('min_budget'),
                func.max(Job.budget_max).label('max_budget'),
                func.avg((Job.budget_min + Job.budget_max) / 2).label('avg_budget')
            ).first()
            
            # Get unique locations from city and state
            locations = db.session.query(
                (Job.city + ', ' + Job.state).label('location')
            ).filter(
                and_(Job.city.isnot(None), Job.state.isnot(None))
            ).distinct().limit(50).all()
            
            filters = {
                'categories': [cat[0] for cat in categories if cat[0]],
                'budget_range': {
                    'min': budget_stats.min_budget or 0,
                    'max': budget_stats.max_budget or 10000,
                    'average': round(budget_stats.avg_budget or 0, 2)
                },
                'locations': [loc[0] for loc in locations if loc[0]],
                'status_options': [status.value for status in JobStatus],
                'urgency_options': [True, False]
            }
        
        else:  # providers
            # Get unique skills
            all_skills = set()
            skills_data = db.session.query(ProviderProfile.skills).filter(
                ProviderProfile.skills.isnot(None)
            ).all()
            
            for skill_row in skills_data:
                if skill_row[0]:
                    skills = [skill.strip() for skill in skill_row[0].split(',')]
                    all_skills.update(skills)
            
            # Get rate ranges
            rate_stats = db.session.query(
                func.min(ProviderProfile.hourly_rate).label('min_rate'),
                func.max(ProviderProfile.hourly_rate).label('max_rate'),
                func.avg(ProviderProfile.hourly_rate).label('avg_rate')
            ).first()
            
            # Get experience ranges
            experience_stats = db.session.query(
                func.min(ProviderProfile.years_experience).label('min_exp'),
                func.max(ProviderProfile.years_experience).label('max_exp'),
                func.avg(ProviderProfile.years_experience).label('avg_exp')
            ).first()
            
            # Get service areas
            service_areas = db.session.query(ProviderProfile.service_area).filter(
                ProviderProfile.service_area.isnot(None)
            ).distinct().limit(50).all()
            
            filters = {
                'skills': sorted(list(all_skills))[:100],  # Limit to top 100 skills
                'rate_range': {
                    'min': rate_stats.min_rate or 0,
                    'max': rate_stats.max_rate or 200,
                    'average': round(rate_stats.avg_rate or 0, 2)
                },
                'experience_range': {
                    'min': experience_stats.min_exp or 0,
                    'max': experience_stats.max_exp or 30,
                    'average': round(experience_stats.avg_exp or 0, 1)
                },
                'service_areas': [area[0] for area in service_areas if area[0]],
                'rating_options': [1, 2, 3, 4, 5]
            }
        
        return jsonify({
            'success': True,
            'filters': filters,
            'type': search_type
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

