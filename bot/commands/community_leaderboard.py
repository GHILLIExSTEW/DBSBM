import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime

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
        """Get leaderboard data for a specific category."""
        try:
            # This would integrate with the CommunityAnalyticsService
            # For now, return placeholder data
            if category == "reactions":
                return [
                    {"user_id": 123456789, "reaction_count": 150},
                    {"user_id": 987654321, "reaction_count": 120},
                    {"user_id": 456789123, "reaction_count": 95},
                ]
            elif category == "achievements":
                return [
                    {"user_id": 123456789, "achievement_count": 5},
                    {"user_id": 987654321, "achievement_count": 4},
                    {"user_id": 456789123, "achievement_count": 3},
                ]
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to get leaderboard data: {e}")
            return []

    async def get_user_achievements(self, guild_id: int, user_id: int):
        """Get achievements for a specific user."""
        try:
            # This would integrate with the CommunityAnalyticsService
            # For now, return placeholder data
            return [
                {
                    "achievement_type": "reaction_master",
                    "achievement_name": "Reaction Master",
                    "earned_at": datetime.now(),
                },
                {
                    "achievement_type": "helpful_member",
                    "achievement_name": "Helpful Member",
                    "earned_at": datetime.now(),
                },
            ]
        except Exception as e:
            logger.error(f"Failed to get user achievements: {e}")
            return []

    async def get_community_stats(self, guild_id: int, days: int):
        """Get community statistics."""
        try:
            # This would integrate with the CommunityAnalyticsService
            # For now, return placeholder data
            return {
                "total_reactions": 1250,
                "total_achievements": 45,
                "active_users": 25,
                "community_commands": 180,
                "events_participated": 12,
            }
        except Exception as e:
            logger.error(f"Failed to get community stats: {e}")
            return {}


async def setup(bot):
    await bot.add_cog(CommunityLeaderboardCog(bot))
