#!/usr/bin/env python3
"""
Test script to verify database connection and cappers table
"""


import asyncio
import logging
import os
import sys
import pytest
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_db_connection():
    """Test database connection functionality."""

    print("Testing database connection...")

    # Load environment variables
    load_dotenv()


    # Use PostgreSQL environment variables
    db_manager = DatabaseManager()

    # Test connection
    try:
        await db_manager.connect()
        print("✅ Database connection successful")

        # Test a simple query
        result = await db_manager.fetch_one("SELECT 1 as test")
        if result:
            print("✅ Database query successful")
        else:
            print("❌ Database query failed")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    result = asyncio.run(test_db_connection())
    if result:
        print("\n🎉 All database tests passed!")
    else:
        print("\n💥 Database tests failed!")
        sys.exit(1)
