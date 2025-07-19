#!/usr/bin/env python3
"""
Test script to verify database connection and cappers table
"""

import asyncio
import os
import sys

import pytest
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.db_manager import DatabaseManager


@pytest.mark.asyncio
async def test_db_connection():
    """Test database connection and cappers table"""
    print("Testing database connection...")

    # Load environment variables
    load_dotenv()

    # Create database manager
    db_manager = DatabaseManager()

    try:
        # Connect to database
        pool = await db_manager.connect()
        if not pool:
            print("❌ Failed to connect to database")
            return False

        print("✅ Database connection successful")

        # Check if cappers table exists
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = %s AND table_name = 'cappers'",
                    (db_manager.db_name,),
                )
                result = await cursor.fetchone()
                if result and result[0] > 0:
                    print("✅ Cappers table exists")
                else:
                    print("❌ Cappers table does not exist")
                    return False

        # Test inserting a dummy record
        print("Testing INSERT into cappers table...")
        test_guild_id = 123456789
        test_user_id = 987654321

        try:
            result = await db_manager.execute(
                """
                INSERT INTO cappers (
                    guild_id, user_id, display_name, image_path, banner_color, bet_won, bet_loss, bet_push, updated_at
                ) VALUES (%s, %s, NULL, NULL, NULL, 0, 0, 0, UTC_TIMESTAMP())
                ON DUPLICATE KEY UPDATE updated_at = UTC_TIMESTAMP()
                """,
                test_guild_id,
                test_user_id,
            )
            print(f"✅ INSERT test successful: {result}")

            # Clean up test record
            await db_manager.execute(
                "DELETE FROM cappers WHERE guild_id = %s AND user_id = %s",
                test_guild_id,
                test_user_id,
            )
            print("✅ Test record cleaned up")

        except Exception as e:
            print(f"❌ INSERT test failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        await db_manager.close()


if __name__ == "__main__":
    result = asyncio.run(test_db_connection())
    if result:
        print("\n🎉 All database tests passed!")
    else:
        print("\n💥 Database tests failed!")
        sys.exit(1)
