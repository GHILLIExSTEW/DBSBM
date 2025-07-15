"""Tests for the services layer."""

import pytest
from unittest.mock import Mock, AsyncMock
clsfrom services.user_service import UserService
from services.analytics_service import AnalyticsService


@pytest.fixture
def mock_bot():
    return Mock()


@pytest.mark.asyncio
async def test_get_user_returns_none_for_missing_user(mock_bot, mock_database_manager):
    user_service = UserService(mock_bot, mock_database_manager)
    # Mock the cache to return None (cache miss)
    user_service.cache.get = Mock(return_value=None)
    # Simulate DB returning None
    user_service.db.fetch_one = AsyncMock(return_value=None)
    result = await user_service.get_user(123)
    assert result is None


@pytest.mark.asyncio
async def test_get_or_create_user_creates_user_if_missing(
    mock_bot, mock_database_manager
):
    user_service = UserService(mock_bot, mock_database_manager)
    # Simulate DB returning None, then a user dict
    user_service.db.fetch_one = AsyncMock(
        side_effect=[None, {"user_id": 123, "username": "TestUser", "balance": 0.0}]
    )
    user_service.db.execute = AsyncMock(return_value=1)
    result = await user_service.get_or_create_user(123, "TestUser")
    assert result["user_id"] == 123
    assert result["username"] == "TestUser"


@pytest.mark.asyncio
async def test_update_user_balance_adds_amount(mock_bot, mock_database_manager):
    user_service = UserService(mock_bot, mock_database_manager)
    # Simulate user exists
    user_service.get_or_create_user = AsyncMock(
        return_value={"user_id": 123, "balance": 10.0}
    )
    user_service.db.execute = AsyncMock(return_value=1)
    result = await user_service.update_user_balance(123, 5.0, "deposit")
    assert result["balance"] == 15.0


@pytest.mark.asyncio
async def test_get_user_balance_returns_balance(mock_bot, mock_database_manager):
    user_service = UserService(mock_bot, mock_database_manager)
    user_service.get_user = AsyncMock(return_value={"user_id": 123, "balance": 42.0})
    result = await user_service.get_user_balance(123)
    assert result == 42.0


@pytest.mark.asyncio
async def test_analytics_get_user_stats_returns_dict(mock_bot, mock_database_manager):
    analytics_service = AnalyticsService(mock_bot, mock_database_manager)
    analytics_service.db.fetch_one = AsyncMock(
        return_value={
            "total_bets": 10,
            "wins": 5,
            "losses": 5,
            "pushes": 0,
            "net_units": 10.0,
        }
    )
    analytics_service.db.fetch_one = AsyncMock(return_value={"total_risked": 100.0})
    result = await analytics_service.get_user_stats(1, 2)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_analytics_get_guild_stats_returns_dict(mock_bot, mock_database_manager):
    analytics_service = AnalyticsService(mock_bot, mock_database_manager)
    analytics_service.db.fetch_one = AsyncMock(
        return_value={
            "total_bets": 10,
            "wins": 5,
            "losses": 5,
            "pushes": 0,
            "net_units": 10.0,
            "total_cappers": 3,
        }
    )
    analytics_service.db.fetch_one = AsyncMock(return_value={"total_risked": 100.0})
    result = await analytics_service.get_guild_stats(1)
    assert isinstance(result, dict)
