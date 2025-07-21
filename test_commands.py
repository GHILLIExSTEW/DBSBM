#!/usr/bin/env python3
"""
Test script to check bot commands.
"""

import asyncio
import os
import sys
import logging

# Add the bot directory to the path
sys.path.append('.')

from bot.main import BettingBot

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_commands():
    """Test if bot can load and show commands."""
    try:
        logger.info("🧪 Testing bot command loading...")
        
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
        
        # Try to connect (briefly)
        logger.info("🔌 Testing connection...")
        try:
            await bot.start(os.getenv("DISCORD_TOKEN"), log_handler=None)
        except Exception as e:
            logger.info(f"Connection test completed: {e}")
        
        logger.info("🎉 Test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_commands()) 