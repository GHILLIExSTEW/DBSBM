import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables from bot/.env
env_path = os.path.join(os.path.dirname(__file__), 'bot', '.env')
load_dotenv(env_path)

async def test_connection():
    try:
        print("Testing PostgreSQL connection...")
        print(f"Loading .env from: {env_path}")
        print(f"Host: {os.getenv('POSTGRES_HOST')}")
        print(f"Port: {os.getenv('POSTGRES_PORT')}")
        print(f"User: {os.getenv('POSTGRES_USER')}")
        print(f"Database: {os.getenv('POSTGRES_DB')}")
        
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'password'),
            database='postgres'  # Try connecting to default postgres database first
        )
        
        # Test query
        result = await conn.fetchval('SELECT version()')
        print(f"✅ PostgreSQL connection successful!")
        print(f"Database version: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
