#!/usr/bin/env python3
"""
Test script to verify bot startup and automatic syncing
"""

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

# Set up logging
logging.basicConfig(level=logging.DEBUG)


async def test_bot_startup():
    """Test bot startup and automatic syncing"""
    print("Testing bot startup and automatic syncing...")

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

        # Test the sync method directly
        print("Testing sync_commands_with_retry method...")
        try:
            success = await bot.sync_commands_with_retry()

            if success:
                print("✅ Sync method completed successfully!")
            else:
                print("❌ Sync method failed")
        except Exception as sync_error:
            print(f"❌ Sync method threw exception: {sync_error}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot_startup())
