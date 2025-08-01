"""
Comprehensive Fetcher for ALL API-Sports Leagues
Automatically fetches data for every single league available from the API.
"""

from bot.utils.league_discovery import SPORT_ENDPOINTS, LeagueDiscovery
from bot.utils.fetcher_logger import (
    get_fetcher_logger, log_fetcher_operation, log_fetcher_error, 
    log_fetcher_statistics, log_fetcher_startup, log_fetcher_shutdown,
    log_league_fetch, log_api_request, log_database_operation,
    log_memory_usage, log_cleanup_operation
)
import asyncio
import logging
import os
import psutil
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from zoneinfo import ZoneInfo

import aiohttp
import aiomysql
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
    def __init__(self, db_pool: aiomysql.Pool):
        self.db_pool = db_pool
        self.api_key = API_KEY
        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables")

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
        """Discover all available leagues using the LeagueDiscovery utility."""
        log_fetcher_operation("Starting comprehensive league discovery")

        async with LeagueDiscovery() as discoverer:
            self.discovered_leagues = await discoverer.discover_all_leagues()

            total_leagues = sum(
                len(leagues) for leagues in self.discovered_leagues.values()
            )
            logger.info(
                f"Discovered {total_leagues} leagues across {len(self.discovered_leagues)} sports"
            )

            return self.discovered_leagues

    async def fetch_all_leagues_data(
        self, date: str = None, next_days: int = 2
    ) -> Dict[str, int]:
        """Fetch data for ALL discovered leagues."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        log_fetcher_operation("Starting comprehensive fetch", {
            "date": date,
            "next_days": next_days
        })

        # Clear existing data
        await self.clear_api_games_table()

        results = {
            "total_leagues": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "total_games": 0,
        }

        # Fetch for each sport and league
        for sport, leagues in self.discovered_leagues.items():
            logger.info(f"Processing {len(leagues)} leagues for {sport}")

            for league in leagues:
                results["total_leagues"] += 1

                try:
                    # Fetch for multiple days
                    for day_offset in range(next_days):
                        fetch_date = (
                            datetime.strptime(date, "%Y-%m-%d")
                            + timedelta(days=day_offset)
                        ).strftime("%Y-%m-%d")

                        games_fetched = await self._fetch_league_games(
                            sport, league, fetch_date
                        )

                        if games_fetched > 0:
                            results["total_games"] += games_fetched
                            logger.info(
                                f"Fetched {games_fetched} games for {league['name']} on {fetch_date}"
                            )

                        # Rate limiting between requests - reduced for hourly operation
                        await asyncio.sleep(0.5)  # Reduced from 1.5s to 0.5s

                    results["successful_fetches"] += 1

                except Exception as e:
                    results["failed_fetches"] += 1
                    self.failed_leagues.add(league["name"])
                    log_fetcher_error(f"Failed to fetch data for {league['name']}: {e}", "league_fetch")
                    continue

        logger.info(f"Comprehensive fetch completed: {results}")
        return results

    async def _fetch_league_games(self, sport: str, league: Dict, date: str) -> int:
        """Fetch games for a specific league on a specific date."""
        import time
        
        base_url = SPORT_ENDPOINTS.get(sport)
        if not base_url:
            log_fetcher_error(f"No endpoint found for sport: {sport}")
            return 0

        # Determine the correct endpoint based on sport
        if sport == "football":
            endpoint = "fixtures"
        elif sport == "formula-1":
            endpoint = "races"
        elif sport == "mma":
            endpoint = "fights"
        elif sport in [
            "tennis",
            "golf",
            "darts",
            "cricket",
            "boxing",
            "cycling",
            "esports",
            "snooker",
            "squash",
        ]:
            endpoint = "matches"
        elif sport in [
            "futsal",
            "table-tennis",
            "badminton",
            "beach-volleyball",
            "field-hockey",
            "ice-hockey",
            "water-polo",
            "winter-sports",
        ]:
            endpoint = "games"
        elif sport == "motorsport":
            endpoint = "races"
        else:
            endpoint = "games"

        url = f"{base_url}/{endpoint}"
        headers = {"x-apisports-key": self.api_key}
        params = {
            "league": league["id"],
            "season": league.get("season", datetime.now().year),
            "date": date,
        }

        start_time = time.time()
        try:
            async with self.session.get(
                url, headers=headers, params=params
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 429:  # Rate limit exceeded
                    logger.warning(
                        f"Rate limit exceeded for {league['name']}, waiting..."
                    )
                    log_api_request(url, False, response_time, "Rate limit exceeded")
                    await asyncio.sleep(60)
                    return await self._fetch_league_games(sport, league, date)

                response.raise_for_status()
                data = await response.json()

                if "errors" in data and data["errors"]:
                    logger.warning(
                        f"API errors for {league['name']}: {data['errors']}")
                    log_api_request(url, False, response_time, f"API errors: {data['errors']}")
                    return 0

                games = data.get("response", [])
                games_saved = 0

                for game in games:
                    try:
                        mapped_game = self._map_game_data(game, sport, league)
                        if mapped_game:
                            await self._save_game_to_db(mapped_game)
                            games_saved += 1
                    except Exception as e:
                        log_fetcher_error(f"Error processing game for {league['name']}: {e}", "game_processing")
                        continue

                # Log successful fetch
                log_league_fetch(sport, league['name'], True, games_saved)
                log_api_request(url, True, response_time)
                
                return games_saved

        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            log_league_fetch(sport, league['name'], False, 0, str(e))
            log_api_request(url, False, response_time, str(e))
            log_fetcher_error(f"API request failed for {league['name']}: {e}", "api_request")
            return 0
        except Exception as e:
            response_time = time.time() - start_time
            log_league_fetch(sport, league['name'], False, 0, str(e))
            log_api_request(url, False, response_time, str(e))
            log_fetcher_error(f"Unexpected error fetching {league['name']}: {e}", "league_fetch")
            return 0

    def _convert_utc_to_est(self, utc_time_str: str) -> str:
        """Convert UTC time string to EST time string."""
        try:
            if not utc_time_str:
                return None

            # Parse the UTC time string
            if "T" in utc_time_str and "Z" in utc_time_str:
                # ISO format with Z suffix
                dt = datetime.fromisoformat(
                    utc_time_str.replace("Z", "+00:00"))
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
            logger.warning(
                f"Failed to convert time '{utc_time_str}' to EST: {e}")
            return utc_time_str

    def _map_football_game_data(self, game: Dict, league: Dict) -> Optional[Dict]:
        """Map football game data to our standard format."""
        # Force league_name for Brazil Serie A and Italian Serie A
        league_id = str(league["id"])
        if league_id == "71":
            league_name_final = "Brazil Serie A"
        elif league_id == "135":
            league_name_final = "Serie A"
        else:
            league_name_final = league["name"]

        # Convert UTC time to EST
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
                game["fixture"]["venue"]["name"]
                if "venue" in game["fixture"]
                else None
            ),
        }

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
            }

            mapper = sport_mappers.get(sport)
            if mapper:
                return mapper(game, league)
            else:
                logger.warning(f"Unknown sport type: {sport}")
                return None

        except Exception as e:
            log_fetcher_error(f"Error mapping game data for sport {sport}: {e}", "game_mapping")
            return None

    async def _save_game_to_db(self, game_data: Dict) -> bool:
        """Save game data to the database."""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Check if game already exists
                    await cur.execute(
                        "SELECT api_game_id FROM api_games WHERE api_game_id = %s",
                        (game_data["api_game_id"],),
                    )

                    if await cur.fetchone():
                        # Update existing game
                        await cur.execute(
                            """
                            UPDATE api_games SET
                                sport = %s, league_id = %s, league_name = %s,
                                home_team_name = %s, away_team_name = %s,
                                start_time = %s, status = %s, score = %s, venue = %s,
                                updated_at = NOW()
                            WHERE api_game_id = %s
                        """,
                            (
                                game_data["sport"],
                                game_data["league_id"],
                                game_data["league_name"],
                                game_data["home_team_name"],
                                game_data["away_team_name"],
                                game_data["start_time"],
                                game_data["status"],
                                str(game_data["score"]
                                    ) if game_data["score"] else None,
                                game_data["venue"],
                                game_data["api_game_id"],
                            ),
                        )
                        log_database_operation("UPDATE game", True, 1)
                    else:
                        # Insert new game
                        await cur.execute(
                            """
                            INSERT INTO api_games (
                                api_game_id, sport, league_id, league_name,
                                home_team_name, away_team_name, start_time,
                                status, score, venue, created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """,
                            (
                                game_data["api_game_id"],
                                game_data["sport"],
                                game_data["league_id"],
                                game_data["league_name"],
                                game_data["home_team_name"],
                                game_data["away_team_name"],
                                game_data["start_time"],
                                game_data["status"],
                                str(game_data["score"]
                                    ) if game_data["score"] else None,
                                game_data["venue"],
                            ),
                        )
                        log_database_operation("INSERT game", True, 1)

                    await conn.commit()
                    return True

        except Exception as e:
            log_database_operation("Save game", False, 0, str(e))
            log_fetcher_error(f"Error saving game to database: {e}", "database_save")
            return False

    async def clear_api_games_table(self):
        """Clear the api_games table."""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("DELETE FROM api_games")
                    await conn.commit()
                    log_cleanup_operation("Cleared api_games table")
        except Exception as e:
            log_fetcher_error(f"Error clearing api_games table: {e}", "database_cleanup")

    async def clear_past_games(self):
        """Clear finished games and past games data, keeping active and upcoming games."""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Get current time in UTC
                    current_time = datetime.now(timezone.utc)

                    # Remove finished games and games that have started
                    await cur.execute(
                        """
                        DELETE FROM api_games
                        WHERE status IN (
                            'Match Finished', 'FT', 'AET', 'PEN', 'Match Cancelled', 'Match Postponed', 'Match Suspended', 'Match Interrupted',
                            'Fight Finished', 'Cancelled', 'Postponed', 'Suspended', 'Interrupted', 'Completed'
                        )
                        OR start_time < %s
                    """,
                        (current_time,),
                    )

                    deleted_count = cur.rowcount
                    await conn.commit()
                    log_cleanup_operation("Cleared finished/past games", deleted_count)
                    logger.info(
                        f"Cleared {deleted_count} finished/past games from api_games table"
                    )
        except Exception as e:
            log_fetcher_error(f"Error clearing finished/past games data: {e}", "database_cleanup")
            # Don't raise - continue with fetch even if cleanup fails

    async def get_fetch_statistics(self) -> Dict:
        """Get statistics about the fetch operation."""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute("SELECT COUNT(*) as total_games FROM api_games")
                    total_games = (await cur.fetchone())["total_games"]

                    await cur.execute(
                        "SELECT COUNT(DISTINCT league_id) as unique_leagues FROM api_games"
                    )
                    unique_leagues = (await cur.fetchone())["unique_leagues"]

                    await cur.execute(
                        "SELECT COUNT(DISTINCT sport) as unique_sports FROM api_games"
                    )
                    unique_sports = (await cur.fetchone())["unique_sports"]

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


async def run_comprehensive_hourly_fetch(db_pool: aiomysql.Pool):
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
                logger.info(
                    f"  - Unique leagues: {stats.get('unique_leagues', 0)}")
                logger.info(
                    f"  - Unique sports: {stats.get('unique_sports', 0)}")
                logger.info(
                    f"  - Failed leagues: {len(stats.get('failed_leagues', []))}"
                )

        except Exception as e:
            log_fetcher_error(f"Error in comprehensive hourly fetch: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying


async def main():
    """Main function to run the comprehensive fetcher."""
    # Log startup
    log_fetcher_startup()
    
    # Set up database pool
    db_pool = await aiomysql.create_pool(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        db=os.getenv("MYSQL_DB"),
        minsize=int(os.getenv("MYSQL_POOL_MIN_SIZE", 1)),
        maxsize=int(os.getenv("MYSQL_POOL_MAX_SIZE", 10)),
        autocommit=True,
    )

    try:
        logger.info("Starting comprehensive fetcher...")

        # Run the comprehensive hourly fetch
        await run_comprehensive_hourly_fetch(db_pool)

    except Exception as e:
        log_fetcher_error(f"Fatal error in comprehensive fetcher: {e}")
        raise
    finally:
        db_pool.close()
        await db_pool.wait_closed()
        log_fetcher_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
