#!/usr/bin/env python3
"""
League Discovery Script
Discovers all available leagues from API-Sports and updates the configuration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the bot directory to the Python path
bot_dir = Path(__file__).parent.parent
sys.path.insert(0, str(bot_dir))

from utils.league_discovery import LeagueDiscovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("league_discovery.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to discover all leagues."""
    logger.info("Starting comprehensive league discovery...")
    
    try:
        async with LeagueDiscovery() as discoverer:
            # Discover all leagues
            discovered_leagues = await discoverer.discover_all_leagues()
            
            if not discovered_leagues:
                logger.error("No leagues discovered!")
                return False
            
            # Save to JSON file
            await discoverer.save_discovered_leagues(discovered_leagues, "discovered_leagues.json")
            
            # Update configuration file
            config_updated = await discoverer.update_league_config(
                discovered_leagues, 
                "bot/config/leagues.py"
            )
            
            if not config_updated:
                logger.error("Failed to update configuration file!")
                return False
            
            # Print summary
            total_leagues = sum(len(leagues) for leagues in discovered_leagues.values())
            logger.info(f"Discovery complete! Found {total_leagues} leagues across {len(discovered_leagues)} sports")
            
            # Print breakdown by sport
            for sport, leagues in discovered_leagues.items():
                logger.info(f"  {sport.title()}: {len(leagues)} leagues")
            
            return True
            
    except Exception as e:
        logger.error(f"Error during league discovery: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("League discovery completed successfully!")
        sys.exit(0)
    else:
        logger.error("League discovery failed!")
        sys.exit(1) 