#!/usr/bin/env python3
"""
Test script for FlashLive Sports player data API
"""

import asyncio
import json
import logging
import os
import sys

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.multi_provider_api import MultiProviderAPI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_player_data():
    """Test the FlashLive Sports player data API."""
    logger.info("=== PLAYER DATA API TEST ===")

    async with MultiProviderAPI() as api:
        try:
            # Test player data fetching for golf (sport_id: 23)
            sport_id = "23"  # Golf
            player_id = "vgOOdZbd"
            locale = "en_INT"

            logger.info(
                f"Fetching player data for sport_id: {sport_id}, player_id: {player_id}"
            )
            data = await api.fetch_player_data(sport_id, player_id, locale)

            logger.info(f"API response type: {type(data)}")

            if isinstance(data, dict):
                logger.info(f"Response keys: {list(data.keys())}")
                logger.info(f"Response structure: {json.dumps(data, indent=2)}")
            else:
                logger.info(f"Response: {data}")

        except Exception as e:
            logger.error(f"Error testing player data API: {e}")


if __name__ == "__main__":
    asyncio.run(test_player_data())
