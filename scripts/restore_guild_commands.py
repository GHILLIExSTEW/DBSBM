#!/usr/bin/env python3
"""
Emergency Guild Commands Restoration Script
Restores all commands to guilds that lost them during the migration.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.data.db_manager import DatabaseManager
from bot.utils.environment_validator import validate_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def restore_guild_commands():
    """Restore commands to all guilds in the database."""
    try:
        # Load environment variables
        validate_environment()
        logger.info("✅ Environment variables loaded")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        logger.info("✅ Database manager initialized")
        
        # Get all guilds from the database
        guilds = await db_manager.fetch_all(
            "SELECT guild_id, is_paid, subscription_level FROM guild_settings"
        )
        
        logger.info(f"📋 Found {len(guilds)} guilds in database")
        
        for guild in guilds:
            guild_id = guild['guild_id']
            is_paid = guild['is_paid']
            subscription_level = guild['subscription_level'] or 'free'
            
            logger.info(f"🔧 Processing guild {guild_id} (Paid: {is_paid}, Level: {subscription_level})")
            
            # Update subscription level if needed
            if is_paid and subscription_level != 'premium':
                await db_manager.execute(
                    """
                    UPDATE guild_settings
                    SET subscription_level = 'premium'
                    WHERE guild_id = %s
                    """,
                    (guild_id,)
                )
                logger.info(f"✅ Updated guild {guild_id} to premium")
            
            # Ensure guild has basic settings
            await db_manager.execute(
                """
                INSERT IGNORE INTO guild_settings (guild_id, is_active, subscription_level)
                VALUES (%s, 1, %s)
                """,
                (guild_id, subscription_level)
            )
            
            logger.info(f"✅ Guild {guild_id} settings verified")
        
        logger.info("🎉 All guild commands restored successfully!")
        logger.info("📝 Next steps:")
        logger.info("   1. Restart the bot")
        logger.info("   2. The bot will automatically sync commands to all guilds")
        logger.info("   3. Commands should be visible again")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Command restoration failed: {e}")
        return False

async def main():
    """Main function to restore guild commands."""
    logger.info("🚀 Starting emergency guild command restoration...")
    
    success = await restore_guild_commands()
    
    if success:
        logger.info("✅ Command restoration completed!")
        logger.info("🔄 Please restart the bot now to sync commands")
    else:
        logger.error("❌ Command restoration failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 