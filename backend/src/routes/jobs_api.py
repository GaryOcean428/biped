import random
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

jobs_api_bp = Blueprint("jobs_api", __name__)

# Sample data for demonstration
SAMPLE_JOBS = [
    {
        "id": 1,
        "title": "Kitchen Renovation - Full Remodel",
        "description": "Looking for experienced tradies to completely renovate my kitchen. Includes plumbing, electrical, tiling, and carpentry work. Need someone who can coordinate all trades and provide project management.",
        "location": "Sydney, NSW",
        "suburb": "Bondi",
        "budget_min": 15000,
        "budget_max": 25000,
        "budget_display": "$15,000 - $25,000",
        "category": "Renovation",
        "subcategory": "Kitchen Renovation",
        "posted_date": datetime.now() - timedelta(hours=2),
        "posted_display": "2 hours ago",
        "quotes_count": 8,
        "urgent": True,
        "status": "open",
        "customer_id": 1,
        "customer_name": "Sarah M.",
        "customer_rating": 4.8,
        "skills_required": ["Plumbing", "Electrical", "Tiling", "Carpentry"],
        "timeline": "4-6 weeks",
        "property_type": "Apartment",
    },
    {
        "id": 2,
        "title": "Bathroom Leak Repair - Urgent",
        "description": "Urgent repair needed for bathroom leak. Water damage visible on ceiling below. Need immediate assessment and repair. Available for inspection today.",
        "location": "Melbourne, VIC",
        "suburb": "Richmond",
        "budget_min": 500,
        "budget_max": 1500,
        "budget_display": "$500 - $1,500",
        "category": "Plumbing",
        "subcategory": "Leak Repair",
        "posted_date": datetime.now() - timedelta(hours=4),
        "posted_display": "4 hours ago",
        "quotes_count": 12,
        "urgent": True,
        "status": "open",
        "customer_id": 2,
        "customer_name": "Michael K.",
        "customer_rating": 4.6,
        "skills_required": ["Plumbing", "Waterproofing"],
        "timeline": "ASAP",
        "property_type": "House",
    },
    {
        "id": 3,
        "title": "Deck Construction - Outdoor Entertainment Area",
        "description": "Build new timber deck 6m x 4m with pergola for outdoor entertainment. Materials to be quoted separately. Looking for quality workmanship and design input.",
        "location": "Brisbane, QLD",
        "suburb": "New Farm",
        "budget_min": 8000,
        "budget_max": 12000,
        "budget_display": "$8,000 - $12,000",
        "category": "Carpentry",
        "subcategory": "Deck Construction",
        "posted_date": datetime.now() - timedelta(days=1),
        "posted_display": "1 day ago",
        "quotes_count": 5,
        "urgent": False,
        "status": "open",
        "customer_id": 3,
        "customer_name": "Emma L.",
        "customer_rating": 4.9,
        "skills_required": ["Carpentry", "Construction"],
        "timeline": "3-4 weeks",
        "property_type": "House",
    },
    {
        "id": 4,
        "title": "Electrical Safety Inspection",
        "description": "Annual electrical safety inspection required for rental property. Certificate needed for compliance. Property is currently vacant so flexible timing.",
        "location": "Perth, WA",
        "suburb": "Fremantle",
        "budget_min": 200,
        "budget_max": 400,
        "budget_display": "$200 - $400",
        "category": "Electrical",
        "subcategory": "Safety Inspection",
        "posted_date": datetime.now() - timedelta(days=2),
        "posted_display": "2 days ago",
        "quotes_count": 15,
        "urgent": False,
        "status": "open",
        "customer_id": 4,
        "customer_name": "David R.",
        "customer_rating": 4.7,
        "skills_required": ["Electrical", "Certification"],
        "timeline": "Within 2 weeks",
        "property_type": "Apartment",
    },
    {
        "id": 5,
        "title": "Garden Landscaping - Complete Makeover",
        "description": "Transform backyard into modern landscape design. Includes lawn, garden beds, irrigation, and feature lighting. Design consultation required.",
        "location": "Adelaide, SA",
        "suburb": "Norwood",
        "budget_min": 5000,
        "budget_max": 10000,
        "budget_display": "$5,000 - $10,000",
        "category": "Landscaping",
        "subcategory": "Garden Design",
        "posted_date": datetime.now() - timedelta(days=3),
        "posted_display": "3 days ago",
        "quotes_count": 7,
        "urgent": False,
        "status": "open",
        "customer_id": 5,
        "customer_name": "Lisa T.",
        "customer_rating": 4.5,
        "skills_required": ["Landscaping", "Garden Design", "Irrigation"],
        "timeline": "6-8 weeks",
        "property_type": "House",
    },
    {
        "id": 6,
        "title": "House Painting - Interior and Exterior",
        "description": "Full house painting required. 3 bedroom house, interior and exterior. Quality finish required, preparation work included. Color consultation welcome.",
        "location": "Hobart, TAS",
        "suburb": "Battery Point",
        "budget_min": 6000,
        "budget_max": 9000,
        "budget_display": "$6,000 - $9,000",
        "category": "Painting",
        "subcategory": "House Painting",
        "posted_date": datetime.now() - timedelta(hours=6),
        "posted_display": "6 hours ago",
        "quotes_count": 9,
        "urgent": False,
        "status": "open",
        "customer_id": 6,
        "customer_name": "James W.",
        "customer_rating": 4.8,
        "skills_required": ["Painting", "Surface Preparation"],
        "timeline": "2-3 weeks",
        "property_type": "House",
    },
]

