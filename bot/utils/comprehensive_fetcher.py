print("=== COMPREHENSIVE_FETCHER.PY: FILE EXECUTION TEST LINE ===")
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).info("=== COMPREHENSIVE_FETCHER.PY: FILE EXECUTION TEST LINE ===")
"""
Comprehensive Fetcher for ALL API-Sports Leagues
Automatically fetches data for every single league available from the API.
"""

import sys
import os

# Add the bot directory to sys.path for subprocess execution
bot_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if bot_dir not in sys.path:
    sys.path.insert(0, bot_dir)

from utils.league_discovery import SPORT_ENDPOINTS, LeagueDiscovery
from utils.fetcher_logger import (
    get_fetcher_logger,
    log_fetcher_operation,
    log_fetcher_error,
    log_fetcher_statistics,
    log_fetcher_startup,
    log_fetcher_shutdown,
    log_league_fetch,
    log_api_request,
    log_database_operation,
    log_memory_usage,
    log_cleanup_operation,
)
import asyncio
import logging
import os
import psutil
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from zoneinfo import ZoneInfo

import aiohttp
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Get the custom fetcher logger
fetcher_logger = get_fetcher_logger()
logger = fetcher_logger  # Use the custom logger for all logging

# Import the league discovery utility

# Timezone constants
EST = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


