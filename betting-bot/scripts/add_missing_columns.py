#!/usr/bin/env python3
"""
Add missing columns to bets table for enhanced player props.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env
BASE_DIR = Path(__file__).parent.parent
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Loaded environment variables from: {dotenv_path}")
else:
    print(f"WARNING: .env file not found at: {dotenv_path}")

# Add the parent directory to the path so we can import our modules
sys.path.append(str(BASE_DIR))

from data.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_missing_columns():
    """Add missing columns to the bets table."""
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.connect()

        logger.info("Adding missing columns to bets table...")

        # Add player_name column if it doesn't exist
        try:
            await db_manager.execute(
                """
                ALTER TABLE bets
                ADD COLUMN player_name VARCHAR(100) NULL COMMENT 'Player name for player props'
            """
            )
            logger.info("✅ Added player_name column to bets table")
        except Exception as e:
            if "Duplicate column name" in str(e):
                logger.info("ℹ️ player_name column already exists")
            else:
                logger.error(f"❌ Error adding player_name column: {e}")

        # Add team_name column if it doesn't exist
        try:
            await db_manager.execute(
                """
                ALTER TABLE bets
                ADD COLUMN team_name VARCHAR(100) NULL COMMENT 'Team name for player props'
            """
            )
            logger.info("✅ Added team_name column to bets table")
        except Exception as e:
            if "Duplicate column name" in str(e):
                logger.info("ℹ️ team_name column already exists")
            else:
                logger.error(f"❌ Error adding team_name column: {e}")

        # Add sport column if it doesn't exist
        try:
            await db_manager.execute(
                """
                ALTER TABLE bets
                ADD COLUMN sport VARCHAR(50) NULL COMMENT 'Sport type (NBA, NFL, etc.)'
            """
            )
            logger.info("✅ Added sport column to bets table")
        except Exception as e:
            if "Duplicate column name" in str(e):
                logger.info("ℹ️ sport column already exists")
            else:
                logger.error(f"❌ Error adding sport column: {e}")

        # Create indexes for better performance
        try:
            await db_manager.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bets_player_name
                ON bets(player_name)
            """
            )
            logger.info("✅ Created index on player_name")
        except Exception as e:
            logger.warning(f"⚠️ Could not create player_name index: {e}")

        try:
            await db_manager.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bets_team_name
                ON bets(team_name)
            """
            )
            logger.info("✅ Created index on team_name")
        except Exception as e:
            logger.warning(f"⚠️ Could not create team_name index: {e}")

        try:
            await db_manager.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bets_player_prop_complete
                ON bets(player_prop, player_name, created_at DESC)
            """
            )
            logger.info("✅ Created composite index for player props")
        except Exception as e:
            logger.warning(f"⚠️ Could not create composite index: {e}")

        # Verify the table structure
        logger.info("Verifying table structure...")
        columns = await db_manager.fetch_all(
            """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'bets'
            ORDER BY ORDINAL_POSITION
        """,
            (db_manager.db_name,),
        )

        logger.info("Current bets table columns:")
        for col in columns:
            logger.info(
                f"  - {col['COLUMN_NAME']}: {col['DATA_TYPE']} "
                f"({'NULL' if col['IS_NULLABLE'] == 'YES' else 'NOT NULL'}) "
                f"Default: {col['COLUMN_DEFAULT']} "
                f"Comment: {col['COLUMN_COMMENT']}"
            )

        logger.info("✅ Column addition completed successfully!")

        # Close database connection
        await db_manager.close()

    except Exception as e:
        logger.error(f"❌ Error adding columns: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(add_missing_columns())
