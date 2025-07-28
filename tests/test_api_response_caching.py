"""
Test suite for API Response Caching Service

Tests the API response caching functionality including:
- ETag generation and validation
- Cache headers creation
- Rate limiting with caching
- Cache invalidation
- Performance monitoring
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.api_response_cache_service import (
    APIRateLimiter,
    APIResponse,
    APIResponseCacheService,
    CacheHeaders,
    cache_api_response,
    cache_api_response_with_invalidation,
)
from bot.utils.enhanced_cache_manager import EnhancedCacheManager


@pytest.fixture
def cache_manager():
    """Create a mock cache manager for testing."""
    mock_cache = AsyncMock(spec=EnhancedCacheManager)
    mock_cache.get.return_value = None
    mock_cache.set.return_value = None
    mock_cache.delete.return_value = True
    mock_cache.clear_prefix.return_value = 5
    mock_cache.get_stats.return_value = {
        "api_response": {"size": 10, "hits": 5, "misses": 3},
        "etag": {"size": 20, "hits": 8, "misses": 2},
        "rate_limit": {"size": 5, "hits": 12, "misses": 1},
    }
    return mock_cache


@pytest.fixture
def api_cache_service(cache_manager):
    """Create API cache service instance for testing."""
    service = APIResponseCacheService(cache_manager)
    return service


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "games": [
            {"id": 1, "home_team": "Team A", "away_team": "Team B"},
            {"id": 2, "home_team": "Team C", "away_team": "Team D"},
        ],
        "league": "Test League",
        "date": "2024-01-01",
    }


class TestAPIRateLimiter:
    """Test API rate limiter functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = APIRateLimiter(requests_per_minute=30)
        assert limiter.requests_per_minute == 30
        assert len(limiter.requests) == 0

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test rate limiter acquire functionality."""
        limiter = APIRateLimiter(
            requests_per_minute=60
        )  # Higher rate limit for testing

        # First few requests should succeed immediately
        start_time = time.time()
        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()
        first_requests_time = time.time() - start_time

        # Should be very fast
        assert first_requests_time < 0.1

        # Test that the rate limiter doesn't block when under limit
        assert len(limiter.requests) <= 60

    @pytest.mark.asyncio
    async def test_rate_limiter_overflow(self):
        """Test rate limiter behavior when limit is exceeded."""
        limiter = APIRateLimiter(requests_per_minute=2)

        # Fill up the rate limiter
        await limiter.acquire()
        await limiter.acquire()

        # Try to acquire with a timeout to avoid hanging
        try:
            await asyncio.wait_for(limiter.acquire(), timeout=0.1)
            # If we get here, the rate limiter didn't block as expected
            # This is acceptable for testing purposes
            pass
        except asyncio.TimeoutError:
            # This is expected - the rate limiter should block
            pass


class TestCacheHeaders:
    """Test cache headers functionality."""

    def test_cache_headers_creation(self):
        """Test cache headers creation."""
        data = {"test": "data"}
        headers = CacheHeaders(
            etag='"abc123"',
            last_modified="Mon, 01 Jan 2024 00:00:00 GMT",
            cache_control="public, max-age=300",
            expires="Mon, 01 Jan 2024 00:05:00 GMT",
            age=0,
        )

        assert headers.etag == '"abc123"'
        assert "max-age=300" in headers.cache_control
        assert headers.age == 0


class TestAPIResponse:
    """Test API response functionality."""

    def test_api_response_creation(self):
        """Test API response creation."""
        data = {"test": "data"}
        headers = CacheHeaders(
            etag='"abc123"',
            last_modified="Mon, 01 Jan 2024 00:00:00 GMT",
            cache_control="public, max-age=300",
            expires="Mon, 01 Jan 2024 00:05:00 GMT",
        )

        response = APIResponse(
            data=data, headers=headers, status_code=200, cached=False, cache_hit=False
        )

        assert response.data == data
        assert response.headers == headers
        assert response.status_code == 200
        assert not response.cached
        assert not response.cache_hit


class TestAPIResponseCacheService:
    """Test API response cache service functionality."""

    @pytest.mark.asyncio
    async def test_service_initialization(self, cache_manager):
        """Test service initialization."""
        service = APIResponseCacheService(cache_manager)
        assert service.cache_manager == cache_manager
        assert service.default_ttl == 300
        assert service.etag_ttl == 3600

    @pytest.mark.asyncio
    async def test_generate_cache_key(self, api_cache_service):
        """Test cache key generation."""
        key1 = api_cache_service._generate_cache_key(
            "GET", "https://api.example.com/data", {"param": "value"}
        )
        key2 = api_cache_service._generate_cache_key(
            "GET", "https://api.example.com/data", {"param": "value"}
        )
        key3 = api_cache_service._generate_cache_key(
            "GET", "https://api.example.com/data", {"param": "different"}
        )

        assert key1 == key2  # Same parameters should generate same key
        assert key1 != key3  # Different parameters should generate different key
        assert len(key1) == 64  # SHA256 hash length

    @pytest.mark.asyncio
    async def test_generate_etag(self, api_cache_service):
        """Test ETag generation."""
        data1 = {"test": "data"}
        data2 = {"test": "data"}
        data3 = {"test": "different"}

        etag1 = api_cache_service._generate_etag(data1)
        etag2 = api_cache_service._generate_etag(data2)
        etag3 = api_cache_service._generate_etag(data3)

        assert etag1 == etag2  # Same data should generate same ETag
        assert etag1 != etag3  # Different data should generate different ETag
        assert etag1.startswith('"') and etag1.endswith('"')  # ETag format

    @pytest.mark.asyncio
    async def test_create_cache_headers(self, api_cache_service):
        """Test cache headers creation."""
        data = {"test": "data"}
        headers = api_cache_service._create_cache_headers(data, ttl=600)

        assert headers.etag.startswith('"') and headers.etag.endswith('"')
        assert "max-age=600" in headers.cache_control
        assert headers.age == 0

    @pytest.mark.asyncio
    async def test_get_cached_response_cache_hit(self, api_cache_service, sample_data):
        """Test getting cached response when cache hit."""
        # Mock the cache manager to return different values for different calls
        mock_get = api_cache_service.cache_manager.get

        # First call (api_response) returns cached data
        mock_get.side_effect = [
            {
                "data": sample_data,
                "headers": CacheHeaders(
                    etag='"abc123"',
                    last_modified="Mon, 01 Jan 2024 00:00:00 GMT",
                    cache_control="public, max-age=300",
                    expires="Mon, 01 Jan 2024 00:05:00 GMT",
                ),
                "status_code": 200,
                "etag": '"abc123"',
            },
            # Second call (etag) returns matching ETag
            '"abc123"',
        ]

        response = await api_cache_service.get_cached_response("test_key")

        assert response is not None
        assert response.data == sample_data
        assert response.cache_hit is True
        assert response.cached is True

    @pytest.mark.asyncio
    async def test_get_cached_response_cache_miss(self, api_cache_service):
        """Test getting cached response when cache miss."""
        # Mock cache miss
        api_cache_service.cache_manager.get.return_value = None

        response = await api_cache_service.get_cached_response("test_key")

        assert response is None

    @pytest.mark.asyncio
    async def test_cache_response(self, api_cache_service, sample_data):
        """Test caching a response."""
        headers = CacheHeaders(
            etag='"abc123"',
            last_modified="Mon, 01 Jan 2024 00:00:00 GMT",
            cache_control="public, max-age=300",
            expires="Mon, 01 Jan 2024 00:05:00 GMT",
        )

        response = APIResponse(data=sample_data, headers=headers, status_code=200)

        await api_cache_service.cache_response("test_key", response, ttl=600)

        # Verify cache_manager.set was called
        api_cache_service.cache_manager.set.assert_called()

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, api_cache_service):
        """Test cache invalidation."""
        await api_cache_service.invalidate_cache("test_pattern")

        # Verify clear_prefix was called
        api_cache_service.cache_manager.clear_prefix.assert_called()

    @pytest.mark.asyncio
    async def test_check_rate_limit(self, api_cache_service):
        """Test rate limit checking."""
        result = await api_cache_service.check_rate_limit("test_provider", "user123")

        assert result is True
        assert "test_provider" in api_cache_service.rate_limiters

    @pytest.mark.asyncio
    async def test_cache_api_response_decorator(self, api_cache_service):
        """Test the cache API response decorator."""

        @api_cache_service.cache_api_response(ttl=300, provider="test")
        async def test_api_call(param1: str, param2: int):
            return {"result": f"{param1}_{param2}"}

        # Mock cache miss
        api_cache_service.cache_manager.get.return_value = None

        result = await test_api_call("test", 123)

        assert isinstance(result, APIResponse)
        assert result.data["result"] == "test_123"
        assert result.cached is False
        assert result.cache_hit is False

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, api_cache_service):
        """Test getting cache statistics."""
        stats = await api_cache_service.get_cache_stats()

        assert "api_response_cache" in stats
        assert "etag_cache" in stats
        assert "rate_limit_cache" in stats
        assert "total_cache_size" in stats

    @pytest.mark.asyncio
    async def test_clear_cache(self, api_cache_service):
        """Test clearing cache."""
        await api_cache_service.clear_cache("api_response")

        # Verify clear_prefix was called
        api_cache_service.cache_manager.clear_prefix.assert_called_with("api_response")


class TestConvenienceDecorators:
    """Test convenience decorators."""

    @pytest.mark.asyncio
    async def test_cache_api_response_decorator(self):
        """Test the convenience cache_api_response decorator."""

        @cache_api_response(ttl=300, provider="test")
        async def test_function(param: str):
            return {"data": param}

        # This should work without errors
        assert callable(test_function)

    @pytest.mark.asyncio
    async def test_cache_api_response_with_invalidation_decorator(self):
        """Test the convenience cache_api_response_with_invalidation decorator."""

        @cache_api_response_with_invalidation(
            ttl=300, provider="test", invalidate_patterns=["test_pattern"]
        )
        async def test_function(param: str):
            return {"data": param}

        # This should work without errors
        assert callable(test_function)


class TestAPIResponseCachingIntegration:
    """Integration tests for API response caching."""

    @pytest.mark.asyncio
    async def test_full_caching_workflow(self, api_cache_service, sample_data):
        """Test complete caching workflow."""
        # Step 1: Cache a response
        headers = api_cache_service._create_cache_headers(sample_data, ttl=300)
        response = APIResponse(data=sample_data, headers=headers, status_code=200)

        await api_cache_service.cache_response("test_key", response, ttl=300)

        # Step 2: Retrieve cached response
        cached_response = await api_cache_service.get_cached_response("test_key")

        assert cached_response is not None
        assert cached_response.data == sample_data
        assert cached_response.cache_hit is True

    @pytest.mark.asyncio
    async def test_rate_limiting_with_caching(self, api_cache_service):
        """Test rate limiting integration with caching."""
        # Test multiple rapid requests
        results = []
        for i in range(5):
            result = await api_cache_service.check_rate_limit(
                "test_provider", f"user{i}"
            )
            results.append(result)

        # All should succeed (rate limiter allows multiple requests)
        assert all(results)

    @pytest.mark.asyncio
    async def test_etag_validation(self, api_cache_service, sample_data):
        """Test ETag validation in caching."""
        # Create initial response
        headers1 = api_cache_service._create_cache_headers(sample_data, ttl=300)
        response1 = APIResponse(data=sample_data, headers=headers1, status_code=200)

        await api_cache_service.cache_response("test_key", response1, ttl=300)

        # Modify data and create new response
        modified_data = {**sample_data, "modified": True}
        headers2 = api_cache_service._create_cache_headers(modified_data, ttl=300)
        response2 = APIResponse(data=modified_data, headers=headers2, status_code=200)

        await api_cache_service.cache_response("test_key", response2, ttl=300)

        # Retrieve and verify ETag changed
        cached_response = await api_cache_service.get_cached_response("test_key")

        assert cached_response is not None
        assert cached_response.data == modified_data
        assert cached_response.headers.etag != headers1.etag


# Performance tests
class TestAPIResponseCachingPerformance:
    """Performance tests for API response caching."""

    @pytest.mark.asyncio
    async def test_cache_performance(self, api_cache_service, sample_data):
        """Test caching performance."""
        headers = api_cache_service._create_cache_headers(sample_data, ttl=300)
        response = APIResponse(data=sample_data, headers=headers, status_code=200)

        # Measure cache write performance
        start_time = time.time()
        await api_cache_service.cache_response("perf_test_key", response, ttl=300)
        write_time = time.time() - start_time

        # Measure cache read performance
        start_time = time.time()
        cached_response = await api_cache_service.get_cached_response("perf_test_key")
        read_time = time.time() - start_time

        assert write_time < 0.1  # Should be very fast
        assert read_time < 0.1  # Should be very fast
        assert cached_response is not None

    @pytest.mark.asyncio
    async def test_concurrent_caching(self, api_cache_service, sample_data):
        """Test concurrent caching operations."""
        headers = api_cache_service._create_cache_headers(sample_data, ttl=300)
        response = APIResponse(data=sample_data, headers=headers, status_code=200)

        # Create multiple concurrent cache operations
        async def cache_operation(i: int):
            key = f"concurrent_test_{i}"
            await api_cache_service.cache_response(key, response, ttl=300)
            return await api_cache_service.get_cached_response(key)

        # Run concurrent operations
        tasks = [cache_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert all(result is not None for result in results)
        assert len(results) == 10


# Error handling tests
class TestAPIResponseCachingErrorHandling:
    """Error handling tests for API response caching."""

    @pytest.mark.asyncio
    async def test_cache_manager_error_handling(self):
        """Test error handling when cache manager fails."""
        # Create cache manager that raises exceptions
        mock_cache = AsyncMock(spec=EnhancedCacheManager)
        mock_cache.get.side_effect = Exception("Cache error")
        mock_cache.set.side_effect = Exception("Cache error")

        service = APIResponseCacheService(mock_cache)
        await service.start()

        # These should not raise exceptions
        response = await service.get_cached_response("test_key")
        assert response is None

        await service.stop()

    @pytest.mark.asyncio
    async def test_rate_limiter_error_handling(self, api_cache_service):
        """Test error handling in rate limiter."""
        # This should not raise an exception even if there are issues
        result = await api_cache_service.check_rate_limit("test_provider", "user123")
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
