import discord
from discord import app_commands, Interaction, Member
from discord.ext import commands
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.debug(f"Loaded environment variables from: {dotenv_path}")

TEST_GUILD_ID = int(os.getenv('TEST_GUILD_ID', '0'))

# Helper to check if a guild is paid
async def is_paid_guild(guild_id, db_manager):
    try:
        result = await db_manager.fetch_one(
            "SELECT subscription_level FROM guild_settings WHERE guild_id = %s",
            guild_id
        )
        return bool(result and result.get('subscription_level') == 'premium')
    except Exception as e:
        logger.error(f"Error checking guild subscription: {e}")
        return False

class AddUserCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_manager = bot.db_manager

    @app_commands.command(
        name="add_user",
        description="Add a user as a capper (admin only)"
    )
    @app_commands.describe(user="The user to add as a capper.")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_user_command(self, interaction: Interaction, user: Member):
        """Add a user as a capper (admin only)"""
        guild_id = interaction.guild_id
        user_id = user.id
        logger.info(f"Adding user {user_id} as capper in guild {guild_id}")
        try:
            # Insert or update the capper row
            logger.debug(f"Executing INSERT INTO cappers for guild_id={guild_id}, user_id={user_id}")
            await self.db_manager.execute(
                """
                INSERT INTO cappers (
                    guild_id, user_id, display_name, image_path, banner_color, bet_won, bet_loss, bet_push, updated_at
                ) VALUES (%s, %s, %s, NULL, NULL, 0, 0, 0, UTC_TIMESTAMP())
                ON DUPLICATE KEY UPDATE updated_at = UTC_TIMESTAMP()
                """,
                guild_id, user_id, user.display_name
            )
            logger.info(f"Successfully executed INSERT for user {user_id} in guild {guild_id}")
            # Check if paid guild
            if not await is_paid_guild(guild_id, self.db_manager):
                await interaction.channel.send(
                    f"✅ {user.mention} has been added as a capper (free guild, setup complete)."
                )
                return
            # If paid, authorize user for /setid (could be a flag or just allow if row exists)
            await interaction.channel.send(
                f"✅ {user.mention} has been added as a capper! They can now use /setid to finish their profile."
            )
        except Exception as e:
            logger.exception(f"Error in add_user: {e}")
            await interaction.channel.send(
                f"❌ An error occurred while adding the capper: {str(e)}"
            )

    @add_user_command.error
    async def add_user_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        """Handle errors for the add_user command."""
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.channel.send(
                "❌ You need Administrator permissions to add cappers. Please ask a server administrator for help."
            )
        else:
            await interaction.channel.send(
                "❌ An error occurred while processing the command."
            )

async def setup(bot: commands.Bot):
    cog = AddUserCog(bot)
    await bot.add_cog(cog)
    logger.info("AddUserCog loaded")
    # Register command to specific guild for testing
    try:
        if TEST_GUILD_ID:
            test_guild = discord.Object(id=TEST_GUILD_ID)
            bot.tree.copy_global_to(guild=test_guild)
            # await bot.tree.sync(guild=test_guild)  # DISABLED: Prevent rate limit
            logger.info(f"Successfully synced add_user command to test guild {TEST_GUILD_ID}")
        else:
            logger.warning("TEST_GUILD_ID not set, command will not be synced to test guild")
    except Exception as e:
        logger.error(f"Failed to sync add_user command: {e}")
