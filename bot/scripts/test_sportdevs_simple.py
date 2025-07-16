#!/usr/bin/env python3
"""
Simple test to check SportDevs API accessibility.
"""

import asyncio
import aiohttp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sportdevs_endpoints():
    """Test various SportDevs endpoints to see what's accessible."""
    
    sportdevs_endpoints = {
        "darts": "https://darts.sportdevs.com",
        "esports": "https://esports.sportdevs.com", 
        "tennis": "https://tennis.sportdevs.com"
    }
    
    # Test different endpoints for each sport
    test_paths = [
        "/",
        "/health",
        "/status",
        "/api",
        "/v1",
        "/tournaments",
        "/leagues",
        "/matches",
        "/teams",
        "/players"
    ]
    
    async with aiohttp.ClientSession() as session:
        for sport, base_url in sportdevs_endpoints.items():
            logger.info(f"\n=== Testing {sport.upper()} ===")
            
            for path in test_paths:
                url = f"{base_url}{path}"
                try:
                    logger.info(f"Testing: {url}")
                    
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        logger.info(f"  Status: {response.status}")
                        
                        if response.status == 200:
                            try:
                                data = await response.json()
                                logger.info(f"  Success! JSON response with {len(str(data))} characters")
                            except:
                                text = await response.text()
                                logger.info(f"  Success! Text response with {len(text)} characters")
                        elif response.status == 404:
                            logger.info(f"  Not found (expected for some endpoints)")
                        elif response.status == 500:
                            logger.info(f"  Server error")
                        else:
                            logger.info(f"  Other status: {response.reason}")
                            
                except Exception as e:
                    logger.error(f"  Error: {e}")
                
                # Small delay between requests
                await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(test_sportdevs_endpoints()) 