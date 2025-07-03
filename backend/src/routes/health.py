"""
Health Check Routes for Railway Deployment
Provides comprehensive system status for debugging
"""

import os
import sys
from datetime import datetime

from flask import Blueprint, jsonify

from ..models.user import db
from ..utils.cv_fallback import ComputerVisionChecker
from ..utils.redis_client import redis_client

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Comprehensive health check for Railway deployment"""

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "checks": {},
    }

    # Check Python dependencies
    try:
        import matplotlib
        import numpy
        import pandas
        import plotly
        import seaborn
        import sklearn

        health_status["checks"]["dependencies"] = {
            "status": "healthy",
            "pandas": pandas.__version__,
            "numpy": numpy.__version__,
            "sklearn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
            "seaborn": seaborn.__version__,
            "plotly": plotly.__version__,
        }
    except ImportError as e:
        health_status["checks"]["dependencies"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Check Redis connection
    try:
        if redis_client and redis_client.is_connected():
            redis_client.redis_client.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "connected": True,
                "url": (
                    os.environ.get("REDIS_URL", "not_set")[:20] + "..."
                    if os.environ.get("REDIS_URL")
                    else "not_set"
                ),
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "degraded",
                "connected": False,
                "message": "Redis not available, running in degraded mode",
            }
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}

    # Check database connection
    try:
        # Test database connection using SQLAlchemy
        db.session.execute(db.text("SELECT 1")).scalar()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "connected": True,
            "url": (
                os.environ.get("DATABASE_URL", "not_set")[:30] + "..."
                if os.environ.get("DATABASE_URL")
                else "not_set"
            ),
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }

    # Check computer vision capabilities
    try:
        cv_status = ComputerVisionChecker.get_cv_status()
        is_available = ComputerVisionChecker.is_cv_available()

        # Test basic OpenCV functionality
        cv_functional = False
        opencv_error = None
        try:
            import cv2
            import numpy as np

            test_img = np.zeros((10, 10, 3), dtype=np.uint8)
            cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
            cv_functional = True
        except Exception as e:
            opencv_error = str(e)

        health_status["checks"]["computer_vision"] = {
            "status": "healthy" if (is_available and cv_functional) else "degraded",
            "available": is_available,
            "functional": cv_functional,
            "opencv_version": cv_status.get("libraries", {})
            .get("opencv", {})
            .get("version", "unknown"),
            "pillow_version": cv_status.get("libraries", {})
            .get("pillow", {})
            .get("version", "unknown"),
            "numpy_version": cv_status.get("libraries", {})
            .get("numpy", {})
            .get("version", "unknown"),
            "environment": cv_status.get("environment", "unknown"),
            "headless": cv_status.get("headless", False),
            "error": opencv_error,
        }

        # Additional CV diagnostics
        if cv_functional:
            health_status["checks"]["computer_vision"]["capabilities"] = {
                "image_analysis": "available",
                "progress_comparison": "available",
                "quality_assessment": "available",
                "defect_detection": "available",
            }
        else:
            health_status["checks"]["computer_vision"]["capabilities"] = {
                "image_analysis": "fallback_mode",
                "progress_comparison": "fallback_mode",
                "quality_assessment": "fallback_mode",
                "defect_detection": "unavailable",
            }

    except Exception as e:
        health_status["checks"]["computer_vision"] = {
            "status": "unhealthy",
            "available": False,
            "error": str(e),
        }

    # System information
    health_status["system"] = {
        "python_version": sys.version,
        "platform": sys.platform,
        "working_directory": os.getcwd(),
        "environment_variables": {
            "PORT": os.environ.get("PORT", "not_set"),
            "ENVIRONMENT": os.environ.get("ENVIRONMENT", "not_set"),
            "DEBUG": os.environ.get("DEBUG", "not_set"),
            "DATA_DIR": os.environ.get("DATA_DIR", "not_set"),
            "PYTHONPATH": os.environ.get("PYTHONPATH", "not_set"),
        },
    }

    # Determine overall status
    if any(check.get("status") == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
        status_code = 503
    elif any(check.get("status") == "degraded" for check in health_status["checks"].values()):
        health_status["status"] = "degraded"
        status_code = 200
    else:
        status_code = 200

    return jsonify(health_status), status_code


@health_bp.route("/health/simple", methods=["GET"])
def simple_health_check():
    """Simple health check for Railway health monitoring"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200


@health_bp.route("/health/vision", methods=["GET"])
def vision_health_check():
    """Dedicated computer vision health check"""
    try:
        from ..utils.cv_fallback import ComputerVisionChecker, FallbackComputerVision

        # Get detailed CV status
        cv_status = ComputerVisionChecker.get_cv_status()
        is_available = ComputerVisionChecker.is_cv_available()

        # Test CV functionality with real operations
        cv_engine = FallbackComputerVision()
        capabilities = cv_engine.get_capabilities()

        # Test image analysis capability
        test_analysis_working = False
        analysis_error = None
        try:
            test_data = b"test_image_data_placeholder"
            analysis = cv_engine.analyze_image(test_data)
            test_analysis_working = True
        except Exception as e:
            analysis_error = str(e)

        vision_health = {
            "status": "healthy" if is_available else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "computer_vision": {
                "available": is_available,
                "libraries_status": cv_status.get("libraries", {}),
                "environment": cv_status.get("environment", "unknown"),
                "headless_mode": cv_status.get("headless", False),
            },
            "functionality": {
                "analysis_working": test_analysis_working,
                "analysis_error": analysis_error,
                "capabilities": capabilities.get("features", {}),
            },
            "recommendations": capabilities.get("recommendations", []),
            "deployment_ready": is_available and test_analysis_working,
        }

        status_code = 200 if vision_health["deployment_ready"] else 503
        return jsonify(vision_health), status_code

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                    "deployment_ready": False,
                }
            ),
            503,
        )


@health_bp.route("/health/dependencies", methods=["GET"])
def dependencies_check():
    """Check all Python dependencies"""
    dependencies = {}

    required_packages = [
        "pandas",
        "numpy",
        "sklearn",
        "matplotlib",
        "seaborn",
        "plotly",
        "flask",
        "redis",
        "celery",
        "gunicorn",
        "psycopg2",
        "sqlalchemy",
    ]

    for package in required_packages:
        try:
            module = __import__(package)
            dependencies[package] = {
                "status": "available",
                "version": getattr(module, "__version__", "unknown"),
            }
        except ImportError:
            dependencies[package] = {"status": "missing", "error": f"Module {package} not found"}

    return jsonify({"dependencies": dependencies, "timestamp": datetime.utcnow().isoformat()}), 200
