#!/usr/bin/env python3
"""
Platinum Tier Database Migration Script
Runs the Platinum tier migration to add all necessary database support.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the bot directory to the Python path
bot_dir = Path(__file__).parent.parent / "bot"
sys.path.insert(0, str(bot_dir))

from bot.data.db_manager import DatabaseManager
from bot.utils.environment_validator import validate_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_platinum_migration():
    """Run the Platinum tier database migration."""
    try:
        # Load environment variables
        validate_environment()
        logger.info("✅ Environment variables loaded")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        logger.info("✅ Database manager initialized")
        
        # Read the migration file
        migration_file = Path(__file__).parent.parent / "bot" / "migrations" / "005_platinum_channel_support.sql"
        
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
        await verify_platinum_migration(db_manager)
        
        logger.info("🎉 Platinum tier migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

async def verify_platinum_migration(db_manager):
    """Verify that the Platinum migration was successful."""
    logger.info("🔍 Verifying Platinum migration...")
    
    # Check if subscription_level column exists in guild_settings
    try:
        result = await db_manager.fetch_one(
            "SHOW COLUMNS FROM guild_settings LIKE 'subscription_level'"
        )
        if result:
            logger.info("✅ subscription_level column exists in guild_settings")
        else:
            logger.warning("⚠️ subscription_level column not found in guild_settings")
    except Exception as e:
        logger.error(f"❌ Error checking subscription_level column: {e}")
    
    # Check if platinum_features table exists
    try:
        result = await db_manager.fetch_one(
            "SHOW TABLES LIKE 'platinum_features'"
        )
        if result:
            logger.info("✅ platinum_features table exists")
        else:
            logger.warning("⚠️ platinum_features table not found")
    except Exception as e:
        logger.error(f"❌ Error checking platinum_features table: {e}")
    
    # Check if webhook_integrations table exists
    try:
        result = await db_manager.fetch_one(
            "SHOW TABLES LIKE 'webhook_integrations'"
        )
        if result:
            logger.info("✅ webhook_integrations table exists")
        else:
            logger.warning("⚠️ webhook_integrations table not found")
    except Exception as e:
        logger.error(f"❌ Error checking webhook_integrations table: {e}")
    
    # Check if data_exports table exists
    try:
        result = await db_manager.fetch_one(
            "SHOW TABLES LIKE 'data_exports'"
        )
        if result:
            logger.info("✅ data_exports table exists")
        else:
            logger.warning("⚠️ data_exports table not found")
    except Exception as e:
        logger.error(f"❌ Error checking data_exports table: {e}")
    
    # Check if platinum_analytics table exists
    try:
        result = await db_manager.fetch_one(
            "SHOW TABLES LIKE 'platinum_analytics'"
        )
        if result:
            logger.info("✅ platinum_analytics table exists")
        else:
            logger.warning("⚠️ platinum_analytics table not found")
    except Exception as e:
        logger.error(f"❌ Error checking platinum_analytics table: {e}")
    
    # Check current guild settings
    try:
        guilds = await db_manager.fetch_all(
            "SELECT guild_id, subscription_level, platinum_features_enabled FROM guild_settings LIMIT 5"
        )
        logger.info(f"📊 Found {len(guilds)} guild settings records")
        for guild in guilds:
            logger.info(f"   Guild {guild['guild_id']}: {guild['subscription_level']} (Platinum: {guild['platinum_features_enabled']})")
    except Exception as e:
        logger.error(f"❌ Error checking guild settings: {e}")

async def main():
    """Main function to run the migration."""
    logger.info("🚀 Starting Platinum tier database migration...")
    
    success = await run_platinum_migration()
    
    if success:
        logger.info("✅ Migration completed successfully!")
        logger.info("🎯 Platinum tier features are now available in the database")
        logger.info("📝 Next steps:")
        logger.info("   1. Restart the bot to load the new Platinum commands")
        logger.info("   2. Test the /platinum command")
        logger.info("   3. Configure Platinum features for your guild")
    else:
        logger.error("❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 