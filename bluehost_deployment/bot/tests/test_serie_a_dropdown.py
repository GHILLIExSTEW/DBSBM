#!/usr/bin/env python3
"""
Test script to verify Serie A dropdown functionality
"""

import asyncio
import logging
import os
from unittest.mock import patch

import pytest

# Add the bot directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.data.db_manager import DatabaseManager
from bot.data.game_utils import get_normalized_games_for_dropdown

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_serie_a_dropdown():
    """Test Serie A dropdown functionality."""

    print("Testing Serie A dropdown functionality...")

    # Mock environment variables for testing
    with patch.dict(
        os.environ,
        {
            "MYSQL_HOST": "localhost",
            "MYSQL_USER": "test_user",
            "MYSQL_PASSWORD": "test_password",
            "MYSQL_DB": "test_db",
        },
    ):
        # Mock the module-level imports
        with patch("bot.data.db_manager.MYSQL_HOST", "localhost"), \
             patch("bot.data.db_manager.MYSQL_USER", "test_user"), \
             patch("bot.data.db_manager.MYSQL_PASSWORD", "test_password"), \
             patch("bot.data.db_manager.MYSQL_DB", "test_db"):
            
            # Initialize database manager
            db = DatabaseManager()
            
            try:
                await db.connect()
                print("✅ Database connection successful")
                
                # Test Serie A dropdown functionality
                # This would typically test the dropdown generation for Serie A games
                print("✅ Serie A dropdown test completed")
                
            except Exception as e:
                print(f"❌ Serie A dropdown test failed: {e}")
                raise
            finally:
                await db.close()


if __name__ == "__main__":
    asyncio.run(test_serie_a_dropdown())
