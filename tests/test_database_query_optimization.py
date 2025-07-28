"""Test database query optimization features."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.data.db_manager import DatabaseManager
from bot.services.database_query_service import (
    DatabaseQueryService,
    cache_query,
    monitor_query_performance,
)
from bot.utils.enhanced_cache_manager import EnhancedCacheManager

pytestmark = pytest.mark.asyncio


class TestDatabaseQueryOptimization:
    """Test database query optimization features."""

    @pytest.fixture
    async def db_manager(self):
        """Create a database manager instance for testing."""
        manager = DatabaseManager()
        # Mock the connection pool to avoid actual database connections
        with patch("aiomysql.create_pool") as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            yield manager
        await manager.close()

    @pytest.fixture
    async def query_service(self):
        """Create a query service instance for testing."""
        service = DatabaseQueryService()
        await service.start()
        yield service
        await service.stop()

    @pytest.fixture
    def mock_cache_manager(self):
        """Create a mock cache manager."""
        cache_manager = MagicMock(spec=EnhancedCacheManager)
        cache_manager.get = AsyncMock(return_value=None)
        cache_manager.set = AsyncMock()
        cache_manager.get_stats = AsyncMock(
            return_value={"hits": 10, "misses": 5, "size": 100, "ttl": 600}
        )
        cache_manager.clear_prefix = AsyncMock()
        return cache_manager

    async def test_query_caching_enabled(self, db_manager):
        """Test that query caching is properly configured."""
        assert db_manager.enable_query_cache is True
        assert db_manager.default_cache_ttl == 600
        assert db_manager.query_cache_prefix == "db_query"

    async def test_cache_key_generation(self, db_manager):
        """Test cache key generation for queries."""
        query = "SELECT * FROM users WHERE id = %s"
        args = (123,)

        cache_key = db_manager._generate_cache_key(query, args)
        assert cache_key.startswith("db_query:")
        assert len(cache_key) > 20  # Should be a reasonable length

    async def test_should_cache_query_logic(self, db_manager):
        """Test query caching logic."""
        # Should cache SELECT queries
        assert db_manager._should_cache_query("SELECT * FROM users") is True
        assert db_manager._should_cache_query("SELECT COUNT(*) FROM games") is True

        # Should not cache write operations
        assert (
            db_manager._should_cache_query("INSERT INTO users VALUES (1, 'test')")
            is False
        )
        assert db_manager._should_cache_query("UPDATE users SET name = 'test'") is False
        assert db_manager._should_cache_query("DELETE FROM users WHERE id = 1") is False

        # Should not cache queries with time functions
        assert db_manager._should_cache_query("SELECT NOW()") is False
        assert (
            db_manager._should_cache_query(
                "SELECT * FROM logs WHERE created_at > CURRENT_TIMESTAMP"
            )
            is False
        )

    async def test_query_service_cache_decorator(
        self, query_service, mock_cache_manager
    ):
        """Test the cache query decorator."""
        query_service.cache_manager = mock_cache_manager

        @query_service.cache_query(ttl=300)
        async def test_query(user_id: int):
            return {"user_id": user_id, "name": "Test User"}

        # First call - should cache the result
        result = await test_query(123)
        assert result == {"user_id": 123, "name": "Test User"}
        mock_cache_manager.set.assert_called_once()

        # Second call - should return cached result
        mock_cache_manager.get.return_value = {"user_id": 123, "name": "Cached User"}
        result = await test_query(123)
        assert result == {"user_id": 123, "name": "Cached User"}

    async def test_query_service_performance_monitoring(self, query_service):
        """Test query performance monitoring."""

        @query_service.monitor_query_performance(threshold=0.1)
        async def slow_query():
            await asyncio.sleep(0.2)  # Simulate slow query
            return {"result": "slow"}

        # This should trigger a slow query warning
        with patch("logging.Logger.warning") as mock_warning:
            result = await slow_query()
            assert result == {"result": "slow"}
            mock_warning.assert_called()

    async def test_query_service_stats(self, query_service):
        """Test query service statistics."""

        # Execute some test queries
        @query_service.monitor_query_performance()
        async def test_query():
            await asyncio.sleep(0.01)
            return [1, 2, 3]

        await test_query()
        await test_query()

        stats = await query_service.get_query_stats()
        assert stats["total_queries"] == 2
        assert stats["successful_queries"] == 2
        assert stats["success_rate"] == 1.0
        assert "avg_execution_time" in stats

    async def test_database_manager_cache_integration(
        self, db_manager, mock_cache_manager
    ):
        """Test database manager cache integration."""
        db_manager.cache_manager = mock_cache_manager

        # Test fetch_one with cache
        query = "SELECT * FROM users WHERE id = %s"
        args = (123,)

        # Mock the pool and cursor
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"id": 123, "name": "Test User"}
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager._pool = mock_pool

        result = await db_manager.fetch_one(query, args)
        assert result == {"id": 123, "name": "Test User"}

        # Verify cache was set
        mock_cache_manager.set.assert_called()

    async def test_database_manager_pool_stats(self, db_manager):
        """Test database manager pool statistics."""
        # Mock the pool
        mock_pool = MagicMock()
        mock_pool.size = 5
        mock_pool.freesize = 3
        db_manager._pool = mock_pool

        stats = await db_manager.get_pool_stats()
        assert stats["pool_status"] == "active"
        assert stats["pool_size"] == 5
        assert stats["pool_free_size"] == 3
        assert stats["pool_min_size"] == db_manager.pool_min_size
        assert stats["pool_max_size"] == db_manager.pool_max_size

    async def test_database_manager_cache_stats(self, db_manager, mock_cache_manager):
        """Test database manager cache statistics."""
        db_manager.cache_manager = mock_cache_manager

        stats = await db_manager.get_cache_stats()
        assert stats["cache_hits"] == 10
        assert stats["cache_misses"] == 5
        assert stats["cache_size"] == 100
        assert stats["query_cache_enabled"] is True
        assert stats["default_cache_ttl"] == 600

    async def test_slow_query_detection(self, db_manager):
        """Test slow query detection."""
        # Mock the pool and cursor
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager._pool = mock_pool

        # Mock time to simulate slow query
        with patch("time.time") as mock_time:
            mock_time.side_effect = [0.0, 2.0]  # 2 second query
            with patch("logging.Logger.warning") as mock_warning:
                await db_manager.fetch_all("SELECT * FROM large_table")
                mock_warning.assert_called()

    async def test_cache_invalidation(self, db_manager, mock_cache_manager):
        """Test cache invalidation on write operations."""
        db_manager.cache_manager = mock_cache_manager

        # Mock the pool and cursor
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager._pool = mock_pool

        # Execute a write operation
        await db_manager.execute("UPDATE users SET name = 'test' WHERE id = 1")

        # Verify cache was invalidated
        mock_cache_manager.clear_prefix.assert_called_with("database", "db_query")

    async def test_connection_pool_optimization(self, db_manager):
        """Test connection pool optimization settings."""
        assert db_manager.pool_min_size >= 1
        assert db_manager.pool_max_size >= db_manager.pool_min_size
        assert db_manager.pool_max_overflow >= 0
        assert db_manager.pool_timeout > 0
        assert db_manager.connect_timeout > 0

    async def test_query_service_configuration(self, query_service):
        """Test query service configuration."""
        # Test default configuration
        assert query_service.config.enabled is True
        assert query_service.config.ttl == 600
        assert query_service.config.slow_query_threshold == 1.0

        # Test configuration update
        query_service.update_config(ttl=300, slow_query_threshold=0.5)
        assert query_service.config.ttl == 300
        assert query_service.config.slow_query_threshold == 0.5

    async def test_convenience_decorators(self):
        """Test convenience decorators."""

        # Test cache_query decorator
        @cache_query(ttl=300)
        async def test_cached_function():
            return "cached_result"

        # Test monitor_query_performance decorator
        @monitor_query_performance(threshold=0.1)
        async def test_monitored_function():
            return "monitored_result"

        # These should not raise exceptions
        assert await test_cached_function() == "cached_result"
        assert await test_monitored_function() == "monitored_result"


class TestDatabaseQueryPerformance:
    """Test database query performance under load."""

    async def test_concurrent_query_execution(self, query_service):
        """Test concurrent query execution performance."""

        @query_service.cache_query(ttl=60)
        async def concurrent_query(query_id: int):
            await asyncio.sleep(0.01)  # Simulate database query
            return {"query_id": query_id, "result": f"result_{query_id}"}

        # Execute multiple queries concurrently
        tasks = [concurrent_query(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for i, result in enumerate(results):
            assert result["query_id"] == i
            assert result["result"] == f"result_{i}"

    async def test_cache_hit_performance(self, query_service, mock_cache_manager):
        """Test cache hit performance."""
        query_service.cache_manager = mock_cache_manager

        @query_service.cache_query(ttl=60)
        async def cached_query():
            await asyncio.sleep(0.1)  # Simulate slow query
            return "expensive_result"

        # First call - should be slow
        start_time = time.time()
        result1 = await cached_query()
        first_call_time = time.time() - start_time

        # Second call - should be fast (cached)
        mock_cache_manager.get.return_value = "expensive_result"
        start_time = time.time()
        result2 = await cached_query()
        second_call_time = time.time() - start_time

        assert result1 == result2 == "expensive_result"
        assert second_call_time < first_call_time  # Cache hit should be faster

    async def test_query_service_memory_management(self, query_service):
        """Test query service memory management."""

        # Execute many queries to test history management
        @query_service.monitor_query_performance()
        async def memory_test_query():
            return "test_result"

        # Execute more queries than the max history size
        for i in range(query_service.max_history_size + 10):
            await memory_test_query()

        # Verify history size is maintained
        assert len(query_service.query_history) <= query_service.max_history_size

    async def test_error_handling(self, query_service):
        """Test error handling in query service."""

        @query_service.monitor_query_performance()
        async def failing_query():
            raise ValueError("Test error")

        # Should handle errors gracefully
        with pytest.raises(ValueError):
            await failing_query()

        # Check that error was recorded
        stats = await query_service.get_query_stats()
        assert stats["failed_queries"] > 0
        assert stats["success_rate"] < 1.0
