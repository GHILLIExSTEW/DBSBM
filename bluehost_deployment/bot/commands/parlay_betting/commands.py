"""Main parlay betting command and cog."""

import logging
from typing import Optional

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from bot.commands.admin import require_registered_guild

from .workflow import ParlayBetWorkflowView

logger = logging.getLogger(__name__)


class ParlayCog(commands.Cog):
    """Cog for parlay betting commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logging.info("ParlayCog initialized")

    @app_commands.command(
        name="parlay",
        description="Create a multi-leg parlay - combine multiple bets for bigger payouts",
    )
    @require_registered_guild()
    async def parlay(self, interaction: Interaction):
        """Handle the /parlay command."""
        logging.info(
            f"/parlay command invoked by {interaction.user} (ID: {interaction.user.id})"
        )
        try:
            view = ParlayBetWorkflowView(interaction, self.bot)
            logging.debug("ParlayBetWorkflowView initialized successfully.")
            await interaction.response.send_message(
                "Let's build your parlay! Add legs (game lines or player props) and finalize when ready:",
                view=view,
                ephemeral=True,
            )
            view.message = await interaction.original_response()
            logging.info("/parlay command response sent successfully.")

            # Start the workflow
            await view.start_flow(interaction)
            logging.info("Parlay workflow started successfully.")
        except Exception as e:
            logging.error(f"Error in /parlay command: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An error occurred while processing your parlay request.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    """Set up the parlay betting cog."""
    logging.info("Setting up parlay commands...")
    try:
        await bot.add_cog(ParlayCog(bot))
        logging.info("ParlayCog loaded successfully")
    except Exception as e:
        logging.error(f"Error during parlay command setup: {e}", exc_info=True)
        raise
