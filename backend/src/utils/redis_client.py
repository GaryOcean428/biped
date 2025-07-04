"""
Redis Client Configuration for Biped Platform
Handles caching, sessions, and real-time features
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper with caching and real-time features"""

    def __init__(self):
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        self.connected = False
        self._connect()

    def _connect(self):
        """Establish Redis connection with Railway support and fallback"""
        try:
            # Try Railway Redis URL first
            if self.redis_url.startswith("rediss://"):
                # SSL connection for Railway production
                self.redis_client = redis.from_url(
                    self.redis_url, 
                    decode_responses=True, 
                    ssl_cert_reqs=None,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
            else:
                # Standard connection for Railway or local
                self.redis_client = redis.from_url(
                    self.redis_url, 
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )

            # Test connection
            self.redis_client.ping()
            self.connected = True
            logger.info(f"✅ Redis connected successfully to {self.redis_url[:30]}...")

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without Redis.")
            self.connected = False
            self.redis_client = None

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self.connected and self.redis_client is not None

    # Caching Methods
    def set_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache with TTL (default 1 hour)"""
        if not self.is_connected():
            return False

        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.is_connected():
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def delete_cache(self, key: str) -> bool:
        """Delete cached value"""
        if not self.is_connected():
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_cache_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern"""
        if not self.is_connected():
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0

    # Session Management
    def set_session(self, session_id: str, data: Dict, ttl: int = 86400) -> bool:
        """Set session data (default 24 hours)"""
        return self.set_cache(f"session:{session_id}", data, ttl)

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        return self.get_cache(f"session:{session_id}")

    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        return self.delete_cache(f"session:{session_id}")

    # Real-time Features
    def publish_notification(self, channel: str, message: Dict) -> bool:
        """Publish real-time notification"""
        if not self.is_connected():
            return False

        try:
            message["timestamp"] = datetime.utcnow().isoformat()
            serialized_message = json.dumps(message, default=str)
            self.redis_client.publish(channel, serialized_message)
            return True
        except Exception as e:
            logger.error(f"Publish notification error: {e}")
            return False

    def subscribe_to_channel(self, channel: str):
        """Subscribe to real-time channel"""
        if not self.is_connected():
            return None

        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.error(f"Subscribe error: {e}")
            return None

    # Rate Limiting
    def check_rate_limit(self, key: str, limit: int, window: int = 3600) -> Dict:
        """Check rate limit (requests per window)"""
        if not self.is_connected():
            return {"allowed": True, "remaining": limit, "reset_time": None}

        try:
            current_time = datetime.utcnow()
            window_start = current_time.replace(second=0, microsecond=0)
            rate_key = f"rate_limit:{key}:{window_start.isoformat()}"

            current_count = self.redis_client.get(rate_key)
            current_count = int(current_count) if current_count else 0

            if current_count >= limit:
                reset_time = window_start + timedelta(seconds=window)
                return {"allowed": False, "remaining": 0, "reset_time": reset_time.isoformat()}

            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, window)
            pipe.execute()

            return {
                "allowed": True,
                "remaining": limit - current_count - 1,
                "reset_time": (window_start + timedelta(seconds=window)).isoformat(),
            }

        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            return {"allowed": True, "remaining": limit, "reset_time": None}

    # Analytics & Metrics
    def increment_metric(self, metric_name: str, value: int = 1) -> bool:
        """Increment metric counter"""
        if not self.is_connected():
            return False

        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            key = f"metrics:{metric_name}:{today}"
            self.redis_client.incrby(key, value)
            self.redis_client.expire(key, 86400 * 30)  # Keep for 30 days
            return True
        except Exception as e:
            logger.error(f"Increment metric error: {e}")
            return False

    def get_metrics(self, metric_name: str, days: int = 7) -> Dict[str, int]:
        """Get metrics for the last N days"""
        if not self.is_connected():
            return {}

        try:
            metrics = {}
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
                key = f"metrics:{metric_name}:{date}"
                value = self.redis_client.get(key)
                metrics[date] = int(value) if value else 0
            return metrics
        except Exception as e:
            logger.error(f"Get metrics error: {e}")
            return {}

    # Health Check
    def health_check(self) -> Dict:
        """Redis health check"""
        if not self.is_connected():
            return {"status": "disconnected", "connected": False, "error": "Redis not connected"}

        try:
            info = self.redis_client.info()
            return {
                "status": "healthy",
                "connected": True,
                "version": info.get("redis_version"),
                "memory_used": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime": info.get("uptime_in_seconds"),
            }
        except Exception as e:
            return {"status": "error", "connected": False, "error": str(e)}


# Global Redis client instance
redis_client = RedisClient()


# Convenience functions
def cache_get(key: str) -> Optional[Any]:
    """Get cached value"""
    return redis_client.get_cache(key)


def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set cached value"""
    return redis_client.set_cache(key, value, ttl)


def cache_delete(key: str) -> bool:
    """Delete cached value"""
    return redis_client.delete_cache(key)


def publish_notification(channel: str, message: Dict) -> bool:
    """Publish real-time notification"""
    return redis_client.publish_notification(channel, message)


def check_rate_limit(key: str, limit: int, window: int = 3600) -> Dict:
    """Check rate limit"""
    return redis_client.check_rate_limit(key, limit, window)


def increment_metric(metric_name: str, value: int = 1) -> bool:
    """Increment metric"""
    return redis_client.increment_metric(metric_name, value)
