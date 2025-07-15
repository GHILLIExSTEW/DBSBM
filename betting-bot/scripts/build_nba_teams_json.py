import json
import re


def build_nba_teams_json():
    """Build the NBA teams JSON file from the template data"""

    # Read the template file
    with open(
        "betting-bot/data/basketball_nba_teams_template.json", "r", encoding="utf-8"
    ) as f:
        content = f.read()

    # Extract team blocks using a more specific pattern
    # Look for blocks that start with { and contain id and name
    team_pattern = r"\{\s*id:\s*\d+[^}]+\}"
    team_blocks = re.findall(team_pattern, content, re.DOTALL)

    teams = []
    for block in team_blocks:
        try:
            # Clean up the block
            # Add quotes around property names
            block = re.sub(r"(\s+)(\w+):", r'\1"\2":', block)

            # Add commas between properties
            block = re.sub(r'"(false|true|null)"\s*\n\s*"', r'"\1",\n    "', block)
            block = re.sub(r'"(false|true|null)"\s*\n\s*\}', r'"\1"\n  }', block)

            # Parse the team object
            team_data = json.loads(block)
            if "id" in team_data and "name" in team_data:
                teams.append(team_data)

        except Exception as e:
            print(f"Failed to parse team block: {e}")
            continue

    # Create the final JSON structure
    nba_teams = {
        "get": "teams/",
        "parameters": [],
        "errors": [],
        "results": len(teams),
        "response": teams,
    }

    # Write the properly formatted JSON
    with open("betting-bot/data/basketball_nba_teams.json", "w", encoding="utf-8") as f:
        json.dump(nba_teams, f, indent=2, ensure_ascii=False)

    print(f"Successfully built NBA teams JSON with {len(teams)} teams!")
    print("File saved as: betting-bot/data/basketball_nba_teams.json")


if __name__ == "__main__":
    build_nba_teams_json()
