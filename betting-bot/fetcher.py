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
from config.leagues import LEAGUE_IDS, LEAGUE_SEASON_STARTS, ENDPOINTS, get_current_season

# Configure logging to file and console
try:
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "fetcher.log")),
            logging.StreamHandler(),
        ],
    )
except Exception as e:
    print(f"Failed to configure logging: {e}", file=sys.stderr)
    raise
logger = logging.getLogger(__name__)
logger.info("Starting fetcher.py")

# Load environment variables
load_dotenv()

# Check API key configuration
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    logger.error("API_KEY not found in environment variables!")
    sys.exit(1)
logger.info("API key configuration found")

# Check database configuration
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_POOL_MIN_SIZE = int(os.getenv("MYSQL_POOL_MIN_SIZE", "1"))
MYSQL_POOL_MAX_SIZE = int(os.getenv("MYSQL_POOL_MAX_SIZE", "10"))

logger.info("Database configuration:")
logger.info(f"  Host: {MYSQL_HOST}")
logger.info(f"  Port: {MYSQL_PORT}")
logger.info(f"  Database: {MYSQL_DB}")
logger.info(f"  User: {MYSQL_USER}")
logger.info(f"  Pool size: {MYSQL_POOL_MIN_SIZE}-{MYSQL_POOL_MAX_SIZE}")

if not all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB]):
    logger.error("Missing required database configuration!")
    logger.error(f"Host: {'✓' if MYSQL_HOST else '✗'}")
    logger.error(f"User: {'✓' if MYSQL_USER else '✗'}")
    logger.error(f"Password: {'✓' if MYSQL_PASSWORD else '✗'}")
    logger.error(f"Database: {'✓' if MYSQL_DB else '✗'}")
    sys.exit(1)
logger.info("Database configuration found")

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
    "afl": {
        "AFL": {"id": 1, "name": "Australian Football League"},
    },
    "formula-1": {
        "Formula-1": {"id": 1, "name": "Formula 1"},
    },
    "mma": {
        "MMA": {"id": 1, "name": "Mixed Martial Arts"},
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
    """Convert ISO 8601 string to MySQL DATETIME string (ETC)."""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_etc = dt.astimezone(EDT).replace(tzinfo=None)
        return dt_etc.strftime("%Y-%m-%d %H:%M:%S")
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
                "fetched_at": datetime.now(EDT).strftime("%Y-%m-%d %H:%M:%S"),
            }
        elif sport.lower() in ["baseball", "mlb"]:
            teams = safe_get(game, "teams", default={})
            home_team = safe_get(teams, "home", default={})
            away_team = safe_get(teams, "away", default={})
            
            # Get team names and normalize them for MLB
            home_team_name = safe_get(home_team, "name", default="Unknown")
            away_team_name = safe_get(away_team, "name", default="Unknown")
            
            if league.upper() == "MLB":
                from data.game_utils import normalize_team_name_any_league
                home_team_name = normalize_team_name_any_league(home_team_name)
                away_team_name = normalize_team_name_any_league(away_team_name)
            
            game_data = {
                "id": str(safe_get(game, "id", default="")),
                "sport": "Baseball",
                "league_id": league_id,
                "league_name": LEAGUE_CONFIG["baseball"].get(league, {}).get("name", league),
                "home_team_id": str(safe_get(home_team, "id")),
                "away_team_id": str(safe_get(away_team, "id")),
                "home_team_name": home_team_name,
                "away_team_name": away_team_name,
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
                "fetched_at": datetime.now(EDT).strftime("%Y-%m-%d %H:%M:%S"),
            }
        elif sport.lower() == "afl":
            teams = safe_get(game, "teams", default={})
            home_team = safe_get(teams, "home", default={})
            away_team = safe_get(teams, "away", default={})
            league_info = safe_get(game, "league", default={})
            score = safe_get(game, "scores", default={})
            game_data = {
                "id": str(safe_get(game, "game", "id", default="")),
                "sport": "AFL",
                "league_id": league_id,
                "league_name": LEAGUE_CONFIG["afl"].get(league, {}).get("name", league),
                "home_team_id": str(safe_get(home_team, "id")),
                "away_team_id": str(safe_get(away_team, "id")),
                "home_team_name": safe_get(home_team, "name", default="Unknown"),
                "away_team_name": safe_get(away_team, "name", default="Unknown"),
                "start_time": iso_to_mysql_datetime(safe_get(game, "date")),
                "status": safe_get(game, "status", "long", default="Scheduled"),
                "score": json.dumps(
                    {
                        "home": safe_get(score, "home", "score", default=0),
                        "away": safe_get(score, "away", "score", default=0),
                    }
                ),
                "venue": safe_get(game, "venue", default=None),
                "referee": None,
                "raw_json": json.dumps(game),
                "fetched_at": datetime.now(EDT).strftime("%Y-%m-%d %H:%M:%S"),
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
                "league_name": LEAGUE_CONFIG.get(sport, {}).get(league, {}).get("name", league),
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
                "fetched_at": datetime.now(EDT).strftime("%Y-%m-%d %H:%M:%S"),
            }
        if not game_data["id"] or not game_data["start_time"]:
            logger.error(f"Skipping game with missing id or start_time: {json.dumps(game)}")
            return None
        logger.debug(f"Successfully mapped game: {game_data['id']}")
        return game_data
    except Exception as e:
        logger.error(f"Error mapping game data for {sport}/{league}: {e}")
        return None


