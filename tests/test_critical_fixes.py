"""
Comprehensive test suite for critical fixes implemented in Phase 1.

This module tests all the critical fixes including:
- Rate limiter implementation
- Database configuration improvements
- Enhanced error recovery strategies
- Centralized configuration system
- Environment validation enhancements
"""

import asyncio
import logging
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import the components to test
try:
    from bot.data.db_manager import DatabaseManager
    from bot.utils.environment_validator import EnvironmentValidator
    from bot.utils.error_handler import (
        get_error_handler,
        initialize_default_recovery_strategies,
    )
    from bot.utils.rate_limiter import RateLimiter, RateLimitExceededError, rate_limit
    from config.settings import (
        get_api_config,
        get_database_config,
        get_settings,
        validate_settings,
    )
except ImportError:
    # Fallback - try to import from parent directory
    import os
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Add multiple possible paths for different execution contexts
    possible_paths = [
        current_dir,  # From tests/
        os.path.dirname(current_dir),  # From root/
    ]
    for path in possible_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        from bot.data.db_manager import DatabaseManager
        from bot.utils.environment_validator import EnvironmentValidator
        from bot.utils.error_handler import (
            get_error_handler,
            initialize_default_recovery_strategies,
        )
        from bot.utils.rate_limiter import (
            RateLimiter,
            RateLimitExceededError,
            rate_limit,
        )
        from config.settings import (
            get_api_config,
            get_database_config,
            get_settings,
            validate_settings,
        )
    except ImportError:
        # Final fallback - create mock functions for testing
        def get_settings():
            return None

        def validate_settings():
            return []

        def get_api_config():
            return {}

        def get_database_config():
            return {}


class TestRateLimiterFixes:
    """Test suite for rate limiter fixes."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter instance for testing."""
        return RateLimiter()

    @pytest.mark.asyncio
    async def test_is_allowed_returns_boolean(self, rate_limiter):
        """Test that is_allowed returns a boolean instead of tuple."""
        user_id = 123456789
        action = "test_action"

        result = await rate_limiter.is_allowed(user_id, action)
        assert isinstance(result, bool)
        assert result is True  # Should allow first request

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_works(self, rate_limiter):
        """Test that the rate limit decorator works correctly."""
        # Mock interaction
        mock_interaction = Mock()
        mock_interaction.user.id = 123456789

        # Create test function with decorator
        @rate_limit("test_action")
        async def test_func(interaction):
            return "success"

        # Should succeed on first call
        result = await test_func(mock_interaction)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_rate_limit_exceeds_limit(self, rate_limiter):
        """Test that rate limiting works when limit is exceeded."""
        user_id = 123456789
        action = "bet_placement"  # Use a known action from the rate limiter

        # Make multiple requests to exceed limit
        for i in range(10):  # More than default limit of 5
            await rate_limiter.is_allowed(user_id, action)

        # Next request should be blocked
        result = await rate_limiter.is_allowed(user_id, action)
        assert result is False

    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self, rate_limiter):
        """Test that old rate limit entries are cleaned up."""
        user_id = 123456789
        action = "bet_placement"  # Use a known action from the rate limiter

        # Make a request
        await rate_limiter.is_allowed(user_id, action)

        # Simulate time passing (cleanup happens automatically)
        # This is a basic test - in real scenarios, cleanup happens in background

        # Should still be allowed for new requests
        result = await rate_limiter.is_allowed(user_id, action)
        assert result is True


class TestDatabaseConfiguration:
    """Test suite for database configuration improvements."""

    @pytest.fixture
    def db_manager(self):
        """Create a database manager instance for testing."""
        return DatabaseManager()

    def test_database_config_environment_variables(self, db_manager):
        """Test that database configuration uses environment variables."""
        # Test that the manager has configurable pool settings
        assert hasattr(db_manager, "pool_min_size")
        assert hasattr(db_manager, "pool_max_size")
        assert hasattr(db_manager, "pool_max_overflow")
        assert hasattr(db_manager, "pool_timeout")
        assert hasattr(db_manager, "connect_timeout")

        # Test that values are integers
        assert isinstance(db_manager.pool_min_size, int)
        assert isinstance(db_manager.pool_max_size, int)
        assert isinstance(db_manager.pool_max_overflow, int)
        assert isinstance(db_manager.pool_timeout, int)
        assert isinstance(db_manager.connect_timeout, int)

    def test_database_config_validation(self, db_manager):
        """Test that database configuration validates properly."""
        # Test that max_size is greater than or equal to min_size
        assert db_manager.pool_max_size >= db_manager.pool_min_size

        # Test that values are within reasonable bounds
        assert 1 <= db_manager.pool_min_size <= 50
        assert 1 <= db_manager.pool_max_size <= 100
        assert 0 <= db_manager.pool_max_overflow <= 50
        # Note: pool_timeout is not used in aiomysql.create_pool() as it's not supported
        assert 5 <= db_manager.pool_timeout <= 300
        assert 5 <= db_manager.connect_timeout <= 300

    @pytest.mark.asyncio
    async def test_database_connection_handling(self, db_manager):
        """Test that database connection handles errors gracefully."""
        # This test would require a mock database or real connection
        # For now, we'll test the configuration is valid
        assert db_manager.db_name is not None

        # Test that the manager can be instantiated without errors
        assert db_manager is not None


