#!/usr/bin/env python3

import pytest
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

@pytest.mark.asyncio
async def test_db_connection():
    """Test database connection"""
    load_dotenv()
    
    try:
        print("Testing PostgreSQL connection...")
        print(f"Host: {os.getenv('POSTGRES_HOST')}")
        print(f"Port: {os.getenv('POSTGRES_PORT')}")
        print(f"Database: {os.getenv('POSTGRES_DB')}")
        print(f"User: {os.getenv('POSTGRES_USER')}")
        
        conn = await asyncio.wait_for(
            asyncpg.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', 5432)),
                database=os.getenv('POSTGRES_DB', 'DBSBM'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'password')
            ),
            timeout=10.0  # 10 second timeout
        )
        print("✅ Connection successful!")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_db_connection())
