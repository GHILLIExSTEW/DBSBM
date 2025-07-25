#!/usr/bin/env python3
"""
Summarize the generated teams and players CSV file.
"""

import csv
from collections import defaultdict


def summarize_csv(filename):
    """Summarize the CSV file contents."""
    leagues = set()
    teams = set()
    players = set()
    league_team_counts = defaultdict(int)
    league_player_counts = defaultdict(int)

    with open(filename, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            league = row["League"]
            team = row["Team"]
            player = row["Player"]

            leagues.add(league)
            teams.add((league, team))

            if player:  # Only count non-empty players
                players.add((league, team, player))
                league_player_counts[league] += 1

            league_team_counts[league] += 1

    print(f"CSV Summary for {filename}:")
    print(f"Total rows: {sum(league_team_counts.values())}")
    print(f"Unique leagues: {len(leagues)}")
    print(f"Unique teams: {len(teams)}")
    print(f"Unique players: {len(players)}")
    print()

    print("Leagues with most teams:")
    sorted_leagues = sorted(
        league_team_counts.items(), key=lambda x: x[1], reverse=True
    )
    for league, count in sorted_leagues[:10]:
        print(f"  {league}: {count} teams")

    print()
    print("Leagues with most players:")
    sorted_player_leagues = sorted(
        league_player_counts.items(), key=lambda x: x[1], reverse=True
    )
    for league, count in sorted_player_leagues[:10]:
        print(f"  {league}: {count} players")


if __name__ == "__main__":
    summarize_csv("teams_and_players_final.csv")
