"""
Analytics API Routes
Provides endpoints for data pipeline, business intelligence, and advanced analytics
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from ..services.data_pipeline import BusinessIntelligenceEngine, RealTimeDataProcessor
from ..utils.security import SecurityEnhancer
from ..utils.performance import TradingCacheService

logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v2/analytics')

def get_services():
    """Get data services from app context"""
    return current_app.config.get('DATA_SERVICES', {})

@analytics_bp.route('/portfolio/<user_id>', methods=['GET'])
@login_required
def get_portfolio_analytics(user_id: str):
    """Get comprehensive portfolio analytics for a user"""
    try:
        # Security check - users can only access their own analytics
        if current_user.id != user_id and not current_user.is_admin:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        services = get_services()
        bi_engine = services.get('bi_engine')
        
        if not bi_engine:
            return jsonify({'error': 'Analytics service not available'}), 503
        
        # Get analytics asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(
            bi_engine.generate_portfolio_analytics(user_id)
        )
        
        return jsonify({
            'status': 'success',
            'data': analytics,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio analytics for {user_id}: {e}")
        return jsonify({'error': 'Failed to generate analytics'}), 500

@analytics_bp.route('/market-intelligence', methods=['GET'])
@login_required
def get_market_intelligence():
    """Get comprehensive market intelligence report"""
    try:
        services = get_services()
        bi_engine = services.get('bi_engine')
        
        if not bi_engine:
            return jsonify({'error': 'Analytics service not available'}), 503
        
        # Get market intelligence
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        intelligence = loop.run_until_complete(
            bi_engine.generate_market_intelligence()
        )
        
        return jsonify({
            'status': 'success',
            'data': intelligence,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating market intelligence: {e}")
        return jsonify({'error': 'Failed to generate market intelligence'}), 500

@analytics_bp.route('/real-time/market-data', methods=['GET'])
@login_required
def get_real_time_market_data():
    """Get real-time marketplace data for service categories"""
    try:
        categories = request.args.get('categories', '').split(',')
        if not categories or categories == ['']:
            categories = ['Plumbing', 'Electrical', 'Carpentry', 'Painting', 'Landscaping']
        
        # Get cached marketplace data
        cache_service = current_app.config.get('CACHE_SERVICE')
        if not cache_service:
            return jsonify({'error': 'Cache service not available'}), 503
        
        marketplace_data = {}
        for category in categories:
            try:
                cached_data = cache_service.get(f"service_data:{category}")
                if cached_data:
                    marketplace_data[category] = cached_data
            except Exception as e:
                logger.debug(f"Could not get cached data for {category}: {e}")
                # Provide fallback data
                marketplace_data[category] = {
                    'avg_price': 250,
                    'demand_score': 0.6,
                    'supply_score': 0.5,
                    'completion_rate': 0.9,
                    'avg_rating': 4.5,
                    'response_time': 4.2
                }
        
        return jsonify({
            'status': 'success',
            'data': marketplace_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting marketplace data: {e}")
        return jsonify({'error': 'Failed to get marketplace data'}), 500

@analytics_bp.route('/performance/summary', methods=['GET'])
@login_required
def get_performance_summary():
    """Get performance summary for current user"""
    try:
        user_id = current_user.id
        days = request.args.get('days', 30, type=int)
        
        services = get_services()
        bi_engine = services.get('bi_engine')
        
        if not bi_engine:
            return jsonify({'error': 'Analytics service not available'}), 503
        
        # Get performance data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get portfolio analytics
        analytics = loop.run_until_complete(
            bi_engine.generate_portfolio_analytics(user_id)
        )
        
        # Extract performance summary
        performance_summary = {
            'portfolio_value': analytics.get('portfolio_summary', {}).get('total_value', 0),
            'total_pnl': analytics.get('portfolio_summary', {}).get('total_pnl', 0),
            'total_pnl_percent': analytics.get('portfolio_summary', {}).get('total_pnl_percent', 0),
            'daily_change': analytics.get('portfolio_summary', {}).get('daily_change', 0),
            'position_count': analytics.get('portfolio_summary', {}).get('position_count', 0),
            'performance_metrics': analytics.get('performance_metrics', {}),
            'risk_metrics': analytics.get('risk_metrics', {}),
            'period_days': days
        }
        
        return jsonify({
            'status': 'success',
            'data': performance_summary,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        return jsonify({'error': 'Failed to get performance summary'}), 500

@analytics_bp.route('/risk/assessment', methods=['GET'])
@login_required
def get_risk_assessment():
    """Get comprehensive risk assessment for current user"""
    try:
        user_id = current_user.id
        
        services = get_services()
        bi_engine = services.get('bi_engine')
        
        if not bi_engine:
            return jsonify({'error': 'Analytics service not available'}), 503
        
        # Get risk assessment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(
            bi_engine.generate_portfolio_analytics(user_id)
        )
        
        risk_assessment = {
            'risk_score': analytics.get('risk_metrics', {}).get('volatility', 0) * 10,  # Scale to 0-100
            'risk_level': _determine_risk_level(analytics.get('risk_metrics', {})),
            'risk_metrics': analytics.get('risk_metrics', {}),
            'risk_factors': _identify_risk_factors(analytics),
            'recommendations': _generate_risk_recommendations(analytics),
            'portfolio_diversification': _analyze_diversification(analytics.get('allocation_analysis', {})),
            'stress_test_results': _perform_stress_test(analytics)
        }
        
        return jsonify({
            'status': 'success',
            'data': risk_assessment,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting risk assessment: {e}")
        return jsonify({'error': 'Failed to get risk assessment'}), 500

@analytics_bp.route('/user/activity', methods=['GET'])
@login_required
def get_user_activity():
    """Analyze user marketplace activity patterns"""
    try:
        user_id = current_user.id
        
        services = get_services()
        bi_engine = services.get('bi_engine')
        
        if not bi_engine:
            return jsonify({'error': 'Analytics service not available'}), 503
        
        # Get user analytics
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(
            bi_engine.generate_user_analytics(user_id)
        )
        
        activity_patterns = analytics.get('activity_patterns', {})
        
        # Enhance with additional analysis
        enhanced_patterns = {
            **activity_patterns,
            'service_preferences': analytics.get('service_preferences', {}),
            'satisfaction_metrics': analytics.get('satisfaction_metrics', {}),
            'spending_analysis': analytics.get('spending_analysis', {}),
            'recommendations': analytics.get('recommendations', [])
        }
        
        return jsonify({
            'status': 'success',
            'data': enhanced_patterns,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error analyzing user activity: {e}")
        return jsonify({'error': 'Failed to analyze user activity'}), 500

@analytics_bp.route('/marketplace/insights', methods=['GET'])
@login_required
def get_marketplace_insights():
    """Get marketplace insights and trends"""
    try:
        categories = request.args.get('categories', '').split(',')
        if not categories or categories == ['']:
            categories = ['Plumbing', 'Electrical', 'Carpentry', 'Painting', 'Landscaping']
        
        services = get_services()
        bi_engine = services.get('bi_engine')
        
        if not bi_engine:
            return jsonify({'error': 'Analytics service not available'}), 503
        
        # Get market intelligence for sentiment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        intelligence = loop.run_until_complete(
            bi_engine.generate_market_intelligence()
        )
        
        # Extract sentiment data
        sentiment_data = {}
        symbol_analysis = intelligence.get('symbol_analysis', {})
        
        for symbol in symbols:
            if symbol in symbol_analysis:
                sentiment_data[symbol] = symbol_analysis[symbol].get('sentiment', {})
        
        # Overall market sentiment
        overall_sentiment = intelligence.get('market_overview', {}).get('market_sentiment', {})
        
        return jsonify({
            'status': 'success',
            'data': {
                'overall_sentiment': overall_sentiment,
                'symbol_sentiment': sentiment_data,
                'sentiment_trends': _analyze_sentiment_trends(sentiment_data),
                'sentiment_signals': _generate_sentiment_signals(sentiment_data)
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting market sentiment: {e}")
        return jsonify({'error': 'Failed to get market sentiment'}), 500

@analytics_bp.route('/alerts/generate', methods=['POST'])
@login_required
def generate_custom_alerts():
    """Generate custom alerts based on user criteria"""
    try:
        alert_config = request.get_json()
        user_id = current_user.id
        
        # Validate alert configuration
        required_fields = ['alert_type', 'conditions', 'notification_method']
        if not all(field in alert_config for field in required_fields):
            return jsonify({'error': 'Missing required alert configuration'}), 400
        
        # Create alert
        alert = {
            'id': f"ALERT-{user_id}-{int(datetime.utcnow().timestamp())}",
            'user_id': user_id,
            'alert_type': alert_config['alert_type'],
            'conditions': alert_config['conditions'],
            'notification_method': alert_config['notification_method'],
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'triggered_count': 0,
            'last_triggered': None
        }
        
        # Store alert (in production, save to database)
        cache_service = current_app.config.get('CACHE_SERVICE')
        if cache_service:
            cache_service.cache_user_data(f"{user_id}:alerts:{alert['id']}", alert, ttl=86400)
        
        return jsonify({
            'status': 'success',
            'data': {
                'alert_id': alert['id'],
                'message': 'Alert created successfully',
                'alert': alert
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error creating custom alert: {e}")
        return jsonify({'error': 'Failed to create alert'}), 500

@analytics_bp.route('/reports/generate', methods=['POST'])
@login_required
def generate_custom_report():
    """Generate custom analytics report"""
    try:
        report_config = request.get_json()
        user_id = current_user.id
        
        # Validate report configuration
        if 'report_type' not in report_config:
            return jsonify({'error': 'Missing report type'}), 400
        
        services = get_services()
        bi_engine = services.get('bi_engine')
        
        if not bi_engine:
            return jsonify({'error': 'Analytics service not available'}), 503
        
        # Generate report based on type
        report_type = report_config['report_type']
        
        if report_type == 'portfolio_performance':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            report_data = loop.run_until_complete(
                bi_engine.generate_portfolio_analytics(user_id)
            )
        elif report_type == 'market_analysis':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            report_data = loop.run_until_complete(
                bi_engine.generate_market_intelligence()
            )
        else:
            return jsonify({'error': 'Unknown report type'}), 400
        
        # Create report metadata
        report = {
            'id': f"REPORT-{user_id}-{int(datetime.utcnow().timestamp())}",
            'user_id': user_id,
            'report_type': report_type,
            'generated_at': datetime.utcnow().isoformat(),
            'config': report_config,
            'data': report_data,
            'format': report_config.get('format', 'json'),
            'status': 'completed'
        }
        
        return jsonify({
            'status': 'success',
            'data': report,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating custom report: {e}")
        return jsonify({'error': 'Failed to generate report'}), 500

# Helper functions
def _determine_risk_level(risk_metrics: Dict) -> str:
    """Determine risk level based on metrics"""
    volatility = risk_metrics.get('volatility', 0)
    max_drawdown = abs(risk_metrics.get('max_drawdown', 0))
    
    if volatility > 30 or max_drawdown > 20:
        return 'high'
    elif volatility > 15 or max_drawdown > 10:
        return 'medium'
    else:
        return 'low'

def _identify_risk_factors(analytics: Dict) -> List[str]:
    """Identify key risk factors"""
    risk_factors = []
    
    risk_metrics = analytics.get('risk_metrics', {})
    portfolio_summary = analytics.get('portfolio_summary', {})
    
    # Check various risk factors
    if risk_metrics.get('volatility', 0) > 25:
        risk_factors.append('high_volatility')
    
    if abs(risk_metrics.get('max_drawdown', 0)) > 15:
        risk_factors.append('large_drawdowns')
    
    if portfolio_summary.get('position_count', 0) < 3:
        risk_factors.append('concentration_risk')
    
    if risk_metrics.get('sharpe_ratio', 0) < 1:
        risk_factors.append('poor_risk_adjusted_returns')
    
    return risk_factors

def _generate_risk_recommendations(analytics: Dict) -> List[str]:
    """Generate risk management recommendations"""
    recommendations = []
    
    risk_factors = _identify_risk_factors(analytics)
    
    if 'high_volatility' in risk_factors:
        recommendations.append('Consider reducing position sizes to manage volatility')
    
    if 'concentration_risk' in risk_factors:
        recommendations.append('Diversify portfolio across more assets and sectors')
    
    if 'large_drawdowns' in risk_factors:
        recommendations.append('Implement stop-loss orders to limit downside risk')
    
    if 'poor_risk_adjusted_returns' in risk_factors:
        recommendations.append('Review trading strategy and consider risk-adjusted metrics')
    
    return recommendations

def _analyze_diversification(allocation: Dict) -> Dict:
    """Analyze portfolio diversification"""
    # Simulated diversification analysis
    return {
        'diversification_score': 75,  # 0-100 scale
        'sector_concentration': 'moderate',
        'geographic_concentration': 'low',
        'service_category_distribution': {
            'plumbing': 30,
            'electrical': 25,
            'landscaping': 20,
            'painting': 15,
            'cleaning': 10
        },
        'recommendations': [
            'Consider adding international exposure',
            'Increase bond allocation for stability'
        ]
    }

def _perform_stress_test(analytics: Dict) -> Dict:
    """Perform portfolio stress test"""
    # Simulated stress test results
    return {
        'market_crash_scenario': {
            'portfolio_loss': -25.5,
            'recovery_time_months': 8
        },
        'interest_rate_shock': {
            'portfolio_impact': -5.2,
            'affected_positions': ['bonds', 'reits']
        },
        'sector_rotation': {
            'portfolio_impact': -3.1,
            'beneficiary_sectors': ['technology', 'healthcare']
        },
        'overall_resilience': 'moderate'
    }

def _determine_user_type(patterns: Dict) -> str:
    """Determine user's marketplace activity type"""
    # Analyze patterns to determine user type
    job_frequency = patterns.get('jobs_last_30_days', 0)
    
    if job_frequency > 10:  # More than 10 jobs per month
        return 'power_user'
    elif job_frequency > 3:  # 3-10 jobs per month
        return 'regular_user'
    else:
        return 'occasional_user'

