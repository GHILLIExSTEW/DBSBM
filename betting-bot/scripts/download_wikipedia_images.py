#!/usr/bin/env python3
"""
Wikipedia Player Image Downloader
Downloads player images from Wikipedia for darts, tennis, and golf.
Saves images in PNG format with consistent sizing.
"""

import os
import sys
import requests
import time
import json
import urllib.parse
import logging
from pathlib import Path
from PIL import Image
from io import BytesIO

# Add the parent directory to the path to import config modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wikipedia_download.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WikipediaImageDownloader:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.static_dir = self.base_dir / "static"
        self.logos_dir = self.static_dir / "logos"
        self.players_dir = self.logos_dir / "players"
        self.scripts_dir = self.base_dir / "scripts"

        # Load player lists
        self.player_lists_file = self.scripts_dir / "player_lists.json"
        self.load_player_lists()

        # Wikipedia API endpoints
        self.wikipedia_api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        self.wikipedia_search_url = "https://en.wikipedia.org/w/api.php"

        # Rate limiting
        self.delay_between_requests = 1.0  # seconds

        # Image settings
        self.image_size = (200, 200)  # Same as LOGO_SIZE from image_settings

    def load_player_lists(self):
        """Load player lists from JSON file."""
        try:
            with open(self.player_lists_file, "r", encoding="utf-8") as f:
                self.player_lists = json.load(f)
            logger.info(f"Loaded player lists from {self.player_lists_file}")
        except FileNotFoundError:
            logger.error(f"Player lists file not found: {self.player_lists_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing player lists JSON: {e}")
            sys.exit(1)

    def create_directories(self):
        """Create the necessary directory structure."""
        for sport, leagues in self.player_lists.items():
            sport_dir = self.players_dir / sport
            sport_dir.mkdir(parents=True, exist_ok=True)

            for league in leagues:
                league_dir = sport_dir / league
                league_dir.mkdir(exist_ok=True)

                # Create .gitkeep files for empty directories
                gitkeep_file = league_dir / ".gitkeep"
                if not gitkeep_file.exists():
                    gitkeep_file.touch()

        logger.info("Created directory structure for all sports and leagues")

    def search_wikipedia_player(self, player_name):
        """Search for a player on Wikipedia and return image data."""
        try:
            # First try direct page lookup
            encoded_name = urllib.parse.quote(player_name.replace(" ", "_"))
            url = f"{self.wikipedia_api_url}{encoded_name}"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "thumbnail" in data and data["thumbnail"]:
                    return {
                        "title": data["title"],
                        "image_url": data["thumbnail"]["source"],
                        "page_url": data["content_urls"]["desktop"]["page"],
                    }

            # If direct lookup fails, try search
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{player_name} (tennis OR darts OR golf)",
                "srlimit": 3,
                "srnamespace": 0,
            }

            response = requests.get(
                self.wikipedia_search_url, params=search_params, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if (
                    "query" in data
                    and "search" in data["query"]
                    and data["query"]["search"]
                ):
                    # Try each search result
                    for result in data["query"]["search"]:
                        page_title = result["title"]

                        # Get the page summary for this result
                        encoded_title = urllib.parse.quote(page_title.replace(" ", "_"))
                        summary_url = f"{self.wikipedia_api_url}{encoded_title}"

                        summary_response = requests.get(summary_url, timeout=10)
                        if summary_response.status_code == 200:
                            summary_data = summary_response.json()
                            if (
                                "thumbnail" in summary_data
                                and summary_data["thumbnail"]
                            ):
                                return {
                                    "title": summary_data["title"],
                                    "image_url": summary_data["thumbnail"]["source"],
                                    "page_url": summary_data["content_urls"]["desktop"][
                                        "page"
                                    ],
                                }

            return None

        except Exception as e:
            logger.error(f"Error searching for {player_name}: {e}")
            return None

    def download_and_save_image(self, image_url, player_name, sport, league):
        """Download and save an image for a player."""
        try:
            # Download the image
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()

            # Open and process the image
            with Image.open(BytesIO(response.content)) as img:
                # Convert to RGBA if needed
                if img.mode != "RGBA":
                    img = img.convert("RGBA")

                # Resize to standard size
                img.thumbnail(self.image_size, Image.Resampling.LANCZOS)

                # Create safe filename
                safe_name = self.create_safe_filename(player_name)

                # Save path
                save_dir = self.players_dir / sport / league
                save_path = save_dir / f"{safe_name}.png"

                # Save the image
                img.save(save_path, "PNG", optimize=True)

                logger.info(f"✓ Downloaded: {player_name} -> {save_path}")
                return str(save_path)

        except Exception as e:
            logger.error(f"✗ Error downloading image for {player_name}: {e}")
            return None

    def create_safe_filename(self, player_name):
        """Create a safe filename from player name."""
        # Replace special characters and spaces
        replacements = {
            "ć": "c",
            "ś": "s",
            "ń": "n",
            "ó": "o",
            "ł": "l",
            "ż": "z",
            "ź": "z",
            "á": "a",
            "é": "e",
            "í": "i",
            "ú": "u",
            "ý": "y",
            "à": "a",
            "è": "e",
            "ì": "i",
            "ò": "o",
            "ù": "u",
            "â": "a",
            "ê": "e",
            "î": "i",
            "ô": "o",
            "û": "u",
            "ä": "a",
            "ë": "e",
            "ï": "i",
            "ö": "o",
            "ü": "u",
            "ã": "a",
            "ñ": "n",
            "õ": "o",
            " ": "_",
        }

        safe_name = player_name.lower()
        for old, new in replacements.items():
            safe_name = safe_name.replace(old, new)

        # Remove any remaining non-alphanumeric characters except underscores
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

        # Remove multiple consecutive underscores
        while "__" in safe_name:
            safe_name = safe_name.replace("__", "_")

        # Remove leading/trailing underscores
        safe_name = safe_name.strip("_")

        return safe_name

    def download_sport_players(self, sport, league, players):
        """Download images for players in a specific sport/league."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {sport.upper()} - {league}")
        logger.info(f"{'='*60}")

        results = {"successful": [], "failed": [], "not_found": []}

        for i, player in enumerate(players, 1):
            logger.info(f"[{i}/{len(players)}] Processing: {player}")

            # Search for player on Wikipedia
            player_data = self.search_wikipedia_player(player)

            if player_data:
                # Download and save the image
                saved_path = self.download_and_save_image(
                    player_data["image_url"], player, sport, league
                )

                if saved_path:
                    results["successful"].append(
                        {
                            "player": player,
                            "wikipedia_title": player_data["title"],
                            "image_path": saved_path,
                            "wikipedia_url": player_data["page_url"],
                        }
                    )
                else:
                    results["failed"].append(player)
            else:
                logger.warning(f"  No Wikipedia page found for: {player}")
                results["not_found"].append(player)

            # Rate limiting
            time.sleep(self.delay_between_requests)

        # Log summary for this league
        logger.info(f"\nSummary for {sport}/{league}:")
        logger.info(f"  ✓ Successful: {len(results['successful'])}")
        logger.info(f"  ✗ Failed: {len(results['failed'])}")
        logger.info(f"  ? Not Found: {len(results['not_found'])}")

        return results

    def download_all_sports(self):
        """Download images for all sports and leagues."""
        logger.info("Starting Wikipedia player image download")
        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"Players directory: {self.players_dir}")

        # Create directories first
        self.create_directories()

        all_results = {}

        for sport, leagues in self.player_lists.items():
            all_results[sport] = {}

            for league, players in leagues.items():
                results = self.download_sport_players(sport, league, players)
                all_results[sport][league] = results

        # Save results to JSON file
        results_file = self.scripts_dir / "wikipedia_download_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        logger.info(f"\nResults saved to: {results_file}")

        # Print final summary
        self.print_final_summary(all_results)

        return all_results

    def print_final_summary(self, results):
        """Print a final summary of all downloads."""
        logger.info(f"\n{'='*60}")
        logger.info("FINAL DOWNLOAD SUMMARY")
        logger.info(f"{'='*60}")

        total_successful = 0
        total_failed = 0
        total_not_found = 0

        for sport, leagues in results.items():
            logger.info(f"\n{sport.upper()}:")
            for league, league_results in leagues.items():
                successful = len(league_results["successful"])
                failed = len(league_results["failed"])
                not_found = len(league_results["not_found"])

                total_successful += successful
                total_failed += failed
                total_not_found += not_found

                logger.info(f"  {league}: {successful} ✓, {failed} ✗, {not_found} ?")

        logger.info(f"\nTOTALS:")
        logger.info(f"  ✓ Successful: {total_successful}")
        logger.info(f"  ✗ Failed: {total_failed}")
        logger.info(f"  ? Not Found: {total_not_found}")
        logger.info(
            f"  Total Attempted: {total_successful + total_failed + total_not_found}"
        )

        # Show failed/not found players
        if total_failed > 0 or total_not_found > 0:
            logger.info(f"\nFailed/Not Found Players:")
            for sport, leagues in results.items():
                for league, league_results in leagues.items():
                    if league_results["failed"]:
                        logger.info(
                            f"  {sport}/{league} - Failed: {', '.join(league_results['failed'])}"
                        )
                    if league_results["not_found"]:
                        logger.info(
                            f"  {sport}/{league} - Not Found: {', '.join(league_results['not_found'])}"
                        )


def main():
    """Main function to run the downloader."""
    downloader = WikipediaImageDownloader()

    try:
        results = downloader.download_all_sports()
        logger.info("\n🎉 Wikipedia player image download completed!")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Download interrupted by user")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
