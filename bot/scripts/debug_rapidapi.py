#!/usr/bin/env python3
"""
Debug script to test RapidAPI connections and identify issues.
"""

import os
import sys
import asyncio
import aiohttp
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rapidapi_connection():
    """Test RapidAPI connection with detailed debugging."""

    # Load environment variables
    load_dotenv()

    # Get RapidAPI key
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    if not rapidapi_key:
        logger.error("RAPIDAPI_KEY not found in environment variables")
        return

    logger.info(f"Testing RapidAPI key: {rapidapi_key[:10]}...")

    # Test different RapidAPI endpoints with detailed debugging
    test_apis = [
        {
            "name": "Darts Devs API",
            "url": "https://darts-devs.p.rapidapi.com/tournaments",
            "host": "darts-devs.p.rapidapi.com",
            "description": "Darts tournaments and matches",
        },
        {
            "name": "API-Football (for comparison)",
            "url": "https://api-football-v1.p.rapidapi.com/v3/leagues",
            "host": "api-football-v1.p.rapidapi.com",
            "description": "Football leagues (should work if key is valid)",
        },
        {
            "name": "API-Basketball (for comparison)",
            "url": "https://api-basketball.p.rapidapi.com/leagues",
            "host": "api-basketball.p.rapidapi.com",
            "description": "Basketball leagues (should work if key is valid)",
        },
    ]

    async with aiohttp.ClientSession() as session:
        for api in test_apis:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing: {api['name']}")
            logger.info(f"Description: {api['description']}")
            logger.info(f"URL: {api['url']}")
            logger.info(f"Host: {api['host']}")

            headers = {
                "X-RapidAPI-Key": rapidapi_key,
                "X-RapidAPI-Host": api["host"],
                "Accept": "application/json",
            }

            logger.info(f"Headers: {headers}")

            try:
                async with session.get(
                    api["url"], headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    logger.info(f"Status Code: {response.status}")
                    logger.info(f"Status Text: {response.reason}")
                    logger.info(f"Response Headers: {dict(response.headers)}")

                    # Get response body
                    try:
                        response_text = await response.text()
                        logger.info(f"Response Length: {len(response_text)} characters")

                        if response.status == 200:
                            logger.info("✅ SUCCESS - API is working!")
                            try:
                                import json

                                data = json.loads(response_text)
                                logger.info(
                                    f"JSON Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
                                )
                            except:
                                logger.info("Response is not valid JSON")
                        elif response.status == 403:
                            logger.error("❌ FORBIDDEN - Possible causes:")
                            logger.error("  1. Not subscribed to this specific API")
                            logger.error("  2. Subscription expired or inactive")
                            logger.error("  3. API provider restricted access")
                            logger.error("  4. Wrong API host or endpoint")
                            logger.error("  5. Rate limit exceeded")
                            logger.error(
                                f"  6. Response body: {response_text[:200]}..."
                            )
                        elif response.status == 401:
                            logger.error("❌ UNAUTHORIZED - Invalid API key")
                        elif response.status == 429:
                            logger.error("❌ RATE LIMITED - Too many requests")
                        elif response.status == 404:
                            logger.error("❌ NOT FOUND - Endpoint doesn't exist")
                        else:
                            logger.error(f"❌ OTHER ERROR - Status {response.status}")
                            logger.error(f"Response body: {response_text[:200]}...")

                    except Exception as e:
                        logger.error(f"Error reading response: {e}")

            except Exception as e:
                logger.error(f"Request failed: {e}")

            # Small delay between requests
            await asyncio.sleep(1)


async def test_rapidapi_dashboard_info():
    """Test to get information about your RapidAPI account."""
    logger.info(f"\n{'='*60}")
    logger.info("RAPIDAPI ACCOUNT INFORMATION")
    logger.info("=" * 60)
    logger.info("To check your RapidAPI account:")
    logger.info("1. Go to: https://rapidapi.com/developer/dashboard")
    logger.info("2. Click on 'My Apps'")
    logger.info("3. Click on 'Subscriptions'")
    logger.info("4. Look for the APIs you're trying to use")
    logger.info("5. Check if they show as 'Active'")
    logger.info("6. Check the usage limits and current usage")
    logger.info("7. Check if there are any billing issues")


async def main():
    """Run all tests."""
    logger.info("Starting RapidAPI Debug Tests...")

    await test_rapidapi_connection()
    await test_rapidapi_dashboard_info()

    logger.info(f"\n{'='*60}")
    logger.info("DEBUG COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
