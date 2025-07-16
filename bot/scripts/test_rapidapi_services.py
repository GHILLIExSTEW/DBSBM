#!/usr/bin/env python3
"""
Test script to check popular RapidAPI sports services.
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

async def test_rapidapi_services():
    """Test popular RapidAPI sports services."""
    
    # Load environment variables
    load_dotenv()
    
    # Get RapidAPI key
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    if not rapidapi_key:
        logger.error("RAPIDAPI_KEY not found in environment variables")
        return
    
    logger.info(f"Testing RapidAPI key: {rapidapi_key[:10]}...")
    
    # Test popular RapidAPI sports services
    test_services = [
        {
            'name': 'API-Football (RapidAPI)',
            'url': 'https://api-football-v1.p.rapidapi.com/v3/leagues',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
            }
        },
        {
            'name': 'API-Basketball (RapidAPI)',
            'url': 'https://api-basketball.p.rapidapi.com/leagues',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'api-basketball.p.rapidapi.com'
            }
        },
        {
            'name': 'API-Hockey (RapidAPI)',
            'url': 'https://api-hockey.p.rapidapi.com/leagues',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'api-hockey.p.rapidapi.com'
            }
        },
        {
            'name': 'API-Baseball (RapidAPI)',
            'url': 'https://api-baseball.p.rapidapi.com/leagues',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'api-baseball.p.rapidapi.com'
            }
        },
        {
            'name': 'LiveScore API (RapidAPI)',
            'url': 'https://livescore6.p.rapidapi.com/matches/v2/list-live',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'livescore6.p.rapidapi.com'
            }
        },
        {
            'name': 'SportRadar API (RapidAPI)',
            'url': 'https://sportradar.usatoday.com/trial/v7/en/games/sr:trial:game:1030/boxscore.json?api_key=YOUR_API_KEY',
            'headers': {
                'X-RapidAPI-Key': rapidapi_key,
                'X-RapidAPI-Host': 'sportradar.usatoday.com'
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for service in test_services:
            try:
                logger.info(f"Testing {service['name']}...")
                
                async with session.get(
                    service['url'],
                    headers=service['headers'],
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    status = response.status
                    logger.info(f"{service['name']}: Status {status}")
                    
                    if status == 200:
                        try:
                            data = await response.json()
                            logger.info(f"{service['name']}: SUCCESS - Got {len(str(data))} characters of data")
                        except:
                            text = await response.text()
                            logger.info(f"{service['name']}: SUCCESS - Got {len(text)} characters of text")
                    elif status == 403:
                        logger.error(f"{service['name']}: FORBIDDEN - API key doesn't have access to this service")
                    elif status == 401:
                        logger.error(f"{service['name']}: UNAUTHORIZED - Invalid API key")
                    elif status == 404:
                        logger.warning(f"{service['name']}: NOT FOUND - Endpoint doesn't exist")
                    elif status == 429:
                        logger.warning(f"{service['name']}: RATE LIMITED - Too many requests")
                    else:
                        logger.warning(f"{service['name']}: Status {status} - {response.reason}")
                        
            except Exception as e:
                logger.error(f"{service['name']}: ERROR - {str(e)}")
            
            # Small delay between requests
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_rapidapi_services()) 