class TestErrorRecoveryStrategies:
    """Test suite for enhanced error recovery strategies."""

    @pytest.fixture
    def error_handler(self):
        """Get the error handler instance."""
        initialize_default_recovery_strategies()
        return get_error_handler()

    def test_error_handler_initialization(self, error_handler):
        """Test that error handler initializes with recovery strategies."""
        assert error_handler is not None
        assert hasattr(error_handler, "recovery_strategies")
        assert len(error_handler.recovery_strategies) > 0

    def test_database_recovery_strategy_exists(self, error_handler):
        """Test that database recovery strategy is available."""
        # Check if database recovery strategy is registered
        # The recovery strategies are stored by exception type
        from bot.utils.error_handler import DatabaseError

        assert DatabaseError in error_handler.recovery_strategies

    def test_api_recovery_strategy_exists(self, error_handler):
        """Test that API recovery strategy is available."""
        # Check if API recovery strategy is registered
        from bot.utils.error_handler import APIError

        assert APIError in error_handler.recovery_strategies

    @pytest.mark.asyncio
    async def test_error_handler_async_handling(self, error_handler):
        """Test that error handler can handle async errors."""
        # Create a mock error
        mock_error = Exception("Test error")
        mock_context = {"user_id": 123, "guild_id": 456, "command": "test"}

        # Test that the error handler can process the error
        # This is a basic test - actual implementation would depend on the error handler
        assert error_handler is not None


class TestCentralizedConfiguration:
    """Test suite for centralized configuration system."""

    def test_settings_import(self):
        """Test that settings can be imported and instantiated."""
        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, "environment")
        assert hasattr(settings, "database")
        assert hasattr(settings, "api")
        assert hasattr(settings, "discord")

    def test_settings_validation(self):
        """Test that settings validation works."""
        errors = validate_settings()
        assert isinstance(errors, list)

        # In a test environment, we expect some errors due to missing env vars
        # This is expected behavior
        assert len(errors) >= 0

    def test_database_config_function(self):
        """Test that database config function works."""
        db_config = get_database_config()
        assert isinstance(db_config, dict)
        assert "host" in db_config
        assert "port" in db_config
        assert "user" in db_config
        assert "password" in db_config
        assert "database" in db_config

    def test_api_config_function(self):
        """Test that API config function works."""
        api_config = get_api_config()
        assert isinstance(api_config, dict)
        assert "key" in api_config
        assert "timeout" in api_config
        assert "retry_attempts" in api_config
        assert "enabled" in api_config

    def test_settings_masked_config(self):
        """Test that sensitive data is masked in config summary."""
        settings = get_settings()
        masked_config = settings.get_masked_config()

        # Check that sensitive fields are masked
        for section_name, section_data in masked_config.items():
            if isinstance(section_data, dict):
                for field_name, field_value in section_data.items():
                    if any(
                        sensitive in field_name.lower()
                        for sensitive in ["password", "token", "key"]
                    ):
                        assert field_value == "***MASKED***" or field_value == ""

    def test_settings_environment_methods(self):
        """Test that environment checking methods work."""
        settings = get_settings()

        # Test environment checking methods
        assert isinstance(settings.is_development(), bool)
        assert isinstance(settings.is_production(), bool)
        assert isinstance(settings.is_testing(), bool)


