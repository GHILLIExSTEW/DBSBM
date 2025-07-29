#!/usr/bin/env python3
"""
Fixed manual sync script that works with the bot's existing sync logic.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

from bot.main import BettingBot

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))


async def manual_sync_fixed():
    """Manually sync all commands using the bot's existing sync logic."""
    print("Starting fixed manual sync...")

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

        # Use the bot's existing sync logic
        print("Using bot's sync logic...")
        success = await bot.sync_commands_with_retry()

        if success:
            print("✅ Commands synced successfully using bot's logic!")
        else:
            print("❌ Failed to sync commands")

        print("Manual sync completed!")

    except Exception as e:
        print(f"Error during manual sync: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(manual_sync_fixed())
