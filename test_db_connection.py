#!/usr/bin/env python3
"""
Test database connection with the provided credentials.
"""

import asyncio
import os
import aiomysql
from dotenv import load_dotenv


async def test_database_connection():
    """Test database connection with the provided credentials."""
    print("🔍 Testing Database Connection...")

    # Load environment variables
    load_dotenv('bot/.env')

    try:
        # Create database connection
        connection = await aiomysql.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            db=os.getenv("MYSQL_DB"),
            autocommit=True
        )

        # Test connection
        print("✅ Connected to database successfully!")

        # Test simple query
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT 1")
            result = await cursor.fetchone()
            print(f"✅ Query test: {result}")

        # Close connection
        connection.close()
        print("🎉 Database connection test successful!")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_database_connection())
