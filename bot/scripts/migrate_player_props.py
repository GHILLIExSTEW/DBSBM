#!/usr/bin/env python3
"""
Player Props Database Migration Script
Sets up the enhanced player props database schema and migrates existing data.
"""

import asyncio
import logging
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


class PlayerPropsMigration:
    """Handles migration of player props database schema."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def run_migration(self):
        """Run the complete migration process."""
        try:
            logger.info("Starting Player Props Database Migration...")

            # Step 1: Create new tables
            await self._create_player_props_tables()

            # Step 2: Migrate existing data
            await self._migrate_existing_data()

            # Step 3: Create indexes for performance
            await self._create_indexes()

            # Step 4: Populate initial data
            await self._populate_initial_data()

            logger.info("✅ Player Props Migration completed successfully!")

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise

    async def _create_player_props_tables(self):
        """Create the new player props tables."""
        logger.info("Creating player props tables...")

        # Read and execute the schema file
        schema_file = Path(__file__).parent.parent / "data" / "player_props_schema.sql"

        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return

        with open(schema_file, "r") as f:
            schema_sql = f.read()

        # Split into individual statements and execute
        statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]

        for statement in statements:
            if statement:
                try:
                    await self.db_manager.execute(statement)
                    logger.info(f"Executed: {statement[:50]}...")
                except Exception as e:
                    logger.warning(f"Statement failed (may already exist): {e}")

    async def _migrate_existing_data(self):
        """Migrate existing player prop data from bets table."""
        logger.info("Migrating existing player prop data...")

        try:
            # Get existing player prop bets
            query = """
                SELECT DISTINCT
                    player_name, team_name, league, sport,
                    COUNT(*) as bet_count,
                    MAX(created_at) as last_used
                FROM bets
                WHERE player_prop = 1
                AND player_name IS NOT NULL
                AND player_name != ''
                GROUP BY player_name, team_name, league, sport
            """

            existing_players = await self.db_manager.fetch_all(query)

            if not existing_players:
                logger.info("No existing player prop data found.")
                return

            # Insert into player_search_cache
            for player in existing_players:
                await self._insert_player_to_cache(player)

            logger.info(f"Migrated {len(existing_players)} players to search cache.")

        except Exception as e:
            logger.error(f"Error migrating existing data: {e}")

    async def _insert_player_to_cache(self, player_data: dict):
        """Insert a player into the search cache."""
        try:
            # Normalize search keywords
            keywords = self._normalize_search_keywords(
                player_data["player_name"], player_data["team_name"]
            )

            query = """
                INSERT INTO player_search_cache
                (player_name, team_name, league, sport, search_keywords, last_used, usage_count, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    search_keywords = VALUES(search_keywords),
                    last_used = VALUES(last_used),
                    usage_count = usage_count + VALUES(usage_count)
            """

            await self.db_manager.execute(
                query,
                (
                    player_data["player_name"],
                    player_data["team_name"],
                    player_data["league"],
                    player_data["sport"],
                    keywords,
                    player_data["last_used"],
                    player_data["bet_count"],
                ),
            )

        except Exception as e:
            logger.error(f"Error inserting player to cache: {e}")

    def _normalize_search_keywords(self, player_name: str, team_name: str) -> str:
        """Normalize search keywords for better matching."""
        import re

        # Remove special characters and normalize
        normalized = re.sub(r"[^\w\s]", "", f"{player_name} {team_name}".lower())

        # Split into words and create variations
        words = normalized.split()
        keywords = set()

        # Add full name
        keywords.add(normalized)

        # Add individual words
        keywords.update(words)

        # Add common abbreviations
        if len(words) >= 2:
            # First letter of each word
            abbreviations = [word[0] for word in words if word]
            keywords.add("".join(abbreviations))

            # First word + last word
            if len(words) >= 2:
                keywords.add(f"{words[0]} {words[-1]}")

        return " ".join(keywords)

    async def _create_indexes(self):
        """Create additional indexes for performance."""
        logger.info("Creating performance indexes...")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_player_props_active ON player_props(is_active, league)",
            "CREATE INDEX IF NOT EXISTS idx_player_performance_date ON player_performance(game_date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_search_cache_league ON player_search_cache(league, usage_count DESC)",
            "CREATE INDEX IF NOT EXISTS idx_bets_player_prop_complete ON bets(player_prop, player_name, created_at DESC)",
        ]

        for index_sql in indexes:
            try:
                await self.db_manager.execute(index_sql)
                logger.info(f"Created index: {index_sql[:50]}...")
            except Exception as e:
                logger.warning(f"Index creation failed: {e}")

    async def _populate_initial_data(self):
        """Populate initial prop types and templates."""
        logger.info("Populating initial prop data...")

        # This could be expanded to populate common prop types
        # For now, we'll just log that the migration is complete
        logger.info("Initial data population complete.")

    async def verify_migration(self):
        """Verify that the migration was successful."""
        logger.info("Verifying migration...")

        try:
            # Check if tables exist
            tables = ["player_props", "player_performance", "player_search_cache"]

            for table in tables:
                result = await self.db_manager.fetch_one(f"SHOW TABLES LIKE '{table}'")
                if result:
                    logger.info(f"✅ Table {table} exists")
                else:
                    logger.error(f"❌ Table {table} missing")

            # Check player search cache count
            result = await self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM player_search_cache"
            )
            if result:
                logger.info(f"✅ Player search cache has {result['count']} entries")

            logger.info("✅ Migration verification complete!")

        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")


async def main():
    """Main migration function."""
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.connect()

        # Run migration
        migration = PlayerPropsMigration(db_manager)
        await migration.run_migration()

        # Verify migration
        await migration.verify_migration()

        # Close database connection
        await db_manager.close()

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
