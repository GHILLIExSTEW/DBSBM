#!/usr/bin/env python3
"""
Database Setup Script for DBSBM

This script automatically sets up the complete database schema by running
all SQL migration files in the correct order.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import aiomysql
from dotenv import load_dotenv

# Load environment variables from .env file in bot directory
dotenv_path = os.path.join("bot", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(f"✅ Loaded environment variables from: {dotenv_path}")
else:
    print(f"❌ .env file not found at: {dotenv_path}")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Handles database setup and migration execution."""

    def __init__(self):
        self.connection = None
        self.migrations_dir = Path("bot/migrations")

        # Database configuration from .env file (using the variable names from database_mysql.py)
        self.db_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", 3306)),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "db": os.getenv("MYSQL_DB", "dbsbm"),
            "charset": "utf8mb4",
            "autocommit": True,
        }

        # Log the configuration (without password)
        logger.info(
            f"Database config: {self.db_config['host']}:{self.db_config['port']}, user: {self.db_config['user']}, db: {self.db_config['db']}"
        )

    async def connect(self):
        """Connect to the database."""
        try:
            self.connection = await aiomysql.connect(**self.db_config)
            logger.info("✅ Connected to database successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            logger.info(
                "💡 Make sure your bot/.env file has the correct database credentials!"
            )
            logger.info(
                "   Required variables: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB"
            )
            raise

    async def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("✅ Database connection closed")

    def get_migration_files(self):
        """Get all SQL migration files in order."""
        migration_files = []

        if self.migrations_dir.exists():
            for file_path in sorted(self.migrations_dir.glob("*.sql")):
                migration_files.append(file_path)

        return migration_files

    async def execute_statement(self, statement: str):
        """Execute a single SQL statement."""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(statement)
                return True, None
        except Exception as e:
            return False, str(e)

    async def execute_migration(self, file_path: Path):
        """Execute a single migration file."""
        try:
            logger.info(f"📄 Executing migration: {file_path.name}")

            # Read the SQL file
            with open(file_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Split by semicolon to get individual statements
            statements = [
                stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
            ]

            # Execute each statement
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith("--"):
                    success, error = await self.execute_statement(statement)
                    if success:
                        logger.debug(f"  ✅ Statement {i} executed successfully")
                    else:
                        # Some statements might fail if tables already exist (which is fine)
                        if error and (
                            "already exists" in error.lower()
                            or "duplicate" in error.lower()
                        ):
                            logger.debug(f"  ⚠️ Statement {i} skipped (already exists)")
                        else:
                            logger.warning(f"  ⚠️ Statement {i} failed: {error}")

            logger.info(f"✅ Migration completed: {file_path.name}")

        except Exception as e:
            logger.error(f"❌ Failed to execute migration {file_path.name}: {e}")
            raise

    async def setup_database(self):
        """Set up the complete database schema."""
        try:
            logger.info("🚀 Starting database setup...")

            # Get all migration files
            migration_files = self.get_migration_files()

            if not migration_files:
                logger.warning("⚠️ No migration files found in bot/migrations/")
                return

            logger.info(f"📋 Found {len(migration_files)} migration files")

            # Execute each migration in order
            for file_path in migration_files:
                await self.execute_migration(file_path)

            logger.info("🎉 Database setup completed successfully!")

        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise

    async def verify_setup(self):
        """Verify that all tables were created successfully."""
        try:
            logger.info("🔍 Verifying database setup...")

            # List of expected tables
            expected_tables = [
                "users",
                "guilds",
                "bets",
                "games",
                "betting_odds",
                "user_stats",
                "guild_stats",
                "voice_channels",
                "voice_sessions",
                "admin_logs",
                "analytics_events",
                "data_sync_logs",
                "platinum_features",
                "ml_models",
                "predictions",
                "model_performance",
                "feature_importance",
            ]

            # Check each table
            async with self.connection.cursor() as cursor:
                for table in expected_tables:
                    try:
                        await cursor.execute(f"SHOW TABLES LIKE '{table}'")
                        result = await cursor.fetchone()
                        if result:
                            logger.info(f"  ✅ Table '{table}' exists")
                        else:
                            logger.warning(f"  ⚠️ Table '{table}' not found")
                    except Exception as e:
                        logger.warning(f"  ⚠️ Could not verify table '{table}': {e}")

            logger.info("✅ Database verification completed")

        except Exception as e:
            logger.error(f"❌ Database verification failed: {e}")


async def main():
    """Main function to run the database setup."""
    setup = DatabaseSetup()

    try:
        # Connect to database
        await setup.connect()

        # Set up database schema
        await setup.setup_database()

        # Verify setup
        await setup.verify_setup()

        logger.info("🎉 All done! Your database is ready to use.")

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)

    finally:
        # Close database connection
        await setup.close()


if __name__ == "__main__":
    print("=" * 60)
    print("DBSBM Database Setup Script")
    print("=" * 60)
    print()
    print("📋 Reading database credentials from bot/.env file...")
    print()

    # Check if required packages are installed
    try:
        import aiomysql
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install it with:")
        print("   pip install aiomysql python-dotenv")
        sys.exit(1)

    # Check if .env file exists in bot directory
    if not os.path.exists("bot/.env"):
        print("❌ bot/.env file not found!")
        print("Please create a bot/.env file with your database credentials:")
        print("   MYSQL_HOST=localhost")
        print("   MYSQL_PORT=3306")
        print("   MYSQL_USER=your_username")
        print("   MYSQL_PASSWORD=your_password")
        print("   MYSQL_DB=dbsbm")
        sys.exit(1)

    # Run the setup
    asyncio.run(main())
