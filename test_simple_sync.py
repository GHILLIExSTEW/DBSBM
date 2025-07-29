#!/usr/bin/env python3
"""
Simple test to sync commands globally
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))


async def test_simple_sync():
    """Test simple global command syncing"""
    print("Testing simple global command syncing...")

    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), 'bot', '.env'))

    try:
        from bot.main import BettingBot
        print("✓ BettingBot imported successfully")

        bot = BettingBot()
        print("✓ Bot instance created")

        print("Loading extensions...")
        await bot.load_extensions()
        print("✓ Extensions loaded")

        # Get all commands
        commands = [cmd.name for cmd in bot.tree.get_commands()]
        print(f"✓ Found {len(commands)} commands: {commands}")

        # Check for setup command specifically
        setup_cmd = bot.tree.get_command("setup")
        if setup_cmd:
            print("✓ Setup command found")
        else:
            print("❌ Setup command NOT found")

        # Connect to Discord first
        print("Connecting to Discord...")
        await bot.start(os.getenv('DISCORD_TOKEN'))

        # Try simple global sync
        print("Attempting simple global sync...")
        try:
            synced = await bot.tree.sync()
            synced_names = [cmd.name for cmd in synced]
            print(
                f"✅ Simple sync successful! Synced {len(synced_names)} commands: {synced_names}")
        except Exception as sync_error:
            print(f"❌ Simple sync failed: {sync_error}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'bot' in locals():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(test_simple_sync())
