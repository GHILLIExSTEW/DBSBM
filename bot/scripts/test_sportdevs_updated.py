#!/usr/bin/env python3
"""
Test script for updated SportDevs API integration with proper query syntax.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.multi_provider_api import MultiProviderAPI
from utils.sportdevs_query_builder import endpoint, get_tournaments, get_matches_by_date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sportdevs_query_builder():
    """Test the SportDevs query builder."""
    logger.info("Testing SportDevs Query Builder...")
    
    # Test basic queries
    tournaments_query = get_tournaments(limit=10)
    logger.info(f"Tournaments query: {tournaments_query}")
    
    today = datetime.now().strftime("%Y-%m-%d")
    matches_query = get_matches_by_date(today, limit=10)
    logger.info(f"Matches query: {matches_query}")
    
    # Test complex query
    complex_query = endpoint("matches").property("date").equals(today).property("status").equals("scheduled").limit(20).build_url()
    logger.info(f"Complex query: {complex_query}")

async def test_sportdevs_apis():
    """Test SportDevs APIs with proper query syntax."""
    logger.info("Testing SportDevs APIs...")
    
    async with MultiProviderAPI() as api:
        # Test each SportDevs sport
        sportdevs_sports = ["darts", "esports", "tennis"]
        
        for sport in sportdevs_sports:
            logger.info(f"\n--- Testing {sport.upper()} ---")
            
            try:
                # Test league discovery
                logger.info(f"Discovering {sport} leagues...")
                leagues = await api.discover_leagues(sport)
                logger.info(f"Found {len(leagues)} {sport} leagues")
                
                if leagues:
                    # Show first few leagues
                    for i, league in enumerate(leagues[:3]):
                        logger.info(f"  {i+1}. {league['name']} (ID: {league['id']})")
                    
                    # Test fetching games for the first league
                    if leagues:
                        first_league = leagues[0]
                        today = datetime.now().strftime("%Y-%m-%d")
                        logger.info(f"Fetching games for {first_league['name']} on {today}...")
                        
                        games = await api.fetch_games(sport, first_league, today)
                        logger.info(f"Found {len(games)} games")
                        
                        if games:
                            for i, game in enumerate(games[:3]):
                                logger.info(f"  {i+1}. {game.get('home_team_name', 'Unknown')} vs {game.get('away_team_name', 'Unknown')}")
                else:
                    logger.warning(f"No leagues found for {sport}")
                    
            except Exception as e:
                logger.error(f"Error testing {sport}: {e}")

async def test_direct_sportdevs_calls():
    """Test direct SportDevs API calls to verify endpoints."""
    logger.info("Testing direct SportDevs API calls...")
    
    import aiohttp
    
    sportdevs_endpoints = {
        "darts": "https://darts.sportdevs.com",
        "esports": "https://esports.sportdevs.com", 
        "tennis": "https://tennis.sportdevs.com"
    }
    
    async with aiohttp.ClientSession() as session:
        for sport, base_url in sportdevs_endpoints.items():
            logger.info(f"\n--- Testing {sport.upper()} direct API ---")
            
            try:
                # Test tournaments endpoint
                tournaments_url = f"{base_url}/tournaments?limit=5"
                logger.info(f"Testing tournaments: {tournaments_url}")
                
                async with session.get(tournaments_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    logger.info(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Success! Got {len(str(data))} characters of data")
                        
                        # Try to parse tournaments
                        tournaments = data.get("tournaments", [])
                        logger.info(f"Found {len(tournaments)} tournaments")
                        
                        if tournaments:
                            for i, tournament in enumerate(tournaments[:3]):
                                logger.info(f"  {i+1}. {tournament.get('name', 'Unknown')} (ID: {tournament.get('id', 'Unknown')})")
                    else:
                        logger.error(f"Failed with status {response.status}: {response.reason}")
                        
            except Exception as e:
                logger.error(f"Error testing {sport} direct API: {e}")

async def main():
    """Run all tests."""
    logger.info("Starting SportDevs API tests...")
    
    # Test query builder
    await test_sportdevs_query_builder()
    
    # Test direct API calls
    await test_direct_sportdevs_calls()
    
    # Test multi-provider API integration
    await test_sportdevs_apis()
    
    logger.info("SportDevs API tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 