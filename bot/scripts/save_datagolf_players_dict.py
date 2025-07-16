#!/usr/bin/env python3
"""
Fetch DataGolf player list and save as a dict keyed by player_name.
"""

import asyncio
import json
import logging
import os
import sys

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.multi_provider_api import MultiProviderAPI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_FILE = "datagolf_players_by_name.json"

async def save_datagolf_players_dict():
    logger.info("Fetching DataGolf player list...")
    async with MultiProviderAPI() as api:
        players = await api.fetch_golf_players("json")
        if not players:
            logger.error("No players fetched from DataGolf.")
            return
        
        # Build dict keyed by player_name
        player_dict = {p["player_name"]: p for p in players if "player_name" in p}
        logger.info(f"Saving {len(player_dict)} players to {OUTPUT_FILE}")
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(player_dict, f, ensure_ascii=False, indent=2)
        logger.info("Done.")

if __name__ == "__main__":
    asyncio.run(save_datagolf_players_dict()) 