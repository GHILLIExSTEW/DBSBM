#!/usr/bin/env python3
"""
FIFA World Cup Data Fetcher
Fetches teams, logos, and other data for FIFA World Cup from API-Sports.
"""

import os
import sys
import json
import asyncio
import aiohttp
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import csv

# Add the parent directory to sys.path for imports
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from config.leagues import LEAGUE_IDS, ENDPOINTS
    from config.team_mappings import normalize_team_name
    from config.asset_paths import get_sport_category_for_path
    from data.db_manager import DatabaseManager
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / 'logs' / 'fifa_world_cup_fetch.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    logger.error("API_KEY not found in environment variables")
    sys.exit(1)

# FIFA World Cup configuration
WORLDCUP_CONFIG = {
    'league_id': '15',
    'sport': 'football',
    'name': 'FIFA World Cup',
    'league_key': 'WorldCup'
}

# Directories
STATIC_DIR = BASE_DIR / 'static'
LOGOS_DIR = STATIC_DIR / 'logos'
TEAMS_DIR = LOGOS_DIR / 'teams' / 'SOCCER' / 'WORLDCUP'
LEAGUES_DIR = LOGOS_DIR / 'leagues' / 'SOCCER'
DATA_DIR = BASE_DIR / 'data'

# Create directories if they don't exist
TEAMS_DIR.mkdir(parents=True, exist_ok=True)
LEAGUES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

class FIFAWorldCupFetcher:
    def __init__(self):
        self.api_key = API_KEY
        self.base_url = ENDPOINTS['football']
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'x-apisports-key': self.api_key}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling and rate limiting."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
            
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        try:
            logger.info(f"Making request to: {url}")
            logger.debug(f"Parameters: {params}")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    logger.warning("Rate limit hit, waiting 60 seconds...")
                    await asyncio.sleep(60)
                    return await self.make_request(endpoint, params)
                    
                response.raise_for_status()
                data = await response.json()
                
                # Check for API errors
                if 'errors' in data and data['errors']:
                    error_msg = ', '.join(f"{k}: {v}" for k, v in data['errors'].items())
                    logger.error(f"API returned errors: {error_msg}")
                    return None
                    
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    async def fetch_league_info(self) -> Optional[Dict]:
        """Fetch FIFA World Cup league information."""
        params = {
            'id': WORLDCUP_CONFIG['league_id'],
            'season': 2025  # 2025 Club World Cup
        }
        
        data = await self.make_request('leagues', params)
        if data and 'response' in data and data['response']:
            league_info = data['response'][0]
            logger.info(f"Fetched league info: {league_info.get('league', {}).get('name')}")
            return league_info
        return None
    
    async def fetch_teams(self, season: int = 2025) -> List[Dict]:
        """Fetch all teams participating in FIFA World Cup."""
        params = {
            'league': WORLDCUP_CONFIG['league_id'],
            'season': season
        }
        
        data = await self.make_request('teams', params)
        if data and 'response' in data:
            teams = data['response']
            logger.info(f"Fetched {len(teams)} teams for FIFA Club World Cup {season}")
            return teams
        return []
    
    async def fetch_seasons(self) -> List[Dict]:
        """Fetch available seasons for FIFA World Cup."""
        params = {
            'league': WORLDCUP_CONFIG['league_id']
        }
        
        data = await self.make_request('seasons', params)
        if data and 'response' in data:
            seasons = data['response']
            logger.info(f"Fetched {len(seasons)} seasons for FIFA World Cup")
            return seasons
        return []
    
    async def fetch_standings(self, season: int = 2026) -> List[Dict]:
        """Fetch current standings for FIFA World Cup."""
        params = {
            'league': WORLDCUP_CONFIG['league_id'],
            'season': season
        }
        
        data = await self.make_request('standings', params)
        if data and 'response' in data:
            standings = data['response']
            logger.info(f"Fetched standings for FIFA World Cup {season}")
            return standings
        return []
    
    async def fetch_fixtures(self, season: int = 2026, date: str = None) -> List[Dict]:
        """Fetch fixtures for FIFA World Cup."""
        params = {
            'league': WORLDCUP_CONFIG['league_id'],
            'season': season
        }
        if date:
            params['date'] = date
            
        data = await self.make_request('fixtures', params)
        if data and 'response' in data:
            fixtures = data['response']
            logger.info(f"Fetched {len(fixtures)} fixtures for FIFA World Cup {season}")
            return fixtures
        return []

class LogoDownloader:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def download_logo(self, url: str, save_path: Path) -> bool:
        """Download and save a logo image."""
        if not url or not url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid logo URL: {url}")
            return False
            
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
                # Save the image
                save_path.write_bytes(content)
                logger.info(f"Downloaded logo: {save_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error downloading logo from {url}: {e}")
            return False

async def save_teams_to_csv(teams: List[Dict], filename: str):
    """Save teams data to CSV file."""
    csv_path = DATA_DIR / filename
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'team_id', 'team_name', 'team_code', 'country', 'founded', 
            'national', 'logo_url', 'venue_name', 'venue_city', 'venue_capacity'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for team_data in teams:
            team = team_data.get('team', {})
            venue = team_data.get('venue', {})
            
            row = {
                'team_id': team.get('id'),
                'team_name': team.get('name'),
                'team_code': team.get('code'),
                'country': team.get('country'),
                'founded': team.get('founded'),
                'national': team.get('national'),
                'logo_url': team.get('logo'),
                'venue_name': venue.get('name'),
                'venue_city': venue.get('city'),
                'venue_capacity': venue.get('capacity')
            }
            writer.writerow(row)
    
    logger.info(f"Saved {len(teams)} teams to {csv_path}")

