#!/usr/bin/env python3
"""
Debug Golf API
Script to test the golf API and understand its data structure.
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime, timedelta

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def debug_golf_api():
    """Debug golf API responses."""
    logger.info("=== GOLF API DEBUG ===")

    async with MultiProviderAPI() as api:
        # Test league discovery
        logger.info("Testing golf league discovery...")
        try:
            leagues = await api.discover_leagues("golf")
            logger.info(f"Found {len(leagues)} golf leagues")

            if leagues:
                logger.info("First 5 leagues:")
                for i, league in enumerate(leagues[:5]):
                    logger.info(
                        f"  {i+1}. ID: {league.get('id')}, Name: {league.get('name')}, Country: {league.get('country')}"
                    )
            else:
                logger.info("No leagues found")

        except Exception as e:
            logger.error(f"Error discovering golf leagues: {e}")

        # Test fetching events/games
        logger.info("\nTesting golf events fetching...")
        try:
            # Get the endpoint config
            endpoint_config = api.get_endpoint_config("golf")
            games_endpoint = endpoint_config.get("games")

            logger.info(f"Using endpoint: {games_endpoint}")

            # Make a test request
            today = datetime.now().strftime("%Y-%m-%d")
            params = {"start_date": today, "end_date": "2099-12-31"}

            logger.info(f"Making request with params: {params}")

            raw_data = await api.make_request("golf", games_endpoint, params)
            logger.info(f"Raw API response type: {type(raw_data)}")

            if isinstance(raw_data, dict):
                logger.info(f"Raw API response keys: {list(raw_data.keys())}")
            elif isinstance(raw_data, list):
                logger.info(f"Raw API response is a list with {len(raw_data)} items")

            # Pretty print the first part of the response
            logger.info("Raw API response (first 1000 chars):")
            raw_json = json.dumps(raw_data, indent=2)
            logger.info(raw_json[:1000])

            # If it's a list, show the first item
            if isinstance(raw_data, list) and len(raw_data) > 0:
                logger.info("First item in response:")
                logger.info(json.dumps(raw_data[0], indent=2))
            elif isinstance(raw_data, dict) and "events" in raw_data:
                events = raw_data["events"]
                if events and len(events) > 0:
                    logger.info("First event in response:")
                    logger.info(json.dumps(events[0], indent=2))

        except Exception as e:
            logger.error(f"Error fetching golf events: {e}")

        # Test the full fetch_games method
        logger.info("\nTesting full fetch_games method...")
        try:
            dummy_league = {"id": "all", "name": "All Golf Leagues"}
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            matches = await api.fetch_games("golf", dummy_league, date)
            logger.info(f"Found {len(matches)} golf matches/events")

            if matches:
                logger.info("First match structure:")
                logger.info(json.dumps(matches[0], indent=2))

        except Exception as e:
            logger.error(f"Error in fetch_games: {e}")


async def main():
    await debug_golf_api()


if __name__ == "__main__":
    asyncio.run(main())
