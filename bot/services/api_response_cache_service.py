"""
API Response Caching Service for DBSBM System

This service provides comprehensive API response caching with:
- ETag support for conditional requests
- Cache headers for HTTP responses
- Intelligent cache invalidation
- Rate limiting with caching
- Performance monitoring
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from functools import wraps

from bot.utils.enhanced_cache_manager import EnhancedCacheManager

logger = logging.getLogger(__name__)


@dataclass
class CacheHeaders:
    """Cache headers for API responses."""

    etag: str
    last_modified: str
    cache_control: str
    expires: str
    age: int = 0


@dataclass
class APIResponse:
    """API response with cache metadata."""

    data: Any
    headers: CacheHeaders
    status_code: int = 200
    cached: bool = False
    cache_hit: bool = False


class APIRateLimiter:
    """Rate limiter for API requests with caching."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire rate limit permission."""
        async with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req for req in self.requests if now - req < 60]

            if len(self.requests) >= self.requests_per_minute:
                # Wait until we can make another request
                sleep_time = 60 - (now - self.requests[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self.requests = self.requests[1:]

            self.requests.append(now)


class APIResponseCacheService:
    """Service for caching API responses with advanced features."""

    def __init__(self, cache_manager: Optional[EnhancedCacheManager] = None):
        self.cache_manager = cache_manager or EnhancedCacheManager()
        self.rate_limiters: Dict[str, APIRateLimiter] = {}
        self.default_ttl = 300  # 5 minutes
        self.etag_ttl = 3600  # 1 hour for ETags

        # Cache configuration
        self.cache_config = {
            "api_response": {"ttl": 300, "prefix": "api_resp:", "max_size": 1000},
            "etag": {"ttl": 3600, "prefix": "api_etag:", "max_size": 5000},
            "rate_limit": {"ttl": 60, "prefix": "api_rate:", "max_size": 100},
        }

    async def start(self):
        """Start the cache service."""
        await self.cache_manager.connect()
        logger.info("API Response Cache Service started")

    async def stop(self):
        """Stop the cache service."""
        await self.cache_manager.disconnect()
        logger.info("API Response Cache Service stopped")

    def _generate_cache_key(
        self, method: str, url: str, params: Dict = None, headers: Dict = None
    ) -> str:
        """Generate a unique cache key for an API request."""
        # Create a hash of the request components
        request_data = {
            "method": method,
            "url": url,
            "params": sorted(params.items()) if params else {},
            "headers": {
                k: v
                for k, v in (headers or {}).items()
                if k.lower() not in ["authorization", "x-api-key"]
            },
        }

        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(request_str.encode()).hexdigest()

    def _generate_etag(self, data: Any) -> str:
        """Generate ETag for response data."""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        return f'"{hashlib.md5(data_str.encode()).hexdigest()}"'

    def _create_cache_headers(self, data: Any, ttl: int = None) -> CacheHeaders:
        """Create cache headers for a response."""
        etag = self._generate_etag(data)
        now = datetime.utcnow()
        expires = now + timedelta(seconds=ttl or self.default_ttl)

        return CacheHeaders(
            etag=etag,
            last_modified=now.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            cache_control=f"public, max-age={ttl or self.default_ttl}",
            expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            age=0,
        )

    async def get_cached_response(self, cache_key: str) -> Optional[APIResponse]:
        """Get cached API response."""
        try:
            cached_data = await self.cache_manager.get("api_response", cache_key)
            if cached_data:
                # Check if ETag is still valid
                etag_key = f"etag:{cache_key}"
                cached_etag = await self.cache_manager.get("etag", etag_key)

                if cached_etag and cached_etag == cached_data.get("etag"):
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return APIResponse(
                        data=cached_data["data"],
                        headers=cached_data["headers"],
                        status_code=cached_data["status_code"],
                        cached=True,
                        cache_hit=True,
                    )
                else:
                    # ETag mismatch, invalidate cache
                    await self.invalidate_cache(cache_key)

            return None
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            return None

    async def cache_response(
        self, cache_key: str, response: APIResponse, ttl: int = None
    ) -> None:
        """Cache an API response."""
        try:
            cache_data = {
                "data": response.data,
                "headers": response.headers,
                "status_code": response.status_code,
                "cached_at": datetime.utcnow().isoformat(),
            }

            # Cache the response
            await self.cache_manager.set(
                "api_response", cache_key, cache_data, ttl or self.default_ttl
            )

            # Cache the ETag separately
            etag_key = f"etag:{cache_key}"
            await self.cache_manager.set(
                "etag", etag_key, response.headers.etag, self.etag_ttl
            )

            logger.debug(f"Cached response for key: {cache_key}")
        except Exception as e:
            logger.error(f"Error caching response: {e}")

    async def invalidate_cache(self, pattern: str) -> None:
        """Invalidate cache entries matching a pattern."""
        try:
            # Use clear_prefix instead of delete_pattern
            await self.cache_manager.clear_prefix("api_response")
            await self.cache_manager.clear_prefix("etag")
            logger.info(f"Invalidated cache pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

    async def check_rate_limit(
        self, provider: str, user_id: Optional[str] = None
    ) -> bool:
        """Check if rate limit allows the request."""
        try:
            # Get or create rate limiter for provider
            if provider not in self.rate_limiters:
                self.rate_limiters[provider] = APIRateLimiter()

            await self.rate_limiters[provider].acquire()

            # Cache rate limit info
            rate_key = f"{provider}:{user_id or 'anonymous'}"
            await self.cache_manager.set(
                "rate_limit", rate_key, {"last_request": time.time()}, 60
            )

            return True
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False

    def cache_api_response(
        self,
        ttl: Optional[int] = None,
        provider: Optional[str] = None,
        invalidate_patterns: Optional[List[str]] = None,
    ):
        """Decorator for caching API responses."""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function and arguments
                func_name = func.__name__
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = hashlib.sha256(
                    f"{func_name}:{args_str}".encode()
                ).hexdigest()

                # Check cache first
                cached_response = await self.get_cached_response(cache_key)
                if cached_response:
                    return cached_response

                # Check rate limit if provider specified
                if provider:
                    rate_allowed = await self.check_rate_limit(provider)
                    if not rate_allowed:
                        raise Exception("Rate limit exceeded")

                # Execute the function
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Create API response with cache headers
                    headers = self._create_cache_headers(result, ttl)
                    api_response = APIResponse(
                        data=result,
                        headers=headers,
                        status_code=200,
                        cached=False,
                        cache_hit=False,
                    )

                    # Cache the response
                    await self.cache_response(cache_key, api_response, ttl)

                    # Invalidate related cache patterns if specified
                    if invalidate_patterns:
                        for pattern in invalidate_patterns:
                            await self.invalidate_cache(pattern)

                    logger.info(
                        f"API response cached for {func_name} (execution time: {execution_time:.2f}s)"
                    )
                    return api_response

                except Exception as e:
                    logger.error(f"API request failed for {func_name}: {e}")
                    raise

            return wrapper

        return decorator

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = await self.cache_manager.get_stats()
            return {
                "api_response_cache": stats.get("api_response", {}),
                "etag_cache": stats.get("etag", {}),
                "rate_limit_cache": stats.get("rate_limit", {}),
                "total_cache_size": sum(
                    stats.get(prefix, {}).get("size", 0)
                    for prefix in ["api_response", "etag", "rate_limit"]
                ),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    async def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """Clear cache entries."""
        try:
            if cache_type:
                await self.cache_manager.clear_prefix(cache_type)
                logger.info(f"Cleared {cache_type} cache")
            else:
                # Clear all API-related caches
                for cache_type in ["api_response", "etag", "rate_limit"]:
                    await self.cache_manager.clear_prefix(cache_type)
                logger.info("Cleared all API response caches")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    async def warm_cache(self, warmup_functions: List[Tuple[callable, Dict]]) -> None:
        """Warm up the cache with common API calls."""
        logger.info("Starting cache warming...")

        for func, params in warmup_functions:
            try:
                await func(**params)
                logger.debug(f"Warmed cache for {func.__name__}")
            except Exception as e:
                logger.warning(f"Failed to warm cache for {func.__name__}: {e}")

        logger.info("Cache warming completed")


# Global instance for easy access
api_cache_service = APIResponseCacheService()

# Convenience decorators


def cache_api_response(ttl: Optional[int] = None, provider: Optional[str] = None):
    """Convenience decorator for caching API responses."""
    return api_cache_service.cache_api_response(ttl=ttl, provider=provider)


def cache_api_response_with_invalidation(
    ttl: Optional[int] = None,
    provider: Optional[str] = None,
    invalidate_patterns: Optional[List[str]] = None,
):
    """Convenience decorator for caching API responses with invalidation."""
    return api_cache_service.cache_api_response(
        ttl=ttl, provider=provider, invalidate_patterns=invalidate_patterns
    )
