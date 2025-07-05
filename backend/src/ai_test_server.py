"""
Biped AI Testing Server - Standalone AI routes for testing
"""

import logging
import os
import secrets
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_ai_test_app():
    """Create a simple app just for testing AI functionality"""

    try:
        from flask import Flask, jsonify, request
        from flask_cors import CORS
    except ImportError as e:
        logger.error(f"Missing required dependencies: {e}")
        raise

    app = Flask(__name__)

    # Basic configuration
    app.config["SECRET_KEY"] = secrets.token_hex(32)

    # Simple CORS
    CORS(app)

    # Import AI engines
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from ai_engine import BipedAIEngine, JobRequirement, Provider
        from enhanced_ai_engine import EnhancedBipedAI

        # Initialize both traditional and enhanced AI
        traditional_ai = BipedAIEngine()
        enhanced_ai = EnhancedBipedAI()

        logger.info("✅ Both traditional and enhanced AI engines imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import AI engines: {e}")
        traditional_ai = None
        enhanced_ai = None

    @app.route("/api/health")
    def health_check():
        """Health check endpoint"""
        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "traditional_ai": traditional_ai is not None,
                "enhanced_ai": enhanced_ai is not None,
                "ai_providers": (
                    {
                        provider.value: available
                        for provider, available in enhanced_ai.router.available_providers.items()
                    }
                    if enhanced_ai
                    else {}
                ),
            }
        )

    @app.route("/api/ai/analyze-job", methods=["POST"])
    def analyze_job():
        """Analyze job description using enhanced AI"""
        if not enhanced_ai:
            return jsonify({"error": "Enhanced AI engine not available"}), 500

        try:
            data = request.get_json()

            if not data or "description" not in data:
                return jsonify({"error": "Missing job description"}), 400

            description = data["description"]
            category = data.get("category", "general")

            # Use enhanced AI for analysis
            analysis = enhanced_ai.analyze_job_with_ai(description, category)

            return jsonify(
                {
                    "status": "success",
                    "analysis": analysis,
                    "category": category,
                    "timestamp": datetime.utcnow().isoformat(),
                    "enhanced_features": True,
                }
            )

        except Exception as e:
            logger.error(f"Error analyzing job: {str(e)}")
            return jsonify({"error": "Failed to analyze job description"}), 500

    @app.route("/api/ai/find-matches", methods=["POST"])
    def find_matches():
        """Find AI-matched providers for a job"""
        if not enhanced_ai and not traditional_ai:
            return jsonify({"error": "AI engines not available"}), 500

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

            # Get mock providers (simplified for testing)
            mock_providers = [
                Provider(
                    id="provider_1",
                    name="Test Provider 1",
                    category=data["category"],
                    skills=["electrical", "wiring", "safety"],
                    location=(-33.8688, 151.2093),  # Sydney
                    rating=4.5,
                    completed_jobs=25,
                    hourly_rate=75.0,
                    availability={"monday": True, "tuesday": True},
                    response_time=2.0,
                    quality_score=0.85,
                ),
                Provider(
                    id="provider_2",
                    name="Test Provider 2",
                    category=data["category"],
                    skills=["electrical", "installation"],
                    location=(-33.8765, 151.2063),  # Near Sydney
                    rating=4.2,
                    completed_jobs=18,
                    hourly_rate=80.0,
                    availability={"monday": True, "wednesday": True},
                    response_time=3.0,
                    quality_score=0.78,
                ),
            ]

            # Use enhanced AI for matching if available, fallback to traditional
            if enhanced_ai:
                job_data = {
                    "id": job.id,
                    "title": job.title,
                    "description": job.description,
                    "category": job.category,
                    "budget_min": job.budget_min,
                    "budget_max": job.budget_max,
                    "location": job.location,
                    "urgency": job.urgency,
                    "skills": job.skills_required,
                }
                result = enhanced_ai.enhanced_job_matching(job_data, mock_providers)
                matches = result["matches"]

                # Convert back to match objects for compatibility
                from dataclasses import make_dataclass

                MatchResult = make_dataclass(
                    "MatchResult",
                    [
                        "provider_id",
                        "match_score",
                        "skill_match",
                        "location_score",
                        "budget_compatibility",
                        "availability_score",
                        "quality_score",
                        "explanation",
                    ],
                )
                matches = [
                    MatchResult(
                        **{
                            k: v
                            for k, v in match.items()
                            if k
                            in [
                                "provider_id",
                                "match_score",
                                "skill_match",
                                "location_score",
                                "budget_compatibility",
                                "availability_score",
                                "quality_score",
                                "explanation",
                            ]
                        }
                    )
                    for match in matches
                ]
            else:
                matches = (
                    traditional_ai.find_matches(job, mock_providers, top_k=5)
                    if traditional_ai
                    else []
                )

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
                        "budget_compatibility": round(
                            match.budget_compatibility * 100, 1
                        ),
                        "availability_score": round(match.availability_score * 100, 1),
                        "quality_score": round(match.quality_score * 100, 1),
                        "explanation": match.explanation,
                    }
                    for match in matches
                ],
            }

            return jsonify(response)

        except Exception as e:
            logger.error(f"Error finding matches: {str(e)}")
            return jsonify({"error": "Failed to find matches"}), 500

    @app.route("/api/ai/transparency", methods=["GET"])
    def get_transparency_report():
        """Get AI transparency report"""
        if not enhanced_ai:
            return jsonify({"error": "Enhanced AI not available"}), 500

        try:
            report = enhanced_ai.get_transparency_report()
            return jsonify(
                {
                    "status": "success",
                    "transparency_report": report,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error generating transparency report: {str(e)}")
            return jsonify({"error": "Failed to generate transparency report"}), 500

    @app.route("/api/ai/predict-demand", methods=["POST"])
    def predict_demand():
        """Predict demand using enhanced AI"""
        if not enhanced_ai:
            return jsonify({"error": "Enhanced AI not available"}), 500

        try:
            data = request.get_json()

            required_fields = ["category", "location"]
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400

            category = data["category"]
            location = tuple(data["location"])
            days_ahead = data.get("days_ahead", 30)

            prediction = enhanced_ai.predict_demand_with_ai(
                category, location, days_ahead
            )

            return jsonify(
                {
                    "status": "success",
                    "prediction": prediction,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        except Exception as e:
            logger.error(f"Error predicting demand: {str(e)}")
            return jsonify({"error": "Failed to predict demand"}), 500

    @app.route("/")
    def index():
        """Landing page"""
        return jsonify(
            {
                "message": "Biped AI Testing Server",
                "status": "running",
                "ai_engine": traditional_ai is not None,
                "enhanced_ai": enhanced_ai is not None,
                "endpoints": [
                    "/api/health",
                    "/api/ai/analyze-job",
                    "/api/ai/find-matches",
                    "/api/ai/transparency",
                    "/api/ai/predict-demand",
                ],
            }
        )

    logger.info("✅ AI testing app created successfully")
    return app


# Create the app
app = create_ai_test_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting AI testing server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
