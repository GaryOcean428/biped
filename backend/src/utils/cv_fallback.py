"""
Computer Vision Fallback Utilities
Provides graceful degradation when CV features are unavailable
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MockImageAnalysis:
    """Mock results when computer vision is unavailable"""

    image_id: str
    quality_score: float = 0.8
    defects_detected: List[Dict] = None
    progress_indicators: Dict = None
    safety_compliance: Dict = None
    professional_assessment: Dict = None
    recommendations: List[str] = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.defects_detected is None:
            self.defects_detected = []
        if self.progress_indicators is None:
            self.progress_indicators = {"status": "analysis_unavailable"}
        if self.safety_compliance is None:
            self.safety_compliance = {"status": "manual_review_required"}
        if self.professional_assessment is None:
            self.professional_assessment = {"status": "cv_unavailable"}
        if self.recommendations is None:
            self.recommendations = ["Manual quality inspection recommended"]


@dataclass
class MockProgressComparison:
    """Mock progress comparison when CV is unavailable"""

    before_image_id: str
    after_image_id: str
    progress_percentage: float = 50.0
    improvements_detected: List[Dict] = None
    quality_change: float = 0.0
    completion_indicators: List[str] = None
    issues_identified: List[Dict] = None
    overall_assessment: str = "Manual review required - Computer vision unavailable"

    def __post_init__(self):
        if self.improvements_detected is None:
            self.improvements_detected = []
        if self.completion_indicators is None:
            self.completion_indicators = ["Manual assessment needed"]
        if self.issues_identified is None:
            self.issues_identified = []


class ComputerVisionChecker:
    """Utility to check computer vision availability"""

    @staticmethod
    def is_cv_available() -> bool:
        """Check if computer vision libraries are available"""
        try:
            import cv2

            # Test basic CV functionality
            import numpy as np

            test_img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
            return True
        except Exception as e:
            logger.warning(f"Computer vision not available: {e}")
            return False

    @staticmethod
    def get_cv_status() -> Dict[str, Any]:
        """Get detailed computer vision status"""
        status = {
            "available": False,
            "libraries": {},
            "environment": os.environ.get("ENVIRONMENT", "unknown"),
            "headless": os.environ.get("OPENCV_HEADLESS", "false").lower() == "true",
        }

        # Check OpenCV
        try:
            import cv2

            status["libraries"]["opencv"] = {
                "available": True,
                "version": cv2.__version__,
                "build_info": (
                    cv2.getBuildInformation()[:200] + "..."
                    if len(cv2.getBuildInformation()) > 200
                    else cv2.getBuildInformation()
                ),
            }
        except Exception as e:
            status["libraries"]["opencv"] = {"available": False, "error": str(e)}

        # Check PIL
        try:
            from PIL import Image

            status["libraries"]["pillow"] = {
                "available": True,
                "version": Image.__version__ if hasattr(Image, "__version__") else "unknown",
            }
        except Exception as e:
            status["libraries"]["pillow"] = {"available": False, "error": str(e)}

        # Check NumPy
        try:
            import numpy as np

            status["libraries"]["numpy"] = {"available": True, "version": np.__version__}
        except Exception as e:
            status["libraries"]["numpy"] = {"available": False, "error": str(e)}

        # Overall availability
        status["available"] = (
            status["libraries"].get("opencv", {}).get("available", False)
            and status["libraries"].get("pillow", {}).get("available", False)
            and status["libraries"].get("numpy", {}).get("available", False)
        )

        return status


class FallbackComputerVision:
    """Fallback computer vision implementation"""

    def __init__(self):
        self.cv_available = ComputerVisionChecker.is_cv_available()
        self.status = ComputerVisionChecker.get_cv_status()

        if self.cv_available:
            logger.info("Computer vision libraries available")
        else:
            logger.warning("Computer vision unavailable - using fallback mode")

    def analyze_image(self, image_data: bytes, image_id: str = None) -> MockImageAnalysis:
        """Analyze image with fallback to mock results"""
        if image_id is None:
            import hashlib

            image_id = hashlib.md5(image_data).hexdigest()[:8]

        if self.cv_available:
            try:
                # Try to use real computer vision
                from computer_vision import BipedComputerVision

                cv_engine = BipedComputerVision()
                return cv_engine.analyze_image(image_data, image_id)
            except Exception as e:
                logger.error(f"Computer vision analysis failed: {e}")

        # Return mock analysis
        return MockImageAnalysis(
            image_id=image_id,
            quality_score=0.75,  # Default reasonable score
            recommendations=[
                "Computer vision analysis unavailable",
                "Manual quality inspection recommended",
                "Upload clear, well-lit images for best results",
            ],
        )

    def compare_progress(
        self, before_data: bytes, after_data: bytes, category: str = "construction"
    ) -> MockProgressComparison:
        """Compare progress with fallback to mock results"""
        import hashlib

        before_id = hashlib.md5(before_data).hexdigest()[:8]
        after_id = hashlib.md5(after_data).hexdigest()[:8]

        if self.cv_available:
            try:
                # Try to use real computer vision
                from computer_vision import BipedComputerVision

                cv_engine = BipedComputerVision()
                return cv_engine.compare_progress(before_data, after_data, category)
            except Exception as e:
                logger.error(f"Progress comparison failed: {e}")

        # Return mock comparison
        return MockProgressComparison(
            before_image_id=before_id,
            after_image_id=after_id,
            overall_assessment="Manual review required - Computer vision analysis unavailable",
        )

    def get_capabilities(self) -> Dict[str, Any]:
        """Get current computer vision capabilities"""
        return {
            "computer_vision_available": self.cv_available,
            "status": self.status,
            "features": {
                "image_analysis": "fallback" if not self.cv_available else "full",
                "progress_comparison": "fallback" if not self.cv_available else "full",
                "quality_assessment": "fallback" if not self.cv_available else "full",
                "defect_detection": "unavailable" if not self.cv_available else "available",
            },
            "recommendations": (
                [
                    "Computer vision features running in fallback mode",
                    "Manual quality inspection recommended",
                    "Consider enabling computer vision for enhanced analysis",
                ]
                if not self.cv_available
                else [
                    "Full computer vision capabilities available",
                    "Automated quality analysis enabled",
                    "Progress tracking and defect detection active",
                ]
            ),
        }
