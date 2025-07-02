"""
Performance Optimization Module
Implements caching, async operations, and performance monitoring
"""

import time
import asyncio
import orjson
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from flask import Flask, g, request
from flask_caching import Cache
from dataclasses import dataclass
import logging

from .redis_client import redis_client

logger = logging.getLogger(__name__)

@dataclass
class PerformanceConfig:
    """Performance configuration settings"""
    cache_default_timeout: int = 300  # 5 minutes
    market_data_ttl: int = 5  # 5 seconds for real-time data
    portfolio_cache_ttl: int = 600  # 10 minutes
    query_cache_ttl: int = 1800  # 30 minutes
    max_concurrent_requests: int = 100
    request_timeout: int = 30

class TradingCacheService:
    """High-performance caching service for trading platform"""
    
    def __init__(self, app: Flask, config: PerformanceConfig = None):
        self.app = app
        self.config = config or PerformanceConfig()
        self.redis_client = redis_client
        
        # Initialize Flask-Caching
        self.cache = Cache(app, config={
            'CACHE_TYPE': 'RedisCache',
            'CACHE_REDIS_URL': app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
            'CACHE_DEFAULT_TIMEOUT': self.config.cache_default_timeout,
            'CACHE_KEY_PREFIX': 'biped:',
            'CACHE_OPTIONS': {
                'socket_keepalive': True,
                'socket_keepalive_options': {
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL  
                    3: 5,  # TCP_KEEPCNT
                }
            }
        })
        
    def cache_market_data(self, symbol: str, data: dict, ttl: int = None) -> bool:
        """Cache market data with short TTL for real-time updates"""
        try:
            ttl = ttl or self.config.market_data_ttl
            key = f"market:{symbol}"
            
            # Use orjson for faster serialization
            serialized_data = orjson.dumps(data)
            
            return self.redis_client.set_cache(key, serialized_data, ttl=ttl)
        except Exception as e:
            logger.error(f"Failed to cache market data for {symbol}: {e}")
            return False
            
    def get_market_data(self, symbol: str) -> Optional[dict]:
        """Retrieve cached market data"""
        try:
            key = f"market:{symbol}"
            data = self.redis_client.get_cache(key)
            
            if data:
                if isinstance(data, bytes):
                    return orjson.loads(data)
                elif isinstance(data, str):
                    return orjson.loads(data.encode())
                return data
            return None
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return None
            
    def cache_portfolio_snapshot(self, user_id: str, portfolio: dict) -> bool:
        """Cache portfolio snapshot with longer TTL"""
        try:
            key = f"portfolio:{user_id}"
            return self.cache.set(key, portfolio, timeout=self.config.portfolio_cache_ttl)
        except Exception as e:
            logger.error(f"Failed to cache portfolio for user {user_id}: {e}")
            return False
            
    def get_portfolio_snapshot(self, user_id: str) -> Optional[dict]:
        """Get cached portfolio snapshot"""
        try:
            key = f"portfolio:{user_id}"
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Failed to get portfolio for user {user_id}: {e}")
            return None
            
    def cache_user_data(self, user_id: str, data: dict, ttl: int = None) -> bool:
        """Cache user-specific data"""
        try:
            ttl = ttl or self.config.cache_default_timeout
            key = f"user:{user_id}"
            return self.cache.set(key, data, timeout=ttl)
        except Exception as e:
            logger.error(f"Failed to cache user data for {user_id}: {e}")
            return False
            
    def get_user_data(self, user_id: str) -> Optional[dict]:
        """Get cached user data"""
        try:
            key = f"user:{user_id}"
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Failed to get user data for {user_id}: {e}")
            return None
            
    def cache_query_result(self, query_key: str, result: Any, ttl: int = None) -> bool:
        """Cache database query results"""
        try:
            ttl = ttl or self.config.query_cache_ttl
            key = f"query:{query_key}"
            return self.cache.set(key, result, timeout=ttl)
        except Exception as e:
            logger.error(f"Failed to cache query result for {query_key}: {e}")
            return False
            
    def get_query_result(self, query_key: str) -> Optional[Any]:
        """Get cached query result"""
        try:
            key = f"query:{query_key}"
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Failed to get query result for {query_key}: {e}")
            return None
            
    def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalidate all user-related caches"""
        try:
            keys_to_delete = [
                f"user:{user_id}",
                f"portfolio:{user_id}",
                f"positions:{user_id}",
                f"trades:{user_id}",
                f"notifications:{user_id}"
            ]
            
            for key in keys_to_delete:
                self.cache.delete(key)
                
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate cache for user {user_id}: {e}")
            return False
            
    def invalidate_market_cache(self, symbol: str = None) -> bool:
        """Invalidate market data cache"""
        try:
            if symbol:
                key = f"market:{symbol}"
                return self.redis_client.delete_cache(key)
            else:
                # Invalidate all market data
                pattern = "market:*"
                keys = self.redis_client.redis_client.keys(pattern)
                if keys:
                    self.redis_client.redis_client.delete(*keys)
                return True
        except Exception as e:
            logger.error(f"Failed to invalidate market cache: {e}")
            return False
            
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics"""
        try:
            redis_info = self.redis_client.redis_client.info()
            
            return {
                'redis_connected': self.redis_client.is_connected(),
                'redis_memory_usage': redis_info.get('used_memory_human', 'unknown'),
                'redis_connected_clients': redis_info.get('connected_clients', 0),
                'redis_total_commands': redis_info.get('total_commands_processed', 0),
                'redis_keyspace_hits': redis_info.get('keyspace_hits', 0),
                'redis_keyspace_misses': redis_info.get('keyspace_misses', 0),
                'cache_hit_rate': self._calculate_hit_rate(
                    redis_info.get('keyspace_hits', 0),
                    redis_info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}
            
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100

class AsyncMarketDataService:
    """Async service for fetching market data"""
    
    def __init__(self, cache_service: TradingCacheService):
        self.cache_service = cache_service
        
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, dict]:
        """Fetch multiple quotes concurrently"""
        try:
            tasks = [self._get_quote_async(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            quote_data = {}
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to get quote for {symbol}: {result}")
                    quote_data[symbol] = None
                else:
                    quote_data[symbol] = result
                    
            return quote_data
        except Exception as e:
            logger.error(f"Failed to get multiple quotes: {e}")
            return {}
            
    async def _get_quote_async(self, symbol: str) -> Optional[dict]:
        """Get single quote with caching"""
        try:
            # Try cache first
            cached_quote = self.cache_service.get_market_data(symbol)
            if cached_quote:
                return cached_quote
                
            # Simulate external API call (replace with actual API)
            await asyncio.sleep(0.1)  # Simulate network latency
            
            # Generate mock data (replace with real API call)
            quote = {
                "symbol": symbol,
                "price": np.random.uniform(100, 200),
                "volume": np.random.randint(1000000, 10000000),
                "bid": np.random.uniform(99, 199),
                "ask": np.random.uniform(101, 201),
                "timestamp": datetime.utcnow().isoformat(),
                "change": np.random.uniform(-5, 5),
                "change_percent": np.random.uniform(-2.5, 2.5)
            }
            
            # Cache the result
            self.cache_service.cache_market_data(symbol, quote)
            
            return quote
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self, cache_service: TradingCacheService):
        self.cache_service = cache_service
        self.request_times = []
        self.max_stored_times = 1000
        
    def track_request_time(self, duration_ms: float, endpoint: str = None):
        """Track request processing time"""
        try:
            timestamp = time.time()
            request_data = {
                'duration_ms': duration_ms,
                'endpoint': endpoint or 'unknown',
                'timestamp': timestamp
            }
            
            # Store in memory for quick access
            self.request_times.append(request_data)
            if len(self.request_times) > self.max_stored_times:
                self.request_times.pop(0)
                
            # Store in Redis for persistence
            key = f"performance:request:{int(timestamp)}"
            self.cache_service.redis_client.set_cache(key, request_data, ttl=3600)  # 1 hour
            
        except Exception as e:
            logger.error(f"Failed to track request time: {e}")
            
    def get_performance_stats(self) -> dict:
        """Get performance statistics"""
        try:
            if not self.request_times:
                return {
                    'avg_response_time_ms': 0,
                    'min_response_time_ms': 0,
                    'max_response_time_ms': 0,
                    'total_requests': 0,
                    'requests_per_minute': 0
                }
                
            durations = [req['duration_ms'] for req in self.request_times]
            
            # Calculate time-based metrics
            now = time.time()
            recent_requests = [
                req for req in self.request_times 
                if now - req['timestamp'] <= 60  # Last minute
            ]
            
            return {
                'avg_response_time_ms': np.mean(durations),
                'min_response_time_ms': np.min(durations),
                'max_response_time_ms': np.max(durations),
                'p95_response_time_ms': np.percentile(durations, 95),
                'p99_response_time_ms': np.percentile(durations, 99),
                'total_requests': len(self.request_times),
                'requests_per_minute': len(recent_requests),
                'cache_stats': self.cache_service.get_cache_stats()
            }
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {'error': str(e)}

class DatabaseOptimizer:
    """Database query optimization utilities"""
    
    def __init__(self, cache_service: TradingCacheService):
        self.cache_service = cache_service
        
    def cached_query(self, query_key: str, query_func, ttl: int = None):
        """Decorator for caching database queries"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Try cache first
                cached_result = self.cache_service.get_query_result(query_key)
                if cached_result is not None:
                    return cached_result
                    
                # Execute query
                result = func(*args, **kwargs)
                
                # Cache result
                self.cache_service.cache_query_result(query_key, result, ttl)
                
                return result
            return wrapper
        return decorator
        
    def batch_query_optimizer(self, queries: List[dict]) -> List[Any]:
        """Optimize multiple queries by batching and caching"""
        try:
            results = []
            uncached_queries = []
            
            # Check cache for each query
            for query in queries:
                query_key = query.get('key')
                cached_result = self.cache_service.get_query_result(query_key)
                
                if cached_result is not None:
                    results.append(cached_result)
                else:
                    uncached_queries.append(query)
                    results.append(None)  # Placeholder
                    
            # Execute uncached queries
            if uncached_queries:
                # This would be implemented based on your specific database queries
                pass
                
            return results
        except Exception as e:
            logger.error(f"Failed to optimize batch queries: {e}")
            return []

def configure_performance(app: Flask) -> Flask:
    """Configure performance optimizations for Flask app"""
    
    # Connection pooling for SQLAlchemy
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 40,
        'pool_timeout': 30,
        'echo_pool': app.config.get('DEBUG', False)
    }
    
    # JSON optimization
    app.json_encoder = orjson.dumps
    app.json_decoder = orjson.loads
    
    # Request optimization
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request
    
    # Add performance monitoring middleware
    @app.before_request
    def before_request_performance():
        g.start_time = time.time()
        
    @app.after_request
    def after_request_performance(response):
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            
            # Track performance if monitor is available
            if hasattr(g, 'performance_monitor'):
                g.performance_monitor.track_request_time(duration_ms, request.endpoint)
                
            # Add performance headers
            response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
            
        return response
    
    return app

# Utility functions for performance optimization
def memoize_with_ttl(ttl: int = 300):
    """Memoization decorator with TTL"""
    def decorator(func):
        cache = {}
        
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            now = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl:
                    return result
                else:
                    del cache[key]
                    
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
            
        return wrapper
    return decorator

def async_cache_warmer(cache_service: TradingCacheService, symbols: List[str]):
    """Async function to warm up cache with market data"""
    async def warm_cache():
        try:
            market_service = AsyncMarketDataService(cache_service)
            await market_service.get_multiple_quotes(symbols)
            logger.info(f"Cache warmed for {len(symbols)} symbols")
        except Exception as e:
            logger.error(f"Failed to warm cache: {e}")
            
    return warm_cache

def performance_profiler(func):
    """Decorator to profile function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        logger.info(f"Function {func.__name__} took {duration_ms:.2f}ms")
        
        return result
    return wrapper

