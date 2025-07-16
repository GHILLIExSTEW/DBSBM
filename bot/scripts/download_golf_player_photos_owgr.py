#!/usr/bin/env python3
"""
Official World Golf Ranking (OWGR) player photo downloader
"""

import asyncio
import json
import logging
import os
import sys
import re
from urllib.parse import quote, urljoin
import aiohttp
import aiofiles
from PIL import Image
import io
from datetime import datetime
from bs4 import BeautifulSoup

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OWGR URLs
OWGR_SEARCH_URL = "https://www.owgr.com/ranking"
OWGR_BASE_URL = "https://www.owgr.com"

# Base directory for saving photos
BASE_PHOTO_DIR = "static/logos/players/golf"

# Quality filters
MIN_WIDTH = 200
MIN_HEIGHT = 200
MAX_WIDTH = 2000
MAX_HEIGHT = 2000
MIN_ASPECT_RATIO = 0.5
MAX_ASPECT_RATIO = 2.0

def is_valid_person_image(image_data: bytes) -> tuple[bool, dict]:
    """Check if the image is likely a valid person photo."""
    try:
        img = Image.open(io.BytesIO(image_data))
        width, height = img.size
        
        metadata = {
            'width': width,
            'height': height,
            'format': img.format,
            'mode': img.mode,
            'file_size': len(image_data)
        }
        
        # Basic dimension checks
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            return False, metadata
        if width > MAX_WIDTH or height > MAX_HEIGHT:
            return False, metadata
            
        # Aspect ratio check
        aspect_ratio = width / height
        if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
            return False, metadata
            
        # Minimum area check
        if width * height < 40000:  # 200x200 minimum area
            return False, metadata
            
        return True, metadata
        
    except Exception as e:
        logger.warning(f"Error validating image: {e}")
        return False, {'error': str(e)}

