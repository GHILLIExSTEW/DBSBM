"""
Enhanced Redis Cache Manager for DBSBM System

This module provides advanced caching capabilities with:
- Connection pooling
- Automatic retry logic
- Circuit breaker pattern
- Advanced serialization
- Cache warming
- Performance monitoring
"""

import asyncio
import json
import logging
import os
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

# Import centralized configuration with fallback
try:
    from config.settings import get_settings
except ImportError:
    # Fallback - try to import from parent directory
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Add multiple possible paths for different execution contexts
    possible_paths = [
        os.path.dirname(os.path.dirname(current_dir)),  # From bot/utils/
        os.path.dirname(current_dir),  # From utils/
    ]
    for path in possible_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        from config.settings import get_settings
    except ImportError:
        # Final fallback - create mock function for testing
        def get_settings():
            return None


logger = logging.getLogger(__name__)

# Cache key prefixes for different data types
CACHE_PREFIXES = {
    "api_response": "api:",
    "db_query": "db:",
    "database": "db:",  # Alias for database queries
    "user_data": "user:",
    "guild_data": "guild:",
    "game_data": "game:",
    "team_data": "team:",
    "league_data": "league:",
    "parlay_data": "parlay:",
    "image_cache": "img:",
    "session": "session:",
    "weather_data": "weather:",
    "odds_data": "odds:",
    "stats_data": "stats:",
    "analytics_data": "analytics:",
}

# Default TTL values (in seconds)
DEFAULT_TTLS = {
    "api_response": 300,  # 5 minutes
    "db_query": 600,  # 10 minutes
    "database": 600,  # 10 minutes (alias for db_query)
    "user_data": 1800,  # 30 minutes
    "guild_data": 3600,  # 1 hour
    "game_data": 900,  # 15 minutes
    "team_data": 7200,  # 2 hours
    "league_data": 14400,  # 4 hours
    "parlay_data": 300,  # 5 minutes
    "image_cache": 86400,  # 24 hours
    "session": 1800,  # 30 minutes
    "weather_data": 1800,  # 30 minutes
    "odds_data": 300,  # 5 minutes
    "stats_data": 3600,  # 1 hour
    "analytics_data": 7200,  # 2 hours
}


