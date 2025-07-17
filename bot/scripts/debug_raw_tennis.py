#!/usr/bin/env python3
"""
Debug Raw Tennis API Response
Script to examine the raw API response structure.
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


async def debug_raw_tennis():
    """Debug raw tennis API response."""
    logger.info("=== RAW TENNIS API DEBUG ===")

    async with MultiProviderAPI() as api:
        # Make a direct API request to see the raw response
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Get the endpoint config
        endpoint_config = api.get_endpoint_config("tennis")
        games_endpoint = endpoint_config.get("games")

        logger.info(f"Using endpoint: {games_endpoint}")

        # Make the raw request
        params = {
            "offset": "0",
            "limit": "10",  # Just get 10 matches for debugging
            "lang": "en",
            "date": f"eq.{date}",
        }

        logger.info(f"Making request with params: {params}")

        try:
            raw_data = await api.make_request("tennis", games_endpoint, params)
            logger.info(f"Raw API response type: {type(raw_data)}")
            logger.info(
                f"Raw API response keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}"
            )

            # Pretty print the first part of the response
            logger.info("Raw API response (first 1000 chars):")
            raw_json = json.dumps(raw_data, indent=2)
            logger.info(raw_json[:1000])

            # If it's a list, show the first item
            if isinstance(raw_data, list) and len(raw_data) > 0:
                logger.info("First item in response:")
                logger.info(json.dumps(raw_data[0], indent=2))

        except Exception as e:
            logger.error(f"Error making raw request: {e}")


async def debug_tennis_parsing():
    """Debug how the tennis parsing works."""
    logger.info("\n=== TENNIS PARSING DEBUG ===")

    async with MultiProviderAPI() as api:
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        dummy_league = {"id": "all", "name": "All Tennis Leagues"}

        # Get the raw matches
        matches = await api.fetch_games("tennis", dummy_league, date)

        if matches:
            logger.info(f"Found {len(matches)} matches after parsing")

            # Show the first match in detail
            first_match = matches[0]
            logger.info("First match after parsing:")
            logger.info(json.dumps(first_match, indent=2))

            # Check what fields are available
            logger.info("Available fields in first match:")
            for key, value in first_match.items():
                logger.info(f"  {key}: {value}")


async def main():
    await debug_raw_tennis()
    await debug_tennis_parsing()


if __name__ == "__main__":
    asyncio.run(main())
