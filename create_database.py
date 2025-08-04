import asyncpg
import asyncio

async def create_database():
    try:
        # Connect to default postgres database to create DBSBM
        conn = await asyncpg.connect(
            host='localhost',
            user='postgres', 
            password='password',
            database='postgres'  # Connect to default database first
        )
        
        # Check if DBSBM database exists
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'DBSBM'")
        
        if not exists:
            print("Creating DBSBM database...")
            await conn.execute('CREATE DATABASE "DBSBM"')
            print("✅ DBSBM database created successfully!")
        else:
            print("✅ DBSBM database already exists!")
            
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == '__main__':
    asyncio.run(create_database())
