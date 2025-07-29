#!/usr/bin/env python3
"""
Manual sync script to sync all Discord bot commands globally.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

from bot.main import BettingBot

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))


async def manual_sync():
    """Manually sync all commands globally."""
    print("Starting manual sync...")

    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), "bot", ".env"))

    # Create bot instance
    bot = BettingBot()

    try:
        # Load extensions
        print("Loading extensions...")
        await bot.load_extensions()

        # Get all commands
        commands = [cmd.name for cmd in bot.tree.get_commands()]
        print(f"Found {len(commands)} commands: {commands}")

        # Connect to Discord
        print("Connecting to Discord...")
        await bot.start(os.getenv("DISCORD_TOKEN"))

        # Manual sync - sync all commands globally
        print("Syncing all commands globally...")
        synced = await bot.tree.sync()
        synced_names = [cmd.name for cmd in synced]
        print(f"Synced {len(synced_names)} commands: {synced_names}")

        print("Manual sync completed successfully!")

    except Exception as e:
        print(f"Error during manual sync: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(manual_sync())
