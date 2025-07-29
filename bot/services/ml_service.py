"""Machine learning service for betting insights and predictions."""

import asyncio
import logging
import pickle
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import enhanced_cache_get, enhanced_cache_set, enhanced_cache_delete, get_enhanced_cache_manager
from bot.utils.performance_monitor import time_operation

logger = logging.getLogger(__name__)

# Cache TTLs for ML data
ML_CACHE_TTLS = {
    "model_cache": 86400,  # 24 hours
    "prediction_cache": 3600,  # 1 hour
    "feature_cache": 7200,  # 2 hours
    "training_data": 3600,  # 1 hour
    "model_metadata": 86400,  # 24 hours
}


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

    async def _periodic_training(self):
        """Periodic model training task."""
        while self._is_running:
            try:
                await self._retrain_models()
                await asyncio.sleep(self.config['model_retrain_interval'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic training: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

    async def _load_models(self):
        """Load cached models from storage."""
        try:
            for model_type in self.config['model_types']:
                # Try to load from cache first
                cached_model = await enhanced_cache_get("ml_data", f"model:{model_type}")
                cached_scaler = await enhanced_cache_get("ml_data", f"scaler:{model_type}")

                if cached_model and cached_scaler:
                    try:
                        self.models[model_type] = pickle.loads(cached_model)
                        self.scalers[model_type] = pickle.loads(cached_scaler)
                        logger.info(f"Loaded cached model: {model_type}")
                    except Exception as e:
                        logger.error(
                            f"Error loading cached model {model_type}: {e}")
                        # Fall back to training new model
                        await self._train_model(model_type)
                else:
                    # No cached model, train new one
                    await self._train_model(model_type)

        except Exception as e:
            logger.error(f"Error loading models: {e}")

    async def _retrain_models(self):
        """Retrain all models with fresh data."""
        try:
            logger.info("Starting model retraining...")

            for model_type in self.config['model_types']:
                try:
                    await self._train_model(model_type)
                    logger.info(f"Retrained model: {model_type}")
                except Exception as e:
                    logger.error(f"Error retraining model {model_type}: {e}")

        except Exception as e:
            logger.error(f"Error in model retraining: {e}")

    async def _train_model(self, model_type: str):
        """Train a specific model type."""
        try:
            # Get training data
            training_data = await self._get_training_data(model_type)

            if len(training_data) < self.config['min_training_samples']:
                logger.warning(
                    f"Insufficient training data for {model_type}: {len(training_data)} samples")
                return

            # Prepare features and labels
            X, y = self._prepare_features(model_type, training_data)

            if len(X) == 0:
                logger.warning(f"No valid features for {model_type}")
                return

            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X, y)

            # Train scaler
            scaler = StandardScaler()
            scaler.fit(X)

            # Cache the trained model and scaler
            model_bytes = pickle.dumps(model)
            scaler_bytes = pickle.dumps(scaler)

            await enhanced_cache_set("ml_data", f"model:{model_type}", model_bytes, ttl=ML_CACHE_TTLS["model_cache"])
            await enhanced_cache_set("ml_data", f"scaler:{model_type}", scaler_bytes, ttl=ML_CACHE_TTLS["model_cache"])

            # Store in memory
            self.models[model_type] = model
            self.scalers[model_type] = scaler

            # Update model version
            self.model_versions[model_type] = datetime.now(
                timezone.utc).isoformat()

            logger.info(f"Trained and cached model: {model_type}")

        except Exception as e:
            logger.error(f"Error training model {model_type}: {e}")

    async def _get_training_data(self, model_type: str) -> List[Dict]:
        """Get training data for a specific model type."""
        try:
            # Check cache first
            cache_key = f"training_data:{model_type}"
            cached_data = await enhanced_cache_get("ml_data", cache_key)

            if cached_data:
                return cached_data

            # Get data from database based on model type
            if model_type == 'bet_outcome':
                query = """
                    SELECT bet_id, amount, odds, sport, league, created_at, status
                    FROM bets
                    WHERE status IN ('won', 'lost')
                    AND created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
                    ORDER BY created_at DESC
                    LIMIT 1000
                """
            elif model_type == 'odds_movement':
                query = """
                    SELECT game_id, initial_odds, final_odds, sport, league, created_at
                    FROM odds_history
                    WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
                    ORDER BY created_at DESC
                    LIMIT 1000
                """
            elif model_type == 'value_bet':
                query = """
                    SELECT bet_id, amount, odds, expected_value, actual_result, sport, league
                    FROM bets
                    WHERE status IN ('won', 'lost')
                    AND created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
                    ORDER BY created_at DESC
                    LIMIT 1000
                """
            elif model_type == 'user_behavior':
                query = """
                    SELECT user_id, bet_count, avg_bet_size, win_rate, favorite_sport, created_at
                    FROM user_analytics
                    WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
                    ORDER BY created_at DESC
                    LIMIT 1000
                """
            else:
                return []

            data = await self.db_manager.fetch_all(query)

            # Cache the training data
            await enhanced_cache_set("ml_data", cache_key, data, ttl=ML_CACHE_TTLS["training_data"])

            return data

        except Exception as e:
            logger.error(f"Error getting training data for {model_type}: {e}")
            return []

    def _prepare_features(self, model_type: str, data: List[Dict]) -> tuple:
        """Prepare features and labels for model training."""
        try:
            if not data:
                return [], []

            if model_type == 'bet_outcome':
                return self._prepare_bet_outcome_features(data)
            elif model_type == 'odds_movement':
                return self._prepare_odds_movement_features(data)
            elif model_type == 'value_bet':
                return self._prepare_value_bet_features(data)
            elif model_type == 'user_behavior':
                return self._prepare_user_behavior_features(data)
            else:
                return [], []

        except Exception as e:
            logger.error(f"Error preparing features for {model_type}: {e}")
            return [], []

    def _prepare_bet_outcome_features(self, data: List[Dict]) -> tuple:
        """Prepare features for bet outcome prediction."""
        try:
            features = []
            labels = []

            for row in data:
                # Extract features
                amount = float(row.get('amount', 0))
                odds = float(row.get('odds', 1.0))
                sport_encoded = hash(row.get('sport', '')
                                     ) % 100  # Simple encoding
                league_encoded = hash(row.get('league', '')) % 100

                # Create feature vector
                feature_vector = [amount, odds, sport_encoded, league_encoded]
                features.append(feature_vector)

                # Create label (1 for win, 0 for loss)
                label = 1 if row.get('status') == 'won' else 0
                labels.append(label)

            return np.array(features), np.array(labels)

        except Exception as e:
            logger.error(f"Error preparing bet outcome features: {e}")
            return [], []

    def _prepare_odds_movement_features(self, data: List[Dict]) -> tuple:
        """Prepare features for odds movement prediction."""
        try:
            features = []
            labels = []

            for row in data:
                initial_odds = float(row.get('initial_odds', 1.0))
                final_odds = float(row.get('final_odds', 1.0))
                sport_encoded = hash(row.get('sport', '')) % 100
                league_encoded = hash(row.get('league', '')) % 100

                # Calculate odds movement
                odds_change = final_odds - initial_odds
                odds_change_percent = (odds_change / initial_odds) * 100

                feature_vector = [initial_odds, final_odds, odds_change,
                                  odds_change_percent, sport_encoded, league_encoded]
                features.append(feature_vector)

                # Label: 1 if odds increased, 0 if decreased
                label = 1 if odds_change > 0 else 0
                labels.append(label)

            return np.array(features), np.array(labels)

        except Exception as e:
            logger.error(f"Error preparing odds movement features: {e}")
            return [], []

    def _prepare_value_bet_features(self, data: List[Dict]) -> tuple:
        """Prepare features for value bet prediction."""
        try:
            features = []
            labels = []

            for row in data:
                amount = float(row.get('amount', 0))
                odds = float(row.get('odds', 1.0))
                expected_value = float(row.get('expected_value', 0))
                sport_encoded = hash(row.get('sport', '')) % 100
                league_encoded = hash(row.get('league', '')) % 100

                # Calculate value metrics
                value_ratio = expected_value / amount if amount > 0 else 0

                feature_vector = [amount, odds, expected_value,
                                  value_ratio, sport_encoded, league_encoded]
                features.append(feature_vector)

                # Label: 1 if actual result was positive, 0 otherwise
                label = 1 if row.get('actual_result') == 'positive' else 0
                labels.append(label)

            return np.array(features), np.array(labels)

        except Exception as e:
            logger.error(f"Error preparing value bet features: {e}")
            return [], []

    def _prepare_user_behavior_features(self, data: List[Dict]) -> tuple:
        """Prepare features for user behavior prediction."""
        try:
            features = []
            labels = []

            for row in data:
                bet_count = int(row.get('bet_count', 0))
                avg_bet_size = float(row.get('avg_bet_size', 0))
                win_rate = float(row.get('win_rate', 0))
                sport_encoded = hash(row.get('favorite_sport', '')) % 100

                feature_vector = [bet_count,
                                  avg_bet_size, win_rate, sport_encoded]
                features.append(feature_vector)

                # Label: 1 if user is active (bet_count > 5), 0 otherwise
                label = 1 if bet_count > 5 else 0
                labels.append(label)

            return np.array(features), np.array(labels)

        except Exception as e:
            logger.error(f"Error preparing user behavior features: {e}")
            return [], []

    @time_operation("ml_predict_bet_outcome")
    async def predict_bet_outcome(self, bet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict the outcome of a bet."""
        try:
            # Check cache first
            cache_key = f"prediction:bet_outcome:{hash(str(bet_data))}"
            cached_prediction = await enhanced_cache_get("ml_data", cache_key)

            if cached_prediction:
                logger.debug("Cache hit for bet outcome prediction")
                return cached_prediction

            if 'bet_outcome' not in self.models:
                return {'prediction': 'unknown', 'confidence': 0.0, 'error': 'Model not available'}

            # Prepare features
            features = self._prepare_bet_prediction_features(bet_data)
            if len(features) == 0:
                return {'prediction': 'unknown', 'confidence': 0.0, 'error': 'Invalid features'}

            # Scale features
            scaler = self.scalers.get('bet_outcome')
            if scaler:
                features_scaled = scaler.transform([features])
            else:
                features_scaled = [features]

            # Make prediction
            model = self.models['bet_outcome']
            prediction_proba = model.predict_proba(features_scaled)[0]
            prediction = model.predict(features_scaled)[0]

            confidence = max(prediction_proba)
            predicted_outcome = 'win' if prediction == 1 else 'loss'

            result = {
                'prediction': predicted_outcome,
                'confidence': float(confidence),
                'model_version': self.model_versions.get('bet_outcome', 'unknown'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Cache the prediction
            await enhanced_cache_set("ml_data", cache_key, result, ttl=ML_CACHE_TTLS["prediction_cache"])

            return result

        except Exception as e:
            logger.error(f"Error predicting bet outcome: {e}")
            return {'prediction': 'unknown', 'confidence': 0.0, 'error': str(e)}

    def _prepare_bet_prediction_features(self, bet_data: Dict[str, Any]) -> List[float]:
        """Prepare features for bet outcome prediction."""
        try:
            amount = float(bet_data.get('amount', 0))
            odds = float(bet_data.get('odds', 1.0))
            sport = bet_data.get('sport', '')
            league = bet_data.get('league', '')

            sport_encoded = hash(sport) % 100
            league_encoded = hash(league) % 100

            return [amount, odds, sport_encoded, league_encoded]

        except Exception as e:
            logger.error(f"Error preparing bet prediction features: {e}")
            return []

    @time_operation("ml_predict_odds_movement")
    async def predict_odds_movement(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict odds movement for a game."""
        try:
            # Check cache first
            cache_key = f"prediction:odds_movement:{hash(str(game_data))}"
            cached_prediction = await enhanced_cache_get("ml_data", cache_key)

            if cached_prediction:
                logger.debug("Cache hit for odds movement prediction")
                return cached_prediction

            if 'odds_movement' not in self.models:
                return {'prediction': 'unknown', 'confidence': 0.0, 'error': 'Model not available'}

            # Prepare features
            features = self._prepare_odds_prediction_features(game_data)
            if len(features) == 0:
                return {'prediction': 'unknown', 'confidence': 0.0, 'error': 'Invalid features'}

            # Scale features
            scaler = self.scalers.get('odds_movement')
            if scaler:
                features_scaled = scaler.transform([features])
            else:
                features_scaled = [features]

            # Make prediction
            model = self.models['odds_movement']
            prediction_proba = model.predict_proba(features_scaled)[0]
            prediction = model.predict(features_scaled)[0]

            confidence = max(prediction_proba)
            predicted_movement = 'increase' if prediction == 1 else 'decrease'

            result = {
                'prediction': predicted_movement,
                'confidence': float(confidence),
                'model_version': self.model_versions.get('odds_movement', 'unknown'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Cache the prediction
            await enhanced_cache_set("ml_data", cache_key, result, ttl=ML_CACHE_TTLS["prediction_cache"])

            return result

        except Exception as e:
            logger.error(f"Error predicting odds movement: {e}")
            return {'prediction': 'unknown', 'confidence': 0.0, 'error': str(e)}

    def _prepare_odds_prediction_features(self, game_data: Dict[str, Any]) -> List[float]:
        """Prepare features for odds movement prediction."""
        try:
            initial_odds = float(game_data.get('initial_odds', 1.0))
            sport = game_data.get('sport', '')
            league = game_data.get('league', '')

            sport_encoded = hash(sport) % 100
            league_encoded = hash(league) % 100

            return [initial_odds, sport_encoded, league_encoded]

        except Exception as e:
            logger.error(f"Error preparing odds prediction features: {e}")
            return []

    async def get_model_status(self) -> Dict[str, Any]:
        """Get status of all ML models."""
        try:
            status = {}
            for model_type in self.config['model_types']:
                model_available = model_type in self.models
                scaler_available = model_type in self.scalers
                version = self.model_versions.get(model_type, 'unknown')

                status[model_type] = {
                    'available': model_available and scaler_available,
                    'version': version,
                    'last_trained': version if version != 'unknown' else None
                }

            return status

        except Exception as e:
            logger.error(f"Error getting model status: {e}")
            return {}

    async def clear_ml_cache(self, model_type: Optional[str] = None):
        """Clear ML cache for specific model or all models."""
        try:
            if model_type:
                # Clear specific model cache
                await enhanced_cache_delete("ml_data", f"model:{model_type}")
                await enhanced_cache_delete("ml_data", f"scaler:{model_type}")
                await enhanced_cache_delete("ml_data", f"training_data:{model_type}")
                logger.info(f"Cleared ML cache for model: {model_type}")
            else:
                # Clear all ML cache
                for mt in self.config['model_types']:
                    await enhanced_cache_delete("ml_data", f"model:{mt}")
                    await enhanced_cache_delete("ml_data", f"scaler:{mt}")
                    await enhanced_cache_delete("ml_data", f"training_data:{mt}")
                logger.info("Cleared all ML cache")

        except Exception as e:
            logger.error(f"Error clearing ML cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get ML cache statistics."""
        try:
            return await get_enhanced_cache_manager().get_stats()
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