SAMPLE_PROVIDERS = [
    {
        "id": 1,
        "name": "Mike's Premium Plumbing",
        "business_name": "Premium Plumbing Solutions Pty Ltd",
        "rating": 4.9,
        "reviews_count": 127,
        "specialties": ["Plumbing", "Gas Fitting", "Drainage", "Hot Water Systems"],
        "location": "Sydney, NSW",
        "suburbs_served": ["Bondi", "Coogee", "Randwick", "Maroubra", "Clovelly"],
        "verified": True,
        "insurance_verified": True,
        "license_number": "PL12345",
        "response_time": "Usually responds within 2 hours",
        "response_rate": 98,
        "completed_jobs": 340,
        "years_experience": 12,
        "hourly_rate_min": 80,
        "hourly_rate_max": 120,
        "availability": "Available this week",
        "profile_image": "/images/providers/mike-plumbing.jpg",
        "description": "Experienced plumber specializing in residential and commercial plumbing. Licensed and insured with 12+ years experience.",
        "services": [
            "Emergency plumbing repairs",
            "Bathroom renovations",
            "Kitchen plumbing",
            "Hot water system installation",
            "Blocked drain clearing",
            "Gas fitting and repairs",
        ],
    },
    {
        "id": 2,
        "name": "Elite Electrical Services",
        "business_name": "Elite Electrical Pty Ltd",
        "rating": 4.8,
        "reviews_count": 89,
        "specialties": [
            "Electrical",
            "Solar Installation",
            "Home Automation",
            "Safety Inspections",
        ],
        "location": "Melbourne, VIC",
        "suburbs_served": ["Richmond", "South Yarra", "Prahran", "Windsor", "Toorak"],
        "verified": True,
        "insurance_verified": True,
        "license_number": "EL67890",
        "response_time": "Usually responds within 1 hour",
        "response_rate": 95,
        "completed_jobs": 256,
        "years_experience": 8,
        "hourly_rate_min": 90,
        "hourly_rate_max": 140,
        "availability": "Available next week",
        "profile_image": "/images/providers/elite-electrical.jpg",
        "description": "Professional electrical contractor specializing in residential electrical work and solar installations.",
        "services": [
            "Electrical repairs and maintenance",
            "Solar panel installation",
            "Home automation systems",
            "Safety inspections and certificates",
            "LED lighting upgrades",
            "Switchboard upgrades",
        ],
    },
    {
        "id": 3,
        "name": "Precision Carpentry Co.",
        "business_name": "Precision Carpentry & Construction",
        "rating": 4.7,
        "reviews_count": 156,
        "specialties": ["Carpentry", "Renovation", "Custom Furniture", "Deck Construction"],
        "location": "Brisbane, QLD",
        "suburbs_served": [
            "New Farm",
            "Teneriffe",
            "Fortitude Valley",
            "Spring Hill",
            "Kangaroo Point",
        ],
        "verified": True,
        "insurance_verified": True,
        "license_number": "CP11111",
        "response_time": "Usually responds within 4 hours",
        "response_rate": 92,
        "completed_jobs": 423,
        "years_experience": 15,
        "hourly_rate_min": 70,
        "hourly_rate_max": 110,
        "availability": "Booking 2 weeks ahead",
        "profile_image": "/images/providers/precision-carpentry.jpg",
        "description": "Master carpenter with 15+ years experience in custom carpentry and home renovations.",
        "services": [
            "Custom carpentry work",
            "Kitchen and bathroom renovations",
            "Deck and pergola construction",
            "Built-in furniture",
            "Timber flooring",
            "General home repairs",
        ],
    },
]


