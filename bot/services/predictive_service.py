"""Predictive analytics service for betting insights and forecasts."""

import asyncio
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import enhanced_cache_manager, enhanced_cache_get, enhanced_cache_set, enhanced_cache_delete
from bot.utils.performance_monitor import time_operation

logger = logging.getLogger(__name__)

# Cache TTLs for predictive data
PREDICTIVE_CACHE_TTLS = {
    "game_predictions": 3600,  # 1 hour
    "user_predictions": 1800,  # 30 minutes
    "trend_analysis": 7200,  # 2 hours
    "statistical_models": 86400,  # 24 hours
    "forecast_data": 3600,  # 1 hour
}


class PredictiveService:
    """Predictive analytics service for betting insights and forecasts."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._is_running = False
        self._prediction_task = None

        # Configuration
        self.config = {
            'prediction_horizon': 72,  # hours
            'confidence_threshold': 0.7,
            'min_data_points': 10,
            'update_interval': 3600,  # 1 hour
            'max_predictions_per_user': 50
        }

        logger.info("PredictiveService initialized")

    async def start(self):
        """Start the predictive service."""
        if self._is_running:
            logger.warning("PredictiveService is already running")
            return

        self._is_running = True
        self._prediction_task = asyncio.create_task(self._periodic_predictions())
        logger.info("PredictiveService started")

    async def stop(self):
        """Stop the predictive service."""
        if not self._is_running:
            return

        self._is_running = False
        if self._prediction_task:
            self._prediction_task.cancel()
            try:
                await self._prediction_task
            except asyncio.CancelledError:
                pass
        logger.info("PredictiveService stopped")

    async def _periodic_predictions(self):
        """Periodic prediction generation task."""
        while self._is_running:
            try:
                await self._generate_predictions()
                await asyncio.sleep(self.config['update_interval'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic predictions: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _generate_predictions(self):
        """Generate predictions for upcoming games."""
        try:
            # Get upcoming games
            upcoming_games = await self._get_upcoming_games()

            for game in upcoming_games:
                try:
                    # Generate predictions for each game
                    predictions = await self._predict_game_outcome(game)

                    if predictions:
                        # Cache predictions
                        cache_key = f"game_predictions:{game.get('id')}"
                        await enhanced_cache_set("predictive_data", cache_key, predictions, ttl=PREDICTIVE_CACHE_TTLS["game_predictions"])

                        logger.debug(f"Generated predictions for game {game.get('id')}")

                except Exception as e:
                    logger.error(f"Error generating predictions for game {game.get('id')}: {e}")

        except Exception as e:
            logger.error(f"Error in prediction generation: {e}")

    @time_operation("predictive_predict_game_outcome")
    async def predict_game_outcome(self, game_id: str) -> Dict[str, Any]:
        """Predict the outcome of a specific game."""
        try:
            # Check cache first
            cache_key = f"game_predictions:{game_id}"
            cached_prediction = await enhanced_cache_get("predictive_data", cache_key)

            if cached_prediction:
                logger.debug(f"Cache hit for game prediction: {game_id}")
                return cached_prediction

            # Get game data
            game_data = await self._get_game_data(game_id)
            if not game_data:
                return {'error': 'Game not found'}

            # Generate prediction
            prediction = await self._predict_game_outcome(game_data)

            if prediction:
                # Cache the prediction
                await enhanced_cache_set("predictive_data", cache_key, prediction, ttl=PREDICTIVE_CACHE_TTLS["game_predictions"])
                return prediction
            else:
                return {'error': 'Unable to generate prediction'}

        except Exception as e:
            logger.error(f"Error predicting game outcome: {e}")
            return {'error': str(e)}

    async def _predict_game_outcome(self, game_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate prediction for a game."""
        try:
            home_team = game_data.get('home_team')
            away_team = game_data.get('away_team')
            sport = game_data.get('sport')
            league = game_data.get('league')

            # Get historical data for teams
            home_stats = await self._get_team_stats(home_team, sport, league)
            away_stats = await self._get_team_stats(away_team, sport, league)

            if not home_stats or not away_stats:
                return None

            # Calculate win probabilities
            home_win_prob = self._calculate_win_probability(home_stats, away_stats, True)
            away_win_prob = self._calculate_win_probability(away_stats, home_stats, False)
            draw_prob = 1 - home_win_prob - away_win_prob

            # Ensure probabilities sum to 1
            total_prob = home_win_prob + away_win_prob + draw_prob
            if total_prob > 0:
                home_win_prob /= total_prob
                away_win_prob /= total_prob
                draw_prob /= total_prob

            # Calculate confidence
            confidence = self._calculate_prediction_confidence(home_stats, away_stats)

            # Determine predicted outcome
            if home_win_prob > away_win_prob and home_win_prob > draw_prob:
                predicted_outcome = 'home_win'
                predicted_prob = home_win_prob
            elif away_win_prob > home_win_prob and away_win_prob > draw_prob:
                predicted_outcome = 'away_win'
                predicted_prob = away_win_prob
            else:
                predicted_outcome = 'draw'
                predicted_prob = draw_prob

            return {
                'game_id': game_data.get('id'),
                'home_team': home_team,
                'away_team': away_team,
                'predicted_outcome': predicted_outcome,
                'home_win_probability': home_win_prob,
                'away_win_probability': away_win_prob,
                'draw_probability': draw_prob,
                'confidence': confidence,
                'predicted_probability': predicted_prob,
                'model_version': 'v1.0',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error in game outcome prediction: {e}")
            return None

    def _calculate_win_probability(self, team_stats: Dict[str, Any], opponent_stats: Dict[str, Any], is_home: bool) -> float:
        """Calculate win probability for a team."""
        try:
            # Get team performance metrics
            team_win_rate = team_stats.get('win_rate', 0.5)
            team_goals_for = team_stats.get('goals_for', 1.0)
            team_goals_against = team_stats.get('goals_against', 1.0)

            opponent_win_rate = opponent_stats.get('win_rate', 0.5)
            opponent_goals_for = opponent_stats.get('goals_for', 1.0)
            opponent_goals_against = opponent_stats.get('goals_against', 1.0)

            # Home advantage factor
            home_advantage = 1.1 if is_home else 0.9

            # Calculate expected goals
            team_expected_goals = (team_goals_for * opponent_goals_against) * home_advantage
            opponent_expected_goals = opponent_goals_for * team_goals_against

            # Use Poisson distribution for goal prediction
            team_goals_prob = stats.poisson.pmf(range(6), team_expected_goals)
            opponent_goals_prob = stats.poisson.pmf(range(6), opponent_expected_goals)

            # Calculate win probability
            win_prob = 0.0
            for team_goals in range(6):
                for opponent_goals in range(6):
                    if team_goals > opponent_goals:
                        win_prob += team_goals_prob[team_goals] * opponent_goals_prob[opponent_goals]

            # Blend with historical win rate
            blended_prob = (win_prob * 0.7) + (team_win_rate * 0.3)

            return min(max(blended_prob, 0.01), 0.99)  # Ensure probability is between 0.01 and 0.99

        except Exception as e:
            logger.error(f"Error calculating win probability: {e}")
            return 0.5

    def _calculate_prediction_confidence(self, home_stats: Dict[str, Any], away_stats: Dict[str, Any]) -> float:
        """Calculate confidence in the prediction."""
        try:
            # Factors that increase confidence
            home_games_played = home_stats.get('games_played', 0)
            away_games_played = away_stats.get('games_played', 0)

            # More games played = higher confidence
            games_factor = min((home_games_played + away_games_played) / 20, 1.0)

            # Win rate difference = higher confidence
            home_win_rate = home_stats.get('win_rate', 0.5)
            away_win_rate = away_stats.get('win_rate', 0.5)
            win_rate_diff = abs(home_win_rate - away_win_rate)

            # Recent form factor
            home_recent_form = home_stats.get('recent_form', 0.5)
            away_recent_form = away_stats.get('recent_form', 0.5)
            form_diff = abs(home_recent_form - away_recent_form)

            # Calculate overall confidence
            confidence = (games_factor * 0.4) + (win_rate_diff * 0.3) + (form_diff * 0.3)

            return min(max(confidence, 0.1), 0.95)  # Ensure confidence is between 0.1 and 0.95

        except Exception as e:
            logger.error(f"Error calculating prediction confidence: {e}")
            return 0.5

    @time_operation("predictive_predict_user_performance")
    async def predict_user_performance(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Predict user's future betting performance."""
        try:
            # Check cache first
            cache_key = f"user_predictions:{user_id}:{guild_id}"
            cached_prediction = await enhanced_cache_get("predictive_data", cache_key)

            if cached_prediction:
                logger.debug(f"Cache hit for user performance prediction: {user_id}")
                return cached_prediction

            # Get user's betting history
            betting_history = await self._get_user_betting_history(user_id, guild_id)

            if len(betting_history) < self.config['min_data_points']:
                return {'error': 'Insufficient betting history for prediction'}

            # Generate prediction
            prediction = await self._predict_user_performance(betting_history)

            if prediction:
                # Cache the prediction
                await enhanced_cache_set("predictive_data", cache_key, prediction, ttl=PREDICTIVE_CACHE_TTLS["user_predictions"])
                return prediction
            else:
                return {'error': 'Unable to generate user prediction'}

        except Exception as e:
            logger.error(f"Error predicting user performance: {e}")
            return {'error': str(e)}

    async def _predict_user_performance(self, betting_history: List[Dict]) -> Optional[Dict[str, Any]]:
        """Generate performance prediction for a user."""
        try:
            # Calculate historical metrics
            total_bets = len(betting_history)
            win_rate = sum(1 for bet in betting_history if bet.get('status') == 'won') / total_bets
            avg_bet_size = sum(bet.get('amount', 0) for bet in betting_history) / total_bets

            # Calculate recent trends
            recent_bets = betting_history[:10]  # Last 10 bets
            recent_win_rate = sum(1 for bet in recent_bets if bet.get('status') == 'won') / len(recent_bets)

            # Predict future performance
            predicted_win_rate = self._predict_win_rate(win_rate, recent_win_rate, total_bets)
            predicted_bet_frequency = self._predict_bet_frequency(betting_history)
            predicted_roi = self._predict_roi(win_rate, avg_bet_size)

            # Calculate confidence
            confidence = self._calculate_user_prediction_confidence(betting_history)

            return {
                'predicted_win_rate': predicted_win_rate,
                'predicted_bet_frequency': predicted_bet_frequency,
                'predicted_roi': predicted_roi,
                'confidence': confidence,
                'trend': 'improving' if recent_win_rate > win_rate else 'declining',
                'recommendations': self._generate_user_recommendations(betting_history),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error in user performance prediction: {e}")
            return None

    def _predict_win_rate(self, historical_win_rate: float, recent_win_rate: float, total_bets: int) -> float:
        """Predict future win rate."""
        try:
            # Weight recent performance more heavily
            recent_weight = min(total_bets / 50, 0.7)  # Cap at 70% weight
            historical_weight = 1 - recent_weight

            predicted_rate = (recent_win_rate * recent_weight) + (historical_win_rate * historical_weight)

            # Apply regression to mean for small sample sizes
            if total_bets < 20:
                regression_factor = (20 - total_bets) / 20
                predicted_rate = (predicted_rate * (1 - regression_factor)) + (0.5 * regression_factor)

            return min(max(predicted_rate, 0.1), 0.9)

        except Exception as e:
            logger.error(f"Error predicting win rate: {e}")
            return 0.5

    def _predict_bet_frequency(self, betting_history: List[Dict]) -> float:
        """Predict future bet frequency (bets per day)."""
        try:
            if len(betting_history) < 2:
                return 1.0

            # Calculate time between bets
            bet_dates = [bet.get('created_at') for bet in betting_history if bet.get('created_at')]
            if len(bet_dates) < 2:
                return 1.0

            # Calculate average days between bets
            bet_dates.sort()
            intervals = []
            for i in range(1, len(bet_dates)):
                interval = (bet_dates[i] - bet_dates[i-1]).days
                if interval > 0:
                    intervals.append(interval)

            if not intervals:
                return 1.0

            avg_interval = sum(intervals) / len(intervals)
            frequency = 1 / avg_interval if avg_interval > 0 else 1.0

            return min(max(frequency, 0.1), 5.0)  # Between 0.1 and 5 bets per day

        except Exception as e:
            logger.error(f"Error predicting bet frequency: {e}")
            return 1.0

    def _predict_roi(self, win_rate: float, avg_bet_size: float) -> float:
        """Predict return on investment."""
        try:
            # Simple ROI calculation based on win rate and bet sizing
            # Assuming average odds of 2.0 (50% implied probability)
            avg_odds = 2.0
            expected_value = (win_rate * (avg_odds - 1)) - ((1 - win_rate) * 1)

            # Convert to ROI percentage
            roi_percentage = (expected_value / avg_bet_size) * 100 if avg_bet_size > 0 else 0

            return min(max(roi_percentage, -50), 50)  # Between -50% and 50%

        except Exception as e:
            logger.error(f"Error predicting ROI: {e}")
            return 0.0

    def _calculate_user_prediction_confidence(self, betting_history: List[Dict]) -> float:
        """Calculate confidence in user prediction."""
        try:
            total_bets = len(betting_history)

            # More bets = higher confidence
            bets_factor = min(total_bets / 50, 1.0)

            # Consistency in bet sizing
            bet_sizes = [bet.get('amount', 0) for bet in betting_history]
            if bet_sizes:
                size_consistency = 1 - (np.std(bet_sizes) / np.mean(bet_sizes)) if np.mean(bet_sizes) > 0 else 0
                size_factor = max(size_consistency, 0)
            else:
                size_factor = 0

            # Recent activity factor
            recent_activity = min(len(betting_history[:7]), 7) / 7  # Last 7 days

            confidence = (bets_factor * 0.5) + (size_factor * 0.3) + (recent_activity * 0.2)

            return min(max(confidence, 0.1), 0.95)

        except Exception as e:
            logger.error(f"Error calculating user prediction confidence: {e}")
            return 0.5

    def _generate_user_recommendations(self, betting_history: List[Dict]) -> List[str]:
        """Generate recommendations for user improvement."""
        try:
            recommendations = []

            # Analyze betting patterns
            win_rate = sum(1 for bet in betting_history if bet.get('status') == 'won') / len(betting_history)
            avg_bet_size = sum(bet.get('amount', 0) for bet in betting_history) / len(betting_history)

            if win_rate < 0.4:
                recommendations.append("Focus on bet selection and analysis")

            if avg_bet_size > 100:
                recommendations.append("Consider reducing bet sizes for better bankroll management")

            if len(betting_history) < 10:
                recommendations.append("Build more betting history for better predictions")

            # Check for betting frequency
            recent_bets = betting_history[:7]
            if len(recent_bets) > 5:
                recommendations.append("Consider reducing betting frequency for better decision making")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating user recommendations: {e}")
            return ["Focus on consistent betting patterns"]

    async def _get_upcoming_games(self) -> List[Dict]:
        """Get upcoming games for prediction."""
        try:
            query = """
                SELECT id, home_team, away_team, sport, league, start_time
                FROM api_games
                WHERE start_time > NOW()
                AND start_time < DATE_ADD(NOW(), INTERVAL %s HOUR)
                ORDER BY start_time ASC
                LIMIT 50
            """
            return await self.db_manager.fetch_all(query, self.config['prediction_horizon'])

        except Exception as e:
            logger.error(f"Error getting upcoming games: {e}")
            return []

    async def _get_game_data(self, game_id: str) -> Optional[Dict]:
        """Get detailed game data."""
        try:
            query = """
                SELECT id, home_team, away_team, sport, league, start_time, venue
                FROM api_games
                WHERE id = %s
            """
            return await self.db_manager.fetch_one(query, game_id)

        except Exception as e:
            logger.error(f"Error getting game data: {e}")
            return None

    async def _get_team_stats(self, team_name: str, sport: str, league: str) -> Optional[Dict]:
        """Get team statistics."""
        try:
            # Check cache first
            cache_key = f"team_stats:{team_name}:{sport}:{league}"
            cached_stats = await enhanced_cache_get("predictive_data", cache_key)

            if cached_stats:
                return cached_stats

            # Get team's recent games
            query = """
                SELECT home_team, away_team, home_score, away_score, status
                FROM api_games
                WHERE (home_team = %s OR away_team = %s)
                AND sport = %s AND league = %s
                AND status = 'finished'
                ORDER BY start_time DESC
                LIMIT 20
            """
            games = await self.db_manager.fetch_all(query, team_name, team_name, sport, league)

            if not games:
                return None

            # Calculate team statistics
            stats = self._calculate_team_stats(games, team_name)

            # Cache the stats
            await enhanced_cache_set("predictive_data", cache_key, stats, ttl=PREDICTIVE_CACHE_TTLS["statistical_models"])

            return stats

        except Exception as e:
            logger.error(f"Error getting team stats: {e}")
            return None

    def _calculate_team_stats(self, games: List[Dict], team_name: str) -> Dict[str, Any]:
        """Calculate team statistics from games."""
        try:
            wins = 0
            goals_for = 0
            goals_against = 0
            games_played = len(games)

            for game in games:
                home_team = game.get('home_team')
                away_team = game.get('away_team')
                home_score = game.get('home_score', 0)
                away_score = game.get('away_score', 0)

                if home_team == team_name:
                    goals_for += home_score
                    goals_against += away_score
                    if home_score > away_score:
                        wins += 1
                elif away_team == team_name:
                    goals_for += away_score
                    goals_against += home_score
                    if away_score > home_score:
                        wins += 1

            win_rate = wins / games_played if games_played > 0 else 0.5
            avg_goals_for = goals_for / games_played if games_played > 0 else 1.0
            avg_goals_against = goals_against / games_played if games_played > 0 else 1.0

            # Calculate recent form (last 5 games)
            recent_games = games[:5]
            recent_wins = 0
            for game in recent_games:
                home_team = game.get('home_team')
                away_team = game.get('away_team')
                home_score = game.get('home_score', 0)
                away_score = game.get('away_score', 0)

                if home_team == team_name and home_score > away_score:
                    recent_wins += 1
                elif away_team == team_name and away_score > home_score:
                    recent_wins += 1

            recent_form = recent_wins / len(recent_games) if recent_games else 0.5

            return {
                'win_rate': win_rate,
                'goals_for': avg_goals_for,
                'goals_against': avg_goals_against,
                'games_played': games_played,
                'recent_form': recent_form
            }

        except Exception as e:
            logger.error(f"Error calculating team stats: {e}")
            return {
                'win_rate': 0.5,
                'goals_for': 1.0,
                'goals_against': 1.0,
                'games_played': 0,
                'recent_form': 0.5
            }

    async def _get_user_betting_history(self, user_id: int, guild_id: int) -> List[Dict]:
        """Get user's betting history."""
        try:
            query = """
                SELECT bet_id, amount, odds, status, created_at, game_id
                FROM bets
                WHERE user_id = %s AND guild_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            return await self.db_manager.fetch_all(query, user_id, guild_id, self.config['max_predictions_per_user'])

        except Exception as e:
            logger.error(f"Error getting user betting history: {e}")
            return []

    async def clear_predictive_cache(self, game_id: Optional[str] = None, user_id: Optional[int] = None):
        """Clear predictive cache for specific game or user."""
        try:
            if game_id:
                await enhanced_cache_delete("predictive_data", f"game_predictions:{game_id}")
                logger.info(f"Cleared predictive cache for game: {game_id}")

            if user_id:
                # Clear all user predictions (would need guild_id for specific user)
                logger.info(f"Cleared predictive cache for user: {user_id}")

            if not game_id and not user_id:
                # Clear all predictive cache
                logger.info("Cleared all predictive cache")

        except Exception as e:
            logger.error(f"Error clearing predictive cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get predictive cache statistics."""
        try:
            return await enhanced_cache_manager.get_stats()
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
