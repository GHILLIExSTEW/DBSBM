"""Redis cache manager for performance optimization."""

import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis

from config.database_mysql import REDIS_DB, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT

logger = logging.getLogger(__name__)

# Cache key prefixes for different data types
CACHE_PREFIXES = {
    "api_response": "api:",
    "db_query": "db:",
    "user_data": "user:",
    "guild_data": "guild:",
    "game_data": "game:",
    "team_data": "team:",
    "league_data": "league:",
    "parlay_data": "parlay:",
    "image_cache": "img:",
    "session": "session:",
}

# Default TTL values (in seconds)
DEFAULT_TTLS = {
    "api_response": 300,  # 5 minutes
    "db_query": 600,  # 10 minutes
    "user_data": 1800,  # 30 minutes
    "guild_data": 3600,  # 1 hour
    "game_data": 900,  # 15 minutes
    "team_data": 7200,  # 2 hours
    "league_data": 14400,  # 4 hours
    "parlay_data": 300,  # 5 minutes
    "image_cache": 86400,  # 24 hours
    "session": 1800,  # 30 minutes
}


class CacheManager:
    """Manages Redis caching for improved performance."""

    def __init__(self):
        """Initialize the cache manager."""
        self._redis_client: Optional[redis.Redis] = None
        self._is_connected = False
        self._connection_retries = 3
        self._retry_delay = 2

        # Validate Redis configuration
        if not REDIS_HOST:
            logger.warning("REDIS_HOST not configured, caching will be disabled")
            self._enabled = False
        else:
            self._enabled = True
            logger.info(
                f"Cache manager initialized with Redis host: {REDIS_HOST}:{REDIS_PORT}"
            )

    async def connect(self) -> bool:
        """Connect to Redis server."""
        if not self._enabled:
            logger.warning("Caching is disabled due to missing Redis configuration")
            return False

        if self._is_connected:
            return True

        for attempt in range(self._connection_retries):
            try:
                self._redis_client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    password=REDIS_PASSWORD,
                    db=REDIS_DB or 0,
                    decode_responses=False,  # Keep as bytes for pickle compatibility
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )

                # Test connection
                await self._redis_client.ping()
                self._is_connected = True
                logger.info("Successfully connected to Redis cache")
                return True

            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < self._connection_retries - 1:
                    await asyncio.sleep(self._retry_delay)

        logger.error("Failed to connect to Redis after all retries")
        self._enabled = False
        return False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis_client and self._is_connected:
            await self._redis_client.close()
            self._is_connected = False
            logger.info("Disconnected from Redis cache")

    def _get_cache_key(self, prefix: str, key: str) -> str:
        """Generate a cache key with prefix."""
        if prefix not in CACHE_PREFIXES:
            raise ValueError(f"Invalid cache prefix: {prefix}")
        return f"{CACHE_PREFIXES[prefix]}{key}"

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize a value for storage in Redis."""
        try:
            # Try JSON first for simple types
            return json.dumps(value, default=str).encode("utf-8")
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)

    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize a value from Redis storage."""
        if not value:
            return None

        try:
            # Try JSON first
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Fall back to pickle
                return pickle.loads(value)
            except Exception as e:
                logger.error(f"Failed to deserialize cached value: {e}")
                return None

    async def get(self, prefix: str, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self._enabled or not self._is_connected:
            return None

        try:
            cache_key = self._get_cache_key(prefix, key)
            value = await self._redis_client.get(cache_key)
            if value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return self._deserialize_value(value)
            else:
                logger.debug(f"Cache MISS: {cache_key}")
                return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    async def set(
        self, prefix: str, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache with optional TTL."""
        if not self._enabled or not self._is_connected:
            return False

        try:
            cache_key = self._get_cache_key(prefix, key)
            serialized_value = self._serialize_value(value)

            if ttl is None:
                ttl = DEFAULT_TTLS.get(prefix, 300)

            await self._redis_client.setex(cache_key, ttl, serialized_value)
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    async def delete(self, prefix: str, key: str) -> bool:
        """Delete a value from cache."""
        if not self._enabled or not self._is_connected:
            return False

        try:
            cache_key = self._get_cache_key(prefix, key)
            result = await self._redis_client.delete(cache_key)
            if result:
                logger.debug(f"Cache DELETE: {cache_key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    async def exists(self, prefix: str, key: str) -> bool:
        """Check if a key exists in cache."""
        if not self._enabled or not self._is_connected:
            return False

        try:
            cache_key = self._get_cache_key(prefix, key)
            return bool(await self._redis_client.exists(cache_key))
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False

    async def expire(self, prefix: str, key: str, ttl: int) -> bool:
        """Set expiration time for a cache key."""
        if not self._enabled or not self._is_connected:
            return False

        try:
            cache_key = self._get_cache_key(prefix, key)
            return bool(await self._redis_client.expire(cache_key, ttl))
        except Exception as e:
            logger.error(f"Error setting cache expiration: {e}")
            return False

    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with a specific prefix."""
        if not self._enabled or not self._is_connected:
            return 0

        try:
            pattern = f"{CACHE_PREFIXES[prefix]}*"
            keys = await self._redis_client.keys(pattern)
            if keys:
                deleted = await self._redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys with prefix: {prefix}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache prefix: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._enabled or not self._is_connected:
            return {"enabled": False, "connected": False}

        try:
            info = await self._redis_client.info()
            stats = {
                "enabled": True,
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }

            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total = hits + misses
            if total > 0:
                stats["hit_rate"] = f"{(hits / total) * 100:.2f}%"
            else:
                stats["hit_rate"] = "0.00%"

            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}

    async def health_check(self) -> bool:
        """Perform a health check on the cache connection."""
        if not self._enabled:
            return False

        try:
            if not self._is_connected:
                return await self.connect()

            await self._redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            self._is_connected = False
            return False


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions for common cache operations
async def cache_get(prefix: str, key: str) -> Optional[Any]:
    """Get a value from cache."""
    return await cache_manager.get(prefix, key)


async def cache_set(
    prefix: str, key: str, value: Any, ttl: Optional[int] = None
) -> bool:
    """Set a value in cache."""
    return await cache_manager.set(prefix, key, value, ttl)


async def cache_delete(prefix: str, key: str) -> bool:
    """Delete a value from cache."""
    return await cache_manager.delete(prefix, key)


async def cache_exists(prefix: str, key: str) -> bool:
    """Check if a key exists in cache."""
    return await cache_manager.exists(prefix, key)


async def cache_clear_prefix(prefix: str) -> int:
    """Clear all keys with a specific prefix."""
    return await cache_manager.clear_prefix(prefix)


# Database query caching decorator
def cache_query(prefix: str = "db_query", ttl: Optional[int] = None):
    """Decorator to cache database query results."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            # Try to get from cache first
            cached_result = await cache_get(prefix, cache_key)
            if cached_result is not None:
                return cached_result

            # Execute the function and cache the result
            result = await func(*args, **kwargs)
            await cache_set(prefix, cache_key, result, ttl)
            return result

        return wrapper

    return decorator


# API response caching decorator
def cache_api_response(prefix: str = "api_response", ttl: Optional[int] = None):
    """Decorator to cache API response results."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            # Try to get from cache first
            cached_result = await cache_get(prefix, cache_key)
            if cached_result is not None:
                return cached_result

            # Execute the function and cache the result
            result = await func(*args, **kwargs)
            await cache_set(prefix, cache_key, result, ttl)
            return result

        return wrapper

    return decorator
