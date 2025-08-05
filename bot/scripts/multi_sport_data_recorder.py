#!/usr/bin/env python3
"""
Multi-Sport Data Recorder
Comprehensive script to fetch and record data from multiple sports APIs.
Currently supports: Tennis, Darts
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

from data.db_manager import DatabaseManager
from utils.multi_provider_api import MultiProviderAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MultiSportDataRecorder:
    """Comprehensive multi-sport data recorder that fetches and saves data from multiple sports."""

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
        self.api = MultiProviderAPI(self.db_manager._pool)
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
            # The API already provides league information in each match
            dummy_league = {"id": "all", "name": "All Tennis Leagues"}
            matches = await self.api.fetch_games("tennis", dummy_league, date)

            if matches:
                # Remove duplicates based on match ID
                unique_matches = {}
                for match in matches:
                    match_id = match.get("api_game_id", match.get("id", ""))
                    if match_id:
                        unique_matches[match_id] = match

                logger.info(f"Total unique tennis matches found: {len(unique_matches)}")
                return list(unique_matches.values())
            else:
                logger.info(f"No tennis matches found for {date}")
                return []

        except Exception as e:
            logger.error(f"Error fetching tennis matches: {e}")
            return []

    async def fetch_darts_matches(self, date: str) -> List[Dict]:
        """Fetch darts matches for a specific date."""
        try:
            logger.info(f"Fetching darts matches for {date}")

            # For RapidAPI Darts, we can get all matches for a date in one request
            # The API already provides league information in each match
            dummy_league = {"id": "all", "name": "All Darts Leagues"}
            matches = await self.api.fetch_games("darts", dummy_league, date)

            if matches:
                # Remove duplicates based on match ID
                unique_matches = {}
                for match in matches:
                    match_id = match.get("api_game_id", match.get("id", ""))
                    if match_id:
                        unique_matches[match_id] = match

                logger.info(f"Total unique darts matches found: {len(unique_matches)}")
                return list(unique_matches.values())
            else:
                logger.info(f"No darts matches found for {date}")
                return []

        except Exception as e:
            logger.error(f"Error fetching darts matches: {e}")
            return []

    async def fetch_golf_events(self, date: str) -> List[Dict]:
        """Fetch golf events for a specific date."""
        try:
            logger.info(f"Fetching golf events for {date}")

            # For RapidAPI Golf, we can get all events for a date in one request
            # The API already provides tournament information in each event
            dummy_league = {"id": "all", "name": "All Golf Tournaments"}
            events = await self.api.fetch_games("golf", dummy_league, date)

            if events:
                # Remove duplicates based on event ID
                unique_events = {}
                for event in events:
                    event_id = event.get("api_game_id", event.get("id", ""))
                    if event_id:
                        unique_events[event_id] = event

                logger.info(f"Total unique golf events found: {len(unique_events)}")
                return list(unique_events.values())
            else:
                logger.info(f"No golf events found for {date}")
                return []

        except Exception as e:
            logger.error(f"Error fetching golf events: {e}")
            return []

    async def save_match_to_db(self, match: Dict) -> bool:
        """Save a match to the database."""
        try:
            # Extract match data with safe gets
            api_game_id = str(match.get("api_game_id", match.get("id", "")))
            sport = match.get("sport", "Unknown")
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

    async def process_matches_in_batches(self, matches: List[Dict], sport: str) -> Dict:
        """Process matches in batches with delays to respect rate limits."""
        results = {
            "sport": sport,
            "total_matches": len(matches),
            "matches_saved": 0,
            "errors": 0,
            "batches_processed": 0,
        }

        # Limit matches if specified
        if self.max_matches and len(matches) > self.max_matches:
            matches = matches[: self.max_matches]
            logger.info(f"Limited {sport} to {self.max_matches} matches")

        # Process in batches
        for i in range(0, len(matches), self.batch_size):
            batch = matches[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(matches) + self.batch_size - 1) // self.batch_size

            logger.info(
                f"Processing {sport} batch {batch_num}/{total_batches} ({len(batch)} matches)"
            )

            # Process batch
            for match in batch:
                success = await self.save_match_to_db(match)
                if success:
                    results["matches_saved"] += 1
                else:
                    results["errors"] += 1

            results["batches_processed"] += 1

            # Add delay between batches (except for the last batch)
            if i + self.batch_size < len(matches):
                logger.info(
                    f"Waiting {self.delay_between_batches} seconds before next {sport} batch..."
                )
                await asyncio.sleep(self.delay_between_batches)

        return results

    async def record_sport_data(self, sport: str, date: str) -> Dict:
        """Record data for a specific sport and date."""
        logger.info(f"Starting {sport} data recording for {date}")

        # Fetch matches based on sport
        if sport.lower() == "tennis":
            matches = await self.fetch_tennis_matches(date)
        elif sport.lower() == "darts":
            matches = await self.fetch_darts_matches(date)
        elif sport.lower() == "golf":
            matches = await self.fetch_golf_events(date)
        else:
            logger.error(f"Unsupported sport: {sport}")
            return {"error": f"Unsupported sport: {sport}"}

        if not matches:
            logger.warning(f"No {sport} matches found")
            return {"error": f"No {sport} matches found"}

        # Process matches in batches
        results = await self.process_matches_in_batches(matches, sport)

        logger.info(f"{sport} data recording completed:")
        logger.info(f"  Total matches: {results['total_matches']}")
        logger.info(f"  Matches saved: {results['matches_saved']}")
        logger.info(f"  Errors: {results['errors']}")
        logger.info(f"  Batches processed: {results['batches_processed']}")

        return results

    async def record_all_sports_data(self, sports: List[str], date: str) -> Dict:
        """Record data for multiple sports on a specific date."""
        logger.info(f"Starting multi-sport data recording for {date}")
        logger.info(f"Sports to process: {', '.join(sports)}")

        all_results = {}

        for sport in sports:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {sport.upper()}")
            logger.info(f"{'='*60}")

            result = await self.record_sport_data(sport, date)
            all_results[sport] = result

            # Add delay between sports
            if sport != sports[-1]:  # Not the last sport
                logger.info(f"Waiting 3 seconds before processing next sport...")
                await asyncio.sleep(3.0)

        # Summary
        total_matches = sum(
            r.get("matches_saved", 0)
            for r in all_results.values()
            if isinstance(r, dict)
        )
        total_errors = sum(
            r.get("errors", 0) for r in all_results.values() if isinstance(r, dict)
        )

        logger.info(f"\n{'='*60}")
        logger.info(f"MULTI-SPORT DATA RECORDING SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Date: {date}")
        logger.info(f"Total Matches Saved: {total_matches}")
        logger.info(f"Total Errors: {total_errors}")
        logger.info(
            f"Success Rate: {((total_matches / (total_matches + total_errors)) * 100):.1f}%"
            if (total_matches + total_errors) > 0
            else "N/A"
        )

        return all_results


async def main():
    parser = argparse.ArgumentParser(description="Multi-Sport Data Recorder")
    parser.add_argument(
        "--date",
        default=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        help="Date to fetch matches for (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--sports",
        nargs="+",
        default=["tennis", "darts", "golf"],
        help="Sports to process (default: tennis darts golf)",
    )
    parser.add_argument(
        "--max-matches",
        type=int,
        default=None,
        help="Maximum number of matches to process per sport (default: all)",
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
    async with MultiSportDataRecorder(
        max_matches=args.max_matches,
        batch_size=args.batch_size,
        delay_between_batches=args.delay,
    ) as recorder:
        results = await recorder.record_all_sports_data(args.sports, args.date)
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
