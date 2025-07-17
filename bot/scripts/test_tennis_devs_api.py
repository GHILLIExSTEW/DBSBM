#!/usr/bin/env python3
"""
Test Tennis Devs API endpoints with proper parameters.
"""

import os
import sys
import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_tennis_devs_api():
    """Test Tennis Devs API endpoints."""
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        logger.warning("⚠️ RAPIDAPI_KEY not found in environment variables")
        api_key = input("Please enter your RapidAPI key: ").strip()
        if not api_key:
            logger.error("❌ No API key provided")
            return

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "tennis-devs.p.rapidapi.com",
    }

    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Get tournaments
            logger.info("🔍 Testing tournaments endpoint...")
            url = "https://tennis-devs.p.rapidapi.com/tournaments"
            params = {"offset": "0", "limit": "10", "lang": "en"}

            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        f"✅ Tournaments response: {len(data) if isinstance(data, list) else 'unknown'} tournaments found"
                    )

                    # Show first few tournaments
                    tournaments = (
                        data if isinstance(data, list) else data.get("tournaments", [])
                    )
                    for i, tournament in enumerate(tournaments[:3]):
                        logger.info(
                            f"  {i+1}. {tournament.get('name', 'Unknown')} (ID: {tournament.get('id', 'Unknown')})"
                        )
                else:
                    logger.error(f"❌ Tournaments failed: {response.status}")
                    logger.error(await response.text())

            # Test 2: Get matches by date (tomorrow)
            logger.info("\n🔍 Testing matches-by-date endpoint...")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            url = "https://tennis-devs.p.rapidapi.com/matches-by-date"
            params = {
                "lang": "en",
                "offset": "0",
                "date": f"eq.{tomorrow}",
                "limit": "10",
            }

            logger.info(f"Using date parameter: {params['date']}")

            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        f"✅ Matches by date response: {len(data) if isinstance(data, list) else 'unknown'} matches found for {tomorrow}"
                    )

                    # Show first few matches
                    matches = (
                        data if isinstance(data, list) else data.get("matches", [])
                    )
                    for i, match in enumerate(matches[:3]):
                        home = match.get("home_team_name", "Unknown")
                        away = match.get("away_team_name", "Unknown")
                        date = match.get("date", "Unknown")
                        logger.info(f"  {i+1}. {home} vs {away} on {date}")

                        # Show raw match data for debugging
                        logger.info(f"     Raw match data: {match}")
                else:
                    logger.error(f"❌ Matches by date failed: {response.status}")
                    logger.error(await response.text())

        except Exception as e:
            logger.error(f"❌ Error testing Tennis Devs API: {e}")


async def main():
    """Run the test."""
    await test_tennis_devs_api()


if __name__ == "__main__":
    asyncio.run(main())
