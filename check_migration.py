import asyncpg
import asyncio

async def check_migration():
    try:
        conn = await asyncpg.connect('postgresql://postgres:password@localhost/DBSBM')
        
        # Get table count
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        print(f'PostgreSQL has {len(tables)} tables')
        
        # Check some key tables and their row counts
        key_tables = ['bets', 'games', 'teams', 'player_search_cache', 'bet_reactions', 'users', 'guilds']
        
        for table in key_tables:
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table}"')
                print(f'  {table}: {count} rows')
            except Exception as e:
                print(f'  {table}: Table not found or error - {e}')
        
        await conn.close()
        print('\nMigration check complete!')
        
    except Exception as e:
        print(f'Database connection error: {e}')

if __name__ == '__main__':
    asyncio.run(check_migration())
