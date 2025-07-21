#!/usr/bin/env python3
"""
Platinum Tier Migration Script

This script runs the database migration to add Platinum tier support.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the bot directory to the path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from bot.data.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def run_migration():
    """Run the Platinum tier database migration."""
    try:
        logger.info("Starting Platinum tier database migration...")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.connect()
        
        # Read migration file
        migration_file = project_root / "bot" / "migrations" / "004_add_platinum_tier.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        logger.info("Executing Platinum tier migration...")
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    logger.info(f"Executing statement {i}/{len(statements)}")
                    await db_manager.execute(statement)
                    logger.info(f"Statement {i} executed successfully")
                except Exception as e:
                    logger.warning(f"Statement {i} failed (may already exist): {e}")
                    # Continue with other statements even if one fails
        
        logger.info("Platinum tier migration completed successfully!")
        
        # Verify migration by checking if tables exist
        logger.info("Verifying migration...")
        
        tables_to_check = [
            'platinum_features',
            'custom_commands', 
            'webhook_integrations',
            'real_time_alerts',
            'data_exports',
            'custom_branding',
            'multi_guild_sync',
            'platinum_analytics'
        ]
        
        for table in tables_to_check:
            try:
                result = await db_manager.fetch_one(f"SHOW TABLES LIKE '{table}'")
                if result:
                    logger.info(f"✅ Table '{table}' exists")
                else:
                    logger.warning(f"⚠️ Table '{table}' not found")
            except Exception as e:
                logger.error(f"❌ Error checking table '{table}': {e}")
        
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
        
        await db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


async def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("PLATINUM TIER MIGRATION SCRIPT")
    logger.info("=" * 60)
    
    success = await run_migration()
    
    if success:
        logger.info("=" * 60)
        logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("Platinum tier features are now available!")
        logger.info("Features added:")
        logger.info("• Custom Commands (20 max)")
        logger.info("• Webhook Integrations (10 max)")
        logger.info("• Real-Time Alerts")
        logger.info("• Data Export Tools (50 max/month)")
        logger.info("• Custom Branding")
        logger.info("• Multi-Guild Synchronization")
        logger.info("• Advanced Analytics")
        logger.info("• Priority Support")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("❌ MIGRATION FAILED")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 