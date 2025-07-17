#!/usr/bin/env python3
"""
Test script for the new golf API provider
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


async def test_golf_new():
    """Test the new golf API provider."""
    logger.info("=== NEW GOLF API TEST ===")

    async with MultiProviderAPI() as api:
        try:
            # Test golf events fetching with a date range
            params = {"start_date": "2024-10-01", "end_date": "2024-10-30"}

            logger.info("Making API call to new golf events endpoint...")
            data = await api.make_request("golf", "/v1/events", params)

            logger.info(f"API response type: {type(data)}")

            if isinstance(data, dict):
                logger.info(f"Response keys: {list(data.keys())}")
                logger.info(f"Response structure: {json.dumps(data, indent=2)}")
            elif isinstance(data, list):
                logger.info(f"Found {len(data)} events")
                if data:
                    logger.info(
                        f"First event structure: {json.dumps(data[0], indent=2)}"
                    )
            else:
                logger.info(f"Response: {data}")

        except Exception as e:
            logger.error(f"Error testing new golf API: {e}")


if __name__ == "__main__":
    asyncio.run(test_golf_new())
