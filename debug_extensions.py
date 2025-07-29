#!/usr/bin/env python3
"""
Debug script to test extension loading
"""

import asyncio
import os
import sys

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))


async def debug_extensions():
    """Debug extension loading"""
    print("Starting extension debug...")

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

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_extensions())
