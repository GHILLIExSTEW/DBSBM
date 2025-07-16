#!/usr/bin/env python3
"""
Check API Usage
Script to check current API usage and help identify what might be causing high request counts.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_api_usage():
    """Check current API usage and rate limiting status."""
    logger.info("=== API USAGE CHECK ===")
    
    async with MultiProviderAPI() as api:
        # Check rate limiter status
        logger.info("Current rate limiter status:")
        for provider, limiter in api.rate_limiter.limiters.items():
            calls_count = len(limiter["calls"])
            limit = limiter["limit"]
            logger.info(f"  {provider}: {calls_count}/{limit} calls in the last minute")
        
        # Test a simple darts request to see current status
        logger.info("\nTesting current darts API status...")
        try:
            # Make a minimal test request
            endpoint_config = api.get_endpoint_config("darts")
            leagues_endpoint = endpoint_config.get("leagues")
            
            if leagues_endpoint:
                logger.info(f"Making test request to: {leagues_endpoint}")
                data = await api.make_request("darts", leagues_endpoint, None)
                
                if data:
                    logger.info("✅ Darts API is working")
                    if isinstance(data, list):
                        logger.info(f"   Found {len(data)} leagues/tournaments")
                    elif isinstance(data, dict):
                        logger.info(f"   Response keys: {list(data.keys())}")
                else:
                    logger.info("⚠️  Darts API returned empty response")
                    
        except Exception as e:
            logger.error(f"❌ Darts API error: {e}")
        
        # Check rate limiter again after the test
        logger.info("\nRate limiter status after test:")
        for provider, limiter in api.rate_limiter.limiters.items():
            calls_count = len(limiter["calls"])
            limit = limiter["limit"]
            logger.info(f"  {provider}: {calls_count}/{limit} calls in the last minute")

async def main():
    await check_api_usage()

if __name__ == "__main__":
    asyncio.run(main()) 