"""Redis-based caching system for high-performance caching."""

import asyncio
import json
import logging
import pickle
from functools import wraps
from typing import Any, Dict, Optional

import aioredis

logger = logging.getLogger(__name__)


class RedisCacheManager:
    """High-performance Redis-based cache manager."""

    def __init__(
        self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600
    ):
        """
        Initialize Redis cache manager.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default time to live in seconds
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> bool:
        """Connect to Redis."""
        try:
            self._redis = aioredis.from_url(self.redis_url, decode_responses=False)
            await self._redis.ping()
            logger.info("Connected to Redis successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis")

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in Redis cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self._redis:
            return False

        try:
            ttl = ttl or self.default_ttl
            serialized_value = pickle.dumps(value)
            await self._redis.setex(key, ttl, serialized_value)
            logger.debug(f"Cached value for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """
        Delete a value from Redis cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self._redis:
            return False

        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if not self._redis:
            return 0

        try:
            keys = await self._redis.keys(pattern)
            if keys:
                result = await self._redis.delete(*keys)
                logger.info(f"Deleted {result} keys matching pattern: {pattern}")
                return result
            return 0
        except Exception as e:
            logger.error(f"Error clearing pattern {pattern}: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self._redis:
            return {}

        try:
            info = await self._redis.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {}

    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    async def set_hash(
        self, key: str, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Set a hash in Redis cache.

        Args:
            key: Cache key
            data: Dictionary data to cache
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self._redis:
            return False

        try:
            ttl = ttl or self.default_ttl
            # Convert all values to strings for Redis hash
            hash_data = {
                k: (
                    json.dumps(v)
                    if not isinstance(v, (str, int, float, bool))
                    else str(v)
                )
                for k, v in data.items()
            }

            await self._redis.hset(key, mapping=hash_data)
            await self._redis.expire(key, ttl)
            logger.debug(f"Cached hash for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error setting hash for key {key}: {e}")
            return False

    async def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a hash from Redis cache.

        Args:
            key: Cache key

        Returns:
            Cached hash or None if not found
        """
        if not self._redis:
            return None

        try:
            data = await self._redis.hgetall(key)
            if data:
                # Convert back from strings
                result = {}
                for k, v in data.items():
                    k_str = k.decode() if isinstance(k, bytes) else k
                    v_str = v.decode() if isinstance(v, bytes) else v
                    try:
                        result[k_str] = json.loads(v_str)
                    except (json.JSONDecodeError, TypeError):
                        result[k_str] = v_str
                return result
            return None
        except Exception as e:
            logger.error(f"Error getting hash for key {key}: {e}")
            return None


# Global Redis cache instance
redis_cache = RedisCacheManager()


def redis_cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for Redis caching of function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = await redis_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_cache.set(cache_key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'll need to run in event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
