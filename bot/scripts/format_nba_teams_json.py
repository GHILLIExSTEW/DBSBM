import json

INPUT_PATH = "bot/data/basketball_nba_teams.json"
OUTPUT_PATH = "bot/data/basketball_nba_teams.json"


def format_nba_teams_json():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Formatted {OUTPUT_PATH} successfully!")


if __name__ == "__main__":
    format_nba_teams_json()
