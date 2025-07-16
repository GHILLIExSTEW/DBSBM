#!/usr/bin/env python3
"""
PGA TOUR actual players page photo downloader
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

# PGA TOUR URLs
PGATOUR_PLAYERS_URL = "https://www.pgatour.com/players"
PGATOUR_BASE_URL = "https://www.pgatour.com"

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

def generate_pgatour_profile_urls(player_name: str) -> list[str]:
    """Generate possible PGA TOUR profile URLs for a player."""
    # Clean player name
    clean_name = player_name.split(',')[0] if ',' in player_name else player_name
    
    # Remove special characters and convert to URL-friendly format
    url_name = re.sub(r'[^a-zA-Z\s]', '', clean_name)
    url_name = url_name.strip().lower().replace(' ', '-')
    
    # Generate different URL patterns for PGA TOUR
    urls = [
        f"{PGATOUR_BASE_URL}/players/{url_name}",
        f"{PGATOUR_BASE_URL}/players/{url_name}.html",
        f"{PGATOUR_BASE_URL}/player/{url_name}",
        f"{PGATOUR_BASE_URL}/player/{url_name}.html",
        f"{PGATOUR_BASE_URL}/golfer/{url_name}",
        f"{PGATOUR_BASE_URL}/golfer/{url_name}.html",
    ]
    
    # Also try with first initial + last name
    name_parts = clean_name.split()
    if len(name_parts) >= 2:
        first_initial = name_parts[0][0].lower()
        last_name = name_parts[-1].lower()
        urls.extend([
            f"{PGATOUR_BASE_URL}/players/{first_initial}-{last_name}",
            f"{PGATOUR_BASE_URL}/players/{first_initial}-{last_name}.html",
            f"{PGATOUR_BASE_URL}/player/{first_initial}-{last_name}",
            f"{PGATOUR_BASE_URL}/player/{first_initial}-{last_name}.html",
        ])
    
    # Handle special cases like "J.B. Holmes" -> "jb-holmes"
    if '.' in clean_name:
        # Remove periods and try
        no_periods = clean_name.replace('.', '').replace(' ', '-').lower()
        urls.extend([
            f"{PGATOUR_BASE_URL}/players/{no_periods}",
            f"{PGATOUR_BASE_URL}/players/{no_periods}.html",
        ])
    
    # Handle special cases like "S.H. Kim" -> "sh-kim"
    if len(name_parts) >= 2 and '.' in name_parts[0]:
        initials = ''.join([part[0] for part in name_parts[:-1]]).lower()
        last_name = name_parts[-1].lower()
        urls.extend([
            f"{PGATOUR_BASE_URL}/players/{initials}-{last_name}",
            f"{PGATOUR_BASE_URL}/players/{initials}-{last_name}.html",
        ])
    
    return urls

async def check_pgatour_profile(session: aiohttp.ClientSession, profile_url: str) -> bool:
    """Check if a PGA TOUR profile URL exists and is valid."""
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
            return response.status == 200
    except Exception:
        return False

async def get_player_photos_from_pgatour_profile(session: aiohttp.ClientSession, profile_url: str) -> list[tuple[str, dict]]:
    """Extract player photos from a PGA TOUR profile page."""
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
                            src = urljoin(PGATOUR_BASE_URL, src)
                        
                        # Skip small images and icons
                        if any(skip in src.lower() for skip in ['icon', 'logo', 'thumb', 'avatar', 'flag', 'sponsor']):
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

async def download_golf_player_photos_pgatour_actual():
    """Main function to download golf player photos using actual PGA TOUR structure."""
    logger.info("Starting PGA TOUR actual player photo download...")
    
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
                
                # Generate possible profile URLs
                profile_urls = generate_pgatour_profile_urls(player_name)
                logger.info(f"Generated {len(profile_urls)} possible URLs for {player_name}")
                
                # Check which URLs exist
                valid_urls = []
                for url in profile_urls:
                    if await check_pgatour_profile(session, url):
                        valid_urls.append(url)
                        logger.info(f"Found valid profile: {url}")
                        break  # Just need one valid URL
                
                if not valid_urls:
                    logger.warning(f"No valid PGA TOUR profiles found for {player_name}")
                    failed_downloads += 1
                    continue
                
                # Get photos from the first valid profile
                profile_url = valid_urls[0]
                images = await get_player_photos_from_pgatour_profile(session, profile_url)
                
                if not images:
                    logger.warning(f"No valid images found for {player_name}")
                    failed_downloads += 1
                    continue
                
                # Get the best image (largest area)
                best_image = max(images, key=lambda x: x[1]['width'] * x[1]['height'])
                best_image_url, best_metadata = best_image
                
                logger.info(f"Best image for {player_name}: {best_metadata['width']}x{best_metadata['height']}")
                
                # Create file path
                clean_name = clean_filename(player_name)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(BASE_PHOTO_DIR, "PGA_TOUR", f"{clean_name}_pgatour_actual_{timestamp}.png")
                
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
                
                # 3-second delay between players
                logger.info(f"Waiting 3 seconds before next player...")
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error processing {player_name}: {e}")
                failed_downloads += 1
    
    # Save updated player dict
    with open("datagolf_players_by_name.json", "w", encoding="utf-8") as f:
        json.dump(players_dict, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"Download complete! Successful: {successful_downloads}, Failed: {failed_downloads}")

if __name__ == "__main__":
    asyncio.run(download_golf_player_photos_pgatour_actual()) 