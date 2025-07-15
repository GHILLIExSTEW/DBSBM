import logging
from io import BytesIO

from discord import File, Interaction, app_commands
from discord.ext import commands

from utils.stats_image_generator import StatsImageGenerator

logger = logging.getLogger(__name__)


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.analytics_service = bot.analytics_service
        self.db_manager = bot.db_manager

    @app_commands.command(
        name="leaderboard",
        description="View top cappers leaderboard with flashy charts",
    )
    @app_commands.describe(
        metric="Sort by: net_units, win_rate, total_bets, roi",
        limit="Number of cappers to show (1-20)",
    )
    @app_commands.choices(
        metric=[
            app_commands.Choice(name="Net Units", value="net_units"),
            app_commands.Choice(name="Win Rate", value="win_rate"),
            app_commands.Choice(name="Total Bets", value="total_bets"),
            app_commands.Choice(name="ROI", value="roi"),
        ]
    )
    async def leaderboard(
        self, interaction: Interaction, metric: str = "net_units", limit: int = 10
    ):
        """Display a flashy leaderboard of top cappers."""
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)

            # Validate limit
            if limit < 1 or limit > 20:
                await interaction.followup.send(
                    "❌ Limit must be between 1 and 20.", ephemeral=True
                )
                return

            # Get leaderboard data
            cappers = await self.analytics_service.get_leaderboard(
                interaction.guild_id, metric=metric, limit=limit
            )

            if not cappers:
                await interaction.followup.send(
                    "❌ No capper data available for leaderboard.", ephemeral=True
                )
                return

            # Generate flashy leaderboard image
            image_generator = StatsImageGenerator()
            img = image_generator.generate_top_cappers_image(cappers)

            # Convert to Discord file
            img_buffer = BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            file = File(img_buffer, filename=f"leaderboard_{metric}.png")

            # Create title based on metric
            metric_names = {
                "net_units": "Net Units",
                "win_rate": "Win Rate",
                "total_bets": "Total Bets",
                "roi": "ROI",
            }

            title = (
                f"🏆 Top {limit} Cappers by {metric_names.get(metric, metric.title())}"
            )

            await interaction.followup.send(content=title, file=file, ephemeral=True)

        except Exception as e:
            logger.exception(f"Error in leaderboard command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while generating the leaderboard. Please try again.",
                ephemeral=True,
            )

    @app_commands.command(
        name="stats_comparison", description="Compare stats between multiple cappers"
    )
    async def stats_comparison(self, interaction: Interaction):
        """Compare stats between multiple cappers with charts."""
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)

            # Get all cappers in the guild
            cappers = await self.db_manager.fetch_all(
                "SELECT user_id, display_name FROM cappers WHERE guild_id = %s",
                (interaction.guild_id,),
            )

            if not cappers:
                await interaction.followup.send(
                    "❌ No cappers found in this guild.", ephemeral=True
                )
                return

            # Create comparison view (you can expand this with a selection interface)
            # For now, just show top 5 cappers comparison

            top_cappers = await self.analytics_service.get_leaderboard(
                interaction.guild_id, metric="net_units", limit=5
            )

            if not top_cappers:
                await interaction.followup.send(
                    "❌ No capper data available for comparison.", ephemeral=True
                )
                return

            # Generate comparison chart
            image_generator = StatsImageGenerator()
            img = image_generator.generate_top_cappers_image(top_cappers)

            # Convert to Discord file
            img_buffer = BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            file = File(img_buffer, filename="stats_comparison.png")

            await interaction.followup.send(
                content="📊 Top 5 Cappers Comparison", file=file, ephemeral=True
            )

        except Exception as e:
            logger.exception(f"Error in stats comparison command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while generating the comparison. Please try again.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
    logger.info("LeaderboardCog loaded")
