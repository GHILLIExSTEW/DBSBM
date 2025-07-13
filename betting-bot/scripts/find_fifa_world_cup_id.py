#!/usr/bin/env python3
"""
Script to find the correct FIFA World Cup ID by searching through available leagues.
"""

import os
import sys
import asyncio
import aiohttp
import logging
from pathlib import Path

# Add the parent directory to sys.path for imports
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BASE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / 'logs' / 'find_fifa_world_cup_id.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    logger.error("ERROR: API_KEY not found in environment variables")
    sys.exit(1)

class FIFAWorldCupFinder:
    def __init__(self):
        self.api_key = API_KEY
        self.base_url = "https://v3.football.api-sports.io"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'x-apisports-key': self.api_key}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_leagues(self, search_term: str = "World Cup"):
        """Search for leagues containing the search term."""
        params = {
            'name': search_term
        }
        
        try:
            logger.info(f"Searching for leagues containing '{search_term}'...")
            url = f"{self.base_url}/leagues"
            
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if 'response' in data:
                    leagues = data['response']
                    logger.info(f"Found {len(leagues)} leagues matching '{search_term}'")
                    
                    for league in leagues:
                        league_info = league.get('league', {})
                        logger.info(f"League ID: {league_info.get('id')}")
                        logger.info(f"League Name: {league_info.get('name')}")
                        logger.info(f"League Type: {league_info.get('type')}")
                        logger.info(f"Country: {league_info.get('country')}")
                        logger.info("-" * 50)
                    
                    return leagues
                else:
                    logger.warning("No 'response' field in API response")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching leagues: {e}")
            return []
    
    async def get_league_teams(self, league_id: int, season: int = 2026):
        """Get teams for a specific league and season."""
        params = {
            'league': league_id,
            'season': season
        }
        
        try:
            logger.info(f"Getting teams for league {league_id}, season {season}...")
            url = f"{self.base_url}/teams"
            
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if 'response' in data:
                    teams = data['response']
                    logger.info(f"Found {len(teams)} teams")
                    
                    # Show first few teams
                    for i, team_data in enumerate(teams[:5]):
                        team = team_data.get('team', {})
                        logger.info(f"Team {i+1}: {team.get('name')} ({team.get('country')}) - National: {team.get('national')}")
                    
                    if len(teams) > 5:
                        logger.info(f"... and {len(teams) - 5} more teams")
                    
                    return teams
                else:
                    logger.warning("No 'response' field in API response")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            return []
    
    async def test_potential_ids(self):
        """Test potential FIFA World Cup IDs."""
        # Test a wider range of IDs that might be FIFA World Cup
        potential_ids = list(range(1, 50))  # Test IDs 1-49
        
        for league_id in potential_ids:
            logger.info(f"Testing league ID: {league_id}")
            teams = await self.get_league_teams(league_id, 2026)
            
            if teams:
                # Check if any teams are national teams
                national_teams = [t for t in teams if t.get('team', {}).get('national', False)]
                if national_teams:
                    logger.info(f"FOUND POTENTIAL FIFA WORLD CUP ID: {league_id}")
                    logger.info(f"Contains {len(national_teams)} national teams")
                    for team in national_teams[:5]:
                        team_info = team.get('team', {})
                        logger.info(f"  - {team_info.get('name')} ({team_info.get('country')})")
                    logger.info("-" * 50)
            
            await asyncio.sleep(0.5)  # Rate limiting

async def main():
    """Main function."""
    logger.info("Starting FIFA World Cup ID search...")
    
    async with FIFAWorldCupFinder() as finder:
        # Search for World Cup leagues
        await finder.search_leagues("World Cup")
        
        # Search for FIFA leagues
        await finder.search_leagues("FIFA")
        
        # Search for specific terms
        await finder.search_leagues("FIFA World Cup")
        await finder.search_leagues("World Cup 2026")
        
        # Test potential IDs
        await finder.test_potential_ids()

if __name__ == "__main__":
    asyncio.run(main()) 