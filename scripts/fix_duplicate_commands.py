#!/usr/bin/env python3
"""
Fix Duplicate Commands Script
Clears all duplicate commands and re-syncs them properly.
"""

import asyncio
import logging
import sys
from pathlib import Path
import os

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import discord
from discord.ext import commands
from bot.data.db_manager import DatabaseManager
from bot.utils.environment_validator import validate_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fix_duplicate_commands():
    """Clear all commands and re-sync them properly."""
    try:
        # Load environment variables
        validate_environment()
        logger.info("✅ Environment variables loaded")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        logger.info("✅ Database manager initialized")
        
        # Create bot instance for syncing
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        
        bot = commands.Bot(
            command_prefix=commands.when_mentioned_or("/"), 
            intents=intents
        )
        
        # Load only basic command extensions (skip Platinum for now)
        commands_dir = project_root / "bot" / "commands"
        cog_files = [
            "admin.py",
            "betting.py", 
            "enhanced_player_props.py",
            "parlay_betting.py",
            "remove_user.py",
            "setid.py",
            "add_user.py",
            "stats.py",
            "load_logos.py",
            "schedule.py",
            "maintenance.py",
            "odds.py",
        ]
        
        logger.info("🔄 Loading command extensions...")
        for filename in cog_files:
            file_path = commands_dir / filename
            if file_path.exists():
                extension = f"bot.commands.{filename[:-3]}"
                try:
                    await bot.load_extension(extension)
                    logger.info(f"✅ Loaded: {extension}")
                except Exception as e:
                    logger.error(f"❌ Failed to load {extension}: {e}")
        
        # Get all guilds from database
        guilds = await db_manager.fetch_all(
            "SELECT guild_id, is_paid, subscription_level FROM guild_settings"
        )
        
        logger.info(f"📋 Found {len(guilds)} guilds to fix")
        
        # Login to Discord
        await bot.login(os.getenv('DISCORD_TOKEN'))
        logger.info("✅ Logged into Discord")
        
        # First, clear ALL commands globally
        logger.info("🧹 Clearing all commands globally...")
        try:
            bot.tree.clear_commands(guild=None)
            await bot.tree.sync()
            logger.info("✅ All global commands cleared")
        except Exception as e:
            logger.error(f"❌ Failed to clear global commands: {e}")
        
        # Clear commands for each guild
        for guild in guilds:
            guild_id = guild['guild_id']
            logger.info(f"🧹 Clearing commands for guild {guild_id}...")
            
            try:
                guild_obj = discord.Object(id=guild_id)
                bot.tree.clear_commands(guild=guild_obj)
                await bot.tree.sync(guild=guild_obj)
                logger.info(f"✅ Cleared commands for guild {guild_id}")
            except Exception as e:
                logger.error(f"❌ Failed to clear guild {guild_id}: {e}")
        
        # Wait a moment for Discord to process the clears
        await asyncio.sleep(2)
        
        # Now re-sync commands to each guild
        for guild in guilds:
            guild_id = guild['guild_id']
            is_paid = guild['is_paid']
            subscription_level = guild['subscription_level'] or 'free'
            
            logger.info(f"🔧 Re-syncing commands to guild {guild_id} (Level: {subscription_level})")
            
            try:
                # Create guild object
                guild_obj = discord.Object(id=guild_id)
                
                # Add all commands to this guild
                for cmd in bot.tree.get_commands():
                    bot.tree.add_command(cmd, guild=guild_obj)
                
                # Sync to this guild
                await bot.tree.sync(guild=guild_obj)
                logger.info(f"✅ Re-synced {len(bot.tree.get_commands())} commands to guild {guild_id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to re-sync guild {guild_id}: {e}")
        
        # Also sync globally as backup
        logger.info("🌐 Syncing commands globally as backup...")
        try:
            await bot.tree.sync()
            logger.info("✅ Global sync completed")
        except Exception as e:
            logger.error(f"❌ Global sync failed: {e}")
        
        await bot.close()
        
        logger.info("🎉 Duplicate command fix completed!")
        logger.info("📝 Commands should now appear only once in Discord")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Duplicate command fix failed: {e}")
        return False

async def main():
    """Main function to fix duplicate commands."""
    logger.info("🚀 Starting duplicate command fix...")
    
    success = await fix_duplicate_commands()
    
    if success:
        logger.info("✅ Duplicate command fix completed!")
        logger.info("🎯 Commands should now appear only once in Discord")
        logger.info("📝 Check your Discord server - no more duplicates!")
    else:
        logger.error("❌ Duplicate command fix failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 