#!/usr/bin/env python3
"""
Test Golf API
Simple test script to verify the golf API implementation.
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


async def test_golf():
    """Test the golf API implementation."""
    logger.info("=== GOLF API TEST ===")

    async with MultiProviderAPI() as api:
        # Test league discovery
        logger.info("Testing golf league discovery...")
        try:
            leagues = await api.discover_leagues("golf")
            logger.info(f"Found {len(leagues)} golf tournaments")

            if leagues:
                logger.info("First 5 tournaments:")
                for i, league in enumerate(leagues[:5]):
                    logger.info(
                        f"  {i+1}. ID: {league.get('id')}, Name: {league.get('name')}, Country: {league.get('country')}"
                    )
            else:
                logger.info("No tournaments found")

        except Exception as e:
            logger.error(f"Error discovering golf tournaments: {e}")

        # Test fetching events
        logger.info("\nTesting golf events fetching...")
        try:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            dummy_league = {"id": "all", "name": "All Golf Tournaments"}

            events = await api.fetch_games("golf", dummy_league, date)
            logger.info(f"Found {len(events)} golf events for {date}")

            if events:
                logger.info("First event structure:")
                logger.info(json.dumps(events[0], indent=2))

        except Exception as e:
            logger.error(f"Error fetching golf events: {e}")


async def main():
    await test_golf()


if __name__ == "__main__":
    asyncio.run(main())
