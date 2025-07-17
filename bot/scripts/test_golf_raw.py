#!/usr/bin/env python3
"""
Test script to see raw golf API response structure
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


async def test_golf_raw():
    """Test golf API and show raw response structure."""
    logger.info("=== GOLF RAW API TEST ===")

    async with MultiProviderAPI() as api:
        try:
            # Test golf events fetching with a broader date range
            params = {"start_date": "2025-01-01", "end_date": "2025-12-31"}

            logger.info("Making direct API call to golf events endpoint...")
            data = await api.make_request("golf", "/v1/events", params)

            logger.info(f"Raw API response type: {type(data)}")
            logger.info(
                f"Raw API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
            )

            if isinstance(data, dict):
                logger.info(f"Response structure: {json.dumps(data, indent=2)}")
            else:
                logger.info(f"Response: {data}")

        except Exception as e:
            logger.error(f"Error testing golf API: {e}")


if __name__ == "__main__":
    asyncio.run(test_golf_raw())
