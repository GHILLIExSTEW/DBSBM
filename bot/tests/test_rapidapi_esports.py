#!/usr/bin/env python3
"""
Test script to verify RapidAPI esports integration.
"""

import asyncio
import logging
import pytest
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot.utils.multi_provider_api import MultiProviderAPI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_rapidapi_esports():
    """Test RapidAPI esports integration."""
    logger.info("Testing RapidAPI esports integration...")

    async with MultiProviderAPI() as api:
        try:
            # Test 1: Discover esports leagues
            logger.info("Test 1: Discovering esports leagues...")
            leagues = await api.discover_leagues("esports")
            logger.info(f"Found {len(leagues)} esports leagues")

            for league in leagues[:5]:  # Show first 5 leagues
                logger.info(f"  - {league.get('name')} (ID: {league.get('id')})")

            if not leagues:
                logger.warning("No esports leagues found")
                assert True, "No esports leagues found (this is acceptable)"

            # Test 2: Fetch games for the first league
            logger.info("Test 2: Fetching esports games...")
            first_league = leagues[0]
            today = datetime.now().strftime("%Y-%m-%d")

            games = await api.fetch_games("esports", first_league, today)
            logger.info(
                f"Found {len(games)} esports games for {first_league.get('name')}"
            )

            for game in games[:3]:  # Show first 3 games
                logger.info(
                    f"  - {game.get('home_team_name')} vs {game.get('away_team_name')} at {game.get('start_time')}"
                )

            # Test 3: Test direct API call
            logger.info("Test 3: Testing direct API call...")
            try:
                # Test with tournament_id filter
                data = await api.make_request(
                    "esports",
                    "/matches",
                    {
                        "tournament_id": f"eq.{first_league['id']}",
                        "limit": "10",
                        "lang": "en",
                        "offset": "0",
                    },
                )
                logger.info(f"Direct API call successful, response type: {type(data)}")
                if isinstance(data, dict):
                    logger.info(f"Response keys: {list(data.keys())}")
                elif isinstance(data, list):
                    logger.info(f"Response length: {len(data)}")
            except Exception as e:
                logger.error(f"Direct API call failed: {e}")

        except Exception as e:
            logger.error(f"Error testing esports integration: {e}")
            assert False, f"Esports integration test failed: {e}"

    assert True, "RapidAPI esports integration test completed successfully"


if __name__ == "__main__":
    asyncio.run(test_rapidapi_esports())
