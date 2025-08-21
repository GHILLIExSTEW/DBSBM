#!/usr/bin/env python3
"""
Simple PostgreSQL connection test
"""
import asyncio
import pytest
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.mark.asyncio
async def test_postgres_connection():
    """Test PostgreSQL connection with current .env settings"""
    print("🔄 Testing PostgreSQL connection...")
    
    db_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", 5432)),
        "database": os.getenv("POSTGRES_DB", "dbsbm"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }
    
    print(f"📊 Connection details:")
    print(f"   Host: {db_config['host']}")
    print(f"   Port: {db_config['port']}")
    print(f"   Database: {db_config['database']}")
    print(f"   User: {db_config['user']}")
    print(f"   Password: {'*' * len(db_config['password'])}")
    
    try:
        # Test connection
        print("🔗 Attempting connection...")
        connection = await asyncpg.connect(**db_config)
        
        # Test query
        print("✅ Connection successful! Testing query...")
        result = await connection.fetchval("SELECT version()")
        print(f"📊 PostgreSQL Version: {result}")
        
        # Test table query
        tables = await connection.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            LIMIT 5
        """)
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        await connection.close()
        print("✅ PostgreSQL connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_postgres_connection())
