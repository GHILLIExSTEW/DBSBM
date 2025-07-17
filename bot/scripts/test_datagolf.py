#!/usr/bin/env python3
"""
Test script for DataGolf API
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


async def test_datagolf():
    """Test the DataGolf API."""
    logger.info("=== DATAGOLF API TEST ===")

    async with MultiProviderAPI() as api:
        try:
            # Test golf player list fetching
            logger.info("Fetching golf player list...")
            players = await api.fetch_golf_players("json")

            logger.info(f"API response type: {type(players)}")

            if isinstance(players, list):
                logger.info(f"Found {len(players)} golf players")
                if players:
                    logger.info(
                        f"First player structure: {json.dumps(players[0], indent=2)}"
                    )

                    # Show a few more players
                    logger.info("Sample players:")
                    for i, player in enumerate(players[:5]):
                        logger.info(
                            f"  {i+1}. {player.get('player_name', 'Unknown')} (ID: {player.get('dg_id', 'Unknown')})"
                        )

            else:
                logger.info(f"Response: {players}")

        except Exception as e:
            logger.error(f"Error testing DataGolf API: {e}")


if __name__ == "__main__":
    asyncio.run(test_datagolf())
