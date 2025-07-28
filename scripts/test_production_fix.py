#!/usr/bin/env python3
"""
Test script to simulate production environment and test the database initialization fixes.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('bot/.env')

# Add parent directory to path so we can import from bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_database_initialization():
    """Test the database initialization process that was causing the bot to freeze."""
    print("Testing Database Initialization Fixes")
    print("=" * 50)

    try:
        # Import the database manager
        from bot.data.db_manager import DatabaseManager

        print("✅ Database manager imported successfully")

        # Create database manager instance
        db_manager = DatabaseManager()
        print("✅ Database manager instance created")

        # Test connection
        pool = await db_manager.connect()
        if not pool:
            print("❌ Failed to create connection pool")
            return False
        print("✅ Database connection pool created")

        # Test database initialization
        try:
            await db_manager.initialize_db()
            print("✅ Database initialization completed successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Close the pool
        await db_manager.close()
        print("✅ Database connection pool closed")

        print("🎉 SUCCESS: Database initialization fixes work!")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    success = await test_database_initialization()

    if success:
        print("\nALL TESTS PASSED!")
        return True
    else:
        print("\nTESTS FAILED!")
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
