#!/usr/bin/env python3
"""
Add sync command directly to the bot's command tree.
This is a workaround for when the sync command isn't loading properly.
"""

import os
import sys
import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleSyncCommand:
    """Simple sync command that can be added to any bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="sync", 
        description="Manually sync bot commands (admin only)"
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
            
            # Get all commands
            all_commands = self.bot.tree.get_commands()
            logger.info(f"Available commands: {[cmd.name for cmd in all_commands]}")
            
            # Sync to current guild
            guild_obj = discord.Object(id=interaction.guild_id)
            
            # Clear existing commands for this guild
            self.bot.tree.clear_commands(guild=guild_obj)
            logger.info("Cleared existing guild commands")
            
            # Add all commands to guild
            added_count = 0
            for cmd in all_commands:
                if cmd.name not in ("setup", "load_logos", "down", "up"):
                    self.bot.tree.add_command(cmd, guild=guild_obj)
                    added_count += 1
                    logger.debug(f"Added: {cmd.name}")
            
            logger.info(f"Added {added_count} commands to guild")
            
            # Sync to Discord
            synced = await self.bot.tree.sync(guild=guild_obj)
            logger.info(f"Synced {len(synced)} commands to Discord")
            
            # Verify
            guild_commands = [cmd.name for cmd in self.bot.tree.get_commands(guild=guild_obj)]
            logger.info(f"Final guild commands: {guild_commands}")
            
            await interaction.followup.send(
                f"✅ Commands synced successfully! Synced {len(synced)} commands.", 
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Failed to sync commands: {e}", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Failed to sync commands: {e}", 
                    ephemeral=True
                )

async def main():
    """Main function to demonstrate the sync command."""
    logger.info("=== Sync Command Helper ===")
    logger.info("")
    logger.info("This script provides a sync command that can be added to your bot.")
    logger.info("")
    logger.info("To use this:")
    logger.info("1. Copy the SimpleSyncCommand class to your bot")
    logger.info("2. Add it to your bot's command tree")
    logger.info("3. The /sync command will then be available")
    logger.info("")
    logger.info("Alternatively, you can manually sync commands by:")
    logger.info("1. Using Discord Developer Portal")
    logger.info("2. Restarting the bot with sync enabled")
    logger.info("3. Using the bot's built-in sync method")
    logger.info("")
    logger.info("Since other commands are working, the issue is likely")
    logger.info("that the sync command cog isn't loading properly.")

if __name__ == "__main__":
    asyncio.run(main()) 