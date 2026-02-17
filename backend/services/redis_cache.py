"""
Redis cache service for brand context caching
"""
import redis
import json
from typing import Optional, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Service for Redis caching operations"""
    
    def __init__(self):
        self.client = None
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Continuing without cache.")
            self.client = None
    
    async def get(self, key: str) -> Optional[Dict]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value as dict, or None if not found or error
        """
        if not self.client:
            return None
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key '{key}': {str(e)}")
            return None
    
    async def set(self, key: str, value: Dict, ttl: int = 3600):
        """
        Set value in cache with TTL (time to live)
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 3600 = 1 hour)
        """
        if not self.client:
            return
        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.debug(f"Cached key '{key}' with TTL {ttl}s")
        except Exception as e:
            logger.error(f"Redis set error for key '{key}': {str(e)}")
    
    async def delete(self, key: str):
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
        """
        if not self.client:
            return
        try:
            self.client.delete(key)
            logger.debug(f"Deleted key '{key}' from cache")
        except Exception as e:
            logger.error(f"Redis delete error for key '{key}': {str(e)}")


# Singleton instance
redis_cache = RedisCacheService()

