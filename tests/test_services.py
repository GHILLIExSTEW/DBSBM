"""Tests for the services layer."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from betting-bot.services.bet_service import BetService
from betting-bot.services.user_service import UserService
from betting-bot.services.analytics_service import AnalyticsService


class TestBetService:
    """Test cases for BetService."""

    @pytest.fixture
    def bet_service(self, mock_database_manager):
        """Create a BetService instance with mocked dependencies."""
        return BetService(mock_database_manager)

    @pytest.mark.asyncio
    async def test_create_straight_bet_success(self, bet_service, sample_bet_data):
        """Test successful straight bet creation."""
        # Arrange
        bet_service.db_manager.execute.return_value = {"bet_id": "test_bet_123"}

        # Act
        result = await bet_service.create_straight_bet(
            guild_id=sample_bet_data["guild_id"],
            user_id=sample_bet_data["user_id"],
            game_id=sample_bet_data["game_id"],
            selection=sample_bet_data["selection"],
            odds=sample_bet_data["odds"],
            units=sample_bet_data["units"],
            description=sample_bet_data["description"]
        )

        # Assert
        assert result["bet_id"] == "test_bet_123"
        bet_service.db_manager.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_straight_bet_invalid_odds(self, bet_service, sample_bet_data):
        """Test bet creation with invalid odds."""
        # Arrange
        invalid_odds = 0.5  # Invalid odds

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid odds"):
            await bet_service.create_straight_bet(
                guild_id=sample_bet_data["guild_id"],
                user_id=sample_bet_data["user_id"],
                game_id=sample_bet_data["game_id"],
                selection=sample_bet_data["selection"],
                odds=invalid_odds,
                units=sample_bet_data["units"],
                description=sample_bet_data["description"]
            )

    @pytest.mark.asyncio
    async def test_get_user_bets(self, bet_service, sample_bet_data):
        """Test retrieving user bets."""
        # Arrange
        mock_bets = [
            {"bet_id": "1", "description": "Bet 1"},
            {"bet_id": "2", "description": "Bet 2"}
        ]
        bet_service.db_manager.fetch_all.return_value = mock_bets

        # Act
        result = await bet_service.get_user_bets(
            guild_id=sample_bet_data["guild_id"],
            user_id=sample_bet_data["user_id"]
        )

        # Assert
        assert len(result) == 2
        assert result[0]["bet_id"] == "1"
        bet_service.db_manager.fetch_all.assert_called_once()


class TestUserService:
    """Test cases for UserService."""

    @pytest.fixture
    def user_service(self, mock_database_manager):
        """Create a UserService instance with mocked dependencies."""
        return UserService(mock_database_manager)

    @pytest.mark.asyncio
    async def test_get_user_stats(self, user_service, sample_user_data):
        """Test retrieving user statistics."""
        # Arrange
        user_service.db_manager.fetch_one.return_value = sample_user_data

        # Act
        result = await user_service.get_user_stats(
            guild_id=123456789,
            user_id=sample_user_data["user_id"]
        )

        # Assert
        assert result["display_name"] == "TestUser"
        assert result["bet_won"] == 100.0
        user_service.db_manager.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_profile(self, user_service, sample_user_data):
        """Test updating user profile."""
        # Arrange
        user_service.db_manager.execute.return_value = {"affected_rows": 1}

        # Act
        result = await user_service.update_user_profile(
            guild_id=123456789,
            user_id=sample_user_data["user_id"],
            display_name="UpdatedName",
            image_path="/new/path.png"
        )

        # Assert
        assert result["affected_rows"] == 1
        user_service.db_manager.execute.assert_called_once()


class TestAnalyticsService:
    """Test cases for AnalyticsService."""

    @pytest.fixture
    def analytics_service(self, mock_database_manager):
        """Create an AnalyticsService instance with mocked dependencies."""
        return AnalyticsService(mock_database_manager)

    @pytest.mark.asyncio
    async def test_get_guild_stats(self, analytics_service, sample_guild_stats):
        """Test retrieving guild statistics."""
        # Arrange
        analytics_service.db_manager.fetch_one.return_value = sample_guild_stats

        # Act
        result = await analytics_service.get_guild_stats(guild_id=123456789)

        # Assert
        assert result["total_bets"] == 150
        assert result["total_cappers"] == 25
        assert len(result["leaderboard"]) == 3
        analytics_service.db_manager.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_top_cappers(self, analytics_service):
        """Test retrieving top cappers."""
        # Arrange
        mock_cappers = [
            {"user_id": 1, "username": "User1", "net_units": 25.5},
            {"user_id": 2, "username": "User2", "net_units": 20.0}
        ]
        analytics_service.db_manager.fetch_all.return_value = mock_cappers

        # Act
        result = await analytics_service.get_top_cappers(guild_id=123456789, limit=10)

        # Assert
        assert len(result) == 2
        assert result[0]["net_units"] == 25.5
        analytics_service.db_manager.fetch_all.assert_called_once() 