def _calculate_satisfaction_score(patterns: Dict) -> float:
    """Calculate user satisfaction score"""
    # Calculate satisfaction based on ratings and completion rates
    avg_rating = patterns.get('avg_rating', 4.0)
    completion_rate = patterns.get('completion_rate', 80)
    
    satisfaction = (avg_rating / 5.0) * (completion_rate / 100) * 100
    return min(satisfaction, 100)

def _analyze_user_behavior(patterns: Dict) -> Dict:
    """Analyze behavioral patterns in marketplace usage"""
    return {
        'service_loyalty': 'moderate',
        'price_sensitivity': 'average',
        'quality_focus': 'high',
        'planning_horizon': 'medium-term',
        'decision_factors': ['price', 'rating', 'response_time']
    }

def _suggest_marketplace_improvements(patterns: Dict) -> List[str]:
    """Suggest marketplace usage improvements"""
    return [
        'Consider posting more detailed job descriptions to improve completion rates',
        'Look for providers with higher ratings and more completed jobs',
        'Consider bundling related services for better value',
        'Leave detailed reviews to help other users and providers',
        'Plan seasonal work in advance for better availability and pricing'
    ]

def _analyze_marketplace_trends(category_data: Dict) -> Dict:
    """Analyze marketplace trends for categories"""
    return {
        'overall_trend': 'stable',
        'growth_areas': ['Landscaping', 'Cleaning'],
        'seasonal_factors': ['Winter demand for heating', 'Spring demand for landscaping'],
        'key_drivers': ['population_growth', 'home_renovations', 'seasonal_changes']
    }

def _generate_category_insights(category_data: Dict) -> List[Dict]:
    """Generate insights for service categories"""
    insights = []
    
    for category, data in category_data.items():
        demand_score = data.get('demand_score', 0.5)
        supply_score = data.get('supply_score', 0.5)
        
        if demand_score > 0.7 and supply_score < 0.4:
            insights.append({
                'category': category,
                'insight': 'high_demand_low_supply',
                'recommendation': 'Consider booking in advance, prices may be higher',
                'urgency': 'high'
            })
        elif demand_score < 0.3 and supply_score > 0.7:
            insights.append({
                'category': category,
                'insight': 'low_demand_high_supply',
                'recommendation': 'Good time to book, competitive pricing expected',
                'urgency': 'low'
            })
    
    return insights

