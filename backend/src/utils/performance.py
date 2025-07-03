"""
Performance optimization utilities for TradeHub Platform
Provides caching, database optimization, and response compression
"""

import gzip
import hashlib
import io
import json
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional

import psutil
from flask import current_app, g, jsonify, request


class ResponseCache:
    """In-memory response cache with TTL support"""

    def __init__(self):
        self.cache = {}
        self.default_ttl = 300  # 5 minutes

    def _generate_cache_key(self, endpoint: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from endpoint and parameters"""
        key_data = {
            "endpoint": endpoint,
            "args": args,
            "kwargs": kwargs,
            "user_id": getattr(request, "current_user", {}).get("user_id", "anonymous"),
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            data, expires_at = self.cache[key]
            if time.time() < expires_at:
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set cached value with TTL"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        self.cache[key] = (value, expires_at)

    def cache_response(self, ttl: int = None):
        """Decorator to cache function responses"""

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                cache_key = self._generate_cache_key(f.__name__, args, kwargs)

                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # Execute function and cache result
                result = f(*args, **kwargs)
                self.set(cache_key, result, ttl)

                return result

            return decorated_function

        return decorator

    def clear_cache(self, pattern: str = None) -> None:
        """Clear cache entries matching pattern"""
        if pattern is None:
            self.cache.clear()
        else:
            keys_to_delete = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_delete:
                del self.cache[key]


class CompressionMiddleware:
    """Response compression middleware"""

    @staticmethod
    def compress_response(response, min_size: int = 1000):
        """Compress response if it's large enough and client supports it"""
        try:
            if (
                response.status_code == 200
                and hasattr(response, "data")
                and len(response.data) > min_size
                and "gzip" in request.headers.get("Accept-Encoding", "")
            ):

                # Compress the response data
                buffer = io.BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode="wb") as f:
                    f.write(response.data)

                response.data = buffer.getvalue()
                response.headers["Content-Encoding"] = "gzip"
                response.headers["Vary"] = "Accept-Encoding"
                response.headers["Content-Length"] = len(response.data)
        except (RuntimeError, AttributeError):
            # Skip compression if response is in passthrough mode or has no data
            pass

        return response


class DatabaseOptimizer:
    """Database performance optimization utilities"""

    @staticmethod
    def with_connection_pooling():
        """Context manager for database connection pooling"""
        # This would integrate with SQLAlchemy's connection pooling
        # For now, we'll add performance monitoring
        start_time = time.time()

        def log_query_time():
            query_time = (time.time() - start_time) * 1000
            if query_time > 100:  # Log slow queries (>100ms)
                current_app.logger.warning(f"Slow database query: {query_time:.2f}ms")

        return log_query_time

    @staticmethod
    def optimize_query_params(params: dict) -> dict:
        """Optimize query parameters for better performance"""
        optimized = {}

        for key, value in params.items():
            # Limit string lengths to prevent excessive memory usage
            if isinstance(value, str) and len(value) > 1000:
                optimized[key] = value[:1000]
            # Limit list sizes
            elif isinstance(value, list) and len(value) > 100:
                optimized[key] = value[:100]
            else:
                optimized[key] = value

        return optimized

    @staticmethod
    def monitor_slow_queries(threshold_ms: int = 100):
        """Decorator to monitor slow database queries"""

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                start_time = time.time()
                result = f(*args, **kwargs)
                query_time = (time.time() - start_time) * 1000

                if query_time > threshold_ms:
                    current_app.logger.warning(f"Slow query in {f.__name__}: {query_time:.2f}ms")

                return result

            return decorated_function

        return decorator


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""

    def __init__(self):
        self.metrics = {
            "request_count": 0,
            "response_times": [],
            "error_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def record_request(self, response_time: float, status_code: int) -> None:
        """Record request metrics"""
        self.metrics["request_count"] += 1
        self.metrics["response_times"].append(response_time)

        # Keep only last 1000 response times to prevent memory growth
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

        if status_code >= 400:
            self.metrics["error_count"] += 1

    def record_cache_hit(self) -> None:
        """Record cache hit"""
        self.metrics["cache_hits"] += 1

    def record_cache_miss(self) -> None:
        """Record cache miss"""
        self.metrics["cache_misses"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        response_times = self.metrics["response_times"]

        return {
            "request_count": self.metrics["request_count"],
            "error_count": self.metrics["error_count"],
            "error_rate": (self.metrics["error_count"] / max(1, self.metrics["request_count"]))
            * 100,
            "average_response_time": (
                sum(response_times) / len(response_times) if response_times else 0
            ),
            "cache_hit_rate": (
                self.metrics["cache_hits"]
                / max(1, self.metrics["cache_hits"] + self.metrics["cache_misses"])
            )
            * 100,
            "system_metrics": self._get_system_metrics(),
        }

    def _get_system_metrics(self) -> Dict[str, float]:
        """Get system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
            }
        except Exception:
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_used_gb": 0,
                "disk_percent": 0,
                "disk_free_gb": 0,
            }

    def monitor_performance(self, f: Callable) -> Callable:
        """Decorator to monitor function performance"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            try:
                result = f(*args, **kwargs)
                response_time = time.time() - start_time

                # Record metrics based on response type
                if hasattr(result, "status_code"):
                    self.record_request(response_time, result.status_code)
                else:
                    self.record_request(response_time, 200)

                return result
            except Exception as e:
                response_time = time.time() - start_time
                self.record_request(response_time, 500)
                raise

        return decorated_function


class StaticAssetOptimizer:
    """Static asset optimization utilities"""

    @staticmethod
    def add_cache_headers(response, max_age: int = 3600):
        """Add cache headers to static assets"""
        response.headers["Cache-Control"] = f"public, max-age={max_age}"
        response.headers["ETag"] = hashlib.md5(response.data).hexdigest()

        # Check for conditional requests
        if request.headers.get("If-None-Match") == response.headers["ETag"]:
            response.status_code = 304
            response.data = b""

        return response

    @staticmethod
    def optimize_static_assets():
        """Optimize static asset delivery"""

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                response = f(*args, **kwargs)

                # Add cache headers for static files
                if request.endpoint and "static" in request.endpoint:
                    response = StaticAssetOptimizer.add_cache_headers(response)

                return response

            return decorated_function

        return decorator


class TradingCacheService:
    """Trading-specific cache service with advanced features"""

    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.default_ttl = ttl
        self.access_times = {}
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if not expired"""
        if key in self.cache:
            data, expires_at = self.cache[key]
            if time.time() < expires_at:
                self.access_times[key] = time.time()
                self.hit_count += 1
                return data
            else:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]

        self.miss_count += 1
        return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Cache value with expiration"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        self.cache[key] = (value, expires_at)
        self.access_times[key] = time.time()

    def delete(self, key: str) -> bool:
        """Delete cached value"""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries"""
        self.cache.clear()
        self.access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "total_requests": total_requests,
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        current_time = time.time()
        expired_keys = []

        for key, (data, expires_at) in self.cache.items():
            if current_time >= expires_at:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]

        return len(expired_keys)


# Global instances
response_cache = ResponseCache()
performance_monitor = PerformanceMonitor()
database_optimizer = DatabaseOptimizer()
compression_middleware = CompressionMiddleware()
static_optimizer = StaticAssetOptimizer()
trading_cache = TradingCacheService()
