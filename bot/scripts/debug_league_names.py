#!/usr/bin/env python3
"""
Debug League Names
Script to examine the actual match data structure and league information.
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime, timedelta

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_tennis_data():
    """Debug tennis match data structure."""
    logger.info("=== TENNIS DEBUG ===")
    
    async with MultiProviderAPI() as api:
        # Discover leagues
        logger.info("Discovering tennis leagues...")
        leagues = await api.discover_leagues("tennis")
        logger.info(f"Found {len(leagues)} tennis leagues")
        
        # Show first few leagues
        logger.info("First 5 leagues:")
        for i, league in enumerate(leagues[:5]):
            logger.info(f"  {i+1}. ID: {league.get('id')}, Name: {league.get('name')}, Country: {league.get('country')}")
        
        # Fetch matches
        logger.info("Fetching tennis matches...")
        dummy_league = {"id": "all", "name": "All Tennis Leagues"}
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        matches = await api.fetch_games("tennis", dummy_league, date)
        
        if matches:
            logger.info(f"Found {len(matches)} tennis matches")
            
            # Show first few matches with their structure
            logger.info("First 3 matches structure:")
            for i, match in enumerate(matches[:3]):
                logger.info(f"\nMatch {i+1}:")
                logger.info(f"  Raw match keys: {list(match.keys())}")
                logger.info(f"  Tournament ID: {match.get('tournament_id')}")
                logger.info(f"  League ID: {match.get('league_id')}")
                logger.info(f"  Tournament Name: {match.get('tournament_name')}")
                logger.info(f"  League Name: {match.get('league_name')}")
                logger.info(f"  Home Team: {match.get('home_team_name')}")
                logger.info(f"  Away Team: {match.get('away_team_name')}")
                
                # Check if there's a tournament object
                if 'tournament' in match:
                    logger.info(f"  Tournament object: {match['tournament']}")
        else:
            logger.info("No tennis matches found")

async def debug_darts_data():
    """Debug darts match data structure."""
    logger.info("\n=== DARTS DEBUG ===")
    
    async with MultiProviderAPI() as api:
        # Discover leagues
        logger.info("Discovering darts leagues...")
        leagues = await api.discover_leagues("darts")
        logger.info(f"Found {len(leagues)} darts leagues")
        
        # Show first few leagues
        logger.info("First 5 leagues:")
        for i, league in enumerate(leagues[:5]):
            logger.info(f"  {i+1}. ID: {league.get('id')}, Name: {league.get('name')}, Country: {league.get('country')}")
        
        # Fetch matches
        logger.info("Fetching darts matches...")
        dummy_league = {"id": "all", "name": "All Darts Leagues"}
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        matches = await api.fetch_games("darts", dummy_league, date)
        
        if matches:
            logger.info(f"Found {len(matches)} darts matches")
            
            # Show first few matches with their structure
            logger.info("First 3 matches structure:")
            for i, match in enumerate(matches[:3]):
                logger.info(f"\nMatch {i+1}:")
                logger.info(f"  Raw match keys: {list(match.keys())}")
                logger.info(f"  Tournament ID: {match.get('tournament_id')}")
                logger.info(f"  League ID: {match.get('league_id')}")
                logger.info(f"  Tournament Name: {match.get('tournament_name')}")
                logger.info(f"  League Name: {match.get('league_name')}")
                logger.info(f"  Home Team: {match.get('home_team_name')}")
                logger.info(f"  Away Team: {match.get('away_team_name')}")
                
                # Check if there's a tournament object
                if 'tournament' in match:
                    logger.info(f"  Tournament object: {match['tournament']}")
        else:
            logger.info("No darts matches found")

async def main():
    await debug_tennis_data()
    await debug_darts_data()

if __name__ == "__main__":
    asyncio.run(main()) 