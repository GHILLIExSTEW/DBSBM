#!/usr/bin/env python3
"""
Simple Master Player Image Downloader
Downloads player images from Wikipedia for darts, tennis, and golf.
Runs the downloader classes directly instead of using subprocess.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to the path to import config modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the downloader classes
from scripts.download_tennis_players import TennisPlayerDownloader
from scripts.download_darts_players import DartsPlayerDownloader
from scripts.download_golf_players import GolfPlayerDownloader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Download player images from Wikipedia for darts, tennis, and golf"
    )
    parser.add_argument(
        "--sport",
        choices=["tennis", "darts", "golf", "all"],
        default="all",
        help="Which sport to download (default: all)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip sports that already have downloaded images",
    )

    args = parser.parse_args()

    # Define downloaders for each sport
    downloaders = {
        "tennis": TennisPlayerDownloader,
        "darts": DartsPlayerDownloader,
        "golf": GolfPlayerDownloader,
    }

    base_dir = Path(__file__).parent.parent
    players_dir = base_dir / "static" / "logos" / "players"

    logger.info("🎯 Starting Player Image Download from Wikipedia")
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Players directory: {players_dir}")

    if args.sport == "all":
        sports_to_run = list(downloaders.keys())
    else:
        sports_to_run = [args.sport]

    successful_sports = []
    failed_sports = []

    for sport in sports_to_run:
        if args.skip_existing:
            # Check if sport directory exists and has images
            sport_dir = players_dir / sport
            if sport_dir.exists():
                # Count PNG files in subdirectories
                png_count = 0
                for subdir in sport_dir.iterdir():
                    if subdir.is_dir():
                        png_count += len(list(subdir.glob("*.png")))

                if png_count > 0:
                    logger.info(
                        f"⏭️ Skipping {sport} - {png_count} images already exist"
                    )
                    continue

        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting {sport.upper()} player download")
            logger.info(f"{'='*60}")

            # Create downloader instance and run
            downloader_class = downloaders[sport]
            downloader = downloader_class()

            if sport == "tennis":
                results = downloader.download_all_tennis_players()
            elif sport == "darts":
                results = downloader.download_all_darts_players()
            elif sport == "golf":
                results = downloader.download_all_golf_players()

            logger.info(f"✅ {sport} download completed successfully")
            successful_sports.append(sport)

        except Exception as e:
            logger.error(f"❌ {sport} download failed: {e}")
            failed_sports.append(sport)

    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'='*60}")

    if successful_sports:
        logger.info(f"✅ Successful: {', '.join(successful_sports)}")

    if failed_sports:
        logger.info(f"❌ Failed: {', '.join(failed_sports)}")

    logger.info(f"\nTotal sports processed: {len(sports_to_run)}")
    logger.info(f"Successful: {len(successful_sports)}")
    logger.info(f"Failed: {len(failed_sports)}")

    if failed_sports:
        logger.info(f"\nTo retry failed sports, run:")
        for sport in failed_sports:
            logger.info(f"  python scripts/download_{sport}_players.py")

    logger.info("\n🎉 Player image download process completed!")


if __name__ == "__main__":
    main()
