import asyncio
import asyncpg
import os
from dotenv import load_dotenv

def main():
    # Load .env from the bot folder
    env_path = os.path.join(os.path.dirname(__file__), 'bot', '.env')
    load_dotenv(dotenv_path=env_path)
    async def check_api_games():
        pool = await asyncpg.create_pool(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host=os.getenv("POSTGRES_HOST"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
        )
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM api_games")
            print(f"api_games table row count: {count}")
            if count > 0:
                row = await conn.fetchrow("SELECT * FROM api_games LIMIT 1")
                print("Sample row:", dict(row))
        await pool.close()
    asyncio.run(check_api_games())

if __name__ == "__main__":
    main()
