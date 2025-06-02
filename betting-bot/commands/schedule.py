"""Schedule command for viewing upcoming games."""

import logging
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv

from utils.schedule_image_generator import ScheduleImageGenerator

logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.debug(f"Loaded environment variables from: {dotenv_path}")

TEST_GUILD_ID = int(os.getenv('TEST_GUILD_ID', '0'))

class ScheduleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.image_generator = ScheduleImageGenerator()

    @app_commands.command(
        name="schedule",
        description="View all games available to bet on"
    )
    async def schedule_command(self, interaction: discord.Interaction):
        """Display a schedule of all games available to bet on."""
        try:
            await interaction.response.defer(ephemeral=True)

            # Check if guild is paid
            guild_settings = await self.bot.db_manager.fetch_one(
                """
                SELECT subscription_level 
                FROM guild_settings 
                WHERE guild_id = %s
                """,
                interaction.guild_id
            )

            if not guild_settings or guild_settings['subscription_level'] != 'premium':
                await interaction.followup.send(
                    "❌ This command is only available in premium guilds. Please contact your server administrator to upgrade.",
                    ephemeral=True
                )
                return

            # Get user's timezone from their locale or default to UTC
            user_timezone = interaction.locale or 'UTC'
            if user_timezone not in pytz.all_timezones:
                user_timezone = 'UTC'

            # Query all games from the database
            query = """
                SELECT 
                    api_game_id,
                    sport,
                    league_id,
                    league_name,
                    home_team_name,
                    away_team_name,
                    start_time,
                    status
                FROM api_games
                WHERE DATE(start_time) = CURDATE()
                AND status = 'Not Started'
                ORDER BY start_time ASC
            """
            
            logger.info("Fetching upcoming games...")
            try:
                # Only run the main query
                games = await self.bot.db_manager.fetch_all(query)
                logger.info(f"Found {len(games) if games else 0} upcoming games")
                if games:
                    logger.info(f"First game: {games[0]}")
            except Exception as e:
                logger.error(f"Error fetching games: {e}", exc_info=True)
                await interaction.followup.send(
                    "An error occurred while fetching the schedule.",
                    ephemeral=True
                )
                return
            
            if not games:
                await interaction.followup.send(
                    "No upcoming games found.", 
                    ephemeral=True
                )
                return

            # Generate the schedule image
            image_path = await self.image_generator.generate_schedule_image(
                games, 
                user_timezone
            )

            if image_path:
                await interaction.followup.send(
                    f"Found {len(games)} upcoming games.",
                    file=discord.File(image_path),
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "Failed to generate schedule image.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in schedule command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while fetching the schedule.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "An error occurred while fetching the schedule.",
                    ephemeral=True
                )

async def setup(bot: commands.Bot):
    cog = ScheduleCog(bot)
    await bot.add_cog(cog)
    logger.info("ScheduleCog loaded")
    # Register command to specific guild for testing
    try:
        if TEST_GUILD_ID:
            test_guild = discord.Object(id=TEST_GUILD_ID)
            bot.tree.copy_global_to(guild=test_guild)
            await bot.tree.sync(guild=test_guild)
            logger.info(f"Successfully synced schedule command to test guild {TEST_GUILD_ID}")
        else:
            logger.warning("TEST_GUILD_ID not set, command will not be synced to test guild")
    except Exception as e:
        logger.error(f"Failed to sync schedule command: {e}") 