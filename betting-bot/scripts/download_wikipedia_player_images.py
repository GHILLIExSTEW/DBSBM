#!/usr/bin/env python3
"""
Wikipedia Player Image Downloader
Downloads player images from Wikipedia for darts, tennis, and golf.
Organizes images in the same format as existing player images.
"""

import os
import sys
import requests
import time
import json
import csv
from pathlib import Path
from PIL import Image
from io import BytesIO
import urllib.parse
import logging

# Add the parent directory to the path to import config modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.image_settings import LOGO_SIZE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wikipedia_download.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WikipediaPlayerImageDownloader:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.static_dir = self.base_dir / "static"
        self.logos_dir = self.static_dir / "logos"
        self.players_dir = self.logos_dir / "players"

        # Create directories if they don't exist
        self.players_dir.mkdir(parents=True, exist_ok=True)

        # Player lists for each sport
        self.player_lists = {
            "tennis": {
                "ATP": [
                    "Novak Djokovic",
                    "Carlos Alcaraz",
                    "Daniil Medvedev",
                    "Jannik Sinner",
                    "Andrey Rublev",
                    "Stefanos Tsitsipas",
                    "Alexander Zverev",
                    "Casper Ruud",
                    "Hubert Hurkacz",
                    "Taylor Fritz",
                    "Holger Rune",
                    "Karen Khachanov",
                    "Frances Tiafoe",
                    "Tommy Paul",
                    "Ben Shelton",
                    "Sebastian Korda",
                    "Felix Auger-Aliassime",
                    "Denis Shapovalov",
                    "Grigor Dimitrov",
                    "Lorenzo Musetti",
                ],
                "WTA": [
                    "Iga Świątek",
                    "Aryna Sabalenka",
                    "Coco Gauff",
                    "Elena Rybakina",
                    "Jessica Pegula",
                    "Ons Jabeur",
                    "Markéta Vondroušová",
                    "Karolína Muchová",
                    "Maria Sakkari",
                    "Barbora Krejčíková",
                    "Daria Kasatkina",
                    "Veronika Kudermetova",
                    "Madison Keys",
                    "Belinda Bencic",
                    "Liudmila Samsonova",
                    "Victoria Azarenka",
                    "Petra Kvitová",
                    "Caroline Garcia",
                    "Beatriz Haddad Maia",
                    "Elina Svitolina",
                ],
            },
            "darts": {
                "PDC": [
                    "Luke Humphries",
                    "Michael van Gerwen",
                    "Michael Smith",
                    "Nathan Aspinall",
                    "Gerwyn Price",
                    "Rob Cross",
                    "Peter Wright",
                    "Dimitri Van den Bergh",
                    "Jonny Clayton",
                    "Danny Noppert",
                    "Joe Cullen",
                    "Damon Heta",
                    "Dave Chisnall",
                    "Chris Dobey",
                    "Ross Smith",
                    "Josh Rock",
                    "Andrew Gilding",
                    "Stephen Bunting",
                    "Ryan Searle",
                    "Krzysztof Ratajski",
                ],
                "BDO": [
                    "Glen Durrant",
                    "Scott Waites",
                    "Scott Mitchell",
                    "Mark McGeeney",
                    "Jim Williams",
                    "Wayne Warren",
                    "Mikuru Suzuki",
                    "Lisa Ashton",
                    "Anastasia Dobromyslova",
                    "Deta Hedman",
                    "Fallon Sherrock",
                    "Beau Greaves",
                ],
            },
            "golf": {
                "PGA": [
                    "Scottie Scheffler",
                    "Rory McIlroy",
                    "Jon Rahm",
                    "Viktor Hovland",
                    "Patrick Cantlay",
                    "Xander Schauffele",
                    "Max Homa",
                    "Wyndham Clark",
                    "Brian Harman",
                    "Tommy Fleetwood",
                    "Tyrrell Hatton",
                    "Jordan Spieth",
                    "Justin Thomas",
                    "Collin Morikawa",
                    "Sam Burns",
                    "Tony Finau",
                    "Sungjae Im",
                    "Cameron Young",
                    "Keegan Bradley",
                    "Rickie Fowler",
                ],
                "LPGA": [
                    "Lilia Vu",
                    "Celine Boutier",
                    "Ruoning Yin",
                    "Atthaya Thitikul",
                    "Nelly Korda",
                    "Jin Young Ko",
                    "Minjee Lee",
                    "Hyo Joo Kim",
                    "Charley Hull",
                    "Linn Grant",
                    "Leona Maguire",
                    "Brooke Henderson",
                    "Danielle Kang",
                    "Nasa Hataoka",
                    "Hannah Green",
                    "Alison Lee",
                    "Megan Khang",
                    "Jennifer Kupcho",
                    "Andrea Lee",
                    "Grace Kim",
                ],
            },
        }

        # Wikipedia API endpoints
        self.wikipedia_api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        self.wikipedia_search_url = "https://en.wikipedia.org/w/api.php"

        # Rate limiting
        self.delay_between_requests = 1.0  # seconds

    def create_sport_directories(self):
        """Create the necessary directory structure for each sport."""
        for sport, leagues in self.player_lists.items():
            sport_dir = self.players_dir / sport
            sport_dir.mkdir(exist_ok=True)

            for league in leagues:
                league_dir = sport_dir / league
                league_dir.mkdir(exist_ok=True)

                # Create .gitkeep files for empty directories
                gitkeep_file = league_dir / ".gitkeep"
                if not gitkeep_file.exists():
                    gitkeep_file.touch()

        logger.info("Created directory structure for all sports and leagues")

    def search_wikipedia_player(self, player_name):
        """Search for a player on Wikipedia and return the best match."""
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
                "srsearch": player_name,
                "srlimit": 5,
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
                    # Try the first search result
                    first_result = data["query"]["search"][0]
                    page_title = first_result["title"]

                    # Get the page summary for the first result
                    encoded_title = urllib.parse.quote(page_title.replace(" ", "_"))
                    summary_url = f"{self.wikipedia_api_url}{encoded_title}"

                    summary_response = requests.get(summary_url, timeout=10)
                    if summary_response.status_code == 200:
                        summary_data = summary_response.json()
                        if "thumbnail" in summary_data and summary_data["thumbnail"]:
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

    def download_and_process_image(self, image_url, player_name, sport, league):
        """Download and process an image for a player."""
        try:
            # Download the image
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()

            # Open and process the image
            with Image.open(BytesIO(response.content)) as img:
                # Convert to RGBA if needed
                if img.mode != "RGBA":
                    img = img.convert("RGBA")

                # Resize to standard logo size
                img.thumbnail(LOGO_SIZE, Image.Resampling.LANCZOS)

                # Create filename
                safe_name = (
                    player_name.lower()
                    .replace(" ", "_")
                    .replace("ć", "c")
                    .replace("ś", "s")
                    .replace("ń", "n")
                    .replace("ó", "o")
                    .replace("ł", "l")
                    .replace("ż", "z")
                    .replace("ź", "z")
                )
                safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

                # Save path
                save_dir = self.players_dir / sport / league
                save_path = save_dir / f"{safe_name}.png"

                # Save the image
                img.save(save_path, "PNG", optimize=True)

                logger.info(f"Downloaded and saved: {player_name} -> {save_path}")
                return str(save_path)

        except Exception as e:
            logger.error(f"Error downloading image for {player_name}: {e}")
            return None

    def download_player_images(self, sport, league, players):
        """Download images for a list of players in a specific league."""
        logger.info(f"Starting download for {sport}/{league} ({len(players)} players)")

        results = {"successful": [], "failed": [], "not_found": []}

        for player in players:
            logger.info(f"Processing: {player}")

            # Search for player on Wikipedia
            player_data = self.search_wikipedia_player(player)

            if player_data:
                # Download and save the image
                saved_path = self.download_and_process_image(
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
                results["not_found"].append(player)

            # Rate limiting
            time.sleep(self.delay_between_requests)

        return results

    def download_all_sports(self):
        """Download images for all sports and leagues."""
        logger.info("Starting Wikipedia player image download for all sports")

        all_results = {}

        # Create directories first
        self.create_sport_directories()

        for sport, leagues in self.player_lists.items():
            all_results[sport] = {}

            for league, players in leagues.items():
                logger.info(f"\n{'='*50}")
                logger.info(f"Processing {sport.upper()} - {league}")
                logger.info(f"{'='*50}")

                results = self.download_player_images(sport, league, players)
                all_results[sport][league] = results

                # Log summary
                logger.info(f"Summary for {sport}/{league}:")
                logger.info(f"  Successful: {len(results['successful'])}")
                logger.info(f"  Failed: {len(results['failed'])}")
                logger.info(f"  Not Found: {len(results['not_found'])}")

        # Save results to JSON file
        results_file = self.base_dir / "scripts" / "wikipedia_download_results.json"
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

                logger.info(
                    f"  {league}: {successful} successful, {failed} failed, {not_found} not found"
                )

        logger.info(f"\nTOTALS:")
        logger.info(f"  Successful: {total_successful}")
        logger.info(f"  Failed: {total_failed}")
        logger.info(f"  Not Found: {total_not_found}")
        logger.info(
            f"  Total Attempted: {total_successful + total_failed + total_not_found}"
        )

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
    downloader = WikipediaPlayerImageDownloader()

    try:
        results = downloader.download_all_sports()
        logger.info("Wikipedia player image download completed successfully!")

    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
