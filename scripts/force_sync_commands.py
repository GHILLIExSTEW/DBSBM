#!/usr/bin/env python3
"""
Emergency Force Command Sync Script
Forces all commands to sync to guilds when only /setup is visible.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import discord
from discord.ext import commands

from bot.data.db_manager import DatabaseManager
from bot.utils.environment_validator import validate_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def force_sync_commands():
    """Force sync all commands to guilds."""
    try:
        # Load environment variables
        validate_environment()
        logger.info("✅ Environment variables loaded")

        # Initialize database manager
        db_manager = DatabaseManager()
        logger.info("✅ Database manager initialized")

        # Create bot instance for syncing
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True

        bot = commands.Bot(
            command_prefix=commands.when_mentioned_or("/"), intents=intents
        )

        # Load all command extensions
        commands_dir = project_root / "bot" / "commands"
        cog_files = [
            "admin.py",
            "betting.py",
            "enhanced_player_props.py",
            "parlay_betting.py",
            "remove_user.py",
            "setid.py",
            "add_user.py",
            "stats.py",
            "load_logos.py",
            "schedule.py",
            "maintenance.py",
            "odds.py",
            "platinum.py",
            "platinum_api.py",
        ]

        logger.info("🔄 Loading command extensions...")
        for filename in cog_files:
            file_path = commands_dir / filename
            if file_path.exists():
                extension = f"bot.commands.{filename[:-3]}"
                try:
                    await bot.load_extension(extension)
                    logger.info(f"✅ Loaded: {extension}")
                except Exception as e:
                    logger.error(f"❌ Failed to load {extension}: {e}")

        # Get all guilds from database
        guilds = await db_manager.fetch_all(
            "SELECT guild_id, is_paid, subscription_level FROM guild_settings"
        )

        logger.info(f"📋 Found {len(guilds)} guilds to sync")

        # Login to Discord
        await bot.login(os.getenv("DISCORD_TOKEN"))
        logger.info("✅ Logged into Discord")

        # Force sync to each guild
        for guild in guilds:
            guild_id = guild["guild_id"]
            is_paid = guild["is_paid"]
            subscription_level = guild["subscription_level"] or "free"

            logger.info(
                f"🔧 Syncing commands to guild {guild_id} (Level: {subscription_level})"
            )

            try:
                # Create guild object
                guild_obj = discord.Object(id=guild_id)

                # Clear existing commands for this guild
                bot.tree.clear_commands(guild=guild_obj)

                # Add all commands to this guild
                for cmd in bot.tree.get_commands():
                    bot.tree.add_command(cmd, guild=guild_obj)

                # Sync to this guild
                await bot.tree.sync(guild=guild_obj)
                logger.info(
                    f"✅ Synced {len(bot.tree.get_commands())} commands to guild {guild_id}"
                )

            except Exception as e:
                logger.error(f"❌ Failed to sync guild {guild_id}: {e}")

        # Also sync globally as backup
        logger.info("🌐 Syncing commands globally as backup...")
        try:
            await bot.tree.sync()
            logger.info("✅ Global sync completed")
        except Exception as e:
            logger.error(f"❌ Global sync failed: {e}")

        await bot.close()

        logger.info("🎉 Force command sync completed!")
        logger.info("📝 All commands should now be visible in your Discord servers")

        return True

    except Exception as e:
        logger.error(f"❌ Force sync failed: {e}")
        return False


async def main():
    """Main function to force sync commands."""
    logger.info("🚀 Starting emergency force command sync...")

    success = await force_sync_commands()

    if success:
        logger.info("✅ Force sync completed successfully!")
        logger.info("🎯 All commands should now be visible in your Discord servers")
    else:
        logger.error("❌ Force sync failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
