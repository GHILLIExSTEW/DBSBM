import json
from pathlib import Path

def load_sweden_league_names(json_path=Path('data/sweden_leagues_and_teams.json')):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            leagues = json.load(f)
        return [league['name'] for league in leagues if 'name' in league]
    except Exception as e:
        print(f"Failed to load league names: {e}")
        return [] 