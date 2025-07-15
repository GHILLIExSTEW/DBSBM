#!/usr/bin/env python3
"""
Golf Player Image Downloader
Downloads PGA and LPGA player images from Wikipedia.
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
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GolfPlayerDownloader:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.players_dir = self.base_dir / "static" / "logos" / "players" / "golf"

        # Golf players by league
        self.golf_players = {
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
        }

        # Wikipedia API
        self.wikipedia_api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        self.delay = 1.0

        # Create directories
        self.players_dir.mkdir(parents=True, exist_ok=True)
        for league in ["PGA", "LPGA"]:
            league_dir = self.players_dir / league
            league_dir.mkdir(exist_ok=True)

    def search_wikipedia_player(self, player_name):
        """Search for a golf player on Wikipedia."""
        try:
            # Proper User-Agent header following Wikipedia's policy
            headers = {
                "User-Agent": "DBSBM-BettingBot/1.0 (https://github.com/your-repo; kaleb@example.com) python-requests/2.31.0"
            }

            # Try direct page lookup
            encoded_name = urllib.parse.quote(player_name.replace(" ", "_"))
            url = f"{self.wikipedia_api_url}{encoded_name}"

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "thumbnail" in data and data["thumbnail"]:
                    return {
                        "title": data["title"],
                        "image_url": data["thumbnail"]["source"],
                        "page_url": data["content_urls"]["desktop"]["page"],
                    }

            # Try with "golf" suffix
            golf_name = f"{player_name} (golfer)"
            encoded_golf_name = urllib.parse.quote(golf_name.replace(" ", "_"))
            url = f"{self.wikipedia_api_url}{encoded_golf_name}"

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "thumbnail" in data and data["thumbnail"]:
                    return {
                        "title": data["title"],
                        "image_url": data["thumbnail"]["source"],
                        "page_url": data["content_urls"]["desktop"]["page"],
                    }

            return None

        except Exception as e:
            logger.error(f"Error searching for {player_name}: {e}")
            return None

    def download_and_save_image(self, image_url, player_name, league):
        """Download and save a golf player image."""
        try:
            # Proper User-Agent header for image downloads
            headers = {
                "User-Agent": "DBSBM-BettingBot/1.0 (https://github.com/your-repo; kaleb@example.com) python-requests/2.31.0"
            }

            response = requests.get(image_url, headers=headers, timeout=15)
            response.raise_for_status()

            with Image.open(BytesIO(response.content)) as img:
                if img.mode != "RGBA":
                    img = img.convert("RGBA")

                # Resize to 200x200
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)

                # Create safe filename
                safe_name = player_name.lower().replace(" ", "_")
                safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

                # Save path
                save_dir = self.players_dir / league
                save_path = save_dir / f"{safe_name}.png"

                img.save(save_path, "PNG", optimize=True)

                logger.info(f"✓ Downloaded: {player_name} ({league}) -> {save_path}")
                return str(save_path)

        except Exception as e:
            logger.error(f"✗ Error downloading {player_name}: {e}")
            return None

    def download_league_players(self, league, players):
        """Download images for players in a specific league."""
        logger.info(f"\n{'='*50}")
        logger.info(f"Downloading {league} players ({len(players)} players)")
        logger.info(f"{'='*50}")

        successful = []
        failed = []
        not_found = []

        for i, player in enumerate(players, 1):
            logger.info(f"[{i}/{len(players)}] Processing: {player}")

            player_data = self.search_wikipedia_player(player)

            if player_data:
                saved_path = self.download_and_save_image(
                    player_data["image_url"], player, league
                )

                if saved_path:
                    successful.append(player)
                else:
                    failed.append(player)
            else:
                logger.warning(f"  No Wikipedia page found for: {player}")
                not_found.append(player)

            time.sleep(self.delay)

        logger.info(f"\n{league} Summary:")
        logger.info(f"  ✓ Successful: {len(successful)}")
        logger.info(f"  ✗ Failed: {len(failed)}")
        logger.info(f"  ? Not Found: {len(not_found)}")

        return {"successful": successful, "failed": failed, "not_found": not_found}

    def download_all_golf_players(self):
        """Download all golf player images."""
        logger.info("⛳ Starting Golf Player Image Download")

        all_results = {}

        for league, players in self.golf_players.items():
            results = self.download_league_players(league, players)
            all_results[league] = results

        # Save results
        results_file = self.base_dir / "scripts" / "golf_download_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        logger.info(f"\nResults saved to: {results_file}")

        # Final summary
        total_successful = sum(len(r["successful"]) for r in all_results.values())
        total_failed = sum(len(r["failed"]) for r in all_results.values())
        total_not_found = sum(len(r["not_found"]) for r in all_results.values())

        logger.info(f"\n⛳ GOLF DOWNLOAD COMPLETE:")
        logger.info(f"  ✓ Total Successful: {total_successful}")
        logger.info(f"  ✗ Total Failed: {total_failed}")
        logger.info(f"  ? Total Not Found: {total_not_found}")

        return all_results


def main():
    downloader = GolfPlayerDownloader()

    try:
        results = downloader.download_all_golf_players()
        logger.info("\n🎉 Golf player download completed!")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Download interrupted by user")
    except Exception as e:
        logger.error(f"💥 Error: {e}")
        raise


if __name__ == "__main__":
    main()
