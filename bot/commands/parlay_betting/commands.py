"""Main parlay betting command and cog."""

import logging
from typing import Optional

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from commands.admin import require_registered_guild

from .workflow import ParlayBetWorkflowView

logger = logging.getLogger(__name__)


class ParlayCog(commands.Cog):
    """Cog for parlay betting commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ParlayCog initialized")

    @app_commands.command(
        name="parlay",
        description="Create a multi-leg parlay - combine multiple bets for bigger payouts",
    )
    @require_registered_guild()
    async def parlay(self, interaction: Interaction):
        """Handle the /parlay command."""
        logger.debug(
            f"Parlay command invoked by user {interaction.user.id} in guild {interaction.guild_id}"
        )
        logger.info(f"User {interaction.user.id} started parlay workflow")

        try:
            # Check if user is in allowed channel
            from commands.betting import is_allowed_command_channel

            if not await is_allowed_command_channel(interaction):
                logger.debug(
                    f"User {interaction.user.id} not in allowed channel for parlay"
                )
                return

            view = ParlayBetWorkflowView(interaction, self.bot)
            logger.debug("ParlayBetWorkflowView initialized successfully.")

            await interaction.response.send_message(
                "Let's build your parlay! Add legs (game lines or player props) and finalize when ready:",
                view=view,
                ephemeral=True,
            )
            logger.debug("Initial parlay message sent")

            view.message = await interaction.original_response()
            logger.debug("Message object assigned to parlay workflow view")

            # Start the workflow
            await view.start_flow(interaction)
            logger.debug("Parlay workflow started successfully")
            logger.info("Parlay workflow started successfully.")

        except Exception as e:
            logger.exception(
                f"Error in /parlay command for user {interaction.user.id}: {e}"
            )
            await interaction.response.send_message(
                "❌ An error occurred while processing your parlay request.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    """Set up the parlay betting cog."""
    logger.info("Setting up parlay commands...")
    try:
        await bot.add_cog(ParlayCog(bot))
        logger.info("ParlayCog loaded successfully")
    except Exception as e:
        logger.exception(f"Error during parlay command setup: {e}")
        raise