class CircuitBreaker:
    """Circuit breaker pattern for cache operations."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def on_success(self):
        """Called when an operation succeeds."""
        self.failure_count = 0
        self.state = "CLOSED"

    def on_failure(self):
        """Called when an operation fails."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class EnhancedCacheManager:
    """Enhanced Redis cache manager with advanced features."""

    def __init__(self):
        """Initialize the enhanced cache manager."""
        self.settings = get_settings()
        self._redis_client: Optional[redis.Redis] = None
        self._connection_pool: Optional[ConnectionPool] = None
        self._is_connected = False
        self._connection_retries = 3
        self._retry_delay = 2
        self._circuit_breaker = CircuitBreaker()
        # Local cache fallback (in-memory cache when Redis is unavailable)
        self._local_cache = {}
        self._local_cache_ttl = {}
        self._use_local_fallback = True

        self._performance_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_operations": 0,
        }

        # Get Redis configuration
        if self.settings and hasattr(self.settings, "redis"):
            self._redis_host = self.settings.redis.host
            self._redis_port = self.settings.redis.port
            self._redis_username = getattr(self.settings.redis, "username", None)
            self._redis_password = (
                self.settings.redis.password.get_secret_value()
                if self.settings.redis.password
                else None
            )
            self._redis_db = self.settings.redis.database
        else:
            # Fallback to environment variables
            self._redis_host = os.getenv("REDIS_HOST")
            self._redis_port = int(os.getenv("REDIS_PORT", "11437"))
            self._redis_username = os.getenv("REDIS_USERNAME", "default")
            self._redis_password = os.getenv("REDIS_PASSWORD")
            self._redis_db = int(os.getenv("REDIS_DB", "0"))

        # Validate Redis configuration
        if not self._redis_host:
            logger.warning("REDIS_HOST not configured, caching will be disabled")
            self._enabled = False
        else:
            # Check if Redis is explicitly disabled via environment variable
            redis_disabled = os.getenv("REDIS_DISABLED", "false").lower() == "true"
            if redis_disabled:
                logger.info(
                    "Redis is explicitly disabled via REDIS_DISABLED environment variable"
                )
                self._enabled = False
            else:
                self._enabled = True
                logger.info(
                    f"Enhanced cache manager initialized with Redis Cloud: {self._redis_host}:{self._redis_port}"
                )
                if self._redis_username:
                    logger.info(f"Redis username: {self._redis_username}")

    async def connect(self) -> bool:
        """Connect to Redis Cloud server with connection pooling and authentication."""
        if not self._enabled:
            logger.warning("Caching is disabled due to missing Redis configuration")
            return False

        if self._is_connected:
            return True

        if not self._circuit_breaker.can_execute():
            logger.warning("Circuit breaker is OPEN, skipping connection attempt")
            return False

        # Use a shorter timeout to prevent hanging
        for attempt in range(self._connection_retries):
            try:
                # Create connection pool with Redis Cloud configuration
                pool_kwargs = {
                    "host": self._redis_host,
                    "port": self._redis_port,
                    "db": self._redis_db,
                    "decode_responses": False,  # Keep as bytes for pickle compatibility
                    "socket_connect_timeout": 5,  # Reduced timeout to prevent hanging
                    "socket_timeout": 5,  # Reduced timeout to prevent hanging
                    "retry_on_timeout": True,
                    "health_check_interval": 30,
                    "max_connections": 20,
                    "retry_on_error": [redis.ConnectionError, redis.TimeoutError],
                }

                # Add authentication if provided
                if self._redis_username and self._redis_password:
                    pool_kwargs["username"] = self._redis_username
                    pool_kwargs["password"] = self._redis_password
                elif self._redis_password:
                    pool_kwargs["password"] = self._redis_password

                self._connection_pool = ConnectionPool(**pool_kwargs)

                # Create Redis client with connection pool
                self._redis_client = redis.Redis(connection_pool=self._connection_pool)

                # Test connection with authentication using asyncio.wait_for to prevent hanging
                try:
                    await asyncio.wait_for(self._redis_client.ping(), timeout=5.0)
                    self._is_connected = True
                    self._circuit_breaker.on_success()
                    logger.info(
                        f"Successfully connected to Redis Cloud: {self._redis_host}:{self._redis_port}"
                    )
                    return True
                except asyncio.TimeoutError:
                    logger.warning(f"Redis ping timeout on attempt {attempt + 1}")
                    self._circuit_breaker.on_failure()
                    if attempt < self._connection_retries - 1:
                        await asyncio.sleep(self._retry_delay)
                    continue

            except redis.AuthenticationError as e:
                logger.error(f"Redis authentication failed: {e}")
                self._circuit_breaker.on_failure()
                break  # Don't retry authentication errors
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                self._circuit_breaker.on_failure()
                if attempt < self._connection_retries - 1:
                    await asyncio.sleep(self._retry_delay)

        logger.warning(
            "Failed to connect to Redis Cloud after all retries - continuing with local cache only"
        )
        self._enabled = False
        return False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis_client and self._is_connected:
            await self._redis_client.close()
            if self._connection_pool:
                await self._connection_pool.disconnect()
            self._is_connected = False
            logger.info("Disconnected from Redis cache")

    def _get_cache_key(self, prefix: str, key: str) -> str:
        """Generate a cache key with prefix."""
        if prefix not in CACHE_PREFIXES:
            raise ValueError(f"Invalid cache prefix: {prefix}")
        return f"{CACHE_PREFIXES[prefix]}{key}"

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize a value for storage in Redis with compression."""
        try:
            # Try JSON first for simple types
            return json.dumps(value, default=str).encode("utf-8")
        except (TypeError, ValueError):
            try:
                # Fall back to pickle for complex objects
                return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception as e:
                logger.error(f"Failed to serialize value: {e}")
                return pickle.dumps(None)

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
        """Get a value from cache with performance tracking and local fallback."""
        self._performance_stats["total_operations"] += 1

        # Try Redis first
        if self._enabled and self._is_connected:
            try:
                cache_key = self._get_cache_key(prefix, key)
                value = await self._redis_client.get(cache_key)

                if value is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    self._performance_stats["hits"] += 1
                    return self._deserialize_value(value)
                else:
                    logger.debug(f"Cache MISS: {cache_key}")
                    self._performance_stats["misses"] += 1
                    return None
            except Exception as e:
                logger.warning(f"Redis cache error, falling back to local cache: {e}")
                self._performance_stats["errors"] += 1

        # Fallback to local cache
        if self._use_local_fallback:
            try:
                local_key = f"{prefix}:{key}"
                if local_key in self._local_cache:
                    # Check TTL
                    if local_key in self._local_cache_ttl:
                        if time.time() < self._local_cache_ttl[local_key]:
                            logger.debug(f"Local cache HIT: {local_key}")
                            self._performance_stats["hits"] += 1
                            return self._local_cache[local_key]
                        else:
                            # Expired, remove from cache
                            del self._local_cache[local_key]
                            del self._local_cache_ttl[local_key]

                logger.debug(f"Local cache MISS: {local_key}")
                self._performance_stats["misses"] += 1
                return None
            except Exception as e:
                logger.error(f"Error accessing local cache: {e}")
                self._performance_stats["errors"] += 1

        return None

    async def set(
        self, prefix: str, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache with optional TTL and local fallback."""
        self._performance_stats["total_operations"] += 1

        if ttl is None:
            ttl = DEFAULT_TTLS.get(prefix, 300)

        # Try Redis first
        if self._enabled and self._is_connected:
            try:
                cache_key = self._get_cache_key(prefix, key)
                serialized_value = self._serialize_value(value)
                await self._redis_client.setex(cache_key, ttl, serialized_value)
                logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")

                # Also set in local cache for fallback
                if self._use_local_fallback:
                    local_key = f"{prefix}:{key}"
                    self._local_cache[local_key] = value
                    self._local_cache_ttl[local_key] = time.time() + ttl

                return True
            except Exception as e:
                logger.warning(f"Redis cache error, using local cache only: {e}")
                self._performance_stats["errors"] += 1

        # Fallback to local cache only
        if self._use_local_fallback:
            try:
                local_key = f"{prefix}:{key}"
                self._local_cache[local_key] = value
                self._local_cache_ttl[local_key] = time.time() + ttl
                logger.debug(f"Local cache SET: {local_key} (TTL: {ttl}s)")
                return True
            except Exception as e:
                logger.error(f"Error setting local cache: {e}")
                self._performance_stats["errors"] += 1

        return False

    async def mget(self, prefix: str, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple values from cache efficiently."""
        self._performance_stats["total_operations"] += 1

        if not self._enabled or not self._is_connected:
            return [None] * len(keys)

        try:
            cache_keys = [self._get_cache_key(prefix, key) for key in keys]
            values = await self._redis_client.mget(cache_keys)

            results = []
            for i, value in enumerate(values):
                if value is not None:
                    logger.debug(f"Cache HIT: {cache_keys[i]}")
                    self._performance_stats["hits"] += 1
                    results.append(self._deserialize_value(value))
                else:
                    logger.debug(f"Cache MISS: {cache_keys[i]}")
                    self._performance_stats["misses"] += 1
                    results.append(None)

            return results
        except Exception as e:
            logger.error(f"Error getting multiple values from cache: {e}")
            self._performance_stats["errors"] += 1
            return [None] * len(keys)

    async def mset(
        self, prefix: str, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache efficiently."""
        self._performance_stats["total_operations"] += 1

        if not self._enabled or not self._is_connected:
            return False

        try:
            if ttl is None:
                ttl = DEFAULT_TTLS.get(prefix, 300)

            # Prepare data for mset
            mset_data = {}
            for key, value in data.items():
                cache_key = self._get_cache_key(prefix, key)
                mset_data[cache_key] = self._serialize_value(value)

            # Use pipeline for atomic operation
            async with self._redis_client.pipeline() as pipe:
                await pipe.mset(mset_data)
                for cache_key in mset_data.keys():
                    await pipe.expire(cache_key, ttl)
                await pipe.execute()

            logger.debug(f"Cache MSET: {len(data)} keys (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting multiple values in cache: {e}")
            self._performance_stats["errors"] += 1
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

    async def clear_prefix(self, prefix: str, pattern: str = None) -> int:
        """Clear all keys with a specific prefix."""
        if not self._enabled or not self._is_connected:
            return 0

        try:
            if pattern:
                # Use the provided pattern directly
                search_pattern = f"{CACHE_PREFIXES.get(prefix, prefix)}*{pattern}*"
            else:
                # Use the default prefix pattern
                search_pattern = f"{CACHE_PREFIXES[prefix]}*"

            keys = await self._redis_client.keys(search_pattern)
            if keys:
                deleted = await self._redis_client.delete(*keys)
                logger.info(
                    f"Cleared {deleted} cache keys with prefix: {prefix}, pattern: {pattern}"
                )
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache prefix: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive Redis Cloud statistics."""
        if not self._enabled or not self._is_connected:
            return {"enabled": False, "connected": False}

        try:
            info = await self._redis_client.info()

            # Calculate hit rate
            hits = self._performance_stats["hits"]
            misses = self._performance_stats["misses"]
            total = hits + misses
            hit_rate = f"{(hits / total) * 100:.2f}%" if total > 0 else "0.00%"

            stats = {
                "enabled": True,
                "connected": True,
                "circuit_breaker_state": self._circuit_breaker.state,
                "redis_cloud_config": {
                    "host": self._redis_host,
                    "port": self._redis_port,
                    "username": self._redis_username,
                    "database": self._redis_db,
                },
                "performance": {
                    "hits": hits,
                    "misses": misses,
                    "errors": self._performance_stats["errors"],
                    "total_operations": self._performance_stats["total_operations"],
                    "hit_rate": hit_rate,
                },
                "redis_cloud_info": {
                    "version": info.get("redis_version", "unknown"),
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                },
                "local_cache": {
                    "size": len(self._local_cache),
                    "ttl_entries": len(self._local_cache_ttl),
                },
            }

            # Calculate Redis Cloud hit rate
            redis_hits = info.get("keyspace_hits", 0)
            redis_misses = info.get("keyspace_misses", 0)
            redis_total = redis_hits + redis_misses
            if redis_total > 0:
                stats["redis_cloud_info"][
                    "redis_hit_rate"
                ] = f"{(redis_hits/redis_total)*100:.2f}%"
            else:
                stats["redis_cloud_info"]["redis_hit_rate"] = "0.00%"

            return stats
        except Exception as e:
            logger.error(f"Error getting Redis Cloud stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}

    async def health_check(self) -> bool:
        """Perform a comprehensive health check on the Redis Cloud connection."""
        if not self._enabled:
            return False

        try:
            if not self._is_connected:
                return await self.connect()

            # Test basic connectivity
            await self._redis_client.ping()

            # Test basic operations
            test_key = "_health_check_test"
            test_value = "health_check"

            # Test set operation
            await self._redis_client.setex(test_key, 10, test_value.encode())

            # Test get operation
            result = await self._redis_client.get(test_key)
            if result.decode() != test_value:
                raise Exception("Health check get/set test failed")

            # Test delete operation
            await self._redis_client.delete(test_key)

            # Test Redis Cloud specific features
            try:
                # Test info command to get Redis Cloud info
                info = await self._redis_client.info()
                if "redis_version" in info:
                    logger.debug(f"Redis version: {info['redis_version']}")
                if "used_memory_human" in info:
                    logger.debug(f"Memory usage: {info['used_memory_human']}")
            except Exception as e:
                logger.warning(f"Could not get Redis info: {e}")

            # Check circuit breaker state
            if not self._circuit_breaker.can_execute():
                logger.warning("Circuit breaker is OPEN during health check")
                return False

            logger.debug("Redis Cloud health check passed")
            return True
        except redis.AuthenticationError as e:
            logger.error(f"Redis Cloud authentication failed during health check: {e}")
            self._is_connected = False
            self._circuit_breaker.on_failure()
            return False
        except Exception as e:
            logger.error(f"Redis Cloud health check failed: {e}")
            self._is_connected = False
            self._circuit_breaker.on_failure()
            return False

    async def warm_cache(self, warming_functions: List[Callable]) -> int:
        """Warm the cache with predefined data."""
        if not self._enabled or not self._is_connected:
            return 0

        warmed_count = 0
        for func in warming_functions:
            try:
                await func(self)
                warmed_count += 1
                logger.info(f"Successfully warmed cache with function: {func.__name__}")
            except Exception as e:
                logger.error(f"Failed to warm cache with function {func.__name__}: {e}")

        return warmed_count


# Global enhanced cache manager instance - use function to avoid import-time execution
def get_enhanced_cache_manager():
    """Get the global enhanced cache manager instance."""
    if not hasattr(get_enhanced_cache_manager, "_instance"):
        get_enhanced_cache_manager._instance = EnhancedCacheManager()
    return get_enhanced_cache_manager._instance


# Convenience functions for common cache operations


async def enhanced_cache_get(prefix: str, key: str) -> Optional[Any]:
    """Get a value from enhanced cache."""
    cache_manager = get_enhanced_cache_manager()
    return await cache_manager.get(prefix, key)


async def enhanced_cache_set(
    prefix: str, key: str, value: Any, ttl: Optional[int] = None
) -> bool:
    """Set a value in enhanced cache."""
    cache_manager = get_enhanced_cache_manager()
    return await cache_manager.set(prefix, key, value, ttl)


async def enhanced_cache_mget(prefix: str, keys: List[str]) -> List[Optional[Any]]:
    """Get multiple values from enhanced cache."""
    cache_manager = get_enhanced_cache_manager()
    return await cache_manager.mget(prefix, keys)


async def enhanced_cache_mset(
    prefix: str, data: Dict[str, Any], ttl: Optional[int] = None
) -> bool:
    """Set multiple values in enhanced cache."""
    cache_manager = get_enhanced_cache_manager()
    return await cache_manager.mset(prefix, data, ttl)


async def enhanced_cache_delete(prefix: str, key: str) -> bool:
    """Delete a value from enhanced cache."""
    cache_manager = get_enhanced_cache_manager()
    return await cache_manager.delete(prefix, key)


async def enhanced_cache_exists(prefix: str, key: str) -> bool:
    """Check if a key exists in enhanced cache."""
    cache_manager = get_enhanced_cache_manager()
    return await cache_manager.exists(prefix, key)


async def enhanced_cache_clear_prefix(prefix: str, pattern: str = None) -> int:
    """Clear all keys with a specific prefix in enhanced cache."""
    cache_manager = get_enhanced_cache_manager()
    return await cache_manager.clear_prefix(prefix, pattern)


# Enhanced caching decorators
def enhanced_cache_query(prefix: str = "db_query", ttl: Optional[int] = None):
    """Enhanced decorator to cache database query results."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            # Try to get from cache first
            cached_result = await enhanced_cache_get(prefix, cache_key)
            if cached_result is not None:
                return cached_result

            # Execute the function and cache the result
            result = await func(*args, **kwargs)
            await enhanced_cache_set(prefix, cache_key, result, ttl)
            return result

        return wrapper

    return decorator


def enhanced_cache_api_response(
    prefix: str = "api_response", ttl: Optional[int] = None
):
    """Enhanced decorator to cache API response results."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            # Try to get from cache first
            cached_result = await enhanced_cache_get(prefix, cache_key)
            if cached_result is not None:
                return cached_result

            # Execute the function and cache the result
            result = await func(*args, **kwargs)
            await enhanced_cache_set(prefix, cache_key, result, ttl)
            return result

        return wrapper

    return decorator


# Cache warming functions
async def warm_user_data_cache(cache_manager: EnhancedCacheManager):
    """Warm cache with frequently accessed user data."""
    # This would typically load user data from database
    # For now, we'll just log the warming attempt
    logger.info("Warming user data cache")


async def warm_game_data_cache(cache_manager: EnhancedCacheManager):
    """Warm cache with frequently accessed game data."""
    # This would typically load game data from database
    # For now, we'll just log the warming attempt
    logger.info("Warming game data cache")


async def warm_team_data_cache(cache_manager: EnhancedCacheManager):
    """Warm cache with frequently accessed team data."""
    # This would typically load team data from database
    # For now, we'll just log the warming attempt
    logger.info("Warming team data cache")
