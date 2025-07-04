import logging
import os

import redis

logger = logging.getLogger(__name__)


def get_redis_client():
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            client = redis.from_url(redis_url)
            client.ping()
            return client
        except Exception as e:
            logger.error(f"Redis error: {e}")
    return None


# Create a global redis client instance
redis_client = get_redis_client()


# Additional utility functions for backward compatibility
def publish_notification(channel, data):
    """Publish notification to Redis channel"""
    if redis_client:
        try:
            redis_client.publish(channel, data)
        except Exception as e:
            logger.error(f"Failed to publish notification: {e}")


class RedisClient:
    """Redis client wrapper for backward compatibility"""

    def __init__(self):
        self.redis_client = redis_client

    def is_connected(self):
        """Check if Redis is connected"""
        if self.redis_client:
            try:
                self.redis_client.ping()
                return True
            except (ConnectionError, TimeoutError, Exception):
                return False
        return False

    def get_cache(self, key):
        """Get value from cache"""
        if self.redis_client:
            try:
                return self.redis_client.get(key)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        return None

    def set_cache(self, key, value, ttl=None):
        """Set value in cache"""
        if self.redis_client:
            try:
                if ttl:
                    self.redis_client.setex(key, ttl, value)
                else:
                    self.redis_client.set(key, value)
            except Exception as e:
                logger.error(f"Redis set error: {e}")

    def delete_cache(self, key):
        """Delete key from cache"""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

    def get_session(self, session_id):
        """Get session data"""
        return self.get_cache(f"session:{session_id}")

    def set_session(self, session_id, data, ttl=3600):
        """Set session data"""
        self.set_cache(f"session:{session_id}", data, ttl)

    def delete_session(self, session_id):
        """Delete session"""
        self.delete_cache(f"session:{session_id}")

    def publish_notification(self, channel, data):
        """Publish notification"""
        publish_notification(channel, data)


# Create default instance for backward compatibility
if not redis_client:
    # Create a mock redis client for when Redis is not available
    class MockRedisClient:
        def is_connected(self):
            return False

        def get_cache(self, key):
            return None

        def set_cache(self, key, value, ttl=None):
            pass

        def delete_cache(self, key):
            pass

        def get_session(self, session_id):
            return None

        def set_session(self, session_id, data, ttl=3600):
            pass

        def delete_session(self, session_id):
            pass

        def publish_notification(self, channel, data):
            pass

        @property
        def redis_client(self):
            return None

    redis_client = MockRedisClient()
