import requests
import json
import os
from datetime import datetime

def fetch_nba_teams():
    """Fetch NBA teams from API-Sports and save the response"""
    
    # Get API key from environment
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        API_KEY = input("Enter your API-Sports key: ").strip()
    
    # Remove "API_KEY=" prefix if present
    if API_KEY.startswith("API_KEY="):
        API_KEY = API_KEY[8:]
    
    # API endpoint
    url = "https://v2.nba.api-sports.io/teams"
    
    # Headers
    headers = {
        "x-apisports-key": API_KEY
    }
    
    print(f"Fetching NBA teams from: {url}")
    print(f"Using API key: {API_KEY[:10]}...")
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Save to file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"betting-bot/data/basketball_nba_teams_api_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Successfully saved NBA teams data to: {filename}")
            
            # Also save to the main file
            main_filename = "betting-bot/data/basketball_nba_teams.json"
            with open(main_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Also saved to main file: {main_filename}")
            
            # Show some info about the response
            if 'response' in data:
                print(f"📊 Found {len(data['response'])} teams in the response")
                if data['response']:
                    print(f"📋 First team: {data['response'][0].get('name', 'Unknown')}")
            
            return data
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response text: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching NBA teams: {e}")
        return None

if __name__ == "__main__":
    fetch_nba_teams() 