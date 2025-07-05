"""
AI API Routes for Biped Platform
Provides endpoints for AI-powered features
"""

import json
import logging
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from ai_engine import BipedAIEngine, JobRequirement, Provider
from flask import Blueprint, jsonify, request, session

# Create blueprint
ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

# Initialize AI engine
ai_engine = BipedAIEngine()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@ai_bp.route("/analyze-job", methods=["POST"])
def analyze_job():
    """Analyze job description using AI"""
    try:
        data = request.get_json()

        if not data or "description" not in data:
            return jsonify({"error": "Job description is required"}), 400

        description = data["description"]

        # Analyze the job description
        analysis = ai_engine.analyze_job_description(description)

        # Add additional insights
        insights = []

        if analysis["urgency"] == "asap":
            insights.append(
                {
                    "type": "warning",
                    "title": "Urgent Request",
                    "message": "This job requires immediate attention. Providers may charge premium rates.",
                }
            )

        if analysis["complexity"] == "complex":
            insights.append(
                {
                    "type": "info",
                    "title": "Complex Project",
                    "message": "This appears to be a complex project. Consider breaking it into phases.",
                }
            )

        if len(analysis["skills"]) > 1:
            insights.append(
                {
                    "type": "tip",
                    "title": "Multi-Skill Project",
                    "message": f'This project requires {len(analysis["skills"])} different skill sets. You may need multiple providers.',
                }
            )

        # Budget recommendations
        budget_min, budget_max = analysis["budget_range"]
        if budget_max > 5000:
            insights.append(
                {
                    "type": "info",
                    "title": "Large Budget Project",
                    "message": "Consider requesting detailed quotes and project timelines from providers.",
                }
            )

        response = {
            "analysis": analysis,
            "insights": insights,
            "suggestions": {
                "title_suggestions": _generate_title_suggestions(analysis),
                "category_suggestion": _suggest_category(analysis["skills"]),
                "timeline_recommendation": _recommend_timeline(
                    analysis["urgency"], analysis["complexity"]
                ),
            },
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error analyzing job: {str(e)}")
        return jsonify({"error": "Failed to analyze job description"}), 500


@ai_bp.route("/find-matches", methods=["POST"])
def find_matches():
    """Find AI-matched providers for a job"""
    try:
        data = request.get_json()

        required_fields = [
            "title",
            "description",
            "category",
            "budget_min",
            "budget_max",
            "location",
            "urgency",
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Create job requirement object
        job = JobRequirement(
            id=f"job_{datetime.now().timestamp()}",
            title=data["title"],
            description=data["description"],
            category=data["category"],
            budget_min=float(data["budget_min"]),
            budget_max=float(data["budget_max"]),
            location=tuple(data["location"]),  # [lat, lng]
            urgency=data["urgency"],
            skills_required=data.get("skills", []),
            posted_date=datetime.now(),
        )

        # Get mock providers (in real implementation, this would come from database)
        providers = _get_mock_providers(data["category"])

        # Find matches
        matches = ai_engine.find_matches(job, providers, top_k=5)

        # Format response
        response = {
            "job_id": job.id,
            "matches_found": len(matches),
            "matches": [
                {
                    "provider_id": match.provider_id,
                    "match_score": round(match.match_score * 100, 1),
                    "skill_match": round(match.skill_match * 100, 1),
                    "location_score": round(match.location_score * 100, 1),
                    "budget_compatibility": round(match.budget_compatibility * 100, 1),
                    "availability_score": round(match.availability_score * 100, 1),
                    "quality_score": round(match.quality_score * 100, 1),
                    "explanation": match.explanation,
                    "provider_info": _get_provider_info(match.provider_id, providers),
                }
                for match in matches
            ],
            "ai_insights": _generate_matching_insights(matches, job),
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error finding matches: {str(e)}")
        return jsonify({"error": "Failed to find provider matches"}), 500


@ai_bp.route("/predict-demand", methods=["POST"])
def predict_demand():
    """Predict demand for services in a specific area"""
    try:
        data = request.get_json()

        if not data or "category" not in data or "location" not in data:
            return jsonify({"error": "Category and location are required"}), 400

        category = data["category"]
        location = tuple(data["location"])
        days_ahead = data.get("days_ahead", 30)

        # Predict demand
        prediction = ai_engine.predict_demand(category, location, days_ahead)

        return jsonify(prediction)

    except Exception as e:
        logger.error(f"Error predicting demand: {str(e)}")
        return jsonify({"error": "Failed to predict demand"}), 500


@ai_bp.route("/optimize-pricing", methods=["POST"])
def optimize_pricing():
    """Provide pricing optimization recommendations"""
    try:
        data = request.get_json()

        required_fields = [
            "provider_id",
            "category",
            "current_rate",
            "rating",
            "completed_jobs",
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Create provider object
        provider = Provider(
            id=data["provider_id"],
            name=data.get("name", "Provider"),
            category=data["category"],
            skills=data.get("skills", []),
            location=tuple(data.get("location", [0, 0])),
            rating=float(data["rating"]),
            completed_jobs=int(data["completed_jobs"]),
            hourly_rate=float(data["current_rate"]),
            availability=data.get("availability", {}),
            response_time=data.get("response_time", 24),
            quality_score=float(data["rating"]) / 5.0,
        )

        # Get pricing optimization
        optimization = ai_engine.optimize_pricing(provider, {})

        return jsonify(optimization)

    except Exception as e:
        logger.error(f"Error optimizing pricing: {str(e)}")
        return jsonify({"error": "Failed to optimize pricing"}), 500


@ai_bp.route("/business-insights", methods=["POST"])
def business_insights():
    """Generate AI-powered business insights for providers"""
    try:
        data = request.get_json()

        provider_id = data.get("provider_id")
        if not provider_id:
            return jsonify({"error": "Provider ID is required"}), 400

        # Generate mock insights (in real implementation, this would analyze actual data)
        insights = _generate_business_insights(data)

        return jsonify(insights)

    except Exception as e:
        logger.error(f"Error generating business insights: {str(e)}")
        return jsonify({"error": "Failed to generate business insights"}), 500


@ai_bp.route("/smart-scheduling", methods=["POST"])
def smart_scheduling():
    """Provide AI-powered scheduling recommendations"""
    try:
        data = request.get_json()

        provider_id = data.get("provider_id")
        if not provider_id:
            return jsonify({"error": "Provider ID is required"}), 400

        # Generate scheduling recommendations
        recommendations = _generate_scheduling_recommendations(data)

        return jsonify(recommendations)

    except Exception as e:
        logger.error(f"Error generating scheduling recommendations: {str(e)}")
        return jsonify({"error": "Failed to generate scheduling recommendations"}), 500


# Helper functions


def _generate_title_suggestions(analysis):
    """Generate title suggestions based on analysis"""
    skills = analysis["skills"]
    complexity = analysis["complexity"]

    suggestions = []

    if "electrical" in skills:
        if complexity == "simple":
            suggestions.extend(
                [
                    "Electrical Outlet Installation",
                    "Light Fixture Replacement",
                    "Switch Repair",
                ]
            )
        elif complexity == "complex":
            suggestions.extend(
                [
                    "Complete Home Rewiring",
                    "Electrical Panel Upgrade",
                    "Smart Home Installation",
                ]
            )
        else:
            suggestions.extend(
                ["Electrical Repair", "Wiring Installation", "Circuit Installation"]
            )

    if "plumbing" in skills:
        if complexity == "simple":
            suggestions.extend(
                ["Leaky Faucet Repair", "Toilet Installation", "Drain Cleaning"]
            )
        elif complexity == "complex":
            suggestions.extend(
                [
                    "Bathroom Renovation Plumbing",
                    "Pipe Replacement",
                    "Water Heater Installation",
                ]
            )
        else:
            suggestions.extend(
                ["Plumbing Repair", "Pipe Installation", "Fixture Replacement"]
            )

    return suggestions[:3]


def _suggest_category(skills):
    """Suggest the most appropriate category"""
    if "electrical" in skills:
        return "electrical"
    elif "plumbing" in skills:
        return "plumbing"
    elif "construction" in skills:
        return "construction"
    elif "tech" in skills:
        return "tech"
    elif "automotive" in skills:
        return "automotive"
    elif "landscaping" in skills:
        return "landscaping"
    elif "cleaning" in skills:
        return "cleaning"
    else:
        return "construction"


def _recommend_timeline(urgency, complexity):
    """Recommend timeline based on urgency and complexity"""
    if urgency == "asap":
        return "Within 24-48 hours (urgent)"
    elif urgency == "week":
        if complexity == "complex":
            return "Within 1-2 weeks"
        else:
            return "Within 3-7 days"
    elif urgency == "month":
        if complexity == "complex":
            return "Within 2-4 weeks"
        else:
            return "Within 1-2 weeks"
    else:
        return "Flexible timeline"


def _get_mock_providers(category):
    """Get mock providers for testing (replace with database query)"""
    providers = [
        Provider(
            id="prov_001",
            name="Mike Johnson",
            category=category,
            skills=[category, "general"],
            location=(-33.8915, 151.2767),  # Sydney coordinates
            rating=4.8,
            completed_jobs=127,
            hourly_rate=85,
            availability={
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            response_time=2,
            quality_score=0.95,
        ),
        Provider(
            id="prov_002",
            name="Sarah Mitchell",
            category=category,
            skills=[category, "residential"],
            location=(-33.8688, 151.2093),
            rating=4.6,
            completed_jobs=89,
            hourly_rate=75,
            availability={
                "monday": True,
                "tuesday": True,
                "wednesday": False,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": False,
            },
            response_time=4,
            quality_score=0.88,
        ),
        Provider(
            id="prov_003",
            name="David Chen",
            category=category,
            skills=[category, "commercial"],
            location=(-33.8650, 151.2094),
            rating=4.9,
            completed_jobs=203,
            hourly_rate=95,
            availability={
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            response_time=1,
            quality_score=0.98,
        ),
        Provider(
            id="prov_004",
            name="Emma Wilson",
            category=category,
            skills=[category, "emergency"],
            location=(-33.8830, 151.2167),
            rating=4.7,
            completed_jobs=156,
            hourly_rate=90,
            availability={
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
            response_time=0.5,
            quality_score=0.92,
        ),
        Provider(
            id="prov_005",
            name="James Brown",
            category=category,
            skills=[category, "renovation"],
            location=(-33.8568, 151.2153),
            rating=4.5,
            completed_jobs=67,
            hourly_rate=70,
            availability={
                "monday": False,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": False,
            },
            response_time=6,
            quality_score=0.85,
        ),
    ]

    return providers


def _get_provider_info(provider_id, providers):
    """Get provider information by ID"""
    for provider in providers:
        if provider.id == provider_id:
            return {
                "id": provider.id,
                "name": provider.name,
                "rating": provider.rating,
                "completed_jobs": provider.completed_jobs,
                "hourly_rate": provider.hourly_rate,
                "response_time": provider.response_time,
                "skills": provider.skills,
            }
    return None


def _generate_matching_insights(matches, job):
    """Generate insights about the matching results"""
    insights = []

    if len(matches) == 0:
        insights.append(
            {
                "type": "warning",
                "title": "No Matches Found",
                "message": "No providers match your criteria. Consider adjusting your requirements.",
            }
        )
    elif len(matches) < 3:
        insights.append(
            {
                "type": "info",
                "title": "Limited Options",
                "message": f"Only {len(matches)} providers match your criteria. Consider expanding your search area.",
            }
        )
    else:
        insights.append(
            {
                "type": "success",
                "title": "Great Matches",
                "message": f"Found {len(matches)} excellent providers for your project.",
            }
        )

    # Analyze match quality
    if matches:
        avg_score = sum(match.match_score for match in matches) / len(matches)
        if avg_score > 0.8:
            insights.append(
                {
                    "type": "success",
                    "title": "High Quality Matches",
                    "message": "All matched providers are highly compatible with your requirements.",
                }
            )
        elif avg_score > 0.6:
            insights.append(
                {
                    "type": "info",
                    "title": "Good Matches",
                    "message": "Matched providers are well-suited for your project.",
                }
            )

    return insights


def _generate_business_insights(data):
    """Generate business insights for providers"""
    return {
        "revenue_trend": {
            "direction": "increasing",
            "percentage": 12,
            "message": "Your revenue is up 12% compared to last month",
        },
        "market_position": {
            "ranking": "top_20_percent",
            "message": "You're in the top 20% of providers in your category",
        },
        "opportunities": [
            {
                "type": "growth",
                "title": "Smart Home Services",
                "message": "Demand for smart home installations is up 35% in your area",
                "potential_revenue": 2500,
            },
            {
                "type": "pricing",
                "title": "Rate Optimization",
                "message": "You could increase rates by 8% and remain competitive",
                "potential_revenue": 1200,
            },
        ],
        "recommendations": [
            "Consider expanding into smart home services",
            "Update your profile with recent certifications",
            "Respond to quotes within 2 hours for better conversion",
        ],
    }


def _generate_scheduling_recommendations(data):
    """Generate scheduling recommendations"""
    return {
        "optimal_times": [
            {
                "day": "Tuesday",
                "time": "10:00 AM",
                "reason": "High customer availability",
            },
            {"day": "Wednesday", "time": "2:00 PM", "reason": "Low competition"},
            {"day": "Thursday", "time": "9:00 AM", "reason": "Best conversion rates"},
        ],
        "busy_periods": [
            {"period": "Monday mornings", "reason": "High demand, book early"},
            {"period": "Friday afternoons", "reason": "Weekend preparation rush"},
        ],
        "suggestions": [
            "Block out 3 hours on Tuesday for the Bondi Beach follow-up",
            "Consider offering emergency services on weekends for premium rates",
            "Schedule routine maintenance calls during slower periods",
        ],
    }