async def create_db_pool() -> aiomysql.Pool:
    """Create a MySQL connection pool."""
    logger.info("Attempting to create MySQL connection pool")
    if not MYSQL_HOST:
        logger.error("MYSQL_HOST is not set in environment variables")
        raise ValueError("MYSQL_HOST is required")
    if not MYSQL_USER:
        logger.error("MYSQL_USER is not set in environment variables")
        raise ValueError("MYSQL_USER is required")
    if not MYSQL_PASSWORD:
        logger.error("MYSQL_PASSWORD is not set in environment variables")
        raise ValueError("MYSQL_PASSWORD is required")
    if not MYSQL_DB:
        logger.error("MYSQL_DB is not set in environment variables")
        raise ValueError("MYSQL_DB is required")
    logger.info("Database connection parameters:")
    logger.info(f"  Host: {MYSQL_HOST}")
    logger.info(f"  Port: {MYSQL_PORT}")
    logger.info(f"  Database: {MYSQL_DB}")
    logger.info(f"  User: {MYSQL_USER}")
    logger.info(f"  Password: {'*' * len(MYSQL_PASSWORD) if MYSQL_PASSWORD else 'Not set'}")
    logger.info("Testing database connection...")
    try:
        async with aiomysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DB,
            connect_timeout=10
        ) as test_conn:
            logger.info("Test connection successful")
        logger.info("Creating connection pool...")
        pool = await aiomysql.create_pool(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DB,
            autocommit=True,
            minsize=MYSQL_POOL_MIN_SIZE,
            maxsize=MYSQL_POOL_MAX_SIZE,
            connect_timeout=10
        )
        logger.info("Database connection pool created successfully")
        return pool
    except aiomysql.Error as e:
        error_code = e.args[0] if e.args else 'unknown'
        sql_state = e.args[1] if len(e.args) > 1 else 'unknown'
        error_message = str(e)
        logger.error("MySQL error creating database pool:")
        logger.error(f"  Error code: {error_code}")
        logger.error(f"  SQL state: {sql_state}")
        logger.error(f"  Error message: {error_message}")
        if error_code == 1045:
            logger.error("Access denied - please check username and password")
        elif error_code == 2003:
            logger.error(f"Could not connect to MySQL server at {MYSQL_HOST}:{MYSQL_PORT}")
        elif error_code == 1049:
            logger.error(f"Database '{MYSQL_DB}' does not exist")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating database pool: {e}")
        logger.exception("Full traceback:")
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
                    (api_game_id, id, sport, league_id, league_name, home_team_id, away_team_id, 
                     home_team_name, away_team_name, start_time, status, score, 
                     venue, referee, raw_json, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        game_data.get("api_game_id", str(game_data["id"])),  # Use api_game_id if available, fallback to id
                        None,  # Let MySQL auto-increment handle the internal id
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
    """Fetch active bets for live games from bets table."""
    if not live_game_ids:
        logger.info("No live game IDs provided for bet check")
        return []
    query = f"""
        SELECT game_id, league
        FROM bets
        WHERE game_id IN ({','.join(['%s'] * len(live_game_ids))})
        AND status = 'pending'
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, live_game_ids)
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
    end_date: str = None,
):
    """Fetch game data for a specific league and date range, saving to database and cache."""
    logger.info(
        f"Fetching games for {league_name} (league_id={league_id}, sport={sport}, date={date}, season={season})"
    )
    headers = {"x-apisports-key": API_KEY}
    base_endpoint = ENDPOINTS.get(sport)
    if not base_endpoint or not league_id:
        logger.warning(f"Skipping {league_name}: missing endpoint or league_id")
        return

    endpoint = f"{base_endpoint}/fixtures" if sport == "football" else f"{base_endpoint}/games"
    params = {"league": league_id, "date": date, "season": season}
    if end_date:
        params["to"] = end_date

    logger.debug(f"API request to {endpoint} with params: {params}")
    try:
        async with session.get(endpoint, headers=headers, params=params) as resp:
            logger.info(f"API response status for {league_name}: {resp.status}")
            if resp.status != 200:
                logger.error(f"Error fetching {league_name}: {resp.status} - {await resp.text()}")
                return

            data = await resp.json()
            games = data.get("response", [])
            logger.info(f"Received {len(games)} games for {league_name}")

            if not games:
                logger.warning(f"No games returned for {league_name} on {date}. Skipping future queries for this league.")
                return  # Stop querying this league

            # Save league-level data to cache
            cache_file = os.path.join(CACHE_DIR, f"{league_name}_{date}.json")
            with open(cache_file, "w") as f:
                json.dump(data, f)

            # Use H2H query format for each game
            for game in games:
                home_team_id = game.get("teams", {}).get("home", {}).get("id")
                away_team_id = game.get("teams", {}).get("away", {}).get("id")
                if home_team_id and away_team_id:
                    h2h_endpoint = f"{base_endpoint}/games/h2h"
                    h2h_params = {
                        "league": league_id,
                        "season": season,
                        "date": date,
                        "h2h": f"{home_team_id}-{away_team_id}"
                    }
                    async with session.get(h2h_endpoint, headers=headers, params=h2h_params) as h2h_resp:
                        logger.info(f"H2H API response status: {h2h_resp.status}")
                        if h2h_resp.status == 200:
                            h2h_data = await h2h_resp.json()
                            h2h_games = h2h_data.get("response", [])
                            for h2h_game in h2h_games:
                                normalized_game = map_game_data(h2h_game, sport, league_name, league_id)
                                if normalized_game:
                                    await save_game_to_db(pool, normalized_game)
                        else:
                            logger.error(f"Error fetching H2H data: {h2h_resp.status} - {await h2h_resp.text()}")

    except Exception as e:
        logger.error(f"Error processing {league_name}: {str(e)}", exc_info=True)


async def initial_fetch(pool: aiomysql.Pool):
    """Perform initial fetch of all scheduled games for today and tomorrow."""
    today = datetime.now(timezone.utc)
    tomorrow = today + timedelta(days=1)
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    # Add a 6-hour timer for querying all leagues
    last_full_fetch = datetime.now(timezone.utc)
    while True:
        now = datetime.now(timezone.utc)
        if (now - last_full_fetch).total_seconds() >= 6 * 3600:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for league_name, league_info in LEAGUE_IDS.items():
                    sport = league_info["sport"]
                    league_id = league_info["id"]
                    season = get_current_season(league_name)
                    logger.info(f"Performing full fetch for {league_name} (season: {season})")
                    tasks.append(fetch_games(pool, session, sport, league_name, league_id, today_str, season))
                    tasks.append(fetch_games(pool, session, sport, league_name, league_id, tomorrow_str, season))
                await asyncio.gather(*tasks)
            last_full_fetch = now
        await asyncio.sleep(15)


# Remove old live_games_fetch and daily_3am_fetch functions
# Add new 15-second update loop
async def update_api_games_every_15_seconds(pool: aiomysql.Pool):
    """Fetch and update all leagues' games every 15 seconds."""
    logger.info("Starting 15-second API update loop for api_games table.")
    while True:
        try:
            now = datetime.now(timezone.utc)
            today_str = now.strftime("%Y-%m-%d")
            async with aiohttp.ClientSession() as session:
                tasks = []
                for league_name, league_info in LEAGUE_IDS.items():
                    sport = league_info["sport"]
                    league_id = league_info["id"]
                    season = get_current_season(league_name)
                    logger.info(f"[15s] Fetching games for {league_name} (season: {season})")
                    tasks.append(fetch_games(pool, session, sport, league_name, league_id, today_str, season))
                await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("[15s] All leagues updated. Sleeping 15 seconds.")
        except Exception as e:
            logger.error(f"[15s] Error in 15-second update loop: {e}", exc_info=True)
        await asyncio.sleep(15)


async def main():
    """Run initial fetch, then update api_games every 15 seconds."""
    logger.info("Entering main function of fetcher.py (15s update mode)")
    try:
        logger.info(f"Using database: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
        logger.info(f"API endpoints configured for: {list(ENDPOINTS.keys())}")
        logger.info(f"League IDs configured: {list(LEAGUE_IDS.keys())}")
        logger.info("Creating database connection pool...")
        pool = await create_db_pool()
        logger.info("Database connection pool created successfully")
        try:
            logger.info("Starting initial fetch...")
            await initial_fetch(pool)
            logger.info("Initial fetch completed successfully")
            logger.info("Starting 15-second background update task...")
            await update_api_games_every_15_seconds(pool)
        finally:
            logger.info("Closing database connection pool...")
            pool.close()
            await pool.wait_closed()
            logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        logger.exception("Full traceback:")
        raise


if __name__ == "__main__":
    logger.info("Executing fetcher.py as main script")
    asyncio.run(main())