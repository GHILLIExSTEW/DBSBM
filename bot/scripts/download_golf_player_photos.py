#!/usr/bin/env python3
"""
Download golf player photos from Wikipedia and save to static/logos/players/golf/{league}/{player_name}.png
"""

import asyncio
import json
import logging
import os
import sys
import re
from urllib.parse import quote
import aiohttp
import aiofiles

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wikipedia API endpoints
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKIPEDIA_SEARCH_URL = "https://en.wikipedia.org/w/api.php"

# Base directory for saving photos
BASE_PHOTO_DIR = "static/logos/players/golf"

async def search_wikipedia_player(session: aiohttp.ClientSession, player_name: str) -> str:
    """Search Wikipedia for a player and return the page title if found."""
    try:
        # Clean player name for search
        search_name = player_name.split(',')[0] if ',' in player_name else player_name
        
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f"{search_name} golfer",
            "srlimit": 1
        }
        
        async with session.get(WIKIPEDIA_SEARCH_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("query", {}).get("search"):
                    return data["query"]["search"][0]["title"]
        return None
    except Exception as e:
        logger.error(f"Error searching Wikipedia for {player_name}: {e}")
        return None

async def get_wikipedia_image(session: aiohttp.ClientSession, page_title: str) -> str:
    """Get the main image URL from a Wikipedia page."""
    try:
        url = f"{WIKIPEDIA_API_URL}{quote(page_title)}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if "thumbnail" in data:
                    return data["thumbnail"]["source"]
        return None
    except Exception as e:
        logger.error(f"Error getting image for {page_title}: {e}")
        return None

async def download_image(session: aiohttp.ClientSession, image_url: str, file_path: str) -> bool:
    """Download an image and save it to the specified path."""
    try:
        async with session.get(image_url) as response:
            if response.status == 200:
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Download and save image
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(await response.read())
                return True
        return False
    except Exception as e:
        logger.error(f"Error downloading image to {file_path}: {e}")
        return False

def clean_filename(name: str) -> str:
    """Clean a player name for use as a filename."""
    # Remove special characters and replace spaces with underscores
    cleaned = re.sub(r'[<>:"/\\|?*]', '', name)
    cleaned = cleaned.replace(' ', '_')
    return cleaned

async def download_golf_player_photos():
    """Main function to download golf player photos."""
    logger.info("Starting golf player photo download...")
    
    # Load the player dict
    try:
        with open("datagolf_players_by_name.json", "r", encoding="utf-8") as f:
            players_dict = json.load(f)
    except FileNotFoundError:
        logger.error("datagolf_players_by_name.json not found. Run save_datagolf_players_dict.py first.")
        return
    
    logger.info(f"Loaded {len(players_dict)} players")
    
    # Create base directory
    os.makedirs(BASE_PHOTO_DIR, exist_ok=True)
    
    # Track progress
    total_players = len(players_dict)
    successful_downloads = 0
    failed_downloads = 0
    
    async with aiohttp.ClientSession() as session:
        for i, (player_name, player_data) in enumerate(players_dict.items(), 1):
            logger.info(f"Processing {i}/{total_players}: {player_name}")
            
            try:
                # Determine league (you might need to adjust this based on your data)
                # For now, let's use a default league or extract from player data
                league = "PGA_TOUR"  # Default, you can modify this logic
                
                # Search Wikipedia for the player
                page_title = await search_wikipedia_player(session, player_name)
                if not page_title:
                    logger.warning(f"No Wikipedia page found for {player_name}")
                    failed_downloads += 1
                    continue
                
                # Get the image URL
                image_url = await get_wikipedia_image(session, page_title)
                if not image_url:
                    logger.warning(f"No image found for {player_name}")
                    failed_downloads += 1
                    continue
                
                # Create file path
                clean_name = clean_filename(player_name)
                file_path = os.path.join(BASE_PHOTO_DIR, league, f"{clean_name}.png")
                
                # Download the image
                if await download_image(session, image_url, file_path):
                    logger.info(f"Successfully downloaded photo for {player_name}")
                    successful_downloads += 1
                    
                    # Update player data with photo path
                    players_dict[player_name]["photo_path"] = file_path
                else:
                    logger.warning(f"Failed to download photo for {player_name}")
                    failed_downloads += 1
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing {player_name}: {e}")
                failed_downloads += 1
    
    # Save updated player dict with photo paths
    with open("datagolf_players_by_name.json", "w", encoding="utf-8") as f:
        json.dump(players_dict, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Download complete! Successful: {successful_downloads}, Failed: {failed_downloads}")

if __name__ == "__main__":
    asyncio.run(download_golf_player_photos()) 