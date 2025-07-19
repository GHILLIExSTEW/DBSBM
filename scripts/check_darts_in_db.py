#!/usr/bin/env python3
"""
Check if darts games are in the database.
"""

import asyncio
import logging
import sys
import os

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiomysql

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_db_pool() -> aiomysql.Pool:
    """Set up and return a MySQL connection pool."""
    try:
        logger.info("Creating MySQL connection pool...")
        pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            db=os.getenv("MYSQL_DB"),
            minsize=1,
            maxsize=5,
            autocommit=True,
        )
        logger.info("MySQL connection pool created successfully")
        return pool
    except Exception as e:
        logger.error(f"Failed to create MySQL connection pool: {e}")
        raise


async def check_darts_in_db():
    """Check if darts games are in the database."""
    logger.info("Checking for darts games in database...")
    
    pool = None
    try:
        pool = await setup_db_pool()
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Check total games
                await cur.execute("SELECT COUNT(*) FROM api_games")
                total_games = await cur.fetchone()
                logger.info(f"Total games in database: {total_games[0]}")
                
                # Check darts games
                await cur.execute("SELECT COUNT(*) FROM api_games WHERE sport = 'Darts'")
                darts_games = await cur.fetchone()
                logger.info(f"Darts games in database: {darts_games[0]}")
                
                # Check tennis games
                await cur.execute("SELECT COUNT(*) FROM api_games WHERE sport = 'Tennis'")
                tennis_games = await cur.fetchone()
                logger.info(f"Tennis games in database: {tennis_games[0]}")
                
                # Check golf games
                await cur.execute("SELECT COUNT(*) FROM api_games WHERE sport = 'Golf'")
                golf_games = await cur.fetchone()
                logger.info(f"Golf games in database: {golf_games[0]}")
                
                # Check esports games
                await cur.execute("SELECT COUNT(*) FROM api_games WHERE sport = 'Esports'")
                esports_games = await cur.fetchone()
                logger.info(f"Esports games in database: {esports_games[0]}")
                
                # Show sample darts games
                await cur.execute("""
                    SELECT api_game_id, home_team_name, away_team_name, start_time, league_name 
                    FROM api_games 
                    WHERE sport = 'Darts' 
                    ORDER BY start_time DESC 
                    LIMIT 10
                """)
                sample_darts = await cur.fetchall()
                logger.info("Sample darts games:")
                for game in sample_darts:
                    logger.info(f"  {game[0]}: {game[1]} vs {game[2]} ({game[3]}) - {game[4]}")
                
                # Show all sports in database
                await cur.execute("SELECT DISTINCT sport, COUNT(*) FROM api_games GROUP BY sport ORDER BY COUNT(*) DESC")
                sports_count = await cur.fetchall()
                logger.info("All sports in database:")
                for sport, count in sports_count:
                    logger.info(f"  {sport}: {count} games")
                
    except Exception as e:
        logger.error(f"Error checking database: {e}", exc_info=True)
    finally:
        if pool:
            pool.close()
            await pool.wait_closed()


if __name__ == "__main__":
    asyncio.run(check_darts_in_db()) 