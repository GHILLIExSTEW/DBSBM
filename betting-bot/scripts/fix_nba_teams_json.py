import json
import re

INPUT_PATH = "betting-bot/data/basketball_nba_teams.json"
OUTPUT_PATH = "betting-bot/data/basketball_nba_teams.json"


def fix_nba_teams_json():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Add quotes around property names
    content = re.sub(r"([,{\s])(\w+):", r'\1"\2":', content)
    # Add commas between objects in the response array
    content = re.sub(r"}\s*{", "},\n{", content)
    # Add commas between top-level keys
    content = re.sub(r'"\]\s*"', '"],\n"', content)
    # Remove trailing commas before closing brackets
    content = re.sub(r",\s*([}\]])", r"\1", content)

    # Try to parse and pretty-print
    try:
        data = json.loads(content)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Fixed and formatted {OUTPUT_PATH} successfully!")
    except Exception as e:
        print(f"Failed to fix JSON: {e}")


if __name__ == "__main__":
    fix_nba_teams_json()
