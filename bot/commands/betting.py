# REV 1.0.0 - Enhanced betting command with improved workflow selection and error handling
# betting-bot/commands/betting.py

"""Main betting command for placing straight or parlay bets."""

import logging
from typing import Optional, Union

import discord
from discord import ButtonStyle, Interaction, SelectOption, app_commands
from discord.ext import commands
from discord.ui import Button, Select, View

from commands.admin import require_registered_guild

# Import from same directory
from commands.straight_betting import StraightBetWorkflowView

logger = logging.getLogger(__name__)


# --- Authorization Check Function ---
async def is_allowed_command_channel(interaction: Interaction) -> bool:
    """Checks if the command is used in a configured command channel."""
    try:
        # Get guild settings
        settings = await interaction.client.db_manager.fetch_one(
            "SELECT command_channel_1, command_channel_2 FROM guild_settings WHERE guild_id = $1",
            (interaction.guild_id,),
        )

        if not settings:
            # If no settings found, allow the command (global command)
            return True

        command_channel_1_id = settings.get("command_channel_1")
        command_channel_2_id = settings.get("command_channel_2")

        # If no channels configured, allow the command (global command)
        if not command_channel_1_id and not command_channel_2_id:
            return True

        allowed_channel_ids = []
        if command_channel_1_id:
            try:
                allowed_channel_ids.append(int(command_channel_1_id))
            except (ValueError, TypeError):
                logger.error(
                    f"Invalid command_channel_1 ID in DB for guild {interaction.guild_id}: {command_channel_1_id}"
                )
        if command_channel_2_id:
            try:
                allowed_channel_ids.append(int(command_channel_2_id))
            except (ValueError, TypeError):
                logger.error(
                    f"Invalid command_channel_2 ID in DB for guild {interaction.guild_id}: {command_channel_2_id}"
                )

        if not allowed_channel_ids:
            return True  # Allow if no valid channels configured

        if interaction.channel_id not in allowed_channel_ids:
            msg = "This command can only be used in designated command channels. Please ask an admin to set them up or use the correct channel."
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                try:
                    await interaction.followup.send(msg, ephemeral=True)
                except discord.HTTPException:
                    pass
            return False

        return True
    except Exception as e:
        logger.error(f"Error checking command channel: {e}")
        return True  # Allow command on error to prevent blocking


# (Bet type selection UI removed - gameline and other flows start their workflows directly)


class BettingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("BettingCog initialized")

    @app_commands.command(
        name="gameline",
        description="Place a single game bet - moneyline, spread, or over/under",
    )
    @require_registered_guild()
    async def gameline(self, interaction: Interaction):
        logger.info(
            f"/gameline command invoked by {interaction.user} (ID: {interaction.user.id})"
        )
        try:
            # For /gameline, always use straight bets - skip bet type selection
            from commands.straight_betting import StraightBetWorkflowView

            # Directly start the straight bet workflow without an intermediate bet-type selection
            view = StraightBetWorkflowView(interaction, self.bot, message_to_control=None)

            # Send the initial message and attach the workflow view
            await interaction.response.send_message("Starting game line bet workflow...", view=view, ephemeral=True)

            # Capture the sent message to allow edits by the workflow
            view.message = await interaction.original_response()

            # Start the workflow, instructing it to skip the line-type selector
            await view.start_flow(interaction, skip_line_type=True)

            logger.info("/gameline command response sent successfully.")
        except Exception as e:
            logger.error(f"Error in /gameline command: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An error occurred while processing your request.", ephemeral=True
            )


# Add the command to the bot's command tree
async def setup(bot: commands.Bot):
    logger.info("Setting up betting commands...")
    try:
        await bot.add_cog(BettingCog(bot))
        logger.info("BettingCog loaded successfully")
    except Exception as e:
        logger.error(f"Error during betting command setup: {e}", exc_info=True)
        raise  # Re-raise the exception to ensure the bot knows about the failure
