#!/usr/bin/env python3
"""
Tennis Player Image Downloader
Downloads ATP and WTA player images from Wikipedia.
"""

import json
import logging
import os
import sys
import time
import urllib.parse
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

# Add the parent directory to the path to import config modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TennisPlayerDownloader:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.players_dir = self.base_dir / "static" / "logos" / "players" / "tennis"

        # Tennis players by league
        self.tennis_players = {
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
        }

        # Wikipedia API
        self.wikipedia_api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        self.delay = 1.0

        # Create directories
        self.players_dir.mkdir(parents=True, exist_ok=True)
        for league in ["ATP", "WTA"]:
            league_dir = self.players_dir / league
            league_dir.mkdir(exist_ok=True)

    def search_wikipedia_player(self, player_name):
        """Search for a tennis player on Wikipedia."""
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

            # Try with "tennis" suffix
            tennis_name = f"{player_name} (tennis)"
            encoded_tennis_name = urllib.parse.quote(tennis_name.replace(" ", "_"))
            url = f"{self.wikipedia_api_url}{encoded_tennis_name}"

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
        """Download and save a tennis player image."""
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

                # Create safe filename - handle special characters properly
                safe_name = player_name.lower().replace(" ", "_")
                # Handle special characters and accents
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
                    "ç": "c",
                    "ă": "a",
                    "ș": "s",
                    "ț": "t",
                    "î": "i",
                    "š": "s",
                    "č": "c",
                    "ř": "r",
                    "ž": "z",
                    "ě": "e",
                    "ů": "u",
                    "ň": "n",
                    "ď": "d",
                    "ť": "t",
                    "ľ": "l",
                }
                for old, new in replacements.items():
                    safe_name = safe_name.replace(old, new)
                safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

                # Save path
                save_dir = self.players_dir / league
                save_path = save_dir / f"{safe_name}.png"

                img.save(save_path, "PNG", optimize=True)

                logger.info(f"✓ Downloaded: {player_name} ({league}) -> {save_path}")
                return str(save_path)

        except Exception as e:
            logger.error(f"✗ Error downloading {player_name}: {e}")
            # Log the specific error type for debugging
            if isinstance(e, UnicodeDecodeError):
                logger.error(f"  Unicode error details: {e}")
            elif isinstance(e, requests.RequestException):
                logger.error(f"  Request error details: {e}")
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

    def download_all_tennis_players(self):
        """Download all tennis player images."""
        logger.info("🎾 Starting Tennis Player Image Download")

        all_results = {}

        for league, players in self.tennis_players.items():
            results = self.download_league_players(league, players)
            all_results[league] = results

        # Save results
        results_file = self.base_dir / "scripts" / "tennis_download_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        logger.info(f"\nResults saved to: {results_file}")

        # Final summary
        total_successful = sum(len(r["successful"]) for r in all_results.values())
        total_failed = sum(len(r["failed"]) for r in all_results.values())
        total_not_found = sum(len(r["not_found"]) for r in all_results.values())

        logger.info(f"\n🎾 TENNIS DOWNLOAD COMPLETE:")
        logger.info(f"  ✓ Total Successful: {total_successful}")
        logger.info(f"  ✗ Total Failed: {total_failed}")
        logger.info(f"  ? Total Not Found: {total_not_found}")

        return all_results


def main():
    downloader = TennisPlayerDownloader()

    try:
        results = downloader.download_all_tennis_players()
        logger.info("\n🎉 Tennis player download completed!")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Download interrupted by user")
    except Exception as e:
        logger.error(f"💥 Error: {e}")
        raise


if __name__ == "__main__":
    main()
