"""
Cache Warming Service for DBSBM System.
Implements intelligent cache warming strategies for critical data.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)


class WarmingStrategy(Enum):
    """Cache warming strategies."""

    ON_STARTUP = "on_startup"
    SCHEDULED = "scheduled"
    ON_DEMAND = "on_demand"
    INTELLIGENT = "intelligent"


@dataclass
class WarmingTask:
    """Cache warming task configuration."""

    name: str
    strategy: WarmingStrategy
    warming_function: Callable
    priority: int
    ttl: int
    is_active: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class CacheWarmingService:
    """Service for intelligent cache warming strategies."""

    def __init__(
        self, db_manager: DatabaseManager, cache_manager: EnhancedCacheManager
    ):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.warming_tasks: Dict[str, WarmingTask] = {}
        self.warming_stats = {
            "total_warming_runs": 0,
            "successful_warming_runs": 0,
            "failed_warming_runs": 0,
            "total_cache_hits": 0,
            "total_cache_misses": 0,
        }

    async def start(self):
        """Start the cache warming service."""
        logger.info("Starting CacheWarmingService...")

        # Register default warming tasks
        await self._register_default_tasks()

        # Start background warming tasks
        asyncio.create_task(self._scheduled_warming_worker())
        asyncio.create_task(self._intelligent_warming_worker())

        logger.info("CacheWarmingService started successfully")

    async def stop(self):
        """Stop the cache warming service."""
        logger.info("Stopping CacheWarmingService...")
        logger.info("CacheWarmingService stopped successfully")

    @time_operation("cache_warming_register_task")
    async def register_warming_task(self, task: WarmingTask) -> bool:
        """Register a new cache warming task."""
        try:
            self.warming_tasks[task.name] = task
            logger.info(f"Registered warming task: {task.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register warming task {task.name}: {e}")
            return False

    @time_operation("cache_warming_execute_task")
    async def execute_warming_task(self, task_name: str) -> bool:
        """Execute a specific warming task."""
        try:
            task = self.warming_tasks.get(task_name)
            if not task or not task.is_active:
                return False

            logger.info(f"Executing warming task: {task_name}")

            # Execute the warming function
            await task.warming_function()

            # Update task statistics
            task.last_run = datetime.utcnow()
            self.warming_stats["total_warming_runs"] += 1
            self.warming_stats["successful_warming_runs"] += 1

            logger.info(f"Successfully executed warming task: {task_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to execute warming task {task_name}: {e}")
            self.warming_stats["failed_warming_runs"] += 1
            return False

    @time_operation("cache_warming_startup")
    async def warm_cache_on_startup(self) -> Dict[str, Any]:
        """Warm cache on system startup."""
        try:
            logger.info("Starting cache warming on startup...")

            startup_tasks = [
                task
                for task in self.warming_tasks.values()
                if task.strategy == WarmingStrategy.ON_STARTUP and task.is_active
            ]

            # Sort by priority (higher priority first)
            startup_tasks.sort(key=lambda x: x.priority, reverse=True)

            results = {}
            for task in startup_tasks:
                success = await self.execute_warming_task(task.name)
                results[task.name] = success

            logger.info(f"Cache warming on startup completed: {len(results)} tasks")
            return results

        except Exception as e:
            logger.error(f"Failed to warm cache on startup: {e}")
            return {}

    async def _register_default_tasks(self):
        """Register default cache warming tasks."""
        try:
            # User data warming
            user_warming_task = WarmingTask(
                name="user_data_warming",
                strategy=WarmingStrategy.ON_STARTUP,
                warming_function=self._warm_user_data,
                priority=1,
                ttl=1800,
            )
            await self.register_warming_task(user_warming_task)

            # Game data warming
            game_warming_task = WarmingTask(
                name="game_data_warming",
                strategy=WarmingStrategy.ON_STARTUP,
                warming_function=self._warm_game_data,
                priority=2,
                ttl=900,
            )
            await self.register_warming_task(game_warming_task)

            # Team data warming
            team_warming_task = WarmingTask(
                name="team_data_warming",
                strategy=WarmingStrategy.ON_STARTUP,
                warming_function=self._warm_team_data,
                priority=3,
                ttl=7200,
            )
            await self.register_warming_task(team_warming_task)

            # League data warming
            league_warming_task = WarmingTask(
                name="league_data_warming",
                strategy=WarmingStrategy.ON_STARTUP,
                warming_function=self._warm_league_data,
                priority=4,
                ttl=14400,
            )
            await self.register_warming_task(league_warming_task)

            # Scheduled tasks
            scheduled_user_task = WarmingTask(
                name="scheduled_user_warming",
                strategy=WarmingStrategy.SCHEDULED,
                warming_function=self._warm_active_user_data,
                priority=5,
                ttl=1800,
            )
            await self.register_warming_task(scheduled_user_task)

            logger.info("Default warming tasks registered successfully")

        except Exception as e:
            logger.error(f"Failed to register default warming tasks: {e}")

    async def _warm_user_data(self):
        """Warm user data cache."""
        try:
            # Get active users
            users = await self.db_manager.fetch_all(
                "SELECT * FROM users WHERE is_active = 1 LIMIT 1000"
            )

            for user in users:
                cache_key = f"user:{user['user_id']}"
                await self.cache_manager.set("user_data", cache_key, user, ttl=1800)

            logger.info(f"Warmed user data for {len(users)} users")

        except Exception as e:
            logger.error(f"Failed to warm user data: {e}")

    async def _warm_game_data(self):
        """Warm game data cache."""
        try:
            # Get upcoming games
            games = await self.db_manager.fetch_all(
                """
                SELECT * FROM api_games
                WHERE start_time > NOW()
                AND start_time < DATE_ADD(NOW(), INTERVAL 7 DAY)
                LIMIT 500
                """
            )

            for game in games:
                cache_key = f"game:{game['api_game_id']}"
                await self.cache_manager.set("game_data", cache_key, game, ttl=900)

            logger.info(f"Warmed game data for {len(games)} games")

        except Exception as e:
            logger.error(f"Failed to warm game data: {e}")

    async def _warm_team_data(self):
        """Warm team data cache."""
        try:
            # Get all teams
            teams = await self.db_manager.fetch_all(
                "SELECT * FROM teams WHERE is_active = 1"
            )

            for team in teams:
                cache_key = f"team:{team['team_id']}"
                await self.cache_manager.set("team_data", cache_key, team, ttl=7200)

            logger.info(f"Warmed team data for {len(teams)} teams")

        except Exception as e:
            logger.error(f"Failed to warm team data: {e}")

    async def _warm_league_data(self):
        """Warm league data cache."""
        try:
            # Get all leagues
            leagues = await self.db_manager.fetch_all(
                "SELECT * FROM leagues WHERE is_active = 1"
            )

            for league in leagues:
                cache_key = f"league:{league['league_id']}"
                await self.cache_manager.set(
                    "league_data", cache_key, league, ttl=14400
                )

            logger.info(f"Warmed league data for {len(leagues)} leagues")

        except Exception as e:
            logger.error(f"Failed to warm league data: {e}")

    async def _warm_active_user_data(self):
        """Warm data for active users."""
        try:
            # Get users active in last 24 hours
            active_users = await self.db_manager.fetch_all(
                """
                SELECT DISTINCT u.* FROM users u
                JOIN bets b ON u.user_id = b.user_id
                WHERE b.created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                LIMIT 500
                """
            )

            for user in active_users:
                cache_key = f"active_user:{user['user_id']}"
                await self.cache_manager.set("user_data", cache_key, user, ttl=1800)

            logger.info(f"Warmed active user data for {len(active_users)} users")

        except Exception as e:
            logger.error(f"Failed to warm active user data: {e}")

    async def _scheduled_warming_worker(self):
        """Background worker for scheduled warming tasks."""
        while True:
            try:
                scheduled_tasks = [
                    task
                    for task in self.warming_tasks.values()
                    if task.strategy == WarmingStrategy.SCHEDULED and task.is_active
                ]

                for task in scheduled_tasks:
                    if task.next_run and datetime.utcnow() >= task.next_run:
                        await self.execute_warming_task(task.name)
                        # Schedule next run (every hour for scheduled tasks)
                        task.next_run = datetime.utcnow() + timedelta(hours=1)

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in scheduled warming worker: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error

    async def _intelligent_warming_worker(self):
        """Background worker for intelligent warming based on usage patterns."""
        while True:
            try:
                # Analyze cache hit patterns and warm frequently accessed data
                cache_stats = await self.cache_manager.get_stats()

                # If cache miss rate is high, trigger additional warming
                if cache_stats.get("misses", 0) > cache_stats.get("hits", 0) * 0.3:
                    logger.info(
                        "High cache miss rate detected, triggering intelligent warming"
                    )
                    await self._warm_frequently_accessed_data()

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Error in intelligent warming worker: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _warm_frequently_accessed_data(self):
        """Warm data that is frequently accessed."""
        try:
            # Get frequently accessed data based on recent activity
            frequent_data = await self.db_manager.fetch_all(
                """
                SELECT
                    'user' as data_type,
                    user_id as id,
                    COUNT(*) as access_count
                FROM bets
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
                GROUP BY user_id
                ORDER BY access_count DESC
                LIMIT 100
                """
            )

            for item in frequent_data:
                if item["data_type"] == "user":
                    user_data = await self.db_manager.fetch_one(
                        "SELECT * FROM users WHERE user_id = %s", (item["id"],)
                    )
                    if user_data:
                        cache_key = f"frequent_user:{item['id']}"
                        await self.cache_manager.set(
                            "user_data", cache_key, user_data, ttl=900
                        )

            logger.info(
                f"Warmed frequently accessed data for {len(frequent_data)} items"
            )

        except Exception as e:
            logger.error(f"Failed to warm frequently accessed data: {e}")

    async def get_warming_stats(self) -> Dict[str, Any]:
        """Get cache warming statistics."""
        return {
            **self.warming_stats,
            "active_tasks": len(
                [t for t in self.warming_tasks.values() if t.is_active]
            ),
            "total_tasks": len(self.warming_tasks),
            "last_warming_run": max(
                [t.last_run for t in self.warming_tasks.values() if t.last_run],
                default=None,
            ),
        }

    async def clear_warming_cache(self):
        """Clear all warming-related cache."""
        try:
            await self.cache_manager.clear_prefix("user_data")
            await self.cache_manager.clear_prefix("game_data")
            await self.cache_manager.clear_prefix("team_data")
            await self.cache_manager.clear_prefix("league_data")
            logger.info("Warming cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing warming cache: {e}")
