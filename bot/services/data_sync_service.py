"""Service for synchronizing external data with the database."""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from dateutil import parser
from dotenv import load_dotenv

from bot.config.leagues import LEAGUE_CONFIG

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY not found in .env file")

EDT = ZoneInfo("America/New_York")


def iso_to_mysql_datetime(iso_str):
    """Convert ISO 8601 string to MySQL DATETIME string (ETC)."""
    if not iso_str:
        return None
    dt = parser.isoparse(iso_str)
    dt_etc = dt.astimezone(EDT).replace(tzinfo=None)
    return dt_etc.strftime("%Y-%m-%d %H:%M:%S")


def normalize_sport_name(sport: str) -> str:
    """Normalize sport name for consistent matching."""
    sport = sport.lower().replace("-", "").replace(" ", "")
    if sport in ["icehockey", "hockey"]:
        return "icehockey"
    if sport in ["americanfootball", "football"]:
        return "americanfootball"
    return sport


def safe_get(obj, *keys, default=""):
    """Safely access nested dictionary keys, returning default if any key is missing or invalid."""
    current = obj
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


try:
    from bot.config.api_settings import API_ENABLED
    from bot.data.cache_manager import CacheManager
except ImportError:
    from bot.config.api_settings import API_ENABLED
    from bot.data.cache_manager import CacheManager


logger = logging.getLogger(__name__)


