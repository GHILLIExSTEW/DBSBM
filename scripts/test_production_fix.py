#!/usr/bin/env python3
"""
Test script to simulate production environment and test the database initialization fixes.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv


async def test_database_fix():
    """Test the database initialization fix."""
    print("Testing Database Initialization Fix")
    print("=" * 50)

    # Load environment variables
    load_dotenv('bot/.env')

    # Simulate production environment
    os.environ['HOSTNAME'] = 'container-123'
    os.environ['FLASK_ENV'] = 'production'

    print("Environment variables loaded")
    print("Production environment simulated")

    # Test the database manager
    try:
        # Fix the import path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bot_dir = os.path.join(os.path.dirname(current_dir), 'bot')
        if bot_dir not in sys.path:
            sys.path.insert(0, bot_dir)

        from data.db_manager import DatabaseManager

        print("\nTesting Database Manager:")

        # Create database manager instance
        db_manager = DatabaseManager()
        print("Database manager created")

        # Test connection
        print("Testing database connection...")
        pool = await db_manager.connect()
        if pool:
            print("Database connection successful")
        else:
            print("Database connection failed")
            return False

        # Test database initialization
        print("Testing database initialization...")
        try:
            await db_manager.initialize_db()
            print("Database initialization successful")
        except Exception as e:
            print(f"Database initialization failed: {e}")
            return False

        # Test basic query
        print("Testing basic query...")
        try:
            result = await db_manager.fetch_one("SELECT 1 as test")
            if result and result.get('test') == 1:
                print("Basic query successful")
            else:
                print("Basic query failed")
                return False
        except Exception as e:
            print(f"Basic query failed: {e}")
            return False

        # Close connection
        await db_manager.close()
        print("Database connection closed")

        print("SUCCESS: Database initialization fix works!")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("Starting Production Fix Tests")
    print("=" * 50)

    # Test database fix
    db_success = await test_database_fix()

    if db_success:
        print("\nALL TESTS PASSED!")
        print("Database initialization fix works")
        return True
    else:
        print("\nSOME TESTS FAILED!")
        print("Database test failed")
        return False


if __name__ == "__main__":
    # Set up logging without emoji characters
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
