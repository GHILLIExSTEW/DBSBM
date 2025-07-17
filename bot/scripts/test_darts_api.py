#!/usr/bin/env python3
"""
Test RapidAPI Darts Integration
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


async def test_darts_api():
    """Test the RapidAPI Darts API with working parameters."""
    logger.info("Testing RapidAPI Darts API...")

    # Check if RapidAPI key is available
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    if not rapidapi_key:
        logger.error("RAPIDAPI_KEY not found in environment variables!")
        return False

    logger.info(f"RapidAPI key found: {rapidapi_key[:10]}...")

    async with MultiProviderAPI() as api:
        try:
            # Test Darts API with working parameters
            params = {
                "offset": "0",
                "round_id": "eq.343554",
                "lang": "en",
                "away_team_id": "eq.61609",
                "home_team_id": "eq.61486",
                "season_id": "eq.33898",
                "limit": "50",
                "tournament_id": "eq.15677",
                "id": "eq.1",
            }

            darts_data = await api.make_request("darts", "/matches", params)

            logger.info(f"Darts API response received!")
            logger.info(f"Response type: {type(darts_data)}")

            if isinstance(darts_data, dict):
                logger.info(f"Response keys: {list(darts_data.keys())}")
                if "data" in darts_data:
                    logger.info(f"Number of matches: {len(darts_data['data'])}")
                    if darts_data["data"]:
                        logger.info(f"First match: {darts_data['data'][0]}")
                elif "matches" in darts_data:
                    logger.info(f"Number of matches: {len(darts_data['matches'])}")
                    if darts_data["matches"]:
                        logger.info(f"First match: {darts_data['matches'][0]}")

            return True

        except Exception as e:
            logger.error(f"Darts API failed: {e}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_darts_api())
    if success:
        logger.info("Darts API test successful!")
    else:
        logger.error("Darts API test failed!")
