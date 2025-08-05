import logging
from datetime import datetime
from typing import Dict

import discord

logger = logging.getLogger(__name__)


class CommunityAnalyticsService:
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager

        # Achievement definitions
        self.achievements = {
            "reaction_master": {
                "name": "Reaction Master",
                "requirement": 100,
                "icon": "🎯",
                "description": "Reacted to 100+ bets",
            },
            "popular_predictor": {
                "name": "Popular Predictor",
                "requirement": 10,
                "icon": "👑",
                "description": "Had 10+ bets with high reaction counts",
            },
            "streak_supporter": {
                "name": "Streak Supporter",
                "requirement": 50,
                "icon": "🔥",
                "description": "Consistently supported community bets",
            },
            "community_cheerleader": {
                "name": "Community Cheerleader",
                "requirement": 200,
                "icon": "📣",
                "description": "Very active community supporter",
            },
            "helpful_member": {
                "name": "Helpful Member",
                "requirement": 25,
                "icon": "🤝",
                "description": "Helped other community members",
            },
            "event_participant": {
                "name": "Event Participant",
                "requirement": 5,
                "icon": "🎉",
                "description": "Participated in community events",
            },
            "discussion_starter": {
                "name": "Discussion Starter",
                "requirement": 20,
                "icon": "💬",
                "description": "Started engaging discussions",
            },
        }

    async def track_metric(self, guild_id: int, metric_type: str, value: float):
        """Track a community metric."""
        try:
            query = """
                INSERT INTO community_metrics (guild_id, metric_type, metric_value, recorded_at)
                VALUES ($1, $2, $3, $4)
            """
            await self.db_manager.execute(
                query, (guild_id, metric_type, value, datetime.utcnow())
            )
            logger.debug(f"Tracked metric {metric_type}: {value} for guild {guild_id}")
        except Exception as e:
            logger.error(f"Failed to track metric: {e}")

    async def get_community_health(self, guild_id: int, days: int = 7):
        """Get community health metrics."""
        try:
            query = """
                SELECT
                    metric_type,
                    AVG(metric_value) as avg_value,
                    MAX(metric_value) as max_value,
                    MIN(metric_value) as min_value,
                    COUNT(*) as data_points,
                    SUM(metric_value) as total_value
                FROM community_metrics
                WHERE guild_id = $1
                AND recorded_at >= DATE_SUB(NOW(), INTERVAL $2 DAY)
                GROUP BY metric_type
                ORDER BY avg_value DESC
            """
            return await self.db_manager.fetch_all(query, (guild_id, days))
        except Exception as e:
            logger.error(f"Failed to get community health: {e}")
            return []

    async def track_reaction_activity(
        self, guild_id: int, user_id: int, bet_serial: int, emoji: str
    ):
        """Track user reaction activity."""
        try:
            # Track individual reaction
            await self.track_metric(guild_id, "daily_reactions", 1)
            await self.track_metric(guild_id, f"reactions_{emoji}", 1)

            # Track user-specific metrics
            await self.track_user_metric(guild_id, user_id, "total_reactions", 1)
            await self.track_user_metric(guild_id, user_id, f"reactions_{emoji}", 1)

            # Check for achievements
            await self.check_reaction_achievements(guild_id, user_id)

        except Exception as e:
            logger.error(f"Failed to track reaction activity: {e}")

    async def track_user_metric(
        self, guild_id: int, user_id: int, metric_type: str, value: float
    ):
        """Track user-specific metrics."""
        try:
            query = """
                INSERT INTO user_metrics (guild_id, user_id, metric_type, metric_value, recorded_at)
                VALUES ($1, $2, $3, $4, $5)
                ON DUPLICATE KEY UPDATE
                metric_value = metric_value + VALUES(metric_value),
                recorded_at = VALUES(recorded_at)
            """
            await self.db_manager.execute(
                query, (guild_id, user_id, metric_type, value, datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Failed to track user metric: {e}")

    async def check_reaction_achievements(self, guild_id: int, user_id: int):
        """Check if user has earned reaction achievements."""
        try:
            # Count user's total reactions
            query = """
                SELECT COUNT(*) as reaction_count
                FROM bet_reactions br
                JOIN bets b ON br.bet_serial = b.bet_serial
                WHERE b.guild_id = $1 AND br.user_id = $2
            """
            result = await self.db_manager.fetch_one(query, (guild_id, user_id))
            reaction_count = result["reaction_count"] if result else 0

            # Check achievements
            achievements_to_check = {
                100: "reaction_master",
                50: "streak_supporter",
                200: "community_cheerleader",
            }

            for threshold, achievement in achievements_to_check.items():
                if reaction_count >= threshold:
                    await self.grant_achievement(guild_id, user_id, achievement)

        except Exception as e:
            logger.error(f"Failed to check reaction achievements: {e}")

    async def grant_achievement(
        self, guild_id: int, user_id: int, achievement_type: str
    ):
        """Grant an achievement to a user."""
        try:
            # Check if already earned
            query = """
                SELECT COUNT(*) as count
                FROM community_achievements
                WHERE guild_id = $1 AND user_id = $2 AND achievement_type = $3
            """
            result = await self.db_manager.fetch_one(
                query, (guild_id, user_id, achievement_type)
            )

            if result["count"] == 0:
                # Grant achievement
                achievement_info = self.achievements.get(achievement_type, {})
                achievement_name = achievement_info.get("name", achievement_type)

                insert_query = """
                    INSERT INTO community_achievements (guild_id, user_id, achievement_type, achievement_name, earned_at)
                    VALUES ($1, $2, $3, $4, $5)
                """
                await self.db_manager.execute(
                    insert_query,
                    (
                        guild_id,
                        user_id,
                        achievement_type,
                        achievement_name,
                        datetime.utcnow(),
                    ),
                )

                # Track achievement metric
                await self.track_metric(guild_id, "achievements_granted", 1)
                await self.track_user_metric(
                    guild_id, user_id, "achievements_earned", 1
                )

                logger.info(
                    f"Granted achievement {achievement_type} to user {user_id} in guild {guild_id}"
                )

                # Notify user about achievement (if possible)
                await self.notify_achievement(guild_id, user_id, achievement_info)

        except Exception as e:
            logger.error(f"Failed to grant achievement: {e}")

    async def notify_achievement(
        self, guild_id: int, user_id: int, achievement_info: Dict
    ):
        """Notify user about earning an achievement."""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return

            user = guild.get_member(user_id)
            if not user:
                return

            # Get main chat channel from guild settings
            guild_settings = await self.db_manager.fetch_one(
                "SELECT main_chat_channel_id FROM guild_settings WHERE guild_id = $1",
                (guild_id,),
            )

            channel = None
            if guild_settings and guild_settings.get("main_chat_channel_id"):
                # Use the configured main chat channel
                channel = self.bot.get_channel(guild_settings["main_chat_channel_id"])
                logger.info(
                    f"Using configured main chat channel {guild_settings['main_chat_channel_id']} for achievement notification"
                )

            if not channel:
                # Fallback: try to find channel by name "main-chat"
                channel = discord.utils.get(guild.channels, name="main-chat")
                if channel:
                    logger.info(
                        "Using 'main-chat' channel for achievement notification"
                    )

            if not channel:
                # Fallback: try to find channel by name "general-chat"
                channel = discord.utils.get(guild.channels, name="general-chat")
                if channel:
                    logger.info(
                        "Using 'general-chat' channel for achievement notification"
                    )

            if not channel:
                # Final fallback: use first text channel
                channel = discord.utils.get(
                    guild.channels, type=discord.ChannelType.text
                )
                if channel:
                    logger.info(
                        f"Using fallback text channel {channel.name} for achievement notification"
                    )

            if channel:
                embed = discord.Embed(
                    title=f"{achievement_info.get('icon', '🏆')} Achievement Unlocked!",
                    description=f"Congratulations {user.mention}! You've earned the **{achievement_info.get('name', 'Unknown')}** achievement!",
                    color=0xFFD700,
                    timestamp=datetime.utcnow(),
                )
                embed.add_field(
                    name="Description",
                    value=achievement_info.get("description", "Great job!"),
                    inline=False,
                )
                embed.set_footer(text="Keep up the great work!")
                embed.set_thumbnail(url=user.display_avatar.url)

                await channel.send(embed=embed)
                logger.info(
                    f"Sent achievement notification to channel {channel.name} for user {user_id}"
                )

            else:
                logger.warning(
                    f"Could not find any suitable channel for achievement notification in guild {guild_id}"
                )

        except Exception as e:
            logger.error(f"Failed to notify achievement: {e}")

    async def get_user_achievements(self, guild_id: int, user_id: int):
        """Get achievements for a specific user."""
        try:
            query = """
                SELECT achievement_type, achievement_name, earned_at
                FROM community_achievements
                WHERE guild_id = $1 AND user_id = $2
                ORDER BY earned_at DESC
            """
            return await self.db_manager.fetch_all(query, (guild_id, user_id))
        except Exception as e:
            logger.error(f"Failed to get user achievements: {e}")
            return []

    async def get_leaderboard(
        self, guild_id: int, category: str = "reactions", limit: int = 10
    ):
        """Get community leaderboard."""
        try:
            if category == "reactions":
                query = """
                    SELECT
                        br.user_id,
                        COUNT(*) as reaction_count,
                        COUNT(DISTINCT br.bet_serial) as bets_reacted_to
                    FROM bet_reactions br
                    JOIN bets b ON br.bet_serial = b.bet_serial
                    WHERE b.guild_id = $1
                    GROUP BY br.user_id
                    ORDER BY reaction_count DESC
                    LIMIT $2
                """
                results = await self.db_manager.fetch_all(query, (guild_id, limit))
                return [
                    {"user_id": row["user_id"], "value": row["reaction_count"]}
                    for row in results
                ]

            elif category == "achievements":
                query = """
                    SELECT
                        user_id,
                        COUNT(*) as achievement_count
                    FROM community_achievements
                    WHERE guild_id = $1
                    GROUP BY user_id
                    ORDER BY achievement_count DESC
                    LIMIT $2
                """
                results = await self.db_manager.fetch_all(query, (guild_id, limit))
                return [
                    {"user_id": row["user_id"], "value": row["achievement_count"]}
                    for row in results
                ]

            elif category == "helpful":
                query = """
                    SELECT
                        user_id,
                        SUM(metric_value) as helpful_score
                    FROM user_metrics
                    WHERE guild_id = $1
                    AND metric_type IN ('help_requests_answered', 'encouragements_given', 'thanks_received')
                    GROUP BY user_id
                    ORDER BY helpful_score DESC
                    LIMIT $2
                """
                results = await self.db_manager.fetch_all(query, (guild_id, limit))
                return [
                    {"user_id": row["user_id"], "value": row["helpful_score"]}
                    for row in results
                ]

            else:
                return []

        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            return []

    async def get_engagement_summary(self, guild_id: int, days: int = 7):
        """Get engagement summary for a guild."""
        try:
            # Get basic metrics
            health_metrics = await self.get_community_health(guild_id, days)

            # Get top users
            top_reactors = await self.get_leaderboard(guild_id, "reactions", 5)
            top_achievers = await self.get_leaderboard(guild_id, "achievements", 5)

            # Get recent achievements
            query = """
                SELECT user_id, achievement_name, earned_at
                FROM community_achievements
                WHERE guild_id = $1
                AND earned_at >= DATE_SUB(NOW(), INTERVAL $2 DAY)
                ORDER BY earned_at DESC
                LIMIT 10
            """
            recent_achievements = await self.db_manager.fetch_all(
                query, (guild_id, days)
            )

            return {
                "health_metrics": health_metrics,
                "top_reactors": top_reactors,
                "top_achievers": top_achievers,
                "recent_achievements": recent_achievements,
            }

        except Exception as e:
            logger.error(f"Failed to get engagement summary: {e}")
            return {}

    async def track_community_command(
        self, guild_id: int, user_id: int, command_name: str
    ):
        """Track usage of community commands."""
        try:
            await self.track_metric(guild_id, f"command_{command_name}", 1)
            await self.track_user_metric(
                guild_id, user_id, f"commands_{command_name}", 1
            )
            await self.track_user_metric(
                guild_id, user_id, "total_community_commands", 1
            )

            # Check for command-based achievements
            await self.check_command_achievements(guild_id, user_id, command_name)

        except Exception as e:
            logger.error(f"Failed to track community command: {e}")

    async def check_command_achievements(
        self, guild_id: int, user_id: int, command_name: str
    ):
        """Check for command-based achievements."""
        try:
            # Get user's command usage
            query = """
                SELECT SUM(metric_value) as total_commands
                FROM user_metrics
                WHERE guild_id = $1 AND user_id = $2 AND metric_type = 'total_community_commands'
            """
            result = await self.db_manager.fetch_one(query, (guild_id, user_id))
            total_commands = (
                result["total_commands"] if result and result["total_commands"] else 0
            )

            # Check for discussion starter achievement
            if command_name == "discuss" and total_commands >= 20:
                await self.grant_achievement(guild_id, user_id, "discussion_starter")

            # Check for helpful member achievement
            if (
                command_name in ["help_community", "encourage", "thanks"]
                and total_commands >= 25
            ):
                await self.grant_achievement(guild_id, user_id, "helpful_member")

        except Exception as e:
            logger.error(f"Failed to check command achievements: {e}")

    async def start(self):
        """Start the community analytics service."""
        logger.info("Starting Community Analytics Service")

    async def stop(self):
        """Stop the community analytics service."""
        logger.info("Stopping Community Analytics Service")

    async def get_comprehensive_community_stats(self, guild_id: int, days: int = 7):
        """Get comprehensive community statistics from real data."""
        try:
            stats = {}

            # Get total reactions from bet_reactions table (join with bets to get guild_id)
            reactions_query = """
                SELECT COUNT(*) as total_reactions
                FROM bet_reactions br
                JOIN bets b ON br.bet_serial = b.bet_serial
                WHERE b.guild_id = $1
                AND br.created_at >= DATE_SUB(NOW(), INTERVAL $2 DAY)
            """
            reactions_result = await self.db_manager.fetch_one(
                reactions_query, (guild_id, days)
            )
            stats["total_reactions"] = (
                reactions_result["total_reactions"] if reactions_result else 0
            )

            # Get total achievements earned
            achievements_query = """
                SELECT COUNT(*) as total_achievements
                FROM community_achievements
                WHERE guild_id = $1
                AND earned_at >= DATE_SUB(NOW(), INTERVAL $2 DAY)
            """
            achievements_result = await self.db_manager.fetch_one(
                achievements_query, (guild_id, days)
            )
            stats["total_achievements"] = (
                achievements_result["total_achievements"] if achievements_result else 0
            )

            # Get active users (users who have used community commands or reacted to bets)
            active_users_query = """
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM (
                    SELECT user_id FROM user_metrics
                    WHERE guild_id = $1
                    AND recorded_at >= DATE_SUB(NOW(), INTERVAL $2 DAY)
                    UNION
                    SELECT br.user_id FROM bet_reactions br
                    JOIN bets b ON br.bet_serial = b.bet_serial
                    WHERE b.guild_id = $3
                    AND br.created_at >= DATE_SUB(NOW(), INTERVAL $4 DAY)
                ) as active_users
            """
            active_users_result = await self.db_manager.fetch_one(
                active_users_query, (guild_id, days, guild_id, days)
            )
            stats["active_users"] = (
                active_users_result["active_users"] if active_users_result else 0
            )

            # Get community commands used
            commands_query = """
                SELECT SUM(metric_value) as community_commands
                FROM community_metrics
                WHERE guild_id = $1
                AND metric_type LIKE $2
                AND recorded_at >= DATE_SUB(NOW(), INTERVAL $3 DAY)
            """
            commands_result = await self.db_manager.fetch_one(
                commands_query, (guild_id, "command_%", days)
            )
            stats["community_commands"] = (
                int(commands_result["community_commands"])
                if commands_result and commands_result["community_commands"]
                else 0
            )

            # Events participated - set to 0 since community events are disabled
            stats["events_participated"] = 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get comprehensive community stats: {e}")
            return {
                "total_reactions": 0,
                "total_achievements": 0,
                "active_users": 0,
                "community_commands": 0,
                "events_participated": 0,
            }