@jobs_api_bp.route("/api/jobs", methods=["GET"])
def get_jobs():
    """Get all jobs with optional filtering"""
    try:
        # Get query parameters
        category = request.args.get("category")
        location = request.args.get("location")
        urgent_only = request.args.get("urgent") == "true"
        limit = int(request.args.get("limit", 20))

        # Filter jobs based on parameters
        filtered_jobs = SAMPLE_JOBS.copy()

        if category and category != "All Categories":
            filtered_jobs = [job for job in filtered_jobs if job["category"] == category]

        if location and location != "All Locations":
            filtered_jobs = [job for job in filtered_jobs if location in job["location"]]

        if urgent_only:
            filtered_jobs = [job for job in filtered_jobs if job["urgent"]]

        # Limit results
        filtered_jobs = filtered_jobs[:limit]

        return jsonify({"success": True, "jobs": filtered_jobs, "total": len(filtered_jobs)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@jobs_api_bp.route("/api/jobs/<int:job_id>", methods=["GET"])
def get_job(job_id):
    """Get specific job details"""
    try:
        job = next((job for job in SAMPLE_JOBS if job["id"] == job_id), None)

        if not job:
            return jsonify({"success": False, "error": "Job not found"}), 404

        return jsonify({"success": True, "job": job})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@jobs_api_bp.route("/api/providers", methods=["GET"])
def get_providers():
    """Get all service providers with optional filtering"""
    try:
        # Get query parameters
        specialty = request.args.get("specialty")
        location = request.args.get("location")
        verified_only = request.args.get("verified") == "true"
        limit = int(request.args.get("limit", 20))

        # Filter providers based on parameters
        filtered_providers = SAMPLE_PROVIDERS.copy()

        if specialty and specialty != "All Specialties":
            filtered_providers = [p for p in filtered_providers if specialty in p["specialties"]]

        if location and location != "All Locations":
            filtered_providers = [p for p in filtered_providers if location in p["location"]]

        if verified_only:
            filtered_providers = [p for p in filtered_providers if p["verified"]]

        # Limit results
        filtered_providers = filtered_providers[:limit]

        return jsonify(
            {"success": True, "providers": filtered_providers, "total": len(filtered_providers)}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@jobs_api_bp.route("/api/providers/<int:provider_id>", methods=["GET"])
def get_provider(provider_id):
    """Get specific provider details"""
    try:
        provider = next((p for p in SAMPLE_PROVIDERS if p["id"] == provider_id), None)

        if not provider:
            return jsonify({"success": False, "error": "Provider not found"}), 404

        return jsonify({"success": True, "provider": provider})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@jobs_api_bp.route("/api/categories", methods=["GET"])
def get_categories():
    """Get service categories with job counts"""
    try:
        categories = [
            {
                "name": "Plumbing",
                "icon": "🔧",
                "jobs": 247,
                "description": "Plumbing repairs, installations, and maintenance",
            },
            {
                "name": "Electrical",
                "icon": "⚡",
                "jobs": 189,
                "description": "Electrical work, installations, and safety inspections",
            },
            {
                "name": "Carpentry",
                "icon": "🔨",
                "jobs": 156,
                "description": "Custom carpentry, renovations, and repairs",
            },
            {
                "name": "Painting",
                "icon": "🎨",
                "jobs": 134,
                "description": "Interior and exterior painting services",
            },
            {
                "name": "Renovation",
                "icon": "🏠",
                "jobs": 98,
                "description": "Home and commercial renovations",
            },
            {
                "name": "Landscaping",
                "icon": "🌿",
                "jobs": 87,
                "description": "Garden design, landscaping, and maintenance",
            },
            {
                "name": "Cleaning",
                "icon": "🧽",
                "jobs": 76,
                "description": "Professional cleaning services",
            },
            {
                "name": "Handyman",
                "icon": "🛠️",
                "jobs": 65,
                "description": "General repairs and maintenance",
            },
        ]

        return jsonify({"success": True, "categories": categories})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@jobs_api_bp.route("/api/marketplace/stats", methods=["GET"])
def get_marketplace_stats():
    """Get marketplace statistics"""
    try:
        stats = {
            "active_jobs": 2847,
            "verified_tradies": 1256,
            "jobs_completed": 15432,
            "average_rating": 4.8,
            "total_quotes_sent": 45678,
            "response_time_avg": "2.3 hours",
        }

        return jsonify({"success": True, "stats": stats})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
