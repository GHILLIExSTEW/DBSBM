import json
import re

def comprehensive_fix_nba_json():
    """Completely rebuild the NBA teams JSON file with proper structure"""
    
    # Read the malformed file
    with open('betting-bot/data/basketball_nba_teams.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract team objects using regex
    team_pattern = r'\{[^}]+\}'
    teams = re.findall(team_pattern, content)
    
    # Clean up each team object
    cleaned_teams = []
    for team in teams:
        # Add quotes around property names
        team = re.sub(r'(\s+)(\w+):', r'\1"\2":', team)
        # Add commas between properties
        team = re.sub(r'"(false|true|null)"\s*\n\s*"', r'"\1",\n    "', team)
        team = re.sub(r'"(false|true|null)"\s*\n\s*\}', r'"\1"\n  }', team)
        cleaned_teams.append(team)
    
    # Build the complete JSON structure
    json_structure = {
        "get": "teams/",
        "parameters": [],
        "errors": [],
        "results": len(cleaned_teams),
        "response": []
    }
    
    # Parse each team and add to response
    for team_str in cleaned_teams:
        try:
            # Try to parse the team object
            team_data = json.loads(team_str)
            json_structure["response"].append(team_data)
        except json.JSONDecodeError as e:
            print(f"Failed to parse team: {e}")
            print(f"Team string: {team_str[:100]}...")
            continue
    
    # Write the properly formatted JSON
    with open('betting-bot/data/basketball_nba_teams.json', 'w', encoding='utf-8') as f:
        json.dump(json_structure, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully fixed NBA teams JSON with {len(json_structure['response'])} teams!")

if __name__ == "__main__":
    comprehensive_fix_nba_json() 