#!/usr/bin/env python3
"""
Query UFC fighters from the database and analyze the data
"""
import os
import json
import asyncio
import aiomysql
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

async def query_ufc_fighters():
    """Query UFC fighters from the database"""
    
    # Database connection
    pool = await aiomysql.create_pool(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        db=os.getenv("MYSQL_DB"),
        autocommit=True,
    )
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                
                # Query 1: Get all UFC games/fights
                print("=== UFC Fights in Database ===")
                await cur.execute("""
                    SELECT 
                        id, api_game_id, home_team_name, away_team_name, 
                        start_time, status, venue, referee,
                        fetched_at
                    FROM api_games 
                    WHERE sport = 'Mma' AND league_name = 'UFC'
                    ORDER BY start_time DESC
                    LIMIT 20
                """)
                
                ufc_fights = await cur.fetchall()
                print(f"Found {len(ufc_fights)} UFC fights in database")
                
                for fight in ufc_fights:
                    print(f"Fight ID: {fight[0]}")
                    print(f"  Home: {fight[2]}")
                    print(f"  Away: {fight[3]}")
                    print(f"  Date: {fight[4]}")
                    print(f"  Status: {fight[5]}")
                    print(f"  Venue: {fight[6]}")
                    print(f"  Referee: {fight[7]}")
                    print()
                
                # Query 2: Get unique fighters
                print("=== Unique UFC Fighters ===")
                await cur.execute("""
                    SELECT DISTINCT home_team_name as fighter_name
                    FROM api_games 
                    WHERE sport = 'Mma' AND league_name = 'UFC'
                    UNION
                    SELECT DISTINCT away_team_name as fighter_name
                    FROM api_games 
                    WHERE sport = 'Mma' AND league_name = 'UFC'
                    ORDER BY fighter_name
                """)
                
                fighters = await cur.fetchall()
                print(f"Found {len(fighters)} unique UFC fighters")
                
                # Show first 20 fighters
                print("First 20 fighters:")
                for i, fighter in enumerate(fighters[:20]):
                    print(f"  {i+1}. {fighter[0]}")
                
                if len(fighters) > 20:
                    print(f"  ... and {len(fighters) - 20} more")
                
                # Query 3: Check for retirement status in raw JSON
                print("\n=== Checking for Retirement Status in Raw Data ===")
                await cur.execute("""
                    SELECT home_team_name, away_team_name, raw_json
                    FROM api_games 
                    WHERE sport = 'Mma' AND league_name = 'UFC'
                    LIMIT 5
                """)
                
                raw_data_samples = await cur.fetchall()
                print(f"Analyzing {len(raw_data_samples)} sample fights for retirement info...")
                
                for sample in raw_data_samples:
                    home_fighter = sample[0]
                    away_fighter = sample[1]
                    raw_json = sample[2]
                    
                    try:
                        data = json.loads(raw_json)
                        print(f"\nFight: {home_fighter} vs {away_fighter}")
                        
                        # Look for retirement-related fields
                        retirement_indicators = []
                        
                        # Check teams data
                        if 'teams' in data:
                            for team in data['teams']:
                                if 'home' in team:
                                    home_team = team['home']
                                    if isinstance(home_team, dict):
                                        for key, value in home_team.items():
                                            if 'retire' in str(key).lower() or 'status' in str(key).lower():
                                                retirement_indicators.append(f"Home {key}: {value}")
                                
                                if 'away' in team:
                                    away_team = team['away']
                                    if isinstance(away_team, dict):
                                        for key, value in away_team.items():
                                            if 'retire' in str(key).lower() or 'status' in str(key).lower():
                                                retirement_indicators.append(f"Away {key}: {value}")
                        
                        # Check for any retirement-related fields in the entire JSON
                        def search_for_retirement(obj, path=""):
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    current_path = f"{path}.{key}" if path else key
                                    if 'retire' in str(key).lower() or 'status' in str(key).lower():
                                        retirement_indicators.append(f"{current_path}: {value}")
                                    search_for_retirement(value, current_path)
                            elif isinstance(obj, list):
                                for i, item in enumerate(obj):
                                    current_path = f"{path}[{i}]"
                                    search_for_retirement(item, current_path)
                        
                        search_for_retirement(data)
                        
                        if retirement_indicators:
                            print("  Retirement indicators found:")
                            for indicator in retirement_indicators:
                                print(f"    {indicator}")
                        else:
                            print("  No retirement indicators found in raw data")
                            
                    except json.JSONDecodeError:
                        print(f"  Error parsing JSON for {home_fighter} vs {away_fighter}")
                
                # Query 4: Check recent activity
                print("\n=== Recent Fighter Activity ===")
                await cur.execute("""
                    SELECT 
                        home_team_name as fighter,
                        COUNT(*) as fights,
                        MAX(start_time) as last_fight,
                        MIN(start_time) as first_fight
                    FROM api_games 
                    WHERE sport = 'Mma' AND league_name = 'UFC'
                    GROUP BY home_team_name
                    ORDER BY last_fight DESC
                    LIMIT 10
                """)
                
                recent_activity = await cur.fetchall()
                print("Most recently active fighters:")
                for fighter in recent_activity:
                    print(f"  {fighter[0]}: {fighter[1]} fights, last: {fighter[2]}")
                
                # Query 5: Check for inactive fighters (no fights in last 2 years)
                print("\n=== Potentially Inactive Fighters ===")
                await cur.execute("""
                    SELECT 
                        home_team_name as fighter,
                        COUNT(*) as total_fights,
                        MAX(start_time) as last_fight
                    FROM api_games 
                    WHERE sport = 'Mma' AND league_name = 'UFC'
                    GROUP BY home_team_name
                    HAVING last_fight < DATE_SUB(NOW(), INTERVAL 2 YEAR)
                    ORDER BY last_fight DESC
                    LIMIT 10
                """)
                
                inactive_fighters = await cur.fetchall()
                print("Fighters with no fights in last 2 years (potentially retired):")
                for fighter in inactive_fighters:
                    print(f"  {fighter[0]}: {fighter[1]} fights, last: {fighter[2]}")
                
    finally:
        pool.close()
        await pool.wait_closed()

if __name__ == "__main__":
    asyncio.run(query_ufc_fighters()) 