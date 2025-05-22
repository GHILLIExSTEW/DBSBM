import os
import aiohttp
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import aiomysql
from dotenv import load_dotenv
import sys
from zoneinfo import ZoneInfo
import subprocess

# Configure logging to file and console
try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(os.path.dirname(__file__), "fetcher.log")),
            logging.StreamHandler(),
        ],
    )
except Exception as e:
    print(f"Failed to configure logging: {e}", file=sys.stderr)
    raise
logger = logging.getLogger(__name__)

# Log startup
logger.info("Starting fetcher.py initialization")

# Verify .env file exists
env_path = os.path.join(os.path.dirname(__file__), ".env")
if not os.path.exists(env_path):
    logger.error(f".env file not found at {env_path}")
    raise FileNotFoundError(f".env file not found at {env_path}")

# Load environment variables
try:
    load_dotenv()
    logger.info("Attempting to load environment variables")
    API_KEY = os.getenv("API_KEY")
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DB = os.getenv("MYSQL_DB")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_POOL_MIN_SIZE = int(os.getenv("MYSQL_POOL_MIN_SIZE", 1))
    MYSQL_POOL_MAX_SIZE = int(os.getenv("MYSQL_POOL_MAX_SIZE", 10))
except Exception as e:
    logger.error(f"Error loading environment variables: {e}")
    raise

# Verify environment variables
if not API_KEY:
    logger.error("API_KEY not found in .env file")
    raise ValueError("API_KEY not found in .env file")
if not all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB]):
    logger.error(
        "Database credentials missing in .env file: MYSQL_HOST=%s, MYSQL_USER=%s, MYSQL_DB=%s",
        MYSQL_HOST,
        MYSQL_USER,
        MYSQL_DB,
    )
    raise ValueError("Database credentials missing in .env file")
logger.info(
    "Environment variables loaded successfully: API_KEY=%s, MYSQL_HOST=%s, MYSQL_USER=%s, MYSQL_DB=%s, MYSQL_PORT=%s",
    "***" if API_KEY else None,
    MYSQL_HOST,
    MYSQL_USER,
    MYSQL_DB,
    MYSQL_PORT,
)

# Import LEAGUE_IDS and ENDPOINTS
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
    logger.info("Attempting to import utils.api_sports")
    from utils.api_sports import LEAGUE_IDS, ENDPOINTS
    logger.info("Successfully imported LEAGUE_IDS and ENDPOINTS")
except ImportError as e:
    logger.error(f"Failed to import LEAGUE_IDS or ENDPOINTS: {e}")
    raise

# League configuration
LEAGUE_CONFIG = {
    "football": {
        "EPL": {"id": 39, "name": "English Premier League"},
        "LaLiga": {"id": 140, "name": "La Liga"},
        "Bundesliga": {"id": 78, "name": "Bundesliga"},
        "SerieA": {"id": 135, "name": "Serie A"},
        "Ligue1": {"id": 61, "name": "Ligue 1"},
        "MLS": {"id": 253, "name": "Major League Soccer"},
        "ChampionsLeague": {"id": 2, "name": "UEFA Champions League"},
        "EuropaLeague": {"id": 3, "name": "UEFA Europa League"},
        "WorldCup": {"id": 1, "name": "FIFA World Cup"},
    },
    "basketball": {
        "NBA": {"id": 12, "name": "National Basketball Association"},
        "WNBA": {"id": 13, "name": "Women's National Basketball Association"},
        "EuroLeague": {"id": 1, "name": "EuroLeague"},
    },
    "baseball": {
        "MLB": {"id": 1, "name": "Major League Baseball"},
        "NPB": {"id": 2, "name": "Nippon Professional Baseball"},
        "KBO": {"id": 3, "name": "Korea Baseball Organization"},
    },
    "hockey": {
        "NHL": {"id": 57, "name": "National Hockey League"},
        "KHL": {"id": 1, "name": "Kontinental Hockey League"},
    },
    "american-football": {
        "NFL": {"id": 1, "name": "National Football League"},
        "NCAA": {"id": 2, "name": "NCAA Football"},
    },
    "rugby": {
        "SuperRugby": {"id": 1, "name": "Super Rugby"},
        "SixNations": {"id": 2, "name": "Six Nations Championship"},
    },
    "volleyball": {
        "FIVB": {"id": 1, "name": "FIVB World League"},
    },
    "handball": {
        "EHF": {"id": 1, "name": "EHF Champions League"},
    },
    "tennis": {
        "ATP": {"id": 1, "name": "ATP Tour"},
        "WTA": {"id": 2, "name": "WTA Tour"},
        "GrandSlam": {"id": 3, "name": "Grand Slam"},
    },
    "formula-1": {
        "F1": {"id": 1, "name": "Formula 1"},
    },
    "mma": {
        "UFC": {"id": 1, "name": "Ultimate Fighting Championship"},
        "Bellator": {"id": 2, "name": "Bellator MMA"},
    },
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "cache")
try:
    os.makedirs(CACHE_DIR, exist_ok=True)
    logger.info(f"Created cache directory at {CACHE_DIR}")
