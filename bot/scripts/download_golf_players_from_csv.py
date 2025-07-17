#!/usr/bin/env python3
"""
Download photos for golf players from CSV file
"""

import asyncio
import json
import logging
import os
import sys
import re
import csv
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
            return False, {"error": f"Image too small: {width}x{height}"}

        if width > MAX_WIDTH or height > MAX_HEIGHT:
            return False, {"error": f"Image too large: {width}x{height}"}

        # Aspect ratio validation
        aspect_ratio = width / height
        if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
            return False, {"error": f"Bad aspect ratio: {aspect_ratio:.2f}"}

        # Check if it's a reasonable format
        if format_type not in ["JPEG", "JPG", "PNG", "WEBP"]:
            return False, {"error": f"Unsupported format: {format_type}"}

        # Create metadata
        metadata = {
            "width": width,
            "height": height,
            "format": format_type,
            "mode": mode,
            "aspect_ratio": round(aspect_ratio, 2),
            "file_size": len(image_data),
            "timestamp": datetime.now().isoformat(),
        }

        return True, metadata

    except Exception as e:
        return False, {"error": f"Image validation error: {str(e)}"}


async def download_image(
    session: aiohttp.ClientSession, image_url: str, file_path: str, metadata: dict
) -> bool:
    """Download an image and save it to the specified path."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
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
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(image_data)

                # Save metadata
                metadata_file = file_path.replace(".png", "_metadata.json")
                async with aiofiles.open(metadata_file, "w") as f:
                    await f.write(json.dumps(final_metadata, indent=2, default=str))

                return True
        return False
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return False


def clean_filename(name: str) -> str:
    """Clean a player name for use as a filename."""
    cleaned = re.sub(r'[<>:"/\\|?*]', "", name)
    cleaned = cleaned.replace(" ", "_")
    return cleaned


async def download_golf_players_from_csv(csv_file_path: str, league: str = "UNKNOWN"):
    """Download photos for golf players from CSV file."""
    logger.info(f"Starting golf player photo download from CSV: {csv_file_path}")

    # Create base directory
    os.makedirs(BASE_PHOTO_DIR, exist_ok=True)

    # Track progress
    total_players = 0
    successful_downloads = 0
    failed_downloads = 0

    # Read CSV file
    players_to_download = []
    try:
        with open(csv_file_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Assuming CSV has columns like 'name' and 'image_url' or similar
                # Adjust column names based on your CSV structure
                player_name = (
                    row.get("name")
                    or row.get("player_name")
                    or row.get("Name")
                    or row.get("Player")
                )
                image_url = (
                    row.get("image_url")
                    or row.get("url")
                    or row.get("Image")
                    or row.get("URL")
                )

                if player_name and image_url:
                    players_to_download.append((player_name, image_url))
                    total_players += 1
                else:
                    logger.warning(f"Skipping row with missing data: {row}")

    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return

    logger.info(f"Found {total_players} players in CSV file")

    # Create session with longer timeout
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, (player_name, image_url) in enumerate(players_to_download, 1):
            logger.info(f"Processing {i}/{total_players}: {player_name}")

            try:
                logger.info(f"Downloading image for {player_name}: {image_url}")

                # Download and validate the image
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    }

                    async with session.get(image_url, headers=headers) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            is_valid, metadata = is_valid_person_image(image_data)

                            if not is_valid:
                                logger.warning(
                                    f"Image for {player_name} failed validation: {metadata.get('error', 'Unknown error')}"
                                )
                                failed_downloads += 1
                                continue

                            logger.info(
                                f"Valid image for {player_name}: {metadata['width']}x{metadata['height']}"
                            )

                            # Create file path
                            clean_name = clean_filename(player_name)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            file_path = os.path.join(
                                BASE_PHOTO_DIR,
                                league,
                                f"{clean_name}_csv_{timestamp}.png",
                            )

                            # Save the image
                            if await download_image(
                                session, image_url, file_path, metadata
                            ):
                                logger.info(
                                    f"Successfully downloaded photo for {player_name}"
                                )
                                successful_downloads += 1
                            else:
                                logger.warning(
                                    f"Failed to download photo for {player_name}"
                                )
                                failed_downloads += 1
                        else:
                            logger.warning(
                                f"Failed to download image for {player_name}: HTTP {response.status}"
                            )
                            failed_downloads += 1

                except Exception as e:
                    logger.error(f"Error downloading image for {player_name}: {e}")
                    failed_downloads += 1

                # 5-second delay between players to avoid being blocked
                logger.info(f"Waiting 5 seconds before next player...")
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error processing {player_name}: {e}")
                failed_downloads += 1

    logger.info(
        f"Download complete! Successful: {successful_downloads}, Failed: {failed_downloads}"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download golf player photos from CSV file"
    )
    parser.add_argument("csv_file", help="Path to the CSV file containing player data")
    parser.add_argument(
        "--league", default="UNKNOWN", help="League name (e.g., PGA_TOUR, LPGA)"
    )

    args = parser.parse_args()

    asyncio.run(download_golf_players_from_csv(args.csv_file, args.league))
