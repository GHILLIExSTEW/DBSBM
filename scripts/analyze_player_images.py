#!/usr/bin/env python3
"""
Analyze player images in logos folder and compare to team rosters.
Shows missing player images broken down by league and team.
"""

import os
import csv
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_logos_folder():
    """Analyze the logos folder structure and count player images."""
    logos_base = "bot/static/logos/players"
    sport_folders = {}
    
    if not os.path.exists(logos_base):
        logger.error(f"Logos folder not found: {logos_base}")
        return {}
    
    # Analyze each sport folder
    for sport in os.listdir(logos_base):
        sport_path = os.path.join(logos_base, sport)
        if os.path.isdir(sport_path):
            team_counts = {}
            total_players = 0
            
            # Count teams and players in each sport
            for team in os.listdir(sport_path):
                team_path = os.path.join(sport_path, team)
                if os.path.isdir(team_path):
                    # Count PNG files (player images)
                    player_images = [f for f in os.listdir(team_path) if f.endswith('.png')]
                    team_counts[team] = len(player_images)
                    total_players += len(player_images)
            
            sport_folders[sport] = {
                'teams': team_counts,
                'total_players': total_players,
                'total_teams': len(team_counts)
            }
    
    return sport_folders

def analyze_player_csv():
    """Analyze the player CSV to get team rosters."""
    csv_path = "bot/data/players.csv"
    if not os.path.exists(csv_path):
        logger.error(f"Player CSV not found: {csv_path}")
        return {}
    
    team_rosters = defaultdict(list)
    league_teams = defaultdict(set)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            player_name = row.get('name', '')
            team_name = row.get('team', '')
            league = row.get('league', '')
            sport = row.get('sport', '')
            
            if team_name and player_name:
                # Normalize team name for comparison - more aggressive normalization
                normalized_team = team_name.lower()
                normalized_team = normalized_team.replace(' ', '_').replace('-', '_')
                normalized_team = normalized_team.replace('.', '').replace(',', '')
                normalized_team = normalized_team.replace('fc_', '').replace('_fc', '')
                normalized_team = normalized_team.replace('united', 'utd')
                normalized_team = normalized_team.replace('real_madrid', 'real_madrid')
                normalized_team = normalized_team.replace('bayern_munich', 'bayern_münchen')
                normalized_team = normalized_team.replace('bayern_münchen', 'bayern_münchen')
                
                team_rosters[normalized_team].append(player_name)
                league_teams[league].add(normalized_team)
    
    return dict(team_rosters), dict(league_teams)

def compare_images_to_rosters(logos_data, roster_data):
    """Compare available images to team rosters."""
    team_rosters, league_teams = roster_data
    missing_analysis = defaultdict(lambda: defaultdict(dict))
    
    # Debug: Print some team names to see the matching
    print("DEBUG: Sample team names from logos:")
    for sport, sport_data in logos_data.items():
        for team_name in list(sport_data['teams'].keys())[:3]:
            print(f"  {sport}: {team_name}")
    
    print("\nDEBUG: Sample team names from CSV:")
    for team_name in list(team_rosters.keys())[:10]:
        print(f"  {team_name}")
    
    for sport, sport_data in logos_data.items():
        for team_name, image_count in sport_data['teams'].items():
            # Try to find matching team in roster
            roster_count = 0
            matched_team = None
            
            # Direct match
            if team_name in team_rosters:
                roster_count = len(team_rosters[team_name])
                matched_team = team_name
            else:
                # Try variations
                for csv_team, players in team_rosters.items():
                    if (team_name in csv_team or csv_team in team_name or 
                        team_name.replace('_', '') == csv_team.replace('_', '')):
                        roster_count = len(players)
                        matched_team = csv_team
                        break
            
            if roster_count > 0:
                missing_count = max(0, roster_count - image_count)
                if missing_count > 0:
                    missing_analysis[sport][team_name] = {
                        'available_images': image_count,
                        'roster_size': roster_count,
                        'missing_images': missing_count,
                        'matched_csv_team': matched_team
                    }
    
    return missing_analysis

