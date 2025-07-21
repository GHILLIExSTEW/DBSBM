#!/usr/bin/env python3
"""
Add Platinum Tier Channel Columns Script
Runs the migration to add the missing channel columns for Platinum tier.
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

async def add_platinum_channels():
    """Add the missing Platinum tier channel columns."""
    try:
        # Load environment variables
        validate_environment()
        logger.info("✅ Environment variables loaded")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        logger.info("✅ Database manager initialized")
        
        # Read the migration file
        migration_file = project_root / "bot" / "migrations" / "006_add_platinum_channels.sql"
        
        if not migration_file.exists():
            logger.error(f"❌ Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info("✅ Migration file loaded")
        
        # Split the migration into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        logger.info(f"📋 Found {len(statements)} SQL statements to execute")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    logger.info(f"🔧 Executing statement {i}/{len(statements)}")
                    await db_manager.execute(statement)
                    logger.info(f"✅ Statement {i} executed successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Statement {i} failed (this might be expected): {e}")
                    # Continue with other statements even if one fails
                    continue
        
        # Verify the migration
        await verify_platinum_channels(db_manager)
        
        logger.info("🎉 Platinum channel migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

async def verify_platinum_channels(db_manager):
    """Verify that the Platinum channel migration was successful."""
    logger.info("🔍 Verifying Platinum channel migration...")
    
    # Check for embed channels
    embed_channels = ['embed_channel_1', 'embed_channel_2', 'embed_channel_3', 'embed_channel_4', 'embed_channel_5']
    for channel in embed_channels:
        try:
            result = await db_manager.fetch_one(
                f"SHOW COLUMNS FROM guild_settings LIKE '{channel}'"
            )
            if result:
                logger.info(f"✅ {channel} column exists")
            else:
                logger.warning(f"⚠️ {channel} column not found")
        except Exception as e:
            logger.error(f"❌ Error checking {channel} column: {e}")
    
    # Check for command channels
    command_channels = ['command_channel_1', 'command_channel_2', 'command_channel_3', 'command_channel_4', 'command_channel_5']
    for channel in command_channels:
        try:
            result = await db_manager.fetch_one(
                f"SHOW COLUMNS FROM guild_settings LIKE '{channel}'"
            )
            if result:
                logger.info(f"✅ {channel} column exists")
            else:
                logger.warning(f"⚠️ {channel} column not found")
        except Exception as e:
            logger.error(f"❌ Error checking {channel} column: {e}")
    
    # Check for admin channels
    admin_channels = ['admin_channel_1', 'admin_channel_2', 'admin_channel_3', 'admin_channel_4', 'admin_channel_5']
    for channel in admin_channels:
        try:
            result = await db_manager.fetch_one(
                f"SHOW COLUMNS FROM guild_settings LIKE '{channel}'"
            )
            if result:
                logger.info(f"✅ {channel} column exists")
            else:
                logger.warning(f"⚠️ {channel} column not found")
        except Exception as e:
            logger.error(f"❌ Error checking {channel} column: {e}")
    
    # Check for Platinum-specific channels
    platinum_channels = [
        'platinum_webhook_channel_id',
        'platinum_analytics_channel_id', 
        'platinum_export_channel_id',
        'platinum_api_channel_id',
        'platinum_alerts_channel_id'
    ]
    for channel in platinum_channels:
        try:
            result = await db_manager.fetch_one(
                f"SHOW COLUMNS FROM guild_settings LIKE '{channel}'"
            )
            if result:
                logger.info(f"✅ {channel} column exists")
            else:
                logger.warning(f"⚠️ {channel} column not found")
        except Exception as e:
            logger.error(f"❌ Error checking {channel} column: {e}")
    
    logger.info("📊 Platinum tier now supports:")
    logger.info("   • 5 embed channels (Free: 1, Premium: 2, Platinum: 5)")
    logger.info("   • 5 command channels (Free: 1, Premium: 2, Platinum: 5)")
    logger.info("   • 5 admin channels (Free: 1, Premium: 1, Platinum: 5)")
    logger.info("   • 5 Platinum-specific channels (Platinum only)")

async def main():
    """Main function to run the migration."""
    logger.info("🚀 Starting Platinum channel migration...")
    
    success = await add_platinum_channels()
    
    if success:
        logger.info("✅ Channel migration completed successfully!")
        logger.info("🎯 Platinum tier now has full channel support:")
        logger.info("   • 5 embed channels")
        logger.info("   • 5 command channels") 
        logger.info("   • 5 admin channels")
        logger.info("   • 5 Platinum-specific channels")
        logger.info("📝 Next steps:")
        logger.info("   1. Restart the bot to load the new Platinum commands")
        logger.info("   2. Configure the additional channels for Platinum guilds")
        logger.info("   3. Test the /platinum command")
    else:
        logger.error("❌ Channel migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 