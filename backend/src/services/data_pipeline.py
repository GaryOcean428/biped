"""
Advanced Data Pipeline and Analytics Service
Implements real-time data processing, analytics, and business intelligence
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import redis
from flask import current_app

from ..utils.redis_client import redis_client
from ..utils.performance import TradingCacheService

logger = logging.getLogger(__name__)

@dataclass
class MarketDataPoint:
    """Market data point structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float
    bid: float
    ask: float
    spread: float

@dataclass
class TradeEvent:
    """Trade event structure"""
    trade_id: str
    user_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    timestamp: datetime
    order_type: str
    commission: float
    metadata: Dict[str, Any]

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
            'processed_events': 0,
            'processing_errors': 0,
            'last_update': datetime.utcnow()
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
            self._update_analytics_cache()
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
                            'price': data.close,
                            'volume': data.volume,
                            'bid': data.bid,
                            'ask': data.ask,
                            'change': metrics.get('price_change_24h', 0),
                            'timestamp': data.timestamp.isoformat(),
                            'metrics': metrics
                        }
                        # Store in cache (simplified for compatibility)
                        try:
                            self.cache_service.set(cache_key, market_data_dict, timeout=60)
                        except Exception as cache_error:
                            logger.debug(f"Cache storage failed: {cache_error}")
                    
                    # Update processing stats
                    self.processing_stats['processed_events'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing market data: {e}")
                self.processing_stats['processing_errors'] += 1
                
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
    
    def _calculate_trade_impact(self, trade) -> float:
        """Calculate the market impact of a trade"""
        try:
            # Simple impact calculation based on trade size and market conditions
            base_impact = trade.quantity * trade.price / 1000000  # Normalize by $1M
            
            # Adjust for market volatility (simulated)
            volatility_factor = 1.0  # Would be calculated from market data
            
            return base_impact * volatility_factor
        except Exception as e:
            logger.error(f"Error calculating trade impact: {e}")
            return 0.0
    
    def _detect_trade_anomaly(self, trade) -> float:
        """Detect if a trade is anomalous (returns score 0-1)"""
        try:
            # Simple anomaly detection based on trade size
            if trade.quantity * trade.price > 100000:  # Large trade threshold
                return 0.9
            elif trade.quantity * trade.price > 50000:
                return 0.6
            else:
                return 0.1
        except Exception as e:
            logger.error(f"Error detecting trade anomaly: {e}")
            return 0.0
    
    async def _update_user_analytics(self, user_id: str, trade):
        """Update user analytics with new trade"""
        try:
            # Cache user trade data
            if self.cache_service:
                user_key = f"user_trades:{user_id}"
                # In production, this would update user analytics
                logger.debug(f"Updated analytics for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating user analytics: {e}")
    
    async def _flag_suspicious_trade(self, trade, anomaly_score: float):
        """Flag a suspicious trade for review"""
        try:
            suspicious_trade = {
                'trade_id': getattr(trade, 'id', 'unknown'),
                'user_id': trade.user_id,
                'symbol': trade.symbol,
                'quantity': trade.quantity,
                'price': trade.price,
                'anomaly_score': anomaly_score,
                'timestamp': trade.timestamp.isoformat(),
                'flagged_at': datetime.utcnow().isoformat()
            }
            
            if self.cache_service:
                try:
                    self.cache_service.set(f"suspicious_trade:{trade.user_id}", suspicious_trade, timeout=3600)
                except Exception as cache_error:
                    logger.debug(f"Cache storage failed: {cache_error}")
            
            logger.warning(f"Flagged suspicious trade: {suspicious_trade}")
        except Exception as e:
            logger.error(f"Error flagging suspicious trade: {e}")
    
    async def _calculate_real_time_metrics(self):
        """Calculate real-time metrics for all active symbols"""
        while True:
            try:
                # Get all active symbols from data buffer
                active_symbols = set()
                for key in self.data_buffer.keys():
                    if key.startswith('market:'):
                        symbol = key.replace('market:', '')
                        active_symbols.add(symbol)
                
                # Calculate metrics for each symbol
                for symbol in active_symbols:
                    if symbol in self.data_buffer.get(f"market:{symbol}", []):
                        latest_data = self.data_buffer[f"market:{symbol}"][-1] if self.data_buffer[f"market:{symbol}"] else None
                        if latest_data:
                            metrics = self._calculate_symbol_metrics(symbol, latest_data)
                            
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
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        metrics = {}
        
        try:
            # Price change
            if len(df) >= 2:
                metrics['price_change_24h'] = ((df['close'].iloc[-1] - df['close'].iloc[0]) / 
                                             df['close'].iloc[0]) * 100
            
            # Volatility (standard deviation of returns)
            if len(df) >= 10:
                returns = df['close'].pct_change().dropna()
                metrics['volatility'] = returns.std() * np.sqrt(252) * 100  # Annualized
            
            # RSI (Relative Strength Index)
            if len(df) >= 14:
                metrics['rsi'] = self._calculate_rsi(df['close'], 14)
            
            # MACD
            if len(df) >= 26:
                macd_line, signal_line = self._calculate_macd(df['close'])
                metrics['macd'] = macd_line
                metrics['macd_signal'] = signal_line
            
            # Bollinger Bands
            if len(df) >= 20:
                bb_upper, bb_lower = self._calculate_bollinger_bands(df['close'], 20, 2)
                metrics['bollinger_upper'] = bb_upper
                metrics['bollinger_lower'] = bb_lower
            
            # Support and Resistance
            metrics['support_level'] = df['low'].rolling(window=20).min().iloc[-1]
            metrics['resistance_level'] = df['high'].rolling(window=20).max().iloc[-1]
            
            # Volume metrics
            metrics['volume_sma'] = df['volume'].rolling(window=20).mean().iloc[-1]
            metrics['volume_ratio'] = df['volume'].iloc[-1] / metrics['volume_sma']
            
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
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        return macd_line.iloc[-1], signal_line.iloc[-1]
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[float, float]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band.iloc[-1], lower_band.iloc[-1]
    
    async def _fetch_market_data(self) -> Dict[str, MarketDataPoint]:
        """Fetch market data (simulated for demo)"""
        symbols = ['BTC/USD', 'ETH/USD', 'AAPL', 'GOOGL', 'TSLA', 'MSFT']
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
                spread=(current_price * 1.001) - (current_price * 0.999)
            )
            
        return market_data
    
    def _get_base_price(self, symbol: str) -> float:
        """Get base price for symbol (simulated)"""
        base_prices = {
            'BTC/USD': 45000,
            'ETH/USD': 3000,
            'AAPL': 150,
            'GOOGL': 2800,
            'TSLA': 250,
            'MSFT': 350
        }
        return base_prices.get(symbol, 100)
    
    async def _fetch_recent_trades(self) -> List:
        """Fetch recent trades (simulated for demo)"""
        # In production, this would query the database
        trades = []
        symbols = ['BTC/USD', 'ETH/USD', 'AAPL', 'GOOGL']
        
        for _ in range(5):  # Simulate 5 recent trades
            trade = type('Trade', (), {
                'symbol': np.random.choice(symbols),
                'side': np.random.choice(['buy', 'sell']),
                'quantity': np.random.uniform(0.1, 10),
                'price': np.random.uniform(100, 50000),
                'timestamp': datetime.utcnow(),
                'user_id': f"user_{np.random.randint(1, 100)}"
            })()
            trades.append(trade)
        
        return trades
    
    async def _detect_anomalies(self):
        """Detect anomalies in market data and trading patterns"""
        while self.is_running:
            try:
                # Check for unusual price movements
                for symbol in ['BTC/USD', 'ETH/USD', 'AAPL', 'GOOGL']:
                    buffer_key = f"market:{symbol}"
                    if buffer_key in self.data_buffer and len(self.data_buffer[buffer_key]) > 10:
                        recent_data = self.data_buffer[buffer_key][-10:]
                        prices = [point.close for point in recent_data]
                        
                        # Calculate price volatility
                        if len(prices) >= 2:
                            price_changes = [abs((prices[i] - prices[i-1]) / prices[i-1]) for i in range(1, len(prices))]
                            avg_volatility = np.mean(price_changes)
                            
                            # Flag if volatility is unusually high
                            if avg_volatility > 0.05:  # 5% threshold
                                logger.warning(f"High volatility detected for {symbol}: {avg_volatility:.2%}")
                                
                                # Store anomaly
                                anomaly = {
                                    'type': 'high_volatility',
                                    'symbol': symbol,
                                    'volatility': avg_volatility,
                                    'timestamp': datetime.utcnow().isoformat()
                                }
                                
                                if self.cache_service:
                                    try:
                                        self.cache_service.set(f"anomaly:{symbol}", anomaly, timeout=300)
                                    except Exception as cache_error:
                                        logger.debug(f"Cache storage failed: {cache_error}")
                
            except Exception as e:
                logger.error(f"Error detecting anomalies: {e}")
                
            await asyncio.sleep(60)  # Check every minute
    
    async def _update_analytics_cache(self):
        """Update analytics cache with latest data"""
        while self.is_running:
            try:
                # Update market summary
                market_summary = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'active_symbols': len([k for k in self.data_buffer.keys() if k.startswith('market:')]),
                    'total_events_processed': self.processing_stats['processed_events'],
                    'processing_errors': self.processing_stats['processing_errors'],
                    'uptime': (datetime.utcnow() - self.start_time).total_seconds()
                }
                
                if self.cache_service:
                    try:
                        self.cache_service.set('market_summary', market_summary, timeout=300)
                    except Exception as cache_error:
                        logger.debug(f"Cache storage failed: {cache_error}")
                
                # Update top movers
                top_movers = await self._calculate_top_movers()
                if self.cache_service:
                    try:
                        self.cache_service.set('top_movers', top_movers, timeout=300)
                    except Exception as cache_error:
                        logger.debug(f"Cache storage failed: {cache_error}")
                
            except Exception as e:
                logger.error(f"Error updating analytics cache: {e}")
                
            await asyncio.sleep(300)  # Update every 5 minutes
    
    async def _calculate_top_movers(self) -> Dict:
        """Calculate top moving symbols"""
        movers = {'gainers': [], 'losers': []}
        
        for symbol in ['BTC/USD', 'ETH/USD', 'AAPL', 'GOOGL', 'TSLA', 'MSFT']:
            buffer_key = f"market:{symbol}"
            if buffer_key in self.data_buffer and len(self.data_buffer[buffer_key]) >= 2:
                recent_data = self.data_buffer[buffer_key][-2:]
                if len(recent_data) >= 2:
                    price_change = ((recent_data[-1].close - recent_data[0].close) / recent_data[0].close) * 100
                    
                    mover_data = {
                        'symbol': symbol,
                        'price': recent_data[-1].close,
                        'change_percent': price_change,
                        'volume': recent_data[-1].volume
                    }
                    
                    if price_change > 0:
                        movers['gainers'].append(mover_data)
                    else:
                        movers['losers'].append(mover_data)
        
        # Sort by change percentage
        movers['gainers'] = sorted(movers['gainers'], key=lambda x: x['change_percent'], reverse=True)[:5]
        movers['losers'] = sorted(movers['losers'], key=lambda x: x['change_percent'])[:5]
        
        return movers

