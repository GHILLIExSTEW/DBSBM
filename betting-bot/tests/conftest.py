"""Pytest configuration and fixtures for DBSBM testing."""

import asyncio
import os
import sys
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_bet_data() -> Dict[str, Any]:
    """Sample bet data for testing."""
    return {
        "guild_id": 123456789,
        "user_id": 987654321,
        "game_id": "test_game_123",
        "bet_type": "straight",
        "selection": "home",
        "odds": 1.85,
        "units": 2.0,
        "description": "Test bet description",
    }


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "user_id": 987654321,
        "display_name": "TestUser",
        "image_path": "/static/guilds/123456789/users/987654321.png",
        "banner_color": "#00ff00",
        "bet_won": 100.0,
        "bet_loss": 50.0,
        "bet_push": 10.0,
    }


@pytest.fixture
def sample_guild_stats() -> Dict[str, Any]:
    """Sample guild statistics for testing."""
    return {
        "total_bets": 150,
        "total_cappers": 25,
        "total_units": 500.0,
        "net_units": 75.5,
        "wins": 85,
        "losses": 60,
        "pushes": 5,
        "leaderboard": [
            {"username": "User1", "net_units": 25.5},
            {"username": "User2", "net_units": 20.0},
            {"username": "User3", "net_units": 15.0},
        ],
    }


@pytest.fixture
def mock_discord_interaction():
    """Mock Discord interaction for testing."""
    interaction = Mock()
    interaction.user = Mock()
    interaction.user.id = 987654321
    interaction.user.display_name = "TestUser"
    interaction.guild = Mock()
    interaction.guild.id = 123456789
    interaction.response = Mock()
    interaction.response.send_message = AsyncMock()
    interaction.followup = Mock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.fixture
def mock_database_manager():
    """Mock database manager for testing."""
    db_manager = Mock()
    db_manager.connect = AsyncMock()
    db_manager.execute = AsyncMock()
    db_manager.fetch_one = AsyncMock()
    db_manager.fetch_all = AsyncMock()
    db_manager.close = AsyncMock()
    return db_manager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
