"""
Tests for the rate limiter utility.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from bot.utils.rate_limiter import (
    RateLimiter, 
    RateLimitConfig, 
    RateLimitEntry, 
    RateLimitExceededError,
    get_rate_limiter,
    rate_limit
)


class TestRateLimitConfig:
    """Test cases for RateLimitConfig."""
    
    def test_rate_limit_config_creation(self):
        """Test creating a rate limit configuration."""
        config = RateLimitConfig(
            max_requests=10,
            window_seconds=60,
            action_name="test_action",
            description="Test description"
        )
        
        assert config.max_requests == 10
        assert config.window_seconds == 60
        assert config.action_name == "test_action"
        assert config.description == "Test description"


class TestRateLimiter:
    """Test cases for RateLimiter class."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter instance for testing."""
        return RateLimiter()
    
    @pytest.mark.asyncio
    async def test_is_allowed_within_limit(self, rate_limiter):
        """Test that requests within the limit are allowed."""
        user_id = 123456789
        action = "bet_placement"
        
        # Should allow first 5 requests (default limit)
        for i in range(5):
            is_allowed, retry_after = await rate_limiter.is_allowed(user_id, action)
            assert is_allowed is True
            assert retry_after is None
    
    @pytest.mark.asyncio
    async def test_is_allowed_exceeds_limit(self, rate_limiter):
        """Test that requests exceeding the limit are blocked."""
        user_id = 123456789
        action = "bet_placement"
        
        # Allow first 5 requests
        for i in range(5):
            await rate_limiter.is_allowed(user_id, action)
        
        # 6th request should be blocked
        is_allowed, retry_after = await rate_limiter.is_allowed(user_id, action)
        assert is_allowed is False
        assert retry_after is not None
        assert retry_after > 0
    
    @pytest.mark.asyncio
    async def test_is_allowed_unknown_action(self, rate_limiter):
        """Test that unknown actions are allowed by default."""
        user_id = 123456789
        action = "unknown_action"
        
        is_allowed, retry_after = await rate_limiter.is_allowed(user_id, action)
        assert is_allowed is True
        assert retry_after is None
    
    @pytest.mark.asyncio
    async def test_cleanup_old_entries(self, rate_limiter):
        """Test cleanup of old rate limit entries."""
        user_id = 123456789
        action = "bet_placement"
        
        # Add some requests
        for i in range(3):
            await rate_limiter.is_allowed(user_id, action)
        
        # Manually add old entries
        old_time = time.time() - 120  # 2 minutes ago
        rate_limiter.user_requests[(user_id, action)].appendleft(
            RateLimitEntry(timestamp=old_time, user_id=user_id, action=action)
        )
        
        # Clean up old entries
        await rate_limiter._cleanup_old_entries((user_id, action), 60)
        
        # Should only have recent entries
        current_requests = len(rate_limiter.user_requests[(user_id, action)])
        assert current_requests == 3  # Only the recent ones
    
    @pytest.mark.asyncio
    async def test_cleanup_all_old_entries(self, rate_limiter):
        """Test cleanup of all old entries."""
        user_id = 123456789
        
        # Add requests for different actions
        for action in ["bet_placement", "stats_query"]:
            for i in range(3):
                await rate_limiter.is_allowed(user_id, action)
        
        # Manually add old entries
        old_time = time.time() - 120
        for action in ["bet_placement", "stats_query"]:
            rate_limiter.user_requests[(user_id, action)].appendleft(
                RateLimitEntry(timestamp=old_time, user_id=user_id, action=action)
            )
        
        # Clean up all old entries
        await rate_limiter.cleanup_all_old_entries()
        
        # Should only have recent entries
        for action in ["bet_placement", "stats_query"]:
            current_requests = len(rate_limiter.user_requests[(user_id, action)])
            assert current_requests == 3
    
    def test_get_user_stats(self, rate_limiter):
        """Test getting user statistics."""
        user_id = 123456789
        
        # Add some requests
        asyncio.run(rate_limiter.is_allowed(user_id, "bet_placement"))
        asyncio.run(rate_limiter.is_allowed(user_id, "stats_query"))
        
        stats = rate_limiter.get_user_stats(user_id)
        
        assert "bet_placement" in stats
        assert "stats_query" in stats
        assert stats["bet_placement"]["current_requests"] == 1
        assert stats["bet_placement"]["remaining"] == 4  # 5 - 1
        assert stats["stats_query"]["current_requests"] == 1
        assert stats["stats_query"]["remaining"] == 9  # 10 - 1
    
    def test_get_global_stats(self, rate_limiter):
        """Test getting global statistics."""
        user_id = 123456789
        
        # Add some requests
        asyncio.run(rate_limiter.is_allowed(user_id, "bet_placement"))
        
        stats = rate_limiter.get_global_stats()
        
        assert stats["total_requests"] == 1
        assert stats["rate_limited_requests"] == 0
        assert stats["total_users"] == 1
        assert stats["total_actions"] == 1
        assert stats["active_limits"] == 6  # Number of default limits
        assert stats["rate_limit_percentage"] == 0.0
    
    def test_reset_user_specific_action(self, rate_limiter):
        """Test resetting rate limit for specific action."""
        user_id = 123456789
        action = "bet_placement"
        
        # Add some requests
        asyncio.run(rate_limiter.is_allowed(user_id, action))
        
        # Reset the action
        rate_limiter.reset_user(user_id, action)
        
        # Should be able to make requests again
        is_allowed, retry_after = asyncio.run(rate_limiter.is_allowed(user_id, action))
        assert is_allowed is True
        assert retry_after is None
    
    def test_reset_user_all_actions(self, rate_limiter):
        """Test resetting rate limit for all user actions."""
        user_id = 123456789
        
        # Add requests for multiple actions
        asyncio.run(rate_limiter.is_allowed(user_id, "bet_placement"))
        asyncio.run(rate_limiter.is_allowed(user_id, "stats_query"))
        
        # Reset all actions
        rate_limiter.reset_user(user_id)
        
        # Should be able to make requests again
        for action in ["bet_placement", "stats_query"]:
            is_allowed, retry_after = asyncio.run(rate_limiter.is_allowed(user_id, action))
            assert is_allowed is True
            assert retry_after is None


