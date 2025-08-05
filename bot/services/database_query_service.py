"""Database query service with caching decorators and optimization utilities."""

import asyncio
import functools
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import record_query

logger = logging.getLogger(__name__)


@dataclass
class QueryCacheConfig:
    """Configuration for query caching."""

    enabled: bool = True
    ttl: int = 600  # 10 minutes
    key_prefix: str = "db_query"
    max_cache_size: int = 1000
    enable_slow_query_logging: bool = True
    slow_query_threshold: float = 1.0  # 1 second


@dataclass
class QueryPerformance:
    """Query performance metrics."""

    query: str
    execution_time: float
    cache_hit: bool
    rows_returned: int
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


class DatabaseQueryService:
    """Service for database query optimization and caching."""

    def __init__(self, cache_manager: Optional[EnhancedCacheManager] = None):
        """Initialize the database query service."""
        self.cache_manager = cache_manager or EnhancedCacheManager()
        self.config = QueryCacheConfig()
        self.query_history: List[QueryPerformance] = []
        self.max_history_size = 1000

    def cache_query(self, ttl: Optional[int] = None, key_prefix: Optional[str] = None):
        """Decorator for caching database query results."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.config.enabled:
                    return await func(*args, **kwargs)

                # Generate cache key
                cache_key = self._generate_cache_key(func, args, kwargs, key_prefix)

                # Try to get from cache
                cached_result = await self._get_cached_result(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache HIT for {func.__name__}")
                    return cached_result

                # Execute query and cache result
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Cache the result
                    if result is not None:
                        await self._set_cached_result(cache_key, result, ttl)

                    # Record performance
                    self._record_query_performance(
                        func.__name__,
                        execution_time,
                        False,
                        len(result) if isinstance(result, list) else 1,
                    )

                    # Log slow queries
                    if (
                        self.config.enable_slow_query_logging
                        and execution_time > self.config.slow_query_threshold
                    ):
                        logger.warning(
                            f"Slow query in {func.__name__}: {execution_time:.3f}s"
                        )

                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._record_query_performance(
                        func.__name__,
                        execution_time,
                        False,
                        0,
                        success=False,
                        error_message=str(e),
                    )
                    raise

            return wrapper

        return decorator

    def cache_query_with_invalidation(
        self, invalidation_patterns: List[str], ttl: Optional[int] = None
    ):
        """Decorator for caching queries with automatic cache invalidation."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.config.enabled:
                    return await func(*args, **kwargs)

                # Generate cache key
                cache_key = self._generate_cache_key(func, args, kwargs)

                # Try to get from cache
                cached_result = await self._get_cached_result(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache HIT for {func.__name__}")
                    return cached_result

                # Execute query and cache result
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Cache the result
                    if result is not None:
                        await self._set_cached_result(cache_key, result, ttl)

                    # Invalidate related cache entries
                    await self._invalidate_cache_patterns(invalidation_patterns)

                    # Record performance
                    self._record_query_performance(
                        func.__name__,
                        execution_time,
                        False,
                        len(result) if isinstance(result, list) else 1,
                    )

                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._record_query_performance(
                        func.__name__,
                        execution_time,
                        False,
                        0,
                        success=False,
                        error_message=str(e),
                    )
                    raise

            return wrapper

        return decorator

    def monitor_query_performance(self, threshold: Optional[float] = None):
        """Decorator for monitoring query performance."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Record performance
                    self._record_query_performance(
                        func.__name__,
                        execution_time,
                        False,
                        len(result) if isinstance(result, list) else 1,
                    )

                    # Log slow queries
                    threshold_to_use = threshold or self.config.slow_query_threshold
                    if execution_time > threshold_to_use:
                        logger.warning(
                            f"Slow query in {func.__name__}: {execution_time:.3f}s (threshold: {threshold_to_use}s)"
                        )

                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._record_query_performance(
                        func.__name__,
                        execution_time,
                        False,
                        0,
                        success=False,
                        error_message=str(e),
                    )
                    raise

            return wrapper

        return decorator

    def _generate_cache_key(
        self, func: Callable, args: Tuple, kwargs: Dict, prefix: Optional[str] = None
    ) -> str:
        """Generate a cache key for a function call."""
        # Create a string representation of the function call
        func_str = f"{func.__module__}.{func.__name__}"
        args_str = str(args) + str(sorted(kwargs.items()))

        # Create hash
        key_content = f"{func_str}:{args_str}"
        key_hash = hashlib.md5(key_content.encode()).hexdigest()

        key_prefix = prefix or self.config.key_prefix
        return f"{key_prefix}:{key_hash}"

    async def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result from the enhanced cache manager."""
        try:
            return await self.cache_manager.get("database_query", cache_key)
        except Exception as e:
            logger.warning(f"Error getting cached result: {e}")
            return None

    async def _set_cached_result(
        self, cache_key: str, result: Any, ttl: Optional[int] = None
    ) -> None:
        """Set cached result in the enhanced cache manager."""
        try:
            ttl = ttl or self.config.ttl
            await self.cache_manager.set("database_query", cache_key, result, ttl=ttl)
        except Exception as e:
            logger.warning(f"Error setting cached result: {e}")

    async def _invalidate_cache_patterns(self, patterns: List[str]) -> None:
        """Invalidate cache entries matching patterns."""
        for pattern in patterns:
            try:
                await self.cache_manager.clear_prefix("database_query", pattern)
                logger.debug(f"Invalidated cache pattern: {pattern}")
            except Exception as e:
                logger.warning(f"Error invalidating cache pattern {pattern}: {e}")

    def _record_query_performance(
        self,
        query_name: str,
        execution_time: float,
        cache_hit: bool,
        rows_returned: int,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Record query performance metrics."""
        performance = QueryPerformance(
            query=query_name,
            execution_time=execution_time,
            cache_hit=cache_hit,
            rows_returned=rows_returned,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message,
        )

        self.query_history.append(performance)

        # Maintain history size
        if len(self.query_history) > self.max_history_size:
            self.query_history = self.query_history[-self.max_history_size :]

        # Record in performance monitor
        record_query(
            query_name,
            execution_time,
            success=success,
            error_message=error_message,
            cache_hit=cache_hit,
        )

    async def get_query_stats(
        self, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get query performance statistics."""
        if not self.query_history:
            return {"total_queries": 0}

        # Filter by time window if specified
        if time_window:
            cutoff_time = datetime.now() - time_window
            recent_queries = [
                q for q in self.query_history if q.timestamp > cutoff_time
            ]
        else:
            recent_queries = self.query_history

        if not recent_queries:
            return {"total_queries": 0}

        # Calculate statistics
        total_queries = len(recent_queries)
        successful_queries = len([q for q in recent_queries if q.success])
        failed_queries = total_queries - successful_queries
        cache_hits = len([q for q in recent_queries if q.cache_hit])
        cache_miss_rate = (
            (total_queries - cache_hits) / total_queries if total_queries > 0 else 0
        )

        execution_times = [q.execution_time for q in recent_queries if q.success]
        avg_execution_time = (
            sum(execution_times) / len(execution_times) if execution_times else 0
        )
        max_execution_time = max(execution_times) if execution_times else 0
        min_execution_time = min(execution_times) if execution_times else 0

        slow_queries = len(
            [
                q
                for q in recent_queries
                if q.execution_time > self.config.slow_query_threshold
            ]
        )

        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": (
                successful_queries / total_queries if total_queries > 0 else 0
            ),
            "cache_hits": cache_hits,
            "cache_miss_rate": cache_miss_rate,
            "avg_execution_time": avg_execution_time,
            "max_execution_time": max_execution_time,
            "min_execution_time": min_execution_time,
            "slow_queries": slow_queries,
            "slow_query_threshold": self.config.slow_query_threshold,
        }

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = await self.cache_manager.get_stats()
            return {
                "cache_hits": stats.get("hits", 0),
                "cache_misses": stats.get("misses", 0),
                "cache_size": stats.get("size", 0),
                "cache_ttl": stats.get("ttl", 0),
                "query_cache_enabled": self.config.enabled,
                "default_cache_ttl": self.config.ttl,
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    async def clear_query_cache(self) -> None:
        """Clear all query cache."""
        try:
            await self.cache_manager.clear_prefix("database_query", "")
            logger.info("Query cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing query cache: {e}")

    async def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the slowest queries from history."""
        slow_queries = [
            q
            for q in self.query_history
            if q.execution_time > self.config.slow_query_threshold
        ]
        slow_queries.sort(key=lambda x: x.execution_time, reverse=True)

        return [
            {
                "query": q.query,
                "execution_time": q.execution_time,
                "timestamp": q.timestamp.isoformat(),
                "success": q.success,
                "rows_returned": q.rows_returned,
                "cache_hit": q.cache_hit,
            }
            for q in slow_queries[:limit]
        ]

    def update_config(self, **kwargs) -> None:
        """Update query service configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated query service config: {key} = {value}")

    async def start(self) -> None:
        """Start the database query service."""
        try:
            await self.cache_manager.connect()
            logger.info("Database query service started successfully")
        except Exception as e:
            logger.error(f"Error starting database query service: {e}")

    async def stop(self) -> None:
        """Stop the database query service."""
        try:
            await self.cache_manager.disconnect()
            logger.info("Database query service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping database query service: {e}")


# Global instance
query_service = DatabaseQueryService()


# Convenience decorators
def cache_query(ttl: Optional[int] = None, key_prefix: Optional[str] = None):
    """Convenience decorator for caching database queries."""
    return query_service.cache_query(ttl=ttl, key_prefix=key_prefix)


def cache_query_with_invalidation(
    invalidation_patterns: List[str], ttl: Optional[int] = None
):
    """Convenience decorator for caching queries with invalidation."""
    return query_service.cache_query_with_invalidation(invalidation_patterns, ttl=ttl)


def monitor_query_performance(threshold: Optional[float] = None):
    """Convenience decorator for monitoring query performance."""
    return query_service.monitor_query_performance(threshold=threshold)