class ComprehensiveFetcher:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.api_key = API_KEY
        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables")
        # Never log API keys

        self.session = None
        self.discovered_leagues = {}
        self.failed_leagues = set()
        self.successful_fetches = 0
        self.total_fetches = 0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def discover_all_leagues(self) -> Dict[str, List[Dict]]:
        """Dynamically build league list from LEAGUE_CONFIG, grouping by sport, so only mapped leagues are queried."""
        from config.leagues import LEAGUE_CONFIG
        log_fetcher_operation("Starting league discovery (using mapped leagues from LEAGUE_CONFIG)")
        all_leagues = {}
        for league_key, league_info in LEAGUE_CONFIG.items():
            # Skip manual/other/generic entries
            if league_key.upper() in ("MANUAL", "OTHER"):
                continue
            sport = league_info.get("sport", "Unknown").lower()
            # Use league_key as id if no id is present
            league_id = league_info.get("id", league_key)
            league_dict = {
                "id": league_id,
                "name": league_info.get("name", league_key),
                "country": league_info.get("country", None),
                "season": 2025,  # You can make this dynamic if needed
                "league_key": league_key
            }
            all_leagues.setdefault(sport, []).append(league_dict)
        self.discovered_leagues = all_leagues
        logger.info(f"Loaded {sum(len(l) for l in all_leagues.values())} leagues across {len(all_leagues)} sports (mapped)")
        return all_leagues

    async def fetch_all_leagues_data(
        self, date: str = None, next_days: int = 2
    ) -> dict:
        """Fetch data for ALL discovered leagues and collect HTTP status codes and errors."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        log_fetcher_operation(
            "Starting comprehensive fetch", {"date": date, "next_days": next_days}
        )

        # Clear existing data
        await self.clear_api_games_table()

        results = {
            "total_leagues": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "total_games": 0,
            "http_status_codes": [],
        }

        # Fetch for each sport and league
        for sport, leagues in self.discovered_leagues.items():
            logger.info(f"Processing {len(leagues)} leagues for {sport}")

            for league in leagues:
                # Only process league dicts (should always be dicts now)
                if not isinstance(league, dict):
                    logger.warning(f"Skipping league that is not a dict: {league}")
                    continue

                results["total_leagues"] += 1

                try:
                    # Fetch for multiple days
                    for day_offset in range(next_days):
                        fetch_date = (
                            datetime.strptime(date, "%Y-%m-%d")
                            + timedelta(days=day_offset)
                        ).strftime("%Y-%m-%d")

                        games_fetched, status_code, error_msg = await self._fetch_league_games(
                            sport, league, fetch_date, collect_status=True
                        )
                        results["http_status_codes"].append({
                            "sport": sport,
                            "league": league.get("name"),
                            "date": fetch_date,
                            "status_code": status_code,
                            "error": error_msg
                        })

                        if games_fetched > 0:
                            results["total_games"] += games_fetched
                            logger.info(
                                f"Fetched {games_fetched} games for {league['name']} on {fetch_date}"
                            )

                        # Rate limiting between requests - reduced for hourly operation
                        await asyncio.sleep(0.5)

                    results["successful_fetches"] += 1

                except Exception as e:
                    results["failed_fetches"] += 1
                    self.failed_leagues.add(league.get("name", str(league)))
                    log_fetcher_error(
                        f"Failed to fetch data for {league.get('name', str(league))}: {e}",
                        "league_fetch",
                    )
                    continue

        logger.info(f"Comprehensive fetch completed: {results}")
        return results

    async def _fetch_league_games(self, sport: str, league: dict, date: str, collect_status: bool = False):
        """Fetch games for a specific league on a specific date using MultiProviderAPI."""
        from utils.multi_provider_api import MultiProviderAPI
        import time
        start_time = time.time()
        status_code = None
        error_msg = None
        games_saved = 0
        try:
            # league is always a dict now
            async with MultiProviderAPI() as mpa:
                games = await mpa.fetch_games(sport, league, date)
                logger.info(f"Fetched games list: type={type(games)}, len={len(games) if hasattr(games, '__len__') else 'N/A'}, sample={games[:1] if isinstance(games, list) and games else str(games)[:200]}")
                if not games:
                    logger.warning(f"No games found for {league.get('name', league.get('id'))} on {date}")
                    error_msg = "No games found"
                for game in games:
                    try:
                        # Log the raw game dict for debugging
                        logger.info(f"Raw game dict: {game}")
                        mapped_game = self._map_game_data(game, sport, league)
                        # Log the mapped game result for debugging
                        logger.info(f"Mapped game result: {mapped_game}")
                        if not mapped_game:
                            logger.warning("Game could not be mapped: [DATA REDACTED]")
                        else:
                            logger.info("Mapped game: [DATA REDACTED]")
                            save_result = await self._save_game_to_db(mapped_game)
                            logger.info(f"Save to DB result: {save_result}")
                            if save_result:
                                games_saved += 1
                    except Exception as e:
                        log_fetcher_error(
                            f"Error processing game for {league.get('name', league.get('id'))}: {e}",
                            "game_processing",
                        )
                        continue
            log_league_fetch(sport, league.get("name", league.get("id")), True, games_saved)
            log_api_request(f"multi_provider:{sport}:{league.get('id')}", True, time.time() - start_time)
            return (games_saved, status_code, error_msg) if collect_status else games_saved
        except Exception as e:
            league_name = league.get("name") if isinstance(league, dict) else str(league)
            league_id = league.get("id") if isinstance(league, dict) else str(league)
            log_league_fetch(sport, league_name, False, 0, str(e))
            log_api_request(f"multi_provider:{sport}:{league_id}", False, time.time() - start_time, str(e))
            log_fetcher_error(
                f"Unexpected error fetching {league_name}: {e}", "league_fetch"
            )
            return (0, None, str(e)) if collect_status else 0

    def _convert_utc_to_est(self, utc_time_str: str) -> str:
        """Convert UTC time string to EST time string."""
        try:
            if not utc_time_str:
                return None

            # Parse the UTC time string
            if "T" in utc_time_str and "Z" in utc_time_str:
                # ISO format with Z suffix
                dt = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
            elif "T" in utc_time_str:
                # ISO format without Z
                dt = datetime.fromisoformat(utc_time_str)
            else:
                # Try standard format
                dt = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=UTC)

            # Convert to EST
            est_time = dt.astimezone(EST)
            return est_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Failed to convert time '{utc_time_str}' to EST: {e}")
            return utc_time_str

    def _map_football_game_data(self, game: Dict, league: Dict) -> Optional[Dict]:
        """Map football game data to our standard format."""
        # Support both API-Sports (nested) and MultiProviderAPI (flat) formats
        league_id = str(league["id"])
        if league_id == "71":
            league_name_final = "Brazil Serie A"
        elif league_id == "135":
            league_name_final = "Serie A"
        else:
            league_name_final = league["name"]

        # Try API-Sports format first
        if "fixture" in game and "id" in game["fixture"]:
            start_time_est = self._convert_utc_to_est(game["fixture"]["date"])
            return {
                "api_game_id": str(game["fixture"]["id"]),
                "sport": "Football",
                "league_id": league_id,
                "league_name": league_name_final,
                "home_team_name": game["teams"]["home"]["name"],
                "away_team_name": game["teams"]["away"]["name"],
                "start_time": start_time_est,
                "status": game["fixture"]["status"]["long"],
                "score": (
                    {
                        "home": game["goals"]["home"] if "goals" in game else None,
                        "away": game["goals"]["away"] if "goals" in game else None,
                    }
                    if "goals" in game
                    else None
                ),
                "venue": (
                    game["fixture"]["venue"]["name"] if "venue" in game["fixture"] else None
                ),
            }
        # Fallback: flat format (from MultiProviderAPI)
        # Expect keys: id, home_team_name, away_team_name, start_time, status, score, venue
        if "id" in game and "home_team_name" in game and "away_team_name" in game:
            start_time_est = self._convert_utc_to_est(game.get("start_time") or game.get("date"))
            return {
                "api_game_id": str(game["id"]),
                "sport": "Football",
                "league_id": league_id,
                "league_name": league_name_final,
                "home_team_name": game["home_team_name"],
                "away_team_name": game["away_team_name"],
                "start_time": start_time_est,
                "status": game.get("status", ""),
                "score": game.get("score"),
                "venue": game.get("venue"),
            }
        # If neither format matches, return None
        logger.warning(f"Football game format not recognized: keys={list(game.keys())}")
        return None

    def _map_basketball_game_data(self, game: Dict, league: Dict) -> Optional[Dict]:
        """Map basketball game data to our standard format."""
        # Convert UTC time to EST
        start_time_est = self._convert_utc_to_est(game["date"])

        return {
            "api_game_id": str(game["id"]),
            "sport": "Basketball",
            "league_id": str(league["id"]),
            "league_name": league["name"],
            "home_team_name": game["teams"]["home"]["name"],
            "away_team_name": game["teams"]["away"]["name"],
            "start_time": start_time_est,
            "status": game["status"]["long"],
            "score": (
                {
                    "home": game["scores"]["home"]["total"],
                    "away": game["scores"]["away"]["total"],
                }
                if "scores" in game
                else None
            ),
            "venue": game["venue"]["name"] if "venue" in game else None,
        }

    def _map_baseball_game_data(self, game: Dict, league: Dict) -> Optional[Dict]:
        """Map baseball game data to our standard format."""
        # Convert UTC time to EST
        start_time_est = self._convert_utc_to_est(game["date"])

        return {
            "api_game_id": str(game["id"]),
            "sport": "Baseball",
            "league_id": str(league["id"]),
            "league_name": league["name"],
            "home_team_name": game["teams"]["home"]["name"],
            "away_team_name": game["teams"]["away"]["name"],
            "start_time": start_time_est,
            "status": game["status"]["long"],
            "score": (
                {
                    "home": game["scores"]["home"]["total"],
                    "away": game["scores"]["away"]["total"],
                }
                if "scores" in game
                else None
            ),
            "venue": game["venue"]["name"] if "venue" in game else None,
        }

    def _map_hockey_game_data(self, game: Dict, league: Dict) -> Optional[Dict]:
        """Map hockey game data to our standard format."""
        # Convert UTC time to EST
        start_time_est = self._convert_utc_to_est(game["date"])

        return {
            "api_game_id": str(game["id"]),
            "sport": "Ice Hockey",
            "league_id": str(league["id"]),
            "league_name": league["name"],
            "home_team_name": game["teams"]["home"]["name"],
            "away_team_name": game["teams"]["away"]["name"],
            "start_time": start_time_est,
            "status": game["status"]["long"],
            "score": (
                {
                    "home": game["scores"]["home"]["total"],
                    "away": game["scores"]["away"]["total"],
                }
                if "scores" in game
                else None
            ),
            "venue": game["venue"]["name"] if "venue" in game else None,
        }

    def _map_tennis_game_data(self, game: Dict, league: Dict) -> Optional[Dict]:
        """Map tennis game data to our standard format."""
        # Convert UTC time to EST
        start_time_est = self._convert_utc_to_est(game["date"])

        return {
            "api_game_id": str(game["id"]),
            "sport": "Tennis",
            "league_id": str(league["id"]),
            "league_name": league["name"],
            "home_team_name": game["teams"]["home"]["name"],
            "away_team_name": game["teams"]["away"]["name"],
            "start_time": start_time_est,
            "status": game["status"]["long"],
            "score": (
                {
                    "home": game["scores"]["home"]["total"],
                    "away": game["scores"]["away"]["total"],
                }
                if "scores" in game
                else None
            ),
            "venue": game["venue"]["name"] if "venue" in game else None,
        }

    def _map_volleyball_game_data(self, game: Dict, league: Dict) -> Optional[Dict]:
        """Map volleyball game data to our standard format."""
        # Convert UTC time to EST
        start_time_est = self._convert_utc_to_est(game["date"])

        return {
            "api_game_id": str(game["id"]),
            "sport": "Volleyball",
            "league_id": str(league["id"]),
            "league_name": league["name"],
            "home_team_name": game["teams"]["home"]["name"],
            "away_team_name": game["teams"]["away"]["name"],
            "start_time": start_time_est,
            "status": game["status"]["long"],
            "score": (
                {
                    "home": game["scores"]["home"]["total"],
                    "away": game["scores"]["away"]["total"],
                }
                if "scores" in game
                else None
            ),
            "venue": game["venue"]["name"] if "venue" in game else None,
        }

    def _map_handball_game_data(self, game: Dict, league: Dict) -> Optional[Dict]:
        """Map handball game data to our standard format."""
        # Convert UTC time to EST
        start_time_est = self._convert_utc_to_est(game["date"])

        return {
            "api_game_id": str(game["id"]),
            "sport": "Handball",
            "league_id": str(league["id"]),
            "league_name": league["name"],
            "home_team_name": game["teams"]["home"]["name"],
            "away_team_name": game["teams"]["away"]["name"],
            "start_time": start_time_est,
            "status": game["status"]["long"],
            "score": (
                {
                    "home": game["scores"]["home"]["total"],
                    "away": game["scores"]["away"]["total"],
                }
                if "scores" in game
                else None
            ),
            "venue": game["venue"]["name"] if "venue" in game else None,
        }

    def _map_rugby_game_data(self, game: Dict, league: Dict) -> Optional[Dict]:
        """Map rugby game data to our standard format."""
        # Convert UTC time to EST
        start_time_est = self._convert_utc_to_est(game["date"])

        return {
            "api_game_id": str(game["id"]),
            "sport": "Rugby",
            "league_id": str(league["id"]),
            "league_name": league["name"],
            "home_team_name": game["teams"]["home"]["name"],
            "away_team_name": game["teams"]["away"]["name"],
            "start_time": start_time_est,
            "status": game["status"]["long"],
            "score": (
                {
                    "home": game["scores"]["home"]["total"],
                    "away": game["scores"]["away"]["total"],
                }
                if "scores" in game
                else None
            ),
            "venue": game["venue"]["name"] if "venue" in game else None,
        }

    def _map_game_data(self, game: Dict, sport: str, league: Dict) -> Optional[Dict]:
        """Map API game data to our standard format with EST time conversion."""
        try:
            # Use sport-specific mapping functions
            sport_mappers = {
                "football": self._map_football_game_data,
                "basketball": self._map_basketball_game_data,
                "baseball": self._map_baseball_game_data,
                "hockey": self._map_hockey_game_data,
                "tennis": self._map_tennis_game_data,
                "volleyball": self._map_volleyball_game_data,
                "handball": self._map_handball_game_data,
                "rugby": self._map_rugby_game_data,
                # Add darts and american football mapping inline below
            }

            # Darts mapping (flat format, as seen in logs)
            if sport == "darts":
                # Example keys: api_game_id, sport, league_id, league_name, home_team_name, away_team_name, start_time, status, score, venue
                start_time_est = self._convert_utc_to_est(game.get("start_time") or game.get("date"))
                return {
                    "api_game_id": str(game.get("api_game_id") or game.get("id")),
                    "sport": "Darts",
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_name": game.get("home_team_name") or game.get("home_team"),
                    "away_team_name": game.get("away_team_name") or game.get("away_team"),
                    "start_time": start_time_est,
                    "status": game.get("status", ""),
                    "score": game.get("score"),
                    "venue": game.get("venue"),
                }

            # American football (NFL, NCAA, CFL, etc.) mapping
            if sport == "american football":
                # Try to support both nested and flat formats
                # Nested: {"id", "teams": {"home":..., "away":...}, "date", "status", "scores", "venue"}
                # Flat: {"id", "home_team_name", ...}
                if "teams" in game and "home" in game["teams"] and "away" in game["teams"]:
                    start_time_est = self._convert_utc_to_est(game.get("date") or game.get("start_time"))
                    return {
                        "api_game_id": str(game["id"]),
                        "sport": "American Football",
                        "league_id": str(league["id"]),
                        "league_name": league["name"],
                        "home_team_name": game["teams"]["home"]["name"],
                        "away_team_name": game["teams"]["away"]["name"],
                        "start_time": start_time_est,
                        "status": game["status"]["long"] if "status" in game and isinstance(game["status"], dict) else game.get("status", ""),
                        "score": (
                            {
                                "home": game["scores"]["home"]["total"] if "scores" in game and "home" in game["scores"] else None,
                                "away": game["scores"]["away"]["total"] if "scores" in game and "away" in game["scores"] else None,
                            }
                            if "scores" in game else None
                        ),
                        "venue": game["venue"]["name"] if "venue" in game and isinstance(game["venue"], dict) else game.get("venue"),
                    }
                # Flat format fallback
                if "id" in game and "home_team_name" in game and "away_team_name" in game:
                    start_time_est = self._convert_utc_to_est(game.get("start_time") or game.get("date"))
                    return {
                        "api_game_id": str(game["id"]),
                        "sport": "American Football",
                        "league_id": str(league["id"]),
                        "league_name": league["name"],
                        "home_team_name": game["home_team_name"],
                        "away_team_name": game["away_team_name"],
                        "start_time": start_time_est,
                        "status": game.get("status", ""),
                        "score": game.get("score"),
                        "venue": game.get("venue"),
                    }

            mapper = sport_mappers.get(sport)
            if mapper:
                return mapper(game, league)
            else:
                logger.warning(f"Unknown sport type: {sport}")
                return None

        except Exception as e:
            log_fetcher_error(
                f"Error mapping game data for sport {sport}: {e}", "game_mapping"
            )
            return None

    async def _save_game_to_db(self, game_data: Dict) -> bool:
        """Save game data to the database."""
        try:
            # Log the full mapped game data for debugging (redact keys if needed)
            logger.info(f"_save_game_to_db: mapped game data: {game_data}")
            async with self.db_pool.acquire() as conn:
                # Check if game already exists
                row = await conn.fetchrow(
                    "SELECT api_game_id FROM api_games WHERE api_game_id = $1",
                    game_data["api_game_id"],
                )

                if row:
                    logger.info(f"Game already exists in DB: {game_data['api_game_id']}")
                    # Update existing game
                    result = await conn.execute(
                        """
                        UPDATE api_games SET
                            sport = $1, league_id = $2, league_name = $3,
                            home_team_name = $4, away_team_name = $5,
                            start_time = $6, status = $7, score = $8, venue = $9,
                            updated_at = NOW()
                        WHERE api_game_id = $10
                        """,
                        game_data["sport"],
                        game_data["league_id"],
                        game_data["league_name"],
                        game_data["home_team_name"],
                        game_data["away_team_name"],
                        game_data["start_time"],
                        game_data["status"],
                        str(game_data["score"]) if game_data["score"] else None,
                        game_data["venue"],
                        game_data["api_game_id"],
                    )
                    logger.info(f"UPDATE result: {result}")
                    log_database_operation("UPDATE game", True, 1)
                else:
                    logger.info(f"Inserting new game into DB: {game_data['api_game_id']}")
                    # Insert new game
                    result = await conn.execute(
                        """
                        INSERT INTO api_games (
                            api_game_id, sport, league_id, league_name,
                            home_team_name, away_team_name, start_time,
                            status, score, venue, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
                        """,
                        game_data["api_game_id"],
                        game_data["sport"],
                        game_data["league_id"],
                        game_data["league_name"],
                        game_data["home_team_name"],
                        game_data["away_team_name"],
                        game_data["start_time"],
                        game_data["status"],
                        str(game_data["score"]) if game_data["score"] else None,
                        game_data["venue"],
                    )
                    logger.info(f"INSERT result: {result}")
                    log_database_operation("INSERT game", True, 1)

                return True

        except Exception as e:
            logger.error(f"Exception in _save_game_to_db: {e}")
            logger.error(f"Game data that caused error: {game_data}")
            log_database_operation("Save game", False, 0, str(e))
            log_fetcher_error(f"Error saving game to database: {e}", "database_save")
            return False

    async def clear_api_games_table(self):
        """Clear the api_games table."""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("DELETE FROM api_games")
                log_cleanup_operation("Cleared api_games table")
        except Exception as e:
            log_fetcher_error(
                f"Error clearing api_games table: {e}", "database_cleanup"
            )

    async def clear_past_games(self):
        """Clear finished games and past games data, keeping active and upcoming games."""
        try:
            async with self.db_pool.acquire() as conn:
                # Get current time in UTC
                current_time = datetime.now(timezone.utc)
                # Convert to ISO string for query
                current_time_str = current_time.isoformat()

                # Remove finished games and games that have started
                result = await conn.execute(
                    """
                    DELETE FROM api_games
                    WHERE status IN (
                        'Match Finished', 'FT', 'AET', 'PEN', 'Match Cancelled', 'Match Postponed', 'Match Suspended', 'Match Interrupted',
                        'Fight Finished', 'Cancelled', 'Postponed', 'Suspended', 'Interrupted', 'Completed'
                    )
                    OR start_time < $1
                    """,
                    current_time_str,
                )

                # asyncpg's execute returns a string like 'DELETE X'
                deleted_count = 0
                if result and result.startswith('DELETE'):
                    try:
                        deleted_count = int(result.split(' ')[1])
                    except Exception:
                        deleted_count = 0
                log_cleanup_operation("Cleared finished/past games", deleted_count)
                logger.info(
                    f"Cleared {deleted_count} finished/past games from api_games table"
                )
        except Exception as e:
            log_fetcher_error(
                f"Error clearing finished/past games data: {e}", "database_cleanup"
            )
            # Don't raise - continue with fetch even if cleanup fails

    async def get_fetch_statistics(self) -> Dict:
        """Get statistics about the fetch operation."""
        try:
            async with self.db_pool.acquire() as conn:
                total_games = await conn.fetchval("SELECT COUNT(*) FROM api_games")

                unique_leagues = await conn.fetchval(
                    "SELECT COUNT(DISTINCT league_id) FROM api_games"
                )

                unique_sports = await conn.fetchval(
                    "SELECT COUNT(DISTINCT sport) FROM api_games"
                )

                return {
                    "total_games": total_games,
                    "unique_leagues": unique_leagues,
                    "unique_sports": unique_sports,
                    "failed_leagues": list(self.failed_leagues),
                    "successful_fetches": self.successful_fetches,
                    "total_fetches": self.total_fetches,
                }
        except Exception as e:
            log_fetcher_error(f"Error getting fetch statistics: {e}", "statistics")
            return {}


async def run_comprehensive_hourly_fetch(db_pool: asyncpg.Pool):
    """Run comprehensive fetch for ALL leagues every hour."""
    log_fetcher_operation("Starting comprehensive hourly fetch task for ALL leagues")

    while True:
        try:
            now = datetime.now(timezone.utc)
            # Calculate next hour
            next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(
                hours=1
            )
            wait_seconds = (next_hour - now).total_seconds()

            logger.info(
                f"Waiting {wait_seconds/60:.1f} minutes until next comprehensive hourly fetch..."
            )
            await asyncio.sleep(wait_seconds)

            log_fetcher_operation("Running comprehensive hourly fetch for ALL leagues")

            async with ComprehensiveFetcher(db_pool) as fetcher:
                # Clear past games before fetching new data
                await fetcher.clear_past_games()
                log_cleanup_operation("Cleared past games before fetching new data")

                # Discover all leagues first
                await fetcher.discover_all_leagues()

                # Fetch data for all leagues
                results = await fetcher.fetch_all_leagues_data()

                # Get statistics
                stats = await fetcher.get_fetch_statistics()
                log_fetcher_statistics(stats)

                # Log memory usage
                try:
                    memory = psutil.virtual_memory()
                    cpu_percent = psutil.cpu_percent(interval=1)
                    log_memory_usage(memory.used / (1024**2), cpu_percent)
                except Exception as e:
                    logger.warning(f"Could not log memory usage: {e}")

                logger.info(f"Comprehensive hourly fetch completed:")
                logger.info(f"  - Total games: {stats.get('total_games', 0)}")
                logger.info(f"  - Unique leagues: {stats.get('unique_leagues', 0)}")
                logger.info(f"  - Unique sports: {stats.get('unique_sports', 0)}")
                logger.info(
                    f"  - Failed leagues: {len(stats.get('failed_leagues', []))}"
                )

        except Exception as e:
            log_fetcher_error(f"Error in comprehensive hourly fetch: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying


async def main():
    """Main function to run the comprehensive fetcher."""
    # Log startup
    logger.info("=== DBSBM COMPREHENSIVE FETCHER: CODE VERSION TEST LOG LINE ===")
    log_fetcher_startup()

    # Set up database pool
    db_pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        min_size=int(os.getenv("POSTGRES_POOL_MIN_SIZE", 1)),
        max_size=int(os.getenv("POSTGRES_POOL_MAX_SIZE", 10)),
    )

    try:
        logger.info("Starting comprehensive fetcher...")

        # If 'ONESHOT' env var is set, do a single fetch and exit (for testing)
        if os.getenv("ONESHOT", "0") == "1":
            async with ComprehensiveFetcher(db_pool) as fetcher:
                await fetcher.discover_all_leagues()
                await fetcher.fetch_all_leagues_data()
                stats = await fetcher.get_fetch_statistics()
                logger.info(f"One-shot fetch complete. Stats: {stats}")
            return

        # Run the comprehensive hourly fetch (default)
        await run_comprehensive_hourly_fetch(db_pool)

    except Exception as e:
        log_fetcher_error(f"Fatal error in comprehensive fetcher: {e}")
        raise
    finally:
        # Properly close the asyncpg pool
        if db_pool:
            await db_pool.close()
        log_fetcher_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
