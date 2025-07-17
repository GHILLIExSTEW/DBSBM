#!/usr/bin/env python3
"""
Search for Tennis matches tomorrow.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def search_tennis_tomorrow():
    """Search for Tennis matches tomorrow."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    logger.info(f"🔍 Searching for Tennis matches on {tomorrow}...")
    logger.info("=" * 60)

    async with MultiProviderAPI() as api:
        try:
            # Discover all tennis leagues
            logger.info("📋 Discovering Tennis leagues...")
            leagues = await api.discover_leagues("tennis")

            if not leagues:
                logger.error("❌ No Tennis leagues found!")
                return

            logger.info(f"✅ Found {len(leagues)} Tennis leagues")

            # Get all matches for tomorrow (no need to iterate through leagues)
            logger.info("🎯 Fetching all Tennis matches for tomorrow...")

            try:
                # Use a dummy league object since we're not filtering by league
                dummy_league = {"id": "all", "name": "All Leagues"}
                matches = await api.fetch_games("tennis", dummy_league, tomorrow)

                if matches:
                    # Remove duplicates based on match ID
                    unique_matches = {}
                    for match in matches:
                        match_id = match.get("api_game_id")
                        if match_id and match_id not in unique_matches:
                            unique_matches[match_id] = match

                    all_matches = list(unique_matches.values())
                    logger.info(
                        f"✅ Found {len(all_matches)} unique matches for tomorrow"
                    )

                    # Show match details
                    for j, match in enumerate(
                        all_matches[:10]
                    ):  # Show first 10 matches
                        home = match.get("home_team_name", "Unknown")
                        away = match.get("away_team_name", "Unknown")
                        league = match.get("league_name", "Unknown")
                        start_time = match.get("start_time", "Unknown")

                        logger.info(f"  {j+1}. {home} vs {away}")
                        logger.info(f"     League: {league}")
                        logger.info(f"     Start Time: {start_time}")
                else:
                    logger.info("⚠️  No matches found for tomorrow")
                    all_matches = []

            except Exception as e:
                logger.error(f"❌ Error fetching matches: {e}")
                all_matches = []

            # Summary
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 SUMMARY FOR {tomorrow}")
            logger.info("=" * 60)
            logger.info(f"Total Tennis Leagues: {len(leagues)}")
            logger.info(f"Total Matches Found: {len(all_matches)}")

            if all_matches:
                logger.info(f"\n🎯 MATCHES TOMORROW ({tomorrow}):")
                for i, match in enumerate(all_matches, 1):
                    home = match.get("home_team_name", "Unknown")
                    away = match.get("away_team_name", "Unknown")
                    league = match.get("league_name", "Unknown")
                    start_time = match.get("start_time", "Unknown")

                    logger.info(f"{i:2d}. {home} vs {away}")
                    logger.info(f"    League: {league}")
                    logger.info(f"    Time: {start_time}")
                    logger.info()
            else:
                logger.info("😔 No Tennis matches found for tomorrow")

        except Exception as e:
            logger.error(f"❌ Error searching for Tennis matches: {e}")


async def main():
    """Run the search."""
    await search_tennis_tomorrow()


if __name__ == "__main__":
    asyncio.run(main())
