"""Voice channel management service for Discord bot."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands

from data.db_manager import DatabaseManager
from utils.enhanced_cache_manager import (
    enhanced_cache_get,
    enhanced_cache_set,
    enhanced_cache_delete,
    get_enhanced_cache_manager,
)
from utils.errors import VoiceServiceError

logger = logging.getLogger(__name__)

# Cache TTLs for voice service
VOICE_CACHE_TTLS = {
    "channel_status": 300,  # 5 minutes
    "user_activity": 600,  # 10 minutes
    "guild_settings": 3600,  # 1 hour
}


class VoiceService:
    """Service for managing voice channel activities and tracking."""

    def __init__(self, bot: commands.Bot, db_manager: DatabaseManager):
        self.bot = bot
        self.db_manager = db_manager
        self.cache = get_enhanced_cache_manager()
        self._check_task = None
        self._is_running = False

        # Voice service configuration
        self.config = {
            "check_interval": 300,  # 5 minutes
            "grace_period": 3600,  # 1 hour
            "min_activity_time": 300,  # 5 minutes
            "max_inactive_time": 1800,  # 30 minutes
        }

        logger.info("VoiceService initialized")

    async def start(self):
        """Start the voice service."""
        if self._is_running:
            logger.warning("VoiceService is already running")
            return

        self._is_running = True
        self._check_task = asyncio.create_task(self._periodic_check())
        logger.info("VoiceService started")

    async def stop(self):
        """Stop the voice service."""
        if not self._is_running:
            return

        self._is_running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("VoiceService stopped")

    async def _periodic_check(self):
        """Periodic voice channel activity check."""
        while self._is_running:
            try:
                await self.check_voice_activity()
                await asyncio.sleep(self.config["check_interval"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic voice check: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def check_voice_activity(self) -> Dict[str, Any]:
        """Check voice channel activity across all guilds."""
        try:
            activity_report = {
                "guilds_checked": 0,
                "active_channels": 0,
                "inactive_channels": 0,
                "users_tracked": 0,
                "errors": [],
            }

            for guild in self.bot.guilds:
                try:
                    guild_activity = await self._check_guild_voice_activity(guild)
                    activity_report["guilds_checked"] += 1
                    activity_report["active_channels"] += guild_activity.get(
                        "active_channels", 0
                    )
                    activity_report["inactive_channels"] += guild_activity.get(
                        "inactive_channels", 0
                    )
                    activity_report["users_tracked"] += guild_activity.get(
                        "users_tracked", 0
                    )
                except Exception as e:
                    activity_report["errors"].append(f"Guild {guild.id}: {e}")

            # Cache activity report
            await enhanced_cache_set(
                "voice_activity",
                "last_check",
                activity_report,
                ttl=VOICE_CACHE_TTLS["channel_status"],
            )

            logger.debug(f"Voice activity check completed: {activity_report}")
            return activity_report

        except Exception as e:
            logger.error(f"Error in check_voice_activity: {e}")
            raise VoiceServiceError(f"Failed to check voice activity: {e}")

    async def _check_guild_voice_activity(self, guild: discord.Guild) -> Dict[str, Any]:
        """Check voice activity for a specific guild."""
        try:
            guild_activity = {
                "guild_id": guild.id,
                "active_channels": 0,
                "inactive_channels": 0,
                "users_tracked": 0,
                "channels": [],
            }

            for channel in guild.voice_channels:
                try:
                    channel_activity = await self._check_channel_activity(channel)
                    guild_activity["channels"].append(channel_activity)

                    if channel_activity["is_active"]:
                        guild_activity["active_channels"] += 1
                    else:
                        guild_activity["inactive_channels"] += 1

                    guild_activity["users_tracked"] += len(channel_activity["users"])

                except Exception as e:
                    logger.error(f"Error checking channel {channel.id}: {e}")

            return guild_activity

        except Exception as e:
            logger.error(f"Error checking guild {guild.id} voice activity: {e}")
            return {"guild_id": guild.id, "error": str(e)}

    async def _check_channel_activity(
        self, channel: discord.VoiceChannel
    ) -> Dict[str, Any]:
        """Check activity for a specific voice channel."""
        try:
            current_time = datetime.now(timezone.utc)
            users_in_channel = []

            for member in channel.members:
                if not member.bot:
                    user_activity = {
                        "user_id": member.id,
                        "username": member.display_name,
                        "joined_at": current_time,
                        "is_active": True,
                    }
                    users_in_channel.append(user_activity)

                    # Track user activity in cache
                    await enhanced_cache_set(
                        "user_activity",
                        f"{member.id}_{channel.id}",
                        user_activity,
                        ttl=VOICE_CACHE_TTLS["user_activity"],
                    )

            # Determine if channel is active
            is_active = len(users_in_channel) > 0

            channel_activity = {
                "channel_id": channel.id,
                "channel_name": channel.name,
                "is_active": is_active,
                "user_count": len(users_in_channel),
                "users": users_in_channel,
                "checked_at": current_time.isoformat(),
            }

            return channel_activity

        except Exception as e:
            logger.error(f"Error checking channel {channel.id} activity: {e}")
            return {
                "channel_id": channel.id,
                "channel_name": channel.name,
                "is_active": False,
                "error": str(e),
            }

    async def get_user_voice_stats(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Get voice activity statistics for a user."""
        try:
            # Get user's voice activity from database
            voice_stats = await self.db_manager.fetch_one(
                """
                SELECT
                    COUNT(*) as total_sessions,
                    SUM(EXTRACT(EPOCH FROM (COALESCE(left_at, NOW()) - joined_at))/60) as total_minutes,
                    AVG(EXTRACT(EPOCH FROM (COALESCE(left_at, NOW()) - joined_at))/60) as avg_session_length,
                    MAX(joined_at) as last_joined
                FROM voice_activity
                WHERE user_id = $1 AND guild_id = $2
                """,
                user_id,
                guild_id,
            )

            if not voice_stats:
                return {
                    "total_sessions": 0,
                    "total_minutes": 0,
                    "avg_session_length": 0,
                    "last_joined": None,
                }

            return voice_stats

        except Exception as e:
            logger.error(f"Error getting voice stats for user {user_id}: {e}")
            return {}

    async def record_voice_activity(
        self, user_id: int, guild_id: int, channel_id: int, action: str
    ) -> bool:
        """Record voice activity for a user."""
        try:
            current_time = datetime.now(timezone.utc)

            if action == "join":
                await self.db_manager.execute(
                    """
                    INSERT INTO voice_activity
                    (user_id, guild_id, channel_id, joined_at, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    user_id,
                    guild_id,
                    channel_id,
                    current_time,
                    current_time,
                )
            elif action == "leave":
                await self.db_manager.execute(
                    """
                    UPDATE voice_activity
                    SET left_at = $1, updated_at = $2
                    WHERE user_id = $1 AND guild_id = $2 AND channel_id = $3 AND left_at IS NULL
                    """,
                    current_time,
                    current_time,
                    user_id,
                    guild_id,
                    channel_id,
                )

            return True

        except Exception as e:
            logger.error(f"Error recording voice activity: {e}")
            return False

    async def get_guild_voice_stats(self, guild_id: int) -> Dict[str, Any]:
        """Get voice activity statistics for a guild."""
        try:
            # Get guild voice statistics
            guild_stats = await self.db_manager.fetch_one(
                """
                SELECT
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) as total_sessions,
                    SUM(EXTRACT(EPOCH FROM (COALESCE(left_at, NOW()) - joined_at))/60) as total_minutes,
                    AVG(EXTRACT(EPOCH FROM (COALESCE(left_at, NOW()) - joined_at))/60) as avg_session_length
                FROM voice_activity
                WHERE guild_id = $1
                """,
                guild_id,
            )

            if not guild_stats:
                return {
                    "unique_users": 0,
                    "total_sessions": 0,
                    "total_minutes": 0,
                    "avg_session_length": 0,
                }

            return guild_stats

        except Exception as e:
            logger.error(f"Error getting guild voice stats: {e}")
            return {}

    async def get_active_voice_channels(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get currently active voice channels in a guild."""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return []

            active_channels = []
            for channel in guild.voice_channels:
                if len(channel.members) > 0:
                    channel_info = {
                        "channel_id": channel.id,
                        "channel_name": channel.name,
                        "user_count": len(channel.members),
                        "users": [
                            {
                                "user_id": member.id,
                                "username": member.display_name,
                                "is_bot": member.bot,
                            }
                            for member in channel.members
                        ],
                    }
                    active_channels.append(channel_info)

            return active_channels

        except Exception as e:
            logger.error(f"Error getting active voice channels: {e}")
            return []

    async def get_voice_activity_report(self) -> Dict[str, Any]:
        """Get comprehensive voice activity report."""
        try:
            cached_report = await enhanced_cache_get("voice_activity", "last_check")
            if cached_report:
                return cached_report

            return {
                "guilds_checked": 0,
                "active_channels": 0,
                "inactive_channels": 0,
                "users_tracked": 0,
                "errors": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting voice activity report: {e}")
            return {}

    async def clear_voice_cache(self) -> bool:
        """Clear voice-related cache."""
        try:
            await enhanced_cache_delete("voice_activity", "last_check")
            # Clear user activity cache for all users
            # This would require iterating through all cached keys, which is complex
            # For now, we'll just clear the main activity cache
            logger.info("Voice cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing voice cache: {e}")
            return False
