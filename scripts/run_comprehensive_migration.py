#!/usr/bin/env python3
"""
Comprehensive Database Migration Script
Adds all missing columns to the guild_settings table for the latest bot features.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.data.db_manager import DatabaseManager
from bot.utils.environment_validator import validate_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_comprehensive_migration():
    """Run comprehensive migration to add all missing columns."""
    try:
        # Load environment variables
        validate_environment()
        logger.info("✅ Environment variables loaded")

        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.connect()
        logger.info("✅ Database manager initialized")

        # Migration SQL statements
        migrations = [
            # Main chat channel for community features
            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS main_chat_channel_id BIGINT NULL
            COMMENT 'Channel for achievement notifications and general community updates';
            """,

            # Embed channels for different types of embeds
            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS embed_channel_id BIGINT NULL
            COMMENT 'Channel for general betting embeds';
            """,

            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS parlay_embed_channel_id BIGINT NULL
            COMMENT 'Channel for parlay betting embeds';
            """,

            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS player_prop_embed_channel_id BIGINT NULL
            COMMENT 'Channel for player prop betting embeds';
            """,

            # Platinum tier features
            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS platinum_webhook_url VARCHAR(500) NULL
            COMMENT 'Discord webhook URL for Platinum tier notifications';
            """,

            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS platinum_alert_channel_id BIGINT NULL
            COMMENT 'Channel for Platinum tier alerts and notifications';
            """,

            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS platinum_api_enabled BOOLEAN DEFAULT FALSE
            COMMENT 'Whether Platinum API features are enabled';
            """,

            # Additional settings
            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS auto_sync_commands BOOLEAN DEFAULT TRUE
            COMMENT 'Whether to automatically sync commands on guild join';
            """,

            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS embed_color VARCHAR(7) DEFAULT '#00FF00'
            COMMENT 'Default color for embeds (hex format)';
            """,

            """
            ALTER TABLE guild_settings
            ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC'
            COMMENT 'Timezone for date/time displays';
            """,

            # Add indexes for performance
            """
            CREATE INDEX IF NOT EXISTS idx_guild_settings_main_chat
            ON guild_settings(main_chat_channel_id);
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_guild_settings_embed_channels
            ON guild_settings(embed_channel_id, parlay_embed_channel_id, player_prop_embed_channel_id);
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_guild_settings_platinum
            ON guild_settings(platinum_alert_channel_id, platinum_api_enabled);
            """,
        ]

        logger.info("🔄 Starting comprehensive migration...")

        for i, migration in enumerate(migrations, 1):
            try:
                logger.info(f"📝 Running migration {i}/{len(migrations)}...")
                await db_manager.execute(migration)
                logger.info(f"✅ Migration {i} completed successfully")
            except Exception as e:
                logger.warning(f"⚠️ Migration {i} failed (may already exist): {e}")

        # Verify the migration
        await verify_migration(db_manager)

        logger.info("🎉 Comprehensive migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False
    finally:
        if db_manager:
            await db_manager.close()


async def verify_migration(db_manager):
    """Verify that all expected columns exist."""
    logger.info("🔍 Verifying migration...")

    # Get table structure
    result = await db_manager.fetch_all("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'guild_settings'
        ORDER BY ORDINAL_POSITION;
    """)

    expected_columns = {
        'guild_id': 'Primary key',
        'live_game_updates': 'Live game updates setting',
        'is_paid': 'Paid status',
        'subscription_level': 'Subscription level',
        'main_chat_channel_id': 'Main chat channel',
        'embed_channel_id': 'General embed channel',
        'parlay_embed_channel_id': 'Parlay embed channel',
        'player_prop_embed_channel_id': 'Player prop embed channel',
        'platinum_webhook_url': 'Platinum webhook URL',
        'platinum_alert_channel_id': 'Platinum alert channel',
        'platinum_api_enabled': 'Platinum API enabled',
        'auto_sync_commands': 'Auto sync commands',
        'embed_color': 'Embed color',
        'timezone': 'Timezone setting'
    }

    existing_columns = {row['COLUMN_NAME']: row['COLUMN_COMMENT'] for row in result}

    logger.info("📋 Current table structure:")
    for column_name, comment in existing_columns.items():
        logger.info(f"  ✅ {column_name}: {comment}")

    missing_columns = set(expected_columns.keys()) - set(existing_columns.keys())
    if missing_columns:
        logger.warning(f"⚠️ Missing columns: {missing_columns}")
    else:
        logger.info("✅ All expected columns are present")


async def main():
    """Main function to run the migration."""
    logger.info("🚀 Starting comprehensive database migration...")

    success = await run_comprehensive_migration()

    if success:
        logger.info("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