class DataSyncService:
    def __init__(self, game_service, db_manager):
        self.game_service = game_service
        self.db = db_manager
        self.cache = CacheManager()
        self._sync_task: Optional[asyncio.Task] = None
        self.running = False
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 1.1

        if not API_KEY:
            raise ValueError("API_KEY not found in .env file")

    async def start(self):
        """Start the data sync service without daily sync."""
        if not API_ENABLED:
            logger.warning("API is disabled. DataSyncService will not run.")
            return
        if not self.running:
            if hasattr(self.cache, "connect"):
                await self.cache.connect()
            self.running = True
            logger.info(
                "Data sync service started, relying on fetch_and_cache.py for fetches."
            )

    async def stop(self):
        """Stop the data sync service background task."""
        self.running = False
        logger.info("Stopping DataSyncService...")
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await asyncio.wait_for(self._sync_task, timeout=5.0)
            except asyncio.CancelledError:
                logger.info("Data sync task cancelled.")
            except asyncio.TimeoutError:
                logger.warning("Data sync task did not cancel within timeout.")
            except Exception as e:
                logger.error(f"Error awaiting data sync task cancellation: {e}")
            finally:
                self._sync_task = None

        if hasattr(self.cache, "close"):
            await self.cache.close()
        logger.info("Data sync service stopped.")

    async def _save_games(
        self, games: List[Dict], sport: str, league: str, league_id: str
    ) -> int:
        """Save games to database and return count of saved games."""
        saved_count = 0
        for game in games:
            if not isinstance(game, dict):
                self.logger.error(f"Skipping non-dict game object: {json.dumps(game)}")
                continue
            try:
                teams = safe_get(game, "teams")
                if not isinstance(teams, dict):
                    self.logger.error(
                        f"Skipping game with invalid 'teams' field: {json.dumps(game)}"
                    )
                    continue
                home_team = safe_get(teams, "home")
                away_team = safe_get(teams, "away")
                if not (isinstance(home_team, dict) and isinstance(away_team, dict)):
                    self.logger.error(
                        f"Skipping game with invalid 'home' or 'away' team: {json.dumps(game)}"
                    )
                    continue
                if sport.lower() in ["football", "soccer"]:
                    fixture = safe_get(game, "fixture", default={})
                    league_info = safe_get(game, "league", default={})
                    score = safe_get(game, "score", default={})
                    game_data = {
                        "id": str(
                            safe_get(game, "id", default=safe_get(fixture, "id"))
                        ),
                        "sport": sport,
                        "league_id": league_id,
                        "league_name": safe_get(league_info, "name", default=league),
                        "home_team_id": str(safe_get(home_team, "id")),
                        "away_team_id": str(safe_get(away_team, "id")),
                        "home_team_name": safe_get(home_team, "name"),
                        "away_team_name": safe_get(away_team, "name"),
                        "start_time": iso_to_mysql_datetime(safe_get(fixture, "date")),
                        "status": safe_get(
                            fixture, "status", "long", default="Scheduled"
                        ),
                        "score": json.dumps(score),
                        "venue": safe_get(fixture, "venue", "name"),
                        "referee": safe_get(fixture, "referee"),
                        "raw_json": json.dumps(game),
                        "fetched_at": datetime.now(timezone.utc).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                elif sport.lower() in ["baseball", "mlb"]:
                    game_data = {
                        "id": str(safe_get(game, "id")),
                        "sport": sport,
                        "league_id": league_id,
                        "league_name": LEAGUE_CONFIG.get(league, {}).get(
                            "name", league
                        ),
                        "home_team_id": str(safe_get(home_team, "id")),
                        "away_team_id": str(safe_get(away_team, "id")),
                        "home_team_name": safe_get(home_team, "name"),
                        "away_team_name": safe_get(away_team, "name"),
                        "start_time": iso_to_mysql_datetime(safe_get(game, "date")),
                        "status": safe_get(game, "status", "long", default="Scheduled"),
                        "score": json.dumps(
                            {
                                "home": safe_get(
                                    game, "scores", "home", "total", default=0
                                ),
                                "away": safe_get(
                                    game, "scores", "away", "total", default=0
                                ),
                            }
                        ),
                        "venue": safe_get(game, "venue", "name"),
                        "referee": None,
                        "raw_json": json.dumps(game),
                        "fetched_at": datetime.now(timezone.utc).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                else:
                    game_data = {
                        "id": str(safe_get(game, "id")),
                        "sport": sport,
                        "league_id": league_id,
                        "league_name": LEAGUE_CONFIG.get(league, {}).get(
                            "name", league
                        ),
                        "home_team_id": str(safe_get(home_team, "id")),
                        "away_team_id": str(safe_get(away_team, "id")),
                        "home_team_name": safe_get(home_team, "name"),
                        "away_team_name": safe_get(away_team, "name"),
                        "start_time": iso_to_mysql_datetime(safe_get(game, "date")),
                        "status": safe_get(game, "status", "long", default="Scheduled"),
                        "score": json.dumps(
                            {
                                "home": safe_get(
                                    game, "scores", "home", "total", default=0
                                ),
                                "away": safe_get(
                                    game, "scores", "away", "total", default=0
                                ),
                            }
                        ),
                        "venue": safe_get(game, "venue", "name"),
                        "referee": safe_get(game, "referee"),
                        "raw_json": json.dumps(game),
                        "fetched_at": datetime.now(timezone.utc).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                if not game_data["id"] or not game_data["start_time"]:
                    self.logger.error(
                        f"Skipping game with missing id or start_time: {json.dumps(game)}"
                    )
                    continue
                if await self.db.upsert_api_game(game_data):
                    saved_count += 1
            except Exception as e:
                self.logger.error(
                    f"Error saving game for {sport}/{league}: {str(e)}. Game data: {json.dumps(game)}"
                )
                continue
        return saved_count

    async def _fetch_active_bets(self, live_game_ids: List[str]) -> List[Dict]:
        """Fetch active bets for live games."""
        try:
            query = """
                SELECT b.*, g.start_time
                FROM bets b
                JOIN api_games g ON b.game_id = g.id
                WHERE b.status = 'pending'
                AND g.id IN %s
                AND g.start_time <= NOW()
                AND g.status NOT IN ('Match Finished', 'Finished', 'FT', 'Ended')
            """
            return await self.db.fetch_all(query, (tuple(live_game_ids),))
        except Exception as e:
            self.logger.error(f"Error fetching active bets: {e}")
            return []
