#!/usr/bin/env python3
"""
Debug script to test the golf API specifically.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.multi_provider_api import MultiProviderAPI
from data.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def debug_golf_api():
    """Debug the golf API specifically."""

    # Initialize database manager
    logger.info("Initializing database manager...")
    db_manager = DatabaseManager()
    await db_manager.connect()

    try:
        # Initialize MultiProviderAPI
        logger.info("Initializing MultiProviderAPI...")
        async with MultiProviderAPI(db_manager.db) as api:

            logger.info("Testing golf API...")

            # Test the make_request method directly for golf
            try:
                logger.info("Testing direct golf API call...")

                # Test the events endpoint
                params = {
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": "2099-12-31",
                }

                logger.info(f"Making request with params: {params}")
                data = await api.make_request("golf", "/v1/events", params)

                logger.info(f"Golf API response: {data}")

                if data:
                    logger.info("✅ Golf API call successful!")

                    # Test parsing the response
                    leagues = api._parse_rapidapi_golf_leagues(data, "golf")
                    logger.info(f"Parsed {len(leagues)} golf leagues:")
                    for league in leagues[:5]:
                        logger.info(
                            f"  - {league.get('name')} (ID: {league.get('id')})"
                        )
                else:
                    logger.error("❌ Golf API returned no data")

            except Exception as e:
                logger.error(f"❌ Error testing golf API: {e}")
                import traceback

                traceback.print_exc()

            # Test the discover_leagues method
            try:
                logger.info("Testing golf league discovery...")
                leagues = await api.discover_leagues("golf")
                logger.info(f"Discovered {len(leagues)} golf leagues")

                if leagues:
                    for league in leagues[:5]:
                        logger.info(
                            f"  - {league.get('name')} (ID: {league.get('id')})"
                        )
                else:
                    logger.warning("No golf leagues discovered")

            except Exception as e:
                logger.error(f"❌ Error discovering golf leagues: {e}")
                import traceback

                traceback.print_exc()

    except Exception as e:
        logger.error(f"Error in debug: {e}")
        return False

    finally:
        await db_manager.close()

    return True


if __name__ == "__main__":
    asyncio.run(debug_golf_api())