class TestRateLimitDecorator:
    """Test cases for RateLimitDecorator."""
    
    @pytest.fixture
    def mock_rate_limiter(self):
        """Create a mock rate limiter."""
        limiter = Mock()
        limiter.is_allowed = AsyncMock()
        return limiter
    
    @pytest.fixture
    def decorator(self, mock_rate_limiter):
        """Create a rate limit decorator."""
        from bot.utils.rate_limiter import RateLimitDecorator
        return RateLimitDecorator(mock_rate_limiter, "test_action")
    
    @pytest.mark.asyncio
    async def test_decorator_allows_request(self, decorator, mock_rate_limiter):
        """Test that decorator allows requests when rate limit is not exceeded."""
        # Mock interaction with user
        mock_interaction = Mock()
        mock_interaction.user.id = 123456789
        
        # Mock rate limiter to allow request
        mock_rate_limiter.is_allowed.return_value = (True, None)
        
        # Create test function
        @decorator
        async def test_func(interaction):
            return "success"
        
        # Call the function
        result = await test_func(mock_interaction)
        
        assert result == "success"
        mock_rate_limiter.is_allowed.assert_called_once_with(123456789, "test_action")
    
    @pytest.mark.asyncio
    async def test_decorator_blocks_request(self, decorator, mock_rate_limiter):
        """Test that decorator blocks requests when rate limit is exceeded."""
        # Mock interaction with user
        mock_interaction = Mock()
        mock_interaction.user.id = 123456789
        
        # Mock rate limiter to block request
        mock_rate_limiter.is_allowed.return_value = (False, 30.5)
        
        # Create test function
        @decorator
        async def test_func(interaction):
            return "success"
        
        # Call the function - should raise exception
        with pytest.raises(RateLimitExceededError) as exc_info:
            await test_func(mock_interaction)
        
        assert "Rate limit exceeded" in str(exc_info.value)
        assert "30.5" in str(exc_info.value)
        mock_rate_limiter.is_allowed.assert_called_once_with(123456789, "test_action")
    
    @pytest.mark.asyncio
    async def test_decorator_no_user_id(self, decorator, mock_rate_limiter):
        """Test decorator behavior when user_id cannot be extracted."""
        # Create test function with no user context
        @decorator
        async def test_func():
            return "success"
        
        # Should allow the request and log a warning
        with patch('bot.utils.rate_limiter.logger') as mock_logger:
            result = await test_func()
            
            assert result == "success"
            mock_logger.warning.assert_called_once()


class TestGlobalRateLimiter:
    """Test cases for global rate limiter functions."""
    
    def test_get_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns a singleton."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        assert limiter1 is limiter2
    
    @pytest.mark.asyncio
    async def test_rate_limit_decorator(self):
        """Test the rate_limit decorator."""
        # Mock the global rate limiter
        mock_limiter = Mock()
        mock_limiter.is_allowed = AsyncMock(return_value=(True, None))
        
        with patch('bot.utils.rate_limiter.get_rate_limiter', return_value=mock_limiter):
            @rate_limit("test_action")
            async def test_func(interaction):
                return "success"
            
            # Mock interaction
            mock_interaction = Mock()
            mock_interaction.user.id = 123456789
            
            # Call the function
            result = await test_func(mock_interaction)
            
            assert result == "success"
            mock_limiter.is_allowed.assert_called_once_with(123456789, "test_action")


class TestRateLimitExceededError:
    """Test cases for RateLimitExceededError."""
    
    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError creation and message."""
        error = RateLimitExceededError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__]) 