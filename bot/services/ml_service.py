"""Machine Learning Service for DBSBM System.

This service provides ML-powered features including:
- Smart bet recommendations based on user history
- Odds movement prediction and alerts
- Value bet identification using statistical models
- Portfolio optimization suggestions
- Risk management recommendations
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict
import pickle
import joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
import pandas as pd

from data.db_manager import DatabaseManager
from data.cache_manager import cache_get, cache_set
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

@dataclass
class MLPrediction:
    """Represents an ML prediction."""
    model_type: str
    prediction_data: Dict[str, Any]
    confidence_score: float
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class BetRecommendation:
    """Represents a bet recommendation."""
    user_id: int
    guild_id: int
    recommendation_type: str
    confidence_score: float
    reasoning: str
    expected_value: float
    risk_level: str
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class OddsPrediction:
    """Represents an odds movement prediction."""
    game_id: str
    current_odds: float
    predicted_odds: float
    movement_direction: str
    confidence_score: float
    prediction_horizon: int  # hours
    created_at: datetime = field(default_factory=datetime.utcnow)

class MLService:
    """Machine learning service for betting insights and predictions."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.models = {}  # Cache for trained models
        self.scalers = {}  # Cache for data scalers
        self.model_versions = {}  # Track model versions
        self._training_task = None
        self._is_running = False

        # ML configuration
        self.config = {
            'model_retrain_interval': 86400,  # 24 hours
            'prediction_cache_ttl': 3600,  # 1 hour
            'min_training_samples': 100,
            'max_prediction_horizon': 72,  # hours
            'confidence_threshold': 0.7,
            'model_types': ['bet_outcome', 'odds_movement', 'value_bet', 'user_behavior']
        }

        logger.info("MLService initialized")

    async def start(self):
        """Start the ML service."""
        if self._is_running:
            logger.warning("MLService is already running")
            return

        self._is_running = True
        self._training_task = asyncio.create_task(self._periodic_training())
        await self._load_models()
        logger.info("MLService started")

    async def stop(self):
        """Stop the ML service."""
        if not self._is_running:
            return

        self._is_running = False
        if self._training_task:
            self._training_task.cancel()
            try:
                await self._training_task
            except asyncio.CancelledError:
                pass
        logger.info("MLService stopped")

    @time_operation("ml_get_bet_recommendations")
    async def get_bet_recommendations(self, user_id: int, guild_id: int,
                                    limit: int = 5) -> List[BetRecommendation]:
        """Get personalized bet recommendations for a user."""
        try:
            # Get user's betting history and preferences
            user_data = await self._get_user_betting_data(user_id, guild_id)

            if not user_data or len(user_data['bets']) < 10:
                return []

            # Get available games
            available_games = await self._get_available_games()

            recommendations = []

            # Generate different types of recommendations
            value_bet_recs = await self._generate_value_bet_recommendations(
                user_id, guild_id, available_games, user_data
            )
            recommendations.extend(value_bet_recs)

            pattern_recs = await self._generate_pattern_based_recommendations(
                user_id, guild_id, available_games, user_data
            )
            recommendations.extend(pattern_recs)

            # Sort by expected value and confidence
            recommendations.sort(key=lambda x: x.expected_value * x.confidence_score, reverse=True)

            # Store recommendations
            await self._store_recommendations(recommendations[:limit])

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error getting bet recommendations: {e}")
            return []

    @time_operation("ml_predict_odds_movement")
    async def predict_odds_movement(self, game_id: str,
                                  prediction_horizon: int = 24) -> Optional[OddsPrediction]:
        """Predict odds movement for a specific game."""
        try:
            # Get current odds
            current_odds = await self._get_current_odds(game_id)
            if not current_odds:
                return None

            # Get historical odds data
            historical_odds = await self._get_historical_odds(game_id)
            if len(historical_odds) < 10:
                return None

            # Prepare features for prediction
            features = self._prepare_odds_features(historical_odds, current_odds)

            # Make prediction
            model = self.models.get('odds_movement')
            if not model:
                return None

            prediction = model.predict([features])[0]
            confidence = self._calculate_prediction_confidence(features, model)

            # Determine movement direction
            movement_direction = "up" if prediction > current_odds else "down"

            odds_prediction = OddsPrediction(
                game_id=game_id,
                current_odds=current_odds,
                predicted_odds=prediction,
                movement_direction=movement_direction,
                confidence_score=confidence,
                prediction_horizon=prediction_horizon
            )

            # Store prediction
            await self._store_odds_prediction(odds_prediction)

            return odds_prediction

        except Exception as e:
            logger.error(f"Error predicting odds movement: {e}")
            return None

    @time_operation("ml_identify_value_bets")
    async def identify_value_bets(self, games: List[Dict]) -> List[Dict]:
        """Identify value bets from available games."""
        try:
            value_bets = []

            for game in games:
                # Get historical data for similar games
                similar_games = await self._get_similar_games(game)

                if len(similar_games) < 5:
                    continue

                # Calculate expected value
                expected_value = self._calculate_expected_value(game, similar_games)

                # Calculate confidence
                confidence = self._calculate_value_confidence(game, similar_games)

                if expected_value > 0.05 and confidence > self.config['confidence_threshold']:
                    value_bets.append({
                        'game_id': game['id'],
                        'expected_value': expected_value,
                        'confidence': confidence,
                        'recommended_bet': game['home_team'] if expected_value > 0 else game['away_team'],
                        'reasoning': f"Historical data shows {abs(expected_value):.1%} edge"
                    })

            # Sort by expected value
            value_bets.sort(key=lambda x: x['expected_value'], reverse=True)

            return value_bets

        except Exception as e:
            logger.error(f"Error identifying value bets: {e}")
            return []

    @time_operation("ml_analyze_user_behavior")
    async def analyze_user_behavior(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Analyze user behavior patterns for ML insights."""
        try:
            # Get user's betting history
            user_data = await self._get_user_betting_data(user_id, guild_id)

            if not user_data or len(user_data['bets']) < 10:
                return {}

            # Analyze betting patterns
            patterns = {
                'bet_sizing_pattern': self._analyze_bet_sizing(user_data['bets']),
                'timing_pattern': self._analyze_betting_timing(user_data['bets']),
                'sport_preferences': self._analyze_sport_preferences(user_data['bets']),
                'risk_tolerance': self._analyze_risk_tolerance(user_data['bets']),
                'performance_trends': self._analyze_performance_trends(user_data['bets'])
            }

            # Generate insights
            insights = {
                'optimal_bet_size': self._calculate_optimal_bet_size(patterns),
                'best_betting_times': self._identify_best_betting_times(patterns),
                'recommended_sports': self._get_recommended_sports(patterns),
                'risk_adjustment': self._suggest_risk_adjustment(patterns),
                'improvement_areas': self._identify_improvement_areas(patterns)
            }

            return {
                'patterns': patterns,
                'insights': insights,
                'confidence_score': self._calculate_behavior_confidence(user_data['bets'])
            }

        except Exception as e:
            logger.error(f"Error analyzing user behavior: {e}")
            return {}

    @time_operation("ml_train_models")
    async def train_models(self, model_types: Optional[List[str]] = None):
        """Train or retrain ML models."""
        if model_types is None:
            model_types = self.config['model_types']

        try:
            for model_type in model_types:
                logger.info(f"Training {model_type} model...")

                # Get training data
                training_data = await self._get_training_data(model_type)

                if len(training_data) < self.config['min_training_samples']:
                    logger.warning(f"Insufficient training data for {model_type}")
                    continue

                # Train model
                model, scaler = await self._train_model(model_type, training_data)

                if model and scaler:
                    self.models[model_type] = model
                    self.scalers[model_type] = scaler
                    self.model_versions[model_type] = datetime.utcnow().isoformat()

                    # Save models
                    await self._save_models(model_type, model, scaler)

                    logger.info(f"Successfully trained {model_type} model")

        except Exception as e:
            logger.error(f"Error training models: {e}")

    async def _periodic_training(self):
        """Periodic model training task."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config['model_retrain_interval'])
                await self.train_models()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic training: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

    async def _load_models(self):
        """Load pre-trained models from storage."""
        try:
            for model_type in self.config['model_types']:
                model, scaler = await self._load_model(model_type)
                if model and scaler:
                    self.models[model_type] = model
                    self.scalers[model_type] = scaler
                    logger.info(f"Loaded {model_type} model")

        except Exception as e:
            logger.error(f"Error loading models: {e}")

    async def _get_user_betting_data(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Get comprehensive user betting data for ML analysis."""
        try:
            # Get user's bets
            bet_query = """
                SELECT * FROM bets
                WHERE user_id = %s AND guild_id = %s
                ORDER BY created_at DESC
                LIMIT 1000
            """
            bets = await self.db_manager.fetch_all(bet_query, user_id, guild_id)

            # Get user preferences
            pref_query = """
                SELECT * FROM user_settings
                WHERE user_id = %s AND guild_id = %s
            """
            preferences = await self.db_manager.fetch_one(pref_query, user_id, guild_id)

            return {
                'bets': bets,
                'preferences': preferences or {},
                'total_bets': len(bets),
                'total_volume': sum(bet['amount'] for bet in bets) if bets else 0
            }

        except Exception as e:
            logger.error(f"Error getting user betting data: {e}")
            return {}

    async def _get_available_games(self) -> List[Dict]:
        """Get available games for recommendations."""
        try:
            query = """
                SELECT * FROM api_games
                WHERE status = 'upcoming'
                AND start_time > NOW()
                AND start_time < DATE_ADD(NOW(), INTERVAL 7 DAY)
                ORDER BY start_time ASC
            """
            return await self.db_manager.fetch_all(query)

        except Exception as e:
            logger.error(f"Error getting available games: {e}")
            return []

    async def _generate_value_bet_recommendations(self, user_id: int, guild_id: int,
                                                available_games: List[Dict],
                                                user_data: Dict) -> List[BetRecommendation]:
        """Generate value bet recommendations."""
        recommendations = []

        try:
            # Identify value bets
            value_bets = await self.identify_value_bets(available_games)

            for value_bet in value_bets[:3]:  # Top 3 value bets
                recommendation = BetRecommendation(
                    user_id=user_id,
                    guild_id=guild_id,
                    recommendation_type="value_bet",
                    confidence_score=value_bet['confidence'],
                    reasoning=value_bet['reasoning'],
                    expected_value=value_bet['expected_value'],
                    risk_level="medium"
                )
                recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error generating value bet recommendations: {e}")

        return recommendations

    async def _generate_pattern_based_recommendations(self, user_id: int, guild_id: int,
                                                    available_games: List[Dict],
                                                    user_data: Dict) -> List[BetRecommendation]:
        """Generate recommendations based on user patterns."""
        recommendations = []

        try:
            # Analyze user patterns
            patterns = await self.analyze_user_behavior(user_id, guild_id)

            if not patterns:
                return recommendations

            # Find games matching user preferences
            user_sports = patterns.get('patterns', {}).get('sport_preferences', [])

            for game in available_games:
                if game.get('sport') in user_sports:
                    recommendation = BetRecommendation(
                        user_id=user_id,
                        guild_id=guild_id,
                        recommendation_type="pattern_based",
                        confidence_score=0.6,
                        reasoning=f"Matches your preference for {game.get('sport')}",
                        expected_value=0.02,
                        risk_level="low"
                    )
                    recommendations.append(recommendation)
                    break  # Only recommend one pattern-based bet

        except Exception as e:
            logger.error(f"Error generating pattern-based recommendations: {e}")

        return recommendations

    async def _get_training_data(self, model_type: str) -> List[Dict]:
        """Get training data for specific model type."""
        try:
            if model_type == 'bet_outcome':
                return await self._get_bet_outcome_training_data()
            elif model_type == 'odds_movement':
                return await self._get_odds_movement_training_data()
            elif model_type == 'value_bet':
                return await self._get_value_bet_training_data()
            elif model_type == 'user_behavior':
                return await self._get_user_behavior_training_data()
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting training data for {model_type}: {e}")
            return []

    async def _train_model(self, model_type: str, training_data: List[Dict]) -> Tuple[Any, Any]:
        """Train a specific model type."""
        try:
            if not training_data:
                return None, None

            # Prepare features and labels
            X, y = self._prepare_training_data(model_type, training_data)

            if len(X) < 10:
                return None, None

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            if model_type == 'bet_outcome':
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif model_type == 'odds_movement':
                model = RandomForestRegressor(n_estimators=100, random_state=42)
            elif model_type == 'value_bet':
                model = LogisticRegression(random_state=42)
            elif model_type == 'user_behavior':
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                return None, None

            model.fit(X_train_scaled, y_train)

            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            if model_type == 'odds_movement':
                score = model.score(X_test_scaled, y_test)
            else:
                score = accuracy_score(y_test, y_pred)

            logger.info(f"{model_type} model accuracy: {score:.3f}")

            return model, scaler

        except Exception as e:
            logger.error(f"Error training {model_type} model: {e}")
            return None, None

    def _prepare_training_data(self, model_type: str, training_data: List[Dict]) -> Tuple[List, List]:
        """Prepare features and labels for training."""
        X = []
        y = []

        try:
            for data_point in training_data:
                if model_type == 'bet_outcome':
                    features = self._extract_bet_outcome_features(data_point)
                    label = 1 if data_point.get('result') == 'win' else 0
                elif model_type == 'odds_movement':
                    features = self._extract_odds_movement_features(data_point)
                    label = data_point.get('odds_change', 0)
                elif model_type == 'value_bet':
                    features = self._extract_value_bet_features(data_point)
                    label = 1 if data_point.get('is_value_bet') else 0
                elif model_type == 'user_behavior':
                    features = self._extract_user_behavior_features(data_point)
                    label = data_point.get('behavior_category', 'normal')
                else:
                    continue

                if features is not None:
                    X.append(features)
                    y.append(label)

        except Exception as e:
            logger.error(f"Error preparing training data: {e}")

        return X, y

    def _extract_bet_outcome_features(self, bet_data: Dict) -> Optional[List]:
        """Extract features for bet outcome prediction."""
        try:
            features = [
                bet_data.get('amount', 0),
                bet_data.get('odds', 0),
                bet_data.get('sport_rank', 0),
                bet_data.get('user_win_rate', 0.5),
                bet_data.get('team_win_rate', 0.5),
                bet_data.get('home_away_factor', 0),
                bet_data.get('time_of_day', 12),
                bet_data.get('day_of_week', 3)
            ]
            return features
        except Exception:
            return None

    def _extract_odds_movement_features(self, odds_data: Dict) -> Optional[List]:
        """Extract features for odds movement prediction."""
        try:
            features = [
                odds_data.get('current_odds', 0),
                odds_data.get('volume_24h', 0),
                odds_data.get('bet_count_24h', 0),
                odds_data.get('public_percentage', 0.5),
                odds_data.get('line_movement', 0),
                odds_data.get('time_to_game', 24),
                odds_data.get('weather_factor', 0),
                odds_data.get('injury_factor', 0)
            ]
            return features
        except Exception:
            return None

    def _extract_value_bet_features(self, bet_data: Dict) -> Optional[List]:
        """Extract features for value bet identification."""
        try:
            features = [
                bet_data.get('implied_probability', 0.5),
                bet_data.get('model_probability', 0.5),
                bet_data.get('edge', 0),
                bet_data.get('volume', 0),
                bet_data.get('line_movement', 0),
                bet_data.get('sharp_money', 0),
                bet_data.get('public_percentage', 0.5)
            ]
            return features
        except Exception:
            return None

    def _extract_user_behavior_features(self, user_data: Dict) -> Optional[List]:
        """Extract features for user behavior analysis."""
        try:
            features = [
                user_data.get('avg_bet_size', 0),
                user_data.get('bet_frequency', 0),
                user_data.get('win_rate', 0.5),
                user_data.get('favorite_sport_ratio', 0.5),
                user_data.get('time_consistency', 0),
                user_data.get('risk_tolerance', 0.5),
                user_data.get('session_duration', 0)
            ]
            return features
        except Exception:
            return None

    async def _get_bet_outcome_training_data(self) -> List[Dict]:
        """Get training data for bet outcome prediction."""
        try:
            query = """
                SELECT b.*, u.win_rate as user_win_rate, g.home_team_win_rate, g.away_team_win_rate
                FROM bets b
                LEFT JOIN (
                    SELECT user_id, guild_id,
                           SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) / COUNT(*) as win_rate
                    FROM bets
                    GROUP BY user_id, guild_id
                ) u ON b.user_id = u.user_id AND b.guild_id = u.guild_id
                LEFT JOIN api_games g ON b.game_id = g.id
                WHERE b.result IS NOT NULL
                ORDER BY b.created_at DESC
                LIMIT 10000
            """
            return await self.db_manager.fetch_all(query)

        except Exception as e:
            logger.error(f"Error getting bet outcome training data: {e}")
            return []

    async def _get_odds_movement_training_data(self) -> List[Dict]:
        """Get training data for odds movement prediction."""
        # This would implement odds movement data collection
        # For now, return placeholder data
        return []

    async def _get_value_bet_training_data(self) -> List[Dict]:
        """Get training data for value bet identification."""
        # This would implement value bet data collection
        # For now, return placeholder data
        return []

    async def _get_user_behavior_training_data(self) -> List[Dict]:
        """Get training data for user behavior analysis."""
        # This would implement user behavior data collection
        # For now, return placeholder data
        return []

    async def _store_recommendations(self, recommendations: List[BetRecommendation]):
        """Store bet recommendations in database."""
        if not recommendations:
            return

        try:
            query = """
                INSERT INTO ml_predictions (model_type, prediction_data, confidence_score)
                VALUES (%s, %s, %s)
            """

            values = [
                ('bet_recommendation', json.dumps({
                    'user_id': rec.user_id,
                    'guild_id': rec.guild_id,
                    'recommendation_type': rec.recommendation_type,
                    'reasoning': rec.reasoning,
                    'expected_value': rec.expected_value,
                    'risk_level': rec.risk_level
                }), rec.confidence_score)
                for rec in recommendations
            ]

            await self.db_manager.executemany(query, values)
            logger.debug(f"Stored {len(recommendations)} bet recommendations")

        except Exception as e:
            logger.error(f"Error storing recommendations: {e}")

    async def _store_odds_prediction(self, prediction: OddsPrediction):
        """Store odds prediction in database."""
        try:
            query = """
                INSERT INTO ml_predictions (model_type, prediction_data, confidence_score)
                VALUES (%s, %s, %s)
            """

            prediction_data = {
                'game_id': prediction.game_id,
                'current_odds': prediction.current_odds,
                'predicted_odds': prediction.predicted_odds,
                'movement_direction': prediction.movement_direction,
                'prediction_horizon': prediction.prediction_horizon
            }

            await self.db_manager.execute(query, 'odds_movement',
                                        json.dumps(prediction_data),
                                        prediction.confidence_score)

        except Exception as e:
            logger.error(f"Error storing odds prediction: {e}")

    async def _save_models(self, model_type: str, model: Any, scaler: Any):
        """Save trained models to storage."""
        try:
            # Save model
            model_path = f"models/{model_type}_model.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)

            # Save scaler
            scaler_path = f"models/{model_type}_scaler.pkl"
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)

            logger.info(f"Saved {model_type} model and scaler")

        except Exception as e:
            logger.error(f"Error saving {model_type} model: {e}")

    async def _load_model(self, model_type: str) -> Tuple[Any, Any]:
        """Load trained model from storage."""
        try:
            # Load model
            model_path = f"models/{model_type}_model.pkl"
            with open(model_path, 'rb') as f:
                model = pickle.load(f)

            # Load scaler
            scaler_path = f"models/{model_type}_scaler.pkl"
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)

            return model, scaler

        except Exception as e:
            logger.error(f"Error loading {model_type} model: {e}")
            return None, None

    def _calculate_prediction_confidence(self, features: List, model: Any) -> float:
        """Calculate confidence score for a prediction."""
        try:
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba([features])[0]
                return max(proba)
            else:
                return 0.7  # Default confidence for regression models
        except Exception:
            return 0.5

    def _calculate_expected_value(self, game: Dict, similar_games: List[Dict]) -> float:
        """Calculate expected value for a bet."""
        try:
            if not similar_games:
                return 0.0

            # Calculate win probability from similar games
            wins = sum(1 for g in similar_games if g.get('result') == 'win')
            win_prob = wins / len(similar_games)

            # Calculate expected value
            odds = game.get('odds', 2.0)
            expected_value = (win_prob * (odds - 1)) - (1 - win_prob)

            return expected_value

        except Exception:
            return 0.0

    def _calculate_value_confidence(self, game: Dict, similar_games: List[Dict]) -> float:
        """Calculate confidence for value bet identification."""
        try:
            if len(similar_games) < 5:
                return 0.3

            # Higher confidence with more similar games
            confidence = min(len(similar_games) / 20, 1.0)

            # Adjust based on data quality
            quality_score = sum(1 for g in similar_games if g.get('result') is not None) / len(similar_games)

            return confidence * quality_score

        except Exception:
            return 0.5

    def _analyze_bet_sizing(self, bets: List[Dict]) -> Dict[str, Any]:
        """Analyze user's bet sizing patterns."""
        if not bets:
            return {}

        bet_sizes = [bet['amount'] for bet in bets]
        return {
            'avg_size': sum(bet_sizes) / len(bet_sizes),
            'size_consistency': np.std(bet_sizes) / (sum(bet_sizes) / len(bet_sizes)),
            'size_trend': 'increasing' if len(bet_sizes) > 1 and bet_sizes[-1] > bet_sizes[0] else 'stable'
        }

    def _analyze_betting_timing(self, bets: List[Dict]) -> Dict[str, Any]:
        """Analyze user's betting timing patterns."""
        if not bets:
            return {}

        hours = [bet['created_at'].hour for bet in bets]
        return {
            'peak_hours': [h for h, count in pd.Series(hours).value_counts().head(3).items()],
            'time_consistency': 1 - (np.std(hours) / 24),
            'preferred_days': [bet['created_at'].weekday() for bet in bets[:10]]
        }

    def _analyze_sport_preferences(self, bets: List[Dict]) -> List[str]:
        """Analyze user's sport preferences."""
        if not bets:
            return []

        sport_counts = defaultdict(int)
        for bet in bets:
            sport = bet.get('sport', 'unknown')
            sport_counts[sport] += 1

        return [sport for sport, count in sorted(sport_counts.items(), key=lambda x: x[1], reverse=True)[:3]]

    def _analyze_risk_tolerance(self, bets: List[Dict]) -> str:
        """Analyze user's risk tolerance."""
        if not bets:
            return "unknown"

        avg_bet_size = sum(bet['amount'] for bet in bets) / len(bets)
        win_rate = sum(1 for bet in bets if bet.get('result') == 'win') / len(bets)

        if avg_bet_size > 100 and win_rate < 0.4:
            return "high"
        elif avg_bet_size > 50 or win_rate < 0.5:
            return "medium"
        else:
            return "low"

    def _analyze_performance_trends(self, bets: List[Dict]) -> Dict[str, Any]:
        """Analyze user's performance trends."""
        if len(bets) < 10:
            return {}

        recent_bets = bets[:10]
        older_bets = bets[10:20] if len(bets) >= 20 else []

        recent_win_rate = sum(1 for bet in recent_bets if bet.get('result') == 'win') / len(recent_bets)
        older_win_rate = sum(1 for bet in older_bets if bet.get('result') == 'win') / len(older_bets) if older_bets else recent_win_rate

        return {
            'trend': 'improving' if recent_win_rate > older_win_rate else 'declining',
            'recent_win_rate': recent_win_rate,
            'overall_win_rate': sum(1 for bet in bets if bet.get('result') == 'win') / len(bets)
        }

    def _calculate_optimal_bet_size(self, patterns: Dict) -> float:
        """Calculate optimal bet size based on patterns."""
        sizing = patterns.get('bet_sizing_pattern', {})
        avg_size = sizing.get('avg_size', 50)
        consistency = sizing.get('size_consistency', 0.5)

        # Adjust based on consistency
        if consistency < 0.3:
            return avg_size * 0.8  # More conservative
        else:
            return avg_size

    def _identify_best_betting_times(self, patterns: Dict) -> List[int]:
        """Identify best betting times based on patterns."""
        timing = patterns.get('timing_pattern', {})
        return timing.get('peak_hours', [12, 18, 20])

    def _get_recommended_sports(self, patterns: Dict) -> List[str]:
        """Get recommended sports based on patterns."""
        return patterns.get('sport_preferences', [])

    def _suggest_risk_adjustment(self, patterns: Dict) -> str:
        """Suggest risk adjustment based on patterns."""
        risk_tolerance = patterns.get('risk_tolerance', 'medium')
        performance = patterns.get('performance_trends', {})

        if performance.get('trend') == 'declining' and risk_tolerance == 'high':
            return "Consider reducing bet sizes"
        elif performance.get('trend') == 'improving' and risk_tolerance == 'low':
            return "Consider increasing bet sizes"
        else:
            return "Maintain current risk level"

    def _identify_improvement_areas(self, patterns: Dict) -> List[str]:
        """Identify areas for improvement."""
        areas = []

        performance = patterns.get('performance_trends', {})
        if performance.get('trend') == 'declining':
            areas.append("Focus on bet selection and analysis")

        timing = patterns.get('timing_pattern', {})
        if timing.get('time_consistency', 0) < 0.5:
            areas.append("Develop more consistent betting schedule")

        return areas

    def _calculate_behavior_confidence(self, bets: List[Dict]) -> float:
        """Calculate confidence in behavior analysis."""
        if len(bets) < 20:
            return 0.3
        elif len(bets) < 50:
            return 0.6
        else:
            return 0.9

    async def _get_current_odds(self, game_id: str) -> Optional[float]:
        """Get current odds for a game."""
        try:
            query = "SELECT odds FROM api_games WHERE id = %s"
            result = await self.db_manager.fetch_one(query, game_id)
            return result['odds'] if result else None
        except Exception:
            return None

    async def _get_historical_odds(self, game_id: str) -> List[Dict]:
        """Get historical odds data for a game."""
        # This would implement historical odds retrieval
        # For now, return placeholder data
        return []

    def _prepare_odds_features(self, historical_odds: List[Dict], current_odds: float) -> List:
        """Prepare features for odds movement prediction."""
        # This would implement feature preparation for odds prediction
        # For now, return placeholder features
        return [current_odds, 0, 0, 0.5, 0, 24, 0, 0]

    async def _get_similar_games(self, game: Dict) -> List[Dict]:
        """Get similar games for analysis."""
        try:
            query = """
                SELECT * FROM api_games
                WHERE sport = %s AND status = 'finished'
                ORDER BY start_time DESC
                LIMIT 20
            """
            return await self.db_manager.fetch_all(query, game.get('sport', 'unknown'))
        except Exception:
            return []

# Global ML service instance
ml_service = None

async def initialize_ml_service(db_manager: DatabaseManager):
    """Initialize the global ML service."""
    global ml_service
    ml_service = MLService(db_manager)
    await ml_service.start()
    logger.info("ML service initialized")

async def get_ml_service() -> MLService:
    """Get the global ML service instance."""
    return ml_service