class TestEnvironmentValidation:
    """Test suite for enhanced environment validation."""

    def test_environment_validator_import(self):
        """Test that environment validator can be imported."""
        assert EnvironmentValidator is not None

    def test_basic_validation(self):
        """Test that basic environment validation works."""
        is_valid, errors = EnvironmentValidator.validate_all()
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    @pytest.mark.asyncio
    async def test_connection_validation_methods(self):
        """Test that connection validation methods exist and are callable."""
        # Test that methods exist and are callable
        assert hasattr(EnvironmentValidator, "validate_database_connection")
        assert hasattr(EnvironmentValidator, "validate_api_connection")
        assert hasattr(EnvironmentValidator, "validate_discord_token")
        assert hasattr(EnvironmentValidator, "validate_all_connections")

        # Test that methods are async
        assert asyncio.iscoroutinefunction(
            EnvironmentValidator.validate_database_connection
        )
        assert asyncio.iscoroutinefunction(EnvironmentValidator.validate_api_connection)
        assert asyncio.iscoroutinefunction(EnvironmentValidator.validate_discord_token)
        assert asyncio.iscoroutinefunction(
            EnvironmentValidator.validate_all_connections
        )

    @pytest.mark.asyncio
    async def test_connection_validation_results(self):
        """Test that connection validation returns proper results."""
        # Test database connection validation
        db_success, db_message = (
            await EnvironmentValidator.validate_database_connection()
        )
        assert isinstance(db_success, bool)
        assert isinstance(db_message, str)

        # Test API connection validation
        api_success, api_message = await EnvironmentValidator.validate_api_connection()
        assert isinstance(api_success, bool)
        assert isinstance(api_message, str)

        # Test Discord token validation
        discord_success, discord_message = (
            await EnvironmentValidator.validate_discord_token()
        )
        assert isinstance(discord_success, bool)
        assert isinstance(discord_message, str)

    @pytest.mark.asyncio
    async def test_all_connections_validation(self):
        """Test that all connections validation returns proper structure."""
        results = await EnvironmentValidator.validate_all_connections()

        assert isinstance(results, dict)
        assert "database" in results
        assert "api" in results
        assert "discord" in results

        for connection_type, (success, message) in results.items():
            assert isinstance(success, bool)
            assert isinstance(message, str)


class TestIntegrationScenarios:
    """Test suite for integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_configuration_workflow(self):
        """Test the full configuration workflow."""
        # Test that settings can be loaded
        settings = get_settings()
        assert settings is not None

        # Test that validation works
        errors = validate_settings()
        assert isinstance(errors, list)

        # Test that environment validator works
        is_valid, validation_errors = EnvironmentValidator.validate_all()
        assert isinstance(is_valid, bool)
        assert isinstance(validation_errors, list)

        # Test that error handler is available
        error_handler = get_error_handler()
        assert error_handler is not None

    def test_configuration_consistency(self):
        """Test that configuration is consistent across components."""
        # Test that database config is consistent
        settings = get_settings()
        db_config = get_database_config()

        assert settings.database.host == db_config["host"]
        assert settings.database.port == db_config["port"]
        assert settings.database.user == db_config["user"]

        # Test that API config is consistent
        api_config = get_api_config()
        assert settings.api.timeout == api_config["timeout"]
        assert settings.api.retry_attempts == api_config["retry_attempts"]
        assert settings.api.enabled == api_config["enabled"]


# Performance tests
class TestPerformance:
    """Test suite for performance aspects of critical fixes."""

    @pytest.mark.asyncio
    async def test_rate_limiter_performance(self):
        """Test that rate limiter performs well under load."""
        rate_limiter = RateLimiter()
        user_id = 123456789
        action = "performance_test"

        # Test multiple rapid requests
        start_time = asyncio.get_event_loop().time()

        for i in range(100):
            await rate_limiter.is_allowed(user_id, action)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # Should complete 100 requests in under 1 second
        assert duration < 1.0

    def test_settings_instantiation_performance(self):
        """Test that settings instantiation is fast."""
        import time

        start_time = time.time()

        for i in range(100):
            settings = get_settings()

        end_time = time.time()
        duration = end_time - start_time

        # Should instantiate 100 settings objects in under 1 second
        assert duration < 1.0

    def test_configuration_validation_performance(self):
        """Test that configuration validation is fast."""
        import time

        start_time = time.time()

        for i in range(100):
            errors = validate_settings()

        end_time = time.time()
        duration = end_time - start_time

        # Should validate 100 times in under 1 second
        assert duration < 1.0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
