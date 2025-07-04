"""
Advanced Data Pipeline and Analytics Service
Implements real-time data processing, analytics, and business intelligence
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import redis
from flask import current_app

from ..utils.performance import TradingCacheService
from ..utils.redis_client import redis_client

logger = logging.getLogger(__name__)


@dataclass
class MarketDataPoint:
    """Service market data point structure"""

    service_category: str
    timestamp: datetime
    avg_price: float
    high_price: float
    low_price: float
    total_jobs: int
    active_providers: int
    demand_index: float
    quote_response_rate: float
    avg_completion_time: float
    customer_satisfaction: float


@dataclass
class JobEvent:
    """Job event structure"""

    job_id: str
    customer_id: str
    provider_id: str
    service_category: str
    job_type: str  # 'quote_requested', 'quote_provided', 'job_started', 'job_completed'
    job_value: float
    timestamp: datetime
    location: str
    metadata: Dict[str, Any]


@dataclass
class ServiceDataPoint:
    """Service data point structure"""

    service_category: str
    timestamp: datetime
    avg_quote_price: float
    job_count: int
    completion_rate: float
    avg_rating: float
    provider_count: int
    demand_score: float


@dataclass
class AnalyticsMetrics:
    """Analytics metrics structure"""

    timestamp: datetime
    symbol: str
    price_change_24h: float
    volume_24h: float
    volatility: float
    momentum: float
    rsi: float
    macd: float
    bollinger_upper: float
    bollinger_lower: float
    support_level: float
    resistance_level: float


class RealTimeDataProcessor:
    """Real-time data processing engine"""

    def __init__(self, cache_service: TradingCacheService):
        self.cache_service = cache_service
        self.data_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.is_running = True
        self.start_time = datetime.utcnow()  # Add missing start_time
        self.processing_stats = {
            "processed_events": 0,
            "processing_errors": 0,
            "last_update": datetime.utcnow(),
        }
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def start_processing(self):
        """Start real-time data processing"""
        self.is_running = True

        # Start processing tasks
        tasks = [
            self._process_market_data_stream(),
            self._process_trade_events(),
            self._calculate_real_time_metrics(),
            self._detect_anomalies(),
            self._update_analytics_cache(),
        ]

        await asyncio.gather(*tasks)

    async def _process_market_data_stream(self):
        """Process incoming market data"""
        while self.is_running:
            try:
                # Simulate market data (in production, this would come from external feeds)
                market_data = await self._fetch_market_data()

                for symbol, data in market_data.items():
                    # Add to buffer
                    self.data_buffer[f"market:{symbol}"].append(data)

                    # Calculate real-time metrics
                    metrics = self._calculate_symbol_metrics(symbol, data)

                    # Cache metrics
                    if self.cache_service:
                        # Use the cache service properly
                        cache_key = f"market_data:{symbol}"
                        market_data_dict = {
                            "price": data.close,
                            "volume": data.volume,
                            "bid": data.bid,
                            "ask": data.ask,
                            "change": metrics.get("price_change_24h", 0),
                            "timestamp": data.timestamp.isoformat(),
                            "metrics": metrics,
                        }
                        # Store in cache (simplified for compatibility)
                        try:
                            self.cache_service.set(
                                cache_key, market_data_dict, timeout=60
                            )
                        except Exception as cache_error:
                            logger.debug(f"Cache storage failed: {cache_error}")

                    # Update processing stats
                    self.processing_stats["processed_events"] += 1

            except Exception as e:
                logger.error(f"Error processing market data: {e}")
                self.processing_stats["processing_errors"] += 1

            await asyncio.sleep(1)  # Process every second

    async def _process_trade_events(self):
        """Process trade events for analytics"""
        while self.is_running:
            try:
                # Get recent trades from database
                trades = await self._fetch_recent_trades()

                for trade in trades:
                    # Add to buffer
                    self.data_buffer[f"trades:{trade.symbol}"].append(trade)

                    # Calculate trade impact
                    impact = self._calculate_trade_impact(trade)

                    # Update user analytics
                    await self._update_user_analytics(trade.user_id, trade)

                    # Check for unusual patterns
                    anomaly_score = self._detect_trade_anomaly(trade)
                    if anomaly_score > 0.8:
                        await self._flag_suspicious_trade(trade, anomaly_score)

            except Exception as e:
                logger.error(f"Error processing trade events: {e}")

            await asyncio.sleep(5)  # Process every 5 seconds

    def _calculate_job_impact(self, job) -> float:
        """Calculate the market impact of a job"""
        try:
            # Simple impact calculation based on job value and market conditions
            base_impact = job.job_value / 100000  # Normalize by $100K for services

            # Adjust for service category volatility (simulated)
            volatility_factor = 1.0  # Would be calculated from service market data

            return base_impact * volatility_factor
        except Exception as e:
            logger.error(f"Error calculating job impact: {e}")
            return 0.0

    def _detect_job_anomaly(self, job) -> float:
        """Detect if a job is anomalous (returns score 0-1)"""
        try:
            # Simple anomaly detection based on job value
            if (
                hasattr(job, "job_value") and job.job_value > 10000
            ):  # Large job threshold
                return 0.9
            elif hasattr(job, "job_value") and job.job_value > 5000:
                return 0.6
            else:
                return 0.1
        except Exception as e:
            logger.error(f"Error detecting job anomaly: {e}")
            return 0.0

    async def _update_provider_analytics(self, provider_id: str, job):
        """Update provider analytics with new job"""
        try:
            # Cache provider job data
            if self.cache_service:
                provider_key = f"provider_jobs:{provider_id}"
                # In production, this would update provider analytics
                logger.debug(f"Updated analytics for provider {provider_id}")
        except Exception as e:
            logger.error(f"Error updating provider analytics: {e}")

    async def _flag_suspicious_job(self, job, anomaly_score: float):
        """Flag a suspicious job for review"""
        try:
            suspicious_job = {
                "job_id": getattr(job, "job_id", "unknown"),
                "customer_id": getattr(job, "customer_id", "unknown"),
                "provider_id": getattr(job, "provider_id", "unknown"),
                "service_category": getattr(job, "service_category", "unknown"),
                "job_value": getattr(job, "job_value", 0),
                "anomaly_score": anomaly_score,
                "timestamp": (
                    getattr(job, "timestamp", datetime.utcnow()).isoformat()
                    if hasattr(
                        getattr(job, "timestamp", datetime.utcnow()), "isoformat"
                    )
                    else str(getattr(job, "timestamp", datetime.utcnow()))
                ),
                "flagged_at": datetime.utcnow().isoformat(),
            }

            if self.cache_service:
                try:
                    self.cache_service.set(
                        f"suspicious_job:{getattr(job, 'provider_id', 'unknown')}",
                        suspicious_job,
                        timeout=3600,
                    )
                except Exception as cache_error:
                    logger.debug(f"Cache storage failed: {cache_error}")

            logger.warning(f"Flagged suspicious job: {suspicious_job}")
        except Exception as e:
            logger.error(f"Error flagging suspicious job: {e}")

    async def _calculate_real_time_metrics(self):
        """Calculate real-time metrics for all active symbols"""
        while True:
            try:
                # Get all active symbols from data buffer
                active_symbols = set()
                for key in self.data_buffer.keys():
                    if key.startswith("market:"):
                        symbol = key.replace("market:", "")
                        active_symbols.add(symbol)

                # Calculate metrics for each symbol
                for symbol in active_symbols:
                    if symbol in self.data_buffer.get(f"market:{symbol}", []):
                        latest_data = (
                            self.data_buffer[f"market:{symbol}"][-1]
                            if self.data_buffer[f"market:{symbol}"]
                            else None
                        )
                        if latest_data:
                            metrics = self._calculate_symbol_metrics(
                                symbol, latest_data
                            )

                            # Store metrics in cache
                            cache_key = f"metrics:{symbol}"
                            if self.cache_service:
                                self.cache_service.set(cache_key, metrics, timeout=60)

                            logger.debug(f"Updated metrics for {symbol}: {metrics}")

            except Exception as e:
                logger.error(f"Error calculating real-time metrics: {e}")

            await asyncio.sleep(30)  # Update metrics every 30 seconds

    def _calculate_symbol_metrics(self, symbol: str, data: MarketDataPoint) -> Dict:
        """Calculate technical indicators for a symbol"""
        buffer = self.data_buffer[f"market:{symbol}"]

        if len(buffer) < 20:  # Need minimum data points
            return {}

        # Convert to pandas for calculations
        df = pd.DataFrame([asdict(point) for point in buffer])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        metrics = {}

        try:
            # Price change
            if len(df) >= 2:
                metrics["price_change_24h"] = (
                    (df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0]
                ) * 100

            # Volatility (standard deviation of returns)
            if len(df) >= 10:
                returns = df["close"].pct_change().dropna()
                metrics["volatility"] = returns.std() * np.sqrt(252) * 100  # Annualized

            # RSI (Relative Strength Index)
            if len(df) >= 14:
                metrics["rsi"] = self._calculate_rsi(df["close"], 14)

            # MACD
            if len(df) >= 26:
                macd_line, signal_line = self._calculate_macd(df["close"])
                metrics["macd"] = macd_line
                metrics["macd_signal"] = signal_line

            # Bollinger Bands
            if len(df) >= 20:
                bb_upper, bb_lower = self._calculate_bollinger_bands(df["close"], 20, 2)
                metrics["bollinger_upper"] = bb_upper
                metrics["bollinger_lower"] = bb_lower

            # Support and Resistance
            metrics["support_level"] = df["low"].rolling(window=20).min().iloc[-1]
            metrics["resistance_level"] = df["high"].rolling(window=20).max().iloc[-1]

            # Volume metrics
            metrics["volume_sma"] = df["volume"].rolling(window=20).mean().iloc[-1]
            metrics["volume_ratio"] = df["volume"].iloc[-1] / metrics["volume_sma"]

        except Exception as e:
            logger.error(f"Error calculating metrics for {symbol}: {e}")

        return metrics

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50.0

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[float, float]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        return macd_line.iloc[-1], signal_line.iloc[-1]

    def _calculate_bollinger_bands(
        self, prices: pd.Series, period: int = 20, std_dev: int = 2
    ) -> Tuple[float, float]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band.iloc[-1], lower_band.iloc[-1]

    async def _fetch_market_data(self) -> Dict[str, MarketDataPoint]:
        """Fetch market data (simulated for demo)"""
        service_categories = [
            "Plumbing",
            "Electrical",
            "Carpentry",
            "Painting",
            "Landscaping",
            "Cleaning",
        ]
        market_data = {}

        for symbol in symbols:
            # Simulate realistic market data
            base_price = self._get_base_price(symbol)
            price_change = np.random.normal(0, 0.02)  # 2% volatility
            current_price = base_price * (1 + price_change)

            market_data[symbol] = MarketDataPoint(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                open=current_price * 0.999,
                high=current_price * 1.005,
                low=current_price * 0.995,
                close=current_price,
                volume=np.random.randint(100000, 1000000),
                vwap=current_price * 1.001,
                bid=current_price * 0.999,
                ask=current_price * 1.001,
                spread=(current_price * 1.001) - (current_price * 0.999),
            )

        return market_data

    def _get_base_price(self, service_category: str) -> float:
        """Get base price for service category (simulated)"""
        base_prices = {
            "Plumbing": 250,
            "Electrical": 350,
            "Carpentry": 400,
            "Painting": 45,
            "Landscaping": 800,
            "Cleaning": 40,
        }
        return base_prices.get(service_category, 200)

    async def _fetch_recent_jobs(self) -> List:
        """Fetch recent job completions (simulated for demo)"""
        # In production, this would query the database for completed jobs
        jobs = []
        service_categories = [
            "Plumbing",
            "Electrical",
            "Carpentry",
            "Painting",
            "Landscaping",
            "Cleaning",
        ]

        for _ in range(5):  # Simulate 5 recent job completions
            job = type(
                "Job",
                (),
                {
                    "service_category": np.random.choice(service_categories),
                    "job_type": np.random.choice(["quoted", "completed"]),
                    "job_value": np.random.uniform(100, 5000),
                    "quote_price": np.random.uniform(100, 5000),
                    "timestamp": datetime.utcnow(),
                    "customer_id": f"customer_{np.random.randint(1, 100)}",
                    "provider_id": f"provider_{np.random.randint(1, 50)}",
                },
            )()
            jobs.append(job)

        return jobs

    async def _detect_anomalies(self):
        """Detect anomalies in job pricing and service patterns"""
        while self.is_running:
            try:
                # Check for unusual pricing patterns
                for service_category in [
                    "Plumbing",
                    "Electrical",
                    "Carpentry",
                    "Painting",
                    "Landscaping",
                    "Cleaning",
                ]:
                    buffer_key = f"service:{service_category}"
                    if (
                        buffer_key in self.data_buffer
                        and len(self.data_buffer[buffer_key]) > 10
                    ):
                        recent_data = self.data_buffer[buffer_key][-10:]
                        prices = [
                            job.quote_price
                            for job in recent_data
                            if hasattr(job, "quote_price")
                        ]

                        # Calculate price volatility for service quotes
                        if len(prices) >= 2:
                            price_changes = [
                                abs((prices[i] - prices[i - 1]) / prices[i - 1])
                                for i in range(1, len(prices))
                            ]
                            avg_volatility = np.mean(price_changes)

                            # Flag if pricing volatility is unusually high (could indicate price manipulation)
                            if (
                                avg_volatility > 0.25
                            ):  # 25% threshold for service pricing
                                logger.warning(
                                    f"High pricing volatility detected for {service_category}: {avg_volatility:.2%}"
                                )

                                # Store anomaly
                                anomaly = {
                                    "type": "high_pricing_volatility",
                                    "service_category": service_category,
                                    "volatility": avg_volatility,
                                    "timestamp": datetime.utcnow().isoformat(),
                                }

                                if self.cache_service:
                                    try:
                                        self.cache_service.set(
                                            f"anomaly:{service_category}",
                                            anomaly,
                                            timeout=300,
                                        )
                                    except Exception as cache_error:
                                        logger.debug(
                                            f"Cache storage failed: {cache_error}"
                                        )

            except Exception as e:
                logger.error(f"Error detecting anomalies: {e}")

            await asyncio.sleep(60)  # Check every minute

    async def _update_analytics_cache(self):
        """Update analytics cache with latest data"""
        while self.is_running:
            try:
                # Update market summary
                market_summary = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_symbols": len(
                        [k for k in self.data_buffer.keys() if k.startswith("market:")]
                    ),
                    "total_events_processed": self.processing_stats["processed_events"],
                    "processing_errors": self.processing_stats["processing_errors"],
                    "uptime": (datetime.utcnow() - self.start_time).total_seconds(),
                }

                if self.cache_service:
                    try:
                        self.cache_service.set(
                            "market_summary", market_summary, timeout=300
                        )
                    except Exception as cache_error:
                        logger.debug(f"Cache storage failed: {cache_error}")

                # Update top movers
                top_movers = await self._calculate_top_movers()
                if self.cache_service:
                    try:
                        self.cache_service.set("top_movers", top_movers, timeout=300)
                    except Exception as cache_error:
                        logger.debug(f"Cache storage failed: {cache_error}")

            except Exception as e:
                logger.error(f"Error updating analytics cache: {e}")

            await asyncio.sleep(300)  # Update every 5 minutes

    async def _calculate_top_movers(self) -> Dict:
        """Calculate top moving service categories"""
        movers = {"price_increases": [], "price_decreases": []}

        for service_category in [
            "Plumbing",
            "Electrical",
            "Carpentry",
            "Painting",
            "Landscaping",
            "Cleaning",
        ]:
            buffer_key = f"service:{service_category}"
            if (
                buffer_key in self.data_buffer
                and len(self.data_buffer[buffer_key]) >= 2
            ):
                recent_data = self.data_buffer[buffer_key][-2:]
                if len(recent_data) >= 2:
                    price_change = (
                        (recent_data[-1].avg_price - recent_data[0].avg_price)
                        / recent_data[0].avg_price
                    ) * 100

                    mover_data = {
                        "service_category": service_category,
                        "avg_price": recent_data[-1].avg_price,
                        "change_percent": price_change,
                        "job_count": recent_data[-1].total_jobs,
                    }

                    if price_change > 0:
                        movers["price_increases"].append(mover_data)
                    else:
                        movers["price_decreases"].append(mover_data)

        # Sort by change percentage
        movers["price_increases"] = sorted(
            movers["price_increases"], key=lambda x: x["change_percent"], reverse=True
        )[:5]
        movers["price_decreases"] = sorted(
            movers["price_decreases"], key=lambda x: x["change_percent"]
        )[:5]

        return movers


class BusinessIntelligenceEngine:
    """Business Intelligence and Reporting Engine for Trade Services"""

    def __init__(self, cache_service: TradingCacheService):
        self.cache_service = cache_service
        self.report_cache = {}

    async def generate_provider_analytics(self, provider_id: str) -> Dict:
        """Generate comprehensive provider analytics"""
        try:
            # Get provider jobs and performance data
            jobs = await self._get_provider_jobs(provider_id)
            quotes = await self._get_provider_quotes(provider_id, days=30)

            analytics = {
                "provider_id": provider_id,
                "timestamp": datetime.utcnow().isoformat(),
                "business_summary": self._calculate_business_summary(jobs),
                "performance_metrics": self._calculate_performance_metrics(jobs),
                "pricing_analysis": self._calculate_pricing_metrics(quotes),
                "service_analysis": self._analyze_service_distribution(jobs),
                "customer_patterns": self._analyze_customer_patterns(jobs),
                "recommendations": self._generate_business_recommendations(
                    jobs, quotes
                ),
            }

            # Cache analytics
            await self.cache_service.cache_user_data(
                f"{provider_id}:analytics", analytics, ttl=3600
            )

            return analytics

        except Exception as e:
            logger.error(f"Error generating provider analytics for {provider_id}: {e}")
            return {"error": str(e)}

    def _calculate_business_summary(self, jobs: List[Dict]) -> Dict:
        """Calculate business summary metrics"""
        if not positions:
            return {
                "total_value": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "position_count": 0,
                "largest_position": None,
            }

        total_value = sum(pos["current_value"] for pos in positions)
        total_pnl = sum(pos["unrealized_pnl"] for pos in positions)
        total_cost = sum(pos["cost_basis"] for pos in positions)

        return {
            "total_value": total_value,
            "total_pnl": total_pnl,
            "total_pnl_percent": (
                (total_pnl / total_cost * 100) if total_cost > 0 else 0
            ),
            "position_count": len(positions),
            "largest_position": max(positions, key=lambda x: x["current_value"])[
                "symbol"
            ],
            "daily_change": sum(pos.get("daily_change", 0) for pos in positions),
            "cash_balance": 0,  # Would come from account data
        }

    def _calculate_performance_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate trading performance metrics"""
        if not trades:
            return {}

        df = pd.DataFrame(trades)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # Calculate returns
        df["pnl"] = df["quantity"] * df["price"] * np.where(df["side"] == "sell", 1, -1)

        # Performance metrics
        total_trades = len(df)
        winning_trades = len(df[df["pnl"] > 0])
        losing_trades = len(df[df["pnl"] < 0])

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_win = df[df["pnl"] > 0]["pnl"].mean() if winning_trades > 0 else 0
        avg_loss = df[df["pnl"] < 0]["pnl"].mean() if losing_trades > 0 else 0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            "total_pnl": df["pnl"].sum(),
            "best_trade": df["pnl"].max(),
            "worst_trade": df["pnl"].min(),
            "avg_trade_size": df["quantity"].mean(),
            "trading_frequency": total_trades / 30,  # trades per day over 30 days
        }

    def _calculate_risk_metrics(
        self, positions: List[Dict], trades: List[Dict]
    ) -> Dict:
        """Calculate risk metrics"""
        if not trades:
            return {}

        df = pd.DataFrame(trades)
        df["pnl"] = df["quantity"] * df["price"] * np.where(df["side"] == "sell", 1, -1)

        # Calculate daily returns
        daily_returns = df.groupby(df["timestamp"].dt.date)["pnl"].sum()

        if len(daily_returns) < 2:
            return {}

        # Risk metrics
        volatility = daily_returns.std() * np.sqrt(252)  # Annualized
        sharpe_ratio = (
            (daily_returns.mean() * 252) / volatility if volatility > 0 else 0
        )

        # Value at Risk (95% confidence)
        var_95 = np.percentile(daily_returns, 5)

        # Maximum drawdown
        cumulative_returns = daily_returns.cumsum()
        running_max = cumulative_returns.expanding().max()
        drawdown = cumulative_returns - running_max
        max_drawdown = drawdown.min()

        return {
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "var_95": var_95,
            "max_drawdown": max_drawdown,
            "current_drawdown": drawdown.iloc[-1] if len(drawdown) > 0 else 0,
            "beta": 1.0,  # Would calculate against market benchmark
            "correlation_to_market": 0.7,  # Simulated
        }

    async def generate_market_intelligence(self) -> Dict:
        """Generate market intelligence report"""
        try:
            # Get service market data for analysis
            service_categories = [
                "Plumbing",
                "Electrical",
                "Carpentry",
                "Painting",
                "Landscaping",
            ]
            market_analysis = {}

            for service_category in service_categories:
                cached_data = await self.cache_service.get_market_data(service_category)
                if cached_data:
                    market_analysis[service_category] = {
                        "avg_price": cached_data.get("price", 0),
                        "change_24h": cached_data.get("change", 0),
                        "job_volume": cached_data.get("volume", 0),
                        "metrics": cached_data.get("metrics", {}),
                        "demand_sentiment": self._analyze_demand_sentiment(
                            service_category
                        ),
                        "market_signals": self._get_market_signals(
                            service_category, cached_data
                        ),
                    }

            # Service market overview
            market_overview = {
                "timestamp": datetime.utcnow().isoformat(),
                "market_sentiment": self._calculate_market_sentiment(market_analysis),
                "top_demand_categories": self._get_top_demand_categories(
                    market_analysis
                ),
                "category_performance": self._analyze_category_performance(
                    market_analysis
                ),
                "pricing_volatility_index": self._calculate_pricing_volatility_index(
                    market_analysis
                ),
                "market_health": self._calculate_market_health(market_analysis),
            }

            return {
                "market_overview": market_overview,
                "symbol_analysis": market_analysis,
                "trading_opportunities": self._identify_opportunities(market_analysis),
                "risk_alerts": self._generate_risk_alerts(market_analysis),
            }

        except Exception as e:
            logger.error(f"Error generating market intelligence: {e}")
            return {"error": str(e)}

    def _analyze_sentiment(self, symbol: str) -> Dict:
        """Analyze market sentiment for symbol"""
        # Simulated sentiment analysis
        sentiment_score = np.random.uniform(-1, 1)

        return {
            "score": sentiment_score,
            "label": (
                "bullish"
                if sentiment_score > 0.2
                else "bearish" if sentiment_score < -0.2 else "neutral"
            ),
            "confidence": abs(sentiment_score),
            "sources": ["news", "social_media", "analyst_reports"],
        }

    def _get_technical_signals(self, symbol: str, data: Dict) -> Dict:
        """Get technical analysis signals"""
        metrics = data.get("metrics", {})
        price = data.get("price", 0)

        signals = []

        # RSI signals
        rsi = metrics.get("rsi", 50)
        if rsi > 70:
            signals.append(
                {"type": "overbought", "strength": "strong", "indicator": "RSI"}
            )
        elif rsi < 30:
            signals.append(
                {"type": "oversold", "strength": "strong", "indicator": "RSI"}
            )

        # Bollinger Bands signals
        bb_upper = metrics.get("bollinger_upper", 0)
        bb_lower = metrics.get("bollinger_lower", 0)

        if price > bb_upper:
            signals.append(
                {
                    "type": "overbought",
                    "strength": "medium",
                    "indicator": "Bollinger Bands",
                }
            )
        elif price < bb_lower:
            signals.append(
                {
                    "type": "oversold",
                    "strength": "medium",
                    "indicator": "Bollinger Bands",
                }
            )

        # Support/Resistance signals
        support = metrics.get("support_level", 0)
        resistance = metrics.get("resistance_level", 0)

        if price <= support * 1.02:  # Near support
            signals.append(
                {
                    "type": "support",
                    "strength": "medium",
                    "indicator": "Support/Resistance",
                }
            )
        elif price >= resistance * 0.98:  # Near resistance
            signals.append(
                {
                    "type": "resistance",
                    "strength": "medium",
                    "indicator": "Support/Resistance",
                }
            )

        return {
            "signals": signals,
            "overall_signal": self._determine_overall_signal(signals),
            "confidence": len(signals) / 5,  # Normalize by max possible signals
        }

    async def _get_provider_jobs(self, provider_id: str) -> List[Dict]:
        """Get provider completed jobs (simulated)"""
        # In production, this would query the database
        return [
            {
                "service_category": "Plumbing",
                "job_count": 15,
                "total_revenue": 3750,
                "avg_job_value": 250,
                "avg_rating": 4.8,
                "completion_rate": 0.95,
            },
            {
                "service_category": "Electrical",
                "job_count": 8,
                "total_revenue": 2800,
                "avg_job_value": 350,
                "avg_rating": 4.9,
                "completion_rate": 1.0,
            },
        ]

    async def _get_provider_quotes(
        self, provider_id: str, days: int = 30
    ) -> List[Dict]:
        """Get provider quotes (simulated)"""
        # In production, this would query the database
        quotes = []
        service_categories = [
            "Plumbing",
            "Electrical",
            "Carpentry",
            "Painting",
            "Landscaping",
            "Cleaning",
        ]
        for i in range(20):  # Simulate 20 quotes
            quotes.append(
                {
                    "service_category": np.random.choice(service_categories),
                    "quote_type": np.random.choice(["fixed_price", "hourly_rate"]),
                    "quote_amount": np.random.uniform(100, 2000),
                    "job_value": np.random.uniform(150, 2500),
                    "timestamp": datetime.utcnow()
                    - timedelta(days=np.random.randint(0, days)),
                    "accepted": np.random.choice([True, False], p=[0.3, 0.7]),
                }
            )
        return trades


# Initialize services
def create_data_services(app, cache_service: TradingCacheService):
    """Create and configure data services"""

    # Real-time processor
    processor = RealTimeDataProcessor(cache_service)

    # Business intelligence engine
    bi_engine = BusinessIntelligenceEngine(cache_service)

    # Start background processing
    def start_background_processing():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(processor.start_processing())

    # Start in background thread
    processing_thread = threading.Thread(
        target=start_background_processing, daemon=True
    )
    processing_thread.start()

    return {"processor": processor, "bi_engine": bi_engine}
