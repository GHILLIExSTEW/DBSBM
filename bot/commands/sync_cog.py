"""Sync command cog for manually syncing bot commands."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class SyncCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="sync", description="Manually sync bot commands (admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_command(self, interaction: discord.Interaction):
        logger.info(
            "Manual sync initiated by %s in guild %s",
            interaction.user,
            interaction.guild_id,
        )
        try:
            await interaction.response.defer(ephemeral=True)
            commands_list = [cmd.name for cmd in self.bot.tree.get_commands()]
            logger.debug("Commands to sync: %s", commands_list)

            # Sync commands to the current guild
            guild_obj = discord.Object(id=interaction.guild_id)
            synced = await self.bot.tree.sync(guild=guild_obj)
            logger.info(
                "Guild commands synced: %s",
                [cmd.name for cmd in synced],
            )

            # Log final command list for verification
            guild_commands = [cmd.name for cmd in self.bot.tree.get_commands(guild=guild_obj)]
            logger.info("Final guild commands: %s", guild_commands)

            await interaction.followup.send(
                f"Commands synced successfully to guild! Synced {len(synced)} commands.", ephemeral=True
            )
        except Exception as e:
            logger.error("Failed to sync commands: %s", e, exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"Failed to sync commands: {e}", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"Failed to sync commands: {e}", ephemeral=True
                )


async def setup_sync_cog(bot):
    """Setup function to register the SyncCog."""
    await bot.add_cog(SyncCog(bot))
    logger.info("SyncCog loaded")

async def setup(bot):
    """Setup function for the cog loader."""
    await bot.add_cog(SyncCog(bot))
    logger.info("SyncCog loaded via setup function")
