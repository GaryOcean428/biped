"""
Analytics API Routes
Provides endpoints for data pipeline, business intelligence, and advanced analytics
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from ..services.data_pipeline import BusinessIntelligenceEngine, RealTimeDataProcessor
from ..utils.performance import TradingCacheService
from ..utils.security import SecurityEnhancer

logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v2/analytics")


def get_services():
    """Get data services from app context"""
    return current_app.config.get("DATA_SERVICES", {})


@analytics_bp.route("/portfolio/<user_id>", methods=["GET"])
@login_required
def get_portfolio_analytics(user_id: str):
    """Get comprehensive portfolio analytics for a user"""
    try:
        # Security check - users can only access their own analytics
        if current_user.id != user_id and not current_user.is_admin:
            return jsonify({"error": "Unauthorized access"}), 403

        services = get_services()
        bi_engine = services.get("bi_engine")

        if not bi_engine:
            return jsonify({"error": "Analytics service not available"}), 503

        # Get analytics asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(bi_engine.generate_portfolio_analytics(user_id))

        return jsonify(
            {"status": "success", "data": analytics, "timestamp": datetime.utcnow().isoformat()}
        )

    except Exception as e:
        logger.error(f"Error getting portfolio analytics for {user_id}: {e}")
        return jsonify({"error": "Failed to generate analytics"}), 500


@analytics_bp.route("/market-intelligence", methods=["GET"])
@login_required
def get_market_intelligence():
    """Get comprehensive market intelligence report"""
    try:
        services = get_services()
        bi_engine = services.get("bi_engine")

        if not bi_engine:
            return jsonify({"error": "Analytics service not available"}), 503

        # Get market intelligence
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        intelligence = loop.run_until_complete(bi_engine.generate_market_intelligence())

        return jsonify(
            {"status": "success", "data": intelligence, "timestamp": datetime.utcnow().isoformat()}
        )

    except Exception as e:
        logger.error(f"Error generating market intelligence: {e}")
        return jsonify({"error": "Failed to generate market intelligence"}), 500


@analytics_bp.route("/real-time/market-data", methods=["GET"])
@login_required
def get_real_time_market_data():
    """Get real-time market data for multiple service categories"""
    try:
        service_categories = request.args.get("categories", "").split(",")
        if not service_categories or service_categories == [""]:
            service_categories = ["Plumbing", "Electrical", "Carpentry", "Painting", "Landscaping"]

        # Get cached market data
        cache_service = current_app.config.get("CACHE_SERVICE")
        if not cache_service:
            return jsonify({"error": "Cache service not available"}), 503

        market_data = {}
        for service_category in service_categories:
            data = cache_service.get_market_data(service_category.strip())
            if data:
                market_data[service_category] = data

        return jsonify(
            {"status": "success", "data": market_data, "timestamp": datetime.utcnow().isoformat()}
        )

    except Exception as e:
        logger.error(f"Error getting real-time market data: {e}")
        return jsonify({"error": "Failed to get market data"}), 500


@analytics_bp.route("/performance/summary", methods=["GET"])
@login_required
def get_performance_summary():
    """Get performance summary for current user"""
    try:
        user_id = current_user.id
        days = request.args.get("days", 30, type=int)

        services = get_services()
        bi_engine = services.get("bi_engine")

        if not bi_engine:
            return jsonify({"error": "Analytics service not available"}), 503

        # Get performance data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Get portfolio analytics
        analytics = loop.run_until_complete(bi_engine.generate_portfolio_analytics(user_id))

        # Extract performance summary
        performance_summary = {
            "portfolio_value": analytics.get("portfolio_summary", {}).get("total_value", 0),
            "total_pnl": analytics.get("portfolio_summary", {}).get("total_pnl", 0),
            "total_pnl_percent": analytics.get("portfolio_summary", {}).get("total_pnl_percent", 0),
            "daily_change": analytics.get("portfolio_summary", {}).get("daily_change", 0),
            "position_count": analytics.get("portfolio_summary", {}).get("position_count", 0),
            "performance_metrics": analytics.get("performance_metrics", {}),
            "risk_metrics": analytics.get("risk_metrics", {}),
            "period_days": days,
        }

        return jsonify(
            {
                "status": "success",
                "data": performance_summary,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        return jsonify({"error": "Failed to get performance summary"}), 500


@analytics_bp.route("/risk/assessment", methods=["GET"])
@login_required
def get_risk_assessment():
    """Get comprehensive risk assessment for current user"""
    try:
        user_id = current_user.id

        services = get_services()
        bi_engine = services.get("bi_engine")

        if not bi_engine:
            return jsonify({"error": "Analytics service not available"}), 503

        # Get risk assessment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(bi_engine.generate_portfolio_analytics(user_id))

        risk_assessment = {
            "risk_score": analytics.get("risk_metrics", {}).get("volatility", 0)
            * 10,  # Scale to 0-100
            "risk_level": _determine_risk_level(analytics.get("risk_metrics", {})),
            "risk_metrics": analytics.get("risk_metrics", {}),
            "risk_factors": _identify_risk_factors(analytics),
            "recommendations": _generate_risk_recommendations(analytics),
            "portfolio_diversification": _analyze_diversification(
                analytics.get("allocation_analysis", {})
            ),
            "stress_test_results": _perform_stress_test(analytics),
        }

        return jsonify(
            {
                "status": "success",
                "data": risk_assessment,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting risk assessment: {e}")
        return jsonify({"error": "Failed to get risk assessment"}), 500


@analytics_bp.route("/trading/patterns", methods=["GET"])
@login_required
def get_trading_patterns():
    """Analyze trading patterns for current user"""
    try:
        user_id = current_user.id

        services = get_services()
        bi_engine = services.get("bi_engine")

        if not bi_engine:
            return jsonify({"error": "Analytics service not available"}), 503

        # Get trading patterns
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(bi_engine.generate_portfolio_analytics(user_id))

        patterns = analytics.get("trading_patterns", {})

        # Enhance with additional analysis
        enhanced_patterns = {
            **patterns,
            "trading_style": _determine_trading_style(patterns),
            "efficiency_score": _calculate_efficiency_score(patterns),
            "behavioral_insights": _analyze_trading_behavior(patterns),
            "improvement_suggestions": _suggest_improvements(patterns),
        }

        return jsonify(
            {
                "status": "success",
                "data": enhanced_patterns,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error analyzing trading patterns: {e}")
        return jsonify({"error": "Failed to analyze trading patterns"}), 500


@analytics_bp.route("/market/sentiment", methods=["GET"])
@login_required
def get_market_sentiment():
    """Get market sentiment analysis"""
    try:
        service_categories = request.args.get("categories", "").split(",")
        if not service_categories or service_categories == [""]:
            service_categories = ["Plumbing", "Electrical", "Carpentry", "Painting", "Landscaping"]

        services = get_services()
        bi_engine = services.get("bi_engine")

        if not bi_engine:
            return jsonify({"error": "Analytics service not available"}), 503

        # Get market intelligence for sentiment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        intelligence = loop.run_until_complete(bi_engine.generate_market_intelligence())

        # Extract sentiment data
        sentiment_data = {}
        symbol_analysis = intelligence.get("symbol_analysis", {})

        for symbol in symbols:
            if symbol in symbol_analysis:
                sentiment_data[symbol] = symbol_analysis[symbol].get("sentiment", {})

        # Overall market sentiment
        overall_sentiment = intelligence.get("market_overview", {}).get("market_sentiment", {})

        return jsonify(
            {
                "status": "success",
                "data": {
                    "overall_sentiment": overall_sentiment,
                    "symbol_sentiment": sentiment_data,
                    "sentiment_trends": _analyze_sentiment_trends(sentiment_data),
                    "sentiment_signals": _generate_sentiment_signals(sentiment_data),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting market sentiment: {e}")
        return jsonify({"error": "Failed to get market sentiment"}), 500


@analytics_bp.route("/alerts/generate", methods=["POST"])
@login_required
def generate_custom_alerts():
    """Generate custom alerts based on user criteria"""
    try:
        alert_config = request.get_json()
        user_id = current_user.id

        # Validate alert configuration
        required_fields = ["alert_type", "conditions", "notification_method"]
        if not all(field in alert_config for field in required_fields):
            return jsonify({"error": "Missing required alert configuration"}), 400

        # Create alert
        alert = {
            "id": f"ALERT-{user_id}-{int(datetime.utcnow().timestamp())}",
            "user_id": user_id,
            "alert_type": alert_config["alert_type"],
            "conditions": alert_config["conditions"],
            "notification_method": alert_config["notification_method"],
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "triggered_count": 0,
            "last_triggered": None,
        }

        # Store alert (in production, save to database)
        cache_service = current_app.config.get("CACHE_SERVICE")
        if cache_service:
            cache_service.cache_user_data(f"{user_id}:alerts:{alert['id']}", alert, ttl=86400)

        return jsonify(
            {
                "status": "success",
                "data": {
                    "alert_id": alert["id"],
                    "message": "Alert created successfully",
                    "alert": alert,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error creating custom alert: {e}")
        return jsonify({"error": "Failed to create alert"}), 500


@analytics_bp.route("/reports/generate", methods=["POST"])
@login_required
def generate_custom_report():
    """Generate custom analytics report"""
    try:
        report_config = request.get_json()
        user_id = current_user.id

        # Validate report configuration
        if "report_type" not in report_config:
            return jsonify({"error": "Missing report type"}), 400

        services = get_services()
        bi_engine = services.get("bi_engine")

        if not bi_engine:
            return jsonify({"error": "Analytics service not available"}), 503

        # Generate report based on type
        report_type = report_config["report_type"]

        if report_type == "portfolio_performance":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            report_data = loop.run_until_complete(bi_engine.generate_portfolio_analytics(user_id))
        elif report_type == "market_analysis":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            report_data = loop.run_until_complete(bi_engine.generate_market_intelligence())
        else:
            return jsonify({"error": "Unknown report type"}), 400

        # Create report metadata
        report = {
            "id": f"REPORT-{user_id}-{int(datetime.utcnow().timestamp())}",
            "user_id": user_id,
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "config": report_config,
            "data": report_data,
            "format": report_config.get("format", "json"),
            "status": "completed",
        }

        return jsonify(
            {"status": "success", "data": report, "timestamp": datetime.utcnow().isoformat()}
        )

    except Exception as e:
        logger.error(f"Error generating custom report: {e}")
        return jsonify({"error": "Failed to generate report"}), 500


# Helper functions
def _determine_risk_level(risk_metrics: Dict) -> str:
    """Determine risk level based on metrics"""
    volatility = risk_metrics.get("volatility", 0)
    max_drawdown = abs(risk_metrics.get("max_drawdown", 0))

    if volatility > 30 or max_drawdown > 20:
        return "high"
    elif volatility > 15 or max_drawdown > 10:
        return "medium"
    else:
        return "low"


def _identify_risk_factors(analytics: Dict) -> List[str]:
    """Identify key risk factors"""
    risk_factors = []

    risk_metrics = analytics.get("risk_metrics", {})
    portfolio_summary = analytics.get("portfolio_summary", {})

    # Check various risk factors
    if risk_metrics.get("volatility", 0) > 25:
        risk_factors.append("high_volatility")

    if abs(risk_metrics.get("max_drawdown", 0)) > 15:
        risk_factors.append("large_drawdowns")

    if portfolio_summary.get("position_count", 0) < 3:
        risk_factors.append("concentration_risk")

    if risk_metrics.get("sharpe_ratio", 0) < 1:
        risk_factors.append("poor_risk_adjusted_returns")

    return risk_factors


def _generate_risk_recommendations(analytics: Dict) -> List[str]:
    """Generate risk management recommendations"""
    recommendations = []

    risk_factors = _identify_risk_factors(analytics)

    if "high_volatility" in risk_factors:
        recommendations.append("Consider reducing position sizes to manage volatility")

    if "concentration_risk" in risk_factors:
        recommendations.append("Diversify portfolio across more assets and sectors")

    if "large_drawdowns" in risk_factors:
        recommendations.append("Implement stop-loss orders to limit downside risk")

    if "poor_risk_adjusted_returns" in risk_factors:
        recommendations.append("Review trading strategy and consider risk-adjusted metrics")

    return recommendations


def _analyze_diversification(allocation: Dict) -> Dict:
    """Analyze portfolio diversification"""
    # Simulated diversification analysis
    return {
        "diversification_score": 75,  # 0-100 scale
        "sector_concentration": "moderate",
        "geographic_concentration": "low",
        "service_category_distribution": {
            "plumbing": 30,
            "electrical": 25,
            "carpentry": 20,
            "painting": 15,
            "landscaping": 10,
        },
        "recommendations": [
            "Consider expanding into additional service categories",
            "Increase pricing for high-demand services",
            "Focus on customer retention and repeat business",
        ],
    }


def _perform_stress_test(analytics: Dict) -> Dict:
    """Perform portfolio stress test"""
    # Simulated stress test results
    return {
        "market_crash_scenario": {"portfolio_loss": -25.5, "recovery_time_months": 8},
        "interest_rate_shock": {"portfolio_impact": -5.2, "affected_positions": ["bonds", "reits"]},
        "sector_rotation": {
            "portfolio_impact": -3.1,
            "beneficiary_sectors": ["technology", "healthcare"],
        },
        "overall_resilience": "moderate",
    }


def _determine_trading_style(patterns: Dict) -> str:
    """Determine user's trading style"""
    # Analyze patterns to determine style
    frequency = patterns.get("trading_frequency", 0)

    if frequency > 5:  # More than 5 trades per day
        return "day_trader"
    elif frequency > 1:  # 1-5 trades per day
        return "swing_trader"
    else:
        return "position_trader"


