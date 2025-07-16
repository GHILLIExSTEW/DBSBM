#!/usr/bin/env python3
"""
Highly selective golf player photo downloader with strict quality filtering
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
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
from datetime import datetime

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wikipedia API endpoints
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKIPEDIA_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_PAGE_URL = "https://en.wikipedia.org/w/api.php"

# Base directory for saving photos
BASE_PHOTO_DIR = "static/logos/players/golf"

# Much stricter quality filters
MIN_WIDTH = 300
MIN_HEIGHT = 300
MAX_WIDTH = 3000
MAX_HEIGHT = 3000
MIN_ASPECT_RATIO = 0.6  # width/height - more restrictive for person photos
MAX_ASPECT_RATIO = 1.8

# Metadata filters
MIN_YEAR = 2010  # Much more recent photos only
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB max file size
MIN_QUALITY_SCORE = 4  # Much higher quality threshold

def get_exif_data(image):
    """Extract EXIF data from image."""
    exif_data = {}
    try:
        if hasattr(image, '_getexif') and image._getexif() is not None:
            exif = image._getexif()
            for tag_id in exif:
                tag = TAGS.get(tag_id, tag_id)
                data = exif.get(tag_id)
                if isinstance(data, bytes):
                    data = data.decode(errors='ignore')
                exif_data[tag] = data
    except Exception as e:
        logger.debug(f"Error reading EXIF data: {e}")
    return exif_data

def parse_date_taken(exif_data):
    """Parse date taken from EXIF data."""
    date_fields = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']
    
    for field in date_fields:
        if field in exif_data:
            try:
                date_str = exif_data[field]
                # Parse various date formats
                for fmt in ['%Y:%m:%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y:%m:%d']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
            except Exception as e:
                logger.debug(f"Error parsing date {field}: {e}")
    
    return None

def is_high_quality_person_image(image_data: bytes) -> tuple[bool, dict]:
    """Strict validation for high-quality person photos."""
    try:
        # Open image and check dimensions
        img = Image.open(io.BytesIO(image_data))
        width, height = img.size
        
        metadata = {
            'width': width,
            'height': height,
            'format': img.format,
            'mode': img.mode,
            'file_size': len(image_data),
            'exif_data': {},
            'date_taken': None,
            'camera_info': {},
            'quality_score': 0
        }
        
        # Basic dimension checks
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            logger.debug(f"Image too small: {width}x{height}")
            return False, metadata
        if width > MAX_WIDTH or height > MAX_HEIGHT:
            logger.debug(f"Image too large: {width}x{height}")
            return False, metadata
            
        # Strict aspect ratio for person photos
        aspect_ratio = width / height
        if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
            logger.debug(f"Bad aspect ratio: {aspect_ratio:.2f}")
            return False, metadata
            
        # Minimum area check
        if width * height < 90000:  # 300x300 minimum area
            logger.debug(f"Image area too small: {width * height}")
            return False, metadata
            
        # File size check
        if len(image_data) > MAX_FILE_SIZE:
            logger.debug(f"File too large: {len(image_data)} bytes")
            return False, metadata
        
        # Extract EXIF data
        exif_data = get_exif_data(img)
        metadata['exif_data'] = exif_data
        
        # Parse date taken
        date_taken = parse_date_taken(exif_data)
        metadata['date_taken'] = date_taken
        
        # Reject very old photos
        if date_taken and date_taken.year < MIN_YEAR:
            logger.debug(f"Photo too old: {date_taken.year}")
            return False, metadata
        
        # Extract camera info
        camera_fields = ['Make', 'Model', 'Software', 'Artist']
        for field in camera_fields:
            if field in exif_data:
                metadata['camera_info'][field] = exif_data[field]
        
        # Calculate strict quality score
        quality_score = 0
        
        # Size quality (bigger is better)
        area = width * height
        if area >= 250000:  # 500x500
            quality_score += 3
        elif area >= 100000:  # 316x316
            quality_score += 1
        
        # Date quality (very recent is better)
        if date_taken:
            years_old = datetime.now().year - date_taken.year
            if years_old <= 3:
                quality_score += 4
            elif years_old <= 8:
                quality_score += 2
            elif years_old <= 12:
                quality_score += 1
        else:
            # No date info - assume it's recent enough
            quality_score += 1
        
        # Camera quality (professional cameras get higher scores)
        if 'Make' in exif_data:
            make = exif_data['Make'].lower()
            if any(brand in make for brand in ['canon', 'nikon', 'sony', 'fujifilm', 'leica']):
                quality_score += 3
            elif any(brand in make for brand in ['iphone', 'samsung', 'google', 'pixel']):
                quality_score += 2
            elif any(brand in make for brand in ['apple', 'huawei', 'oneplus']):
                quality_score += 1
        
        # Format quality
        if img.format in ['JPEG', 'PNG']:
            quality_score += 1
        
        metadata['quality_score'] = quality_score
        
        # Very high quality threshold
        if quality_score < MIN_QUALITY_SCORE:
            logger.debug(f"Quality score too low: {quality_score}")
            return False, metadata
            
        return True, metadata
        
    except Exception as e:
        logger.debug(f"Error validating image: {e}")
        return False, {'error': str(e)}

async def search_wikipedia_players(session: aiohttp.ClientSession, player_name: str) -> list[str]:
    """Search Wikipedia for multiple relevant pages for a player."""
    try:
        # Clean player name for search
        search_name = player_name.split(',')[0] if ',' in player_name else player_name
        
        # Try multiple search strategies
        search_terms = [
            f"{search_name} golfer",
            f"{search_name} PGA",
            f"{search_name} professional golfer",
            f"{search_name} golf",
            search_name
        ]
        
        page_titles = []
        
        for search_term in search_terms:
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": search_term,
                "srlimit": 5  # Get more results
            }
            
            async with session.get(WIKIPEDIA_SEARCH_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("query", {}).get("search"):
                        for result in data["query"]["search"][:3]:  # Top 3 results
                            title = result["title"]
                            if title not in page_titles:
                                page_titles.append(title)
        
        return page_titles[:5]  # Limit to 5 unique pages
    except Exception as e:
        logger.error(f"Error searching Wikipedia for {player_name}: {e}")
        return []

async def get_wikipedia_page_images(session: aiohttp.ClientSession, page_title: str) -> list[tuple[str, dict]]:
    """Get multiple images from a Wikipedia page."""
    try:
        # Get page content to find images
        params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "images",
            "imlimit": 20
        }
        
        async with session.get(WIKIPEDIA_PAGE_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                pages = data.get("query", {}).get("pages", {})
                
                image_urls = []
                
                for page_id, page_data in pages.items():
                    if "images" in page_data:
                        for img in page_data["images"]:
                            img_title = img["title"]
                            
                            # Skip non-image files
                            if not img_title.startswith("File:") and not img_title.startswith("Image:"):
                                continue
                                
                            # Skip obvious non-person images
                            img_lower = img_title.lower()
                            if any(skip in img_lower for skip in [
                                'logo', 'flag', 'map', 'chart', 'graph', 'diagram', 
                                'trophy', 'medal', 'badge', 'icon', 'symbol',
                                'stadium', 'course', 'building', 'venue'
                            ]):
                                continue
                            
                            # Get image info
                            img_params = {
                                "action": "query",
                                "format": "json",
                                "titles": img_title,
                                "prop": "imageinfo",
                                "iiprop": "url|size|mime|extmetadata"
                            }
                            
                            async with session.get(WIKIPEDIA_PAGE_URL, params=img_params) as img_response:
                                if img_response.status == 200:
                                    img_data = await img_response.json()
                                    img_pages = img_data.get("query", {}).get("pages", {})
                                    
                                    for img_page_id, img_page_data in img_pages.items():
                                        if "imageinfo" in img_page_data:
                                            for img_info in img_page_data["imageinfo"]:
                                                image_url = img_info["url"]
                                                
                                                # Download and validate the image
                                                async with session.get(image_url) as download_response:
                                                    if download_response.status == 200:
                                                        image_data = await download_response.read()
                                                        is_valid, metadata = is_high_quality_person_image(image_data)
                                                        if is_valid:
                                                            image_urls.append((image_url, metadata))
                                                            logger.info(f"Found valid image: {img_title} (score: {metadata['quality_score']})")
                
                return image_urls
        return []
    except Exception as e:
        logger.error(f"Error getting images for {page_title}: {e}")
        return []

async def download_best_image(session: aiohttp.ClientSession, image_url: str, file_path: str, metadata: dict) -> bool:
    """Download the best quality image."""
    try:
        async with session.get(image_url) as response:
            if response.status == 200:
                image_data = await response.read()
                
                # Final validation
                is_valid, final_metadata = is_high_quality_person_image(image_data)
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

async def download_golf_player_photos_strict():
    """Main function with strict quality filtering."""
    logger.info("Starting strict golf player photo download...")
    
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
    quality_rejected = 0
    
    async with aiohttp.ClientSession() as session:
        for i, (player_name, player_data) in enumerate(players_dict.items(), 1):
            logger.info(f"Processing {i}/{total_players}: {player_name}")
            
            try:
                # Skip if already has a high-quality photo
                if player_data.get("photo_path") and os.path.exists(player_data["photo_path"]):
                    logger.info(f"Skipping {player_name} - already has photo")
                    continue
                
                # Search for multiple Wikipedia pages
                page_titles = await search_wikipedia_players(session, player_name)
                if not page_titles:
                    logger.warning(f"No Wikipedia pages found for {player_name}")
                    failed_downloads += 1
                    continue
                
                logger.info(f"Found {len(page_titles)} Wikipedia pages for {player_name}")
                
                # Get images from all pages
                all_images = []
                for page_title in page_titles:
                    images = await get_wikipedia_page_images(session, page_title)
                    all_images.extend(images)
                
                if not all_images:
                    logger.warning(f"No valid images found for {player_name}")
                    quality_rejected += 1
                    continue
                
                # Sort by quality score and get the best one
                all_images.sort(key=lambda x: x[1]['quality_score'], reverse=True)
                best_image_url, best_metadata = all_images[0]
                
                logger.info(f"Best image for {player_name}: score {best_metadata['quality_score']}")
                
                # Create file path
                clean_name = clean_filename(player_name)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(BASE_PHOTO_DIR, "PGA_TOUR", f"{clean_name}_strict_{timestamp}.png")
                
                # Download the best image
                if await download_best_image(session, best_image_url, file_path, best_metadata):
                    logger.info(f"Successfully downloaded high-quality photo for {player_name}")
                    successful_downloads += 1
                    
                    # Update player data
                    players_dict[player_name]["photo_path"] = file_path
                    players_dict[player_name]["photo_metadata"] = best_metadata
                else:
                    logger.warning(f"Failed to download photo for {player_name}")
                    failed_downloads += 1
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {player_name}: {e}")
                failed_downloads += 1
    
    # Save updated player dict
    with open("datagolf_players_by_name.json", "w", encoding="utf-8") as f:
        json.dump(players_dict, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"Download complete! Successful: {successful_downloads}, Failed: {failed_downloads}, Quality Rejected: {quality_rejected}")

if __name__ == "__main__":
    asyncio.run(download_golf_player_photos_strict()) 