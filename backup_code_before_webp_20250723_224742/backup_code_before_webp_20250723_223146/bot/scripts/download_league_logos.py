#!/usr/bin/env python3
"""
League Logo Downloader for Golf, Tennis, and F1
Downloads league logos from API-Sports API and saves them in the correct directory structure.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional

import aiohttp
from PIL import Image, UnidentifiedImageError

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

from bot.config.asset_paths import get_sport_category_for_path
from bot.config.leagues import LEAGUE_CONFIG

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("league_logo_download.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# API Configuration
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    logger.error("API_KEY not found in environment variables!")
    sys.exit(1)

# API-Sports Base URLs
BASE_URLS = {
    "tennis": "https://v1.tennis.api-sports.io",
    "golf": "https://v1.golf.api-sports.io",
    "formula-1": "https://v1.formula-1.api-sports.io",
}

# League configurations for the sports we want to download
LEAGUE_CONFIGS = {
    "tennis": {
        "ATP": {"name": "ATP Tour", "sport": "tennis"},
        "WTA": {"name": "WTA Tour", "sport": "tennis"},
    },
    "golf": {
        "PGA": {"name": "PGA Tour", "sport": "golf"},
        "LPGA": {"name": "LPGA Tour", "sport": "golf"},
        "EUROPEAN_TOUR": {"name": "European Tour", "sport": "golf"},
        "LIV_GOLF": {"name": "LIV Golf", "sport": "golf"},
        "KORN_FERRY": {"name": "Korn Ferry Tour", "sport": "golf"},
        "CHAMPIONS_TOUR": {"name": "Champions Tour", "sport": "golf"},
        "RYDER_CUP": {"name": "Ryder Cup", "sport": "golf"},
        "PRESIDENTS_CUP": {"name": "Presidents Cup", "sport": "golf"},
        "SOLHEIM_CUP": {"name": "Solheim Cup", "sport": "golf"},
        "OLYMPIC_GOLF": {"name": "Olympic Golf", "sport": "golf"},
    },
    "formula-1": {
        "FORMULA-1": {"name": "Formula 1", "sport": "formula-1"},
    },
}

# Request configuration
REQUEST_DELAY_SECONDS = 0.5
DOWNLOAD_TIMEOUT_SECONDS = 15
MAX_RETRIES = 3


class LeagueLogoDownloader:
    """Downloads league logos from API-Sports API."""

    def __init__(self):
        self.session = None
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logos_dir = os.path.join(self.base_dir, "static", "logos", "leagues")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_SECONDS)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_api_request(
        self, sport: str, endpoint: str, params: Dict = None
    ) -> Optional[Dict]:
        """Make a request to the API-Sports API."""
        if sport not in BASE_URLS:
            logger.error(f"Unsupported sport: {sport}")
            return None

        base_url = BASE_URLS[sport]
        url = f"{base_url}{endpoint}"

        headers = {
            "x-rapidapi-host": f"v1.{sport}.api-sports.io",
            "x-rapidapi-key": API_KEY,
        }

        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Making API request to {url} (attempt {attempt + 1})")
                async with self.session.get(
                    url, headers=headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched data from {url}")
                        return data
                    elif response.status == 429:
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"API request failed with status {response.status}: {url}"
                        )
                        return None
            except Exception as e:
                logger.error(f"Error making API request to {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(1)

        return None

    async def get_league_info(self, sport: str, league_name: str) -> Optional[Dict]:
        """Get league information from the API."""
        params = {"name": league_name}
        data = await self.make_api_request(sport, "/leagues", params)

        if data and "response" in data and data["response"]:
            # Find the best match for the league name
            leagues = data["response"]
            best_match = None
            best_score = 0

            for league in leagues:
                api_name = league.get("league", {}).get("name", "").lower()
                search_name = league_name.lower()

                # Simple similarity scoring
                if api_name == search_name:
                    best_match = league
                    break
                elif search_name in api_name or api_name in search_name:
                    score = len(set(api_name.split()) & set(search_name.split()))
                    if score > best_score:
                        best_score = score
                        best_match = league

            return best_match

        return None

    def normalize_filename(self, name: str) -> str:
        """Normalize a name for use as a filename."""
        return name.lower().replace(" ", "_").replace("-", "_").replace("/", "_")

    async def download_and_save_logo(
        self, sport: str, league_code: str, league_config: Dict
    ):
        """Download and save a league logo."""
        league_name = league_config["name"]
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

        # Get league info from API
        league_info = await self.get_league_info(sport, league_name)
        if not league_info:
            logger.warning(f"Could not find league info for {league_name}")
            return False

        # Extract logo URL
        logo_url = league_info.get("league", {}).get("logo")
        if not logo_url:
            logger.warning(f"No logo URL found for {league_name}")
            return False

        # Download and save the logo
        for pattern in filename_patterns:
            logo_path = os.path.join(league_dir, pattern)

            try:
                logger.info(f"Downloading logo for {league_name} from {logo_url}")
                async with self.session.get(logo_url) as response:
                    if response.status == 200:
                        img_data = await response.read()

                        # Validate and process image
                        try:
                            with Image.open(BytesIO(img_data)) as img:
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
                            logger.error(
                                f"Error processing image for {league_name}: {e}"
                            )
                            continue
                    else:
                        logger.error(
                            f"Failed to download logo for {league_name}: HTTP {response.status}"
                        )

            except Exception as e:
                logger.error(f"Error downloading logo for {league_name}: {e}")
                continue

        return False

    async def download_all_logos(self):
        """Download logos for all configured leagues."""
        logger.info("Starting league logo download process...")

        total_leagues = sum(len(leagues) for leagues in LEAGUE_CONFIGS.values())
        successful_downloads = 0

        for sport, leagues in LEAGUE_CONFIGS.items():
            logger.info(f"Processing {sport} leagues...")

            for league_code, league_config in leagues.items():
                logger.info(f"Processing {league_code} ({league_config['name']})")

                success = await self.download_and_save_logo(
                    sport, league_code, league_config
                )
                if success:
                    successful_downloads += 1

                # Rate limiting
                await asyncio.sleep(REQUEST_DELAY_SECONDS)

        logger.info(
            f"Download process completed. {successful_downloads}/{total_leagues} logos downloaded successfully."
        )
        return successful_downloads


async def main():
    """Main function to run the logo downloader."""
    logger.info("League Logo Downloader starting...")

    async with LeagueLogoDownloader() as downloader:
        try:
            successful_downloads = await downloader.download_all_logos()
            logger.info(f"Successfully downloaded {successful_downloads} league logos")
        except Exception as e:
            logger.error(f"Error during logo download process: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
