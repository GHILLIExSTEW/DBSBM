# betting-bot/services/analytics_service.py

import discord
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone

try:
    from ..utils.errors import AnalyticsServiceError
except ImportError:
    from utils.errors import AnalyticsServiceError

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db = db_manager
        logger.info("AnalyticsService initialized") # Added log for consistency

    async def start(self): # ### ADDED THIS METHOD ###
        """Start the AnalyticsService and perform any necessary setup."""
        logger.info("AnalyticsService started successfully.")
        # Add any specific startup logic for analytics here if needed

    async def stop(self): # ### ADDED THIS METHOD ###
        """Stop the AnalyticsService and perform any necessary cleanup."""
        logger.info("AnalyticsService stopped.")
        # Add any specific cleanup logic here if needed

    async def get_user_stats(self, guild_id: int, user_id: int) -> Dict[str, Any]:
        # ... (rest of your existing method)
        try:
            stats = await self.db.fetch_one("""
                SELECT
                    COUNT(b.bet_serial) as total_bets,
                    SUM(CASE WHEN b.status = 'won' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN b.status = 'lost' THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN b.status = 'push' THEN 1 ELSE 0 END) as pushes,
                    COALESCE(SUM(ur.monthly_result_value), 0.0) as net_units
                FROM bets b
                LEFT JOIN unit_records ur ON b.bet_serial = ur.bet_serial
                WHERE b.guild_id = %s AND b.user_id = %s
                AND b.status IN ('won', 'lost', 'push')
            """, guild_id, user_id)

            if not stats or (stats.get('total_bets') or 0) == 0:
                return {'total_bets': 0, 'wins': 0, 'losses': 0, 'pushes': 0, 'win_rate': 0.0, 'net_units': 0.0, 'roi': 0.0}

            wins = stats.get('wins') or 0
            losses = stats.get('losses') or 0
            total_bets = stats.get('total_bets') or 0
            net_units = float(stats.get('net_units') or 0.0)

            total_resolved_for_winrate = wins + losses
            win_rate = (wins / total_resolved_for_winrate * 100) if total_resolved_for_winrate > 0 else 0.0

            # Assuming 'stake' is the column name for units risked in the 'bets' table.
            # The original query in your files used 'units' for stake, and 'result_value' for payout in unit_records.
            # For ROI, we need total units risked (staked).
            total_risked_result = await self.db.fetch_one("""
                SELECT COALESCE(SUM(units), 0) as total_risked 
                FROM bets
                WHERE guild_id = %s AND user_id = %s
                AND status IN ('won', 'lost', 'push')
            """, guild_id, user_id)
            total_risked = float(total_risked_result.get('total_risked') or 0) if total_risked_result else 0.0

            roi = (net_units / total_risked * 100.0) if total_risked > 0 else 0.0

            return {
                'total_bets': total_bets, 'wins': wins, 'losses': losses,
                'pushes': stats.get('pushes') or 0,
                'win_rate': win_rate, 'net_units': net_units, 'roi': roi
            }
        except Exception as e:
            logger.exception(f"Error getting user stats for user {user_id} in guild {guild_id}: {e}")
            raise AnalyticsServiceError(f"Failed to get user stats: {str(e)}")

    async def get_guild_stats(self, guild_id: int) -> Dict[str, Any]:
        # ... (rest of your existing method)
        try:
            stats = await self.db.fetch_one("""
                SELECT
                    COUNT(b.bet_serial) as total_bets,
                    SUM(CASE WHEN b.status = 'won' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN b.status = 'lost' THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN b.status = 'push' THEN 1 ELSE 0 END) as pushes,
                    COALESCE(SUM(ur.monthly_result_value), 0.0) as net_units,
                    COUNT(DISTINCT b.user_id) as total_cappers
                FROM bets b
                LEFT JOIN unit_records ur ON b.bet_serial = ur.bet_serial
                WHERE b.guild_id = %s
                AND b.status IN ('won', 'lost', 'push')
            """, guild_id)

            if not stats or (stats.get('total_bets') or 0) == 0:
                return {'total_bets': 0, 'wins': 0, 'losses': 0, 'pushes': 0, 'win_rate': 0.0, 'net_units': 0.0, 'total_cappers': 0, 'roi': 0.0}

            wins = float(stats.get('wins') or 0)
            losses = float(stats.get('losses') or 0)
            total_bets = stats.get('total_bets') or 0
            net_units = float(stats.get('net_units') or 0.0)

            total_resolved_for_winrate = wins + losses
            win_rate = (wins / total_resolved_for_winrate * 100.0) if total_resolved_for_winrate > 0 else 0.0

            total_risked_result = await self.db.fetch_one("""
                SELECT COALESCE(SUM(units), 0) as total_risked
                FROM bets
                WHERE guild_id = %s AND status IN ('won', 'lost', 'push')
            """, guild_id)
            total_risked = float(total_risked_result.get('total_risked') or 0) if total_risked_result else 0.0
            roi = (net_units / total_risked * 100.0) if total_risked > 0 else 0.0

            return {
                'total_bets': total_bets, 'wins': wins, 'losses': losses,
                'pushes': stats.get('pushes') or 0, 'win_rate': win_rate,
                'net_units': net_units, 'total_cappers': stats.get('total_cappers') or 0, 'roi': roi
            }
        except Exception as e:
            logger.exception(f"Error getting guild stats for guild {guild_id}: {e}")
            raise AnalyticsServiceError(f"Failed to get guild stats: {str(e)}")

    async def get_leaderboard(self, guild_id: int, metric: str = "net_units", limit: int = 10) -> List[Dict]:
        """Get leaderboard data for cappers sorted by specified metric."""
        try:
            # Build the ORDER BY clause based on metric
            order_by_clause = ""
            if metric == "net_units":
                order_by_clause = "ORDER BY net_units DESC"
            elif metric == "win_rate":
                order_by_clause = "ORDER BY win_rate DESC"
            elif metric == "total_bets":
                order_by_clause = "ORDER BY total_resolved_bets DESC"
            elif metric == "roi":
                order_by_clause = "ORDER BY roi DESC"
            else:
                order_by_clause = "ORDER BY net_units DESC"  # Default
            
            query = f"""
                SELECT
                    b.user_id,
                    COALESCE(c.display_name, CONCAT('User ', b.user_id)) as username,
                    SUM(CASE WHEN b.status IN ('won', 'lost', 'push') THEN 1 ELSE 0 END) as total_resolved_bets,
                    SUM(CASE WHEN b.status = 'won' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN b.status = 'lost' THEN 1 ELSE 0 END) as losses,
                    COALESCE(SUM(ur.monthly_result_value), 0.0) as net_units,
                    COALESCE(SUM(CASE WHEN b.status IN ('won', 'lost', 'push') THEN b.units ELSE 0 END), 0.0) as total_risked,
                    CASE 
                        WHEN SUM(CASE WHEN b.status IN ('won', 'lost', 'push') THEN 1 ELSE 0 END) > 0 
                        THEN (SUM(CASE WHEN b.status = 'won' THEN 1 ELSE 0 END) * 100.0) / SUM(CASE WHEN b.status IN ('won', 'lost', 'push') THEN 1 ELSE 0 END)
                        ELSE 0.0 
                    END as win_rate,
                    CASE 
                        WHEN COALESCE(SUM(CASE WHEN b.status IN ('won', 'lost', 'push') THEN b.units ELSE 0 END), 0.0) > 0 
                        THEN (COALESCE(SUM(ur.monthly_result_value), 0.0) / COALESCE(SUM(CASE WHEN b.status IN ('won', 'lost', 'push') THEN b.units ELSE 0 END), 0.0)) * 100.0
                        ELSE 0.0 
                    END as roi
                FROM bets b
                LEFT JOIN unit_records ur ON b.bet_serial = ur.bet_serial
                LEFT JOIN cappers c ON b.user_id = c.user_id AND c.guild_id = b.guild_id
                WHERE b.guild_id = %s
                GROUP BY b.user_id, c.display_name
                HAVING total_resolved_bets > 0
                {order_by_clause}
                LIMIT %s
            """
            
            results = await self.db.fetch_all(query, (guild_id, limit))
            
            # Convert to list of dictionaries and ensure proper data types
            leaderboard_data = []
            for row in results:
                leaderboard_data.append({
                    'user_id': row['user_id'],
                    'username': row['username'],
                    'total_bets': row['total_resolved_bets'],
                    'wins': row['wins'],
                    'losses': row['losses'],
                    'net_units': float(row['net_units']),
                    'win_rate': float(row['win_rate']),
                    'roi': float(row['roi']),
                    'total_risked': float(row['total_risked'])
                })
            
            return leaderboard_data
            
        except Exception as e:
            logger.error(f"Error getting leaderboard for guild {guild_id}: {str(e)}")
            raise AnalyticsServiceError(f"Failed to get leaderboard: {str(e)}")
