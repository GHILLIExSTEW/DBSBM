#!/usr/bin/env python3
"""
Download photos for golf players from URLs in an Excel file
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
import pandas as pd

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Validate if an image is a good quality person photo."""
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_data))
        
        # Get image info
        width, height = image.size
        format_type = image.format
        mode = image.mode
        
        # Basic size validation
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            return False, {"error": "Image too small", "width": width, "height": height}
        
        if width > MAX_WIDTH or height > MAX_HEIGHT:
            return False, {"error": "Image too large", "width": width, "height": height}
        
        # Aspect ratio validation
        aspect_ratio = width / height
        if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
            return False, {"error": "Aspect ratio out of range", "aspect_ratio": aspect_ratio}
        
        # Format validation
        if format_type not in ['JPEG', 'PNG', 'WEBP']:
            return False, {"error": "Unsupported format", "format": format_type}
        
        # Mode validation (should be RGB or RGBA)
        if mode not in ['RGB', 'RGBA']:
            return False, {"error": "Unsupported color mode", "mode": mode}
        
        # Create metadata
        metadata = {
            "width": width,
            "height": height,
            "format": format_type,
            "mode": mode,
            "aspect_ratio": round(aspect_ratio, 2),
            "file_size": len(image_data),
            "timestamp": datetime.now().isoformat()
        }
        
        return True, metadata
        
    except Exception as e:
        return False, {"error": str(e)}

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

async def download_golf_players_from_excel(excel_file_path: str):
    """Main function to download photos for golf players from Excel file."""
    logger.info(f"Starting golf player photo download from Excel file: {excel_file_path}")
    
    # Read the Excel file
    try:
        df = pd.read_excel(excel_file_path)
        logger.info(f"Loaded Excel file with {len(df)} rows")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Display first few rows to understand structure
        logger.info("First few rows:")
        logger.info(df.head())
        
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        return
    
    # Create base directory
    os.makedirs(BASE_PHOTO_DIR, exist_ok=True)
    
    # Track progress
    total_players = len(df)
    successful_downloads = 0
    failed_downloads = 0
    
    # Create session with longer timeout
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, row in df.iterrows():
            try:
                # Extract player info from row
                # You'll need to adjust these column names based on your Excel structure
                player_name = row.get('Player Name', row.get('Name', row.get('Player', '')))
                image_url = row.get('Image URL', row.get('URL', row.get('Photo', '')))
                league = row.get('League', row.get('Tour', 'UNKNOWN'))
                
                if not player_name or not image_url:
                    logger.warning(f"Row {i+1}: Missing player name or image URL")
                    failed_downloads += 1
                    continue
                
                logger.info(f"Processing {i+1}/{total_players}: {player_name}")
                logger.info(f"Image URL: {image_url}")
                
                # Download and validate the image
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    }
                    
                    async with session.get(image_url, headers=headers) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            is_valid, metadata = is_valid_person_image(image_data)
                            
                            if not is_valid:
                                logger.warning(f"Image for {player_name} failed validation: {metadata.get('error', 'Unknown error')}")
                                failed_downloads += 1
                                continue
                            
                            logger.info(f"Valid image for {player_name}: {metadata['width']}x{metadata['height']}")
                            
                            # Create file path
                            clean_name = clean_filename(player_name)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            file_path = os.path.join(BASE_PHOTO_DIR, league, f"{clean_name}_excel_{timestamp}.png")
                            
                            # Save the image
                            if await download_image(session, image_url, file_path, metadata):
                                logger.info(f"Successfully downloaded photo for {player_name}")
                                successful_downloads += 1
                            else:
                                logger.warning(f"Failed to download photo for {player_name}")
                                failed_downloads += 1
                        else:
                            logger.warning(f"Failed to download image for {player_name}: HTTP {response.status}")
                            failed_downloads += 1
                            
                except Exception as e:
                    logger.error(f"Error downloading image for {player_name}: {e}")
                    failed_downloads += 1
                
                # 5-second delay between players to avoid being blocked
                logger.info(f"Waiting 5 seconds before next player...")
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing row {i+1}: {e}")
                failed_downloads += 1
    
    logger.info(f"Download complete! Successful: {successful_downloads}, Failed: {failed_downloads}")

if __name__ == "__main__":
    # You can specify the Excel file path here or pass it as an argument
    excel_file = "golf_players.xlsx"  # Change this to your Excel file path
    
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    
    asyncio.run(download_golf_players_from_excel(excel_file)) 