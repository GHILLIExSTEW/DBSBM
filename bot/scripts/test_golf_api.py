#!/usr/bin/env python3
"""
Test Golf API with RapidAPI Key
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the bot directory to the Python path
bot_dir = Path(__file__).parent.parent
sys.path.insert(0, str(bot_dir))

from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_golf_api():
    """Test the Golf API specifically."""
    logger.info("Testing Golf API with RapidAPI key...")

    # Check if RapidAPI key is available
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    if not rapidapi_key:
        logger.error("RAPIDAPI_KEY not found in environment variables!")
        return False

    logger.info(f"RapidAPI key found: {rapidapi_key[:10]}...")

    async with MultiProviderAPI() as api:
        try:
            # Test Golf API
            params = {"start_date": "2024-10-01", "end_date": "2024-10-30"}
            golf_data = await api.make_request("golf", "/v1/events", params)

            logger.info(f"Golf API response received!")
            logger.info(f"Response type: {type(golf_data)}")

            if isinstance(golf_data, dict):
                logger.info(f"Response keys: {list(golf_data.keys())}")
                if "events" in golf_data:
                    logger.info(f"Number of events: {len(golf_data['events'])}")
                    if golf_data["events"]:
                        logger.info(f"First event: {golf_data['events'][0]}")

            return True

        except Exception as e:
            logger.error(f"Golf API failed: {e}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_golf_api())
    if success:
        logger.info("Golf API test successful!")
    else:
        logger.error("Golf API test failed!")
