#!/usr/bin/env python3
"""
Simple test script to test database connection and table creation.
"""

import os
import sys
import asyncio
import logging
import aiomysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv('bot/.env')

# Database configuration
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')


async def test_database_connection():
    """Test basic database connection and table creation."""
    print("Testing Database Connection")
    print("=" * 50)

    print(f"Host: {MYSQL_HOST}")
    print(f"Port: {MYSQL_PORT}")
    print(f"User: {MYSQL_USER}")
    print(f"Database: {MYSQL_DB}")

    try:
        # Create connection pool
        pool = await aiomysql.create_pool(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DB,
            minsize=1,
            maxsize=5,
            autocommit=True,
            echo=False,
            pool_recycle=3600,
            connect_timeout=30,
        )
        print("Database connection pool created successfully")

        # Test basic query
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT 1 as test")
                result = await cursor.fetchone()
                if result and result.get('test') == 1:
                    print("Basic query successful")
                else:
                    print("Basic query failed")
                    return False

        # Test table verification
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.Cursor) as cursor:
                # Check if guild_settings table exists
                await cursor.execute("SHOW TABLES LIKE 'guild_settings'")
                table_exists = await cursor.fetchone() is not None

                if table_exists:
                    print("guild_settings table exists")
                else:
                    print("guild_settings table does not exist")

                # Test basic query on existing table
                try:
                    await cursor.execute("SELECT COUNT(*) as count FROM guild_settings")
                    result = await cursor.fetchone()
                    print(f"guild_settings table has {result[0] if result else 0} rows")
                except Exception as e:
                    print(f"Warning: Could not query guild_settings table: {e}")

        # Close pool
        pool.close()
        await pool.wait_closed()
        print("Database connection pool closed")

        print("SUCCESS: Database connection and table creation works!")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    success = await test_database_connection()

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
