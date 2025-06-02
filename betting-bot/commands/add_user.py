import discord
from discord import app_commands, Interaction, Member
from discord.ext import commands
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Helper to check if a guild is paid (stub, replace with your real logic)
def is_paid_guild(guild_id, db_manager):
    # Example: check a subscriptions table or similar
    # Return True if paid, False if free
    # Replace with your actual check
    return True

class AddUserCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_manager = bot.db_manager

    @app_commands.command(name="add_user", description="Add a user as a capper (admin only)")
    @app_commands.describe(user="The user to add as a capper.")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_user_command(self, interaction: Interaction, user: Member):
        guild_id = interaction.guild_id
        user_id = user.id
        try:
            # Insert or update the capper row
            await self.db_manager.execute(
                """
                INSERT INTO cappers (
                    guild_id, user_id, display_name, image_path, banner_color, bet_won, bet_loss, bet_push, updated_at
                ) VALUES ($1, $2, NULL, NULL, NULL, 0, 0, 0, NOW() AT TIME ZONE 'UTC')
                ON CONFLICT (guild_id, user_id) DO UPDATE SET updated_at = NOW() AT TIME ZONE 'UTC'
                """,
                guild_id, user_id
            )
            # Check if paid guild
            if not is_paid_guild(guild_id, self.db_manager):
                await interaction.response.send_message(
                    f"✅ {user.mention} added as a capper (free guild, setup complete).",
                    ephemeral=True
                )
                return
            # If paid, authorize user for /setid (could be a flag or just allow if row exists)
            await interaction.response.send_message(
                f"✅ {user.mention} added as a capper! They can now use /setid to finish their profile.",
                ephemeral=True
            )
        except Exception as e:
            logger.exception(f"Error in add_user: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while adding the capper.", ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(AddUserCog(bot))
    logger.info("AddUserCog loaded")
