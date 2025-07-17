"""
Comprehensive Fetcher for ALL API-Sports Leagues
Automatically fetches data for every single league available from the API.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set

import aiohttp
import aiomysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

logger = logging.getLogger(__name__)

# Import the league discovery utility
from utils.league_discovery import LeagueDiscovery, SPORT_ENDPOINTS


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
        logger.info("Starting comprehensive league discovery...")

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

        logger.info(
            f"Starting comprehensive fetch for {date} and next {next_days} days"
        )

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

                        # Rate limiting between requests
                        await asyncio.sleep(1.5)

                    results["successful_fetches"] += 1

                except Exception as e:
                    results["failed_fetches"] += 1
                    self.failed_leagues.add(league["name"])
                    logger.error(f"Failed to fetch data for {league['name']}: {e}")
                    continue

        logger.info(f"Comprehensive fetch completed: {results}")
        return results

    async def _fetch_league_games(self, sport: str, league: Dict, date: str) -> int:
        """Fetch games for a specific league on a specific date."""
        base_url = SPORT_ENDPOINTS.get(sport)
        if not base_url:
            logger.error(f"No endpoint found for sport: {sport}")
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

        try:
            async with self.session.get(
                url, headers=headers, params=params
            ) as response:
                if response.status == 429:  # Rate limit exceeded
                    logger.warning(
                        f"Rate limit exceeded for {league['name']}, waiting..."
                    )
                    await asyncio.sleep(60)
                    return await self._fetch_league_games(sport, league, date)

                response.raise_for_status()
                data = await response.json()

                if "errors" in data and data["errors"]:
                    logger.warning(f"API errors for {league['name']}: {data['errors']}")
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
                        logger.error(f"Error processing game for {league['name']}: {e}")
                        continue

                return games_saved

        except aiohttp.ClientError as e:
            logger.error(f"API request failed for {league['name']}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error fetching {league['name']}: {e}")
            return 0

    def _map_game_data(self, game: Dict, sport: str, league: Dict) -> Optional[Dict]:
        """Map API game data to our standard format."""
        try:
            if sport == "football":
                # Force league_name for Brazil Serie A and Italian Serie A
                league_id = str(league["id"])
                if league_id == "71":
                    league_name_final = "Brazil Serie A"
                elif league_id == "135":
                    league_name_final = "Serie A"
                else:
                    league_name_final = league["name"]

                return {
                    "api_game_id": str(game["fixture"]["id"]),
                    "sport": "Football",
                    "league_id": league_id,
                    "league_name": league_name_final,
                    "home_team_name": game["teams"]["home"]["name"],
                    "away_team_name": game["teams"]["away"]["name"],
                    "start_time": game["fixture"]["date"],
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
            elif sport == "basketball":
                return {
                    "api_game_id": str(game["id"]),
                    "sport": "Basketball",
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_name": game["teams"]["home"]["name"],
                    "away_team_name": game["teams"]["away"]["name"],
                    "start_time": game["date"],
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
            elif sport == "baseball":
                return {
                    "api_game_id": str(game["id"]),
                    "sport": "Baseball",
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_name": game["teams"]["home"]["name"],
                    "away_team_name": game["teams"]["away"]["name"],
                    "start_time": game["date"],
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
            elif sport == "hockey":
                return {
                    "api_game_id": str(game["id"]),
                    "sport": "Ice Hockey",
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_name": game["teams"]["home"]["name"],
                    "away_team_name": game["teams"]["away"]["name"],
                    "start_time": game["date"],
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
            elif sport == "american-football":
                return {
                    "api_game_id": str(game["id"]),
                    "sport": "American Football",
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_name": game["teams"]["home"]["name"],
                    "away_team_name": game["teams"]["away"]["name"],
                    "start_time": game["date"],
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
                # Individual sports with matches
                return {
                    "api_game_id": str(game.get("id", "")),
                    "sport": sport.title(),
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_name": game.get("home", {}).get("name", ""),
                    "away_team_name": game.get("away", {}).get("name", ""),
                    "start_time": game.get("date", ""),
                    "status": game.get("status", {}).get("long", ""),
                    "score": (
                        {
                            "home": game.get("scores", {}).get("home", {}).get("total"),
                            "away": game.get("scores", {}).get("away", {}).get("total"),
                        }
                        if "scores" in game
                        else None
                    ),
                    "venue": game.get("venue", {}).get("name", ""),
                }
            else:
                # Generic mapping for other sports
                return {
                    "api_game_id": str(
                        game.get("id", game.get("fixture", {}).get("id", ""))
                    ),
                    "sport": sport.title(),
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_name": game.get("teams", {})
                    .get("home", {})
                    .get("name", ""),
                    "away_team_name": game.get("teams", {})
                    .get("away", {})
                    .get("name", ""),
                    "start_time": game.get(
                        "date", game.get("fixture", {}).get("date", "")
                    ),
                    "status": game.get("status", {}).get("long", ""),
                    "score": None,  # Generic sports might not have standardized scoring
                    "venue": game.get("venue", {}).get("name", ""),
                }

        except Exception as e:
            logger.error(f"Error mapping game data: {e}")
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
                                str(game_data["score"]) if game_data["score"] else None,
                                game_data["venue"],
                                game_data["api_game_id"],
                            ),
                        )
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
                                str(game_data["score"]) if game_data["score"] else None,
                                game_data["venue"],
                            ),
                        )

                    await conn.commit()
                    return True

        except Exception as e:
            logger.error(f"Error saving game to database: {e}")
            return False

    async def clear_api_games_table(self):
        """Clear the api_games table."""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("DELETE FROM api_games")
                    await conn.commit()
                    logger.info("Cleared api_games table")
        except Exception as e:
            logger.error(f"Error clearing api_games table: {e}")

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
            logger.error(f"Error getting fetch statistics: {e}")
            return {}


async def run_comprehensive_hourly_fetch(db_pool: aiomysql.Pool):
    """Run comprehensive fetch for ALL leagues every hour."""
    logger.info("Starting comprehensive hourly fetch task for ALL leagues")

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

            logger.info("Running comprehensive hourly fetch for ALL leagues...")

            async with ComprehensiveFetcher(db_pool) as fetcher:
                # Discover all leagues first
                await fetcher.discover_all_leagues()

                # Fetch data for all leagues
                results = await fetcher.fetch_all_leagues_data()

                # Get statistics
                stats = await fetcher.get_fetch_statistics()

                logger.info(f"Comprehensive hourly fetch completed:")
                logger.info(f"  - Total games: {stats.get('total_games', 0)}")
                logger.info(f"  - Unique leagues: {stats.get('unique_leagues', 0)}")
                logger.info(f"  - Unique sports: {stats.get('unique_sports', 0)}")
                logger.info(
                    f"  - Failed leagues: {len(stats.get('failed_leagues', []))}"
                )

        except Exception as e:
            logger.error(f"Error in comprehensive hourly fetch: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying


async def main():
    """Main function to run the comprehensive fetcher."""
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
        logger.error(f"Fatal error in comprehensive fetcher: {e}")
        raise
    finally:
        db_pool.close()
        await db_pool.wait_closed()
        logger.info("Database pool closed")


if __name__ == "__main__":
    asyncio.run(main())