def _calculate_efficiency_score(patterns: Dict) -> float:
    """Calculate trading efficiency score"""
    # Simulated efficiency calculation
    win_rate = patterns.get("win_rate", 50)
    profit_factor = patterns.get("profit_factor", 1)

    efficiency = (win_rate / 100) * profit_factor * 50
    return min(efficiency, 100)


def _analyze_trading_behavior(patterns: Dict) -> Dict:
    """Analyze behavioral patterns in trading"""
    return {
        "risk_tolerance": "moderate",
        "emotional_discipline": "good",
        "timing_consistency": "average",
        "position_sizing": "conservative",
        "behavioral_biases": ["confirmation_bias", "loss_aversion"],
    }


def _suggest_improvements(patterns: Dict) -> List[str]:
    """Suggest trading improvements"""
    return [
        "Consider implementing systematic position sizing",
        "Review and backtest trading strategies",
        "Maintain detailed trading journal",
        "Focus on risk-adjusted returns rather than absolute returns",
    ]


def _analyze_sentiment_trends(sentiment_data: Dict) -> Dict:
    """Analyze sentiment trends"""
    return {
        "overall_trend": "neutral",
        "momentum": "stable",
        "divergences": [],
        "key_drivers": ["economic_data", "earnings", "geopolitical_events"],
    }


def _generate_sentiment_signals(sentiment_data: Dict) -> List[Dict]:
    """Generate trading signals based on sentiment"""
    signals = []

    for symbol, sentiment in sentiment_data.items():
        score = sentiment.get("score", 0)

        if score > 0.7:
            signals.append(
                {
                    "symbol": symbol,
                    "signal": "bullish",
                    "strength": "strong",
                    "confidence": sentiment.get("confidence", 0),
                }
            )
        elif score < -0.7:
            signals.append(
                {
                    "symbol": symbol,
                    "signal": "bearish",
                    "strength": "strong",
                    "confidence": sentiment.get("confidence", 0),
                }
            )

    return signals
