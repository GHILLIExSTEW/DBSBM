"""Data synchronization service for managing game and team data."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from bot.services.game_service import GameService
from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import enhanced_cache_get, enhanced_cache_set, enhanced_cache_delete, get_enhanced_cache_manager
from bot.utils.errors import DataSyncError

logger = logging.getLogger(__name__)

# Cache TTLs for different data types
CACHE_TTLS = {
    "game_data": 900,  # 15 minutes
    "team_data": 7200,  # 2 hours
    "league_data": 14400,  # 4 hours
    "sync_status": 300,  # 5 minutes
}


class DataSyncService:
    """Service for synchronizing game and team data with external APIs."""

    def __init__(self, game_service: GameService, db_manager: DatabaseManager):
        self.game_service = game_service  # Can be None initially
        self.db_manager = db_manager
        self.cache = get_enhanced_cache_manager()
        self._sync_task = None
        self._is_running = False

        # Sync configuration
        self.config = {
            'sync_interval': 300,  # 5 minutes
            'max_games_per_sync': 100,
            'retry_attempts': 3,
            'retry_delay': 30,  # seconds
            'batch_size': 50,
        }

        logger.info("DataSyncService initialized")

    async def start(self):
        """Start the data sync service."""
        if self._is_running:
            logger.warning("DataSyncService is already running")
            return

        self._is_running = True
        self._sync_task = asyncio.create_task(self._periodic_sync())
        logger.info("DataSyncService started")

    async def stop(self):
        """Stop the data sync service."""
        if not self._is_running:
            return

        self._is_running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("DataSyncService stopped")

    async def _periodic_sync(self):
        """Periodic data synchronization task."""
        while self._is_running:
            try:
                await self.sync_all_data()
                await asyncio.sleep(self.config['sync_interval'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
                await asyncio.sleep(self.config['retry_delay'])

    async def sync_all_data(self) -> Dict[str, Any]:
        """Synchronize all data types."""
        try:
            sync_results = {
                'games_synced': 0,
                'teams_synced': 0,
                'leagues_synced': 0,
                'errors': [],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Sync games
            try:
                games_synced = await self.sync_games()
                sync_results['games_synced'] = games_synced
            except Exception as e:
                sync_results['errors'].append(f"Game sync error: {e}")

            # Sync teams
            try:
                teams_synced = await self.sync_teams()
                sync_results['teams_synced'] = teams_synced
            except Exception as e:
                sync_results['errors'].append(f"Team sync error: {e}")

            # Sync leagues
            try:
                leagues_synced = await self.sync_leagues()
                sync_results['leagues_synced'] = leagues_synced
            except Exception as e:
                sync_results['errors'].append(f"League sync error: {e}")

            # Cache sync results
            await enhanced_cache_set("sync_status", "last_sync", sync_results, ttl=CACHE_TTLS['sync_status'])

            logger.info(f"Data sync completed: {sync_results}")
            return sync_results

        except Exception as e:
            logger.error(f"Error in sync_all_data: {e}")
            raise DataSyncError(f"Failed to sync data: {e}")

    async def sync_games(self) -> int:
        """Synchronize game data from external APIs."""
        try:
            # Get upcoming games from database instead of API
            # The games are already being synced by other services
            query = """
                SELECT id, api_game_id, sport, league_id, league_name,
                       home_team_name, away_team_name, start_time, status, score
                FROM api_games
                WHERE start_time > NOW()
                AND start_time < DATE_ADD(NOW(), INTERVAL 72 HOUR)
                ORDER BY start_time ASC
                LIMIT %s
            """

            upcoming_games = await self.db_manager.fetch_all(query, (self.config['max_games_per_sync'],))

            if not upcoming_games:
                logger.info("No upcoming games to sync")
                return 0

            synced_count = len(upcoming_games)
            logger.info(f"Found {synced_count} upcoming games in database")

            # Clear game cache after sync
            await enhanced_cache_delete("game_data", "upcoming_games")

            logger.info(f"Synced {synced_count} games")
            return synced_count

        except Exception as e:
            logger.error(f"Error in sync_games: {e}")
            raise DataSyncError(f"Failed to sync games: {e}")

    async def sync_teams(self) -> int:
        """Synchronize team data from external APIs."""
        try:
            # Get teams from database instead of API
            # Teams are already being synced by other services
            query = """
                SELECT DISTINCT home_team_name as team_name, sport, league_id
                FROM api_games
                WHERE home_team_name IS NOT NULL
                UNION
                SELECT DISTINCT away_team_name as team_name, sport, league_id
                FROM api_games
                WHERE away_team_name IS NOT NULL
                ORDER BY team_name
                LIMIT %s
            """

            teams = await self.db_manager.fetch_all(query, (self.config.get('max_teams_per_sync', 100),))

            if not teams:
                logger.info("No teams to sync")
                return 0

            synced_count = len(teams)
            logger.info(f"Found {synced_count} teams in database")

            # Clear team cache after sync
            await enhanced_cache_delete("team_data", "all_teams")

            logger.info(f"Synced {synced_count} teams")
            return synced_count

        except Exception as e:
            logger.error(f"Error in sync_teams: {e}")
            raise DataSyncError(f"Failed to sync teams: {e}")

    async def sync_leagues(self) -> int:
        """Synchronize league data from external APIs."""
        try:
            # Get leagues from database instead of API
            # Leagues are already being synced by other services
            query = """
                SELECT DISTINCT sport, league_id, league_name
                FROM api_games
                WHERE sport IS NOT NULL AND league_id IS NOT NULL
                ORDER BY sport, league_name
                LIMIT %s
            """

            leagues = await self.db_manager.fetch_all(query, (self.config.get('max_leagues_per_sync', 50),))

            if not leagues:
                logger.info("No leagues to sync")
                return 0

            synced_count = len(leagues)
            logger.info(f"Found {synced_count} leagues in database")

            # Clear league cache after sync
            await enhanced_cache_delete("league_data", "all_leagues")

            logger.info(f"Synced {synced_count} leagues")
            return synced_count

        except Exception as e:
            logger.error(f"Error in sync_leagues: {e}")
            raise DataSyncError(f"Failed to sync leagues: {e}")

    async def _store_game_data(self, game_data: Dict[str, Any]) -> bool:
        """Store game data in the database."""
        try:
            # Check if game already exists
            existing_game = await self.db_manager.fetch_one(
                "SELECT id FROM api_games WHERE game_id = %s",
                game_data.get('id')
            )

            if existing_game:
                # Update existing game
                await self.db_manager.execute(
                    """
                    UPDATE api_games
                    SET home_team = %s, away_team = %s, game_time = %s,
                        league = %s, sport = %s, status = %s, updated_at = UTC_TIMESTAMP()
                    WHERE game_id = %s
                    """,
                    game_data.get('home_team'),
                    game_data.get('away_team'),
                    game_data.get('game_time'),
                    game_data.get('league'),
                    game_data.get('sport'),
                    game_data.get('status'),
                    game_data.get('id')
                )
            else:
                # Insert new game
                await self.db_manager.execute(
                    """
                    INSERT INTO api_games
                    (game_id, home_team, away_team, game_time, league, sport, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, UTC_TIMESTAMP(), UTC_TIMESTAMP())
                    """,
                    game_data.get('id'),
                    game_data.get('home_team'),
                    game_data.get('away_team'),
                    game_data.get('game_time'),
                    game_data.get('league'),
                    game_data.get('sport'),
                    game_data.get('status')
                )

            return True

        except Exception as e:
            logger.error(f"Error storing game data: {e}")
            return False

    async def _store_team_data(self, team_data: Dict[str, Any]) -> bool:
        """Store team data in the database."""
        try:
            # Check if team already exists
            existing_team = await self.db_manager.fetch_one(
                "SELECT id FROM teams WHERE team_id = %s",
                team_data.get('id')
            )

            if existing_team:
                # Update existing team
                await self.db_manager.execute(
                    """
                    UPDATE teams
                    SET name = %s, league = %s, sport = %s, updated_at = UTC_TIMESTAMP()
                    WHERE team_id = %s
                    """,
                    team_data.get('name'),
                    team_data.get('league'),
                    team_data.get('sport'),
                    team_data.get('id')
                )
            else:
                # Insert new team
                await self.db_manager.execute(
                    """
                    INSERT INTO teams
                    (team_id, name, league, sport, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, UTC_TIMESTAMP(), UTC_TIMESTAMP())
                    """,
                    team_data.get('id'),
                    team_data.get('name'),
                    team_data.get('league'),
                    team_data.get('sport')
                )

            return True

        except Exception as e:
            logger.error(f"Error storing team data: {e}")
            return False

    async def _store_league_data(self, league_data: Dict[str, Any]) -> bool:
        """Store league data in the database."""
        try:
            # Check if league already exists
            existing_league = await self.db_manager.fetch_one(
                "SELECT id FROM leagues WHERE league_id = %s",
                league_data.get('id')
            )

            if existing_league:
                # Update existing league
                await self.db_manager.execute(
                    """
                    UPDATE leagues
                    SET name = %s, sport = %s, country = %s, updated_at = UTC_TIMESTAMP()
                    WHERE league_id = %s
                    """,
                    league_data.get('name'),
                    league_data.get('sport'),
                    league_data.get('country'),
                    league_data.get('id')
                )
            else:
                # Insert new league
                await self.db_manager.execute(
                    """
                    INSERT INTO leagues
                    (league_id, name, sport, country, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, UTC_TIMESTAMP(), UTC_TIMESTAMP())
                    """,
                    league_data.get('id'),
                    league_data.get('name'),
                    league_data.get('sport'),
                    league_data.get('country')
                )

            return True

        except Exception as e:
            logger.error(f"Error storing league data: {e}")
            return False

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get the current sync status."""
        try:
            cached_status = await enhanced_cache_get("sync_status", "last_sync")
            if cached_status:
                return cached_status

            return {
                'games_synced': 0,
                'teams_synced': 0,
                'leagues_synced': 0,
                'errors': [],
                'timestamp': None
            }

        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {}

    async def force_sync(self) -> Dict[str, Any]:
        """Force an immediate data sync."""
        try:
            logger.info("Forcing immediate data sync")
            return await self.sync_all_data()
        except Exception as e:
            logger.error(f"Error in force sync: {e}")
            raise DataSyncError(f"Failed to force sync: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for data sync."""
        try:
            return await self.cache.get_stats()
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    async def clear_sync_cache(self) -> bool:
        """Clear all sync-related cache."""
        try:
            await enhanced_cache_delete("sync_status", "last_sync")
            await enhanced_cache_delete("game_data", "upcoming_games")
            await enhanced_cache_delete("team_data", "all_teams")
            await enhanced_cache_delete("league_data", "all_leagues")
            logger.info("Sync cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing sync cache: {e}")
            return False