def generate_report(logos_data, roster_data, missing_analysis):
    """Generate a comprehensive report."""
    team_rosters, league_teams = roster_data
    
    print("=" * 80)
    print("PLAYER IMAGE ANALYSIS REPORT")
    print("=" * 80)
    
    # Overall statistics
    total_images = sum(sport['total_players'] for sport in logos_data.values())
    total_teams_with_images = sum(sport['total_teams'] for sport in logos_data.values())
    
    print(f"\nOVERALL STATISTICS:")
    print(f"Total player images available: {total_images}")
    print(f"Total teams with images: {total_teams_with_images}")
    print(f"Sports covered: {len(logos_data)}")
    
    # Breakdown by sport
    print(f"\nBREAKDOWN BY SPORT:")
    print("-" * 60)
    for sport, sport_data in logos_data.items():
        print(f"{sport.upper()}:")
        print(f"  Teams with images: {sport_data['total_teams']}")
        print(f"  Total player images: {sport_data['total_players']}")
        
        # Show teams with missing images
        if sport in missing_analysis:
            missing_teams = missing_analysis[sport]
            if missing_teams:
                print(f"  Teams with missing images: {len(missing_teams)}")
                total_missing = sum(team['missing_images'] for team in missing_teams.values())
                print(f"  Total missing images: {total_missing}")
                
                # Show top 5 teams with most missing images
                sorted_teams = sorted(missing_teams.items(), 
                                    key=lambda x: x[1]['missing_images'], 
                                    reverse=True)[:5]
                print(f"  Top teams missing images:")
                for team, data in sorted_teams:
                    print(f"    {team}: {data['missing_images']} missing "
                          f"({data['available_images']}/{data['roster_size']})")
        print()
    
    # Save detailed results to file
    with open('reports/detailed_player_image_analysis.md', 'w', encoding='utf-8') as f:
        f.write("# Detailed Player Image Analysis\n\n")
        
        # Overall stats
        f.write(f"## Overall Statistics\n")
        f.write(f"- Total player images available: {total_images}\n")
        f.write(f"- Total teams with images: {total_teams_with_images}\n")
        f.write(f"- Sports covered: {len(logos_data)}\n\n")
        
        # Sport breakdown
        f.write("## Breakdown by Sport\n\n")
        for sport, sport_data in logos_data.items():
            f.write(f"### {sport.upper()}\n")
            f.write(f"- Teams with images: {sport_data['total_teams']}\n")
            f.write(f"- Total player images: {sport_data['total_players']}\n")
            
            if sport in missing_analysis and missing_analysis[sport]:
                missing_teams = missing_analysis[sport]
                total_missing = sum(team['missing_images'] for team in missing_teams.values())
                f.write(f"- Teams with missing images: {len(missing_teams)}\n")
                f.write(f"- Total missing images: {total_missing}\n\n")
                
                f.write("#### Teams with Missing Images:\n")
                for team, data in sorted(missing_teams.items(), 
                                       key=lambda x: x[1]['missing_images'], 
                                       reverse=True):
                    f.write(f"- **{team}**: {data['missing_images']} missing "
                           f"({data['available_images']}/{data['roster_size']})\n")
            f.write("\n")
        
        # League breakdown
        f.write("## Detailed Missing Analysis by League\n\n")
        for league, teams in league_teams.items():
            if not league:
                continue
                
            league_missing = []
            for team in teams:
                # Find which sport this team belongs to
                for sport, sport_data in logos_data.items():
                    if team in sport_data['teams']:
                        if sport in missing_analysis and team in missing_analysis[sport]:
                            missing_data = missing_analysis[sport][team]
                            league_missing.append((team, missing_data))
                        break
            
            if league_missing:
                total_missing = sum(data['missing_images'] for _, data in league_missing)
                f.write(f"### {league.upper()}\n")
                f.write(f"- Total missing images: {total_missing}\n")
                f.write(f"- Teams with missing images: {len(league_missing)}\n\n")
                
                # Show teams with missing images
                for team, data in sorted(league_missing, key=lambda x: x[1]['missing_images'], reverse=True):
                    f.write(f"- **{team}**: {data['missing_images']} missing "
                           f"({data['available_images']}/{data['roster_size']})\n")
                f.write("\n")
    
    print(f"\nDetailed report saved to: reports/detailed_player_image_analysis.md")
    
    # Show summary of missing images by league
    print(f"\nSUMMARY OF MISSING IMAGES BY LEAGUE:")
    print("=" * 80)
    
    league_summary = defaultdict(int)
    for league, teams in league_teams.items():
        if not league:
            continue
            
        for team in teams:
            for sport, sport_data in logos_data.items():
                if team in sport_data['teams']:
                    if sport in missing_analysis and team in missing_analysis[sport]:
                        missing_data = missing_analysis[sport][team]
                        league_summary[league] += missing_data['missing_images']
                    break
    
    # Show top leagues with most missing images
    sorted_leagues = sorted(league_summary.items(), key=lambda x: x[1], reverse=True)
    for league, missing_count in sorted_leagues[:20]:  # Top 20 leagues
        print(f"{league}: {missing_count} missing images")

def main():
    """Main function."""
    logger.info("Analyzing logos folder...")
    logos_data = analyze_logos_folder()
    
    logger.info("Analyzing player CSV...")
    roster_data = analyze_player_csv()
    
    logger.info("Comparing images to rosters...")
    missing_analysis = compare_images_to_rosters(logos_data, roster_data)
    
    logger.info("Generating report...")
    generate_report(logos_data, roster_data, missing_analysis)

if __name__ == "__main__":
    main() 