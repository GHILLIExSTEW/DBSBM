"""
AI Service for DBSBM System.
Provides artificial intelligence and machine learning capabilities.
"""

import asyncio
import json
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from data.db_manager import DatabaseManager
from utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

# AI-specific cache TTLs
AI_CACHE_TTLS = {
    "ai_models": 3600,  # 1 hour
    "ai_predictions": 1800,  # 30 minutes
    "ai_insights": 7200,  # 2 hours
    "ai_recommendations": 900,  # 15 minutes
    "ai_analytics": 3600,  # 1 hour
    "ai_training": 1800,  # 30 minutes
    "ai_evaluation": 3600,  # 1 hour
    "ai_deployment": 7200,  # 2 hours
    "ai_monitoring": 300,  # 5 minutes
    "ai_performance": 1800,  # 30 minutes
}


class ModelType(Enum):
    """AI model types."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    RECOMMENDATION = "recommendation"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"


class ModelStatus(Enum):
    """AI model status."""

    TRAINING = "training"
    READY = "ready"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ARCHIVED = "archived"


class PredictionType(Enum):
    """AI prediction types."""

    BET_OUTCOME = "bet_outcome"
    USER_BEHAVIOR = "user_behavior"
    MARKET_TRENDS = "market_trends"
    RISK_ASSESSMENT = "risk_assessment"
    FRAUD_DETECTION = "fraud_detection"


@dataclass
class AIModel:
    """AI model configuration."""

    id: int
    tenant_id: int
    name: str
    model_type: ModelType
    version: str
    status: ModelStatus
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    created_at: datetime
    updated_at: datetime


@dataclass
class AIPrediction:
    """AI prediction result."""

    id: int
    tenant_id: int
    model_id: int
    prediction_type: PredictionType
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    confidence: float
    created_at: datetime


@dataclass
class AIInsight:
    """AI insight result."""

    id: int
    tenant_id: int
    insight_type: str
    title: str
    description: str
    data: Dict[str, Any]
    confidence: float
    created_at: datetime


@dataclass
class AIRecommendation:
    """AI recommendation result."""

    id: int
    tenant_id: int
    user_id: int
    recommendation_type: str
    title: str
    description: str
    data: Dict[str, Any]
    priority: float
    created_at: datetime


class AIService:
    """AI service for artificial intelligence and machine learning capabilities."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = AI_CACHE_TTLS

        # Background tasks
        self.model_training_task = None
        self.monitoring_task = None
        self.is_running = False

    async def start(self):
        """Start the AI service."""
        try:
            self.is_running = True
            self.model_training_task = asyncio.create_task(self._train_models())
            self.monitoring_task = asyncio.create_task(self._monitor_models())
            logger.info("AI service started successfully")
        except Exception as e:
            logger.error(f"Failed to start AI service: {e}")
            raise

    async def stop(self):
        """Stop the AI service."""
        self.is_running = False
        if self.model_training_task:
            self.model_training_task.cancel()
        if self.monitoring_task:
            self.monitoring_task.cancel()
        logger.info("AI service stopped")

    @time_operation("ai_create_model")
    async def create_model(
        self,
        tenant_id: int,
        name: str,
        model_type: ModelType,
        parameters: Dict[str, Any],
    ) -> Optional[AIModel]:
        """Create a new AI model."""
        try:
            query = """
            INSERT INTO ai_models (tenant_id, name, model_type, version, status,
                                  parameters, metrics, created_at, updated_at)
            VALUES (:tenant_id, :name, :model_type, :version, :status,
                    :parameters, :metrics, NOW(), NOW())
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": tenant_id,
                    "name": name,
                    "model_type": model_type.value,
                    "version": "1.0.0",
                    "status": ModelStatus.TRAINING.value,
                    "parameters": json.dumps(parameters),
                    "metrics": json.dumps({}),
                },
            )

            model_id = result.lastrowid

            # Get created model
            model = await self.get_model_by_id(model_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"ai_models:{tenant_id}:*")

            record_metric("ai_models_created", 1)
            return model

        except Exception as e:
            logger.error(f"Failed to create AI model: {e}")
            return None

    @time_operation("ai_get_model")
    async def get_model_by_id(self, model_id: int) -> Optional[AIModel]:
        """Get AI model by ID."""
        try:
            # Try to get from cache first
            cache_key = f"ai_model:{model_id}"
            cached_model = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_model:
                return AIModel(**cached_model)

            # Get from database
            query = """
            SELECT * FROM ai_models WHERE id = :model_id
            """

            result = await self.db_manager.fetch_one(query, {"model_id": model_id})

            if not result:
                return None

            model = AIModel(
                id=result["id"],
                tenant_id=result["tenant_id"],
                name=result["name"],
                model_type=ModelType(result["model_type"]),
                version=result["version"],
                status=ModelStatus(result["status"]),
                parameters=(
                    json.loads(result["parameters"]) if result["parameters"] else {}
                ),
                metrics=json.loads(result["metrics"]) if result["metrics"] else {},
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )

            # Cache model
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": model.id,
                    "tenant_id": model.tenant_id,
                    "name": model.name,
                    "model_type": model.model_type.value,
                    "version": model.version,
                    "status": model.status.value,
                    "parameters": model.parameters,
                    "metrics": model.metrics,
                    "created_at": model.created_at.isoformat(),
                    "updated_at": model.updated_at.isoformat(),
                },
                ttl=self.cache_ttls["ai_models"],
            )

            return model

        except Exception as e:
            logger.error(f"Failed to get AI model: {e}")
            return None

    @time_operation("ai_get_models")
    async def get_models_by_tenant(
        self, tenant_id: int, model_type: Optional[ModelType] = None
    ) -> List[AIModel]:
        """Get AI models for a tenant."""
        try:
            # Try to get from cache first
            cache_key = (
                f"ai_models:{tenant_id}:{model_type.value if model_type else 'all'}"
            )
            cached_models = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_models:
                return [AIModel(**model) for model in cached_models]

            # Build query
            query = "SELECT * FROM ai_models WHERE tenant_id = :tenant_id"
            params = {"tenant_id": tenant_id}

            if model_type:
                query += " AND model_type = :model_type"
                params["model_type"] = model_type.value

            results = await self.db_manager.fetch_all(query, params)

            models = []
            for row in results:
                model = AIModel(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    name=row["name"],
                    model_type=ModelType(row["model_type"]),
                    version=row["version"],
                    status=ModelStatus(row["status"]),
                    parameters=(
                        json.loads(row["parameters"]) if row["parameters"] else {}
                    ),
                    metrics=json.loads(row["metrics"]) if row["metrics"] else {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                models.append(model)

            # Cache models
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [
                    {
                        "id": m.id,
                        "tenant_id": m.tenant_id,
                        "name": m.name,
                        "model_type": m.model_type.value,
                        "version": m.version,
                        "status": m.status.value,
                        "parameters": m.parameters,
                        "metrics": m.metrics,
                        "created_at": m.created_at.isoformat(),
                        "updated_at": m.updated_at.isoformat(),
                    }
                    for m in models
                ],
                ttl=self.cache_ttls["ai_models"],
            )

            return models

        except Exception as e:
            logger.error(f"Failed to get AI models: {e}")
            return []

    @time_operation("ai_make_prediction")
    async def make_prediction(
        self, model_id: int, prediction_type: PredictionType, input_data: Dict[str, Any]
    ) -> Optional[AIPrediction]:
        """Make a prediction using an AI model."""
        try:
            # Get model
            model = await self.get_model_by_id(model_id)
            if not model or model.status != ModelStatus.DEPLOYED:
                return None

            # Try to get from cache first
            cache_key = f"ai_prediction:{model_id}:{prediction_type.value}:{hashlib.md5(str(input_data).encode()).hexdigest()}"
            cached_prediction = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_prediction:
                return AIPrediction(**cached_prediction)

            # Make prediction
            output_data, confidence = await self._make_model_prediction(
                model, input_data
            )

            # Create prediction record
            query = """
            INSERT INTO ai_predictions (tenant_id, model_id, prediction_type, input_data,
                                       output_data, confidence, created_at)
            VALUES (:tenant_id, :model_id, :prediction_type, :input_data,
                    :output_data, :confidence, NOW())
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": model.tenant_id,
                    "model_id": model_id,
                    "prediction_type": prediction_type.value,
                    "input_data": json.dumps(input_data),
                    "output_data": json.dumps(output_data),
                    "confidence": confidence,
                },
            )

            prediction_id = result.lastrowid

            prediction = AIPrediction(
                id=prediction_id,
                tenant_id=model.tenant_id,
                model_id=model_id,
                prediction_type=prediction_type,
                input_data=input_data,
                output_data=output_data,
                confidence=confidence,
                created_at=datetime.utcnow(),
            )

            # Cache prediction
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": prediction.id,
                    "tenant_id": prediction.tenant_id,
                    "model_id": prediction.model_id,
                    "prediction_type": prediction.prediction_type.value,
                    "input_data": prediction.input_data,
                    "output_data": prediction.output_data,
                    "confidence": prediction.confidence,
                    "created_at": prediction.created_at.isoformat(),
                },
                ttl=self.cache_ttls["ai_predictions"],
            )

            record_metric("ai_predictions_made", 1)
            return prediction

        except Exception as e:
            logger.error(f"Failed to make AI prediction: {e}")
            return None

    @time_operation("ai_generate_insight")
    async def generate_insight(
        self, tenant_id: int, insight_type: str, data: Dict[str, Any]
    ) -> Optional[AIInsight]:
        """Generate an AI insight."""
        try:
            # Try to get from cache first
            cache_key = f"ai_insight:{tenant_id}:{insight_type}:{hashlib.md5(str(data).encode()).hexdigest()}"
            cached_insight = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_insight:
                return AIInsight(**cached_insight)

            # Generate insight
            insight_data = await self._generate_insight_data(insight_type, data)

            # Create insight record
            query = """
            INSERT INTO ai_insights (tenant_id, insight_type, title, description,
                                    data, confidence, created_at)
            VALUES (:tenant_id, :insight_type, :title, :description,
                    :data, :confidence, NOW())
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": tenant_id,
                    "insight_type": insight_type,
                    "title": insight_data["title"],
                    "description": insight_data["description"],
                    "data": json.dumps(insight_data["data"]),
                    "confidence": insight_data["confidence"],
                },
            )

            insight_id = result.lastrowid

            insight = AIInsight(
                id=insight_id,
                tenant_id=tenant_id,
                insight_type=insight_type,
                title=insight_data["title"],
                description=insight_data["description"],
                data=insight_data["data"],
                confidence=insight_data["confidence"],
                created_at=datetime.utcnow(),
            )

            # Cache insight
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": insight.id,
                    "tenant_id": insight.tenant_id,
                    "insight_type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "data": insight.data,
                    "confidence": insight.confidence,
                    "created_at": insight.created_at.isoformat(),
                },
                ttl=self.cache_ttls["ai_insights"],
            )

            return insight

        except Exception as e:
            logger.error(f"Failed to generate AI insight: {e}")
            return None

    @time_operation("ai_generate_recommendation")
    async def generate_recommendation(
        self,
        tenant_id: int,
        user_id: int,
        recommendation_type: str,
        data: Dict[str, Any],
    ) -> Optional[AIRecommendation]:
        """Generate an AI recommendation."""
        try:
            # Try to get from cache first
            cache_key = f"ai_recommendation:{tenant_id}:{user_id}:{recommendation_type}:{hashlib.md5(str(data).encode()).hexdigest()}"
            cached_recommendation = await self.cache_manager.enhanced_cache_get(
                cache_key
            )

            if cached_recommendation:
                return AIRecommendation(**cached_recommendation)

            # Generate recommendation
            recommendation_data = await self._generate_recommendation_data(
                recommendation_type, data
            )

            # Create recommendation record
            query = """
            INSERT INTO ai_recommendations (tenant_id, user_id, recommendation_type, title,
                                           description, data, priority, created_at)
            VALUES (:tenant_id, :user_id, :recommendation_type, :title,
                    :description, :data, :priority, NOW())
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "recommendation_type": recommendation_type,
                    "title": recommendation_data["title"],
                    "description": recommendation_data["description"],
                    "data": json.dumps(recommendation_data["data"]),
                    "priority": recommendation_data["priority"],
                },
            )

            recommendation_id = result.lastrowid

            recommendation = AIRecommendation(
                id=recommendation_id,
                tenant_id=tenant_id,
                user_id=user_id,
                recommendation_type=recommendation_type,
                title=recommendation_data["title"],
                description=recommendation_data["description"],
                data=recommendation_data["data"],
                priority=recommendation_data["priority"],
                created_at=datetime.utcnow(),
            )

            # Cache recommendation
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": recommendation.id,
                    "tenant_id": recommendation.tenant_id,
                    "user_id": recommendation.user_id,
                    "recommendation_type": recommendation.recommendation_type,
                    "title": recommendation.title,
                    "description": recommendation.description,
                    "data": recommendation.data,
                    "priority": recommendation.priority,
                    "created_at": recommendation.created_at.isoformat(),
                },
                ttl=self.cache_ttls["ai_recommendations"],
            )

            return recommendation

        except Exception as e:
            logger.error(f"Failed to generate AI recommendation: {e}")
            return None

    @time_operation("ai_get_analytics")
    async def get_ai_analytics(self, tenant_id: int, days: int = 30) -> Dict[str, Any]:
        """Get AI analytics for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"ai_analytics:{tenant_id}:{days}"
            cached_analytics = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_analytics:
                return cached_analytics

            # Get model statistics
            model_query = """
            SELECT
                model_type,
                status,
                COUNT(*) as count
            FROM ai_models
            WHERE tenant_id = :tenant_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY model_type, status
            """

            model_results = await self.db_manager.fetch_all(
                model_query, {"tenant_id": tenant_id, "days": days}
            )

            # Get prediction statistics
            prediction_query = """
            SELECT
                prediction_type,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence
            FROM ai_predictions
            WHERE tenant_id = :tenant_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY prediction_type
            """

            prediction_results = await self.db_manager.fetch_all(
                prediction_query, {"tenant_id": tenant_id, "days": days}
            )

            analytics = {
                "model_statistics": {
                    "by_type": {
                        row["model_type"]: row["count"] for row in model_results
                    },
                    "by_status": {row["status"]: row["count"] for row in model_results},
                    "total_models": sum(row["count"] for row in model_results),
                },
                "prediction_statistics": {
                    "by_type": {
                        row["prediction_type"]: {
                            "count": row["count"],
                            "avg_confidence": row["avg_confidence"],
                        }
                        for row in prediction_results
                    },
                    "total_predictions": sum(
                        row["count"] for row in prediction_results
                    ),
                },
                "period": {
                    "days": days,
                    "start_date": (
                        datetime.utcnow() - timedelta(days=days)
                    ).isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                },
            }

            # Cache analytics
            await self.cache_manager.enhanced_cache_set(
                cache_key, analytics, ttl=self.cache_ttls["ai_analytics"]
            )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get AI analytics: {e}")
            return {}

    async def clear_ai_cache(self):
        """Clear all AI-related cache entries."""
        try:
            await self.cache_manager.clear_cache_by_pattern("ai_models:*")
            await self.cache_manager.clear_cache_by_pattern("ai_predictions:*")
            await self.cache_manager.clear_cache_by_pattern("ai_insights:*")
            await self.cache_manager.clear_cache_by_pattern("ai_recommendations:*")
            await self.cache_manager.clear_cache_by_pattern("ai_analytics:*")
            await self.cache_manager.clear_cache_by_pattern("ai_training:*")
            await self.cache_manager.clear_cache_by_pattern("ai_evaluation:*")
            await self.cache_manager.clear_cache_by_pattern("ai_deployment:*")
            await self.cache_manager.clear_cache_by_pattern("ai_monitoring:*")
            await self.cache_manager.clear_cache_by_pattern("ai_performance:*")
            logger.info("AI cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear AI cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get AI service cache statistics."""
        try:
            return await self.cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
