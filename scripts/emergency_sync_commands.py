#!/usr/bin/env python3
"""
Emergency script to manually sync all bot commands to a guild.
This should be used when the /sync command clears commands but doesn't resync them.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def emergency_sync():
    """Emergency sync all commands to the guild."""
    try:
        # Import the bot class
        from bot.main import BettingBot
        
        # Create bot instance
        bot = BettingBot()
        
        # Load extensions
        await bot.load_extensions()
        logger.info("Extensions loaded successfully")
        
        # Get guild ID from environment
        guild_id = os.getenv('TEST_GUILD_ID')
        if not guild_id:
            logger.error("TEST_GUILD_ID not found in environment variables")
            return False
        
        guild_id = int(guild_id)
        logger.info(f"Target guild ID: {guild_id}")
        
        # Get all commands
        all_commands = bot.tree.get_commands()
        logger.info(f"Available commands: {[cmd.name for cmd in all_commands]}")
        
        # Create guild object
        import discord
        guild_obj = discord.Object(id=guild_id)
        
        # Clear existing commands for this guild
        bot.tree.clear_commands(guild=guild_obj)
        logger.info("Cleared existing commands for guild")
        
        # Add all commands to the guild
        for cmd in all_commands:
            if cmd.name not in ("setup", "load_logos", "down", "up"):
                bot.tree.add_command(cmd, guild=guild_obj)
                logger.info(f"Added command: {cmd.name}")
        
        # Sync commands to the guild
        synced = await bot.tree.sync(guild=guild_obj)
        logger.info(f"Synced {len(synced)} commands to guild")
        
        # Log final command list
        guild_commands = [cmd.name for cmd in bot.tree.get_commands(guild=guild_obj)]
        logger.info(f"Final guild commands: {guild_commands}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}", exc_info=True)
        return False

async def main():
    """Main function."""
    logger.info("=== Emergency Command Sync ===")
    
    success = await emergency_sync()
    
    if success:
        logger.info("✅ Commands synced successfully!")
        logger.info("The bot should now have all commands available in your guild.")
    else:
        logger.error("❌ Failed to sync commands")
        logger.info("You may need to restart the bot completely.")

if __name__ == "__main__":
    asyncio.run(main()) 