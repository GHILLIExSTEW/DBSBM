#!/usr/bin/env python3
"""
Test Darts Devs API endpoints with proper parameters.
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

async def test_darts_devs_api():
    """Test Darts Devs API endpoints."""
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        logger.warning("⚠️ RAPIDAPI_KEY not found in environment variables")
        api_key = input("Please enter your RapidAPI key: ").strip()
        if not api_key:
            logger.error("❌ No API key provided")
            return
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "darts-devs.p.rapidapi.com"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Get tournaments by league
            logger.info("🔍 Testing tournaments-by-league endpoint...")
            url = "https://darts-devs.p.rapidapi.com/tournaments-by-league"
            params = {
                "offset": "0",
                "limit": "10",
                "lang": "en",
                "league_id": "eq.2875"  # Using the league_id from your example
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Tournaments by league response: {len(data) if isinstance(data, list) else 'unknown'} tournaments found")
                    
                    # Handle both list and dict responses
                    tournaments = data if isinstance(data, list) else data.get('tournaments', [])
                    
                    # Show first few tournaments
                    for i, tournament in enumerate(tournaments[:3]):
                        logger.info(f"  {i+1}. {tournament.get('name', 'Unknown')} (ID: {tournament.get('id', 'Unknown')})")
                else:
                    logger.error(f"❌ Tournaments by league failed: {response.status}")
                    logger.error(await response.text())
            
            # Test 2: Get seasons
            logger.info("\n🔍 Testing seasons endpoint...")
            url = "https://darts-devs.p.rapidapi.com/seasons"
            params = {
                "lang": "en",
                "offset": "0",
                "league_id": "eq.4192",
                "limit": "10",
                "id": "eq.56528"
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Seasons response: {len(data) if isinstance(data, list) else 'unknown'} seasons found")
                    
                    # Handle both list and dict responses
                    seasons = data if isinstance(data, list) else data.get('seasons', [])
                    
                    # Show first few seasons
                    for i, season in enumerate(seasons[:3]):
                        logger.info(f"  {i+1}. {season.get('name', 'Unknown')} (ID: {season.get('id', 'Unknown')})")
                else:
                    logger.error(f"❌ Seasons failed: {response.status}")
                    logger.error(await response.text())
            
            # Test 3: Get matches by date (tomorrow)
            logger.info("\n🔍 Testing matches-by-date endpoint...")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            url = "https://darts-devs.p.rapidapi.com/matches-by-date"
            params = {
                "offset": "0",
                "limit": "10",
                "lang": "en",
                "date": f"eq.{tomorrow}"  # Use eq. prefix like other endpoints
            }
            
            logger.info(f"Using date parameter: {params['date']}")
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Matches by date response: {len(data) if isinstance(data, list) else 'unknown'} matches found for {tomorrow}")
                    
                    # Handle both list and dict responses
                    matches = data if isinstance(data, list) else data.get('matches', [])
                    
                    # Show first few matches
                    for i, match in enumerate(matches[:3]):
                        # Handle the nested structure where each item has a 'matches' array
                        if 'matches' in match:
                            # This is a date group with matches
                            date = match.get('date', 'Unknown')
                            logger.info(f"  {i+1}. Date: {date}")
                            
                            # Show first few matches for this date
                            for j, game in enumerate(match['matches'][:2]):
                                home = game.get('home_team_name', 'Unknown')
                                away = game.get('away_team_name', 'Unknown')
                                start_time = game.get('start_time', 'Unknown')
                                league = game.get('league_name', 'Unknown')
                                logger.info(f"     {j+1}. {home} vs {away}")
                                logger.info(f"        League: {league}")
                                logger.info(f"        Start: {start_time}")
                        else:
                            # This is a direct match
                            home = match.get('home_team_name', 'Unknown')
                            away = match.get('away_team_name', 'Unknown')
                            date = match.get('date', 'Unknown')
                            logger.info(f"  {i+1}. {home} vs {away} on {date}")
                else:
                    logger.error(f"❌ Matches by date failed: {response.status}")
                    logger.error(await response.text())
                    
        except Exception as e:
            logger.error(f"❌ Error testing Darts Devs API: {e}")

async def main():
    """Run the test."""
    await test_darts_devs_api()

if __name__ == "__main__":
    asyncio.run(main()) 