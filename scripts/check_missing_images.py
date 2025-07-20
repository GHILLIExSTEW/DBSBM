#!/usr/bin/env python3
"""
Check which CSV players are missing local images.
"""

import os
import sys
import csv
from pathlib import Path
from typing import Dict, List, Set

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

def load_players_csv() -> List[Dict]:
    """Load all players from CSV."""
    players_file = Path(__file__).parent.parent / 'bot' / 'data' / 'players.csv'
    
    if not players_file.exists():
        print("❌ players.csv not found!")
        return []
    
    players = []
    try:
        with open(players_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                players.append(row)
        
        print(f"✅ Loaded {len(players)} players from CSV")
        return players
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return []

def check_image_exists(image_path: str) -> bool:
    """Check if a local image file exists."""
    if not image_path or image_path == '':
        return False
    
    # Convert relative path to absolute
    base_path = Path(__file__).parent.parent / 'bot'
    full_path = base_path / image_path
    
    return full_path.exists()

def analyze_missing_images():
    """Analyze which players are missing local images."""
    print("=" * 60)
    print("MISSING PLAYER IMAGES ANALYSIS")
    print("=" * 60)
    
    # Load players
    players = load_players_csv()
    
    if not players:
        return
    
    # Analyze by league
    leagues = {}
    missing_by_league = {}
    
    for player in players:
        league = player.get('strLeague', 'Unknown')
        team = player.get('strTeam', 'Unknown')
        player_name = player.get('strPlayer', 'Unknown')
        image_path = player.get('strCutouts', '')
        
        if league not in leagues:
            leagues[league] = {'total': 0, 'with_images': 0, 'missing': 0, 'teams': {}}
            missing_by_league[league] = []
        
        leagues[league]['total'] += 1
        
        if check_image_exists(image_path):
            leagues[league]['with_images'] += 1
        else:
            leagues[league]['missing'] += 1
            missing_by_league[league].append({
                'player': player_name,
                'team': team,
                'image_path': image_path
            })
        
        # Track by team
        if team not in leagues[league]['teams']:
            leagues[league]['teams'][team] = {'total': 0, 'with_images': 0, 'missing': 0}
        
        leagues[league]['teams'][team]['total'] += 1
        if check_image_exists(image_path):
            leagues[league]['teams'][team]['with_images'] += 1
        else:
            leagues[league]['teams'][team]['missing'] += 1
    
    # Print summary
    print("\nOVERALL SUMMARY:")
    print("-" * 40)
    total_players = sum(l['total'] for l in leagues.values())
    total_with_images = sum(l['with_images'] for l in leagues.values())
    total_missing = sum(l['missing'] for l in leagues.values())
    
    print(f"Total players: {total_players}")
    print(f"With images: {total_with_images}")
    print(f"Missing images: {total_missing}")
    print(f"Coverage: {(total_with_images/total_players*100):.1f}%")
    
    # Print by league
    print("\nBREAKDOWN BY LEAGUE:")
    print("-" * 40)
    
    for league, stats in sorted(leagues.items()):
        coverage = (stats['with_images'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"\n{league}:")
        print(f"  Total: {stats['total']}")
        print(f"  With images: {stats['with_images']}")
        print(f"  Missing: {stats['missing']}")
        print(f"  Coverage: {coverage:.1f}%")
        
        # Show teams with most missing
        teams_missing = [(team, data['missing']) for team, data in stats['teams'].items() if data['missing'] > 0]
        teams_missing.sort(key=lambda x: x[1], reverse=True)
        
        if teams_missing:
            print(f"  Top teams missing images:")
            for team, missing in teams_missing[:5]:
                print(f"    {team}: {missing} missing")
    
    # Show detailed missing players for priority leagues
    priority_leagues = ['NBA', 'MLB', 'NFL', 'NHL']
    
    print(f"\nDETAILED MISSING PLAYERS (Priority Leagues):")
    print("-" * 60)
    
    for league in priority_leagues:
        if league in missing_by_league and missing_by_league[league]:
            print(f"\n{league} - Missing {len(missing_by_league[league])} images:")
            
            # Group by team
            by_team = {}
            for item in missing_by_league[league]:
                team = item['team']
                if team not in by_team:
                    by_team[team] = []
                by_team[team].append(item['player'])
            
            for team, players in by_team.items():
                print(f"  {team}: {len(players)} missing")
                if len(players) <= 10:
                    for player in players:
                        print(f"    - {player}")
                else:
                    print(f"    - {', '.join(players[:5])}... and {len(players)-5} more")
    
    # Save detailed report
    report_file = Path(__file__).parent / 'missing_images_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("MISSING PLAYER IMAGES REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Total players: {total_players}\n")
        f.write(f"With images: {total_with_images}\n")
        f.write(f"Missing images: {total_missing}\n")
        f.write(f"Coverage: {(total_with_images/total_players*100):.1f}%\n\n")
        
        for league in priority_leagues:
            if league in missing_by_league and missing_by_league[league]:
                f.write(f"{league} - Missing {len(missing_by_league[league])} images:\n")
                for item in missing_by_league[league]:
                    f.write(f"  {item['player']} ({item['team']})\n")
                f.write("\n")
    
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    analyze_missing_images() 