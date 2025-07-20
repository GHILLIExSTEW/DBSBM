"""
Main Fetcher for API-Sports Leagues
Fetches data for major leagues and saves to database.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import aiohttp
import aiomysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr),
    ]
)

logger = logging.getLogger(__name__)

# API endpoints for different sports
SPORT_ENDPOINTS = {
    "football": "https://v3.football.api-sports.io",
    "basketball": "https://v1.basketball.api-sports.io",
    "baseball": "https://v1.baseball.api-sports.io",
    "hockey": "https://v1.hockey.api-sports.io",
    "american-football": "https://v1.american-football.api-sports.io",
    "afl": "https://v1.afl.api-sports.io",
    "tennis": "https://v1.tennis.api-sports.io",
    "golf": "https://v1.golf.api-sports.io",
    "darts": "https://v1.darts.api-sports.io",
    "mma": "https://v1.mma.api-sports.io",
    "formula-1": "https://v1.formula-1.api-sports.io",
}

# Major leagues to fetch
MAJOR_LEAGUES = [
    # American Football
    {"sport": "american-football", "name": "NFL", "id": 1, "season": 2025},
    {"sport": "american-football", "name": "NCAA", "id": 2, "season": 2025},
    {"sport": "american-football", "name": "CFL", "id": 3, "season": 2025},
    # Basketball
    {"sport": "basketball", "name": "NBA", "id": 12, "season": 2025},
    {"sport": "basketball", "name": "WNBA", "id": 13, "season": 2025},
    {"sport": "basketball", "name": "EuroLeague", "id": 1, "season": 2025},
    # Baseball - Only MLB, removed KBO and NPB
    {"sport": "baseball", "name": "MLB", "id": 1, "season": 2025},
    # Hockey
    {"sport": "hockey", "name": "NHL", "id": 57, "season": 2025},
    {"sport": "hockey", "name": "KHL", "id": 1, "season": 2025},
    # Soccer/Football
    {"sport": "football", "name": "EPL", "id": 39, "season": 2025},
    {"sport": "football", "name": "LaLiga", "id": 140, "season": 2025},
    {"sport": "football", "name": "Bundesliga", "id": 78, "season": 2025},
    {"sport": "football", "name": "SerieA", "id": 135, "season": 2025},
    {"sport": "football", "name": "Ligue1", "id": 61, "season": 2025},
    {"sport": "football", "name": "MLS", "id": 253, "season": 2025},
    {"sport": "football", "name": "ChampionsLeague", "id": 2, "season": 2025},
    {"sport": "football", "name": "EuropaLeague", "id": 3, "season": 2025},
    {"sport": "football", "name": "Brazil_Serie_A", "id": 71, "season": 2025},
    # Tennis
    {"sport": "tennis", "name": "ATP", "id": 2, "season": 2025},
    {"sport": "tennis", "name": "WTA", "id": 3, "season": 2025},
    # Golf
    {"sport": "golf", "name": "PGA", "id": 1, "season": 2025},
    {"sport": "golf", "name": "LPGA", "id": 2, "season": 2025},
    # Darts
    {"sport": "darts", "name": "PDC", "id": 1, "season": 2025},
    # MMA
    {"sport": "mma", "name": "UFC", "id": 1, "season": 2025},
    # AFL
    {"sport": "afl", "name": "AFL", "id": 1, "season": 2025},
]


def safe_get(obj, *keys, default=None):
    """Safely get nested dictionary values."""
    try:
        for key in keys:
            if isinstance(obj, dict) and key in obj:
                obj = obj[key]
            else:
                return default
        return obj
    except (KeyError, TypeError, AttributeError):
        return default


def iso_to_mysql_datetime(iso_string: str) -> Optional[str]:
    """Convert ISO datetime string to MySQL datetime format."""
    if not iso_string:
        return None
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


class MainFetcher:
    def __init__(self, db_pool: aiomysql.Pool):
        self.db_pool = db_pool
        self.api_key = API_KEY
        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables")
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_all_leagues(self, date: str = None, next_days: int = 1) -> Dict[str, int]:
        """Fetch data for all major leagues."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Starting main fetch for {date} and next {next_days} days")

        # Clear old games data before fetching new data (keep recent games)
        await self._clear_old_games_data()
        logger.info("Cleared old games data before fetching new data")

        results = {
            "total_leagues": len(MAJOR_LEAGUES),
            "successful_fetches": 0,
            "failed_fetches": 0,
            "total_games": 0,
        }

        for league in MAJOR_LEAGUES:
            try:
                # Fetch for multiple days
                for day_offset in range(next_days):
                    fetch_date = (
                        datetime.strptime(date, "%Y-%m-%d")
                        + timedelta(days=day_offset)
                    ).strftime("%Y-%m-%d")

                    games_fetched = await self._fetch_league_games(league, fetch_date)

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
                logger.error(f"Failed to fetch data for {league['name']}: {e}")
                continue

        logger.info(f"Main fetch completed: {results}")
        return results

    async def _fetch_league_games(self, league: Dict, date: str) -> int:
        """Fetch games for a specific league on a specific date."""
        sport = league["sport"]
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
        elif sport in ["tennis", "golf", "darts"]:
            endpoint = "matches"
        else:
            endpoint = "games"

        url = f"{base_url}/{endpoint}"
        headers = {"x-apisports-key": self.api_key}
        
        # UFC API uses different parameters
        if sport == "mma":
            params = {
                "season": league["season"],
                "date": date,
            }
        else:
            params = {
                "league": league["id"],
                "season": league["season"],
                "date": date,
            }

        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 429:  # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded for {league['name']}, waiting...")
                    await asyncio.sleep(60)
                    return await self._fetch_league_games(league, date)

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
            logger.error(f"Network error fetching {league['name']}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error fetching {league['name']}: {e}")
            return 0

    def _map_game_data(self, game: Dict, sport: str, league: Dict) -> Optional[Dict]:
        """Map API game data to our database format."""
        try:
            # Handle UFC/MMA differently - they use fighters instead of teams
            if sport == "mma":
                # UFC uses fighters structure
                fighters = safe_get(game, "fighters", default={})
                first_fighter = safe_get(fighters, "first", default={})
                second_fighter = safe_get(fighters, "second", default={})
                
                # Get game ID
                game_id = str(safe_get(game, "id", default=""))
                if not game_id:
                    logger.error(f"Missing game ID for {sport}/{league['name']}")
                    return None

                # Get start time
                start_time = iso_to_mysql_datetime(safe_get(game, "date"))
                if not start_time:
                    logger.error(f"Missing start time for game {game_id}")
                    return None

                # Get status
                status = safe_get(game, "status", "long", default="Scheduled")

                # Get fighter IDs, ensuring they're valid integers
                first_fighter_id = safe_get(first_fighter, "id")
                second_fighter_id = safe_get(second_fighter, "id")
                
                # Convert to string, defaulting to "0" if None or invalid
                home_team_id = str(first_fighter_id) if first_fighter_id is not None else "0"
                away_team_id = str(second_fighter_id) if second_fighter_id is not None else "0"

                # Build UFC game data
                game_data = {
                    "id": game_id,
                    "api_game_id": safe_get(game, "api_game_id", default=game_id),
                    "sport": "MMA",
                    "league_id": str(league["id"]),
                    "league_name": league["name"],
                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id,
                    "home_team_name": safe_get(first_fighter, "name", default="Unknown"),
                    "away_team_name": safe_get(second_fighter, "name", default="Unknown"),
                    "start_time": start_time,
                    "end_time": None,
                    "status": status,
                    "score": json.dumps({"home": 0, "away": 0}),
                    "venue": safe_get(game, "venue", "name", default=None),
                    "referee": safe_get(game, "referee", default=None),
                    "raw_json": json.dumps(game),
                    "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                }
                return game_data

            # Common fields for all other sports
            teams = safe_get(game, "teams", default={})
            home_team = safe_get(teams, "home", default={})
            away_team = safe_get(teams, "away", default={})
            fixture = safe_get(game, "fixture", default={})

            # Get game ID from either game or fixture
            game_id = str(safe_get(game, "id", default=safe_get(fixture, "id", default="")))
            if not game_id:
                logger.error(f"Missing game ID for {sport}/{league['name']}")
                return None

            # Get start time from either game or fixture
            start_time = iso_to_mysql_datetime(
                safe_get(game, "date", default=safe_get(fixture, "date"))
            )
            if not start_time:
                logger.error(f"Missing start time for game {game_id}")
                return None

            # Get status from either game or fixture
            status = safe_get(
                game,
                "status",
                "long",
                default=safe_get(fixture, "status", "long", default="Scheduled"),
            )

            # Get team IDs, ensuring they're valid integers
            home_team_id_raw = safe_get(home_team, "id")
            away_team_id_raw = safe_get(away_team, "id")
            
            # Convert to string, defaulting to "0" if None or invalid
            home_team_id = str(home_team_id_raw) if home_team_id_raw is not None else "0"
            away_team_id = str(away_team_id_raw) if away_team_id_raw is not None else "0"

            # Get score based on sport
            score = {}
            if sport.lower() in ["baseball", "mlb"]:
                score = {
                    "home": safe_get(game, "scores", "home", "total", default=0),
                    "away": safe_get(game, "scores", "away", "total", default=0),
                }
            elif sport.lower() == "afl":
                score = {
                    "home": safe_get(game, "scores", "home", "score", default=0),
                    "away": safe_get(game, "scores", "away", "score", default=0),
                }
            else:
                score = {
                    "home": safe_get(
                        game,
                        "scores",
                        "home",
                        "total",
                        default=safe_get(game, "goals", "home", default=0),
                    ),
                    "away": safe_get(
                        game,
                        "scores",
                        "away",
                        "total",
                        default=safe_get(game, "goals", "away", default=0),
                    ),
                }

            # Normalize league names to prevent duplicates
            league_name = league["name"]
            if league_name.lower() in ["major league baseball", "mlb"]:
                league_name = "MLB"
            elif league_name.lower() in ["national basketball association", "nba"]:
                league_name = "NBA"
            elif league_name.lower() in ["national hockey league", "nhl"]:
                league_name = "NHL"
            elif league_name.lower() in ["national football league", "nfl"]:
                league_name = "NFL"
            elif league_name.lower() in ["ultimate fighting championship", "ufc"]:
                league_name = "UFC"
            
            # Build the game data dictionary
            game_data = {
                "id": game_id,
                "api_game_id": safe_get(game, "api_game_id", default=game_id),
                "sport": sport.title(),
                "league_id": str(league["id"]),
                "league_name": league_name,
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "home_team_name": safe_get(home_team, "name", default="Unknown"),
                "away_team_name": safe_get(away_team, "name", default="Unknown"),
                "start_time": start_time,
                "end_time": None,
                "status": status,
                "score": json.dumps(score),
                "venue": safe_get(game, "venue", "name", default=None),
                "referee": safe_get(game, "referee", default=None),
                "raw_json": json.dumps(game),
                "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            }

            return game_data
        except Exception as e:
            logger.error(f"Error mapping game data for {sport}/{league['name']}: {e}")
            return None

    async def _save_game_to_db(self, game_data: Dict) -> bool:
        """Save a single game to the api_games table."""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO api_games
                        (id, api_game_id, sport, league_id, league_name, home_team_id, away_team_id,
                         home_team_name, away_team_name, start_time, end_time, status, score,
                         venue, referee, raw_json, fetched_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            api_game_id=VALUES(api_game_id),
                            sport=VALUES(sport),
                            league_name=VALUES(league_name),
                            home_team_id=VALUES(home_team_id),
                            away_team_id=VALUES(away_team_id),
                            home_team_name=VALUES(home_team_name),
                            away_team_name=VALUES(away_team_name),
                            start_time=VALUES(start_time),
                            end_time=VALUES(end_time),
                            status=VALUES(status),
                            score=VALUES(score),
                            venue=VALUES(venue),
                            referee=VALUES(referee),
                            raw_json=VALUES(raw_json),
                            fetched_at=VALUES(fetched_at),
                            updated_at=CURRENT_TIMESTAMP
                        """,
                        (
                            game_data["id"],
                            game_data.get("api_game_id", game_data["id"]),
                            game_data["sport"],
                            game_data["league_id"],
                            game_data["league_name"],
                            game_data["home_team_id"],
                            game_data["away_team_id"],
                            game_data["home_team_name"],
                            game_data["away_team_name"],
                            game_data["start_time"],
                            game_data.get("end_time"),
                            game_data["status"],
                            game_data["score"],
                            game_data["venue"],
                            game_data["referee"],
                            game_data["raw_json"],
                            game_data["fetched_at"],
                        ),
                    )
            logger.info(f"Saved game {game_data['id']} to api_games")
            return True
        except Exception as e:
            logger.error(f"Error saving game {game_data['id']} to database: {e}")
            return False

    async def _clear_old_games_data(self):
        """Clear finished games and past games data, keeping active and upcoming games."""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Get current time in UTC
                    current_time = datetime.now(timezone.utc)
                    
                    # Remove finished games and games that have started
                    # Includes status values for all sports including MMA/UFC
                    await cur.execute("""
                        DELETE FROM api_games 
                        WHERE status IN (
                            'Match Finished', 'FT', 'AET', 'PEN', 'Match Cancelled', 'Match Postponed', 'Match Suspended', 'Match Interrupted',
                            'Fight Finished', 'Cancelled', 'Postponed', 'Suspended', 'Interrupted'
                        )
                        OR start_time < %s
                    """, (current_time,))
                    
                    deleted_count = cur.rowcount
                    logger.info(f"Cleared {deleted_count} finished/past games from api_games table")
        except Exception as e:
            logger.error(f"Error clearing finished/past games data: {e}")
            # Don't raise - continue with fetch even if cleanup fails


async def main():
    """Main function to run the fetcher on a schedule."""
    print("FETCHER: Starting fetcher process...")
    logger.info("Starting fetcher process...")
    
    # Database connection
    pool = None
    try:
        pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            db=os.getenv("MYSQL_DB"),
            autocommit=True,
            minsize=int(os.getenv("MYSQL_POOL_MIN_SIZE", "1")),
            maxsize=int(os.getenv("MYSQL_POOL_MAX_SIZE", "10")),
        )
        logger.info("Database connection pool created")
        
        # Run initial fetch on startup
        logger.info("Running initial fetch on startup...")
        async with MainFetcher(pool) as fetcher:
            results = await fetcher.fetch_all_leagues()
            logger.info(f"Initial fetch completed with results: {results}")
        
        # Schedule hourly fetches
        logger.info("Starting scheduled fetcher (runs every hour)...")
        while True:
            try:
                # Calculate time until next hour
                now = datetime.now(timezone.utc)
                next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                wait_seconds = (next_hour - now).total_seconds()
                
                logger.info(f"Waiting {wait_seconds/60:.1f} minutes until next fetch...")
                await asyncio.sleep(wait_seconds)
                
                # Run scheduled fetch
                logger.info("Running scheduled hourly fetch...")
                async with MainFetcher(pool) as fetcher:
                    results = await fetcher.fetch_all_leagues()
                    logger.info(f"Scheduled fetch completed with results: {results}")
                    
            except Exception as e:
                logger.error(f"Error in scheduled fetch: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
        
    except Exception as e:
        logger.error(f"Fetcher process failed: {e}")
        raise
    finally:
        if pool:
            pool.close()
            await pool.wait_closed()
            logger.info("Database connection pool closed")


if __name__ == "__main__":
    print("FETCHER: Script started, about to run main()")
    try:
        asyncio.run(main())
        print("FETCHER: Main function completed successfully")
    except Exception as e:
        print(f"FETCHER: Error in main function: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 