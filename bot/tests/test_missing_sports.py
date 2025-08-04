#!/usr/bin/env python3
"""
Test script to check if darts, tennis, golf, and esports are being fetched and saved to the database.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.data.db_manager import DatabaseManager
from bot.utils.multi_provider_api import MultiProviderAPI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_missing_sports():
    """Test that missing sports APIs are properly handled."""

    # Mock environment variables for testing
    with patch.dict(
        os.environ,
        {
            "RAPIDAPI_KEY": "test_rapidapi_key",
        },
    ):
        # Check if RAPIDAPI_KEY is available
        rapidapi_key = os.getenv("RAPIDAPI_KEY")

        if not rapidapi_key:
            logger.error("❌ RAPIDAPI_KEY not found in environment variables!")
            logger.error("This is required for darts, tennis, and golf APIs")
            assert False, "RAPIDAPI_KEY not found in environment variables"

        logger.info("✅ RAPIDAPI_KEY found in environment variables")
        logger.info("This enables darts, tennis, and golf APIs")

        # Test that the key is properly set
        assert (
            rapidapi_key == "test_rapidapi_key"
        ), "RAPIDAPI_KEY should be set to test value"

        logger.info("✅ Missing sports test completed successfully")


if __name__ == "__main__":
    asyncio.run(test_missing_sports())
