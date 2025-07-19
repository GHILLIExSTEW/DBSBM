#!/usr/bin/env python3
"""
Manual Logo Collector for Golf, Tennis, and F1
Helps collect league logos from various sources when API doesn't provide them.
"""

import os
import sys
import logging
import requests
from typing import Dict, List, Optional
from io import BytesIO

from PIL import Image, UnidentifiedImageError

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config.asset_paths import get_sport_category_for_path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Manual logo URLs for leagues that might not be available via API
MANUAL_LOGO_URLS = {
    "tennis": {
        "ATP": {
            "url": "https://upload.wikimedia.org/wikipedia/en/3/3c/ATP_Tour_logo.svg",
            "name": "ATP Tour",
        },
        "WTA": {
            "url": "https://upload.wikimedia.org/wikipedia/en/8/8d/WTA_logo.svg",
            "name": "WTA Tour",
        },
    },
    "golf": {
        "PGA": {
            "url": "https://upload.wikimedia.org/wikipedia/en/8/8d/PGA_Tour_logo.svg",
            "name": "PGA Tour",
        },
        "LPGA": {
            "url": "https://upload.wikimedia.org/wikipedia/en/9/9c/LPGA_logo.svg",
            "name": "LPGA Tour",
        },
        "EUROPEAN_TOUR": {
            "url": "https://upload.wikimedia.org/wikipedia/en/7/7c/European_Tour_logo.svg",
            "name": "European Tour",
        },
        "LIV_GOLF": {
            "url": "https://upload.wikimedia.org/wikipedia/en/2/2c/LIV_Golf_logo.svg",
            "name": "LIV Golf",
        },
    },
    "formula-1": {
        "FORMULA-1": {
            "url": "https://upload.wikimedia.org/wikipedia/en/a/a3/Formula_1_logo.svg",
            "name": "Formula 1",
        }
    },
}


class ManualLogoCollector:
    """Collects league logos from manual sources."""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logos_dir = os.path.join(self.base_dir, "static", "logos", "leagues")

    def normalize_filename(self, name: str) -> str:
        """Normalize a name for use as a filename."""
        return name.lower().replace(" ", "_").replace("-", "_").replace("/", "_")

    def download_and_save_logo(
        self, sport: str, league_code: str, logo_info: Dict
    ) -> bool:
        """Download and save a league logo from manual URL."""
        league_name = logo_info["name"]
        logo_url = logo_info["url"]
        sport_category = get_sport_category_for_path(league_code.upper())

        if not sport_category:
            logger.warning(f"No sport category found for league: {league_code}")
            return False

        # Create the directory structure
        league_dir = os.path.join(
            self.logos_dir, sport_category.upper(), league_code.upper()
        )
        os.makedirs(league_dir, exist_ok=True)

        # Try different filename patterns
        filename_patterns = [
            f"{self.normalize_filename(league_name)}.png",
            f"{league_code.lower()}.png",
        ]

        # Check if logo already exists
        for pattern in filename_patterns:
            logo_path = os.path.join(league_dir, pattern)
            if os.path.exists(logo_path):
                logger.info(f"Logo already exists: {logo_path}")
                return True

        # Download and save the logo
        for pattern in filename_patterns:
            logo_path = os.path.join(league_dir, pattern)

            try:
                logger.info(f"Downloading logo for {league_name} from {logo_url}")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(logo_url, timeout=15, headers=headers)
                response.raise_for_status()

                # Validate and process image
                try:
                    with Image.open(BytesIO(response.content)) as img:
                        if img.mode != "RGBA":
                            img = img.convert("RGBA")

                        # Resize to reasonable dimensions (max 200x200)
                        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                        img.save(logo_path, "PNG", optimize=True)

                        logger.info(f"Successfully saved logo: {logo_path}")
                        return True

                except UnidentifiedImageError:
                    logger.error(f"Invalid image format for {league_name}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing image for {league_name}: {e}")
                    continue

            except Exception as e:
                logger.error(f"Error downloading logo for {league_name}: {e}")
                continue

        return False

    def collect_all_logos(self) -> int:
        """Collect logos for all configured leagues."""
        logger.info("Starting manual logo collection process...")

        total_leagues = sum(len(leagues) for leagues in MANUAL_LOGO_URLS.values())
        successful_downloads = 0

        for sport, leagues in MANUAL_LOGO_URLS.items():
            logger.info(f"Processing {sport} leagues...")

            for league_code, logo_info in leagues.items():
                logger.info(f"Processing {league_code} ({logo_info['name']})")

                success = self.download_and_save_logo(sport, league_code, logo_info)
                if success:
                    successful_downloads += 1

        logger.info(
            f"Collection process completed. {successful_downloads}/{total_leagues} logos collected successfully."
        )
        return successful_downloads


def main():
    """Main function to run the manual logo collector."""
    logger.info("Manual Logo Collector starting...")

    collector = ManualLogoCollector()
    try:
        successful_downloads = collector.collect_all_logos()
        logger.info(f"Successfully collected {successful_downloads} league logos")
    except Exception as e:
        logger.error(f"Error during logo collection process: {e}")
        raise


if __name__ == "__main__":
    main()
