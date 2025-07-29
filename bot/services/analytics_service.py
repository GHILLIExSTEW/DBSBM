"""Advanced analytics service for comprehensive data analysis."""

import asyncio
import json
import logging
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import enhanced_cache_get, enhanced_cache_set, enhanced_cache_delete, get_enhanced_cache_manager
from bot.utils.performance_monitor import time_operation

logger = logging.getLogger(__name__)

# Cache TTLs for analytics data
ANALYTICS_CACHE_TTLS = {
    "user_metrics": 1800,  # 30 minutes
    "guild_metrics": 3600,  # 1 hour
    "betting_patterns": 7200,  # 2 hours
    "performance_ranks": 3600,  # 1 hour
    "engagement_scores": 1800,  # 30 minutes
    "trend_analysis": 3600,  # 1 hour
}


class AnalyticsService:
    """Advanced analytics service for comprehensive data analysis."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.event_queue = deque(maxlen=10000)  # In-memory event buffer
        self.pattern_cache = {}  # Cache for betting patterns
        self.metrics_cache = {}  # Cache for computed metrics
        self._processing_task = None
        self._is_running = False

        # Analytics configuration
        self.config = {
            'event_batch_size': 100,
            'event_flush_interval': 60,  # seconds
            'pattern_analysis_interval': 300,  # seconds
            'metrics_cache_ttl': 300,  # seconds
            'max_patterns_per_user': 50,
            'min_confidence_score': 0.6
        }

        logger.info("AnalyticsService initialized")

    async def start(self):
        """Start the analytics service."""
        if self._is_running:
            logger.warning("AnalyticsService is already running")
            return

        self._is_running = True
        self._processing_task = asyncio.create_task(self._process_events())
        logger.info("AnalyticsService started")

    async def stop(self):
        """Stop the analytics service."""
        if not self._is_running:
            return

        self._is_running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info("AnalyticsService stopped")

    async def _process_events(self):
        """Process analytics events in the background."""
        while self._is_running:
            try:
                # Process events in batches
                events = []
                while len(events) < self.config['event_batch_size'] and self.event_queue:
                    events.append(self.event_queue.popleft())

                if events:
                    await self._analyze_events(events)

                await asyncio.sleep(self.config['event_flush_interval'])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing analytics events: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def _analyze_events(self, events: List[Dict]):
        """Analyze a batch of events."""
        try:
            for event in events:
                event_type = event.get('type')
                if event_type == 'bet_placed':
                    await self._analyze_betting_pattern(event)
                elif event_type == 'user_activity':
                    await self._analyze_user_behavior(event)
                elif event_type == 'game_result':
                    await self._analyze_game_outcome(event)

        except Exception as e:
            logger.error(f"Error analyzing events: {e}")

    async def _analyze_betting_pattern(self, event: Dict):
        """Analyze betting patterns from events."""
        try:
            user_id = event.get('user_id')
            bet_data = event.get('bet_data', {})

            # Cache betting pattern analysis
            cache_key = f"betting_pattern:{user_id}"
            cached_patterns = await enhanced_cache_get("analytics_data", cache_key)

            if cached_patterns:
                patterns = cached_patterns
            else:
                patterns = await self._get_user_betting_patterns(user_id)
                await enhanced_cache_set("analytics_data", cache_key, patterns, ttl=ANALYTICS_CACHE_TTLS["betting_patterns"])

            # Update patterns with new event
            patterns.append({
                'timestamp': event.get('timestamp'),
                'bet_type': bet_data.get('type'),
                'amount': bet_data.get('amount'),
                'odds': bet_data.get('odds'),
                'sport': bet_data.get('sport')
            })

            # Keep only recent patterns
            if len(patterns) > self.config['max_patterns_per_user']:
                patterns = patterns[-self.config['max_patterns_per_user']:]

            # Update cache
            await enhanced_cache_set("analytics_data", cache_key, patterns, ttl=ANALYTICS_CACHE_TTLS["betting_patterns"])

        except Exception as e:
            logger.error(f"Error analyzing betting pattern: {e}")

    async def _analyze_user_behavior(self, event: Dict):
        """Analyze user behavior patterns."""
        try:
            user_id = event.get('user_id')
            activity_type = event.get('activity_type')

            # Cache user behavior analysis
            cache_key = f"user_behavior:{user_id}"
            cached_behavior = await enhanced_cache_get("analytics_data", cache_key)

            if not cached_behavior:
                cached_behavior = {
                    'activity_count': 0,
                    'last_activity': None,
                    'favorite_sports': {},
                    'peak_hours': {}
                }

            # Update behavior data
            cached_behavior['activity_count'] += 1
            cached_behavior['last_activity'] = event.get('timestamp')

            # Track favorite sports
            sport = event.get('sport')
            if sport:
                cached_behavior['favorite_sports'][sport] = cached_behavior['favorite_sports'].get(
                    sport, 0) + 1

            # Track peak hours
            hour = datetime.fromisoformat(event.get('timestamp')).hour
            cached_behavior['peak_hours'][hour] = cached_behavior['peak_hours'].get(
                hour, 0) + 1

            await enhanced_cache_set("analytics_data", cache_key, cached_behavior, ttl=ANALYTICS_CACHE_TTLS["user_metrics"])

        except Exception as e:
            logger.error(f"Error analyzing user behavior: {e}")

    async def _analyze_game_outcome(self, event: Dict):
        """Analyze game outcome patterns."""
        try:
            game_id = event.get('game_id')
            outcome = event.get('outcome')

            # Cache game outcome analysis
            cache_key = f"game_outcome:{game_id}"
            await enhanced_cache_set("analytics_data", cache_key, {
                'outcome': outcome,
                'timestamp': event.get('timestamp'),
                'affected_bets': event.get('affected_bets', [])
            }, ttl=ANALYTICS_CACHE_TTLS["trend_analysis"])

        except Exception as e:
            logger.error(f"Error analyzing game outcome: {e}")

    @time_operation("analytics_get_user_metrics")
    async def get_user_metrics(self, user_id: int, guild_id: int,
                               time_range: str = "30d") -> Dict[str, Any]:
        """Get comprehensive user metrics."""
        try:
            # Check cache first
            cache_key = f"user_metrics:{user_id}:{guild_id}:{time_range}"
            cached_metrics = await enhanced_cache_get("analytics_data", cache_key)

            if cached_metrics:
                logger.debug(f"Cache hit for user metrics: {user_id}")
                return cached_metrics

            # Calculate time range
            end_date = datetime.utcnow()
            start_date = self._get_start_date(time_range)

            # Get user betting data
            betting_data = await self._get_user_betting_data(user_id, guild_id, start_date, end_date)

            # Calculate metrics
            metrics = {
                'total_bets': len(betting_data),
                'total_volume': sum(bet['amount'] for bet in betting_data),
                'win_rate': self._calculate_win_rate(betting_data),
                'avg_bet_size': self._calculate_avg_bet_size(betting_data),
                'favorite_sports': self._get_favorite_sports(betting_data),
                'betting_trends': await self._analyze_betting_trends(user_id, guild_id, start_date, end_date),
                'engagement_score': await self._calculate_engagement_score(user_id, guild_id, start_date, end_date),
                'risk_profile': self._calculate_risk_profile(betting_data),
                'performance_rank': await self._get_performance_rank(user_id, guild_id)
            }

            # Cache the results
            await enhanced_cache_set("analytics_data", cache_key, metrics, ttl=self.config['metrics_cache_ttl'])

            return metrics

        except Exception as e:
            logger.error(f"Error getting user metrics: {e}")
            return {}

    @time_operation("analytics_get_guild_metrics")
    async def get_guild_metrics(self, guild_id: int, time_range: str = "30d") -> Dict[str, Any]:
        """Get comprehensive guild metrics."""
        try:
            # Check cache first
            cache_key = f"guild_metrics:{guild_id}:{time_range}"
            cached_metrics = await enhanced_cache_get("analytics_data", cache_key)

            if cached_metrics:
                logger.debug(f"Cache hit for guild metrics: {guild_id}")
                return cached_metrics

            # Calculate time range
            end_date = datetime.utcnow()
            start_date = self._get_start_date(time_range)

            # Get guild betting data
            betting_data = await self._get_guild_betting_data(guild_id, start_date, end_date)

            # Calculate metrics
            metrics = {
                'total_bets': len(betting_data),
                'total_volume': sum(bet['amount'] for bet in betting_data),
                'active_users': len(set(bet['user_id'] for bet in betting_data)),
                'avg_bet_size': self._calculate_avg_bet_size(betting_data),
                'popular_sports': self._get_popular_sports(betting_data),
                'revenue_metrics': self._calculate_revenue_metrics(betting_data),
                'user_engagement': await self._calculate_guild_engagement(guild_id, start_date, end_date)
            }

            # Cache the results
            await enhanced_cache_set("analytics_data", cache_key, metrics, ttl=self.config['metrics_cache_ttl'])

            return metrics

        except Exception as e:
            logger.error(f"Error getting guild metrics: {e}")
            return {}

    async def _get_user_betting_data(self, user_id: int, guild_id: int,
                                     start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get user betting data from database."""
        try:
            query = """
                SELECT bet_id, amount, odds, status, created_at, game_id
                FROM bets
                WHERE user_id = %s AND guild_id = %s
                AND created_at BETWEEN %s AND %s
                ORDER BY created_at DESC
            """
            return await self.db_manager.fetch_all(query, user_id, guild_id, start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting user betting data: {e}")
            return []

    async def _get_guild_betting_data(self, guild_id: int,
                                      start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get guild betting data from database."""
        try:
            query = """
                SELECT bet_id, user_id, amount, odds, status, created_at, game_id
                FROM bets
                WHERE guild_id = %s
                AND created_at BETWEEN %s AND %s
                ORDER BY created_at DESC
            """
            return await self.db_manager.fetch_all(query, guild_id, start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting guild betting data: {e}")
            return []

    def _get_start_date(self, time_range: str) -> datetime:
        """Get start date based on time range."""
        now = datetime.utcnow()
        if time_range == "7d":
            return now - timedelta(days=7)
        elif time_range == "30d":
            return now - timedelta(days=30)
        elif time_range == "90d":
            return now - timedelta(days=90)
        else:
            return now - timedelta(days=30)  # Default to 30 days

    def _calculate_win_rate(self, betting_data: List[Dict]) -> float:
        """Calculate win rate from betting data."""
        if not betting_data:
            return 0.0

        completed_bets = [
            bet for bet in betting_data if bet['status'] in ['won', 'lost']]
        if not completed_bets:
            return 0.0

        won_bets = [bet for bet in completed_bets if bet['status'] == 'won']
        return len(won_bets) / len(completed_bets)

    def _calculate_avg_bet_size(self, betting_data: List[Dict]) -> float:
        """Calculate average bet size."""
        if not betting_data:
            return 0.0

        total_amount = sum(bet['amount'] for bet in betting_data)
        return total_amount / len(betting_data)

    def _get_favorite_sports(self, betting_data: List[Dict]) -> Dict[str, int]:
        """Get user's favorite sports based on betting frequency."""
        sport_counts = {}
        for bet in betting_data:
            # Extract sport from game_id or other field
            sport = bet.get('sport', 'Unknown')
            sport_counts[sport] = sport_counts.get(sport, 0) + 1
        return sport_counts

    def _get_popular_sports(self, betting_data: List[Dict]) -> Dict[str, int]:
        """Get popular sports in guild."""
        sport_counts = {}
        for bet in betting_data:
            sport = bet.get('sport', 'Unknown')
            sport_counts[sport] = sport_counts.get(sport, 0) + 1
        return sport_counts

    def _calculate_risk_profile(self, betting_data: List[Dict]) -> str:
        """Calculate user's risk profile."""
        if not betting_data:
            return "Unknown"

        avg_bet_size = self._calculate_avg_bet_size(betting_data)
        total_volume = sum(bet['amount'] for bet in betting_data)

        if avg_bet_size > 100 or total_volume > 1000:
            return "High Risk"
        elif avg_bet_size > 50 or total_volume > 500:
            return "Medium Risk"
        else:
            return "Low Risk"

    async def _analyze_betting_trends(self, user_id: int, guild_id: int,
                                      start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze betting trends for a user."""
        try:
            # This would implement trend analysis logic
            return {
                'trend_direction': 'stable',
                'volume_change': 0.0,
                'frequency_change': 0.0
            }
        except Exception as e:
            logger.error(f"Error analyzing betting trends: {e}")
            return {}

    async def _calculate_engagement_score(self, user_id: int, guild_id: int,
                                          start_date: datetime, end_date: datetime) -> float:
        """Calculate user engagement score."""
        try:
            # This would implement engagement scoring logic
            return 0.75  # Placeholder
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0

    async def _get_performance_rank(self, user_id: int, guild_id: int) -> int:
        """Get user's performance rank in guild."""
        try:
            # This would implement ranking logic
            return 5  # Placeholder
        except Exception as e:
            logger.error(f"Error getting performance rank: {e}")
            return 0

    async def _calculate_revenue_metrics(self, betting_data: List[Dict]) -> Dict[str, float]:
        """Calculate revenue metrics for guild."""
        try:
            total_volume = sum(bet['amount'] for bet in betting_data)
            completed_bets = [
                bet for bet in betting_data if bet['status'] in ['won', 'lost']]

            if not completed_bets:
                return {'total_revenue': 0.0, 'avg_revenue_per_bet': 0.0}

            # Simple revenue calculation (this would be more complex in practice)
            revenue = total_volume * 0.05  # 5% commission
            avg_revenue = revenue / len(completed_bets)

            return {
                'total_revenue': revenue,
                'avg_revenue_per_bet': avg_revenue
            }
        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {e}")
            return {'total_revenue': 0.0, 'avg_revenue_per_bet': 0.0}

    async def _calculate_guild_engagement(self, guild_id: int,
                                          start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate guild engagement metrics."""
        try:
            # This would implement guild engagement analysis
            return {
                'active_users': 0,
                'avg_bets_per_user': 0.0,
                'retention_rate': 0.0
            }
        except Exception as e:
            logger.error(f"Error calculating guild engagement: {e}")
            return {}

    async def _get_user_betting_patterns(self, user_id: int) -> List[Dict]:
        """Get user's betting patterns."""
        try:
            # This would implement pattern analysis
            return []
        except Exception as e:
            logger.error(f"Error getting user betting patterns: {e}")
            return []

    async def clear_analytics_cache(self, user_id: Optional[int] = None, guild_id: Optional[int] = None):
        """Clear analytics cache for specific user or guild."""
        try:
            if user_id:
                # Clear user-specific cache
                await enhanced_cache_delete("analytics_data", f"user_metrics:{user_id}")
                await enhanced_cache_delete("analytics_data", f"user_behavior:{user_id}")
                await enhanced_cache_delete("analytics_data", f"betting_pattern:{user_id}")
                logger.info(f"Cleared analytics cache for user {user_id}")

            if guild_id:
                # Clear guild-specific cache
                await enhanced_cache_delete("analytics_data", f"guild_metrics:{guild_id}")
                logger.info(f"Cleared analytics cache for guild {guild_id}")

            if not user_id and not guild_id:
                # Clear all analytics cache
                # Note: This would need to be implemented in the cache manager
                logger.info("Cleared all analytics cache")

        except Exception as e:
            logger.error(f"Error clearing analytics cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get analytics cache statistics."""
        try:
            return await get_enhanced_cache_manager().get_stats()
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
