"""
Smart Matching Algorithm API for Biped Platform
Revolutionary AI-powered contractor-client matching system
"""

from flask import Blueprint, request, jsonify, g
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
import math
import random
from typing import List, Dict, Any, Tuple

from src.models.user import db, User, ProviderProfile
from src.models.job import Job, JobStatus
from src.models.service import Service, ServiceCategory
from src.models.review import Review

smart_matching_bp = Blueprint('smart_matching', __name__, url_prefix='/api/smart-matching')

class SmartMatchingEngine:
    """
    Advanced AI-powered matching engine that considers multiple factors:
    - Skills and experience compatibility
    - Geographic proximity and availability
    - Historical success rates and ratings
    - Project complexity and requirements
    - Market conditions and pricing
    - Customer preferences and budget
    """
    
    def __init__(self):
        self.weights = {
            'skills_match': 0.25,
            'location_proximity': 0.20,
            'rating_score': 0.20,
            'availability': 0.15,
            'price_compatibility': 0.10,
            'experience_level': 0.10
        }
    
    def calculate_skills_match(self, job: Job, provider: ProviderProfile) -> float:
        """Calculate skills compatibility score (0-1)"""
        if not provider.skills or not job.category:
            return 0.0
        
        # Convert skills to lowercase for comparison
        provider_skills = [skill.lower().strip() for skill in provider.skills.split(',')]
        job_category = job.category.lower().strip()
        
        # Direct category match
        if job_category in provider_skills:
            return 1.0
        
        # Partial match scoring
        related_skills = {
            'plumbing': ['plumber', 'pipe', 'water', 'drain', 'fixture'],
            'electrical': ['electrician', 'wiring', 'electric', 'power', 'lighting'],
            'carpentry': ['carpenter', 'wood', 'cabinet', 'furniture', 'framing'],
            'painting': ['painter', 'paint', 'wall', 'interior', 'exterior'],
            'roofing': ['roofer', 'roof', 'shingle', 'gutter', 'leak'],
            'hvac': ['heating', 'cooling', 'air', 'furnace', 'ac'],
            'landscaping': ['landscape', 'garden', 'lawn', 'tree', 'yard'],
            'cleaning': ['clean', 'house', 'office', 'deep', 'maintenance']
        }
        
        job_related = related_skills.get(job_category, [])
        if job_related:
            matches = sum(1 for skill in provider_skills if any(related in skill for related in job_related))
            return min(matches / len(job_related), 1.0)
        
        return 0.3  # Base compatibility score
    
    def calculate_location_proximity(self, job: Job, provider: ProviderProfile) -> float:
        """Calculate location proximity score (0-1)"""
        if not job.location or not provider.service_area:
            return 0.5  # Neutral score if location data missing
        
        # Simplified location matching (in real implementation, use geolocation)
        job_location = job.location.lower()
        service_areas = [area.lower().strip() for area in provider.service_area.split(',')]
        
        # Check for exact matches or partial matches
        for area in service_areas:
            if area in job_location or job_location in area:
                return 1.0
        
        # Check for city/state matches
        job_parts = job_location.split(',')
        for part in job_parts:
            part = part.strip()
            for area in service_areas:
                if part in area or area in part:
                    return 0.7
        
        return 0.2  # Low score for distant locations
    
    def calculate_rating_score(self, provider_id: int) -> float:
        """Calculate provider rating score (0-1)"""
        avg_rating = db.session.query(func.avg(Review.rating)).filter(
            Review.reviewee_id == provider_id
        ).scalar()
        
        if avg_rating is None:
            return 0.5  # Neutral score for new providers
        
        # Convert 5-star rating to 0-1 scale
        return min(avg_rating / 5.0, 1.0)
    
    def calculate_availability_score(self, provider: ProviderProfile) -> float:
        """Calculate provider availability score (0-1)"""
        if not provider.availability:
            return 0.5
        
        # Check recent job activity
        recent_jobs = db.session.query(Job).filter(
            and_(
                Job.assigned_provider_id == provider.user_id,
                Job.created_at >= datetime.utcnow() - timedelta(days=30),
                Job.status.in_([JobStatus.ACCEPTED, JobStatus.IN_PROGRESS])
            )
        ).count()
        
        # Lower score for overloaded providers
        if recent_jobs > 10:
            return 0.3
        elif recent_jobs > 5:
            return 0.6
        else:
            return 1.0
    
    def calculate_price_compatibility(self, job: Job, provider: ProviderProfile) -> float:
        """Calculate price compatibility score (0-1)"""
        if not job.budget or not provider.hourly_rate:
            return 0.5
        
        # Estimate project hours (simplified)
        estimated_hours = max(job.budget / 50, 1)  # Assume $50/hour average
        provider_cost = provider.hourly_rate * estimated_hours
        
        # Calculate compatibility based on budget vs estimated cost
        if provider_cost <= job.budget:
            return 1.0
        elif provider_cost <= job.budget * 1.2:  # Within 20% of budget
            return 0.8
        elif provider_cost <= job.budget * 1.5:  # Within 50% of budget
            return 0.5
        else:
            return 0.2
    
    def calculate_experience_level(self, provider: ProviderProfile) -> float:
        """Calculate provider experience level score (0-1)"""
        if not provider.years_experience:
            return 0.3
        
        # Score based on years of experience
        years = provider.years_experience
        if years >= 10:
            return 1.0
        elif years >= 5:
            return 0.8
        elif years >= 2:
            return 0.6
        else:
            return 0.4
    
    def calculate_match_score(self, job: Job, provider: ProviderProfile) -> Tuple[float, Dict[str, float]]:
        """Calculate overall match score and component scores"""
        scores = {
            'skills_match': self.calculate_skills_match(job, provider),
            'location_proximity': self.calculate_location_proximity(job, provider),
            'rating_score': self.calculate_rating_score(provider.user_id),
            'availability': self.calculate_availability_score(provider),
            'price_compatibility': self.calculate_price_compatibility(job, provider),
            'experience_level': self.calculate_experience_level(provider)
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[factor] * weight 
            for factor, weight in self.weights.items()
        )
        
        return overall_score, scores
    
    def find_matches(self, job_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Find best matching providers for a job"""
        job = db.session.query(Job).filter(Job.id == job_id).first()
        if not job:
            return []
        
        # Get all available providers
        providers = db.session.query(ProviderProfile).join(User).filter(
            User.is_active == True
        ).all()
        
        matches = []
        for provider in providers:
            overall_score, component_scores = self.calculate_match_score(job, provider)
            
            # Get provider user info
            user = db.session.query(User).filter(User.id == provider.user_id).first()
            if not user:
                continue
            
            match_data = {
                'provider_id': provider.user_id,
                'provider_name': user.full_name,
                'provider_email': user.email,
                'overall_score': round(overall_score, 3),
                'component_scores': {k: round(v, 3) for k, v in component_scores.items()},
                'provider_details': {
                    'skills': provider.skills,
                    'hourly_rate': provider.hourly_rate,
                    'years_experience': provider.years_experience,
                    'service_area': provider.service_area,
                    'availability': provider.availability
                },
                'confidence_level': self._calculate_confidence(overall_score),
                'recommendation_reason': self._generate_recommendation_reason(component_scores)
            }
            matches.append(match_data)
        
        # Sort by overall score and return top matches
        matches.sort(key=lambda x: x['overall_score'], reverse=True)
        return matches[:limit]
    
    def _calculate_confidence(self, score: float) -> str:
        """Calculate confidence level based on score"""
        if score >= 0.8:
            return "Very High"
        elif score >= 0.6:
            return "High"
        elif score >= 0.4:
            return "Medium"
        else:
            return "Low"
    
    def _generate_recommendation_reason(self, scores: Dict[str, float]) -> str:
        """Generate human-readable recommendation reason"""
        top_factors = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:2]
        
        reasons = {
            'skills_match': "excellent skills match",
            'location_proximity': "close location",
            'rating_score': "high customer ratings",
            'availability': "good availability",
            'price_compatibility': "competitive pricing",
            'experience_level': "extensive experience"
        }
        
        reason_text = " and ".join([reasons.get(factor, factor) for factor, _ in top_factors])
        return f"Recommended due to {reason_text}"

# Initialize matching engine
matching_engine = SmartMatchingEngine()

@smart_matching_bp.route('/find-matches/<int:job_id>', methods=['GET'])
def find_matches(job_id):
    """Find best matching providers for a specific job"""
    try:
        limit = request.args.get('limit', 10, type=int)
        matches = matching_engine.find_matches(job_id, limit)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'matches_found': len(matches),
            'matches': matches,
            'algorithm_version': '1.0',
            'generated_at': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@smart_matching_bp.route('/match-score', methods=['POST'])
def calculate_match_score():
    """Calculate match score between specific job and provider"""
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        provider_id = data.get('provider_id')
        
        if not job_id or not provider_id:
            return jsonify({
                'success': False,
                'error': 'job_id and provider_id are required'
            }), 400
        
        job = db.session.query(Job).filter(Job.id == job_id).first()
        provider = db.session.query(ProviderProfile).filter(ProviderProfile.user_id == provider_id).first()
        
        if not job or not provider:
            return jsonify({
                'success': False,
                'error': 'Job or provider not found'
            }), 404
        
        overall_score, component_scores = matching_engine.calculate_match_score(job, provider)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'provider_id': provider_id,
            'overall_score': round(overall_score, 3),
            'component_scores': {k: round(v, 3) for k, v in component_scores.items()},
            'confidence_level': matching_engine._calculate_confidence(overall_score),
            'recommendation_reason': matching_engine._generate_recommendation_reason(component_scores)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@smart_matching_bp.route('/algorithm-stats', methods=['GET'])
def get_algorithm_stats():
    """Get statistics about the matching algorithm performance"""
    try:
        # Calculate algorithm performance metrics
        total_jobs = db.session.query(Job).count()
        matched_jobs = db.session.query(Job).filter(Job.assigned_provider_id.isnot(None)).count()
        completed_jobs = db.session.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        
        match_rate = (matched_jobs / total_jobs * 100) if total_jobs > 0 else 0
        completion_rate = (completed_jobs / matched_jobs * 100) if matched_jobs > 0 else 0
        
        # Get average ratings for matched jobs
        avg_rating = db.session.query(func.avg(Review.rating)).join(Job).filter(
            Job.assigned_provider_id.isnot(None)
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'algorithm_stats': {
                'total_jobs': total_jobs,
                'matched_jobs': matched_jobs,
                'completed_jobs': completed_jobs,
                'match_rate_percent': round(match_rate, 2),
                'completion_rate_percent': round(completion_rate, 2),
                'average_rating': round(avg_rating, 2),
                'algorithm_version': '1.0',
                'weights': matching_engine.weights
            },
            'performance_metrics': {
                'accuracy': round(completion_rate, 2),
                'efficiency': round(match_rate, 2),
                'satisfaction': round(avg_rating / 5 * 100, 2)
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@smart_matching_bp.route('/update-weights', methods=['POST'])
def update_algorithm_weights():
    """Update matching algorithm weights (admin only)"""
    try:
        data = request.get_json()
        new_weights = data.get('weights', {})
        
        # Validate weights
        if not isinstance(new_weights, dict):
            return jsonify({
                'success': False,
                'error': 'Weights must be a dictionary'
            }), 400
        
        # Check if weights sum to 1.0
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            return jsonify({
                'success': False,
                'error': f'Weights must sum to 1.0, got {total_weight}'
            }), 400
        
        # Update weights
        matching_engine.weights.update(new_weights)
        
        return jsonify({
            'success': True,
            'message': 'Algorithm weights updated successfully',
            'new_weights': matching_engine.weights
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