async def search_owgr_player(session: aiohttp.ClientSession, player_name: str) -> list[str]:
    """Search OWGR for a player and return profile URLs."""
    try:
        # Clean player name for search
        search_name = player_name.split(',')[0] if ',' in player_name else player_name
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # First, get the main ranking page
        async with session.get(OWGR_SEARCH_URL, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                profile_urls = []
                
                # Look for player links in the ranking table
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    # Look for player profile patterns
                    if '/player/' in href.lower() or '/ranking/' in href.lower():
                        # Check if this link contains the player name
                        if search_name.lower() in text.lower():
                            full_url = urljoin(OWGR_BASE_URL, href)
                            if full_url not in profile_urls:
                                profile_urls.append(full_url)
                                logger.info(f"Found OWGR profile for {player_name}: {full_url}")
                
                return profile_urls[:3]  # Limit to 3 profile URLs
        
        return []
    except Exception as e:
        logger.error(f"Error searching OWGR for {player_name}: {e}")
        return []

async def get_player_photos_from_owgr_profile(session: aiohttp.ClientSession, profile_url: str) -> list[tuple[str, dict]]:
    """Extract player photos from an OWGR profile page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        async with session.get(profile_url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                image_urls = []
                
                # Look for images on the page
                images = soup.find_all('img')
                for img in images:
                    src = img.get('src', '')
                    if src:
                        # Convert relative URLs to absolute
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = urljoin(OWGR_BASE_URL, src)
                        
                        # Skip small images and icons
                        if any(skip in src.lower() for skip in ['icon', 'logo', 'thumb', 'avatar', 'flag']):
                            continue
                        
                        # Download and validate the image
                        try:
                            async with session.get(src, headers=headers) as img_response:
                                if img_response.status == 200:
                                    image_data = await img_response.read()
                                    is_valid, metadata = is_valid_person_image(image_data)
                                    if is_valid:
                                        image_urls.append((src, metadata))
                                        logger.info(f"Found valid image: {src}")
                        except Exception as e:
                            logger.debug(f"Error downloading image {src}: {e}")
                
                return image_urls
        
        return []
    except Exception as e:
        logger.error(f"Error getting photos from {profile_url}: {e}")
        return []

async def download_image(session: aiohttp.ClientSession, image_url: str, file_path: str, metadata: dict) -> bool:
    """Download an image and save it to the specified path."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        async with session.get(image_url, headers=headers) as response:
            if response.status == 200:
                image_data = await response.read()
                
                # Final validation
                is_valid, final_metadata = is_valid_person_image(image_data)
                if not is_valid:
                    return False
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save image
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(image_data)
                
                # Save metadata
                metadata_file = file_path.replace('.png', '_metadata.json')
                async with aiofiles.open(metadata_file, 'w') as f:
                    await f.write(json.dumps(final_metadata, indent=2, default=str))
                
                return True
        return False
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return False

def clean_filename(name: str) -> str:
    """Clean a player name for use as a filename."""
    cleaned = re.sub(r'[<>:"/\\|?*]', '', name)
    cleaned = cleaned.replace(' ', '_')
    return cleaned

async def download_golf_player_photos_owgr():
    """Main function to download golf player photos from OWGR."""
    logger.info("Starting OWGR player photo download...")
    
    # Load the player dict
    try:
        with open("datagolf_players_by_name.json", "r", encoding="utf-8") as f:
            players_dict = json.load(f)
    except FileNotFoundError:
        logger.error("datagolf_players_by_name.json not found.")
        return
    
    logger.info(f"Loaded {len(players_dict)} players")
    
    # Create base directory
    os.makedirs(BASE_PHOTO_DIR, exist_ok=True)
    
    # Track progress
    total_players = len(players_dict)
    successful_downloads = 0
    failed_downloads = 0
    
    # Create session with longer timeout
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, (player_name, player_data) in enumerate(players_dict.items(), 1):
            logger.info(f"Processing {i}/{total_players}: {player_name}")
            
            try:
                # Skip if already has a photo
                if player_data.get("photo_path") and os.path.exists(player_data["photo_path"]):
                    logger.info(f"Skipping {player_name} - already has photo")
                    continue
                
                # Search for player profiles
                profile_urls = await search_owgr_player(session, player_name)
                if not profile_urls:
                    logger.warning(f"No OWGR profiles found for {player_name}")
                    failed_downloads += 1
                    continue
                
                logger.info(f"Found {len(profile_urls)} profiles for {player_name}")
                
                # Get photos from all profiles
                all_images = []
                for profile_url in profile_urls:
                    images = await get_player_photos_from_owgr_profile(session, profile_url)
                    all_images.extend(images)
                
                if not all_images:
                    logger.warning(f"No valid images found for {player_name}")
                    failed_downloads += 1
                    continue
                
                # Get the best image (largest area)
                best_image = max(all_images, key=lambda x: x[1]['width'] * x[1]['height'])
                best_image_url, best_metadata = best_image
                
                logger.info(f"Best image for {player_name}: {best_metadata['width']}x{best_metadata['height']}")
                
                # Create file path
                clean_name = clean_filename(player_name)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(BASE_PHOTO_DIR, "PGA_TOUR", f"{clean_name}_owgr_{timestamp}.png")
                
                # Download the image
                if await download_image(session, best_image_url, file_path, best_metadata):
                    logger.info(f"Successfully downloaded photo for {player_name}")
                    successful_downloads += 1
                    
                    # Update player data
                    players_dict[player_name]["photo_path"] = file_path
                    players_dict[player_name]["photo_metadata"] = best_metadata
                else:
                    logger.warning(f"Failed to download photo for {player_name}")
                    failed_downloads += 1
                
                # 5-second delay between players
                logger.info(f"Waiting 5 seconds before next player...")
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing {player_name}: {e}")
                failed_downloads += 1
    
    # Save updated player dict
    with open("datagolf_players_by_name.json", "w", encoding="utf-8") as f:
        json.dump(players_dict, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"Download complete! Successful: {successful_downloads}, Failed: {failed_downloads}")

if __name__ == "__main__":
    asyncio.run(download_golf_player_photos_owgr()) 