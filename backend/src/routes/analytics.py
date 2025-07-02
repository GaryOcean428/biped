"""
Analytics and Autonomous Operations API Routes for Biped Platform
Provides endpoints for platform analytics, monitoring, and autonomous operations
"""

import os
import json
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging

# Import autonomous operations engine
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from autonomous_operations import BipedAutonomousOperations

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

# Initialize autonomous operations engine
auto_ops = BipedAutonomousOperations()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@analytics_bp.route('/platform-health', methods=['GET'])
def get_platform_health():
    """Get current platform health score and status"""
    try:
        health_data = auto_ops.get_platform_health_score()
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Error getting platform health: {str(e)}")
        return jsonify({'error': 'Failed to get platform health'}), 500

@analytics_bp.route('/metrics/current', methods=['GET'])
def get_current_metrics():
    """Get current platform metrics"""
    try:
        metrics = auto_ops.collect_metrics()
        
        response = {
            'timestamp': metrics.timestamp.isoformat(),
            'active_users': metrics.active_users,
            'active_providers': metrics.active_providers,
            'jobs_posted_24h': metrics.jobs_posted_24h,
            'jobs_completed_24h': metrics.jobs_completed_24h,
            'average_response_time': round(metrics.average_response_time, 2),
            'system_load': round(metrics.system_load * 100, 1),
            'error_rate': round(metrics.error_rate * 100, 3),
            'revenue_24h': round(metrics.revenue_24h, 2),
            'user_satisfaction': round(metrics.user_satisfaction, 1),
            'provider_satisfaction': round(metrics.provider_satisfaction, 1)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {str(e)}")
        return jsonify({'error': 'Failed to get current metrics'}), 500

@analytics_bp.route('/metrics/historical', methods=['GET'])
def get_historical_metrics():
    """Get historical metrics data"""
    try:
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        hours = min(hours, 168)  # Limit to 7 days
        
        # Get historical data
        historical_data = []
        current_time = datetime.now()
        
        for i in range(hours):
            timestamp = current_time - timedelta(hours=i)
            # Simulate historical metrics (in real implementation, get from database)
            metrics = auto_ops._generate_realistic_metrics(timestamp)
            
            historical_data.append({
                'timestamp': timestamp.isoformat(),
                'active_users': metrics['active_users'],
                'system_load': round(metrics['system_load'] * 100, 1),
                'response_time': round(metrics['average_response_time'], 2),
                'error_rate': round(metrics['error_rate'] * 100, 3),
                'user_satisfaction': round(metrics['user_satisfaction'], 1)
            })
        
        # Reverse to get chronological order
        historical_data.reverse()
        
        return jsonify({
            'data': historical_data,
            'period_hours': hours,
            'data_points': len(historical_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting historical metrics: {str(e)}")
        return jsonify({'error': 'Failed to get historical metrics'}), 500

@analytics_bp.route('/anomalies', methods=['GET'])
def get_anomalies():
    """Get recent anomaly alerts"""
    try:
        # Get current metrics and detect anomalies
        metrics = auto_ops.collect_metrics()
        alerts = auto_ops.detect_anomalies(metrics)
        
        # Format alerts for response
        formatted_alerts = []
        for alert in alerts:
            formatted_alerts.append({
                'id': alert.id,
                'timestamp': alert.timestamp.isoformat(),
                'type': alert.type,
                'severity': alert.severity,
                'description': alert.description,
                'affected_metrics': alert.affected_metrics,
                'recommended_actions': alert.recommended_actions,
                'auto_resolved': alert.auto_resolved
            })
        
        return jsonify({
            'alerts': formatted_alerts,
            'total_alerts': len(formatted_alerts),
            'critical_count': len([a for a in alerts if a.severity == 'critical']),
            'high_count': len([a for a in alerts if a.severity == 'high']),
            'medium_count': len([a for a in alerts if a.severity == 'medium']),
            'low_count': len([a for a in alerts if a.severity == 'low'])
        })
        
    except Exception as e:
        logger.error(f"Error getting anomalies: {str(e)}")
        return jsonify({'error': 'Failed to get anomalies'}), 500

@analytics_bp.route('/predictions', methods=['GET'])
def get_predictions():
    """Get predictive insights and forecasts"""
    try:
        insights = auto_ops.generate_predictive_insights()
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Error getting predictions: {str(e)}")
        return jsonify({'error': 'Failed to get predictions'}), 500

@analytics_bp.route('/optimizations', methods=['GET'])
def get_optimizations():
    """Get recent optimization actions"""
    try:
        # Get current metrics and generate optimization recommendations
        metrics = auto_ops.collect_metrics()
        alerts = auto_ops.detect_anomalies(metrics)
        optimizations = auto_ops.auto_optimize(metrics, alerts)
        
        # Format optimizations for response
        formatted_optimizations = []
        for opt in optimizations:
            formatted_optimizations.append({
                'id': opt.id,
                'timestamp': opt.timestamp.isoformat(),
                'action_type': opt.action_type,
                'target_system': opt.target_system,
                'parameters': opt.parameters,
                'expected_impact': opt.expected_impact,
                'status': opt.status,
                'actual_impact': opt.actual_impact
            })
        
        return jsonify({
            'optimizations': formatted_optimizations,
            'total_actions': len(formatted_optimizations),
            'pending_count': len([o for o in optimizations if o.status == 'pending']),
            'completed_count': len([o for o in optimizations if o.status == 'completed'])
        })
        
    except Exception as e:
        logger.error(f"Error getting optimizations: {str(e)}")
        return jsonify({'error': 'Failed to get optimizations'}), 500

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        # Collect all dashboard data
        health = auto_ops.get_platform_health_score()
        metrics = auto_ops.collect_metrics()
        alerts = auto_ops.detect_anomalies(metrics)
        insights = auto_ops.generate_predictive_insights()
        
        # Calculate key performance indicators
        kpis = _calculate_kpis(metrics)
        
        # Get trend data (last 24 hours)
        trend_data = _get_trend_data(24)
        
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'platform_health': health,
            'current_metrics': {
                'active_users': metrics.active_users,
                'active_providers': metrics.active_providers,
                'jobs_posted_24h': metrics.jobs_posted_24h,
                'jobs_completed_24h': metrics.jobs_completed_24h,
                'response_time': round(metrics.average_response_time, 2),
                'system_load': round(metrics.system_load * 100, 1),
                'error_rate': round(metrics.error_rate * 100, 3),
                'revenue_24h': round(metrics.revenue_24h, 2)
            },
            'kpis': kpis,
            'alerts_summary': {
                'total': len(alerts),
                'critical': len([a for a in alerts if a.severity == 'critical']),
                'high': len([a for a in alerts if a.severity == 'high']),
                'recent_alerts': [
                    {
                        'type': alert.type,
                        'severity': alert.severity,
                        'description': alert.description
                    } for alert in alerts[:5]  # Last 5 alerts
                ]
            },
            'trends': trend_data,
            'predictions': insights if insights.get('status') != 'insufficient_data' else None
        }
        
        return jsonify(dashboard)
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500

@analytics_bp.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start autonomous monitoring"""
    try:
        auto_ops.start_monitoring()
        return jsonify({
            'status': 'started',
            'message': 'Autonomous monitoring started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        return jsonify({'error': 'Failed to start monitoring'}), 500

@analytics_bp.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop autonomous monitoring"""
    try:
        auto_ops.stop_monitoring()
        return jsonify({
            'status': 'stopped',
            'message': 'Autonomous monitoring stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        return jsonify({'error': 'Failed to stop monitoring'}), 500

@analytics_bp.route('/monitoring/status', methods=['GET'])
def get_monitoring_status():
    """Get monitoring status"""
    try:
        return jsonify({
            'running': auto_ops.running,
            'metrics_collected': len(auto_ops.metrics_history),
            'last_collection': auto_ops.metrics_history[-1].timestamp.isoformat() if auto_ops.metrics_history else None
        })
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {str(e)}")
        return jsonify({'error': 'Failed to get monitoring status'}), 500

@analytics_bp.route('/reports/performance', methods=['GET'])
def get_performance_report():
    """Generate performance report"""
    try:
        # Get time range
        days = request.args.get('days', 7, type=int)
        days = min(days, 30)  # Limit to 30 days
        
        # Generate mock performance report
        report = _generate_performance_report(days)
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}")
        return jsonify({'error': 'Failed to generate performance report'}), 500

@analytics_bp.route('/reports/business', methods=['GET'])
def get_business_report():
    """Generate business analytics report"""
    try:
        # Get time range
        days = request.args.get('days', 30, type=int)
        days = min(days, 90)  # Limit to 90 days
        
        # Generate mock business report
        report = _generate_business_report(days)
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating business report: {str(e)}")
        return jsonify({'error': 'Failed to generate business report'}), 500

# Helper functions

def _calculate_kpis(metrics):
    """Calculate key performance indicators"""
    completion_rate = (metrics.jobs_completed_24h / max(1, metrics.jobs_posted_24h)) * 100
    provider_utilization = (metrics.active_providers / max(1, metrics.active_users)) * 100
    
    return {
        'job_completion_rate': round(completion_rate, 1),
        'provider_utilization': round(provider_utilization, 1),
        'average_response_time': round(metrics.average_response_time, 2),
        'user_satisfaction': round(metrics.user_satisfaction, 1),
        'provider_satisfaction': round(metrics.provider_satisfaction, 1),
        'daily_revenue': round(metrics.revenue_24h, 2),
        'system_uptime': 99.8,  # Mock uptime
        'error_rate': round(metrics.error_rate * 100, 3)
    }

def _get_trend_data(hours):
    """Get trend data for specified hours"""
    trend_data = []
    current_time = datetime.now()
    
    for i in range(hours):
        timestamp = current_time - timedelta(hours=i)
        metrics = auto_ops._generate_realistic_metrics(timestamp)
        
        trend_data.append({
            'timestamp': timestamp.isoformat(),
            'users': metrics['active_users'],
            'load': round(metrics['system_load'] * 100, 1),
            'response_time': round(metrics['average_response_time'], 2)
        })
    
    trend_data.reverse()
    return trend_data

def _generate_performance_report(days):
    """Generate performance report for specified days"""
    import random
    
    return {
        'report_period': f'{days} days',
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'average_response_time': round(random.uniform(1.5, 3.0), 2),
            'peak_response_time': round(random.uniform(3.0, 6.0), 2),
            'uptime_percentage': round(random.uniform(99.5, 99.9), 2),
            'error_rate': round(random.uniform(0.01, 0.05), 3),
            'total_requests': random.randint(50000, 150000)
        },
        'trends': {
            'response_time_trend': random.choice(['improving', 'stable', 'degrading']),
            'error_rate_trend': random.choice(['improving', 'stable', 'increasing']),
            'load_trend': random.choice(['increasing', 'stable', 'decreasing'])
        },
        'recommendations': [
            'Optimize database queries for better response times',
            'Implement caching for frequently accessed data',
            'Consider horizontal scaling during peak hours'
        ]
    }

def _generate_business_report(days):
    """Generate business analytics report"""
    import random
    
    return {
        'report_period': f'{days} days',
        'generated_at': datetime.now().isoformat(),
        'revenue': {
            'total_revenue': round(random.uniform(50000, 150000), 2),
            'average_daily': round(random.uniform(1500, 5000), 2),
            'growth_rate': round(random.uniform(-5, 25), 1),
            'top_categories': [
                {'name': 'Construction', 'revenue': round(random.uniform(15000, 45000), 2)},
                {'name': 'Electrical', 'revenue': round(random.uniform(10000, 30000), 2)},
                {'name': 'Plumbing', 'revenue': round(random.uniform(8000, 25000), 2)}
            ]
        },
        'users': {
            'total_active_users': random.randint(800, 2000),
            'new_registrations': random.randint(50, 200),
            'user_retention_rate': round(random.uniform(75, 90), 1),
            'average_session_duration': round(random.uniform(8, 15), 1)
        },
        'jobs': {
            'total_jobs_posted': random.randint(300, 800),
            'total_jobs_completed': random.randint(250, 700),
            'completion_rate': round(random.uniform(80, 95), 1),
            'average_job_value': round(random.uniform(200, 800), 2)
        },
        'providers': {
            'total_active_providers': random.randint(200, 500),
            'new_provider_registrations': random.randint(10, 50),
            'average_provider_rating': round(random.uniform(4.0, 4.8), 1),
            'provider_utilization_rate': round(random.uniform(60, 85), 1)
        },
        'insights': [
            'Construction category shows highest growth potential',
            'User satisfaction improved by 8% this period',
            'Provider response times decreased by 15%',
            'Mobile usage increased by 22%'
        ]
    }

