
import asyncpg
import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

# Load environment variables
load_dotenv("bot/.env")

# Fix import issues with fallback
try:
    from config.leagues import LEAGUE_CONFIG, LEAGUE_IDS
except ImportError:
    LEAGUE_CONFIG = {}
    LEAGUE_IDS = {}

try:
    from data.game_utils import get_league_abbreviation, normalize_team_name
except ImportError:
    def get_league_abbreviation(league_name: str) -> str:
        return league_name
    def normalize_team_name(team_name: str, sport: str = None, league: str = None) -> str:
        return team_name

try:
    from utils.enhanced_cache_manager import enhanced_cache_get as cache_get, enhanced_cache_set as cache_set, enhanced_cache_query as cache_query
except ImportError:
    async def cache_get(prefix: str, key: str) -> Optional[Any]:
        return None
    async def cache_set(prefix: str, key: str, value: Any, ttl: int = 3600) -> bool:
        return True
    async def cache_query(prefix: str = "db_query", ttl: Optional[int] = None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

try:
    from services.performance_monitor import record_query, time_operation
except ImportError:
    def record_query(query: str, duration: float, success: bool = True, error_message: str = None, cache_hit: bool = False) -> None:
        pass
    def time_operation(operation: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

logger = logging.getLogger(__name__)

# PostgreSQL config
try:
    from config.database import (
        PG_DATABASE,
        PG_HOST,
        PG_PASSWORD,
        PG_PORT,
        PG_USER,
        DATABASE_URL,
    )
except ImportError:
    PG_DATABASE = os.getenv("PG_DATABASE")
    PG_HOST = os.getenv("PG_HOST")
    PG_PASSWORD = os.getenv("PG_PASSWORD")
    PG_PORT = os.getenv("PG_PORT", "5432")
    PG_USER = os.getenv("PG_USER")
    DATABASE_URL = os.getenv("DATABASE_URL")

if not PG_DATABASE:
    logger.critical("CRITICAL ERROR: PG_DATABASE environment variable is not set.")
    logger.critical("Please set PG_DATABASE in your .env file or environment variables.")
    logger.critical("Example: PG_DATABASE=dbsbm")



class DatabaseManager:
    """Manages the connection pool and executes queries against the PostgreSQL DB."""

    def __init__(self):
        self._pool: Optional[asyncpg.pool.Pool] = None
        self.db_name = PG_DATABASE
        missing_vars = []
        if not PG_HOST:
            missing_vars.append("PG_HOST")
        if not PG_USER:
            missing_vars.append("PG_USER")
        if not PG_PASSWORD:
            missing_vars.append("PG_PASSWORD")
        if not self.db_name:
            missing_vars.append("PG_DATABASE")
        if missing_vars:
            logger.critical(f"Missing required PostgreSQL environment variables: {', '.join(missing_vars)}")
            logger.critical("Please set all required variables in your .env file:")
            logger.critical("PG_HOST=localhost")
            logger.critical("PG_USER=your_username")
            logger.critical("PG_PASSWORD=your_password")
            logger.critical("PG_DATABASE=your_database_name")
            raise ValueError(f"Missing required PostgreSQL environment variables: {', '.join(missing_vars)}")
        logger.info("PostgreSQL DatabaseManager initialized successfully.")
        logger.debug(f"Database configuration: Host={PG_HOST}, Port={PG_PORT}, DB={self.db_name}, User={PG_USER}")

    async def connect(self) -> Optional[asyncpg.pool.Pool]:
        if self._pool is None:
            logger.info("Attempting to create PostgreSQL connection pool...")
            max_retries = 3
            retry_delay = 5
            last_error = None
            for attempt in range(max_retries):
                try:
                    self._pool = await asyncpg.create_pool(
                        user=PG_USER,
                        password=PG_PASSWORD,
                        database=self.db_name,
                        host=PG_HOST,
                        port=int(PG_PORT),
                        min_size=1,
                        max_size=5,
                    )
                    async with self._pool.acquire() as conn:
                        await conn.execute("SELECT 1")
                    logger.info("PostgreSQL connection pool created and tested successfully.")
                    await self.initialize_db()
                    return self._pool
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to connect to PostgreSQL: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
            logger.error(f"Failed to create PostgreSQL connection pool after {max_retries} attempts. Last error: {last_error}")
            return None
        return self._pool

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL connection pool closed.")

    @time_operation("db_execute")
    async def execute(self, query: str, *args) -> Tuple[Optional[str], Optional[int]]:
        pool = await self.connect()
        if not pool:
            logger.error("Cannot execute: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")
        logger.debug("Executing DB Query: %s Args: %s", query, args)
        start_time = time.time()
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(query, *args)
                execution_time = time.time() - start_time
                record_query(query, execution_time, success=True)
                return result, None
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time, success=False, error_message=str(e))
            logger.error("[DB EXECUTE] Error executing query: %s Args: %s. Error: %s", query, args, str(e), exc_info=True)
            raise

    @time_operation("db_executemany")
    async def executemany(self, query: str, args_list: List[Tuple]) -> Optional[int]:
        pool = await self.connect()
        if not pool:
            logger.error("Cannot executemany: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")
        logger.debug("Executing Many DB Query: %s Batch size: %s", query, len(args_list))
        start_time = time.time()
        try:
            async with pool.acquire() as conn:
                await conn.executemany(query, args_list)
                execution_time = time.time() - start_time
                record_query(query, execution_time, success=True)
                return len(args_list)
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time, success=False, error_message=str(e))
            logger.error("[DB EXECUTEMANY] Error executing batch query: %s", str(e), exc_info=True)
            logger.error("[DB EXECUTEMANY] Query that failed: %s", query)
            logger.error("[DB EXECUTEMANY] Batch size that failed: %s", len(args_list))
            return None

    @time_operation("db_fetch_one")
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetch_one: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")
        cache_key = f"fetch_one:{hash(query + str(args))}"
        cached_result = await cache_get("db_query", cache_key)
        if cached_result is not None:
            logger.debug(f"Cache HIT for fetch_one: {query[:50]}...")
            return dict(cached_result)
        logger.debug("Fetching One DB Query: %s Args: %s", query, args)
        start_time = time.time()
        try:
            async with pool.acquire() as conn:
                result = await conn.fetchrow(query, *args)
                execution_time = time.time() - start_time
                record_query(query, execution_time, success=True, cache_hit=False)
                if result is not None:
                    await cache_set("db_query", cache_key, dict(result), ttl=600)
                return dict(result) if result else None
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time, success=False, error_message=str(e))
            logger.error("Error fetching one row: %s Args: %s. Error: %s", query, args, e, exc_info=True)
            return None

    @time_operation("db_fetch_all")
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetch_all: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")
        cache_key = f"fetch_all:{hash(query + str(args))}"
        cached_result = await cache_get("db_query", cache_key)
        if cached_result is not None:
            logger.debug(f"Cache HIT for fetch_all: {query[:50]}...")
            return [dict(row) for row in cached_result]
        logger.debug("Fetching All DB Query: %s Args: %s", query, args)
        start_time = time.time()
        try:
            async with pool.acquire() as conn:
                results = await conn.fetch(query, *args)
                execution_time = time.time() - start_time
                record_query(query, execution_time, success=True, cache_hit=False)
                if results:
                    await cache_set("db_query", cache_key, [dict(row) for row in results], ttl=600)
                return [dict(row) for row in results]
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time, success=False, error_message=str(e))
            logger.error("Error fetching all rows: %s Args: %s. Error: %s", query, args, e, exc_info=True)
            return []

    @time_operation("db_fetchval")
    async def fetchval(self, query: str, *args) -> Optional[Any]:
        """Fetch a single value from the first row with caching support."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetchval: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        cache_key = f"fetchval:{hash(query + str(args))}"
        cached_result = await cache_get("db_query", cache_key)
        if cached_result is not None:
            logger.debug(f"Cache HIT for fetchval: {query[:50]}...")
            return cached_result

        logger.debug("Fetching Value DB Query: %s Args: %s", query, args)
        start_time = time.time()
        try:
            async with pool.acquire() as conn:
                result = await conn.fetchval(query, *args)
                execution_time = time.time() - start_time
                record_query(query, execution_time, success=True, cache_hit=False)
                if result is not None:
                    await cache_set("db_query", cache_key, result, ttl=600)
                return result
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time, success=False, error_message=str(e))
            logger.error("Error fetching value: %s Args: %s. Error: %s", query, args, e, exc_info=True)
            return None

    async def table_exists(self, conn, table_name: str) -> bool:
        """Check if a table exists in the PostgreSQL database."""
        try:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1 AND table_schema = 'public')",
                table_name,
            )
            return result
        except Exception as e:
            logger.error("Error checking if table '%s' exists: %s", table_name, e, exc_info=True)
            raise

    async def _check_and_add_column(self, conn, table_name, column_name, column_definition):
        """Checks if a column exists and adds it if not."""
        exists = await self._column_exists(conn, table_name, column_name)
        if not exists:
            logger.info("Adding column '%s' to table '%s'...", column_name, table_name)
            alter_statement = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            try:
                await conn.execute(alter_statement)
                logger.info("Successfully added column '%s'.", column_name)
            except Exception as e:
                logger.error("Failed to add column '%s' to table '%s': %s", column_name, table_name, e, exc_info=True)
                raise
        else:
            logger.debug("Column '%s' already exists in '%s'.", column_name, table_name)

    async def initialize_db(self):
        """Initializes the database schema."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot initialize DB: Connection pool unavailable.")
            return
        try:
            async with pool.acquire() as conn:
                # Create tables using asyncpg for PostgreSQL
                # Example for one table:
                if not await self.table_exists(conn, "users"):
                    await conn.execute(
                        """
                        CREATE TABLE users (
                            id BIGSERIAL PRIMARY KEY,
                            username TEXT NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                        );
                        """
                    )
                # ...repeat for all other tables, updating types and removing MySQL-specific options...
                logger.info("Database schema initialization/verification complete.")
        except Exception as e:
            logger.error(
                "Error initializing/verifying database schema: %s", e, exc_info=True
            )
            raise

    async def _create_game_events_table(self, cursor):
        """Create the game_events table if it doesn't exist."""
        pass  # TODO: Implement table creation

    async def _column_exists(self, conn, table_name: str, column_name: str) -> bool:
        """Helper to check if a column exists in PostgreSQL."""
        result = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = $1 AND column_name = $2 AND table_schema = 'public')",
            table_name,
            column_name,
        )
        return result

    async def save_game(
        self,
        game_id: str,
        league_id: str,
        league_name: str,
        home_team: str,
        away_team: str,
        start_time: str,
        status: str = "Scheduled",
    ):
        """Save a game to the games table."""
        try:
            if not status or str(status).lower() in ("none", "null", "", "n/a"):
                status = "scheduled"
            sport = (
                "Baseball"
                if league_id == "4424"
                else (
                    "Hockey"
                    if league_id == "4380"
                    else (
                        "Football"
                        if league_id == "4405"
                        else (
                            "Basketball"
                            if league_id == "4388"
                            else (
                                "Soccer"
                                if league_id
                                in ["4387", "4391", "4392", "4393", "4394", "4395"]
                                else (
                                    "Baseball"
                                    if league_id in ["4429", "4430"]
                                    else (
                                        "Basketball"
                                        if league_id == "4389"
                                        else (
                                            "Hockey" if league_id == "4431" else "Other"
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )

            query = """
                INSERT INTO games (
                    id, sport, league_id, league_name, home_team_name, away_team_name,
                    start_time, status, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (id) DO UPDATE SET
                    sport = EXCLUDED.sport,
                    league_id = EXCLUDED.league_id,
                    league_name = EXCLUDED.league_name,
                    home_team_name = EXCLUDED.home_team_name,
                    away_team_name = EXCLUDED.away_team_name,
                    start_time = EXCLUDED.start_time,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            """
            await self.execute(
                query,
                game_id,
                sport,
                league_id,
                league_name,
                home_team,
                away_team,
                start_time,
                status,
            )
            logger.info(
                "Saved game %s to database with status '%s' and league_name '%s'",
                game_id,
                status,
                league_name,
            )
            return True
        except Exception as e:
            logger.error("Error saving game %s: %s", game_id, e, exc_info=True)
            return False

    async def upsert_api_game(self, game: dict):
        """Upsert a full API game record, storing all fields in their respective columns."""
        season = game.get("season")
        if not season:
            season = datetime.now().year
            if game.get("sport", "").lower() == "baseball":
                current_month = datetime.now().month
                if current_month >= 10 or current_month <= 2:
                    season = season + 1

        # Support both flat and nested structures
        def safe_get_team(game, key):
            # Try nested structure first
        query = """
            INSERT INTO api_games (
                api_game_id, sport, league_id, league_name, season, home_team_name, away_team_name,
                start_time, end_time, status, score, raw_json, fetched_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (api_game_id) DO UPDATE SET
                sport=EXCLUDED.sport,
                league_id=EXCLUDED.league_id,
                league_name=EXCLUDED.league_name,
                season=EXCLUDED.season,
                home_team_name=EXCLUDED.home_team_name,
                away_team_name=EXCLUDED.away_team_name,
                start_time=EXCLUDED.start_time,
                end_time=EXCLUDED.end_time,
                status=EXCLUDED.status,
                score=EXCLUDED.score,
                raw_json=EXCLUDED.raw_json,
                fetched_at=EXCLUDED.fetched_at,
                updated_at=CURRENT_TIMESTAMP
        """
        score_data = game.get("score")
        score_json = json.dumps(score_data) if isinstance(score_data, dict) else (score_data or "")
        def format_datetime(dt_str):
            if not dt_str:
                return None
            try:
                dt = datetime.fromisoformat(dt_str)
                return dt.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return dt_str
        start_time = format_datetime(game.get("start_time"))
        end_time = format_datetime(game.get("end_time"))
        params = (
            str(game.get("api_game_id") or game.get("id")),
            game.get("sport", ""),
            str(game.get("league_id", "")),
            game.get("league", ""),
            season,
            home_team_name,
            away_team_name,
            start_time,
            end_time,
            game.get("status", ""),
            score_json,
            (
                game.get("raw_json")
                if isinstance(game.get("raw_json"), str)
                else json.dumps(game.get("raw_json", {}))
            ),
            game.get(
                "fetched_at", datetime.now(
                    timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            ),
        )
        await self.execute(query, *params)
            str(game.get("api_game_id") or game.get("id")),
            game.get("sport", ""),
            str(game.get("league_id", "")),
            game.get("league", ""),
            season,
            home_team_name,
            away_team_name,
            start_time,
            end_time,
            game.get("status", ""),
            score_json,
            (
                game.get("raw_json")
                if isinstance(game.get("raw_json"), str)
                else json.dumps(game.get("raw_json", {}))
            ),
            game.get(
                "fetched_at", datetime.now(
                    timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            ),
        )
        await self.execute(query, params)

    async def save_team(self, team: dict):
        """Insert or update a team record in the teams table."""
        query = """
            INSERT INTO teams (
                id, name, sport, code, country, founded, national, logo,
                venue_id, venue_name, venue_address, venue_city, venue_capacity, venue_surface, venue_image
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8,
                $9, $10, $11, $12, $13, $14, $15
            )
            ON CONFLICT (id) DO UPDATE SET
                name=EXCLUDED.name, sport=EXCLUDED.sport, code=EXCLUDED.code, country=EXCLUDED.country,
                founded=EXCLUDED.founded, national=EXCLUDED.national, logo=EXCLUDED.logo,
                venue_id=EXCLUDED.venue_id, venue_name=EXCLUDED.venue_name, venue_address=EXCLUDED.venue_address,
                venue_city=EXCLUDED.venue_city, venue_capacity=EXCLUDED.venue_capacity,
                venue_surface=EXCLUDED.venue_surface, venue_image=EXCLUDED.venue_image
        """
        # ...existing code...
        params = (
            team.get("id"),
            team.get("name"),
            team.get("sport"),
            team.get("code"),
            team.get("country"),
            team.get("founded"),
            int(team.get("national", False)),
            team.get("logo"),
            team.get("venue_id"),
            team.get("venue_name"),
            team.get("venue_address"),
            team.get("venue_city"),
            team.get("venue_capacity"),
            team.get("venue_surface"),
            team.get("venue_image"),
        )
        await self.execute(query, *params)

    async def sync_games_from_api(self, force_season: int = None):
        """Sync games from API to database."""
        try:
            from api.sports_api import SportsAPI

            api = SportsAPI(self)
            current_date = datetime.now().strftime("%Y-%m-%d")
            for league_name, league_info in LEAGUE_IDS.items():
                sport = league_info.get("sport", "").lower()
                if not sport:
                    continue
                try:
                    season = None
                    if force_season and sport == "baseball" and league_name == "MLB":
                        season = force_season
                        logger.info("Using forced season %s for MLB", season)
                    elif sport == "baseball" and league_name == "MLB":
                        current_year = datetime.now().year
                        current_month = datetime.now().month
                        if current_month >= 10 or current_month <= 2:
                            season = current_year + 1
                            logger.info(
                                "MLB: In offseason, using next season %s", season
                            )
                        else:
                            season = current_year
                            logger.info(
                                "MLB: In season, using current season %s", season
                            )
                    else:
                        season = datetime.now().year
                        logger.info(
                            "Using current year %s for %s/%s",
                            season,
                            sport,
                            league_name,
                        )
                    games_response = await api.fetch_games(
                        sport=sport,
                        league=league_name,
                        date=current_date,
                        season=season,
                    )
                    
                    # Handle potential APIResponse object
                    if hasattr(games_response, 'data'):
                        games = games_response.data
                    else:
                        games = games_response
                        
                    if not isinstance(games, list):
                        logger.warning(
                            "Expected list of games but got %s for %s/%s", 
                            type(games), sport, league_name
                        )
                        games = []
                        
                    logger.info(
                        "Fetched %d games for %s/%s", len(
                            games), sport, league_name
                    )
                    for game in games:
                        try:
                            game["season"] = season
                            await self.upsert_api_game(game)
                            logger.info(
                                "Saved game %s to database", game.get("id"))
                        except Exception as e:
                            logger.error(
                                "Error saving game %s: %s",
                                game.get("id"),
                                e,
                                exc_info=True,
                            )
                            continue
                except Exception as e:
                    logger.error(
                        "Error syncing games for %s: %s", league_name, e, exc_info=True
                    )
                    continue
        except Exception as e:
            logger.error("Error in sync_games_from_api: $1", e, exc_info=True)
            raise

    async def get_normalized_games_for_dropdown(
        self, league_name: str, season: int = None
    ) -> List[Dict[str, Any]]:
        """Fetch and normalize games for a league from the api_games table for use in a bet dropdown."""
        logger.info(
            "[get_normalized_games_for_dropdown] Starting fetch for league_name=%s, season=%s",
            league_name,
            season,
        )
        dropdown_games = [
            {
                "id": "manual",
                "api_game_id": "manual",
                "home_team": "Manual Entry",
                "away_team": "Manual Entry",
                "start_time": datetime.now(timezone.utc),
                "status": "Manual",
                "home_team_name": "Manual Entry",
                "away_team_name": "Manual Entry",
            }
        ]
        sport = None
        league_key = None
        for key, league_info in LEAGUE_IDS.items():
            if key == league_name:
                sport = league_info.get("sport", "").capitalize()
                league_key = key
                league_name = (
                    LEAGUE_CONFIG.get(league_info.get("sport", ""), {})
                    .get(key, {})
                    .get("name", key)
                )
                if league_name == "MLB":
                    league_name = "Major League Baseball"
                logger.info(
                    "[get_normalized_games_for_dropdown] Found league info: sport=%s, league_key=%s, league_name=%s",
                    sport,
                    league_key,
                    league_name,
                )
                break
        if not sport or not league_name:
            logger.warning(
                "[get_normalized_games_for_dropdown] Could not find sport and league name for league_name=%s",
                league_name,
            )
            return dropdown_games
        league_abbr = get_league_abbreviation(league_name)
        logger.info(
            "[get_normalized_games_for_dropdown] Looking up games for %s/%s (abbreviation: %s, key: %s)",
            sport,
            league_name,
            league_abbr,
            league_key,
        )
        # Query existing games from api_games table without syncing from API
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        logger.info(
            "[get_normalized_games_for_dropdown] Using today_start=%s", today_start
        )
        if sport.lower() == "baseball":
            finished_statuses = [
                "Match Finished",
                "Finished",
                "FT",
                "Game Finished",
                "Final",
            ]
        else:
            finished_statuses = [
                "Match Finished",
                "Finished",
                "FT",
                "Ended",
                "Game Finished",
                "Final",
            ]
        logger.info(
            "[get_normalized_games_for_dropdown] Using finished_statuses=%s",
            finished_statuses,
        )
        query = """
            SELECT id, api_game_id, home_team_name, away_team_name, start_time, status, score, league_name
            FROM api_games
            WHERE sport = $1
            AND league_id = %s
            AND UPPER(league_name) = UPPER(%s)
            AND start_time >= %s
            AND status NOT IN (%s, %s, %s, %s, %s)
            AND season = %s
            ORDER BY start_time ASC LIMIT 100
        """
        from data.game_utils import LEAGUE_ID_MAP

        league_id = LEAGUE_ID_MAP.get(league_name, "1")
        logger.info(
            "[get_normalized_games_for_dropdown] Using league_id=%s", league_id)
        if sport.lower() == "baseball" and league_key == "MLB":
            current_year = datetime.now().year
            current_month = datetime.now().month
            if season is not None:
                logger.info(
                    "[get_normalized_games_for_dropdown] MLB: Using provided season %s",
                    season,
                )
                rows = await self.fetch_all(
                    query,
                    (sport, league_id, league_name, today_start)
                    + tuple(finished_statuses)
                    + (season,),
                )
            elif current_month >= 10 or current_month <= 2:
                next_year = current_year + 1
                logger.info(
                    "[get_normalized_games_for_dropdown] MLB: In offseason, checking %s",
                    next_year,
                )
                rows = await self.fetch_all(
                    query,
                    (sport, league_id, league_name, today_start)
                    + tuple(finished_statuses)
                    + (next_year,),
                )
            else:
                logger.info(
                    "[get_normalized_games_for_dropdown] MLB: In season, checking %s",
                    current_year,
                )
                rows = await self.fetch_all(
                    query,
                    (sport, league_id, league_name, today_start)
                    + tuple(finished_statuses)
                    + (current_year,),
                )
        else:
            season = season if season is not None else datetime.now().year
            logger.info(
                "[get_normalized_games_for_dropdown] Non-MLB: Using season %s", season
            )
            rows = await self.fetch_all(
                query,
                (sport, league_id, league_name, today_start)
                + tuple(finished_statuses)
                + (season,),
            )
        if not rows:
            logger.warning(
                "[get_normalized_games_for_dropdown] No active games found for sport=%s, league_id=%s, league_name=%s",
                sport,
                league_id,
                league_name,
            )
            return dropdown_games
        for row in rows:
            try:
                # Always use normalize_team_name for all leagues
                home_team = normalize_team_name(
                    row["home_team_name"], sport, league_key
                )
                away_team = normalize_team_name(
                    row["away_team_name"], sport, league_key
                )
                logger.info(
                    "[get_normalized_games_for_dropdown] Normalized teams %s -> %s, %s -> %s",
                    row["home_team_name"],
                    home_team,
                    row["away_team_name"],
                    away_team,
                )

                game_data = {
                    "id": row["id"],
                    "api_game_id": str(row["api_game_id"]),
                    "home_team": home_team,  # Use normalized name for display
                    "away_team": away_team,  # Use normalized name for display
                    "start_time": row["start_time"],
                    "status": row["status"],
                    "home_team_name": home_team,  # Store normalized name
                    "away_team_name": away_team,  # Store normalized name
                }
                dropdown_games.append(game_data)
                logger.info(
                    "[get_normalized_games_for_dropdown] Added game to dropdown: %s",
                    game_data,
                )
            except Exception as e:
                logger.error(
                    "[get_normalized_games_for_dropdown] Error processing game data for league_id=%s, sport=%s, league_name=%s: %s",
                    league_id,
                    sport,
                    league_name,
                    e,
                    exc_info=True,
                )
                continue
        logger.info(
            "[get_normalized_games_for_dropdown] Returning %d normalized games for dropdown (including manual entry)",
            len(dropdown_games),
        )
        return dropdown_games

    async def get_open_bets_by_guild(self, guild_id: int):
        """Fetch open bets for a guild."""
        logger.info("Fetching open bets for guild_id=%s", guild_id)
        query = """
            SELECT DISTINCT COALESCE(b.api_game_id, l.api_game_id) as api_game_id,
                   g.home_team_name, g.away_team_name, g.start_time, g.status,
                   g.score, g.id as game_id
            FROM bets b
            LEFT JOIN bet_legs l ON b.bet_type = 'parlay' AND l.bet_id = b.bet_serial
            JOIN api_games g ON COALESCE(b.api_game_id, l.api_game_id) = g.api_game_id
            WHERE b.guild_id = $1 AND b.confirmed = 1
            AND (b.bet_type = 'game_line' OR l.bet_type = 'game_line')
            AND g.status NOT IN ('finished', 'Match Finished', 'Final', 'Ended')
        """
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetch open bets: DB pool unavailable.")
            return []
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, guild_id)
            logger.info("Fetched %d open bets for guild_id=%s", len(rows), guild_id)
            return [dict(row) for row in rows]

    async def _get_or_create_game(self, api_game_id: str) -> int:
        row = await self.fetch_one("SELECT id FROM games WHERE id = $1", api_game_id)
        if row:
            return row["id"]

        src = await self.fetch_one(
            """
            SELECT sport, league_id, home_team_name, away_team_name,
                   start_time, status
            FROM api_games
            WHERE api_game_id = $1
            """,
            api_game_id,
        )
        if not src:
            raise ValueError(f"No api_games row for {api_game_id}")

        # Insert USING api_game_id as the PK
        insert_q = """
          INSERT INTO games (
            id, sport, league_id, home_team_name, away_team_name,
            start_time, status, created_at
          ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP
          )
        """
        await self.execute(
            insert_q,
            int(api_game_id),
            src["sport"],
            src["league_id"],
            src["home_team_name"],
            src["away_team_name"],
            src["start_time"],
            src["status"],
        )
        return int(api_game_id)

    @property
    def db(self):
        """Returns the PostgreSQL connection pool."""
        if self._pool is None:
            raise RuntimeError(
                "Database connection pool is not initialized. Call connect() first."
            )
        return self._pool

    async def get_next_bet_serial(self) -> Optional[int]:
        """Fetch the next bet_serial value for the bets table (PostgreSQL sequence)."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot get next bet serial: DB pool unavailable.")
            return None
        try:
            async with pool.acquire() as conn:
                # Get next value from bets table sequence
                row = await conn.fetchrow("SELECT nextval(pg_get_serial_sequence('bets', 'bet_serial')) AS next_bet_serial")
                if row and "next_bet_serial" in row:
                    return int(row["next_bet_serial"])
        except Exception as e:
            logger.error(f"Error fetching next bet serial: {e}", exc_info=True)
        return None

# Global database manager instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
