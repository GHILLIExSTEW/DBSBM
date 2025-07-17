#!/usr/bin/env python3
"""
Comprehensive test script for all sports APIs.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_all_apis():
    """Test all sports APIs and show their status."""
    logger.info("Testing All Sports APIs...")
    logger.info("=" * 60)

    # Define all sports to test
    sports_to_test = [
        # API-Sports (should work)
        "football",
        "basketball",
        "baseball",
        "hockey",
        "american-football",
        "rugby",
        "volleyball",
        "handball",
        "afl",
        "formula-1",
        "mma",
        # RapidAPI (should work if subscribed)
        "darts",
        "golf",
        # SportDevs (may be down)
        "tennis",
        "esports",
    ]

    results = {}

    async with MultiProviderAPI() as api:
        for sport in sports_to_test:
            logger.info(f"\n--- Testing {sport.upper()} ---")

            try:
                # Test league discovery
                logger.info(f"Discovering {sport} leagues...")
                leagues = await api.discover_leagues(sport)

                if leagues:
                    logger.info(f"✅ SUCCESS: Found {len(leagues)} {sport} leagues")
                    results[sport] = {"status": "✅ WORKING", "leagues": len(leagues)}

                    # Show first few leagues
                    for i, league in enumerate(leagues[:3]):
                        logger.info(f"  {i+1}. {league['name']} (ID: {league['id']})")

                    # Test fetching games for the first league
                    if leagues:
                        first_league = leagues[0]
                        today = datetime.now().strftime("%Y-%m-%d")
                        logger.info(
                            f"Fetching games for {first_league['name']} on {today}..."
                        )

                        games = await api.fetch_games(sport, first_league, today)
                        logger.info(f"Found {len(games)} games")

                        if games:
                            for i, game in enumerate(games[:2]):
                                home = game.get("home_team_name", "Unknown")
                                away = game.get("away_team_name", "Unknown")
                                status = game.get("status", "Unknown")
                                logger.info(f"  {i+1}. {home} vs {away} ({status})")

                                if game.get("score"):
                                    score = game["score"]
                                    logger.info(
                                        f"     Score: {score.get('home', '?')} - {score.get('away', '?')}"
                                    )
                        else:
                            logger.info("  No games found for today")
                else:
                    logger.warning(f"⚠️  NO LEAGUES: No {sport} leagues found")
                    results[sport] = {"status": "⚠️  NO LEAGUES", "leagues": 0}

            except Exception as e:
                logger.error(f"❌ ERROR: {sport} failed - {e}")
                results[sport] = {"status": "❌ ERROR", "leagues": 0, "error": str(e)}

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY OF ALL API TESTS")
    logger.info("=" * 60)

    working_count = 0
    for sport, result in results.items():
        status = result["status"]
        leagues = result["leagues"]
        logger.info(f"{sport:15} | {status:12} | {leagues:3} leagues")
        if "✅ WORKING" in status:
            working_count += 1

    logger.info(f"\nTotal APIs Working: {working_count}/{len(sports_to_test)}")
    logger.info("=" * 60)


async def main():
    """Run all tests."""
    await test_all_apis()


if __name__ == "__main__":
    asyncio.run(main())
