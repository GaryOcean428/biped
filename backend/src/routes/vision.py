"""
Computer Vision API Routes for Biped Platform
Provides endpoints for image analysis and quality control with graceful fallbacks
"""

import base64
import json
import logging
import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

# Import fallback computer vision system
from ..utils.cv_fallback import ComputerVisionChecker, FallbackComputerVision

# Create blueprint
vision_bp = Blueprint("vision", __name__, url_prefix="/api/vision")

# Initialize fallback computer vision engine
cv_engine = FallbackComputerVision()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@vision_bp.route("/analyze-image", methods=["POST"])
def analyze_image():
    """Analyze a single image for quality and defects"""
    try:
        # Check if image data is provided
        if "image" not in request.files and "image_data" not in request.form:
            return jsonify({"error": "No image provided"}), 400

        # Get category and analysis type
        category = request.form.get("category", "construction")
        analysis_type = request.form.get("analysis_type", "quality")

        # Get image data
        image_data = None

        if "image" in request.files:
            # File upload
            file = request.files["image"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400

            if file and allowed_file(file.filename):
                image_data = file.read()
            else:
                return jsonify({"error": "Invalid file type"}), 400

        elif "image_data" in request.form:
            # Base64 encoded image
            try:
                image_b64 = request.form["image_data"]
                # Remove data URL prefix if present
                if "," in image_b64:
                    image_b64 = image_b64.split(",")[1]
                image_data = base64.b64decode(image_b64)
            except Exception as e:
                return jsonify({"error": "Invalid base64 image data"}), 400

        if not image_data:
            return jsonify({"error": "Could not process image data"}), 400

        # Analyze the image
        analysis = cv_engine.analyze_image(image_data, category, analysis_type)

        # Format response
        response = {
            "image_id": analysis.image_id,
            "quality_score": round(analysis.quality_score * 100, 1),
            "quality_grade": _get_quality_grade(analysis.quality_score),
            "defects_detected": analysis.defects_detected,
            "progress_indicators": analysis.progress_indicators,
            "safety_compliance": {
                "compliant": analysis.safety_compliance.get("overall_compliant", False),
                "score": round(analysis.safety_compliance.get("compliance_score", 0) * 100, 1),
                "issues": analysis.safety_compliance.get("issues", []),
            },
            "professional_assessment": {
                "score": round(analysis.professional_assessment.get("score", 0) * 100, 1),
                "grade": analysis.professional_assessment.get("grade", "Unknown"),
                "notes": analysis.professional_assessment.get("notes", []),
            },
            "recommendations": analysis.recommendations,
            "confidence": round(analysis.confidence * 100, 1),
            "analysis_timestamp": datetime.now().isoformat(),
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return jsonify({"error": "Failed to analyze image"}), 500


@vision_bp.route("/compare-progress", methods=["POST"])
def compare_progress():
    """Compare before and after images to assess progress"""
    try:
        # Check for required images
        if "before_image" not in request.files or "after_image" not in request.files:
            return jsonify({"error": "Both before and after images are required"}), 400

        before_file = request.files["before_image"]
        after_file = request.files["after_image"]
        category = request.form.get("category", "construction")

        # Validate files
        if before_file.filename == "" or after_file.filename == "":
            return jsonify({"error": "No files selected"}), 400

        if not (allowed_file(before_file.filename) and allowed_file(after_file.filename)):
            return jsonify({"error": "Invalid file types"}), 400

        # Read image data
        before_data = before_file.read()
        after_data = after_file.read()

        # Compare progress
        comparison = cv_engine.compare_progress(before_data, after_data, category)

        # Format response
        response = {
            "before_image_id": comparison.before_image_id,
            "after_image_id": comparison.after_image_id,
            "progress_percentage": round(comparison.progress_percentage, 1),
            "progress_grade": _get_progress_grade(comparison.progress_percentage),
            "quality_change": round(comparison.quality_change * 100, 1),
            "improvements_detected": comparison.improvements_detected,
            "completion_indicators": comparison.completion_indicators,
            "issues_identified": comparison.issues_identified,
            "overall_assessment": comparison.overall_assessment,
            "comparison_timestamp": datetime.now().isoformat(),
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error comparing progress: {str(e)}")
        return jsonify({"error": "Failed to compare progress"}), 500


@vision_bp.route("/batch-analyze", methods=["POST"])
def batch_analyze():
    """Analyze multiple images in batch"""
    try:
        # Check for images
        if "images" not in request.files:
            return jsonify({"error": "No images provided"}), 400

        files = request.files.getlist("images")
        category = request.form.get("category", "construction")
        analysis_type = request.form.get("analysis_type", "quality")

        if len(files) == 0:
            return jsonify({"error": "No files selected"}), 400

        if len(files) > 10:  # Limit batch size
            return jsonify({"error": "Maximum 10 images allowed per batch"}), 400

        results = []

        for file in files:
            if file.filename == "" or not allowed_file(file.filename):
                continue

            try:
                image_data = file.read()
                analysis = cv_engine.analyze_image(image_data, category, analysis_type)

                result = {
                    "filename": secure_filename(file.filename),
                    "image_id": analysis.image_id,
                    "quality_score": round(analysis.quality_score * 100, 1),
                    "quality_grade": _get_quality_grade(analysis.quality_score),
                    "defects_count": len(analysis.defects_detected),
                    "safety_compliant": analysis.safety_compliance.get("overall_compliant", False),
                    "recommendations_count": len(analysis.recommendations),
                    "confidence": round(analysis.confidence * 100, 1),
                }

                results.append(result)

            except Exception as e:
                logger.error(f"Error analyzing {file.filename}: {str(e)}")
                results.append(
                    {"filename": secure_filename(file.filename), "error": "Failed to analyze image"}
                )

        # Calculate batch summary
        successful_analyses = [r for r in results if "error" not in r]

        if successful_analyses:
            avg_quality = sum(r["quality_score"] for r in successful_analyses) / len(
                successful_analyses
            )
            total_defects = sum(r["defects_count"] for r in successful_analyses)
            compliant_count = sum(1 for r in successful_analyses if r["safety_compliant"])
        else:
            avg_quality = 0
            total_defects = 0
            compliant_count = 0

        summary = {
            "total_images": len(files),
            "successful_analyses": len(successful_analyses),
            "failed_analyses": len(results) - len(successful_analyses),
            "average_quality_score": round(avg_quality, 1),
            "total_defects_detected": total_defects,
            "safety_compliant_count": compliant_count,
            "overall_grade": (
                _get_quality_grade(avg_quality / 100) if avg_quality > 0 else "Unknown"
            ),
        }

        response = {
            "summary": summary,
            "results": results,
            "batch_timestamp": datetime.now().isoformat(),
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        return jsonify({"error": "Failed to perform batch analysis"}), 500


@vision_bp.route("/quality-report", methods=["POST"])
def generate_quality_report():
    """Generate a comprehensive quality report for a job"""
    try:
        data = request.get_json()

        if not data or "job_id" not in data:
            return jsonify({"error": "Job ID is required"}), 400

        job_id = data["job_id"]
        category = data.get("category", "construction")

        # In a real implementation, this would fetch actual images from the database
        # For now, we'll generate a mock report

        report = _generate_mock_quality_report(job_id, category)

        return jsonify(report)

    except Exception as e:
        logger.error(f"Error generating quality report: {str(e)}")
        return jsonify({"error": "Failed to generate quality report"}), 500


@vision_bp.route("/defect-detection", methods=["POST"])
def detect_defects():
    """Specialized endpoint for defect detection"""
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image provided"}), 400

        file = request.files["image"]
        category = request.form.get("category", "construction")
        sensitivity = request.form.get("sensitivity", "medium")  # low, medium, high

        if file.filename == "" or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file"}), 400

        image_data = file.read()

        # Analyze for defects specifically
        analysis = cv_engine.analyze_image(image_data, category, "defects")

        # Filter and categorize defects by severity
        defects_by_severity = {"critical": [], "major": [], "minor": []}

        for defect in analysis.defects_detected:
            severity = defect.get("severity", "minor")
            if severity == "high":
                defects_by_severity["critical"].append(defect)
            elif severity == "medium":
                defects_by_severity["major"].append(defect)
            else:
                defects_by_severity["minor"].append(defect)

        response = {
            "image_id": analysis.image_id,
            "total_defects": len(analysis.defects_detected),
            "defects_by_severity": defects_by_severity,
            "risk_assessment": _assess_defect_risk(defects_by_severity),
            "immediate_actions": _get_immediate_actions(defects_by_severity),
            "confidence": round(analysis.confidence * 100, 1),
            "detection_timestamp": datetime.now().isoformat(),
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error detecting defects: {str(e)}")
        return jsonify({"error": "Failed to detect defects"}), 500


@vision_bp.route("/safety-inspection", methods=["POST"])
def safety_inspection():
    """Specialized endpoint for safety compliance checking"""
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image provided"}), 400

        file = request.files["image"]
        category = request.form.get("category", "construction")
        inspection_type = request.form.get("inspection_type", "general")

        if file.filename == "" or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file"}), 400

        image_data = file.read()

        # Analyze for safety compliance
        analysis = cv_engine.analyze_image(image_data, category, "safety")

        safety_data = analysis.safety_compliance

        response = {
            "image_id": analysis.image_id,
            "overall_compliant": safety_data.get("overall_compliant", False),
            "compliance_score": round(safety_data.get("compliance_score", 0) * 100, 1),
            "compliance_grade": _get_compliance_grade(safety_data.get("compliance_score", 0)),
            "individual_items": safety_data.get("individual_items", {}),
            "safety_issues": safety_data.get("issues", []),
            "critical_violations": [
                issue for issue in safety_data.get("issues", []) if issue.get("severity") == "high"
            ],
            "recommendations": analysis.recommendations,
            "inspection_timestamp": datetime.now().isoformat(),
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in safety inspection: {str(e)}")
        return jsonify({"error": "Failed to perform safety inspection"}), 500


# Helper functions


def _get_quality_grade(score):
    """Convert quality score to letter grade"""
    if score >= 0.9:
        return "A+"
    elif score >= 0.85:
        return "A"
    elif score >= 0.8:
        return "B+"
    elif score >= 0.75:
        return "B"
    elif score >= 0.7:
        return "C+"
    elif score >= 0.6:
        return "C"
    elif score >= 0.5:
        return "D"
    else:
        return "F"


def _get_progress_grade(percentage):
    """Convert progress percentage to descriptive grade"""
    if percentage >= 95:
        return "Complete"
    elif percentage >= 80:
        return "Nearly Complete"
    elif percentage >= 60:
        return "Good Progress"
    elif percentage >= 40:
        return "Moderate Progress"
    elif percentage >= 20:
        return "Early Progress"
    else:
        return "Just Started"


def _get_compliance_grade(score):
    """Convert compliance score to grade"""
    if score >= 0.95:
        return "Fully Compliant"
    elif score >= 0.85:
        return "Mostly Compliant"
    elif score >= 0.7:
        return "Partially Compliant"
    else:
        return "Non-Compliant"


def _assess_defect_risk(defects_by_severity):
    """Assess overall risk based on defects"""
    critical_count = len(defects_by_severity["critical"])
    major_count = len(defects_by_severity["major"])
    minor_count = len(defects_by_severity["minor"])

    if critical_count > 0:
        return {
            "level": "high",
            "description": f"{critical_count} critical defects require immediate attention",
        }
    elif major_count > 2:
        return {
            "level": "medium",
            "description": f"{major_count} major defects should be addressed soon",
        }
    elif major_count > 0 or minor_count > 5:
        return {"level": "low", "description": "Some defects present but not immediately critical"}
    else:
        return {"level": "minimal", "description": "No significant defects detected"}


def _get_immediate_actions(defects_by_severity):
    """Get immediate actions based on defects"""
    actions = []

    if len(defects_by_severity["critical"]) > 0:
        actions.append("Stop work immediately and address critical safety issues")
        actions.append("Contact supervisor or safety officer")

    if len(defects_by_severity["major"]) > 0:
        actions.append("Schedule repairs for major defects within 24 hours")
        actions.append("Document all major issues for quality review")

    if len(defects_by_severity["minor"]) > 3:
        actions.append("Plan to address minor issues during next maintenance window")

    if len(actions) == 0:
        actions.append("Continue with regular quality monitoring")

    return actions


def _generate_mock_quality_report(job_id, category):
    """Generate a mock quality report"""
    import random

    # Mock data for demonstration
    report = {
        "job_id": job_id,
        "category": category,
        "report_generated": datetime.now().isoformat(),
        "overall_quality_score": round(random.uniform(75, 95), 1),
        "total_images_analyzed": random.randint(5, 15),
        "defects_summary": {
            "total_defects": random.randint(0, 8),
            "critical": random.randint(0, 1),
            "major": random.randint(0, 3),
            "minor": random.randint(0, 5),
        },
        "safety_compliance": {
            "overall_compliant": random.choice([True, False]),
            "compliance_score": round(random.uniform(80, 98), 1),
            "violations_count": random.randint(0, 3),
        },
        "progress_tracking": {
            "completion_percentage": round(random.uniform(60, 100), 1),
            "milestones_completed": random.randint(3, 8),
            "estimated_completion": "2025-01-15",
        },
        "recommendations": [
            "Continue current quality standards",
            "Address minor defects during next visit",
            "Maintain excellent safety compliance",
        ],
        "quality_trend": "improving",
        "next_inspection_due": "2025-01-10",
    }

    return report


@vision_bp.route("/status", methods=["GET"])
def cv_status():
    """Get computer vision system status and capabilities"""
    try:
        status = cv_engine.get_capabilities()
        cv_check = ComputerVisionChecker.get_cv_status()

        return (
            jsonify(
                {
                    "status": "success",
                    "computer_vision": status,
                    "detailed_status": cv_check,
                    "timestamp": datetime.utcnow().isoformat(),
                    "environment": os.environ.get("ENVIRONMENT", "unknown"),
                    "message": "Computer vision status retrieved successfully",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting CV status: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "computer_vision_available": False,
                    "message": "Error retrieving computer vision status",
                }
            ),
            500,
        )


@vision_bp.route("/health", methods=["GET"])
def vision_health():
    """Health check for vision services"""
    try:
        is_available = ComputerVisionChecker.is_cv_available()

        return (
            jsonify(
                {
                    "status": "healthy" if is_available else "degraded",
                    "computer_vision_available": is_available,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": (
                        "Vision services operational"
                        if is_available
                        else "Vision services in fallback mode"
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Vision health check failed: {e}")
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Vision services health check failed",
                }
            ),
            503,
        )
