#!/usr/bin/env python3
"""
Test script for FlashLive Sports golf player data API
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


async def test_golf_players():
    """Test the FlashLive Sports golf player data API."""
    logger.info("=== GOLF PLAYER DATA API TEST ===")

    async with MultiProviderAPI() as api:
        try:
            # Try different sport IDs that might be golf
            sport_ids = ["23", "1", "golf", "GOLF"]
            locale = "en_INT"

            # Test with a known working player ID but different sport IDs
            player_id = "vgOOdZbd"  # This worked before

            for sport_id in sport_ids:
                logger.info(f"Testing sport_id: {sport_id}")
                try:
                    data = await api.fetch_player_data(sport_id, player_id, locale)

                    if data and "DATA" in data:
                        player_data = data["DATA"]
                        logger.info(
                            f"Found player: {player_data.get('NAME', 'Unknown')}"
                        )
                        logger.info(
                            f"  Sport ID: {player_data.get('SPORT_ID', 'Unknown')}"
                        )
                        logger.info(
                            f"  Country: {player_data.get('COUNTRY_NAME', 'Unknown')}"
                        )
                        logger.info(
                            f"  Team: {player_data.get('PARENT_NAME', 'Unknown')}"
                        )
                        logger.info("---")
                    else:
                        logger.info(f"No data found for sport_id: {sport_id}")

                except Exception as e:
                    logger.error(f"Error fetching data for sport_id {sport_id}: {e}")

                # Rate limiting
                await asyncio.sleep(1)

            # Let's also try to see if there are any golf-specific endpoints
            logger.info("Testing if there are golf-specific endpoints...")
            try:
                # Try a different endpoint that might list players
                data = await api.make_request("players", "/v1/sports", {})
                logger.info(f"Sports endpoint response: {data}")
            except Exception as e:
                logger.error(f"Error testing sports endpoint: {e}")

        except Exception as e:
            logger.error(f"Error testing golf player data API: {e}")


if __name__ == "__main__":
    asyncio.run(test_golf_players())
