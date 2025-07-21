#!/usr/bin/env python3
"""
Emergency script to sync commands to all existing guilds immediately.
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

async def sync_commands_now():
    """Sync commands to all existing guilds immediately."""
    try:
        logger.info("🚨 Starting emergency command sync to all guilds...")
        
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
        
        # Connect to Discord
        logger.info("🔌 Connecting to Discord...")
        await bot.start(os.getenv("DISCORD_TOKEN"), log_handler=None)
        
        # Wait for bot to be ready
        await asyncio.sleep(5)
        
        # Get all guilds
        guilds = bot.guilds
        logger.info(f"🏢 Found {len(guilds)} guilds:")
        
        for guild in guilds:
            logger.info(f"  - {guild.name} ({guild.id})")
        
        # Sync commands to each guild
        for guild in guilds:
            try:
                guild_obj = discord.Object(id=guild.id)
                
                # Clear existing commands
                bot.tree.clear_commands(guild=guild_obj)
                
                # Add all commands
                for cmd in all_commands:
                    bot.tree.add_command(cmd, guild=guild_obj)
                
                # Sync to guild
                await bot.tree.sync(guild=guild_obj)
                logger.info(f"✅ Successfully synced {len(all_commands)} commands to guild {guild.name} ({guild.id})")
                
            except Exception as e:
                logger.error(f"❌ Failed to sync to guild {guild.name} ({guild.id}): {e}")
        
        logger.info("🎉 Command sync completed!")
        logger.info("🔄 Please restart your bot to apply the changes.")
        
        # Close bot
        await bot.close()
        
    except Exception as e:
        logger.error(f"❌ Emergency sync failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(sync_commands_now()) 