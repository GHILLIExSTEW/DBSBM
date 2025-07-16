#!/usr/bin/env python3
"""
LPGA official player photo downloader
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

# LPGA URLs
LPGA_ATHLETES_URL = "https://www.lpga.com/athletes/directory"
LPGA_BASE_URL = "https://www.lpga.com"

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

async def get_lpga_athletes_list(session: aiohttp.ClientSession) -> dict:
    """Get the list of all LPGA athletes from the directory page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        async with session.get(LPGA_ATHLETES_URL, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                athletes_dict = {}
                
                # Look for athlete links and images
                # LPGA has athlete cards with profile links
                athlete_elements = soup.find_all(['a', 'div'], class_=re.compile(r'athlete|player|golfer', re.I))
                
                for element in athlete_elements:
                    # Look for athlete name
                    name_element = element.find(['h3', 'h4', 'h5', 'span', 'div'], class_=re.compile(r'name|athlete', re.I))
                    if name_element:
                        athlete_name = name_element.get_text().strip()
                        
                        # Look for athlete image
                        img_element = element.find('img')
                        if img_element:
                            img_src = img_element.get('src', '')
                            if img_src:
                                # Convert relative URLs to absolute
                                if img_src.startswith('//'):
                                    img_src = 'https:' + img_src
                                elif img_src.startswith('/'):
                                    img_src = urljoin(LPGA_BASE_URL, img_src)
                                
                                athletes_dict[athlete_name] = {
                                    'name': athlete_name,
                                    'image_url': img_src,
                                    'profile_url': element.get('href', '') if element.name == 'a' else ''
                                }
                
                # Also look for any image with athlete-like patterns
                images = soup.find_all('img')
                for img in images:
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    
                    # Look for athlete images
                    if any(keyword in alt.lower() for keyword in ['athlete', 'player', 'golfer', 'lpga']):
                        if src:
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = urljoin(LPGA_BASE_URL, src)
                            
                            # Try to extract athlete name from alt text or nearby elements
                            athlete_name = alt.replace('athlete', '').replace('player', '').replace('golfer', '').strip()
                            if athlete_name and len(athlete_name) > 2:
                                athletes_dict[athlete_name] = {
                                    'name': athlete_name,
                                    'image_url': src,
                                    'profile_url': ''
                                }
                
                logger.info(f"Found {len(athletes_dict)} athletes on LPGA directory page")
                return athletes_dict
        
        return {}
    except Exception as e:
        logger.error(f"Error getting LPGA athletes list: {e}")
        return {}

async def search_lpga_athlete(session: aiohttp.ClientSession, athlete_name: str) -> list[str]:
    """Search LPGA for a specific athlete and return profile URLs."""
    try:
        # Clean athlete name for search
        search_name = athlete_name.split(',')[0] if ',' in athlete_name else athlete_name
        
        # Try different search URLs
        search_urls = [
            f"https://www.lpga.com/search?q={quote(search_name)}",
            f"https://www.lpga.com/athletes/search?q={quote(search_name)}",
            f"https://www.lpga.com/athletes/{quote(search_name.lower().replace(' ', '-'))}"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        profile_urls = []
        
        for search_url in search_urls:
            try:
                async with session.get(search_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Look for athlete profile links
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link.get('href', '')
                            text = link.get_text().strip()
                            
                            # Look for athlete profile patterns
                            if '/athlete/' in href.lower() or '/athletes/' in href.lower():
                                if search_name.lower() in text.lower():
                                    full_url = urljoin(LPGA_BASE_URL, href)
                                    if full_url not in profile_urls:
                                        profile_urls.append(full_url)
                                        logger.info(f"Found LPGA profile for {athlete_name}: {full_url}")
            except Exception as e:
                logger.debug(f"Error with search URL {search_url}: {e}")
                continue
        
        return profile_urls[:3]  # Limit to 3 profile URLs
    except Exception as e:
        logger.error(f"Error searching LPGA for {athlete_name}: {e}")
        return []

async def get_athlete_photos_from_lpga_profile(session: aiohttp.ClientSession, profile_url: str) -> list[tuple[str, dict]]:
    """Extract athlete photos from an LPGA profile page."""
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
                            src = urljoin(LPGA_BASE_URL, src)
                        
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
    """Clean an athlete name for use as a filename."""
    cleaned = re.sub(r'[<>:"/\\|?*]', '', name)
    cleaned = cleaned.replace(' ', '_')
    return cleaned

async def download_lpga_athlete_photos():
    """Main function to download LPGA athlete photos."""
    logger.info("Starting LPGA athlete photo download...")
    
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
        # First, try to get the main athletes list
        logger.info("Getting LPGA athletes list...")
        lpga_athletes = await get_lpga_athletes_list(session)
        
        for i, (player_name, player_data) in enumerate(players_dict.items(), 1):
            logger.info(f"Processing {i}/{total_players}: {player_name}")
            
            try:
                # Skip if already has a photo
                if player_data.get("photo_path") and os.path.exists(player_data["photo_path"]):
                    logger.info(f"Skipping {player_name} - already has photo")
                    continue
                
                # First, check if we have this player in the main list
                found_image = None
                if lpga_athletes:
                    for lpga_name, lpga_data in lpga_athletes.items():
                        if player_name.lower() in lpga_name.lower() or lpga_name.lower() in player_name.lower():
                            found_image = lpga_data['image_url']
                            logger.info(f"Found {player_name} in LPGA list")
                            break
                
                # If not found in main list, search for profile pages
                if not found_image:
                    profile_urls = await search_lpga_athlete(session, player_name)
                    if not profile_urls:
                        logger.warning(f"No LPGA profiles found for {player_name}")
                        failed_downloads += 1
                        continue
                    
                    logger.info(f"Found {len(profile_urls)} profiles for {player_name}")
                    
                    # Get photos from all profiles
                    all_images = []
                    for profile_url in profile_urls:
                        images = await get_athlete_photos_from_lpga_profile(session, profile_url)
                        all_images.extend(images)
                    
                    if not all_images:
                        logger.warning(f"No valid images found for {player_name}")
                        failed_downloads += 1
                        continue
                    
                    # Get the best image (largest area)
                    best_image = max(all_images, key=lambda x: x[1]['width'] * x[1]['height'])
                    found_image, best_metadata = best_image
                else:
                    # Validate the found image
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        }
                        async with session.get(found_image, headers=headers) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                is_valid, best_metadata = is_valid_person_image(image_data)
                                if not is_valid:
                                    logger.warning(f"Found image for {player_name} but quality check failed")
                                    failed_downloads += 1
                                    continue
                            else:
                                logger.warning(f"Failed to download found image for {player_name}")
                                failed_downloads += 1
                                continue
                    except Exception as e:
                        logger.error(f"Error validating found image for {player_name}: {e}")
                        failed_downloads += 1
                        continue
                
                logger.info(f"Best image for {player_name}: {best_metadata['width']}x{best_metadata['height']}")
                
                # Create file path
                clean_name = clean_filename(player_name)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(BASE_PHOTO_DIR, "LPGA", f"{clean_name}_lpga_{timestamp}.png")
                
                # Download the image
                if await download_image(session, found_image, file_path, best_metadata):
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
    asyncio.run(download_lpga_athlete_photos()) 