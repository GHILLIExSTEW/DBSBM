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
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

            # Get all available commands
            all_commands = [cmd.name for cmd in self.bot.tree.get_commands()]
            logger.debug("All available commands: %s", all_commands)

            # Sync commands to the current guild
            guild_obj = discord.Object(id=interaction.guild_id)
            synced = await self.bot.tree.sync(guild=guild_obj)
            synced_names = [cmd.name for cmd in synced]
            logger.info("Guild commands synced: %s", synced_names)

            # Create detailed response
            embed = discord.Embed(
                title="✅ Commands Synced Successfully!",
                description=f"Synced {len(synced)} commands to this guild.",
                color=0x00FF00,
            )

            embed.add_field(
                name="📋 Synced Commands",
                value="\n".join([f"• `/{cmd}`" for cmd in synced_names[:10]])
                + (
                    f"\n... and {len(synced_names) - 10} more"
                    if len(synced_names) > 10
                    else ""
                ),
                inline=False,
            )

            embed.add_field(
                name="🔍 Total Available Commands",
                value=str(len(all_commands)),
                inline=True,
            )

            embed.add_field(
                name="📊 Commands Synced", value=str(len(synced)), inline=True
            )

            # Check for specific commands
            important_commands = []
            missing_commands = [
                cmd for cmd in important_commands if cmd not in synced_names
            ]

            if missing_commands:
                embed.add_field(
                    name="⚠️ Missing Important Commands",
                    value="\n".join([f"• `/{cmd}`" for cmd in missing_commands]),
                    inline=False,
                )
                embed.color = 0xFFA500  # Orange for warning

            embed.set_footer(
                text=f"Guild ID: {interaction.guild_id} • Synced at {discord.utils.utcnow().strftime('%H:%M:%S')}"
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error("Failed to sync commands: %s", e, exc_info=True)
            error_embed = discord.Embed(
                title="❌ Sync Failed",
                description=f"Error syncing commands: {str(e)}",
                color=0xFF0000,
            )

            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed, ephemeral=True
                )
            else:
                await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(
        name="sync_global", description="Sync commands globally (owner only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_global_command(self, interaction: discord.Interaction):
        """Sync commands globally for all guilds."""
        logger.info(
            "Global sync initiated by %s in guild %s",
            interaction.user,
            interaction.guild_id,
        )
        try:
            await interaction.response.defer(ephemeral=True)

            # Get all available commands
            all_commands = [cmd.name for cmd in self.bot.tree.get_commands()]
            logger.debug("All available commands for global sync: %s", all_commands)

            # Sync commands globally
            synced = await self.bot.tree.sync()
            synced_names = [cmd.name for cmd in synced]
            logger.info("Global commands synced: %s", synced_names)

            # Create detailed response
            embed = discord.Embed(
                title="✅ Global Commands Synced Successfully!",
                description=f"Synced {len(synced)} commands globally.",
                color=0x00FF00,
            )

            embed.add_field(
                name="📋 Synced Commands",
                value="\n".join([f"• `/{cmd}`" for cmd in synced_names[:15]])
                + (
                    f"\n... and {len(synced_names) - 15} more"
                    if len(synced_names) > 15
                    else ""
                ),
                inline=False,
            )

            embed.add_field(
                name="🔍 Total Available Commands",
                value=str(len(all_commands)),
                inline=True,
            )

            embed.add_field(
                name="📊 Commands Synced", value=str(len(synced)), inline=True
            )

            embed.set_footer(
                text=f"Global sync at {discord.utils.utcnow().strftime('%H:%M:%S')}"
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error("Failed to sync commands globally: %s", e, exc_info=True)
            error_embed = discord.Embed(
                title="❌ Global Sync Failed",
                description=f"Error syncing commands globally: {str(e)}",
                color=0xFF0000,
            )

            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed, ephemeral=True
                )
            else:
                await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(
        name="list_commands", description="List all available commands"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def list_commands(self, interaction: discord.Interaction):
        """List all available commands for debugging."""
        try:
            await interaction.response.defer(ephemeral=True)

            # Get all commands
            all_commands = self.bot.tree.get_commands()
            command_names = [cmd.name for cmd in all_commands]

            # Get guild commands
            guild_obj = discord.Object(id=interaction.guild_id)
            guild_commands = self.bot.tree.get_commands(guild=guild_obj)
            guild_command_names = [cmd.name for cmd in guild_commands]

            embed = discord.Embed(
                title="📋 Available Commands",
                description="List of all commands and their sync status",
                color=0x00FF00,
            )

            embed.add_field(
                name="🔍 All Available Commands",
                value="\n".join([f"• `/{cmd}`" for cmd in command_names[:20]])
                + (
                    f"\n... and {len(command_names) - 20} more"
                    if len(command_names) > 20
                    else ""
                ),
                inline=False,
            )

            embed.add_field(
                name="📊 Guild-Synced Commands",
                value="\n".join([f"• `/{cmd}`" for cmd in guild_command_names[:20]])
                + (
                    f"\n... and {len(guild_command_names) - 20} more"
                    if len(guild_command_names) > 20
                    else ""
                ),
                inline=False,
            )

            embed.add_field(
                name="📈 Statistics",
                value=f"**Total Commands:** {len(command_names)}\n**Guild Commands:** {len(guild_command_names)}",
                inline=False,
            )

            embed.set_footer(text=f"Guild ID: {interaction.guild_id}")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error("Failed to list commands: %s", e, exc_info=True)
            error_embed = discord.Embed(
                title="❌ Failed to List Commands",
                description=f"Error: {str(e)}",
                color=0xFF0000,
            )

            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed, ephemeral=True
                )
            else:
                await interaction.followup.send(embed=error_embed, ephemeral=True)


async def setup_sync_cog(bot):
    """Setup function to register the SyncCog."""
    await bot.add_cog(SyncCog(bot))
    logger.info("SyncCog loaded")


async def setup(bot):
    """Setup function for the cog loader."""
    await bot.add_cog(SyncCog(bot))
    logger.info("SyncCog loaded via setup function")
