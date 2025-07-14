import json

def rebuild_nba_teams():
    """Rebuild the NBA teams JSON file with proper structure"""
    
    # Start with the correct structure
    nba_teams = {
        "get": "teams/",
        "parameters": [],
        "errors": [],
        "results": 66,
        "response": []
    }
    
    # Add a sample team to show the structure
    sample_team = {
        "id": 1,
        "name": "Atlanta Hawks",
        "nickname": "Hawks",
        "code": "ATL",
        "city": "Atlanta",
        "logo": "https://upload.wikimedia.org/wikipedia/fr/e/ee/Hawks_2016.png",
        "allStar": False,
        "nbaFranchise": True,
        "leagues": {
            "standard": {
                "conference": "East",
                "division": "Southeast"
            },
            "vegas": {
                "conference": "summer",
                "division": None
            },
            "utah": {
                "conference": "East",
                "division": "Southeast"
            },
            "sacramento": {
                "conference": "East",
                "division": "Southeast"
            }
        }
    }
    
    nba_teams["response"].append(sample_team)
    
    # Write the file with the sample structure
    with open('betting-bot/data/basketball_nba_teams.json', 'w', encoding='utf-8') as f:
        json.dump(nba_teams, f, indent=2, ensure_ascii=False)
    
    print("Created NBA teams JSON file with sample structure.")
    print("You can now add all your team data following this format.")
    print("Make sure to:")
    print("1. Add quotes around all property names")
    print("2. Separate each team object with commas")
    print("3. Update the 'results' count to match your total teams")

if __name__ == "__main__":
    rebuild_nba_teams() 