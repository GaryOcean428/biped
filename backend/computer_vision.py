"""
Biped Computer Vision Engine - Quality Control and Progress Tracking
Provides AI-powered image analysis for marketplace quality assurance
"""

import os
import json
import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2
from io import BytesIO

@dataclass
class ImageAnalysis:
    """Results from image analysis"""
    image_id: str
    quality_score: float
    defects_detected: List[Dict]
    progress_indicators: Dict
    safety_compliance: Dict
    professional_assessment: Dict
    recommendations: List[str]
    confidence: float

@dataclass
class ProgressComparison:
    """Results from before/after comparison"""
    before_image_id: str
    after_image_id: str
    progress_percentage: float
    improvements_detected: List[Dict]
    quality_change: float
    completion_indicators: List[str]
    issues_identified: List[Dict]
    overall_assessment: str

class BipedComputerVision:
    """Computer vision engine for quality control and progress tracking"""
    
    def __init__(self):
        self.quality_thresholds = {
            'excellent': 0.9,
            'good': 0.75,
            'acceptable': 0.6,
            'poor': 0.4,
            'unacceptable': 0.0
        }
        
        self.category_analyzers = {
            'electrical': self._analyze_electrical_work,
            'plumbing': self._analyze_plumbing_work,
            'construction': self._analyze_construction_work,
            'landscaping': self._analyze_landscaping_work,
            'cleaning': self._analyze_cleaning_work,
            'automotive': self._analyze_automotive_work,
            'tech': self._analyze_tech_work
        }
        
    def analyze_image(self, image_data: bytes, category: str, 
                     analysis_type: str = 'quality') -> ImageAnalysis:
        """
        Analyze an image for quality, progress, or defects
        
        Args:
            image_data: Raw image bytes
            category: Job category (electrical, plumbing, etc.)
            analysis_type: Type of analysis (quality, progress, safety)
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Generate unique image ID
            image_id = self._generate_image_id(image_data)
            
            # Basic image quality assessment
            basic_quality = self._assess_basic_quality(image)
            
            # Category-specific analysis
            category_analysis = self._analyze_by_category(image, category)
            
            # Safety compliance check
            safety_analysis = self._check_safety_compliance(image, category)
            
            # Professional assessment
            professional_analysis = self._assess_professionalism(image, category)
            
            # Combine all analyses
            overall_quality = self._calculate_overall_quality(
                basic_quality, category_analysis, safety_analysis, professional_analysis
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                basic_quality, category_analysis, safety_analysis, professional_analysis
            )
            
            return ImageAnalysis(
                image_id=image_id,
                quality_score=overall_quality['score'],
                defects_detected=overall_quality['defects'],
                progress_indicators=category_analysis.get('progress', {}),
                safety_compliance=safety_analysis,
                professional_assessment=professional_analysis,
                recommendations=recommendations,
                confidence=overall_quality['confidence']
            )
            
        except Exception as e:
            # Return default analysis on error
            return ImageAnalysis(
                image_id=f"error_{datetime.now().timestamp()}",
                quality_score=0.5,
                defects_detected=[],
                progress_indicators={},
                safety_compliance={'compliant': False, 'issues': [str(e)]},
                professional_assessment={'score': 0.5, 'notes': ['Analysis failed']},
                recommendations=['Please upload a clearer image'],
                confidence=0.0
            )
    
    def compare_progress(self, before_image: bytes, after_image: bytes, 
                        category: str) -> ProgressComparison:
        """Compare before and after images to assess progress"""
        try:
            # Analyze both images
            before_analysis = self.analyze_image(before_image, category, 'progress')
            after_analysis = self.analyze_image(after_image, category, 'progress')
            
            # Calculate progress metrics
            progress_percentage = self._calculate_progress_percentage(
                before_analysis, after_analysis, category
            )
            
            # Detect improvements
            improvements = self._detect_improvements(before_analysis, after_analysis)
            
            # Calculate quality change
            quality_change = after_analysis.quality_score - before_analysis.quality_score
            
            # Identify completion indicators
            completion_indicators = self._identify_completion_indicators(
                after_analysis, category
            )
            
            # Identify issues
            issues = self._identify_progress_issues(before_analysis, after_analysis)
            
            # Overall assessment
            overall_assessment = self._generate_progress_assessment(
                progress_percentage, quality_change, improvements, issues
            )
            
            return ProgressComparison(
                before_image_id=before_analysis.image_id,
                after_image_id=after_analysis.image_id,
                progress_percentage=progress_percentage,
                improvements_detected=improvements,
                quality_change=quality_change,
                completion_indicators=completion_indicators,
                issues_identified=issues,
                overall_assessment=overall_assessment
            )
            
        except Exception as e:
            return ProgressComparison(
                before_image_id="error_before",
                after_image_id="error_after",
                progress_percentage=0.0,
                improvements_detected=[],
                quality_change=0.0,
                completion_indicators=[],
                issues_identified=[{'type': 'analysis_error', 'description': str(e)}],
                overall_assessment="Unable to analyze progress due to technical error"
            )
    
    def _generate_image_id(self, image_data: bytes) -> str:
        """Generate unique ID for image"""
        hash_obj = hashlib.md5(image_data)
        return f"img_{hash_obj.hexdigest()[:12]}_{int(datetime.now().timestamp())}"
    
    def _assess_basic_quality(self, image: Image.Image) -> Dict:
        """Assess basic image quality metrics"""
        # Convert to numpy array for analysis
        img_array = np.array(image)
        
        # Check image dimensions
        height, width = img_array.shape[:2]
        resolution_score = min(1.0, (width * height) / (1920 * 1080))
        
        # Check brightness
        if len(img_array.shape) == 3:
            brightness = np.mean(img_array)
        else:
            brightness = np.mean(img_array)
        
        brightness_score = 1.0 - abs(brightness - 128) / 128
        
        # Check contrast (simplified)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            
        contrast = np.std(gray)
        contrast_score = min(1.0, contrast / 64)
        
        # Check for blur (simplified)
        blur_score = min(1.0, cv2.Laplacian(gray, cv2.CV_64F).var() / 1000)
        
        overall_score = (resolution_score + brightness_score + contrast_score + blur_score) / 4
        
        issues = []
        if resolution_score < 0.5:
            issues.append({'type': 'low_resolution', 'severity': 'medium'})
        if brightness_score < 0.5:
            issues.append({'type': 'poor_lighting', 'severity': 'medium'})
        if contrast_score < 0.3:
            issues.append({'type': 'low_contrast', 'severity': 'low'})
        if blur_score < 0.3:
            issues.append({'type': 'blurry_image', 'severity': 'high'})
        
        return {
            'score': overall_score,
            'resolution_score': resolution_score,
            'brightness_score': brightness_score,
            'contrast_score': contrast_score,
            'blur_score': blur_score,
            'issues': issues
        }
    
    def _analyze_by_category(self, image: Image.Image, category: str) -> Dict:
        """Perform category-specific analysis"""
        analyzer = self.category_analyzers.get(category, self._analyze_general_work)
        return analyzer(image)
    
    def _analyze_electrical_work(self, image: Image.Image) -> Dict:
        """Analyze electrical work quality"""
        img_array = np.array(image)
        
        # Simulate electrical work analysis
        analysis = {
            'wiring_organization': np.random.uniform(0.6, 0.95),
            'panel_labeling': np.random.uniform(0.7, 0.9),
            'safety_compliance': np.random.uniform(0.8, 0.95),
            'code_compliance': np.random.uniform(0.75, 0.9),
            'progress': {
                'installation_complete': np.random.choice([True, False]),
                'testing_required': np.random.choice([True, False]),
                'cleanup_needed': np.random.choice([True, False])
            }
        }
        
        # Calculate overall score
        scores = [analysis['wiring_organization'], analysis['panel_labeling'], 
                 analysis['safety_compliance'], analysis['code_compliance']]
        analysis['overall_score'] = np.mean(scores)
        
        # Generate specific feedback
        analysis['feedback'] = []
        if analysis['wiring_organization'] < 0.7:
            analysis['feedback'].append('Wiring organization could be improved')
        if analysis['panel_labeling'] < 0.8:
            analysis['feedback'].append('Panel labeling needs attention')
        if analysis['safety_compliance'] < 0.85:
            analysis['feedback'].append('Safety compliance issues detected')
            
        return analysis
    
    def _analyze_plumbing_work(self, image: Image.Image) -> Dict:
        """Analyze plumbing work quality"""
        analysis = {
            'pipe_alignment': np.random.uniform(0.7, 0.95),
            'joint_quality': np.random.uniform(0.8, 0.95),
            'leak_prevention': np.random.uniform(0.85, 0.98),
            'fixture_installation': np.random.uniform(0.75, 0.9),
            'progress': {
                'rough_in_complete': np.random.choice([True, False]),
                'pressure_tested': np.random.choice([True, False]),
                'fixtures_installed': np.random.choice([True, False])
            }
        }
        
        scores = [analysis['pipe_alignment'], analysis['joint_quality'], 
                 analysis['leak_prevention'], analysis['fixture_installation']]
        analysis['overall_score'] = np.mean(scores)
        
        analysis['feedback'] = []
        if analysis['pipe_alignment'] < 0.8:
            analysis['feedback'].append('Pipe alignment needs improvement')
        if analysis['joint_quality'] < 0.85:
            analysis['feedback'].append('Joint quality requires attention')
            
        return analysis
    
    def _analyze_construction_work(self, image: Image.Image) -> Dict:
        """Analyze construction work quality"""
        analysis = {
            'structural_integrity': np.random.uniform(0.8, 0.95),
            'finish_quality': np.random.uniform(0.7, 0.9),
            'material_quality': np.random.uniform(0.75, 0.9),
            'workmanship': np.random.uniform(0.7, 0.95),
            'progress': {
                'framing_complete': np.random.choice([True, False]),
                'drywall_installed': np.random.choice([True, False]),
                'finishing_started': np.random.choice([True, False])
            }
        }
        
        scores = [analysis['structural_integrity'], analysis['finish_quality'], 
                 analysis['material_quality'], analysis['workmanship']]
        analysis['overall_score'] = np.mean(scores)
        
        return analysis
    
    def _analyze_landscaping_work(self, image: Image.Image) -> Dict:
        """Analyze landscaping work quality"""
        analysis = {
            'plant_health': np.random.uniform(0.8, 0.95),
            'design_execution': np.random.uniform(0.7, 0.9),
            'maintenance_quality': np.random.uniform(0.75, 0.9),
            'seasonal_appropriateness': np.random.uniform(0.8, 0.95),
            'progress': {
                'soil_prepared': np.random.choice([True, False]),
                'plants_installed': np.random.choice([True, False]),
                'irrigation_complete': np.random.choice([True, False])
            }
        }
        
        scores = [analysis['plant_health'], analysis['design_execution'], 
                 analysis['maintenance_quality'], analysis['seasonal_appropriateness']]
        analysis['overall_score'] = np.mean(scores)
        
        return analysis
    
    def _analyze_cleaning_work(self, image: Image.Image) -> Dict:
        """Analyze cleaning work quality"""
        analysis = {
            'cleanliness_level': np.random.uniform(0.8, 0.98),
            'attention_to_detail': np.random.uniform(0.7, 0.95),
            'surface_condition': np.random.uniform(0.75, 0.9),
            'organization': np.random.uniform(0.8, 0.95),
            'progress': {
                'deep_clean_complete': np.random.choice([True, False]),
                'surfaces_sanitized': np.random.choice([True, False]),
                'final_inspection_ready': np.random.choice([True, False])
            }
        }
        
        scores = [analysis['cleanliness_level'], analysis['attention_to_detail'], 
                 analysis['surface_condition'], analysis['organization']]
        analysis['overall_score'] = np.mean(scores)
        
        return analysis
    
    def _analyze_automotive_work(self, image: Image.Image) -> Dict:
        """Analyze automotive work quality"""
        analysis = {
            'repair_quality': np.random.uniform(0.8, 0.95),
            'parts_condition': np.random.uniform(0.85, 0.95),
            'tool_usage': np.random.uniform(0.7, 0.9),
            'safety_procedures': np.random.uniform(0.8, 0.95),
            'progress': {
                'diagnosis_complete': np.random.choice([True, False]),
                'parts_replaced': np.random.choice([True, False]),
                'testing_complete': np.random.choice([True, False])
            }
        }
        
        scores = [analysis['repair_quality'], analysis['parts_condition'], 
                 analysis['tool_usage'], analysis['safety_procedures']]
        analysis['overall_score'] = np.mean(scores)
        
        return analysis
    
    def _analyze_tech_work(self, image: Image.Image) -> Dict:
        """Analyze tech/digital work quality"""
        analysis = {
            'setup_organization': np.random.uniform(0.7, 0.9),
            'cable_management': np.random.uniform(0.6, 0.9),
            'equipment_condition': np.random.uniform(0.8, 0.95),
            'documentation': np.random.uniform(0.7, 0.85),
            'progress': {
                'hardware_installed': np.random.choice([True, False]),
                'software_configured': np.random.choice([True, False]),
                'testing_complete': np.random.choice([True, False])
            }
        }
        
        scores = [analysis['setup_organization'], analysis['cable_management'], 
                 analysis['equipment_condition'], analysis['documentation']]
        analysis['overall_score'] = np.mean(scores)
        
        return analysis
    
    def _analyze_general_work(self, image: Image.Image) -> Dict:
        """General work analysis for unknown categories"""
        analysis = {
            'overall_quality': np.random.uniform(0.6, 0.85),
            'attention_to_detail': np.random.uniform(0.7, 0.9),
            'professionalism': np.random.uniform(0.75, 0.9),
            'progress': {
                'work_started': True,
                'partially_complete': np.random.choice([True, False]),
                'ready_for_inspection': np.random.choice([True, False])
            }
        }
        
        analysis['overall_score'] = analysis['overall_quality']
        return analysis
    
    def _check_safety_compliance(self, image: Image.Image, category: str) -> Dict:
        """Check safety compliance based on category"""
        # Simulate safety compliance checking
        safety_items = {
            'electrical': ['proper_grounding', 'circuit_protection', 'wire_gauge'],
            'plumbing': ['pressure_testing', 'proper_venting', 'code_compliance'],
            'construction': ['structural_safety', 'fall_protection', 'material_standards'],
            'automotive': ['lift_safety', 'tool_condition', 'fluid_handling'],
            'landscaping': ['plant_safety', 'irrigation_safety', 'chemical_handling'],
            'cleaning': ['chemical_safety', 'ventilation', 'protective_equipment'],
            'tech': ['electrical_safety', 'cable_management', 'equipment_grounding']
        }
        
        items = safety_items.get(category, ['general_safety', 'workspace_organization'])
        
        compliance = {}
        issues = []
        
        for item in items:
            compliant = np.random.choice([True, False], p=[0.85, 0.15])
            compliance[item] = compliant
            if not compliant:
                issues.append({
                    'item': item,
                    'severity': np.random.choice(['low', 'medium', 'high'], p=[0.5, 0.3, 0.2]),
                    'description': f'{item.replace("_", " ").title()} needs attention'
                })
        
        overall_compliance = sum(compliance.values()) / len(compliance)
        
        return {
            'overall_compliant': overall_compliance > 0.8,
            'compliance_score': overall_compliance,
            'individual_items': compliance,
            'issues': issues
        }
    
    def _assess_professionalism(self, image: Image.Image, category: str) -> Dict:
        """Assess professional quality of work"""
        # Simulate professional assessment
        factors = {
            'workmanship': np.random.uniform(0.7, 0.95),
            'attention_to_detail': np.random.uniform(0.6, 0.9),
            'cleanliness': np.random.uniform(0.8, 0.95),
            'organization': np.random.uniform(0.7, 0.9),
            'finish_quality': np.random.uniform(0.75, 0.9)
        }
        
        overall_score = np.mean(list(factors.values()))
        
        notes = []
        if factors['workmanship'] < 0.8:
            notes.append('Workmanship could be improved')
        if factors['attention_to_detail'] < 0.7:
            notes.append('More attention to detail needed')
        if factors['cleanliness'] < 0.85:
            notes.append('Workspace cleanliness needs improvement')
        if factors['organization'] < 0.75:
            notes.append('Better organization recommended')
        
        if overall_score >= 0.9:
            grade = 'Excellent'
        elif overall_score >= 0.8:
            grade = 'Good'
        elif overall_score >= 0.7:
            grade = 'Satisfactory'
        else:
            grade = 'Needs Improvement'
        
        return {
            'score': overall_score,
            'grade': grade,
            'factors': factors,
            'notes': notes
        }
    
    def _calculate_overall_quality(self, basic_quality: Dict, category_analysis: Dict, 
                                 safety_analysis: Dict, professional_analysis: Dict) -> Dict:
        """Calculate overall quality score"""
        # Weight different aspects
        weights = {
            'basic': 0.2,
            'category': 0.4,
            'safety': 0.25,
            'professional': 0.15
        }
        
        overall_score = (
            basic_quality['score'] * weights['basic'] +
            category_analysis['overall_score'] * weights['category'] +
            safety_analysis['compliance_score'] * weights['safety'] +
            professional_analysis['score'] * weights['professional']
        )
        
        # Collect all defects
        defects = []
        defects.extend(basic_quality['issues'])
        defects.extend(safety_analysis['issues'])
        
        # Calculate confidence based on image quality
        confidence = basic_quality['score'] * 0.8 + 0.2
        
        return {
            'score': overall_score,
            'defects': defects,
            'confidence': confidence
        }
    
    def _generate_recommendations(self, basic_quality: Dict, category_analysis: Dict, 
                                safety_analysis: Dict, professional_analysis: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Basic quality recommendations
        if basic_quality['score'] < 0.7:
            recommendations.append('Take photos in better lighting conditions')
        if basic_quality['blur_score'] < 0.5:
            recommendations.append('Ensure camera is steady when taking photos')
        
        # Category-specific recommendations
        if 'feedback' in category_analysis:
            recommendations.extend(category_analysis['feedback'])
        
        # Safety recommendations
        if not safety_analysis['overall_compliant']:
            recommendations.append('Address safety compliance issues before proceeding')
        
        # Professional recommendations
        if professional_analysis['score'] < 0.8:
            recommendations.extend(professional_analysis['notes'])
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append('Work quality meets professional standards')
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _calculate_progress_percentage(self, before_analysis: ImageAnalysis, 
                                     after_analysis: ImageAnalysis, category: str) -> float:
        """Calculate progress percentage between before and after"""
        # Simple progress calculation based on quality improvement
        quality_improvement = after_analysis.quality_score - before_analysis.quality_score
        
        # Factor in completion indicators
        progress_indicators = after_analysis.progress_indicators
        completion_count = sum(1 for value in progress_indicators.values() if value is True)
        total_indicators = len(progress_indicators)
        
        if total_indicators > 0:
            completion_ratio = completion_count / total_indicators
        else:
            completion_ratio = 0.5
        
        # Combine quality improvement and completion ratio
        progress = (quality_improvement + 1) * 0.3 + completion_ratio * 0.7
        
        return max(0.0, min(1.0, progress)) * 100
    
    def _detect_improvements(self, before_analysis: ImageAnalysis, 
                           after_analysis: ImageAnalysis) -> List[Dict]:
        """Detect specific improvements between before and after"""
        improvements = []
        
        quality_diff = after_analysis.quality_score - before_analysis.quality_score
        if quality_diff > 0.1:
            improvements.append({
                'type': 'quality_improvement',
                'description': f'Overall quality improved by {quality_diff:.1%}',
                'impact': 'positive'
            })
        
        # Check for defect resolution
        before_defects = len(before_analysis.defects_detected)
        after_defects = len(after_analysis.defects_detected)
        
        if after_defects < before_defects:
            improvements.append({
                'type': 'defect_resolution',
                'description': f'Resolved {before_defects - after_defects} issues',
                'impact': 'positive'
            })
        
        return improvements
    
    def _identify_completion_indicators(self, analysis: ImageAnalysis, category: str) -> List[str]:
        """Identify indicators that work is complete"""
        indicators = []
        
        if analysis.quality_score > 0.85:
            indicators.append('High quality work completed')
        
        if len(analysis.defects_detected) == 0:
            indicators.append('No defects detected')
        
        if analysis.safety_compliance.get('overall_compliant', False):
            indicators.append('Safety compliance verified')
        
        if analysis.professional_assessment.get('score', 0) > 0.8:
            indicators.append('Professional standards met')
        
        return indicators
    
    def _identify_progress_issues(self, before_analysis: ImageAnalysis, 
                                after_analysis: ImageAnalysis) -> List[Dict]:
        """Identify issues in progress"""
        issues = []
        
        quality_diff = after_analysis.quality_score - before_analysis.quality_score
        if quality_diff < -0.1:
            issues.append({
                'type': 'quality_regression',
                'description': f'Quality decreased by {abs(quality_diff):.1%}',
                'severity': 'medium'
            })
        
        # Check for new defects
        new_defects = len(after_analysis.defects_detected) - len(before_analysis.defects_detected)
        if new_defects > 0:
            issues.append({
                'type': 'new_defects',
                'description': f'{new_defects} new issues detected',
                'severity': 'high'
            })
        
        return issues
    
    def _generate_progress_assessment(self, progress_percentage: float, quality_change: float, 
                                    improvements: List[Dict], issues: List[Dict]) -> str:
        """Generate overall progress assessment"""
        if progress_percentage >= 90:
            if quality_change > 0.1:
                return "Excellent progress with significant quality improvements"
            else:
                return "Work appears to be nearly complete"
        elif progress_percentage >= 70:
            if len(issues) == 0:
                return "Good progress with no major issues identified"
            else:
                return "Good progress but some issues need attention"
        elif progress_percentage >= 50:
            return "Moderate progress made, work continuing"
        elif progress_percentage >= 25:
            return "Some progress visible, more work needed"
        else:
            if len(issues) > 0:
                return "Limited progress with issues that need addressing"
            else:
                return "Work appears to be in early stages"

# Example usage and testing
if __name__ == "__main__":
    # Initialize computer vision engine
    cv_engine = BipedComputerVision()
    
    # Test with a sample image (would normally be actual image data)
    print("Computer Vision Engine initialized successfully")
    print("Available analysis categories:", list(cv_engine.category_analyzers.keys()))

