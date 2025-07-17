#!/usr/bin/env python3
"""
Debug script to see the actual darts API response structure.
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.multi_provider_api import MultiProviderAPI
from data.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_darts_api_response():
    """Debug the darts API response structure."""
    
    # Initialize database manager
    logger.info("Initializing database manager...")
    db_manager = DatabaseManager()
    await db_manager.connect()
    
    try:
        # Initialize MultiProviderAPI
        logger.info("Initializing MultiProviderAPI...")
        async with MultiProviderAPI(db_manager.db) as api:
            
            logger.info("Testing darts API response...")
            
            # Test the make_request method directly for darts
            try:
                logger.info("Testing direct darts API call...")
                
                # Test the tournaments endpoint
                params = {
                    "offset": "0",
                    "limit": "10",
                    "lang": "en"
                }
                
                logger.info(f"Making request with params: {params}")
                data = await api.make_request("darts", "/tournaments-by-league", params)
                
                logger.info(f"Darts API response type: {type(data)}")
                logger.info(f"Darts API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                if isinstance(data, list):
                    logger.info(f"Darts API response is a list with {len(data)} items")
                    if data:
                        logger.info(f"First item: {json.dumps(data[0], indent=2)}")
                elif isinstance(data, dict):
                    logger.info(f"Darts API response: {json.dumps(data, indent=2)}")
                else:
                    logger.info(f"Darts API response: {data}")
                
                # Test parsing
                if data:
                    logger.info("Testing darts league parsing...")
                    leagues = api._parse_rapidapi_darts_leagues(data, "darts")
                    logger.info(f"Parsed {len(leagues)} leagues")
                    
                    if leagues:
                        logger.info("First 5 parsed leagues:")
                        for i, league in enumerate(leagues[:5]):
                            logger.info(f"  {i+1}. {league}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing darts API: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        logger.error(f"Error in debug: {e}")
        return False
    
    finally:
        await db_manager.close()
    
    return True

if __name__ == "__main__":
    asyncio.run(debug_darts_api_response()) 