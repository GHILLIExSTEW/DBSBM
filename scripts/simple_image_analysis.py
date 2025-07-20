#!/usr/bin/env python3
"""
Simple analysis of player images vs roster sizes.
"""

import os
import csv
from collections import defaultdict

def count_images_by_team():
    """Count player images for each team."""
    logos_base = "bot/static/logos/players"
    team_images = {}
    
    for sport in os.listdir(logos_base):
        sport_path = os.path.join(logos_base, sport)
        if os.path.isdir(sport_path):
            for team in os.listdir(sport_path):
                team_path = os.path.join(sport_path, team)
                if os.path.isdir(team_path):
                    # Count PNG files
                    player_images = [f for f in os.listdir(team_path) if f.endswith('.png')]
                    team_images[team] = len(player_images)
    
    return team_images

def count_players_by_team():
    """Count players for each team from CSV."""
    csv_path = "bot/data/players.csv"
    team_players = defaultdict(int)
    team_leagues = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = row.get('strTeam', '')
            league = row.get('strLeague', '')
            player = row.get('strPlayer', '')
            if team and player:
                team_players[team] += 1
                team_leagues[team] = league
    
    return dict(team_players), team_leagues

def main():
    """Main analysis."""
    print("=" * 80)
    print("PLAYER IMAGE ANALYSIS - SIMPLE VERSION")
    print("=" * 80)
    
    # Count images
    team_images = count_images_by_team()
    total_images = sum(team_images.values())
    print(f"\nTotal player images available: {total_images}")
    print(f"Teams with images: {len(team_images)}")
    
    # Count players
    team_players, team_leagues = count_players_by_team()
    total_players = sum(team_players.values())
    print(f"Total players in database: {total_players}")
    print(f"Teams in database: {len(team_players)}")
    
    # Find teams with images and compare
    teams_with_images = set(team_images.keys())
    teams_in_db = set(team_players.keys())
    
    # Normalize team names for comparison
    normalized_images = {team.lower().replace(' ', '_').replace('-', '_') for team in teams_with_images}
    normalized_db = {team.lower().replace(' ', '_').replace('-', '_') for team in teams_in_db}
    
    # Find matches
    matches = []
    for img_team in teams_with_images:
        img_normalized = img_team.lower().replace(' ', '_').replace('-', '_')
        for db_team in teams_in_db:
            db_normalized = db_team.lower().replace(' ', '_').replace('-', '_')
            if img_normalized == db_normalized:
                matches.append((img_team, db_team, team_images[img_team], team_players[db_team]))
                break
    
    print(f"\nTeams with both images and database entries: {len(matches)}")
    
    # Calculate missing images
    total_missing = 0
    missing_by_league = defaultdict(int)
    
    print(f"\nDETAILED BREAKDOWN BY TEAM:")
    print("-" * 80)
    
    for img_team, db_team, img_count, player_count in matches:
        missing = max(0, player_count - img_count)
        total_missing += missing
        league = team_leagues.get(db_team, 'Unknown')
        missing_by_league[league] += missing
        
        if missing > 0:
            print(f"{db_team} ({league}): {missing} missing ({img_count}/{player_count})")
    
    print(f"\nSUMMARY BY LEAGUE:")
    print("-" * 80)
    for league, missing in sorted(missing_by_league.items(), key=lambda x: x[1], reverse=True):
        if missing > 0:
            print(f"{league}: {missing} missing images")
    
    print(f"\nTOTAL MISSING IMAGES: {total_missing}")

if __name__ == "__main__":
    main() 