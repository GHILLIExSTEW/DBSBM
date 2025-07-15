#!/usr/bin/env python3
"""
Script to update player search cache from players.csv
This will populate the database cache for enhanced player props
"""

import asyncio
import csv
import os
import sys
from datetime import datetime

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from data.db_manager import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

# Configuration
CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "players.csv")


class PlayerCacheUpdater:
    def __init__(self):
        self.db_manager = None
        self.players_data = []

    async def __aenter__(self):
        self.db_manager = DatabaseManager()
        await self.db_manager.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db_manager:
            await self.db_manager.close()

    def load_csv_data(self):
        """Load player data from CSV file"""
        if not os.path.exists(CSV_FILE):
            print(f"❌ CSV file not found: {CSV_FILE}")
            return False

        print(f"📖 Loading player data from {CSV_FILE}...")

        with open(CSV_FILE, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Only include players with names and teams
                if row.get("strPlayer") and row.get("strTeam"):
                    self.players_data.append(
                        {
                            "player_name": row["strPlayer"].strip(),
                            "team_name": row["strTeam"].strip(),
                            "league": row.get("strLeague", "").strip(),
                            "sport": row.get("strSport", "").strip(),
                            "position": row.get("strPosition", "").strip(),
                            "nationality": row.get("strNationality", "").strip(),
                            "height": row.get("strHeight", "").strip(),
                            "weight": row.get("strWeight", "").strip(),
                            "birth_date": row.get("strBirthDate", "").strip(),
                            "birth_location": row.get("strBirthLocation", "").strip(),
                            "photo_url": row.get("strCutouts", "").strip()
                            or row.get("strThumb", "").strip(),
                        }
                    )

        print(f"✅ Loaded {len(self.players_data)} players from CSV")
        return True

    async def create_cache_table(self):
        """Create the player_search_cache table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS player_search_cache (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            player_name VARCHAR(100) NOT NULL,
            team_name VARCHAR(100) NOT NULL,
            league VARCHAR(50) NOT NULL,
            sport VARCHAR(50) NOT NULL,
            search_keywords TEXT NOT NULL COMMENT 'Normalized search terms',
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usage_count INT DEFAULT 1,
            is_active BOOLEAN DEFAULT TRUE,
            UNIQUE KEY unique_player_team_league (player_name, team_name, league),
            INDEX idx_search_keywords (search_keywords(255)),
            INDEX idx_last_used (last_used),
            INDEX idx_usage_count (usage_count),
            INDEX idx_is_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        try:
            await self.db_manager.execute(create_table_sql)
            print("✅ Player search cache table created/verified")
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            return False

        return True

    async def clear_existing_cache(self):
        """Clear existing cache data"""
        try:
            await self.db_manager.execute("DELETE FROM player_search_cache")
            print("🗑️ Cleared existing cache data")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            return False

        return True

    async def insert_players_to_cache(self):
        """Insert all players into the cache table"""
        if not self.players_data:
            print("❌ No player data to insert")
            return False

        print("💾 Inserting players into cache...")

        # Prepare batch insert
        insert_sql = """
        INSERT INTO player_search_cache (
            player_name, team_name, league, sport, search_keywords,
            usage_count, last_used
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        batch_size = 1000
        total_inserted = 0

        for i in range(0, len(self.players_data), batch_size):
            batch = self.players_data[i : i + batch_size]

            values = []
            for player in batch:
                # Create search keywords from player name and team
                search_keywords = self._normalize_search_keywords(
                    player["player_name"], player["team_name"]
                )

                values.append(
                    (
                        player["player_name"],
                        player["team_name"],
                        player["league"],
                        player["sport"],
                        search_keywords,
                        1,  # usage_count
                        datetime.now(),  # last_used
                    )
                )

            try:
                await self.db_manager.executemany(insert_sql, values)
                total_inserted += len(batch)
                print(f"📊 Inserted batch {i//batch_size + 1}: {len(batch)} players")
            except Exception as e:
                print(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
                continue

        print(f"✅ Total players inserted: {total_inserted}")
        return True

    async def create_search_indexes(self):
        """Create additional indexes for better search performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_player_team ON player_search_cache(player_name, team_name)",
            "CREATE INDEX IF NOT EXISTS idx_league_sport ON player_search_cache(league, sport)",
            "CREATE INDEX IF NOT EXISTS idx_name_fuzzy ON player_search_cache(player_name)",
        ]

        for index_sql in indexes:
            try:
                await self.db_manager.execute(index_sql)
            except Exception as e:
                print(f"⚠️ Warning creating index: {e}")

        print("✅ Search indexes created")

    async def update_cache_statistics(self):
        """Update cache statistics"""
        try:
            # Get total count
            result = await self.db_manager.fetch_one(
                "SELECT COUNT(*) as total FROM player_search_cache"
            )
            total = result["total"] if result else 0

            # Get counts by sport
            sports_result = await self.db_manager.fetch_all(
                """
                SELECT sport, COUNT(*) as count
                FROM player_search_cache
                GROUP BY sport
                ORDER BY count DESC
            """
            )

            print("\n📊 Cache Statistics:")
            print(f"Total players: {total}")
            print("By sport:")
            for sport in sports_result:
                print(f"  {sport['sport']}: {sport['count']} players")

        except Exception as e:
            print(f"❌ Error getting statistics: {e}")

    def _normalize_search_keywords(self, player_name: str, team_name: str) -> str:
        """Normalize search keywords for better matching."""
        import re

        # Remove special characters and normalize
        normalized = re.sub(r"[^\w\s]", "", f"{player_name} {team_name}".lower())

        # Split into words and create variations
        words = normalized.split()
        keywords = set()

        # Add full name
        keywords.add(normalized)

        # Add individual words
        keywords.update(words)

        # Add common abbreviations
        if len(words) >= 2:
            # First letter of each word
            abbreviations = [word[0] for word in words if word]
            keywords.add("".join(abbreviations))

            # First word + last word
            if len(words) >= 2:
                keywords.add(f"{words[0]} {words[-1]}")

        return " ".join(keywords)


async def main():
    """Main function"""
    print("🎯 Player Search Cache Updater")
    print("=" * 50)

    async with PlayerCacheUpdater() as updater:
        # Load CSV data
        if not updater.load_csv_data():
            return

        # Create/verify table
        if not await updater.create_cache_table():
            return

        # Clear existing cache
        if not await updater.clear_existing_cache():
            return

        # Insert new data
        if not await updater.insert_players_to_cache():
            return

        # Create indexes
        await updater.create_search_indexes()

        # Show statistics
        await updater.update_cache_statistics()

    print("\n✅ Player search cache update complete!")


if __name__ == "__main__":
    asyncio.run(main())
