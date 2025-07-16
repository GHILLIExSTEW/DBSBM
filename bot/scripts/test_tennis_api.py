#!/usr/bin/env python3
"""
Test Tennis API endpoints with SportDevs.
"""

import os
import sys
import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_tennis_api():
    """Test Tennis API endpoints."""
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Get tournaments (leagues)
            logger.info("🔍 Testing tournaments endpoint...")
            url = "https://tennis.sportdevs.com/tournaments"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Tournaments response: {len(data) if isinstance(data, list) else 'unknown'} tournaments found")
                    
                    # Show first few tournaments
                    tournaments = data if isinstance(data, list) else data.get('tournaments', [])
                    for i, tournament in enumerate(tournaments[:5]):
                        logger.info(f"  {i+1}. {tournament.get('name', 'Unknown')} (ID: {tournament.get('id', 'Unknown')})")
                else:
                    logger.error(f"❌ Tournaments failed: {response.status}")
                    logger.error(await response.text())
            
            # Test 2: Get matches for a specific tournament
            logger.info("\n🔍 Testing matches endpoint...")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # First get a tournament ID to test with
            if response.status == 200:
                tournaments = data if isinstance(data, list) else data.get('tournaments', [])
                if tournaments:
                    tournament_id = tournaments[0].get('id')
                    logger.info(f"Using tournament ID: {tournament_id}")
                    
                    # Test matches endpoint
                    url = "https://tennis.sportdevs.com/matches"
                    params = {
                        "tournament_id": tournament_id,
                        "date": f"gte.{tomorrow}"
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"✅ Matches response: {len(data) if isinstance(data, list) else 'unknown'} matches found")
                            
                            # Show first few matches
                            matches = data if isinstance(data, list) else data.get('matches', [])
                            for i, match in enumerate(matches[:3]):
                                home = match.get('home', {}).get('name', 'Unknown')
                                away = match.get('away', {}).get('name', 'Unknown')
                                date = match.get('date', 'Unknown')
                                logger.info(f"  {i+1}. {home} vs {away} on {date}")
                        else:
                            logger.error(f"❌ Matches failed: {response.status}")
                            logger.error(await response.text())
                else:
                    logger.error("❌ No tournaments found to test matches")
            else:
                logger.error("❌ Cannot test matches without tournaments")
                    
        except Exception as e:
            logger.error(f"❌ Error testing Tennis API: {e}")

async def main():
    """Run the test."""
    await test_tennis_api()

if __name__ == "__main__":
    asyncio.run(main()) 