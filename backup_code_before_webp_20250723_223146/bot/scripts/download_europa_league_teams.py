#!/usr/bin/env python3
"""
Europa League Teams Downloader
Downloads all Europa League teams and their logos from API-Sports API.
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("europa_league_teams_download.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# API Configuration
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    logger.error("API_KEY not found in environment variables!")
    sys.exit(1)

# Europa League Configuration
EUROPA_LEAGUE_ID = 848
API_BASE_URL = "https://v3.football.api-sports.io"
SEASON = 2025

# Request configuration
REQUEST_DELAY_SECONDS = 0.5
DOWNLOAD_TIMEOUT_SECONDS = 15
MAX_RETRIES = 3


class EuropaLeagueTeamsDownloader:
    """Downloads Europa League teams and their logos from API-Sports API."""

    def __init__(self):
        self.session = None
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.teams_dir = os.path.join(
            self.base_dir, "static", "logos", "teams", "SOCCER", "UEFA_Europa_League"
        )

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_SECONDS)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_api_request(
        self, endpoint: str, params: Dict = None
    ) -> Optional[Dict]:
        """Make a request to the API-Sports API."""
        if params is None:
            params = {}

        url = f"{API_BASE_URL}/{endpoint}"
        headers = {"x-apisports-key": API_KEY}

        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Making API request to: {url}")
                logger.info(f"Parameters: {params}")

                async with self.session.get(
                    url, headers=headers, params=params
                ) as response:
                    logger.info(f"API response status: {response.status}")

                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
                        )
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API request failed with status {response.status}: {error_text}"
                        )

                        if response.status == 429:  # Rate limit
                            wait_time = (attempt + 1) * 2
                            logger.info(f"Rate limited, waiting {wait_time} seconds...")
                            await asyncio.sleep(wait_time)
                            continue

                        return None

            except Exception as e:
                logger.error(f"Error making API request (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(REQUEST_DELAY_SECONDS * (attempt + 1))
                else:
                    return None

        return None

    async def get_europa_league_teams(self) -> List[Dict]:
        """Get all Europa League teams from the API."""
        params = {"league": EUROPA_LEAGUE_ID, "season": SEASON}

        result = await self.make_api_request("teams", params)

        if not result or "error" in result:
            logger.error(f"Failed to get Europa League teams: {result}")
            return []

        teams = result.get("response", [])
        logger.info(f"Found {len(teams)} Europa League teams")

        return teams

    def normalize_filename(self, name: str) -> str:
        """Normalize team name for filename."""
        # Remove special characters and replace spaces with underscores
        normalized = name.lower()
        normalized = normalized.replace(" ", "_")
        normalized = normalized.replace("-", "_")
        normalized = normalized.replace(".", "")
        normalized = normalized.replace(",", "")
        normalized = normalized.replace("(", "")
        normalized = normalized.replace(")", "")
        normalized = normalized.replace("&", "and")
        normalized = normalized.replace("fc", "fc")
        normalized = normalized.replace("cf", "cf")
        normalized = normalized.replace("sc", "sc")
        normalized = normalized.replace("ac", "ac")
        normalized = normalized.replace("fk", "fk")
        normalized = normalized.replace("hk", "hk")
        normalized = normalized.replace("if", "if")
        normalized = normalized.replace("ff", "ff")
        normalized = normalized.replace("af", "af")
        normalized = normalized.replace("sf", "sf")
        normalized = normalized.replace("sk", "sk")
        normalized = normalized.replace("tk", "tk")
        normalized = normalized.replace("tc", "tc")
        normalized = normalized.replace("fs", "fs")
        normalized = normalized.replace("fa", "fa")
        normalized = normalized.replace("fc", "fc")
        normalized = normalized.replace("cf", "cf")
        normalized = normalized.replace("sc", "sc")
        normalized = normalized.replace("ac", "ac")
        normalized = normalized.replace("fk", "fk")
        normalized = normalized.replace("hk", "hk")
        normalized = normalized.replace("if", "if")
        normalized = normalized.replace("ff", "ff")
        normalized = normalized.replace("af", "af")
        normalized = normalized.replace("sf", "sf")
        normalized = normalized.replace("sk", "sk")
        normalized = normalized.replace("tk", "tk")
        normalized = normalized.replace("tc", "tc")
        normalized = normalized.replace("fs", "fs")
        normalized = normalized.replace("fa", "fa")

        return normalized

    async def download_and_save_logo(self, team: Dict) -> bool:
        """Download and save a team's logo."""
        try:
            team_info = team.get("team", {})
            team_name = team_info.get("name", "Unknown")
            team_id = team_info.get("id", 0)
            logo_url = team_info.get("logo", "")

            if not logo_url:
                logger.warning(f"No logo URL for team: {team_name}")
                return False

            # Normalize filename
            filename = self.normalize_filename(team_name)
            filepath = os.path.join(self.teams_dir, f"{filename}.webp")

            # Check if file already exists
            if os.path.exists(filepath):
                logger.info(f"Logo already exists for {team_name}: {filename}.webp")
                return True

            logger.info(
                f"Downloading logo for {team_name} (ID: {team_id}) from {logo_url}"
            )

            # Download the logo
            async with self.session.get(logo_url) as response:
                if response.status == 200:
                    image_data = await response.read()

                    # Verify it's a valid image
                    try:
                        image = Image.open(BytesIO(image_data))
                        image.verify()
                    except UnidentifiedImageError:
                        logger.error(f"Invalid image data for {team_name}")
                        return False

                    # Save the image
                    with open(filepath, "wb") as f:
                        f.write(image_data)

                    logger.info(
                        f"Successfully saved logo for {team_name}: {filename}.webp"
                    )
                    return True
                else:
                    logger.error(
                        f"Failed to download logo for {team_name}: HTTP {response.status}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error downloading logo for {team_name}: {e}")
            return False

    async def download_all_teams(self):
        """Download all Europa League teams and their logos."""
        # Create directory if it doesn't exist
        os.makedirs(self.teams_dir, exist_ok=True)
        logger.info(f"Teams directory: {self.teams_dir}")

        # Get teams from API
        teams = await self.get_europa_league_teams()

        if not teams:
            logger.error("No teams found!")
            return

        # Download logos for each team
        successful_downloads = 0
        failed_downloads = 0

        for i, team in enumerate(teams):
            team_info = team.get("team", {})
            team_name = team_info.get("name", "Unknown")

            logger.info(f"Processing team {i+1}/{len(teams)}: {team_name}")

            if await self.download_and_save_logo(team):
                successful_downloads += 1
            else:
                failed_downloads += 1

            # Add delay between requests
            if i < len(teams) - 1:
                await asyncio.sleep(REQUEST_DELAY_SECONDS)

        logger.info(f"Download completed!")
        logger.info(f"Successful downloads: {successful_downloads}")
        logger.info(f"Failed downloads: {failed_downloads}")
        logger.info(f"Total teams processed: {len(teams)}")


async def main():
    """Main function."""
    logger.info("Starting Europa League teams download...")

    async with EuropaLeagueTeamsDownloader() as downloader:
        await downloader.download_all_teams()

    logger.info("Europa League teams download completed!")


if __name__ == "__main__":
    asyncio.run(main())
