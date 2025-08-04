import asyncpg
import asyncio

async def check_guild_data():
    try:
        conn = await asyncpg.connect('postgresql://postgres:password@localhost/DBSBM')
        
        # Check guild_settings table
        settings_count = await conn.fetchval("SELECT COUNT(*) FROM guild_settings")
        print(f'guild_settings table has {settings_count} rows')
        
        if settings_count > 0:
            settings = await conn.fetch("SELECT guild_id, guild_name, subscription_level, is_active FROM guild_settings LIMIT 5")
            print('Sample guild_settings:')
            for s in settings:
                print(f'  Guild ID: {s[0]}, Name: {s[1]}, Level: {s[2]}, Active: {s[3]}')
        else:
            print('❌ No guild settings found!')
            print('This means the bot has no guild configurations.')
            
        # Check if there are any guild IDs referenced in bets table
        bet_guilds = await conn.fetch("SELECT DISTINCT guild_id FROM bets WHERE guild_id IS NOT NULL LIMIT 5")
        if bet_guilds:
            print(f'\nGuild IDs found in bets table: {len(bet_guilds)} unique')
            for guild in bet_guilds:
                print(f'  Guild ID from bets: {guild[0]}')
                
        # Check the test guild from .env
        test_guild_id = 1328116926903353398  # Updated TEST_GUILD_ID
        test_guild = await conn.fetchrow("SELECT guild_id, guild_name, subscription_level, is_active FROM guild_settings WHERE guild_id = $1", test_guild_id)
        print(f'\nTest Guild ID (from .env): {test_guild_id}')
        if test_guild:
            print(f'✅ Test guild found: {test_guild[1]}, Level: {test_guild[2]}, Active: {test_guild[3]}')
        else:
            print('❌ Test guild NOT found in database!')
            print('This explains why the bot may not work - it\'s configured for a guild that has no data.')
                
        await conn.close()
        print('\nGuild data check complete!')
        
    except Exception as e:
        print(f'Database connection error: {e}')

if __name__ == '__main__':
    asyncio.run(check_guild_data())
