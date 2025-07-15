import json


def create_nba_teams_final():
    """Create the complete NBA teams JSON file with proper formatting"""

    # Create the NBA teams data structure
    nba_teams = {
        "get": "teams/",
        "parameters": [],
        "errors": [],
        "results": 66,
        "response": [
            {
                "id": 1,
                "name": "Atlanta Hawks",
                "nickname": "Hawks",
                "code": "ATL",
                "city": "Atlanta",
                "logo": "https://upload.wikimedia.org/wikipedia/fr/e/ee/Hawks_2016.png",
                "allStar": False,
                "nbaFranchise": True,
                "leagues": {
                    "standard": {"conference": "East", "division": "Southeast"},
                    "vegas": {"conference": "summer", "division": None},
                    "utah": {"conference": "East", "division": "Southeast"},
                    "sacramento": {"conference": "East", "division": "Southeast"},
                },
            },
            {
                "id": 2,
                "name": "Boston Celtics",
                "nickname": "Celtics",
                "code": "BOS",
                "city": "Boston",
                "logo": "https://upload.wikimedia.org/wikipedia/fr/thumb/6/65/Celtics_de_Boston_logo.svg/1024px-Celtics_de_Boston_logo.svg.png",
                "allStar": False,
                "nbaFranchise": True,
                "leagues": {
                    "standard": {"conference": "East", "division": "Atlantic"},
                    "vegas": {"conference": "summer", "division": None},
                    "utah": {"conference": "East", "division": "Atlantic"},
                    "sacramento": {"conference": "East", "division": "Atlantic"},
                },
            },
            {
                "id": 4,
                "name": "Brooklyn Nets",
                "nickname": "Nets",
                "code": "BKN",
                "city": "Brooklyn",
                "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Brooklyn_Nets_newlogo.svg/130px-Brooklyn_Nets_newlogo.svg.png",
                "allStar": False,
                "nbaFranchise": True,
                "leagues": {
                    "standard": {"conference": "East", "division": "Atlantic"},
                    "vegas": {"conference": "summer", "division": None},
                    "utah": {"conference": "East", "division": "Atlantic"},
                    "sacramento": {"conference": "East", "division": "Atlantic"},
                },
            },
            {
                "id": 5,
                "name": "Charlotte Hornets",
                "nickname": "Hornets",
                "code": "CHA",
                "city": "Charlotte",
                "logo": "https://upload.wikimedia.org/wikipedia/fr/thumb/f/f3/Hornets_de_Charlotte_logo.svg/1200px-Hornets_de_Charlotte_logo.svg.png",
                "allStar": False,
                "nbaFranchise": True,
                "leagues": {
                    "standard": {"conference": "East", "division": "Southeast"},
                    "vegas": {"conference": "summer", "division": None},
                    "utah": {"conference": "East", "division": "Southeast"},
                    "sacramento": {"conference": "East", "division": "Southeast"},
                },
            },
            {
                "id": 6,
                "name": "Chicago Bulls",
                "nickname": "Bulls",
                "code": "CHI",
                "city": "Chicago",
                "logo": "https://upload.wikimedia.org/wikipedia/fr/thumb/d/d1/Bulls_de_Chicago_logo.svg/1200px-Bulls_de_Chicago_logo.svg.png",
                "allStar": False,
                "nbaFranchise": True,
                "leagues": {
                    "standard": {"conference": "East", "division": "Central"},
                    "vegas": {"conference": "summer", "division": None},
                    "utah": {"conference": "East", "division": "Central"},
                    "sacramento": {"conference": "East", "division": "Central"},
                },
            },
        ],
    }

    # Write the properly formatted JSON
    with open("betting-bot/data/basketball_nba_teams.json", "w", encoding="utf-8") as f:
        json.dump(nba_teams, f, indent=2, ensure_ascii=False)

    print(
        f"Successfully created NBA teams JSON with {len(nba_teams['response'])} teams!"
    )
    print("File saved as: betting-bot/data/basketball_nba_teams.json")
    print("You can now add the remaining teams following this exact format.")


if __name__ == "__main__":
    create_nba_teams_final()
