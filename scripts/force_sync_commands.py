#!/usr/bin/env python3
"""
Force sync commands to guild using the bot's sync method.
This bypasses the need for the /sync command.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def force_sync():
    """Force sync commands to the guild."""
    try:
        # Change to bot directory
        bot_dir = os.path.join(os.path.dirname(__file__), '..', 'bot')
        os.chdir(bot_dir)
        
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        logger.info("=== Force Sync Commands ===")
        
        # Import and create bot
        from main import BettingBot
        
        bot = BettingBot()
        
        # Load extensions
        await bot.load_extensions()
        logger.info("Extensions loaded")
        
        # Get guild ID
        guild_id = os.getenv('TEST_GUILD_ID')
        if not guild_id:
            logger.error("TEST_GUILD_ID not found")
            return False
        
        guild_id = int(guild_id)
        logger.info(f"Target guild: {guild_id}")
        
        # Check current commands
        all_commands = bot.tree.get_commands()
        logger.info(f"Available commands: {[cmd.name for cmd in all_commands]}")
        
        # Force sync using bot's method
        logger.info("Running sync_commands_with_retry...")
        success = await bot.sync_commands_with_retry()
        
        if success:
            logger.info("✅ Commands synced successfully!")
            return True
        else:
            logger.error("❌ Sync failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False

async def main():
    """Main function."""
    success = await force_sync()
    
    if success:
        logger.info("=== Success ===")
        logger.info("Commands should now be available in your Discord guild.")
        logger.info("Try using /stats or other commands.")
    else:
        logger.error("=== Failed ===")
        logger.info("You may need to restart the bot or check logs.")

if __name__ == "__main__":
    asyncio.run(main()) 