#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "bot"))

from bot.data.db_manager import DatabaseManager


async def initialize_database():
    """Initialize the database with all required tables."""
    print("🔄 Initializing database...")

    db_manager = DatabaseManager()

    try:
        await db_manager.initialize_db()
        print("✅ Database tables created successfully!")

        # Test that the new tables exist
        async with db_manager._pool.acquire() as conn:
            tables_to_check = [
                "community_metrics",
                "community_achievements",
                "user_metrics",
                "community_events",
                "bet_reactions",
            ]

            for table in tables_to_check:
                exists = await db_manager.table_exists(conn, table)
                status = "✅" if exists else "❌"
                print(f"{status} Table '{table}': {'EXISTS' if exists else 'MISSING'}")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    finally:
        await db_manager.close()

    return True


if __name__ == "__main__":
    success = asyncio.run(initialize_database())
    if success:
        print("\n🎉 Database initialization completed successfully!")
    else:
        print("\n💥 Database initialization failed!")
        sys.exit(1)
