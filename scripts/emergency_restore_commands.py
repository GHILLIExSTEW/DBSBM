#!/usr/bin/env python3
"""
Emergency script to restore all bot commands.
Run this if the bot is not registering any commands.
"""

import asyncio
import logging
import os
import sys

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from bot.main import BettingBot

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def emergency_restore():
    """Emergency restore all commands."""
    try:
        logger.info("🚨 Starting emergency command restoration...")

        # Create bot instance
        bot = BettingBot()

        # Load extensions
        logger.info("📦 Loading extensions...")
        await bot.load_extensions()

        # Get all commands
        all_commands = bot.tree.get_commands()
        logger.info(f"✅ Found {len(all_commands)} commands loaded:")
        for cmd in all_commands:
            logger.info(f"  - /{cmd.name}")

        # Sync commands globally
        logger.info("🔄 Syncing commands globally...")
        await bot.tree.sync()
        logger.info("✅ Commands synced globally!")

        # Get guilds from database and sync to each
        logger.info("🏢 Syncing commands to guilds...")
        guilds_query = """
            SELECT guild_id, is_paid, subscription_level
            FROM guild_settings
        """
        guilds = await bot.db_manager.fetch_all(guilds_query)

        for guild in guilds:
            guild_id = guild["guild_id"]
            try:
                guild_obj = discord.Object(id=guild_id)
                await bot.tree.sync(guild=guild_obj)
                logger.info(f"✅ Synced commands to guild {guild_id}")
            except Exception as e:
                logger.error(f"❌ Failed to sync to guild {guild_id}: {e}")

        logger.info("🎉 Emergency command restoration complete!")
        logger.info("🔄 Please restart your bot now.")

    except Exception as e:
        logger.error(f"❌ Emergency restoration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(emergency_restore())
