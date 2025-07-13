#!/usr/bin/env python3
"""
Simple script to download FIFA Club World Cup team logos from existing data.
"""

import os
import sys
import asyncio
import aiohttp
import logging
import json
from pathlib import Path

# Add the parent directory to sys.path for imports
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from config.team_mappings import normalize_team_name
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / 'logs' / 'download_world_cup_logos.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Directories
STATIC_DIR = BASE_DIR / 'static'
LOGOS_DIR = STATIC_DIR / 'logos'
TEAMS_DIR = LOGOS_DIR / 'teams' / 'SOCCER' / 'WORLDCUP'
DATA_DIR = BASE_DIR / 'data'

# Create directories if they don't exist
TEAMS_DIR.mkdir(parents=True, exist_ok=True)

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

async def download_team_logos_from_data():
    """Download team logos from the existing 2022 data file."""
    json_file = DATA_DIR / 'fifa_world_cup_teams_2022.json'
    
    if not json_file.exists():
        logger.error(f"Data file not found: {json_file}")
        return
    
    # Load the teams data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    teams = data.get('teams', [])
    if not teams:
        logger.error("No teams found in data file")
        return
    
    logger.info(f"Found {len(teams)} teams to download logos for")
    
    async with LogoDownloader() as downloader:
        downloaded_count = 0
        
        for team_data in teams:
            team = team_data.get('team', {})
            team_name = team.get('name')
            logo_url = team.get('logo')
            
            if not team_name or not logo_url:
                logger.warning(f"Missing team name or logo URL for team: {team_data}")
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

async def main():
    """Main function."""
    logger.info("Starting FIFA Club World Cup logo download...")
    await download_team_logos_from_data()
    logger.info("Logo download completed!")

if __name__ == "__main__":
    asyncio.run(main()) 