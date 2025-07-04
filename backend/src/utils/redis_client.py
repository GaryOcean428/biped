import os
import redis
import logging

logger = logging.getLogger(__name__)

def get_redis_client():
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        try:
            client = redis.from_url(redis_url)
            client.ping()
            return client
        except Exception as e:
            logger.error(f"Redis error: {e}")
    return None

