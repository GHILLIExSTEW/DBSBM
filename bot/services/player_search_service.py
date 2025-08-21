"""
Enhanced Player Search Service
Provides fuzzy search, autocomplete, and caching for player names across leagues.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


@dataclass
class PlayerSearchResult:
    """Result from player search."""

    player_name: str
    team_name: str
    league: str
    sport: str
    confidence: float
    last_used: Optional[datetime] = None
    usage_count: int = 0


class PlayerSearchService:
    """Service for searching and caching player data."""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._search_cache = {}  # In-memory cache for recent searches
        self._cache_ttl = 300  # 5 minutes cache TTL

    async def search_players(
        self,
        query: str,
        league: Optional[str] = None,
        team_name: Optional[str] = None,
        limit: int = 10,
        min_confidence: float = 60.0,
    ) -> List[PlayerSearchResult]:
        """
        Search for players using fuzzy matching with team library support.

        Args:
            query: Search query (player name)
            league: Optional league filter (REQUIRED for proper sport filtering)
            team_name: Optional team name to prioritize team library players
            limit: Maximum number of results
            min_confidence: Minimum confidence score (0-100)

        Returns:
            List of PlayerSearchResult objects
        """
        if not query or len(query.strip()) < 2:
            return []

        query = query.strip().lower()

        # Check in-memory cache first
        cache_key = f"{query}:{league}:{team_name}:{limit}"
        if cache_key in self._search_cache:
            cached_result, timestamp = self._search_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                return cached_result

        try:
            # Get players from team library first if team is specified
            team_players = []
            if team_name:
                team_players = await self._get_players_from_team_library(
                    league, team_name
                )

            # Get players from database - IMPORTANT: Always filter by league and team if specified
            db_players = await self._get_players_from_db(league, team_name)

            # Combine and prioritize team library players
            all_players = team_players + db_players

            if not all_players:
                return []

            # Perform fuzzy search
            search_results = []
            for player in all_players:
                # Create searchable text
                search_text = f"{player['player_name']} {player['team_name']}".lower()

                # Calculate confidence scores
                name_score = fuzz.partial_ratio(query, player["player_name"].lower())
                team_score = fuzz.partial_ratio(query, player["team_name"].lower())
                full_score = fuzz.partial_ratio(query, search_text)

                # Use the best score
                confidence = max(name_score, team_score, full_score)

                # Boost confidence for team library players
                if player.get("from_team_library", False):
                    confidence += 20  # Boost team library players

                if confidence >= min_confidence:
                    search_results.append(
                        PlayerSearchResult(
                            player_name=player["player_name"],
                            team_name=player["team_name"],
                            league=player["league"],
                            sport=player["sport"],
                            confidence=confidence,
                            last_used=player.get("last_used"),
                            usage_count=player.get("usage_count", 0),
                        )
                    )

            # Sort by confidence and usage count
            search_results.sort(
                key=lambda x: (x.confidence, x.usage_count), reverse=True
            )

            # Limit results
            results = search_results[:limit]

            # Cache results
            self._search_cache[cache_key] = (results, datetime.now())

            # Update usage count for top result
            if results:
                await self._update_player_usage(results[0])

            return results

        except Exception as e:
            logger.error(f"Error searching players: {e}")
            return []

    async def get_player_suggestions(
        self, partial_query: str, league: Optional[str] = None, limit: int = 5
    ) -> List[str]:
        """
        Get autocomplete suggestions for player names.

        Args:
            partial_query: Partial player name
            league: Optional league filter
            limit: Maximum number of suggestions

        Returns:
            List of player name suggestions
        """
        results = await self.search_players(
            partial_query, league, limit, min_confidence=50.0
        )
        return [result.player_name for result in results]

    async def get_popular_players(
        self,
        league: Optional[str] = None,
        team_name: Optional[str] = None,
        limit: int = 20,
    ) -> List[PlayerSearchResult]:
        """
        Get most frequently searched players.

        Args:
            league: League filter (REQUIRED for proper sport filtering)
            limit: Maximum number of results

        Returns:
            List of popular players
        """
        try:
            # IMPORTANT: Always filter by league to avoid wrong sport players
            if not league:
                logger.warning(
                    "get_popular_players called without league filter - this may return wrong sport players"
                )
                return []

            query = """
                SELECT
                    player_name, team_name, league, sport,
                    last_used, usage_count
                FROM player_search_cache
            """
            params = []
            conditions = []

            if league:
                conditions.append("league = %s")
                params.append(league)

            if team_name:
                conditions.append("team_name = %s")
                params.append(team_name)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" ORDER BY usage_count DESC, last_used DESC LIMIT ${len(params) + 1}"
            params.append(limit)

            players = await self.db_manager.fetch_all(query, tuple(params))

            return [
                PlayerSearchResult(
                    player_name=player["player_name"],
                    team_name=player["team_name"],
                    league=player["league"],
                    sport=player["sport"],
                    confidence=100.0,  # Popular players get high confidence
                    last_used=player["last_used"],
                    usage_count=player["usage_count"],
                )
                for player in players
            ]

        except Exception as e:
            logger.error(f"Error getting popular players: {e}")
            return []

    async def add_player_to_cache(
        self, player_name: str, team_name: str, league: str, sport: str
    ) -> bool:
        """
        Add a player to the search cache.

        Args:
            player_name: Player's name
            team_name: Team name
            league: League name
            sport: Sport name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize search keywords
            keywords = self._normalize_search_keywords(player_name, team_name)

            query = """
                INSERT INTO player_search_cache
                (player_name, team_name, league, sport, search_keywords, last_used, usage_count)
                VALUES ($1, $2, $3, $4, $5, $6, 1)
                ON DUPLICATE KEY UPDATE
                    search_keywords = VALUES(search_keywords),
                    last_used = VALUES(last_used),
                    usage_count = usage_count + 1
            """

            await self.db_manager.execute(
                query, (player_name, team_name, league, sport, keywords, datetime.now())
            )

            return True

        except Exception as e:
            logger.error(f"Error adding player to cache: {e}")
            return False

    async def _get_players_from_db(
        self, league: Optional[str] = None, team_name: Optional[str] = None
    ) -> List[Dict]:
        """Get players from database for searching."""
        try:
            # First try player_search_cache table
            query = """
                SELECT
                    player_name, team_name, league, sport,
                    last_used, usage_count
                FROM player_search_cache
            """
            params = []
            conditions = []

            if league:
                conditions.append("league = %s")
                params.append(league)

            if team_name:
                conditions.append("team_name = %s")
                params.append(team_name)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY usage_count DESC, last_used DESC"

            players = await self.db_manager.fetch_all(query, tuple(params))

            # If no results, fall back to bets table
            if not players:
                players = await self._get_players_from_bets(league)

            return players

        except Exception as e:
            logger.error(f"Error getting players from DB: {e}")
            return []

    async def _get_players_from_bets(self, league: Optional[str] = None) -> List[Dict]:
        """Get players from bets table as fallback."""
        try:
            query = """
                SELECT DISTINCT
                    player_name, team_name, league, sport,
                    NULL as last_used, 1 as usage_count
                FROM bets
                WHERE player_name IS NOT NULL
                AND player_name != ''
                AND bet_type = 'player_prop'
            """
            params = []

            if league:
                query += " AND league = %s"
                params.append(league)

            query += " ORDER BY created_at DESC"

            return await self.db_manager.fetch_all(query, tuple(params))

        except Exception as e:
            logger.error(f"Error getting players from bets: {e}")
            return []

    async def _update_player_usage(self, player_result: PlayerSearchResult) -> None:
        """Update usage count for a player."""
        try:
            query = """
                UPDATE player_search_cache
                SET usage_count = usage_count + 1,
                    last_used = %s
                WHERE player_name = $1
                AND team_name = %s
                AND league = %s
            """

            await self.db_manager.execute(
                query,
                (
                    datetime.now(),
                    player_result.player_name,
                    player_result.team_name,
                    player_result.league,
                ),
            )

        except Exception as e:
            logger.error(f"Error updating player usage: {e}")

    def _normalize_search_keywords(self, player_name: str, team_name: str) -> str:
        """Normalize search keywords for better matching."""
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

    async def cleanup_old_cache(self, days: int = 30) -> int:
        """
        Clean up old cache entries.

        Args:
            days: Remove entries older than this many days

        Returns:
            Number of entries removed
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = """
                DELETE FROM player_search_cache
                WHERE last_used < $1 AND usage_count < 5
            """

            result = await self.db_manager.execute(query, (cutoff_date,))
            return result[0] if result else 0

        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return 0

    async def _get_players_from_team_library(
        self, league: Optional[str] = None, team_name: Optional[str] = None
    ) -> List[Dict]:
        """Get players from team library based on league and team."""
        try:
            players = []

            # Import team mappings
            from bot.utils.league_dictionaries.team_mappings import LEAGUE_TEAM_MAPPINGS

            # Get league-specific player data
            if league:
                # Try to get players from league-specific mappings
                if league in LEAGUE_TEAM_MAPPINGS:
                    league_mappings = LEAGUE_TEAM_MAPPINGS[league]

                    # For individual sports (tennis, darts, golf), return players directly
                    if league in [
                        "ATP",
                        "WTA",
                        "PDC",
                        "BDO",
                        "WDF",
                        "PGA",
                        "LPGA",
                        "EuropeanTour",
                        "LIVGolf",
                    ]:
                        for player_key, player_name in league_mappings.items():
                            players.append(
                                {
                                    "player_name": player_name,
                                    "team_name": league,  # Use league as team for individual sports
                                    "league": league,
                                    "sport": self._get_sport_from_league(league),
                                    "from_team_library": True,
                                    "usage_count": 1,
                                }
                            )
                    else:
                        # For team sports, filter by team if specified
                        if team_name:
                            # Get players for this specific team
                            team_players = await self._get_team_players(
                                league, team_name
                            )
                            for player in team_players:
                                players.append(
                                    {
                                        "player_name": player,
                                        "team_name": team_name,
                                        "league": league,
                                        "sport": self._get_sport_from_league(league),
                                        "from_team_library": True,
                                        "usage_count": 1,
                                    }
                                )

            return players

        except Exception as e:
            logger.error(f"Error getting players from team library: {e}")
            return []

    async def _get_team_players(self, league: str, team_name: str) -> List[str]:
        """Get players for a specific team from various sources."""
        try:
            players = []

            # Try to get players from static data files
            if league == "NBA":
                players = await self._get_nba_team_players(team_name)
            elif league == "NFL":
                players = await self._get_nfl_team_players(team_name)
            elif league == "MLB":
                players = await self._get_mlb_team_players(team_name)
            elif league == "NHL":
                players = await self._get_nhl_team_players(team_name)
            elif league in ["EPL", "LaLiga", "Bundesliga", "SerieA", "Ligue1"]:
                players = await self._get_soccer_team_players(team_name)

            return players

        except Exception as e:
            logger.error(f"Error getting team players: {e}")
            return []

    async def _get_nba_team_players(self, team_name: str) -> List[str]:
        """Get NBA team players from static data."""
        try:
            # Common NBA players by team (simplified - in production, use API or database)
            nba_teams_players = {
                "lakers": [
                    "LeBron James",
                    "Anthony Davis",
                    "Austin Reaves",
                    "D'Angelo Russell",
                ],
                "celtics": [
                    "Jayson Tatum",
                    "Jaylen Brown",
                    "Kristaps Porzingis",
                    "Derrick White",
                ],
                "warriors": [
                    "Stephen Curry",
                    "Klay Thompson",
                    "Draymond Green",
                    "Andrew Wiggins",
                ],
                "heat": [
                    "Jimmy Butler",
                    "Bam Adebayo",
                    "Tyler Herro",
                    "Duncan Robinson",
                ],
                "nuggets": [
                    "Nikola Jokic",
                    "Jamal Murray",
                    "Aaron Gordon",
                    "Michael Porter Jr.",
                ],
                "suns": [
                    "Kevin Durant",
                    "Devin Booker",
                    "Bradley Beal",
                    "Jusuf Nurkic",
                ],
                "bucks": [
                    "Giannis Antetokounmpo",
                    "Damian Lillard",
                    "Khris Middleton",
                    "Brook Lopez",
                ],
                "76ers": [
                    "Joel Embiid",
                    "Tyrese Maxey",
                    "Tobias Harris",
                    "Kelly Oubre Jr.",
                ],
            }

            normalized_team = team_name.lower().replace(" ", "")
            return nba_teams_players.get(normalized_team, [])

        except Exception as e:
            logger.error(f"Error getting NBA team players: {e}")
            return []

    async def _get_nfl_team_players(self, team_name: str) -> List[str]:
        """Get NFL team players from static data."""
        try:
            # Common NFL players by team (simplified)
            nfl_teams_players = {
                "chiefs": [
                    "Patrick Mahomes",
                    "Travis Kelce",
                    "Isiah Pacheco",
                    "Rashee Rice",
                ],
                "eagles": [
                    "Jalen Hurts",
                    "A.J. Brown",
                    "DeVonta Smith",
                    "Dallas Goedert",
                ],
                "bills": ["Josh Allen", "Stefon Diggs", "James Cook", "Dalton Kincaid"],
                "cowboys": [
                    "Dak Prescott",
                    "CeeDee Lamb",
                    "Tony Pollard",
                    "Jake Ferguson",
                ],
                "ravens": [
                    "Lamar Jackson",
                    "Mark Andrews",
                    "Zay Flowers",
                    "Gus Edwards",
                ],
            }

            normalized_team = team_name.lower().replace(" ", "")
            return nfl_teams_players.get(normalized_team, [])

        except Exception as e:
            logger.error(f"Error getting NFL team players: {e}")
            return []

    async def _get_mlb_team_players(self, team_name: str) -> List[str]:
        """Get MLB team players from static data."""
        try:
            # Common MLB players by team (simplified)
            mlb_teams_players = {
                "yankees": [
                    "Aaron Judge",
                    "Giancarlo Stanton",
                    "Anthony Rizzo",
                    "Gleyber Torres",
                ],
                "dodgers": [
                    "Mookie Betts",
                    "Freddie Freeman",
                    "Shohei Ohtani",
                    "Will Smith",
                ],
                "astros": [
                    "Yordan Alvarez",
                    "Jose Altuve",
                    "Alex Bregman",
                    "Kyle Tucker",
                ],
                "braves": [
                    "Ronald Acuña Jr.",
                    "Matt Olson",
                    "Austin Riley",
                    "Ozzie Albies",
                ],
                "phillies": [
                    "Bryce Harper",
                    "Trea Turner",
                    "Kyle Schwarber",
                    "Nick Castellanos",
                ],
            }

            normalized_team = team_name.lower().replace(" ", "")
            return mlb_teams_players.get(normalized_team, [])

        except Exception as e:
            logger.error(f"Error getting MLB team players: {e}")
            return []

    async def _get_nhl_team_players(self, team_name: str) -> List[str]:
        """Get NHL team players from static data."""
        try:
            # Common NHL players by team (simplified)
            nhl_teams_players = {
                "oilers": [
                    "Connor McDavid",
                    "Leon Draisaitl",
                    "Evan Bouchard",
                    "Zach Hyman",
                ],
                "avalanche": [
                    "Nathan MacKinnon",
                    "Mikko Rantanen",
                    "Cale Makar",
                    "Valeri Nichushkin",
                ],
                "lightning": [
                    "Nikita Kucherov",
                    "Brayden Point",
                    "Victor Hedman",
                    "Steven Stamkos",
                ],
                "bruins": [
                    "David Pastrnak",
                    "Brad Marchand",
                    "Charlie McAvoy",
                    "Jeremy Swayman",
                ],
                "leafs": [
                    "Auston Matthews",
                    "Mitch Marner",
                    "William Nylander",
                    "John Tavares",
                ],
            }

            normalized_team = team_name.lower().replace(" ", "")
            return nhl_teams_players.get(normalized_team, [])

        except Exception as e:
            logger.error(f"Error getting NHL team players: {e}")
            return []

    async def _get_soccer_team_players(self, team_name: str) -> List[str]:
        """Get soccer team players from static data."""
        try:
            # Common soccer players by team (simplified)
            soccer_teams_players = {
                "manchester city": [
                    "Erling Haaland",
                    "Kevin De Bruyne",
                    "Phil Foden",
                    "Rodri",
                ],
                "arsenal": [
                    "Bukayo Saka",
                    "Martin Ødegaard",
                    "Gabriel Jesus",
                    "Declan Rice",
                ],
                "real madrid": [
                    "Jude Bellingham",
                    "Vinicius Jr.",
                    "Rodrygo",
                    "Toni Kroos",
                ],
                "barcelona": ["Robert Lewandowski", "Frenkie de Jong", "Pedri", "Gavi"],
                "bayern munich": [
                    "Harry Kane",
                    "Jamal Musiala",
                    "Leroy Sané",
                    "Joshua Kimmich",
                ],
            }

            normalized_team = team_name.lower()
            return soccer_teams_players.get(normalized_team, [])

        except Exception as e:
            logger.error(f"Error getting soccer team players: {e}")
            return []

    def _get_sport_from_league(self, league: str) -> str:
        """Get sport name from league."""
        sport_mapping = {
            "NBA": "basketball",
            "WNBA": "basketball",
            "NFL": "football",
            "MLB": "baseball",
            "NHL": "hockey",
            "EPL": "soccer",
            "LaLiga": "soccer",
            "Bundesliga": "soccer",
            "SerieA": "soccer",
            "Ligue1": "soccer",
            "ChampionsLeague": "soccer",
            "EuropaLeague": "soccer",
            "WorldCup": "soccer",
            "ATP": "tennis",
            "WTA": "tennis",
            "Tennis": "tennis",
            "PDC": "darts",
            "BDO": "darts",
            "WDF": "darts",
            "PGA": "golf",
            "LPGA": "golf",
            "EuropeanTour": "golf",
            "LIVGolf": "golf",
            "Formula-1": "racing",
            "MMA": "mma",
            "Bellator": "mma",
        }
        return sport_mapping.get(league, "other")
