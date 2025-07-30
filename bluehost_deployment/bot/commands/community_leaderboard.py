import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class CommunityLeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="community_leaderboard", description="View community leaderboards"
    )
    async def community_leaderboard(
        self, interaction: discord.Interaction, category: str = "reactions"
    ):
        """View community leaderboards."""
        categories = {
            "reactions": "Most Active Reactors",
            "helpful": "Most Helpful Members",
            "positive": "Most Positive Members",
            "predictions": "Best Predictors",
            "achievements": "Most Achievements",
            "events": "Event Participants",
        }

        if category not in categories:
            await interaction.response.send_message(
                f"Available categories: {', '.join(categories.keys())}", ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            # Get leaderboard data
            leaderboard_data = await self.get_leaderboard_data(
                interaction.guild_id, category
            )

            if not leaderboard_data:
                embed = discord.Embed(
                    title=f"🏆 Community Leaderboard: {categories[category]}",
                    description="No data available yet. Start participating to see yourself on the leaderboard!",
                    color=0xFFD700,
                    timestamp=datetime.utcnow(),
                )
                embed.set_footer(text="Leaderboard data updates daily")
                await interaction.followup.send(embed=embed)
                return

            # Create leaderboard embed
            embed = discord.Embed(
                title=f"🏆 Community Leaderboard: {categories[category]}",
                description="Top community members based on engagement and participation",
                color=0xFFD700,
                timestamp=datetime.utcnow(),
            )

            # Add leaderboard entries
            for i, entry in enumerate(leaderboard_data[:10], 1):
                user_id = entry.get("user_id")
                user = interaction.guild.get_member(user_id) if user_id else None
                user_name = user.display_name if user else f"User {user_id}"
                user_avatar = user.display_avatar.url if user else None

                # Get the main metric value
                if category == "reactions":
                    value = entry.get("reaction_count", 0)
                    metric_text = f"{value} reactions"
                elif category == "achievements":
                    value = entry.get("achievement_count", 0)
                    metric_text = f"{value} achievements"
                elif category == "helpful":
                    value = entry.get("helpful_score", 0)
                    metric_text = f"{value} helpful actions"
                elif category == "predictions":
                    value = entry.get("win_rate", 0)
                    metric_text = f"{value:.1f}% win rate"
                else:
                    value = entry.get("score", 0)
                    metric_text = f"{value} points"

                # Add medal emoji for top 3
                medal = (
                    "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                )

                embed.add_field(
                    name=f"{medal} {user_name}", value=metric_text, inline=False
                )

                # Set thumbnail to first place user
                if i == 1 and user_avatar:
                    embed.set_thumbnail(url=user_avatar)

            embed.set_footer(
                text="Leaderboard data updates daily • Use /community_leaderboard <category> to view different categories"
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to get community leaderboard: {e}")
            await interaction.followup.send(
                "Sorry, there was an error loading the leaderboard. Please try again later.",
                ephemeral=True,
            )

    @app_commands.command(
        name="my_achievements", description="View your community achievements"
    )
    async def my_achievements(self, interaction: discord.Interaction):
        """View your community achievements."""
        await interaction.response.defer()

        try:
            # Get user achievements
            achievements = await self.get_user_achievements(
                interaction.guild_id, interaction.user.id
            )

            if not achievements:
                embed = discord.Embed(
                    title="🏆 Your Achievements",
                    description="You haven't earned any achievements yet. Keep participating in the community to unlock them!",
                    color=0xFFD700,
                    timestamp=datetime.utcnow(),
                )
                embed.add_field(
                    name="How to Earn Achievements",
                    value="• React to bets to earn reaction achievements\n• Use community commands to earn participation achievements\n• Help other members to earn helpful achievements",
                    inline=False,
                )
                embed.set_footer(text="Keep up the great work!")
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                await interaction.followup.send(embed=embed)
                return

            # Create achievements embed
            embed = discord.Embed(
                title="🏆 Your Achievements",
                description=f"Congratulations on your achievements, {interaction.user.display_name}!",
                color=0xFFD700,
                timestamp=datetime.utcnow(),
            )

            # Group achievements by type
            achievement_icons = {
                "reaction_master": "🎯",
                "popular_predictor": "👑",
                "streak_supporter": "🔥",
                "community_cheerleader": "📣",
                "helpful_member": "🤝",
                "event_participant": "🎉",
                "discussion_starter": "💬",
            }

            for achievement in achievements:
                achievement_type = achievement.get("achievement_type", "")
                achievement_name = achievement.get("achievement_name", "Unknown")
                earned_at = achievement.get("earned_at", "")

                icon = achievement_icons.get(achievement_type, "🏆")

                embed.add_field(
                    name=f"{icon} {achievement_name}",
                    value=f"Earned on {earned_at.strftime('%B %d, %Y') if earned_at else 'Unknown date'}",
                    inline=True,
                )

            embed.set_footer(text=f"Total Achievements: {len(achievements)}")
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to get user achievements: {e}")
            await interaction.followup.send(
                "Sorry, there was an error loading your achievements. Please try again later.",
                ephemeral=True,
            )

    @app_commands.command(
        name="community_stats", description="View community engagement statistics"
    )
    async def community_stats(self, interaction: discord.Interaction, days: int = 7):
        """View community engagement statistics."""
        if days < 1 or days > 30:
            await interaction.response.send_message(
                "Please specify a number of days between 1 and 30.", ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            # Get community stats
            stats = await self.get_community_stats(interaction.guild_id, days)

            embed = discord.Embed(
                title="📊 Community Engagement Statistics",
                description=f"Community activity over the last {days} days",
                color=0x4169E1,
                timestamp=datetime.utcnow(),
            )

            # Add stats fields
            if stats.get("total_reactions", 0) > 0:
                embed.add_field(
                    name="🔥 Total Reactions",
                    value=f"{stats.get('total_reactions', 0)} reactions",
                    inline=True,
                )

            if stats.get("total_achievements", 0) > 0:
                embed.add_field(
                    name="🏆 Achievements Earned",
                    value=f"{stats.get('total_achievements', 0)} achievements",
                    inline=True,
                )

            if stats.get("active_users", 0) > 0:
                embed.add_field(
                    name="👥 Active Users",
                    value=f"{stats.get('active_users', 0)} users",
                    inline=True,
                )

            if stats.get("community_commands", 0) > 0:
                embed.add_field(
                    name="💬 Community Commands",
                    value=f"{stats.get('community_commands', 0)} commands used",
                    inline=True,
                )

            if stats.get("events_participated", 0) > 0:
                embed.add_field(
                    name="🎉 Events Participated",
                    value=f"{stats.get('events_participated', 0)} events",
                    inline=True,
                )

            # Add engagement rate
            total_members = interaction.guild.member_count
            active_users = stats.get("active_users", 0)
            if total_members > 0:
                engagement_rate = (active_users / total_members) * 100
                embed.add_field(
                    name="📈 Engagement Rate",
                    value=f"{engagement_rate:.1f}% of members active",
                    inline=True,
                )

            embed.set_footer(text=f"Statistics for the last {days} days")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to get community stats: {e}")
            await interaction.followup.send(
                "Sorry, there was an error loading community statistics. Please try again later.",
                ephemeral=True,
            )

    async def get_leaderboard_data(self, guild_id: int, category: str):
        """Get leaderboard data for a specific category from real data."""
        try:
            if category == "reactions":
                # Get top users by reaction count (join with bets to get guild_id)
                query = """
                    SELECT br.user_id, COUNT(*) as reaction_count
                    FROM bet_reactions br
                    JOIN bets b ON br.bet_serial = b.bet_serial
                    WHERE b.guild_id = %s
                    GROUP BY br.user_id
                    ORDER BY reaction_count DESC
                    LIMIT 10
                """
                results = await self.bot.db_manager.fetch_all(query, (guild_id,))
                return [
                    {"user_id": row["user_id"], "reaction_count": row["reaction_count"]}
                    for row in results
                ]

            elif category == "achievements":
                # Get top users by achievement count
                query = """
                    SELECT user_id, COUNT(*) as achievement_count
                    FROM community_achievements
                    WHERE guild_id = %s
                    GROUP BY user_id
                    ORDER BY achievement_count DESC
                    LIMIT 10
                """
                results = await self.bot.db_manager.fetch_all(query, (guild_id,))
                return [
                    {
                        "user_id": row["user_id"],
                        "achievement_count": row["achievement_count"],
                    }
                    for row in results
                ]

            elif category == "helpful":
                # Get top users by helpful actions (encourage, thanks, help_community commands)
                query = """
                    SELECT user_id, SUM(metric_value) as helpful_score
                    FROM user_metrics
                    WHERE guild_id = %s
                    AND metric_type IN ('commands_encourage', 'commands_thanks', 'commands_help_community')
                    GROUP BY user_id
                    ORDER BY helpful_score DESC
                    LIMIT 10
                """
                results = await self.bot.db_manager.fetch_all(query, (guild_id,))
                return [
                    {
                        "user_id": row["user_id"],
                        "helpful_score": int(row["helpful_score"]),
                    }
                    for row in results
                ]

            else:
                return []

        except Exception as e:
            logger.error(f"Failed to get leaderboard data: {e}")
            return []

    async def get_user_achievements(self, guild_id: int, user_id: int):
        """Get achievements for a specific user from real data."""
        try:
            # Get user's achievements from the database
            query = """
                SELECT achievement_type, achievement_name, earned_at
                FROM community_achievements
                WHERE guild_id = %s AND user_id = %s
                ORDER BY earned_at DESC
            """
            results = await self.bot.db_manager.fetch_all(query, (guild_id, user_id))

            return [
                {
                    "achievement_type": row["achievement_type"],
                    "achievement_name": row["achievement_name"],
                    "earned_at": row["earned_at"],
                }
                for row in results
            ]

        except Exception as e:
            logger.error(f"Failed to get user achievements: {e}")
            return []

    async def get_community_stats(self, guild_id: int, days: int):
        """Get community statistics from real data."""
        try:
            # Get the community analytics service from the bot
            analytics_service = getattr(self.bot, "community_analytics_service", None)

            if analytics_service:
                # Use real data from the analytics service
                return await analytics_service.get_comprehensive_community_stats(
                    guild_id, days
                )
            else:
                # Fallback to basic database queries if service not available
                return await self._get_basic_community_stats(guild_id, days)

        except Exception as e:
            logger.error(f"Failed to get community stats: {e}")
            return {
                "total_reactions": 0,
                "total_achievements": 0,
                "active_users": 0,
                "community_commands": 0,
                "events_participated": 0,
            }

    async def _get_basic_community_stats(self, guild_id: int, days: int):
        """Fallback method to get basic community stats directly from database."""
        try:
            stats = {}

            # Get total reactions (join with bets to get guild_id)
            reactions_query = """
                SELECT COUNT(*) as total_reactions
                FROM bet_reactions br
                JOIN bets b ON br.bet_serial = b.bet_serial
                WHERE b.guild_id = %s
                AND br.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            reactions_result = await self.bot.db_manager.fetch_one(
                reactions_query, (guild_id, days)
            )
            stats["total_reactions"] = (
                reactions_result["total_reactions"] if reactions_result else 0
            )

            # Get total achievements
            achievements_query = """
                SELECT COUNT(*) as total_achievements
                FROM community_achievements
                WHERE guild_id = %s
                AND earned_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            achievements_result = await self.bot.db_manager.fetch_one(
                achievements_query, (guild_id, days)
            )
            stats["total_achievements"] = (
                achievements_result["total_achievements"] if achievements_result else 0
            )

            # Get active users
            active_users_query = """
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM (
                    SELECT user_id FROM user_metrics
                    WHERE guild_id = %s
                    AND recorded_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    UNION
                    SELECT br.user_id FROM bet_reactions br
                    JOIN bets b ON br.bet_serial = b.bet_serial
                    WHERE b.guild_id = %s
                    AND br.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ) as active_users
            """
            active_users_result = await self.bot.db_manager.fetch_one(
                active_users_query, (guild_id, days, guild_id, days)
            )
            stats["active_users"] = (
                active_users_result["active_users"] if active_users_result else 0
            )

            # Get community commands
            commands_query = """
                SELECT SUM(metric_value) as community_commands
                FROM community_metrics
                WHERE guild_id = %s
                AND metric_type LIKE %s
                AND recorded_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            commands_result = await self.bot.db_manager.fetch_one(
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
            logger.error(f"Failed to get basic community stats: {e}")
            return {
                "total_reactions": 0,
                "total_achievements": 0,
                "active_users": 0,
                "community_commands": 0,
                "events_participated": 0,
            }


async def setup(bot):
    await bot.add_cog(CommunityLeaderboardCog(bot))
