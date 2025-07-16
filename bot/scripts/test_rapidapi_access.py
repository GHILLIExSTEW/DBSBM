#!/usr/bin/env python3
"""
Test script to check what RapidAPI services are accessible with the current API key.
"""

import os
import sys
import asyncio
import aiohttp
import logging
from dotenv import load_dotenv

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rapidapi_access():
    """Test different RapidAPI endpoints to see what's accessible."""
    
    # Load environment variables
    load_dotenv()
    
    # Get RapidAPI key
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    if not rapidapi_key:
        logger.error("RAPIDAPI_KEY not found in environment variables")
        return
    
    logger.info(f"Testing RapidAPI key: {rapidapi_key[:10]}...")
    
    # Test different RapidAPI endpoints
    test_endpoints = [
        {
            'name': 'Golf API (RapidAPI)',
            'url': 'https://golf-live-data.p.rapidapi.com/tournaments',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'golf-live-data.p.rapidapi.com'
            }
        },
        {
            'name': 'Darts API (RapidAPI)',
            'url': 'https://darts-devs.p.rapidapi.com/tournaments',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'darts-devs.p.rapidapi.com'
            }
        },
        {
            'name': 'Tennis API (RapidAPI)',
            'url': 'https://tennis-live-data.p.rapidapi.com/tournaments',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'tennis-live-data.p.rapidapi.com'
            }
        },
        {
            'name': 'Esports API (RapidAPI)',
            'url': 'https://esports-live-data.p.rapidapi.com/tournaments',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'esports-live-data.p.rapidapi.com'
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in test_endpoints:
            try:
                logger.info(f"Testing {endpoint['name']}...")
                
                async with session.get(
                    endpoint['url'],
                    headers=endpoint['headers'],
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    status = response.status
                    logger.info(f"{endpoint['name']}: Status {status}")
                    
                    if status == 200:
                        data = await response.json()
                        logger.info(f"{endpoint['name']}: SUCCESS - Got {len(str(data))} characters of data")
                    elif status == 403:
                        logger.error(f"{endpoint['name']}: FORBIDDEN - API key doesn't have access to this service")
                    elif status == 401:
                        logger.error(f"{endpoint['name']}: UNAUTHORIZED - Invalid API key")
                    elif status == 404:
                        logger.warning(f"{endpoint['name']}: NOT FOUND - Endpoint doesn't exist")
                    else:
                        logger.warning(f"{endpoint['name']}: Status {status} - {response.reason}")
                        
            except Exception as e:
                logger.error(f"{endpoint['name']}: ERROR - {str(e)}")
            
            # Small delay between requests
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_rapidapi_access()) 