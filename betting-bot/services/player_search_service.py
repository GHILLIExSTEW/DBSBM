"""
Enhanced Player Search Service
Provides fuzzy search, autocomplete, and caching for player names across leagues.
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from rapidfuzz import process, fuzz
from dataclasses import dataclass

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
        limit: int = 10,
        min_confidence: float = 60.0
    ) -> List[PlayerSearchResult]:
        """
        Search for players using fuzzy matching.
        
        Args:
            query: Search query (player name)
            league: Optional league filter
            limit: Maximum number of results
            min_confidence: Minimum confidence score (0-100)
            
        Returns:
            List of PlayerSearchResult objects
        """
        if not query or len(query.strip()) < 2:
            return []
            
        query = query.strip().lower()
        
        # Check in-memory cache first
        cache_key = f"{query}:{league}:{limit}"
        if cache_key in self._search_cache:
            cached_result, timestamp = self._search_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                return cached_result
        
        try:
            # Get players from database
            players = await self._get_players_from_db(league)
            
            if not players:
                return []
            
            # Perform fuzzy search
            search_results = []
            for player in players:
                # Create searchable text
                search_text = f"{player['player_name']} {player['team_name']}".lower()
                
                # Calculate confidence scores
                name_score = fuzz.partial_ratio(query, player['player_name'].lower())
                team_score = fuzz.partial_ratio(query, player['team_name'].lower())
                full_score = fuzz.partial_ratio(query, search_text)
                
                # Use the best score
                confidence = max(name_score, team_score, full_score)
                
                if confidence >= min_confidence:
                    search_results.append(PlayerSearchResult(
                        player_name=player['player_name'],
                        team_name=player['team_name'],
                        league=player['league'],
                        sport=player['sport'],
                        confidence=confidence,
                        last_used=player.get('last_used'),
                        usage_count=player.get('usage_count', 0)
                    ))
            
            # Sort by confidence and usage count
            search_results.sort(
                key=lambda x: (x.confidence, x.usage_count), 
                reverse=True
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
        self, 
        partial_query: str, 
        league: Optional[str] = None,
        limit: int = 5
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
        results = await self.search_players(partial_query, league, limit, min_confidence=50.0)
        return [result.player_name for result in results]
    
    async def get_popular_players(
        self, 
        league: Optional[str] = None, 
        limit: int = 20
    ) -> List[PlayerSearchResult]:
        """
        Get most frequently searched players.
        
        Args:
            league: Optional league filter
            limit: Maximum number of results
            
        Returns:
            List of popular players
        """
        try:
            query = """
                SELECT 
                    player_name, team_name, league, sport,
                    last_used, usage_count
                FROM player_search_cache
                WHERE is_active = 1
            """
            params = []
            
            if league:
                query += " AND league = %s"
                params.append(league)
                
            query += " ORDER BY usage_count DESC, last_used DESC LIMIT %s"
            params.append(limit)
            
            players = await self.db_manager.fetch_all(query, tuple(params))
            
            return [
                PlayerSearchResult(
                    player_name=player['player_name'],
                    team_name=player['team_name'],
                    league=player['league'],
                    sport=player['sport'],
                    confidence=100.0,  # Popular players get high confidence
                    last_used=player['last_used'],
                    usage_count=player['usage_count']
                )
                for player in players
            ]
            
        except Exception as e:
            logger.error(f"Error getting popular players: {e}")
            return []
    
    async def add_player_to_cache(
        self, 
        player_name: str, 
        team_name: str, 
        league: str, 
        sport: str
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
                VALUES (%s, %s, %s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE 
                    search_keywords = VALUES(search_keywords),
                    last_used = VALUES(last_used),
                    usage_count = usage_count + 1
            """
            
            await self.db_manager.execute(
                query, 
                (player_name, team_name, league, sport, keywords, datetime.now())
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding player to cache: {e}")
            return False
    
    async def _get_players_from_db(self, league: Optional[str] = None) -> List[Dict]:
        """Get players from database for searching."""
        try:
            # First try player_search_cache table
            query = """
                SELECT 
                    player_name, team_name, league, sport,
                    last_used, usage_count
                FROM player_search_cache
                WHERE is_active = 1
            """
            params = []
            
            if league:
                query += " AND league = %s"
                params.append(league)
                
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
                WHERE player_name = %s 
                AND team_name = %s 
                AND league = %s
            """
            
            await self.db_manager.execute(
                query,
                (datetime.now(), player_result.player_name, player_result.team_name, player_result.league)
            )
            
        except Exception as e:
            logger.error(f"Error updating player usage: {e}")
    
    def _normalize_search_keywords(self, player_name: str, team_name: str) -> str:
        """Normalize search keywords for better matching."""
        # Remove special characters and normalize
        normalized = re.sub(r'[^\w\s]', '', f"{player_name} {team_name}".lower())
        
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
            keywords.add(''.join(abbreviations))
            
            # First word + last word
            if len(words) >= 2:
                keywords.add(f"{words[0]} {words[-1]}")
        
        return ' '.join(keywords)
    
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
                WHERE last_used < %s AND usage_count < 5
            """
            
            result = await self.db_manager.execute(query, (cutoff_date,))
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return 0 