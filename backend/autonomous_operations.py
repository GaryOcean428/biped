"""
Biped Autonomous Operations Engine
Self-managing platform systems with predictive analytics and automated optimization
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import queue
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle

@dataclass
class PlatformMetrics:
    """Real-time platform metrics"""
    timestamp: datetime
    active_users: int
    active_providers: int
    jobs_posted_24h: int
    jobs_completed_24h: int
    average_response_time: float
    system_load: float
    error_rate: float
    revenue_24h: float
    user_satisfaction: float
    provider_satisfaction: float

@dataclass
class AnomalyAlert:
    """Anomaly detection alert"""
    id: str
    timestamp: datetime
    type: str
    severity: str  # low, medium, high, critical
    description: str
    affected_metrics: List[str]
    recommended_actions: List[str]
    auto_resolved: bool = False

@dataclass
class OptimizationAction:
    """Automated optimization action"""
    id: str
    timestamp: datetime
    action_type: str
    target_system: str
    parameters: Dict[str, Any]
    expected_impact: str
    status: str  # pending, executing, completed, failed
    actual_impact: Optional[Dict[str, float]] = None

class BipedAutonomousOperations:
    """Autonomous platform operations and analytics engine"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=10080)  # 7 days of minute-by-minute data
        self.anomaly_detector = None
        self.scaler = StandardScaler()
        self.alerts_queue = queue.Queue()
        self.optimization_queue = queue.Queue()
        self.running = False
        self.monitoring_thread = None
        
        # Performance baselines
        self.baselines = {
            'response_time': 2.0,  # seconds
            'error_rate': 0.02,    # 2%
            'user_satisfaction': 4.2,  # out of 5
            'provider_satisfaction': 4.0,
            'job_completion_rate': 0.85
        }
        
        # Optimization thresholds
        self.thresholds = {
            'high_load': 0.8,
            'high_error_rate': 0.05,
            'low_satisfaction': 3.5,
            'slow_response': 5.0
        }
        
        # Auto-scaling parameters
        self.scaling_config = {
            'min_instances': 1,
            'max_instances': 10,
            'target_cpu': 70,
            'scale_up_threshold': 80,
            'scale_down_threshold': 30
        }
        
        self._initialize_anomaly_detection()
        
    def start_monitoring(self):
        """Start autonomous monitoring and optimization"""
        if not self.running:
            self.running = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            logging.info("Autonomous monitoring started")
    
    def stop_monitoring(self):
        """Stop autonomous monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logging.info("Autonomous monitoring stopped")
    
    def collect_metrics(self) -> PlatformMetrics:
        """Collect current platform metrics"""
        # In a real implementation, this would collect actual metrics
        # For now, we'll simulate realistic metrics with some variation
        
        current_time = datetime.now()
        base_metrics = self._generate_realistic_metrics(current_time)
        
        metrics = PlatformMetrics(
            timestamp=current_time,
            active_users=base_metrics['active_users'],
            active_providers=base_metrics['active_providers'],
            jobs_posted_24h=base_metrics['jobs_posted_24h'],
            jobs_completed_24h=base_metrics['jobs_completed_24h'],
            average_response_time=base_metrics['average_response_time'],
            system_load=base_metrics['system_load'],
            error_rate=base_metrics['error_rate'],
            revenue_24h=base_metrics['revenue_24h'],
            user_satisfaction=base_metrics['user_satisfaction'],
            provider_satisfaction=base_metrics['provider_satisfaction']
        )
        
        # Store metrics
        self.metrics_history.append(metrics)
        
        return metrics
    
    def detect_anomalies(self, metrics: PlatformMetrics) -> List[AnomalyAlert]:
        """Detect anomalies in platform metrics"""
        alerts = []
        
        # Check against thresholds
        if metrics.average_response_time > self.thresholds['slow_response']:
            alerts.append(AnomalyAlert(
                id=f"slow_response_{int(time.time())}",
                timestamp=metrics.timestamp,
                type="performance",
                severity="high",
                description=f"Response time ({metrics.average_response_time:.2f}s) exceeds threshold",
                affected_metrics=["average_response_time"],
                recommended_actions=[
                    "Scale up server instances",
                    "Optimize database queries",
                    "Enable caching"
                ]
            ))
        
        if metrics.error_rate > self.thresholds['high_error_rate']:
            alerts.append(AnomalyAlert(
                id=f"high_errors_{int(time.time())}",
                timestamp=metrics.timestamp,
                type="reliability",
                severity="critical",
                description=f"Error rate ({metrics.error_rate:.1%}) exceeds threshold",
                affected_metrics=["error_rate"],
                recommended_actions=[
                    "Investigate error logs",
                    "Rollback recent deployments",
                    "Enable circuit breakers"
                ]
            ))
        
        if metrics.system_load > self.thresholds['high_load']:
            alerts.append(AnomalyAlert(
                id=f"high_load_{int(time.time())}",
                timestamp=metrics.timestamp,
                type="capacity",
                severity="medium",
                description=f"System load ({metrics.system_load:.1%}) is high",
                affected_metrics=["system_load"],
                recommended_actions=[
                    "Scale horizontally",
                    "Optimize resource usage",
                    "Load balance traffic"
                ]
            ))
        
        if metrics.user_satisfaction < self.thresholds['low_satisfaction']:
            alerts.append(AnomalyAlert(
                id=f"low_satisfaction_{int(time.time())}",
                timestamp=metrics.timestamp,
                type="quality",
                severity="medium",
                description=f"User satisfaction ({metrics.user_satisfaction:.1f}) below threshold",
                affected_metrics=["user_satisfaction"],
                recommended_actions=[
                    "Review recent user feedback",
                    "Improve matching algorithm",
                    "Enhance user experience"
                ]
            ))
        
        # Use ML-based anomaly detection if we have enough historical data
        if len(self.metrics_history) > 100 and self.anomaly_detector:
            ml_alerts = self._ml_anomaly_detection(metrics)
            alerts.extend(ml_alerts)
        
        return alerts
    
    def auto_optimize(self, metrics: PlatformMetrics, alerts: List[AnomalyAlert]) -> List[OptimizationAction]:
        """Automatically optimize platform based on metrics and alerts"""
        actions = []
        
        # Auto-scaling based on load
        if metrics.system_load > self.scaling_config['scale_up_threshold']:
            actions.append(OptimizationAction(
                id=f"scale_up_{int(time.time())}",
                timestamp=datetime.now(),
                action_type="scale_up",
                target_system="compute",
                parameters={"instances": min(self.scaling_config['max_instances'], 
                                           self._calculate_required_instances(metrics.system_load))},
                expected_impact="Reduce system load and improve response times",
                status="pending"
            ))
        
        elif metrics.system_load < self.scaling_config['scale_down_threshold']:
            actions.append(OptimizationAction(
                id=f"scale_down_{int(time.time())}",
                timestamp=datetime.now(),
                action_type="scale_down",
                target_system="compute",
                parameters={"instances": max(self.scaling_config['min_instances'], 
                                           self._calculate_required_instances(metrics.system_load))},
                expected_impact="Optimize costs while maintaining performance",
                status="pending"
            ))
        
        # Cache optimization for slow responses
        if metrics.average_response_time > self.baselines['response_time'] * 1.5:
            actions.append(OptimizationAction(
                id=f"cache_optimize_{int(time.time())}",
                timestamp=datetime.now(),
                action_type="cache_optimization",
                target_system="application",
                parameters={"cache_ttl": 300, "cache_size": "1GB"},
                expected_impact="Reduce response times by 30-50%",
                status="pending"
            ))
        
        # Database optimization for high load
        if metrics.system_load > 0.7:
            actions.append(OptimizationAction(
                id=f"db_optimize_{int(time.time())}",
                timestamp=datetime.now(),
                action_type="database_optimization",
                target_system="database",
                parameters={"connection_pool_size": 20, "query_timeout": 30},
                expected_impact="Improve database performance and reduce load",
                status="pending"
            ))
        
        # Matching algorithm optimization for low satisfaction
        if metrics.user_satisfaction < self.baselines['user_satisfaction'] * 0.9:
            actions.append(OptimizationAction(
                id=f"matching_optimize_{int(time.time())}",
                timestamp=datetime.now(),
                action_type="algorithm_optimization",
                target_system="matching",
                parameters={"learning_rate": 0.01, "retrain": True},
                expected_impact="Improve user satisfaction by 10-15%",
                status="pending"
            ))
        
        return actions
    
    def generate_predictive_insights(self) -> Dict[str, Any]:
        """Generate predictive insights based on historical data"""
        if len(self.metrics_history) < 24:  # Need at least 24 data points
            return {"status": "insufficient_data"}
        
        # Convert metrics to arrays for analysis
        recent_metrics = list(self.metrics_history)[-168:]  # Last 7 days
        
        # Predict trends
        trends = self._analyze_trends(recent_metrics)
        
        # Forecast demand
        demand_forecast = self._forecast_demand(recent_metrics)
        
        # Capacity planning
        capacity_recommendations = self._plan_capacity(recent_metrics, demand_forecast)
        
        # Revenue predictions
        revenue_forecast = self._forecast_revenue(recent_metrics)
        
        insights = {
            "generated_at": datetime.now().isoformat(),
            "trends": trends,
            "demand_forecast": demand_forecast,
            "capacity_recommendations": capacity_recommendations,
            "revenue_forecast": revenue_forecast,
            "optimization_opportunities": self._identify_optimization_opportunities(recent_metrics),
            "risk_assessment": self._assess_risks(recent_metrics)
        }
        
        return insights
    
    def get_platform_health_score(self) -> Dict[str, Any]:
        """Calculate overall platform health score"""
        if not self.metrics_history:
            return {"score": 0, "status": "no_data"}
        
        latest_metrics = self.metrics_history[-1]
        
        # Calculate component scores (0-100)
        performance_score = self._calculate_performance_score(latest_metrics)
        reliability_score = self._calculate_reliability_score(latest_metrics)
        satisfaction_score = self._calculate_satisfaction_score(latest_metrics)
        capacity_score = self._calculate_capacity_score(latest_metrics)
        
        # Weighted overall score
        weights = {
            'performance': 0.3,
            'reliability': 0.3,
            'satisfaction': 0.25,
            'capacity': 0.15
        }
        
        overall_score = (
            performance_score * weights['performance'] +
            reliability_score * weights['reliability'] +
            satisfaction_score * weights['satisfaction'] +
            capacity_score * weights['capacity']
        )
        
        # Determine status
        if overall_score >= 90:
            status = "excellent"
        elif overall_score >= 80:
            status = "good"
        elif overall_score >= 70:
            status = "fair"
        elif overall_score >= 60:
            status = "poor"
        else:
            status = "critical"
        
        return {
            "overall_score": round(overall_score, 1),
            "status": status,
            "component_scores": {
                "performance": round(performance_score, 1),
                "reliability": round(reliability_score, 1),
                "satisfaction": round(satisfaction_score, 1),
                "capacity": round(capacity_score, 1)
            },
            "timestamp": latest_metrics.timestamp.isoformat(),
            "recommendations": self._get_health_recommendations(overall_score, {
                "performance": performance_score,
                "reliability": reliability_score,
                "satisfaction": satisfaction_score,
                "capacity": capacity_score
            })
        }
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                
                # Detect anomalies
                alerts = self.detect_anomalies(metrics)
                
                # Queue alerts
                for alert in alerts:
                    self.alerts_queue.put(alert)
                
                # Auto-optimize if needed
                if alerts:
                    optimizations = self.auto_optimize(metrics, alerts)
                    for optimization in optimizations:
                        self.optimization_queue.put(optimization)
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _initialize_anomaly_detection(self):
        """Initialize ML-based anomaly detection"""
        try:
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
        except Exception as e:
            logging.warning(f"Could not initialize anomaly detection: {e}")
    
    def _generate_realistic_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Generate realistic metrics with time-based patterns"""
        # Time-based patterns
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        # Base values with realistic patterns
        if 9 <= hour <= 17 and day_of_week < 5:  # Business hours
            base_load = 0.6
            base_users = 150
            base_providers = 80
        elif 18 <= hour <= 22:  # Evening
            base_load = 0.8
            base_users = 200
            base_providers = 60
        else:  # Night/early morning
            base_load = 0.3
            base_users = 50
            base_providers = 20
        
        # Add some randomness
        load_variation = np.random.normal(0, 0.1)
        user_variation = np.random.normal(0, 0.2)
        
        return {
            'active_users': max(10, int(base_users * (1 + user_variation))),
            'active_providers': max(5, int(base_providers * (1 + user_variation * 0.5))),
            'jobs_posted_24h': np.random.poisson(45),
            'jobs_completed_24h': np.random.poisson(38),
            'average_response_time': max(0.5, base_load * 2 + np.random.normal(0, 0.3)),
            'system_load': max(0.1, min(1.0, base_load + load_variation)),
            'error_rate': max(0.001, np.random.exponential(0.02)),
            'revenue_24h': np.random.normal(2500, 500),
            'user_satisfaction': max(1.0, min(5.0, np.random.normal(4.2, 0.3))),
            'provider_satisfaction': max(1.0, min(5.0, np.random.normal(4.0, 0.4)))
        }
    
    def _ml_anomaly_detection(self, metrics: PlatformMetrics) -> List[AnomalyAlert]:
        """Use ML to detect anomalies"""
        alerts = []
        
        try:
            # Prepare feature vector
            features = [
                metrics.active_users,
                metrics.average_response_time,
                metrics.system_load,
                metrics.error_rate,
                metrics.user_satisfaction,
                metrics.provider_satisfaction
            ]
            
            # Normalize features
            features_scaled = self.scaler.fit_transform([features])
            
            # Predict anomaly
            anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
            is_anomaly = self.anomaly_detector.predict(features_scaled)[0] == -1
            
            if is_anomaly:
                alerts.append(AnomalyAlert(
                    id=f"ml_anomaly_{int(time.time())}",
                    timestamp=metrics.timestamp,
                    type="ml_detected",
                    severity="medium",
                    description=f"ML detected anomaly (score: {anomaly_score:.3f})",
                    affected_metrics=["multiple"],
                    recommended_actions=[
                        "Investigate unusual patterns",
                        "Check for external factors",
                        "Monitor closely"
                    ]
                ))
        
        except Exception as e:
            logging.warning(f"ML anomaly detection failed: {e}")
        
        return alerts
    
    def _calculate_required_instances(self, load: float) -> int:
        """Calculate required instances based on load"""
        if load > 0.8:
            return min(self.scaling_config['max_instances'], 
                      int(load * self.scaling_config['max_instances']) + 1)
        elif load < 0.3:
            return max(self.scaling_config['min_instances'], 
                      int(load * self.scaling_config['max_instances']))
        else:
            return int(load * self.scaling_config['max_instances'])
    
    def _analyze_trends(self, metrics_list: List[PlatformMetrics]) -> Dict[str, Any]:
        """Analyze trends in metrics"""
        if len(metrics_list) < 24:
            return {"status": "insufficient_data"}
        
        # Extract time series data
        timestamps = [m.timestamp for m in metrics_list]
        users = [m.active_users for m in metrics_list]
        response_times = [m.average_response_time for m in metrics_list]
        satisfaction = [m.user_satisfaction for m in metrics_list]
        
        # Calculate trends (simplified linear trend)
        user_trend = np.polyfit(range(len(users)), users, 1)[0]
        response_trend = np.polyfit(range(len(response_times)), response_times, 1)[0]
        satisfaction_trend = np.polyfit(range(len(satisfaction)), satisfaction, 1)[0]
        
        return {
            "user_growth_trend": "increasing" if user_trend > 0 else "decreasing",
            "user_growth_rate": float(user_trend),
            "performance_trend": "improving" if response_trend < 0 else "degrading",
            "performance_change": float(response_trend),
            "satisfaction_trend": "improving" if satisfaction_trend > 0 else "declining",
            "satisfaction_change": float(satisfaction_trend)
        }
    
    def _forecast_demand(self, metrics_list: List[PlatformMetrics]) -> Dict[str, Any]:
        """Forecast demand for next 7 days"""
        jobs_posted = [m.jobs_posted_24h for m in metrics_list[-7:]]  # Last 7 days
        
        if len(jobs_posted) < 7:
            return {"status": "insufficient_data"}
        
        # Simple moving average forecast
        avg_jobs = np.mean(jobs_posted)
        trend = np.polyfit(range(len(jobs_posted)), jobs_posted, 1)[0]
        
        forecast = []
        for i in range(7):
            predicted = avg_jobs + (trend * i)
            forecast.append(max(0, int(predicted)))
        
        return {
            "next_7_days": forecast,
            "average_daily": int(avg_jobs),
            "trend": "increasing" if trend > 0 else "stable" if abs(trend) < 1 else "decreasing",
            "confidence": "medium"  # Simplified confidence
        }
    
    def _plan_capacity(self, metrics_list: List[PlatformMetrics], 
                      demand_forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Plan capacity based on demand forecast"""
        current_load = metrics_list[-1].system_load
        
        if demand_forecast.get("status") == "insufficient_data":
            return {"status": "insufficient_data"}
        
        forecast = demand_forecast["next_7_days"]
        max_demand = max(forecast)
        avg_demand = np.mean(forecast)
        
        # Calculate required capacity
        current_capacity = 100  # Assume current capacity is 100%
        required_capacity = (max_demand / metrics_list[-1].jobs_posted_24h) * current_capacity
        
        recommendations = []
        if required_capacity > current_capacity * 1.2:
            recommendations.append("Scale up infrastructure by 20-30%")
        elif required_capacity < current_capacity * 0.8:
            recommendations.append("Consider scaling down to optimize costs")
        else:
            recommendations.append("Current capacity is adequate")
        
        return {
            "current_utilization": f"{current_load:.1%}",
            "projected_peak_utilization": f"{min(1.0, required_capacity/current_capacity):.1%}",
            "recommendations": recommendations,
            "scaling_timeline": "3-5 days" if required_capacity > current_capacity * 1.2 else "no_action"
        }
    
    def _forecast_revenue(self, metrics_list: List[PlatformMetrics]) -> Dict[str, Any]:
        """Forecast revenue based on historical data"""
        revenue_data = [m.revenue_24h for m in metrics_list[-30:]]  # Last 30 days
        
        if len(revenue_data) < 7:
            return {"status": "insufficient_data"}
        
        # Calculate trends
        avg_revenue = np.mean(revenue_data)
        trend = np.polyfit(range(len(revenue_data)), revenue_data, 1)[0]
        
        # Forecast next 30 days
        forecast = []
        for i in range(30):
            predicted = avg_revenue + (trend * i)
            forecast.append(max(0, predicted))
        
        total_forecast = sum(forecast)
        
        return {
            "next_30_days_total": round(total_forecast, 2),
            "daily_average": round(avg_revenue, 2),
            "growth_rate": f"{(trend/avg_revenue)*100:.1f}%" if avg_revenue > 0 else "0%",
            "trend": "growing" if trend > 0 else "stable" if abs(trend) < 50 else "declining"
        }
    
    def _identify_optimization_opportunities(self, metrics_list: List[PlatformMetrics]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        opportunities = []
        
        if not metrics_list:
            return opportunities
        
        latest = metrics_list[-1]
        
        # Response time optimization
        if latest.average_response_time > self.baselines['response_time']:
            opportunities.append({
                "area": "performance",
                "opportunity": "Response time optimization",
                "potential_impact": "20-30% improvement in user experience",
                "effort": "medium",
                "priority": "high"
            })
        
        # User satisfaction improvement
        if latest.user_satisfaction < self.baselines['user_satisfaction']:
            opportunities.append({
                "area": "user_experience",
                "opportunity": "Matching algorithm enhancement",
                "potential_impact": "15-25% increase in user satisfaction",
                "effort": "high",
                "priority": "medium"
            })
        
        # Cost optimization
        if latest.system_load < 0.5:
            opportunities.append({
                "area": "cost",
                "opportunity": "Infrastructure right-sizing",
                "potential_impact": "10-20% cost reduction",
                "effort": "low",
                "priority": "low"
            })
        
        return opportunities
    
    def _assess_risks(self, metrics_list: List[PlatformMetrics]) -> Dict[str, Any]:
        """Assess platform risks"""
        if not metrics_list:
            return {"status": "no_data"}
        
        latest = metrics_list[-1]
        risks = []
        
        # Performance risk
        if latest.average_response_time > self.baselines['response_time'] * 2:
            risks.append({
                "type": "performance",
                "level": "high",
                "description": "Response times significantly above baseline",
                "mitigation": "Immediate performance optimization required"
            })
        
        # Capacity risk
        if latest.system_load > 0.85:
            risks.append({
                "type": "capacity",
                "level": "medium",
                "description": "System approaching capacity limits",
                "mitigation": "Plan for scaling within 24-48 hours"
            })
        
        # Satisfaction risk
        if latest.user_satisfaction < 3.5:
            risks.append({
                "type": "retention",
                "level": "high",
                "description": "User satisfaction critically low",
                "mitigation": "Immediate investigation and improvement needed"
            })
        
        overall_risk = "low"
        if any(r["level"] == "high" for r in risks):
            overall_risk = "high"
        elif any(r["level"] == "medium" for r in risks):
            overall_risk = "medium"
        
        return {
            "overall_risk": overall_risk,
            "identified_risks": risks,
            "risk_count": len(risks)
        }
    
    def _calculate_performance_score(self, metrics: PlatformMetrics) -> float:
        """Calculate performance component score"""
        response_score = max(0, 100 - (metrics.average_response_time / self.baselines['response_time'] - 1) * 50)
        load_score = max(0, 100 - metrics.system_load * 100)
        return (response_score + load_score) / 2
    
    def _calculate_reliability_score(self, metrics: PlatformMetrics) -> float:
        """Calculate reliability component score"""
        error_score = max(0, 100 - (metrics.error_rate / self.baselines['error_rate'] - 1) * 50)
        return error_score
    
    def _calculate_satisfaction_score(self, metrics: PlatformMetrics) -> float:
        """Calculate satisfaction component score"""
        user_score = (metrics.user_satisfaction / 5) * 100
        provider_score = (metrics.provider_satisfaction / 5) * 100
        return (user_score + provider_score) / 2
    
    def _calculate_capacity_score(self, metrics: PlatformMetrics) -> float:
        """Calculate capacity component score"""
        return max(0, 100 - metrics.system_load * 100)
    
    def _get_health_recommendations(self, overall_score: float, component_scores: Dict[str, float]) -> List[str]:
        """Get health improvement recommendations"""
        recommendations = []
        
        if overall_score < 70:
            recommendations.append("Platform health requires immediate attention")
        
        if component_scores['performance'] < 70:
            recommendations.append("Optimize response times and system performance")
        
        if component_scores['reliability'] < 70:
            recommendations.append("Investigate and reduce error rates")
        
        if component_scores['satisfaction'] < 70:
            recommendations.append("Focus on improving user and provider satisfaction")
        
        if component_scores['capacity'] < 70:
            recommendations.append("Scale infrastructure to handle current load")
        
        if not recommendations:
            recommendations.append("Platform health is good, continue monitoring")
        
        return recommendations

# Example usage
if __name__ == "__main__":
    # Initialize autonomous operations
    auto_ops = BipedAutonomousOperations()
    
    # Start monitoring
    auto_ops.start_monitoring()
    
    print("Autonomous operations engine initialized")
    print("Monitoring started...")
    
    # Simulate running for a short time
    time.sleep(5)
    
    # Get platform health
    health = auto_ops.get_platform_health_score()
    print(f"Platform health: {health}")
    
    # Stop monitoring
    auto_ops.stop_monitoring()

