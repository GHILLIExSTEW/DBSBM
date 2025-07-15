import json
import re


def manual_fix_nba_json():
    """Manually fix the NBA teams JSON by parsing the malformed content"""

    # Read the original malformed file
    with open("bot/data/basketball_nba_teams.json", "r", encoding="utf-8") as f:
        content = f.read()

    # Find all team blocks (from { to })
    team_blocks = re.findall(r"\{[^}]+\}", content)

    teams = []
    for block in team_blocks:
        # Skip empty or malformed blocks
        if len(block) < 10:
            continue

        # Add quotes around property names
        block = re.sub(r"(\s+)(\w+):", r'\1"\2":', block)

        # Add commas between properties
        block = re.sub(r'"(false|true|null)"\s*\n\s*"', r'"\1",\n    "', block)
        block = re.sub(r'"(false|true|null)"\s*\n\s*\}', r'"\1"\n  }', block)

        # Try to parse as JSON
        try:
            team_data = json.loads(block)
            if "id" in team_data and "name" in team_data:
                teams.append(team_data)
        except:
            continue

    # Create the proper JSON structure
    result = {
        "get": "teams/",
        "parameters": [],
        "errors": [],
        "results": len(teams),
        "response": teams,
    }

    # Write the fixed file
    with open("bot/data/basketball_nba_teams.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Successfully fixed NBA teams JSON with {len(teams)} teams!")


if __name__ == "__main__":
    manual_fix_nba_json()
