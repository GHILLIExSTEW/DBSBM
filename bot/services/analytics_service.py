"""Advanced Analytics Service for DBSBM System.

This service provides comprehensive analytics and reporting capabilities including:
- Real-time metrics tracking and visualization
- User behavior analysis and engagement metrics
- Betting pattern analysis and trend identification
- Performance benchmarking against historical data
- Custom report generation with export capabilities
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import aiohttp
import pandas as pd
from io import BytesIO

from bot.data.db_manager import DatabaseManager
from bot.data.cache_manager import cache_get, cache_set
from bot.services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsEvent:
    """Represents an analytics event to be tracked."""
    user_id: int
    guild_id: int
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class BettingPattern:
    """Represents a detected betting pattern."""
    user_id: int
    guild_id: int
    pattern_type: str
    pattern_data: Dict[str, Any]
    confidence_score: float
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AnalyticsMetrics:
    """Container for analytics metrics."""
    total_users: int
    active_users: int
    total_bets: int
    total_volume: float
    win_rate: float
    avg_bet_size: float
    engagement_score: float
    retention_rate: float

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

    @time_operation("analytics_track_event")
    async def track_event(self, event: AnalyticsEvent):
        """Track an analytics event."""
        try:
            # Add to in-memory queue for batch processing
            self.event_queue.append(event)

            # If queue is full, trigger immediate processing
            if len(self.event_queue) >= self.config['event_batch_size']:
                await self._flush_events()

            record_metric("analytics_events_tracked", 1)
            logger.debug(f"Tracked event: {event.event_type} for user {event.user_id}")

        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            record_metric("analytics_errors", 1)

    @time_operation("analytics_get_user_metrics")
    async def get_user_metrics(self, user_id: int, guild_id: int,
                              time_range: str = "30d") -> Dict[str, Any]:
        """Get comprehensive metrics for a specific user."""
        cache_key = f"user_metrics:{user_id}:{guild_id}:{time_range}"

        # Check cache first
        cached_metrics = await cache_get("analytics", cache_key)
        if cached_metrics:
            return cached_metrics

        try:
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
            await cache_set("analytics", cache_key, metrics, ttl=self.config['metrics_cache_ttl'])

            return metrics

        except Exception as e:
            logger.error(f"Error getting user metrics: {e}")
            return {}

    @time_operation("analytics_get_guild_metrics")
    async def get_guild_metrics(self, guild_id: int, time_range: str = "30d") -> Dict[str, Any]:
        """Get comprehensive metrics for a guild."""
        cache_key = f"guild_metrics:{guild_id}:{time_range}"

        # Check cache first
        cached_metrics = await cache_get("analytics", cache_key)
        if cached_metrics:
            return cached_metrics

        try:
            # Calculate time range
            end_date = datetime.utcnow()
            start_date = self._get_start_date(time_range)

            # Get guild data
            guild_data = await self._get_guild_data(guild_id, start_date, end_date)

            # Calculate metrics
            metrics = {
                'total_users': guild_data['total_users'],
                'active_users': guild_data['active_users'],
                'total_bets': guild_data['total_bets'],
                'total_volume': guild_data['total_volume'],
                'avg_win_rate': guild_data['avg_win_rate'],
                'avg_bet_size': guild_data['avg_bet_size'],
                'user_engagement': await self._calculate_guild_engagement(guild_id, start_date, end_date),
                'betting_trends': await self._analyze_guild_trends(guild_id, start_date, end_date),
                'top_performers': await self._get_top_performers(guild_id, start_date, end_date),
                'popular_sports': self._get_popular_sports(guild_data['bets']),
                'retention_rate': await self._calculate_retention_rate(guild_id, start_date, end_date)
            }

            # Cache the results
            await cache_set("analytics", cache_key, metrics, ttl=self.config['metrics_cache_ttl'])

            return metrics

        except Exception as e:
            logger.error(f"Error getting guild metrics: {e}")
            return {}

    @time_operation("analytics_detect_patterns")
    async def detect_betting_patterns(self, user_id: int, guild_id: int) -> List[BettingPattern]:
        """Detect betting patterns for a user."""
        try:
            # Get user's betting history
            query = """
                SELECT * FROM bets
                WHERE user_id = %s AND guild_id = %s
                ORDER BY created_at DESC
                LIMIT 1000
            """
            bets = await self.db_manager.fetch_all(query, user_id, guild_id)

            if not bets:
                return []

            patterns = []

            # Detect time-based patterns
            time_patterns = self._detect_time_patterns(bets)
            patterns.extend(time_patterns)

            # Detect bet size patterns
            size_patterns = self._detect_bet_size_patterns(bets)
            patterns.extend(size_patterns)

            # Detect sport/league patterns
            sport_patterns = self._detect_sport_patterns(bets)
            patterns.extend(sport_patterns)

            # Detect win/loss patterns
            outcome_patterns = self._detect_outcome_patterns(bets)
            patterns.extend(outcome_patterns)

            # Store patterns in database
            await self._store_patterns(patterns)

            return patterns

        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []

    @time_operation("analytics_generate_report")
    async def generate_report(self, guild_id: int, report_type: str,
                            time_range: str = "30d", format: str = "json") -> Union[Dict, str]:
        """Generate comprehensive analytics report."""
        try:
            # Get guild metrics
            metrics = await self.get_guild_metrics(guild_id, time_range)

            # Get user patterns
            user_patterns = await self._get_guild_user_patterns(guild_id)

            # Get betting trends
            trends = await self._analyze_guild_trends(guild_id,
                                                     self._get_start_date(time_range),
                                                     datetime.utcnow())

            # Compile report
            report = {
                'report_type': report_type,
                'guild_id': guild_id,
                'time_range': time_range,
                'generated_at': datetime.utcnow().isoformat(),
                'metrics': metrics,
                'patterns': user_patterns,
                'trends': trends,
                'recommendations': await self._generate_recommendations(guild_id, metrics)
            }

            # Format report
            if format == "json":
                return report
            elif format == "csv":
                return self._convert_to_csv(report)
            elif format == "pdf":
                return await self._convert_to_pdf(report)
            else:
                return report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {}

    async def _process_events(self):
        """Background task to process analytics events."""
        while self._is_running:
            try:
                # Flush events periodically
                await asyncio.sleep(self.config['event_flush_interval'])
                await self._flush_events()

                # Analyze patterns periodically
                await self._analyze_patterns()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processing: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def _flush_events(self):
        """Flush events from queue to database."""
        if not self.event_queue:
            return

        events = []
        while self.event_queue and len(events) < self.config['event_batch_size']:
            events.append(self.event_queue.popleft())

        if not events:
            return

        try:
            # Batch insert events
            query = """
                INSERT INTO user_analytics (user_id, guild_id, event_type, event_data, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """

            values = [
                (event.user_id, event.guild_id, event.event_type,
                 json.dumps(event.event_data), event.timestamp)
                for event in events
            ]

            await self.db_manager.executemany(query, values)
            logger.debug(f"Flushed {len(events)} analytics events")

        except Exception as e:
            logger.error(f"Error flushing events: {e}")

    async def _analyze_patterns(self):
        """Analyze betting patterns for all active users."""
        try:
            # Get active users
            query = """
                SELECT DISTINCT user_id, guild_id
                FROM user_analytics
                WHERE timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            active_users = await self.db_manager.fetch_all(query)

            for user in active_users:
                patterns = await self.detect_betting_patterns(user['user_id'], user['guild_id'])
                if patterns:
                    await self._store_patterns(patterns)

        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")

    async def _store_patterns(self, patterns: List[BettingPattern]):
        """Store betting patterns in database."""
        if not patterns:
            return

        try:
            query = """
                INSERT INTO betting_patterns (user_id, guild_id, pattern_type, pattern_data, confidence_score)
                VALUES (%s, %s, %s, %s, %s)
            """

            values = [
                (pattern.user_id, pattern.guild_id, pattern.pattern_type,
                 json.dumps(pattern.pattern_data), pattern.confidence_score)
                for pattern in patterns
            ]

            await self.db_manager.executemany(query, values)
            logger.debug(f"Stored {len(patterns)} betting patterns")

        except Exception as e:
            logger.error(f"Error storing patterns: {e}")

    def _detect_time_patterns(self, bets: List[Dict]) -> List[BettingPattern]:
        """Detect time-based betting patterns."""
        patterns = []

        # Group bets by hour of day
        hourly_bets = defaultdict(list)
        for bet in bets:
            hour = bet['created_at'].hour
            hourly_bets[hour].append(bet)

        # Find peak betting hours
        for hour, hour_bets in hourly_bets.items():
            if len(hour_bets) >= 5:  # Minimum threshold
                confidence = min(len(hour_bets) / len(bets), 1.0)
                if confidence >= self.config['min_confidence_score']:
                    patterns.append(BettingPattern(
                        user_id=bets[0]['user_id'],
                        guild_id=bets[0]['guild_id'],
                        pattern_type="peak_betting_hour",
                        pattern_data={"hour": hour, "bet_count": len(hour_bets)},
                        confidence_score=confidence
                    ))

        return patterns

    def _detect_bet_size_patterns(self, bets: List[Dict]) -> List[BettingPattern]:
        """Detect bet size patterns."""
        patterns = []

        if len(bets) < 10:
            return patterns

        # Calculate bet size statistics
        bet_sizes = [bet['amount'] for bet in bets]
        avg_size = sum(bet_sizes) / len(bet_sizes)

        # Detect consistent bet sizing
        consistent_bets = [bet for bet in bets if abs(bet['amount'] - avg_size) / avg_size < 0.2]
        if len(consistent_bets) >= len(bets) * 0.7:
            confidence = len(consistent_bets) / len(bets)
            patterns.append(BettingPattern(
                user_id=bets[0]['user_id'],
                guild_id=bets[0]['guild_id'],
                pattern_type="consistent_bet_sizing",
                pattern_data={"average_size": avg_size, "consistency_rate": confidence},
                confidence_score=confidence
            ))

        return patterns

    def _detect_sport_patterns(self, bets: List[Dict]) -> List[BettingPattern]:
        """Detect sport/league betting patterns."""
        patterns = []

        # Group bets by sport
        sport_bets = defaultdict(list)
        for bet in bets:
            sport = bet.get('sport', 'unknown')
            sport_bets[sport].append(bet)

        # Find favorite sports
        for sport, sport_bet_list in sport_bets.items():
            if len(sport_bet_list) >= 3:  # Minimum threshold
                confidence = len(sport_bet_list) / len(bets)
                if confidence >= self.config['min_confidence_score']:
                    patterns.append(BettingPattern(
                        user_id=bets[0]['user_id'],
                        guild_id=bets[0]['guild_id'],
                        pattern_type="favorite_sport",
                        pattern_data={"sport": sport, "bet_count": len(sport_bet_list)},
                        confidence_score=confidence
                    ))

        return patterns

    def _detect_outcome_patterns(self, bets: List[Dict]) -> List[BettingPattern]:
        """Detect win/loss patterns."""
        patterns = []

        if len(bets) < 10:
            return patterns

        # Analyze win streaks
        win_streaks = []
        current_streak = 0
        for bet in bets:
            if bet.get('result') == 'win':
                current_streak += 1
            else:
                if current_streak > 0:
                    win_streaks.append(current_streak)
                current_streak = 0

        if current_streak > 0:
            win_streaks.append(current_streak)

        # Detect significant win streaks
        if win_streaks:
            max_streak = max(win_streaks)
            if max_streak >= 3:
                confidence = min(max_streak / len(bets), 1.0)
                patterns.append(BettingPattern(
                    user_id=bets[0]['user_id'],
                    guild_id=bets[0]['guild_id'],
                    pattern_type="win_streak",
                    pattern_data={"max_streak": max_streak, "total_streaks": len(win_streaks)},
                    confidence_score=confidence
                ))

        return patterns

    async def _get_user_betting_data(self, user_id: int, guild_id: int,
                                   start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get user betting data for analysis."""
        query = """
            SELECT * FROM bets
            WHERE user_id = %s AND guild_id = %s
            AND created_at BETWEEN %s AND %s
            ORDER BY created_at DESC
        """
        return await self.db_manager.fetch_all(query, user_id, guild_id, start_date, end_date)

    async def _get_guild_data(self, guild_id: int, start_date: datetime,
                            end_date: datetime) -> Dict[str, Any]:
        """Get guild data for analysis."""
        # Get total users
        user_query = """
            SELECT COUNT(DISTINCT user_id) as total_users
            FROM bets WHERE guild_id = %s AND created_at BETWEEN %s AND %s
        """
        user_result = await self.db_manager.fetch_one(user_query, guild_id, start_date, end_date)

        # Get active users (users with bets in last 7 days)
        active_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM bets WHERE guild_id = %s AND created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
        """
        active_result = await self.db_manager.fetch_one(active_query, guild_id)

        # Get betting data
        bet_query = """
            SELECT * FROM bets
            WHERE guild_id = %s AND created_at BETWEEN %s AND %s
        """
        bets = await self.db_manager.fetch_all(bet_query, guild_id, start_date, end_date)

        return {
            'total_users': user_result['total_users'] if user_result else 0,
            'active_users': active_result['active_users'] if active_result else 0,
            'total_bets': len(bets),
            'total_volume': sum(bet['amount'] for bet in bets),
            'avg_win_rate': self._calculate_win_rate(bets),
            'avg_bet_size': self._calculate_avg_bet_size(bets),
            'bets': bets
        }

    def _calculate_win_rate(self, bets: List[Dict]) -> float:
        """Calculate win rate from betting data."""
        if not bets:
            return 0.0

        wins = sum(1 for bet in bets if bet.get('result') == 'win')
        return wins / len(bets)

    def _calculate_avg_bet_size(self, bets: List[Dict]) -> float:
        """Calculate average bet size."""
        if not bets:
            return 0.0

        total_amount = sum(bet['amount'] for bet in bets)
        return total_amount / len(bets)

    def _get_favorite_sports(self, bets: List[Dict]) -> List[Dict]:
        """Get user's favorite sports."""
        sport_counts = defaultdict(int)
        for bet in bets:
            sport = bet.get('sport', 'unknown')
            sport_counts[sport] += 1

        return [{'sport': sport, 'count': count}
                for sport, count in sorted(sport_counts.items(), key=lambda x: x[1], reverse=True)]

    def _get_popular_sports(self, bets: List[Dict]) -> List[Dict]:
        """Get popular sports in guild."""
        sport_counts = defaultdict(int)
        for bet in bets:
            sport = bet.get('sport', 'unknown')
            sport_counts[sport] += 1

        return [{'sport': sport, 'count': count}
                for sport, count in sorted(sport_counts.items(), key=lambda x: x[1], reverse=True)]

    def _calculate_risk_profile(self, bets: List[Dict]) -> str:
        """Calculate user's risk profile."""
        if not bets:
            return "unknown"

        avg_bet_size = self._calculate_avg_bet_size(bets)
        win_rate = self._calculate_win_rate(bets)

        if avg_bet_size > 100 and win_rate < 0.4:
            return "high_risk"
        elif avg_bet_size > 50 or win_rate < 0.5:
            return "medium_risk"
        else:
            return "low_risk"

    def _get_start_date(self, time_range: str) -> datetime:
        """Get start date based on time range."""
        now = datetime.utcnow()

        if time_range == "1d":
            return now - timedelta(days=1)
        elif time_range == "7d":
            return now - timedelta(days=7)
        elif time_range == "30d":
            return now - timedelta(days=30)
        elif time_range == "90d":
            return now - timedelta(days=90)
        else:
            return now - timedelta(days=30)  # Default to 30 days

    async def _analyze_betting_trends(self, user_id: int, guild_id: int,
                                    start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze betting trends for a user."""
        # This would implement trend analysis logic
        # For now, return basic structure
        return {
            'trend_direction': 'stable',
            'volume_trend': 'increasing',
            'win_rate_trend': 'stable'
        }

    async def _calculate_engagement_score(self, user_id: int, guild_id: int,
                                        start_date: datetime, end_date: datetime) -> float:
        """Calculate user engagement score."""
        # This would implement engagement scoring logic
        # For now, return a placeholder
        return 0.75

    async def _get_performance_rank(self, user_id: int, guild_id: int) -> int:
        """Get user's performance rank in guild."""
        # This would implement ranking logic
        # For now, return a placeholder
        return 5

    async def _calculate_guild_engagement(self, guild_id: int, start_date: datetime,
                                        end_date: datetime) -> float:
        """Calculate guild engagement score."""
        # This would implement guild engagement logic
        # For now, return a placeholder
        return 0.65

    async def _analyze_guild_trends(self, guild_id: int, start_date: datetime,
                                  end_date: datetime) -> Dict[str, Any]:
        """Analyze guild betting trends."""
        # This would implement guild trend analysis
        # For now, return basic structure
        return {
            'user_growth': 'positive',
            'volume_growth': 'stable',
            'engagement_trend': 'increasing'
        }

    async def _get_top_performers(self, guild_id: int, start_date: datetime,
                                end_date: datetime) -> List[Dict]:
        """Get top performing users in guild."""
        # This would implement top performers logic
        # For now, return placeholder
        return [
            {'user_id': 123, 'username': 'User1', 'win_rate': 0.75, 'total_bets': 50},
            {'user_id': 456, 'username': 'User2', 'win_rate': 0.68, 'total_bets': 45}
        ]

    async def _calculate_retention_rate(self, guild_id: int, start_date: datetime,
                                      end_date: datetime) -> float:
        """Calculate user retention rate."""
        # This would implement retention calculation
        # For now, return placeholder
        return 0.82

    async def _get_guild_user_patterns(self, guild_id: int) -> List[Dict]:
        """Get betting patterns for all users in guild."""
        query = """
            SELECT * FROM betting_patterns
            WHERE guild_id = %s
            ORDER BY confidence_score DESC
            LIMIT 100
        """
        return await self.db_manager.fetch_all(query, guild_id)

    async def _generate_recommendations(self, guild_id: int, metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analytics."""
        recommendations = []

        if metrics.get('avg_win_rate', 0) < 0.5:
            recommendations.append("Consider implementing betting education programs")

        if metrics.get('user_engagement', 0) < 0.6:
            recommendations.append("Increase user engagement through community events")

        if metrics.get('retention_rate', 0) < 0.8:
            recommendations.append("Focus on user retention strategies")

        return recommendations

    def _convert_to_csv(self, report: Dict[str, Any]) -> str:
        """Convert report to CSV format."""
        # This would implement CSV conversion
        # For now, return JSON as string
        return json.dumps(report)

    async def _convert_to_pdf(self, report: Dict[str, Any]) -> str:
        """Convert report to PDF format."""
        # This would implement PDF conversion
        # For now, return JSON as string
        return json.dumps(report)

# Global analytics service instance
analytics_service = None

async def initialize_analytics_service(db_manager: DatabaseManager):
    """Initialize the global analytics service."""
    global analytics_service
    analytics_service = AnalyticsService(db_manager)
    await analytics_service.start()
    logger.info("Analytics service initialized")

async def get_analytics_service() -> AnalyticsService:
    """Get the global analytics service instance."""
    return analytics_service
