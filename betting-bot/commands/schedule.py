"""Schedule command for viewing upcoming games."""

import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from utils.schedule_image_generator import ScheduleImageGenerator

logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.debug(f"Loaded environment variables from: {dotenv_path}")

TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", "0"))


class ScheduleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.image_generator = ScheduleImageGenerator()

    @app_commands.command(
        name="schedule", description="View all games available to bet on"
    )
    async def schedule_command(self, interaction: discord.Interaction):
        """Display a schedule of all games available to bet on."""
        logger.info(
            f"Schedule command initiated by {interaction.user} in guild {interaction.guild_id}"
        )
        try:
            await interaction.response.defer(ephemeral=True)

            # Get user's timezone from database or default to UTC
            user_timezone = "UTC"  # Default timezone
            try:
                user_settings = await self.bot.db_manager.fetch_one(
                    "SELECT timezone FROM user_settings WHERE user_id = %s",
                    (interaction.user.id,),
                )
                if user_settings and user_settings.get("timezone"):
                    user_timezone = user_settings["timezone"]
            except Exception as e:
                logger.warning(f"Error fetching user timezone: {e}")

            # Build the query for upcoming games
            query = """
                SELECT
                    ag.api_game_id,
                    ag.home_team_name,
                    ag.away_team_name,
                    ag.start_time,
                    ag.league_id,
                    ag.league_name
                FROM api_games ag
                WHERE ag.start_time > NOW()
                ORDER BY ag.start_time ASC
                LIMIT 10
            """

            try:
                games = await self.bot.db_manager.fetch_all(query)
                logger.info(f"Found {len(games) if games else 0} upcoming games")
                if games:
                    logger.info(f"First game: {games[0]}")
            except Exception as e:
                logger.error(f"Error fetching games: {e}", exc_info=True)
                await interaction.followup.send(
                    "An error occurred while fetching the schedule.", ephemeral=True
                )
                return

            if not games:
                await interaction.followup.send(
                    "No upcoming games found.", ephemeral=True
                )
                return

            # Generate the schedule image
            image_path = await self.image_generator.generate_schedule_image(
                games, user_timezone
            )

            if image_path:
                await interaction.followup.send(
                    f"Found {len(games)} upcoming games.",
                    file=discord.File(image_path),
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "Failed to generate schedule image.", ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in schedule command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while fetching the schedule.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "An error occurred while fetching the schedule.", ephemeral=True
                )

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Handle errors specific to this cog's commands."""
        logger.error(f"Error in ScheduleCog command: {error}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred while processing the schedule command.",
                ephemeral=True,
            )
        else:
            try:
                await interaction.followup.send(
                    "An error occurred while processing the schedule command.",
                    ephemeral=True,
                )
            except discord.HTTPException:
                pass


async def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    await bot.add_cog(ScheduleCog(bot))
    logger.info("ScheduleCog loaded")
    # Register command to specific guild for testing
    try:
        if TEST_GUILD_ID:
            test_guild = discord.Object(id=TEST_GUILD_ID)
            bot.tree.copy_global_to(guild=test_guild)
            # await bot.tree.sync(guild=test_guild)  # DISABLED: Prevent rate limit
            logger.info(
                f"Successfully synced schedule command to test guild {TEST_GUILD_ID}"
            )
        else:
            logger.warning(
                "TEST_GUILD_ID not set, command will not be synced to test guild"
            )
    except Exception as e:
        logger.error(f"Failed to sync schedule command: {e}")
