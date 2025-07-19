#!/usr/bin/env python3
"""
Test UFC API functionality
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Prompt for API key if not found
if not API_KEY:
    API_KEY = input("🔑 Please enter your API-Sports API key: ").strip()
    if not API_KEY:
        print("❌ No API key provided. Exiting.")
        sys.exit(1)

async def test_ufc_api():
    """Test UFC API endpoint"""
    print("🥊 Testing UFC API...")
    
    if not API_KEY:
        print("❌ API_KEY not found in environment variables")
        return
    
    # UFC API endpoint
    url = "https://v1.mma.api-sports.io/fights"
    headers = {"x-apisports-key": API_KEY}
    
    # Test multiple date ranges to find UFC fights
    test_dates = [
        datetime.now().strftime("%Y-%m-%d"),  # Today
        (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),  # Next week
        (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),  # Next month
        "2024-12-14",  # Recent past date
    ]
    
    for test_date in test_dates:
        print(f"\n🔍 Testing date: {test_date}")
        params = {
            "league": 1,  # UFC league ID
            "season": 2024,  # Try 2024 season first
            "date": test_date
        }
        
        print(f"🔗 URL: {url}")
        print(f"📋 Params: {params}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    print(f"📊 Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ API Response received")
                        print(f"📄 Response keys: {list(data.keys())}")
                        
                        if "response" in data:
                            fights = data["response"]
                            print(f"🥊 Found {len(fights)} UFC fights")
                            
                            if len(fights) > 0:
                                for i, fight in enumerate(fights[:3]):  # Show first 3 fights
                                    print(f"\n--- Fight {i+1} ---")
                                    print(f"ID: {fight.get('id')}")
                                    print(f"Date: {fight.get('date')}")
                                    
                                    # Get fighter names
                                    teams = fight.get('teams', {})
                                    home = teams.get('home', {})
                                    away = teams.get('away', {})
                                    print(f"Fighters: {home.get('name', 'Unknown')} vs {away.get('name', 'Unknown')}")
                                    
                                    # Get status
                                    status = fight.get('status', {})
                                    print(f"Status: {status.get('long', 'Unknown')}")
                                    
                                    # Get venue
                                    venue = fight.get('venue', {})
                                    print(f"Venue: {venue.get('name', 'Unknown')}")
                            else:
                                print("📅 No fights found for this date")
                        else:
                            print("❌ No 'response' key in API response")
                            print(f"📄 Full response: {data}")
                            
                    elif response.status == 429:
                        print("⚠️ Rate limit exceeded")
                        await asyncio.sleep(2)  # Wait before next request
                    else:
                        error_text = await response.text()
                        print(f"❌ API Error: {error_text}")
                    
                    # Small delay between requests
                    await asyncio.sleep(1)
                    
        except Exception as e:
            print(f"❌ Error testing UFC API: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🥊 UFC API Test")
    print("=" * 50)
    asyncio.run(test_ufc_api()) 