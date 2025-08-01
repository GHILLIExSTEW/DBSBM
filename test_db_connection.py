#!/usr/bin/env python3
"""
Simple database connection test script.
"""

import os
import asyncio
import aiomysql
from dotenv import load_dotenv

# Load environment variables from bot/.env
load_dotenv("bot/.env")

async def test_db_connection():
    """Test database connection."""
    print("🔍 Testing database connection...")

    # Print environment variables (without password)
    print(f"Host: {os.getenv('MYSQL_HOST', 'NOT SET')}")
    print(f"Port: {os.getenv('MYSQL_PORT', 'NOT SET')}")
    print(f"User: {os.getenv('MYSQL_USER', 'NOT SET')}")
    print(f"Database: {os.getenv('MYSQL_DB', 'NOT SET')}")
    print(f"Password: {'SET' if os.getenv('MYSQL_PASSWORD') else 'NOT SET'}")

    try:
        pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            db=os.getenv("MYSQL_DB"),
            autocommit=True,
            minsize=1,
            maxsize=5,
        )

        print("✅ Database connection pool created successfully!")

        # Test a simple query
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                print(f"✅ Test query result: {result}")

        pool.close()
        await pool.wait_closed()
        print("✅ Database connection test completed successfully!")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Error type: {type(e).__name__}")

        # Check if it's a connection refused error
        if "Can't connect to MySQL server" in str(e):
            print("💡 This suggests MySQL server is not running or not accessible")
        elif "Access denied" in str(e):
            print("💡 This suggests authentication issues")
        elif "Unknown database" in str(e):
            print("💡 This suggests the database doesn't exist")

if __name__ == "__main__":
    asyncio.run(test_db_connection()) 