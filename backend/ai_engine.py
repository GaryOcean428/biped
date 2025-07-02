"""
Biped AI Engine - Intelligent Job Matching and Analytics
Provides AI-powered features for the marketplace platform
"""

import json
import re
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import sqlite3
from geopy.distance import geodesic
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class JobRequirement:
    """Represents a job posting with requirements"""
    id: str
    title: str
    description: str
    category: str
    budget_min: float
    budget_max: float
    location: Tuple[float, float]  # (lat, lng)
    urgency: str  # 'asap', 'week', 'month', 'flexible'
    skills_required: List[str]
    posted_date: datetime
    
@dataclass
class Provider:
    """Represents a service provider"""
    id: str
    name: str
    category: str
    skills: List[str]
    location: Tuple[float, float]  # (lat, lng)
    rating: float
    completed_jobs: int
    hourly_rate: float
    availability: Dict[str, bool]  # day -> available
    response_time: float  # hours
    quality_score: float
    
@dataclass
class MatchResult:
    """Represents a job-provider match with scoring"""
    provider_id: str
    job_id: str
    match_score: float
    skill_match: float
    location_score: float
    budget_compatibility: float
    availability_score: float
    quality_score: float
    explanation: str

class BipedAIEngine:
    """Main AI engine for Biped marketplace"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.skill_weights = {
            'construction': 1.2,
            'electrical': 1.3,
            'plumbing': 1.3,
            'tech': 1.1,
            'automotive': 1.2,
            'landscaping': 1.0,
            'cleaning': 0.9
        }
        
    def analyze_job_description(self, description: str) -> Dict:
        """
        Analyze job description using AI to extract key information
        """
        # Extract urgency indicators
        urgency_keywords = {
            'asap': ['urgent', 'asap', 'immediately', 'emergency', 'today'],
            'week': ['this week', 'soon', 'quickly', 'within days'],
            'month': ['this month', 'few weeks', 'when possible'],
            'flexible': ['flexible', 'no rush', 'when convenient']
        }
        
        description_lower = description.lower()
        detected_urgency = 'flexible'
        
        for urgency, keywords in urgency_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                detected_urgency = urgency
                break
                
        # Extract complexity indicators
        complexity_keywords = {
            'simple': ['simple', 'basic', 'quick', 'small', 'minor'],
            'medium': ['medium', 'standard', 'typical', 'regular'],
            'complex': ['complex', 'major', 'large', 'extensive', 'complete']
        }
        
        complexity = 'medium'
        for level, keywords in complexity_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                complexity = level
                break
                
        # Extract skill requirements
        skill_patterns = {
            'electrical': ['electrical', 'wiring', 'circuit', 'panel', 'outlet'],
            'plumbing': ['plumbing', 'pipe', 'drain', 'water', 'leak'],
            'construction': ['construction', 'building', 'renovation', 'carpentry'],
            'tech': ['website', 'app', 'software', 'computer', 'digital'],
            'automotive': ['car', 'vehicle', 'engine', 'brake', 'automotive'],
            'landscaping': ['garden', 'lawn', 'landscape', 'tree', 'plant'],
            'cleaning': ['clean', 'maintenance', 'janitorial', 'housekeeping']
        }
        
        detected_skills = []
        for skill, patterns in skill_patterns.items():
            if any(pattern in description_lower for pattern in patterns):
                detected_skills.append(skill)
                
        # Estimate budget based on complexity and skills
        base_rates = {
            'electrical': 80,
            'plumbing': 75,
            'construction': 60,
            'tech': 70,
            'automotive': 65,
            'landscaping': 45,
            'cleaning': 35
        }
        
        complexity_multipliers = {
            'simple': 0.5,
            'medium': 1.0,
            'complex': 2.5
        }
        
        estimated_hours = {
            'simple': 2,
            'medium': 8,
            'complex': 24
        }
        
        if detected_skills:
            avg_rate = sum(base_rates.get(skill, 50) for skill in detected_skills) / len(detected_skills)
        else:
            avg_rate = 50
            
        hours = estimated_hours[complexity]
        multiplier = complexity_multipliers[complexity]
        
        budget_estimate = avg_rate * hours * multiplier
        budget_range = (budget_estimate * 0.7, budget_estimate * 1.3)
        
        return {
            'urgency': detected_urgency,
            'complexity': complexity,
            'skills': detected_skills,
            'budget_estimate': budget_estimate,
            'budget_range': budget_range,
            'estimated_hours': hours,
            'confidence': 0.85
        }
    
    def calculate_skill_match(self, job_skills: List[str], provider_skills: List[str]) -> float:
        """Calculate skill compatibility between job and provider"""
        if not job_skills or not provider_skills:
            return 0.0
            
        # Convert to sets for easier comparison
        job_set = set(job_skills)
        provider_set = set(provider_skills)
        
        # Calculate Jaccard similarity
        intersection = len(job_set.intersection(provider_set))
        union = len(job_set.union(provider_set))
        
        if union == 0:
            return 0.0
            
        base_score = intersection / union
        
        # Bonus for having all required skills
        if job_set.issubset(provider_set):
            base_score *= 1.2
            
        # Apply skill weights
        weighted_score = base_score
        for skill in job_set.intersection(provider_set):
            weight = self.skill_weights.get(skill, 1.0)
            weighted_score *= weight
            
        return min(weighted_score, 1.0)
    
    def calculate_location_score(self, job_location: Tuple[float, float], 
                                provider_location: Tuple[float, float]) -> float:
        """Calculate location compatibility score"""
        try:
            distance = geodesic(job_location, provider_location).kilometers
            
            # Score based on distance (closer is better)
            if distance <= 5:
                return 1.0
            elif distance <= 15:
                return 0.8
            elif distance <= 30:
                return 0.6
            elif distance <= 50:
                return 0.4
            else:
                return 0.2
        except:
            return 0.5  # Default score if calculation fails
    
    def calculate_budget_compatibility(self, job_budget: Tuple[float, float], 
                                     provider_rate: float, estimated_hours: float) -> float:
        """Calculate budget compatibility score"""
        job_min, job_max = job_budget
        provider_estimate = provider_rate * estimated_hours
        
        if job_min <= provider_estimate <= job_max:
            return 1.0
        elif provider_estimate < job_min:
            # Provider is cheaper - good for customer
            return 0.9
        else:
            # Provider is more expensive
            overage = (provider_estimate - job_max) / job_max
            if overage <= 0.2:  # Within 20% over budget
                return 0.7
            elif overage <= 0.5:  # Within 50% over budget
                return 0.4
            else:
                return 0.1
    
    def calculate_availability_score(self, urgency: str, provider_availability: Dict[str, bool],
                                   response_time: float) -> float:
        """Calculate availability compatibility score"""
        urgency_requirements = {
            'asap': {'max_response_time': 2, 'min_availability': 0.8},
            'week': {'max_response_time': 12, 'min_availability': 0.6},
            'month': {'max_response_time': 48, 'min_availability': 0.4},
            'flexible': {'max_response_time': 168, 'min_availability': 0.2}
        }
        
        requirements = urgency_requirements.get(urgency, urgency_requirements['flexible'])
        
        # Response time score
        response_score = 1.0 if response_time <= requirements['max_response_time'] else 0.5
        
        # Availability score
        available_days = sum(1 for available in provider_availability.values() if available)
        availability_ratio = available_days / 7
        availability_score = 1.0 if availability_ratio >= requirements['min_availability'] else availability_ratio
        
        return (response_score + availability_score) / 2
    
    def find_matches(self, job: JobRequirement, providers: List[Provider], 
                    top_k: int = 5) -> List[MatchResult]:
        """Find the best provider matches for a job"""
        matches = []
        
        # Analyze job for additional insights
        job_analysis = self.analyze_job_description(job.description)
        estimated_hours = job_analysis['estimated_hours']
        
        for provider in providers:
            # Skip if category doesn't match
            if provider.category != job.category:
                continue
                
            # Calculate individual scores
            skill_score = self.calculate_skill_match(job.skills_required, provider.skills)
            location_score = self.calculate_location_score(job.location, provider.location)
            budget_score = self.calculate_budget_compatibility(
                (job.budget_min, job.budget_max), provider.hourly_rate, estimated_hours
            )
            availability_score = self.calculate_availability_score(
                job.urgency, provider.availability, provider.response_time
            )
            
            # Quality score (provider rating and experience)
            quality_score = (provider.rating / 5.0) * 0.7 + min(provider.completed_jobs / 50, 1.0) * 0.3
            
            # Calculate overall match score with weights
            weights = {
                'skill': 0.3,
                'location': 0.2,
                'budget': 0.2,
                'availability': 0.15,
                'quality': 0.15
            }
            
            overall_score = (
                skill_score * weights['skill'] +
                location_score * weights['location'] +
                budget_score * weights['budget'] +
                availability_score * weights['availability'] +
                quality_score * weights['quality']
            )
            
            # Generate explanation
            explanation = self._generate_match_explanation(
                skill_score, location_score, budget_score, availability_score, quality_score
            )
            
            match = MatchResult(
                provider_id=provider.id,
                job_id=job.id,
                match_score=overall_score,
                skill_match=skill_score,
                location_score=location_score,
                budget_compatibility=budget_score,
                availability_score=availability_score,
                quality_score=quality_score,
                explanation=explanation
            )
            
            matches.append(match)
        
        # Sort by match score and return top k
        matches.sort(key=lambda x: x.match_score, reverse=True)
        return matches[:top_k]
    
    def _generate_match_explanation(self, skill: float, location: float, budget: float, 
                                  availability: float, quality: float) -> str:
        """Generate human-readable explanation for the match"""
        explanations = []
        
        if skill >= 0.8:
            explanations.append("Perfect skill match")
        elif skill >= 0.6:
            explanations.append("Good skill compatibility")
        else:
            explanations.append("Some skill overlap")
            
        if location >= 0.8:
            explanations.append("very close location")
        elif location >= 0.6:
            explanations.append("reasonable distance")
        else:
            explanations.append("further location")
            
        if budget >= 0.8:
            explanations.append("within budget")
        elif budget >= 0.6:
            explanations.append("slightly over budget")
        else:
            explanations.append("budget concerns")
            
        if availability >= 0.8:
            explanations.append("excellent availability")
        elif availability >= 0.6:
            explanations.append("good availability")
        else:
            explanations.append("limited availability")
            
        if quality >= 0.8:
            explanations.append("highly rated provider")
        elif quality >= 0.6:
            explanations.append("well-rated provider")
        else:
            explanations.append("newer provider")
        
        return ", ".join(explanations)
    
    def predict_demand(self, category: str, location: Tuple[float, float], 
                      days_ahead: int = 30) -> Dict:
        """Predict demand for services in a specific area"""
        # Simulate demand prediction based on historical patterns
        base_demand = {
            'construction': 0.7,
            'electrical': 0.6,
            'plumbing': 0.8,
            'tech': 0.5,
            'automotive': 0.6,
            'landscaping': 0.4,
            'cleaning': 0.9
        }
        
        # Seasonal adjustments
        current_month = datetime.now().month
        seasonal_multipliers = {
            'construction': [0.6, 0.7, 0.9, 1.1, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6],
            'electrical': [1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.3, 1.2, 1.0, 1.0, 1.0, 1.1],
            'plumbing': [1.2, 1.1, 1.0, 0.9, 0.8, 0.9, 1.0, 1.0, 0.9, 1.0, 1.1, 1.2],
            'tech': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            'automotive': [0.8, 0.9, 1.1, 1.2, 1.3, 1.2, 1.1, 1.0, 0.9, 1.0, 0.9, 0.8],
            'landscaping': [0.5, 0.6, 0.8, 1.2, 1.4, 1.3, 1.2, 1.1, 1.0, 0.9, 0.7, 0.5],
            'cleaning': [1.1, 1.0, 1.0, 1.1, 1.2, 1.1, 1.0, 1.0, 1.1, 1.2, 1.1, 1.2]
        }
        
        base = base_demand.get(category, 0.5)
        seasonal = seasonal_multipliers.get(category, [1.0] * 12)[current_month - 1]
        
        # Add some randomness for realism
        random_factor = random.uniform(0.8, 1.2)
        
        predicted_demand = base * seasonal * random_factor
        
        # Generate trend data
        trend_data = []
        for i in range(days_ahead):
            date = datetime.now() + timedelta(days=i)
            daily_demand = predicted_demand * random.uniform(0.7, 1.3)
            trend_data.append({
                'date': date.isoformat(),
                'demand': daily_demand,
                'confidence': 0.75
            })
        
        return {
            'category': category,
            'current_demand': predicted_demand,
            'trend': 'increasing' if seasonal > 1.0 else 'stable',
            'confidence': 0.75,
            'forecast': trend_data,
            'recommendations': self._generate_demand_recommendations(category, predicted_demand)
        }
    
    def _generate_demand_recommendations(self, category: str, demand: float) -> List[str]:
        """Generate recommendations based on demand prediction"""
        recommendations = []
        
        if demand > 0.8:
            recommendations.append(f"High demand expected for {category} services")
            recommendations.append("Consider increasing rates by 10-15%")
            recommendations.append("Ensure availability for urgent requests")
        elif demand > 0.6:
            recommendations.append(f"Moderate demand for {category} services")
            recommendations.append("Maintain current pricing strategy")
        else:
            recommendations.append(f"Lower demand period for {category}")
            recommendations.append("Consider promotional pricing")
            recommendations.append("Focus on quality and customer retention")
            
        return recommendations
    
    def optimize_pricing(self, provider: Provider, market_data: Dict) -> Dict:
        """Suggest optimal pricing for a provider"""
        category_rates = {
            'construction': {'min': 45, 'max': 85, 'avg': 65},
            'electrical': {'min': 60, 'max': 120, 'avg': 85},
            'plumbing': {'min': 55, 'max': 110, 'avg': 80},
            'tech': {'min': 50, 'max': 150, 'avg': 90},
            'automotive': {'min': 40, 'max': 100, 'avg': 70},
            'landscaping': {'min': 30, 'max': 70, 'avg': 50},
            'cleaning': {'min': 25, 'max': 60, 'avg': 40}
        }
        
        market_rate = category_rates.get(provider.category, {'avg': 50})['avg']
        
        # Adjust based on provider quality
        quality_multiplier = 0.8 + (provider.rating / 5.0) * 0.4
        experience_multiplier = 1.0 + min(provider.completed_jobs / 100, 0.3)
        
        suggested_rate = market_rate * quality_multiplier * experience_multiplier
        
        # Compare with current rate
        current_rate = provider.hourly_rate
        difference = suggested_rate - current_rate
        percentage_change = (difference / current_rate) * 100 if current_rate > 0 else 0
        
        return {
            'current_rate': current_rate,
            'suggested_rate': round(suggested_rate, 2),
            'market_average': market_rate,
            'difference': round(difference, 2),
            'percentage_change': round(percentage_change, 1),
            'recommendation': self._generate_pricing_recommendation(percentage_change),
            'confidence': 0.8
        }
    
    def _generate_pricing_recommendation(self, percentage_change: float) -> str:
        """Generate pricing recommendation based on analysis"""
        if percentage_change > 15:
            return "Consider increasing your rates significantly - you're underpricing your services"
        elif percentage_change > 5:
            return "Small rate increase recommended to match market value"
        elif percentage_change > -5:
            return "Your rates are well-positioned for the market"
        elif percentage_change > -15:
            return "Consider a small rate decrease to be more competitive"
        else:
            return "Your rates may be too high for the current market"

# Example usage and testing
if __name__ == "__main__":
    # Initialize AI engine
    ai_engine = BipedAIEngine()
    
    # Test job analysis
    test_description = """
    I need an urgent electrical panel upgrade for my home in Bondi Beach. 
    The current panel is old and needs to be completely replaced with a modern one. 
    This is a complex job that requires a licensed electrician with experience in residential work.
    """
    
    analysis = ai_engine.analyze_job_description(test_description)
    print("Job Analysis:", json.dumps(analysis, indent=2))
    
    # Test demand prediction
    demand = ai_engine.predict_demand('electrical', (-33.8915, 151.2767), 7)
    print("\nDemand Prediction:", json.dumps(demand, indent=2, default=str))

