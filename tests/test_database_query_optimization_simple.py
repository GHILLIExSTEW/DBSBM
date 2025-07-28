"""Simple tests for database query optimization features."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.data.db_manager import DatabaseManager
from bot.services.database_query_service import DatabaseQueryService

pytestmark = pytest.mark.asyncio


class TestDatabaseQueryOptimizationSimple:
    """Simple tests for database query optimization."""

    def test_database_manager_initialization(self):
        """Test database manager initialization with enhanced cache."""
        with patch("bot.config.database_mysql.MYSQL_DB", "test_db"):
            with patch("bot.config.database_mysql.MYSQL_HOST", "localhost"):
                with patch("bot.config.database_mysql.MYSQL_USER", "test_user"):
                    with patch("bot.config.database_mysql.MYSQL_PASSWORD", "test_pass"):
                        with patch("bot.config.database_mysql.MYSQL_PORT", 3306):
                            db_manager = DatabaseManager()

                            # Test configuration
                            assert db_manager.enable_query_cache is True
                            assert db_manager.default_cache_ttl == 600
                            assert db_manager.query_cache_prefix == "db_query"
                            assert db_manager.slow_query_threshold == 1.0
                            assert db_manager.enable_query_logging is True

    def test_cache_key_generation(self):
        """Test cache key generation."""
        with patch("bot.config.database_mysql.MYSQL_DB", "test_db"):
            with patch("bot.config.database_mysql.MYSQL_HOST", "localhost"):
                with patch("bot.config.database_mysql.MYSQL_USER", "test_user"):
                    with patch("bot.config.database_mysql.MYSQL_PASSWORD", "test_pass"):
                        with patch("bot.config.database_mysql.MYSQL_PORT", 3306):
                            db_manager = DatabaseManager()

                            query = "SELECT * FROM users WHERE id = %s"
                            args = (123,)

                            cache_key = db_manager._generate_cache_key(query, args)
                            assert cache_key.startswith("db_query:")
                            assert len(cache_key) > 20

    def test_should_cache_query_logic(self):
        """Test query caching logic."""
        with patch("bot.config.database_mysql.MYSQL_DB", "test_db"):
            with patch("bot.config.database_mysql.MYSQL_HOST", "localhost"):
                with patch("bot.config.database_mysql.MYSQL_USER", "test_user"):
                    with patch("bot.config.database_mysql.MYSQL_PASSWORD", "test_pass"):
                        with patch("bot.config.database_mysql.MYSQL_PORT", 3306):
                            db_manager = DatabaseManager()

                            # Should cache SELECT queries
                            assert (
                                db_manager._should_cache_query("SELECT * FROM users")
                                is True
                            )
                            assert (
                                db_manager._should_cache_query(
                                    "SELECT COUNT(*) FROM games"
                                )
                                is True
                            )

                            # Should not cache write operations
                            assert (
                                db_manager._should_cache_query(
                                    "INSERT INTO users VALUES (1, 'test')"
                                )
                                is False
                            )
                            assert (
                                db_manager._should_cache_query(
                                    "UPDATE users SET name = 'test'"
                                )
                                is False
                            )
                            assert (
                                db_manager._should_cache_query(
                                    "DELETE FROM users WHERE id = 1"
                                )
                                is False
                            )

                            # Should not cache queries with time functions
                            assert (
                                db_manager._should_cache_query("SELECT NOW()") is False
                            )
                            assert (
                                db_manager._should_cache_query(
                                    "SELECT * FROM logs WHERE created_at > CURRENT_TIMESTAMP"
                                )
                                is False
                            )

    def test_query_service_initialization(self):
        """Test query service initialization."""
        query_service = DatabaseQueryService()

        # Test default configuration
        assert query_service.config.enabled is True
        assert query_service.config.ttl == 600
        assert query_service.config.slow_query_threshold == 1.0
        assert query_service.config.key_prefix == "db_query"

    def test_query_service_configuration_update(self):
        """Test query service configuration update."""
        query_service = DatabaseQueryService()

        # Update configuration
        query_service.update_config(ttl=300, slow_query_threshold=0.5)

        assert query_service.config.ttl == 300
        assert query_service.config.slow_query_threshold == 0.5

    def test_connection_pool_settings(self):
        """Test connection pool optimization settings."""
        with patch("bot.config.database_mysql.MYSQL_DB", "test_db"):
            with patch("bot.config.database_mysql.MYSQL_HOST", "localhost"):
                with patch("bot.config.database_mysql.MYSQL_USER", "test_user"):
                    with patch("bot.config.database_mysql.MYSQL_PASSWORD", "test_pass"):
                        with patch("bot.config.database_mysql.MYSQL_PORT", 3306):
                            db_manager = DatabaseManager()

                            # Test pool settings
                            assert db_manager.pool_min_size >= 1
                            assert db_manager.pool_max_size >= db_manager.pool_min_size
                            assert db_manager.pool_max_overflow >= 0
                            assert db_manager.pool_timeout > 0
                            assert db_manager.connect_timeout > 0

    async def test_query_service_cache_decorator_simple(self):
        """Test the cache query decorator with simple setup."""
        query_service = DatabaseQueryService()

        # Mock cache manager
        mock_cache_manager = MagicMock()
        mock_cache_manager.get = AsyncMock(return_value=None)
        mock_cache_manager.set = AsyncMock()
        query_service.cache_manager = mock_cache_manager

        @query_service.cache_query(ttl=300)
        async def test_query(user_id: int):
            return {"user_id": user_id, "name": "Test User"}

        # First call - should cache the result
        result = await test_query(123)
        assert result == {"user_id": 123, "name": "Test User"}
        mock_cache_manager.set.assert_called_once()

    async def test_query_service_performance_monitoring_simple(self):
        """Test query performance monitoring with simple setup."""
        query_service = DatabaseQueryService()

        @query_service.monitor_query_performance(threshold=0.1)
        async def test_query():
            return {"result": "test"}

        # This should not trigger a slow query warning
        with patch("logging.Logger.warning") as mock_warning:
            result = await test_query()
            assert result == {"result": "test"}
            mock_warning.assert_not_called()

    async def test_query_service_stats_simple(self):
        """Test query service statistics with simple setup."""
        query_service = DatabaseQueryService()

        @query_service.monitor_query_performance()
        async def test_query():
            return [1, 2, 3]

        await test_query()

        stats = await query_service.get_query_stats()
        assert stats["total_queries"] == 1
        assert stats["successful_queries"] == 1
        assert stats["success_rate"] == 1.0
        assert "avg_execution_time" in stats

    def test_convenience_decorators_import(self):
        """Test that convenience decorators can be imported."""
        from bot.services.database_query_service import (
            cache_query,
            monitor_query_performance,
        )

        # These should be callable
        assert callable(cache_query)
        assert callable(monitor_query_performance)

        # Test with default parameters
        decorator1 = cache_query()
        decorator2 = monitor_query_performance()

        assert callable(decorator1)
        assert callable(decorator2)

    def test_enhanced_cache_manager_integration(self):
        """Test that database manager uses enhanced cache manager."""
        with patch("bot.config.database_mysql.MYSQL_DB", "test_db"):
            with patch("bot.config.database_mysql.MYSQL_HOST", "localhost"):
                with patch("bot.config.database_mysql.MYSQL_USER", "test_user"):
                    with patch("bot.config.database_mysql.MYSQL_PASSWORD", "test_pass"):
                        with patch("bot.config.database_mysql.MYSQL_PORT", 3306):
                            db_manager = DatabaseManager()

                            # Verify enhanced cache manager is used
                            assert hasattr(db_manager, "cache_manager")
                            assert db_manager.cache_manager is not None

    def test_database_query_service_cache_manager_integration(self):
        """Test that query service uses enhanced cache manager."""
        query_service = DatabaseQueryService()

        # Verify enhanced cache manager is used
        assert hasattr(query_service, "cache_manager")
        assert query_service.cache_manager is not None

    def test_environment_variable_configuration(self):
        """Test environment variable configuration for database manager."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "DB_CACHE_TTL": "300",
                "DB_ENABLE_QUERY_CACHE": "false",
                "DB_SLOW_QUERY_THRESHOLD": "2.0",
                "DB_ENABLE_QUERY_LOGGING": "false",
                "MYSQL_POOL_MIN_SIZE": "2",
                "MYSQL_POOL_MAX_SIZE": "20",
                "MYSQL_POOL_MAX_OVERFLOW": "10",
                "MYSQL_POOL_TIMEOUT": "60",
                "MYSQL_CONNECT_TIMEOUT": "60",
            }.get(key, default)

            with patch("bot.config.database_mysql.MYSQL_DB", "test_db"):
                with patch("bot.config.database_mysql.MYSQL_HOST", "localhost"):
                    with patch("bot.config.database_mysql.MYSQL_USER", "test_user"):
                        with patch(
                            "bot.config.database_mysql.MYSQL_PASSWORD", "test_pass"
                        ):
                            with patch("bot.config.database_mysql.MYSQL_PORT", 3306):
                                db_manager = DatabaseManager()

                                # Test environment variable configuration
                                assert db_manager.default_cache_ttl == 300
                                assert db_manager.enable_query_cache is False
                                assert db_manager.slow_query_threshold == 2.0
                                assert db_manager.enable_query_logging is False
                                assert db_manager.pool_min_size == 2
                                assert db_manager.pool_max_size == 20
                                assert db_manager.pool_max_overflow == 10
                                assert db_manager.pool_timeout == 60
                                assert db_manager.connect_timeout == 60