class BusinessIntelligenceEngine:
    """Business Intelligence and Reporting Engine"""
    
    def __init__(self, cache_service: TradingCacheService):
        self.cache_service = cache_service
        self.report_cache = {}
        
    async def generate_portfolio_analytics(self, user_id: str) -> Dict:
        """Generate comprehensive portfolio analytics"""
        try:
            # Get user positions and trades
            positions = await self._get_user_positions(user_id)
            trades = await self._get_user_trades(user_id, days=30)
            
            analytics = {
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'portfolio_summary': self._calculate_portfolio_summary(positions),
                'performance_metrics': self._calculate_performance_metrics(trades),
                'risk_metrics': self._calculate_risk_metrics(positions, trades),
                'allocation_analysis': self._analyze_allocation(positions),
                'trading_patterns': self._analyze_trading_patterns(trades),
                'recommendations': self._generate_recommendations(positions, trades)
            }
            
            # Cache analytics
            await self.cache_service.cache_user_data(
                f"{user_id}:analytics", analytics, ttl=3600
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating portfolio analytics for {user_id}: {e}")
            return {'error': str(e)}
    
    def _calculate_portfolio_summary(self, positions: List[Dict]) -> Dict:
        """Calculate portfolio summary metrics"""
        if not positions:
            return {
                'total_value': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0,
                'position_count': 0,
                'largest_position': None
            }
            
        total_value = sum(pos['current_value'] for pos in positions)
        total_pnl = sum(pos['unrealized_pnl'] for pos in positions)
        total_cost = sum(pos['cost_basis'] for pos in positions)
        
        return {
            'total_value': total_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / total_cost * 100) if total_cost > 0 else 0,
            'position_count': len(positions),
            'largest_position': max(positions, key=lambda x: x['current_value'])['symbol'],
            'daily_change': sum(pos.get('daily_change', 0) for pos in positions),
            'cash_balance': 0  # Would come from account data
        }
    
    def _calculate_performance_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate trading performance metrics"""
        if not trades:
            return {}
            
        df = pd.DataFrame(trades)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate returns
        df['pnl'] = df['quantity'] * df['price'] * np.where(df['side'] == 'sell', 1, -1)
        
        # Performance metrics
        total_trades = len(df)
        winning_trades = len(df[df['pnl'] > 0])
        losing_trades = len(df[df['pnl'] < 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'total_pnl': df['pnl'].sum(),
            'best_trade': df['pnl'].max(),
            'worst_trade': df['pnl'].min(),
            'avg_trade_size': df['quantity'].mean(),
            'trading_frequency': total_trades / 30  # trades per day over 30 days
        }
    
    def _calculate_risk_metrics(self, positions: List[Dict], trades: List[Dict]) -> Dict:
        """Calculate risk metrics"""
        if not trades:
            return {}
            
        df = pd.DataFrame(trades)
        df['pnl'] = df['quantity'] * df['price'] * np.where(df['side'] == 'sell', 1, -1)
        
        # Calculate daily returns
        daily_returns = df.groupby(df['timestamp'].dt.date)['pnl'].sum()
        
        if len(daily_returns) < 2:
            return {}
            
        # Risk metrics
        volatility = daily_returns.std() * np.sqrt(252)  # Annualized
        sharpe_ratio = (daily_returns.mean() * 252) / volatility if volatility > 0 else 0
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(daily_returns, 5)
        
        # Maximum drawdown
        cumulative_returns = daily_returns.cumsum()
        running_max = cumulative_returns.expanding().max()
        drawdown = cumulative_returns - running_max
        max_drawdown = drawdown.min()
        
        return {
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'var_95': var_95,
            'max_drawdown': max_drawdown,
            'current_drawdown': drawdown.iloc[-1] if len(drawdown) > 0 else 0,
            'beta': 1.0,  # Would calculate against market benchmark
            'correlation_to_market': 0.7  # Simulated
        }
    
    async def generate_market_intelligence(self) -> Dict:
        """Generate market intelligence report"""
        try:
            # Get market data for analysis
            symbols = ['BTC/USD', 'ETH/USD', 'AAPL', 'GOOGL', 'TSLA']
            market_analysis = {}
            
            for symbol in symbols:
                cached_data = await self.cache_service.get_market_data(symbol)
                if cached_data:
                    market_analysis[symbol] = {
                        'current_price': cached_data.get('price', 0),
                        'change_24h': cached_data.get('change', 0),
                        'volume': cached_data.get('volume', 0),
                        'metrics': cached_data.get('metrics', {}),
                        'sentiment': self._analyze_sentiment(symbol),
                        'technical_signals': self._get_technical_signals(symbol, cached_data)
                    }
            
            # Market overview
            market_overview = {
                'timestamp': datetime.utcnow().isoformat(),
                'market_sentiment': self._calculate_market_sentiment(market_analysis),
                'top_movers': self._get_top_movers(market_analysis),
                'sector_performance': self._analyze_sector_performance(market_analysis),
                'volatility_index': self._calculate_volatility_index(market_analysis),
                'market_breadth': self._calculate_market_breadth(market_analysis)
            }
            
            return {
                'market_overview': market_overview,
                'symbol_analysis': market_analysis,
                'trading_opportunities': self._identify_opportunities(market_analysis),
                'risk_alerts': self._generate_risk_alerts(market_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error generating market intelligence: {e}")
            return {'error': str(e)}
    
    def _analyze_sentiment(self, symbol: str) -> Dict:
        """Analyze market sentiment for symbol"""
        # Simulated sentiment analysis
        sentiment_score = np.random.uniform(-1, 1)
        
        return {
            'score': sentiment_score,
            'label': 'bullish' if sentiment_score > 0.2 else 'bearish' if sentiment_score < -0.2 else 'neutral',
            'confidence': abs(sentiment_score),
            'sources': ['news', 'social_media', 'analyst_reports']
        }
    
    def _get_technical_signals(self, symbol: str, data: Dict) -> Dict:
        """Get technical analysis signals"""
        metrics = data.get('metrics', {})
        price = data.get('price', 0)
        
        signals = []
        
        # RSI signals
        rsi = metrics.get('rsi', 50)
        if rsi > 70:
            signals.append({'type': 'overbought', 'strength': 'strong', 'indicator': 'RSI'})
        elif rsi < 30:
            signals.append({'type': 'oversold', 'strength': 'strong', 'indicator': 'RSI'})
        
        # Bollinger Bands signals
        bb_upper = metrics.get('bollinger_upper', 0)
        bb_lower = metrics.get('bollinger_lower', 0)
        
        if price > bb_upper:
            signals.append({'type': 'overbought', 'strength': 'medium', 'indicator': 'Bollinger Bands'})
        elif price < bb_lower:
            signals.append({'type': 'oversold', 'strength': 'medium', 'indicator': 'Bollinger Bands'})
        
        # Support/Resistance signals
        support = metrics.get('support_level', 0)
        resistance = metrics.get('resistance_level', 0)
        
        if price <= support * 1.02:  # Near support
            signals.append({'type': 'support', 'strength': 'medium', 'indicator': 'Support/Resistance'})
        elif price >= resistance * 0.98:  # Near resistance
            signals.append({'type': 'resistance', 'strength': 'medium', 'indicator': 'Support/Resistance'})
        
        return {
            'signals': signals,
            'overall_signal': self._determine_overall_signal(signals),
            'confidence': len(signals) / 5  # Normalize by max possible signals
        }
    
    async def _get_user_positions(self, user_id: str) -> List[Dict]:
        """Get user positions (simulated)"""
        # In production, this would query the database
        return [
            {
                'symbol': 'BTC/USD',
                'quantity': 0.5,
                'cost_basis': 22500,
                'current_value': 22750,
                'unrealized_pnl': 250,
                'daily_change': 50
            },
            {
                'symbol': 'AAPL',
                'quantity': 100,
                'cost_basis': 14500,
                'current_value': 15000,
                'unrealized_pnl': 500,
                'daily_change': -25
            }
        ]
    
    async def _get_user_trades(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get user trades (simulated)"""
        # In production, this would query the database
        trades = []
        for i in range(20):  # Simulate 20 trades
            trades.append({
                'symbol': np.random.choice(['BTC/USD', 'ETH/USD', 'AAPL', 'GOOGL']),
                'side': np.random.choice(['buy', 'sell']),
                'quantity': np.random.uniform(0.1, 10),
                'price': np.random.uniform(100, 50000),
                'timestamp': datetime.utcnow() - timedelta(days=np.random.randint(0, days)),
                'commission': np.random.uniform(1, 50)
            })
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
    processing_thread = threading.Thread(target=start_background_processing, daemon=True)
    processing_thread.start()
    
    return {
        'processor': processor,
        'bi_engine': bi_engine
    }

