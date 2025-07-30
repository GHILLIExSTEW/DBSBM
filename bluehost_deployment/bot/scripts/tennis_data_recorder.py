#!/usr/bin/env python3
"""
Tennis Data Recorder
Comprehensive script to fetch and record tennis data from RapidAPI Tennis Devs API.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from bot.data.db_manager import DatabaseManager
from bot.utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TennisDataRecorder:
    """Comprehensive tennis data recorder that fetches and saves tennis data."""

    def __init__(
        self,
        max_matches: int = None,
        batch_size: int = 50,
        delay_between_batches: float = 2.0,
    ):
        self.max_matches = max_matches
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.api = None
        self.db_manager = None

    async def __aenter__(self):
        self.db_manager = DatabaseManager()
        await self.db_manager.connect()
        self.api = MultiProviderAPI(self.db_manager.pool)
        await self.api.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.api:
            await self.api.__aexit__(exc_type, exc_val, exc_tb)
        if self.db_manager:
            await self.db_manager.close()

    async def fetch_tennis_matches(self, date: str) -> List[Dict]:
        """Fetch tennis matches for a specific date."""
        try:
            logger.info(f"Fetching tennis matches for {date}")

            # For RapidAPI Tennis, we can get all matches for a date in one request
            # Use a dummy league object since the matches-by-date endpoint returns all matches
            dummy_league = {"id": "all", "name": "All Tennis Leagues"}

            matches = await self.api.fetch_games("tennis", dummy_league, date)

            if matches:
                # Remove duplicates based on match ID
                unique_matches = {}
                for match in matches:
                    match_id = match.get("api_game_id", match.get("id", ""))
                    if match_id:
                        unique_matches[match_id] = match

                logger.info(f"Total unique matches found: {len(unique_matches)}")
                return list(unique_matches.values())
            else:
                logger.info(f"No matches found for {date}")
                return []

        except Exception as e:
            logger.error(f"Error fetching tennis matches: {e}")
            return []

    async def save_tennis_match_to_db(self, match: Dict) -> bool:
        """Save a tennis match to the database."""
        try:
            # Debug: Log the match structure
            logger.debug(f"Processing match: {type(match)} - {match}")

            # Extract match data with safe gets
            api_game_id = str(match.get("api_game_id", match.get("id", "")))
            sport = match.get("sport", "Tennis")
            league_id = str(match.get("league_id", ""))
            league_name = match.get("league_name", "")
            home_team_name = match.get("home_team_name", "")
            away_team_name = match.get("away_team_name", "")
            start_time = match.get("start_time", "")
            status = match.get("status", "upcoming")
            score = match.get("score", {})
            venue = match.get("venue", "")

            # Convert start_time to proper format if needed
            if start_time and isinstance(start_time, str):
                try:
                    # Parse and format the start time
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    start_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass

            # Prepare game data for database
            game_data = {
                "api_game_id": api_game_id,
                "sport": sport,
                "league_id": league_id,
                "league_name": league_name,
                "home_team_name": home_team_name,
                "away_team_name": away_team_name,
                "start_time": start_time,
                "status": status,
                "score": score,
                "venue": venue,
                "raw_data": match,
            }

            # Save to database
            await self.db_manager.upsert_api_game(game_data)
            return True

        except Exception as e:
            logger.error(f"Error saving match to database: {e}")
            return False

    async def process_matches_in_batches(self, matches: List[Dict]) -> Dict:
        """Process matches in batches with delays to respect rate limits."""
        results = {
            "total_matches": len(matches),
            "matches_saved": 0,
            "errors": 0,
            "batches_processed": 0,
        }

        # Limit matches if specified
        if self.max_matches and len(matches) > self.max_matches:
            matches = matches[: self.max_matches]
            logger.info(f"Limited to {self.max_matches} matches")

        # Process in batches
        for i in range(0, len(matches), self.batch_size):
            batch = matches[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(matches) + self.batch_size - 1) // self.batch_size

            logger.info(
                f"Processing batch {batch_num}/{total_batches} ({len(batch)} matches)"
            )

            # Process batch
            for match in batch:
                success = await self.save_tennis_match_to_db(match)
                if success:
                    results["matches_saved"] += 1
                else:
                    results["errors"] += 1

            results["batches_processed"] += 1

            # Add delay between batches (except for the last batch)
            if i + self.batch_size < len(matches):
                logger.info(
                    f"Waiting {self.delay_between_batches} seconds before next batch..."
                )
                await asyncio.sleep(self.delay_between_batches)

        return results

    async def record_tennis_data(self, date: str) -> Dict:
        """Main method to record tennis data for a specific date."""
        logger.info(f"Starting tennis data recording for {date}")

        # Fetch matches
        matches = await self.fetch_tennis_matches(date)
        if not matches:
            logger.warning("No matches found")
            return {"error": "No matches found"}

        # Process matches in batches
        results = await self.process_matches_in_batches(matches)

        logger.info(f"Tennis data recording completed:")
        logger.info(f"  Total matches: {results['total_matches']}")
        logger.info(f"  Matches saved: {results['matches_saved']}")
        logger.info(f"  Errors: {results['errors']}")
        logger.info(f"  Batches processed: {results['batches_processed']}")

        return results


async def main():
    parser = argparse.ArgumentParser(description="Tennis Data Recorder")
    parser.add_argument(
        "--date",
        default=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        help="Date to fetch matches for (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--max-matches",
        type=int,
        default=None,
        help="Maximum number of matches to process (default: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of matches to process per batch (default: 50)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between batches in seconds (default: 2.0)",
    )

    args = parser.parse_args()

    # Create recorder with conservative settings
    async with TennisDataRecorder(
        max_matches=args.max_matches,
        batch_size=args.batch_size,
        delay_between_batches=args.delay,
    ) as recorder:
        results = await recorder.record_tennis_data(args.date)
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