async def download_team_logos(teams: List[Dict]):
    """Download team logos."""
    async with LogoDownloader() as downloader:
        downloaded_count = 0
        
        for team_data in teams:
            team = team_data.get('team', {})
            team_name = team.get('name')
            logo_url = team.get('logo')
            
            if not team_name or not logo_url:
                continue
                
            # Normalize team name for filename
            normalized_name = normalize_team_name(team_name.lower().replace(' ', '_'))
            logo_filename = f"{normalized_name}.png"
            logo_path = TEAMS_DIR / logo_filename
            
            # Skip if already exists
            if logo_path.exists():
                logger.info(f"Logo already exists: {logo_path}")
                downloaded_count += 1
                continue
                
            # Download logo
            if await downloader.download_logo(logo_url, logo_path):
                downloaded_count += 1
                await asyncio.sleep(0.5)  # Rate limiting
        
        logger.info(f"Downloaded {downloaded_count} team logos")

async def download_league_logo(league_info: Dict):
    """Download FIFA World Cup league logo."""
    if not league_info:
        return
        
    league = league_info.get('league', {})
    logo_url = league.get('logo')
    
    if not logo_url:
        logger.warning("No league logo URL found")
        return
        
    async with LogoDownloader() as downloader:
        logo_filename = "worldcup.png"
        logo_path = LEAGUES_DIR / logo_filename
        
        if await downloader.download_logo(logo_url, logo_path):
            logger.info(f"Downloaded league logo: {logo_path}")

async def save_data_to_json(data: Dict, filename: str):
    """Save data to JSON file."""
    json_path = DATA_DIR / filename
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved data to {json_path}")

async def insert_games_to_db(games: List[Dict], db_manager, season: int = 2025):
    """Insert or update games into the api_games table."""
    logger.info(f"Inserting {len(games)} games into api_games table for WorldCup {season}")
    for game in games:
        try:
            fixture = game.get('fixture', {})
            league = game.get('league', {})
            teams = game.get('teams', {})
            home = teams.get('home', {})
            away = teams.get('away', {})
            status = fixture.get('status', {}).get('short', 'scheduled')
            score = game.get('score', {})
            game_data = {
                'id': str(fixture.get('id')),
                'api_game_id': str(fixture.get('id')),
                'sport': 'football',
                'league_id': '15',
                'league_name': 'WorldCup',
                'season': season,
                'home_team_id': home.get('id'),
                'away_team_id': away.get('id'),
                'home_team_name': home.get('name'),
                'away_team_name': away.get('name'),
                'start_time': fixture.get('date'),
                'end_time': None,
                'status': status,
                'score': score,
                'venue': fixture.get('venue', {}).get('name'),
                'referee': fixture.get('referee'),
                'raw_json': game,
                'fetched_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            }
            await db_manager.upsert_api_game(game_data)
            logger.info(f"Inserted/updated game {game_data['id']} ({home.get('name')} vs {away.get('name')})")
        except Exception as e:
            logger.error(f"Error inserting game: {e}")

async def main():
    """Main function to fetch all FIFA World Cup data."""
    logger.info("Starting FIFA World Cup data fetch...")
    
    async with FIFAWorldCupFetcher() as fetcher:
        # Fetch league information
        logger.info("Fetching league information...")
        league_info = await fetcher.fetch_league_info()
        if league_info:
            await save_data_to_json(league_info, 'fifa_world_cup_league.json')
            await download_league_logo(league_info)
        
        # Fetch available seasons
        logger.info("Fetching available seasons...")
        seasons = await fetcher.fetch_seasons()
        if seasons:
            await save_data_to_json({'seasons': seasons}, 'fifa_world_cup_seasons.json')
        
        # Fetch teams for 2025
        logger.info("Fetching teams for 2025 World Cup...")
        teams_2025 = await fetcher.fetch_teams(season=2025)
        if teams_2025:
            await save_teams_to_csv(teams_2025, 'fifa_world_cup_teams_2025.csv')
            await save_data_to_json({'teams': teams_2025}, 'fifa_world_cup_teams_2025.json')
            await download_team_logos(teams_2025)
        
        # Fetch standings for 2026
        logger.info("Fetching standings for 2026 World Cup...")
        standings_2026 = await fetcher.fetch_standings(2026)
        if standings_2026:
            await save_data_to_json({'standings': standings_2026}, 'fifa_world_cup_standings_2026.json')
        
        # Fetch fixtures for 2026
        logger.info("Fetching fixtures for 2026 World Cup...")
        fixtures_2026 = await fetcher.fetch_fixtures(2026)
        if fixtures_2026:
            await save_data_to_json({'fixtures': fixtures_2026}, 'fifa_world_cup_fixtures_2026.json')
        
        # Fetch fixtures for 2025
        logger.info("Fetching fixtures for 2025 Club World Cup...")
        fixtures_2025 = await fetcher.fetch_fixtures(season=2025)
        await save_data_to_json({'fixtures': fixtures_2025}, 'fifa_world_cup_fixtures_2025.json')
        # Insert games into api_games table
        db_manager = DatabaseManager()
        await db_manager.connect()
        await insert_games_to_db(fixtures_2025, db_manager, season=2025)
        await db_manager.close()
        logger.info("Inserted all 2025 Club World Cup games into api_games table.")
    
    logger.info("FIFA World Cup data fetch completed!")

if __name__ == "__main__":
    asyncio.run(main()) 