#!/usr/bin/env python3
# scripts/sync_games.py

import asyncio
import logging
import os
from dotenv import load_dotenv
from services.game_service import GameService
from services.sports_api import SportsAPI
from data.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY not found in .env file")

async def main():
    """Main function to run the sync service."""
    try:
        # Initialize services
        db_manager = DatabaseManager()
        sports_api = SportsAPI()
        game_service = GameService(sports_api, db_manager)

        # Start the service
        if await game_service.start():
            logger.info("Sync service started successfully")
            
            # Keep the script running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
            finally:
                await game_service.stop()
                logger.info("Sync service stopped")
        else:
            logger.error("Failed to start sync service")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 