except Exception as e:
    logger.error(f"Failed to create cache directory {CACHE_DIR}: {e}")
    raise

EDT = ZoneInfo("America/New_York")


def safe_get(obj, *keys, default=None):
    """Safely access nested dictionary keys, returning default if any key is missing or invalid."""
    current = obj
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def iso_to_mysql_datetime(iso_str):
    """Convert ISO 8601 string to MySQL DATETIME string (UTC)."""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_utc = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt_utc.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        logger.error(f"Error parsing ISO datetime {iso_str}: {e}")
        return None


def map_game_data(game: Dict, sport: str, league: str, league_id: str) -> Optional[Dict]:
    """Normalize game data based on sport and league."""
    try:
        logger.debug(f"Mapping game data for {sport}/{league}, game_id={safe_get(game, 'id', default='unknown')}")
        if sport.lower() in ["football", "soccer"]:
            fixture = safe_get(game, "fixture", default={})
            teams = safe_get(game, "teams", default={})
            home_team = safe_get(teams, "home", default={})
            away_team = safe_get(teams, "away", default={})
            league_info = safe_get(game, "league", default={})
            score = safe_get(game, "score", default={})
            game_data = {
                "id": str(safe_get(fixture, "id", default="")),
                "sport": "Football",
                "league_id": league_id,
                "league_name": safe_get(league_info, "name", default=league),
                "home_team_id": str(safe_get(home_team, "id")),
                "away_team_id": str(safe_get(away_team, "id")),
                "home_team_name": safe_get(home_team, "name", default="Unknown"),
                "away_team_name": safe_get(away_team, "name", default="Unknown"),
                "start_time": iso_to_mysql_datetime(safe_get(fixture, "date")),
                "status": safe_get(fixture, "status", "long", default="Scheduled"),
                "score": json.dumps(score),
                "venue": safe_get(fixture, "venue", "name", default=None),
                "referee": safe_get(fixture, "referee"),
                "raw_json": json.dumps(game),
                "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            }
        elif sport.lower() in ["baseball", "mlb"]:
            teams = safe_get(game, "teams", default={})
            home_team = safe_get(teams, "home", default={})
            away_team = safe_get(teams, "away", default={})
            game_data = {
                "id": str(safe_get(game, "id", default="")),
                "sport": "Baseball",
                "league_id": league_id,
                "league_name": LEAGUE_CONFIG["baseball"].get(league, {}).get("name", league),
                "home_team_id": str(safe_get(home_team, "id")),
                "away_team_id": str(safe_get(away_team, "id")),
                "home_team_name": safe_get(home_team, "name", default="Unknown"),
                "away_team_name": safe_get(away_team, "name", default="Unknown"),
                "start_time": iso_to_mysql_datetime(safe_get(game, "date")),
                "status": safe_get(game, "status", "long", default="Scheduled"),
                "score": json.dumps(
                    {
                        "home": safe_get(game, "scores", "home", "total", default=0),
                        "away": safe_get(game, "scores", "away", "total", default=0),
                    }
                ),
                "venue": safe_get(game, "venue", "name", default=None),
                "referee": None,
                "raw_json": json.dumps(game),
                "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            }
        else:
            teams = safe_get(game, "teams", default={})
            home_team = safe_get(teams, "home", default={})
            away_team = safe_get(teams, "away", default={})
            fixture = safe_get(game, "fixture", default={})
            game_data = {
                "id": str(
                    safe_get(game, "id", default=safe_get(fixture, "id", default=""))
                ),
                "sport": sport.title(),
                "league_id": league_id,
                "league_name": LEAGUE_CONFIG.get(sport.lower(), {}).get(league, {}).get("name", league),
                "home_team_id": str(safe_get(home_team, "id")),
                "away_team_id": str(safe_get(away_team, "id")),
                "home_team_name": safe_get(home_team, "name", default="Unknown"),
                "away_team_name": safe_get(away_team, "name", default="Unknown"),
                "start_time": iso_to_mysql_datetime(
                    safe_get(game, "date", default=safe_get(fixture, "date"))
                ),
                "status": safe_get(
                    game,
                    "status",
                    "long",
                    default=safe_get(fixture, "status", "long", default="Scheduled"),
                ),
                "score": json.dumps(
                    {
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
                ) if any(safe_get(game, key) for key in ["scores", "goals"]) else "{}",
                "venue": safe_get(game, "venue", "name", default=None),
                "referee": safe_get(fixture, "referee"),
                "raw_json": json.dumps(game),
                "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            }
        if not game_data["id"] or not game_data["start_time"]:
            logger.error(f"Skipping game with missing id or start_time: {json.dumps(game)}")
            return None
        logger.debug(f"Successfully mapped game: {game_data['id']}")
        return game_data
    except Exception as e:
        logger.error(f"Error mapping game data for {sport}/{league}: {e}. Game: {json.dumps(game)}")
        return None


async def create_db_pool() -> aiomysql.Pool:
    """Create a MySQL connection pool."""
    logger.info("Attempting to create MySQL connection pool")
    try:
        pool = await aiomysql.create_pool(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DB,
            autocommit=True,
            minsize=MYSQL_POOL_MIN_SIZE,
            maxsize=MYSQL_POOL_MAX_SIZE,
        )
        logger.info("Database connection pool created successfully")
        return pool
    except Exception as e:
        logger.error(f"Error creating database pool: {e}")
        raise


async def clear_api_games_table(pool: aiomysql.Pool):
    """Clear api_games and related game_events tables."""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM game_events")
                await cur.execute("DELETE FROM api_games")
        logger.info("Cleared api_games table and related game_events")
    except Exception as e:
        logger.error(f"Error clearing api_games table: {e}")


async def save_game_to_db(pool: aiomysql.Pool, game_data: Dict) -> bool:
    """Save a single game to the api_games table."""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO api_games 
                    (id, sport, league_id, league_name, home_team_id, away_team_id, 
                     home_team_name, away_team_name, start_time, status, score, 
                     venue, referee, raw_json, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        sport=VALUES(sport),
                        league_name=VALUES(league_name),
                        home_team_id=VALUES(home_team_id),
                        away_team_id=VALUES(away_team_id),
                        home_team_name=VALUES(home_team_name),
                        away_team_name=VALUES(away_team_name),
                        start_time=VALUES(start_time),
                        status=VALUES(status),
                        score=VALUES(score),
                        venue=VALUES(venue),
                        referee=VALUES(referee),
                        raw_json=VALUES(raw_json),
                        fetched_at=VALUES(fetched_at)
                    """,
                    (
                        game_data["id"],
                        game_data["sport"],
                        game_data["league_id"],
                        game_data["league_name"],
                        game_data["home_team_id"],
                        game_data["away_team_id"],
                        game_data["home_team_name"],
                        game_data["away_team_name"],
                        game_data["start_time"],
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


async def get_live_games(pool: aiomysql.Pool) -> List[Dict]:
    """Fetch games past start_time and not finished from api_games table."""
    finished_statuses = ["Match Finished", "Finished", "FT", "Ended"]
    query = """
        SELECT id, league_id, sport, status
        FROM api_games
        WHERE start_time <= %s
        AND (end_time IS NULL OR end_time >= %s)
        AND status NOT IN (%s, %s, %s, %s)
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    query, [datetime.utcnow(), datetime.utcnow()] + finished_statuses
                )
                live_games = await cur.fetchall()
        logger.info(f"Retrieved {len(live_games)} live games from api_games")
        return live_games or []
    except Exception as e:
        logger.error(f"Error fetching live games: {e}")
        return []


async def get_active_bets(pool: aiomysql.Pool, live_game_ids: List[str]) -> List[Dict]:
    """Get active bets for live games."""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                query = """
                    SELECT b.*, g.start_time
                    FROM bets b
                    JOIN api_games g ON b.game_id = g.id
                    WHERE b.status = 'pending'
                    AND g.id IN %s
                    AND g.start_time <= NOW()
                    AND g.status NOT IN ('Match Finished', 'Finished', 'FT', 'Ended')
                """
                await cur.execute(query, (tuple(live_game_ids),))
                active_bets = await cur.fetchall()
        logger.info(f"Retrieved {len(active_bets)} active bets for live games")
        return active_bets or []
    except Exception as e:
        logger.error(f"Error fetching active bets: {e}")
        return []


async def fetch_games(
    pool: aiomysql.Pool,
    session: aiohttp.ClientSession,
    sport: str,
    league_name: str,
    league_id: str,
    date: str,
    season: int,
):
    """Fetch game data for a specific league and date, saving to database and cache."""
    logger.info(
        f"Fetching games for {league_name} (league_id={league_id}, sport={sport}, date={date}, season={season})"
    )
    headers = {"x-apisports-key": API_KEY}
    base_endpoint = ENDPOINTS.get(sport)
    if not base_endpoint or not league_id:
        logger.warning(f"Skipping {league_name}: missing endpoint or league_id")
        return
    endpoint = (
        f"{base_endpoint}/fixtures"
        if sport == "football"
        else f"{base_endpoint}/games"
    )
    params = {"league": league_id, "date": date, "season": season}
    logger.debug(f"Requesting {endpoint} with params: {params}")
    try:
        async with session.get(endpoint, headers=headers, params=params) as resp:
            logger.info(f"API response status for {league_name}: {resp.status}")
            if resp.status != 200:
                error_text = await resp.text()
                logger.error(f"API request failed for {league_name}: {resp.status}: {error_text}")
                return
            data = await resp.json()
            # Save raw data
            raw_file = os.path.join(CACHE_DIR, f"league_{league_name}.json")
            with open(raw_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Fetched and cached raw data for {league_name} ({sport})")
            # Normalize and save to database
            games = data.get("response", [])
            normalized = [
                map_game_data(game, sport, league_name, league_id) for game in games
            ]
            normalized = [g for g in normalized if g]
            for game_data in normalized:
                await save_game_to_db(pool, game_data)
            # Save normalized data
            normalized_file = os.path.join(CACHE_DIR, f"league_{league_name}_normalized.json")
            with open(normalized_file, "w") as f:
                json.dump(normalized, f, indent=2)
            logger.info(f"Saved {len(normalized)} normalized games for {league_name} ({sport})")
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching {league_name}: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error for {league_name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching {league_name}: {e}", exc_info=True)


async def initial_fetch(pool: aiomysql.Pool):
    """Perform initial fetch of all scheduled games for the current day in EDT."""
    today_edt = datetime.now(EDT).strftime("%Y-%m-%d")
    season = datetime.now().year
    logger.info(f"Starting initial fetch for {today_edt} (season: {season})")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for league_name, league_info in LEAGUE_IDS.items():
            sport = league_info.get("sport")
            league_id = str(league_info.get("id"))
            season = get_current_season(league_name)
            tasks.append(
                fetch_games(pool, session, sport, league_name, league_id, today_edt, season)
            )
        await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Initial fetch completed")


async def daily_3am_fetch(pool: aiomysql.Pool):
    """Delete api_games table and fetch games daily at 3 AM EDT."""
    while True:
        now_edt = datetime.now(EDT)
        next_sync = now_edt.replace(hour=3, minute=0, second=0, microsecond=0)
        if now_edt >= next_sync:
            next_sync += timedelta(days=1)
        sleep_seconds = (next_sync - now_edt).total_seconds()
        logger.info(
            f"Next 3 AM EDT sync scheduled at {next_sync.isoformat()} "
            f"(in {sleep_seconds/3600:.2f} hours)"
        )
        await asyncio.sleep(sleep_seconds)
        today_edt = datetime.now(EDT).strftime("%Y-%m-%d")
        season = datetime.now().year
        logger.info(f"Starting 3 AM EDT fetch for {today_edt} (season: {season})")
        await clear_api_games_table(pool)
        async with aiohttp.ClientSession() as session:
            tasks = []
            for league_name, league_info in LEAGUE_IDS.items():
                sport = league_info.get("sport")
                league_id = str(league_info.get("id"))
                season = get_current_season(league_name)
                tasks.append(
                    fetch_games(pool, session, sport, league_name, league_id, today_edt, season)
                )
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("3 AM EDT fetch completed")


async def live_games_fetch(pool: aiomysql.Pool):
    """Fetch data for live games with active bets every 5 minutes."""
    while True:
        live_games = await get_live_games(pool)
        if not live_games:
            logger.info("No live games found, skipping 5-minute fetch")
            await asyncio.sleep(300)
            continue
        live_game_ids = [game["id"] for game in live_games]
        live_league_ids = {str(game["league_id"]) for game in live_games}
        logger.info(f"Found {len(live_games)} live games in leagues: {live_league_ids}")
        active_bets = await get_active_bets(pool, live_game_ids)
        if not active_bets:
            logger.info("No active bets found for live games, skipping 5-minute fetch")
            await asyncio.sleep(300)
            continue
        bet_league_ids = {str(bet["league"]) for bet in active_bets}
        logger.info(f"Found {len(active_bets)} active bets in leagues: {bet_league_ids}")
        target_league_ids = live_league_ids.intersection(bet_league_ids)
        if not target_league_ids:
            logger.info("No leagues with both live games and active bets, skipping 5-minute fetch")
            await asyncio.sleep(300)
            continue
        today_edt = datetime.now(EDT).strftime("%Y-%m-%d")
        season = datetime.now().year
        logger.info(f"Starting 5-minute fetch for live games with bets in {target_league_ids}")
        async with aiohttp.ClientSession() as session:
            for league_name, league_info in LEAGUE_IDS.items():
                sport = league_info.get("sport", "").lower()
                league_id = str(league_info.get("id"))
                if league_id not in target_league_ids:
                    continue
                season = get_current_season(league_name)
                await fetch_games(pool, session, sport, league_name, league_id, today_edt, season)
        logger.info("5-minute fetch for live games with bets completed")
        await asyncio.sleep(300)


async def main():
    """Run initial fetch, daily 3 AM EDT fetch, and 5-minute live games fetch."""
    logger.info("Entering main function of fetcher.py")
    try:
        pool = await create_db_pool()
        try:
            # Run initial fetch
            await initial_fetch(pool)
            # Start background tasks
            daily_task = asyncio.create_task(daily_3am_fetch(pool))
            live_task = asyncio.create_task(live_games_fetch(pool))
            # Keep the main task running
            while True:
                try:
                    # Check if tasks are still running
                    if daily_task.done():
                        logger.error("Daily fetch task ended unexpectedly")
                        daily_task = asyncio.create_task(daily_3am_fetch(pool))
                    if live_task.done():
                        logger.error("Live games fetch task ended unexpectedly")
                        live_task = asyncio.create_task(live_games_fetch(pool))
                    await asyncio.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(60)  # Wait before retrying
        finally:
            pool.close()
            await pool.wait_closed()
            logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise


if __name__ == "__main__":
    logger.info("Executing fetcher.py as main script")
    asyncio.run(main())


def start_fetcher(self):
    if self.fetcher_process is None or self.fetcher_process.poll() is not None:
        # Create a log file for fetcher output
        fetcher_log_path = os.path.join(BASE_DIR, "logs", "fetcher.log")
        os.makedirs(os.path.dirname(fetcher_log_path), exist_ok=True)
        # Open log file in append mode
        with open(fetcher_log_path, "a") as log_file:
            self.fetcher_process = subprocess.Popen(
                [sys.executable, os.path.join(BASE_DIR, "fetcher.py")],
                stdout=log_file,
                stderr=log_file,
                text=True,
                bufsize=1,
            )
        logger.info("Started fetcher (fetcher.py) as a subprocess with logging to %s", fetcher_log_path)
        # Start a background task to monitor the fetcher process
        async def monitor_fetcher():
            while True:
                if self.fetcher_process.poll() is not None:
                    logger.error("Fetcher process ended unexpectedly. Restarting...")
                    self.start_fetcher()
                await asyncio.sleep(5)  # Check every 5 seconds

        asyncio.create_task(monitor_fetcher())