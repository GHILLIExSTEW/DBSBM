"""
Test cases for Advanced AI Service
Tests the advanced AI and machine learning capabilities.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.data.db_manager import DatabaseManager
from bot.services.advanced_ai_service import (
    AdvancedAIService,
    AIModel,
    ComputerVisionResult,
    ModelPerformance,
    ModelStatus,
    ModelTrainingJob,
    ModelType,
    NLPResult,
    Prediction,
    ReinforcementLearningState,
)
from bot.utils.enhanced_cache_manager import EnhancedCacheManager


class TestAdvancedAIService:
    """Test cases for Advanced AI Service."""

    @pytest.fixture
    async def service(self):
        """Create a test instance of AdvancedAIService."""
        db_manager = DatabaseManager()
        cache_manager = EnhancedCacheManager()

        # Mock database and cache connections
        with patch.object(db_manager, "connect", new_callable=AsyncMock), patch.object(
            cache_manager, "connect", new_callable=AsyncMock
        ):

            service = AdvancedAIService(db_manager, cache_manager)
            return service

    def test_model_type_enum(self):
        """Test ModelType enum values."""
        assert ModelType.PREDICTIVE_ANALYTICS.value == "predictive_analytics"
        assert ModelType.NATURAL_LANGUAGE_PROCESSING.value == "nlp"
        assert ModelType.COMPUTER_VISION.value == "computer_vision"
        assert ModelType.REINFORCEMENT_LEARNING.value == "reinforcement_learning"
        assert ModelType.MULTI_MODAL.value == "multi_modal"
        assert ModelType.DEEP_LEARNING.value == "deep_learning"
        assert ModelType.TRANSFORMER.value == "transformer"
        assert ModelType.GENERATIVE_AI.value == "generative_ai"

    def test_model_status_enum(self):
        """Test ModelStatus enum values."""
        assert ModelStatus.TRAINING.value == "training"
        assert ModelStatus.EVALUATING.value == "evaluating"
        assert ModelStatus.DEPLOYED.value == "deployed"
        assert ModelStatus.ARCHIVED.value == "archived"
        assert ModelStatus.FAILED.value == "failed"
        assert ModelStatus.A_B_TESTING.value == "a_b_testing"

    def test_model_performance_enum(self):
        """Test ModelPerformance enum values."""
        assert ModelPerformance.EXCELLENT.value == "excellent"
        assert ModelPerformance.GOOD.value == "good"
        assert ModelPerformance.AVERAGE.value == "average"
        assert ModelPerformance.POOR.value == "poor"
        assert ModelPerformance.FAILED.value == "failed"

    def test_ai_model_dataclass(self):
        """Test AIModel dataclass."""
        model = AIModel(
            model_id="test-model-001",
            name="Test Model",
            model_type=ModelType.PREDICTIVE_ANALYTICS,
            version="1.0.0",
            status=ModelStatus.DEPLOYED,
            performance=ModelPerformance.GOOD,
            accuracy=0.85,
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            training_data_size=1000,
            features=["feature1", "feature2"],
            hyperparameters={"learning_rate": 0.001},
            model_path="models/test-model-001_1.0.0.pkl",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Test model for unit testing",
            tags=["test", "predictive_analytics"],
        )

        assert model.model_id == "test-model-001"
        assert model.name == "Test Model"
        assert model.model_type == ModelType.PREDICTIVE_ANALYTICS
        assert model.status == ModelStatus.DEPLOYED
        assert model.performance == ModelPerformance.GOOD
        assert model.accuracy == 0.85
        assert model.precision == 0.82
        assert model.recall == 0.88
        assert model.f1_score == 0.85
        assert model.training_data_size == 1000
        assert model.features == ["feature1", "feature2"]
        assert model.hyperparameters == {"learning_rate": 0.001}
        assert model.description == "Test model for unit testing"
        assert model.tags == ["test", "predictive_analytics"]

    def test_prediction_dataclass(self):
        """Test Prediction dataclass."""
        prediction = Prediction(
            prediction_id="pred-001",
            model_id="test-model-001",
            input_data={"feature1": 0.5, "feature2": 0.3},
            prediction="win",
            confidence=0.85,
            probabilities={"win": 0.85, "loss": 0.15},
            features_used=["feature1", "feature2"],
            prediction_time=datetime.now(),
            processing_time=0.05,
        )

        assert prediction.prediction_id == "pred-001"
        assert prediction.model_id == "test-model-001"
        assert prediction.input_data == {"feature1": 0.5, "feature2": 0.3}
        assert prediction.prediction == "win"
        assert prediction.confidence == 0.85
        assert prediction.probabilities == {"win": 0.85, "loss": 0.15}
        assert prediction.features_used == ["feature1", "feature2"]
        assert prediction.processing_time == 0.05

    def test_nlp_result_dataclass(self):
        """Test NLPResult dataclass."""
        nlp_result = NLPResult(
            nlp_id="nlp-001",
            text="This is a great betting opportunity",
            sentiment="positive",
            sentiment_score=0.75,
            entities=[{"text": "betting opportunity", "type": "OPPORTUNITY"}],
            keywords=["betting", "opportunity"],
            language="en",
            processing_time=0.025,
            confidence=0.82,
        )

        assert nlp_result.nlp_id == "nlp-001"
        assert nlp_result.text == "This is a great betting opportunity"
        assert nlp_result.sentiment == "positive"
        assert nlp_result.sentiment_score == 0.75
        assert nlp_result.entities == [
            {"text": "betting opportunity", "type": "OPPORTUNITY"}
        ]
        assert nlp_result.keywords == ["betting", "opportunity"]
        assert nlp_result.language == "en"
        assert nlp_result.processing_time == 0.025
        assert nlp_result.confidence == 0.82

    def test_computer_vision_result_dataclass(self):
        """Test ComputerVisionResult dataclass."""
        cv_result = ComputerVisionResult(
            cv_id="cv-001",
            image_path="/images/betting_slip.jpg",
            objects_detected=[{"name": "document", "confidence": 0.95}],
            text_extracted="Betting slip with odds",
            face_analysis={"count": 0, "emotions": []},
            image_quality=0.85,
            processing_time=0.15,
            confidence=0.90,
        )

        assert cv_result.cv_id == "cv-001"
        assert cv_result.image_path == "/images/betting_slip.jpg"
        assert cv_result.objects_detected == [{"name": "document", "confidence": 0.95}]
        assert cv_result.text_extracted == "Betting slip with odds"
        assert cv_result.face_analysis == {"count": 0, "emotions": []}
        assert cv_result.image_quality == 0.85
        assert cv_result.processing_time == 0.15
        assert cv_result.confidence == 0.90

    def test_reinforcement_learning_state_dataclass(self):
        """Test ReinforcementLearningState dataclass."""
        rl_state = ReinforcementLearningState(
            rl_id="rl-001",
            state={"user_engagement": 0.8, "betting_activity": 0.6},
            action="recommend_bet",
            reward=0.75,
            next_state={"user_engagement": 0.85, "betting_activity": 0.7},
            episode=1,
            step=10,
            learning_rate=0.01,
            exploration_rate=0.1,
            timestamp=datetime.now(),
        )

        assert rl_state.rl_id == "rl-001"
        assert rl_state.state == {"user_engagement": 0.8, "betting_activity": 0.6}
        assert rl_state.action == "recommend_bet"
        assert rl_state.reward == 0.75
        assert rl_state.next_state == {"user_engagement": 0.85, "betting_activity": 0.7}
        assert rl_state.episode == 1
        assert rl_state.step == 10
        assert rl_state.learning_rate == 0.01
        assert rl_state.exploration_rate == 0.1

    def test_model_training_job_dataclass(self):
        """Test ModelTrainingJob dataclass."""
        job = ModelTrainingJob(
            job_id="job-001",
            model_type=ModelType.PREDICTIVE_ANALYTICS,
            training_data={"dataset_size": 1000, "features": ["feature1", "feature2"]},
            hyperparameters={"learning_rate": 0.001, "batch_size": 32},
            status="training",
            progress=0.5,
            start_time=datetime.now(),
        )

        assert job.job_id == "job-001"
        assert job.model_type == ModelType.PREDICTIVE_ANALYTICS
        assert job.training_data == {
            "dataset_size": 1000,
            "features": ["feature1", "feature2"],
        }
        assert job.hyperparameters == {"learning_rate": 0.001, "batch_size": 32}
        assert job.status == "training"
        assert job.progress == 0.5

    @pytest.mark.asyncio
    async def test_create_model(self, service):
        """Test creating an AI model."""
        with patch.object(
            service, "_save_model_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            model = await service.create_model(
                name="Test Predictive Model",
                model_type=ModelType.PREDICTIVE_ANALYTICS,
                hyperparameters={"learning_rate": 0.001, "batch_size": 32},
                description="Test model for unit testing",
            )

            assert model.name == "Test Predictive Model"
            assert model.model_type == ModelType.PREDICTIVE_ANALYTICS
            assert model.status == ModelStatus.TRAINING
            assert model.performance == ModelPerformance.AVERAGE
            assert model.hyperparameters == {"learning_rate": 0.001, "batch_size": 32}
            assert model.description == "Test model for unit testing"
            assert model.tags == ["predictive_analytics"]

    @pytest.mark.asyncio
    async def test_train_model(self, service):
        """Test training an AI model."""
        # Create a model first
        with patch.object(
            service, "_save_model_to_db", new_callable=AsyncMock
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            model = await service.create_model(
                name="Test Model",
                model_type=ModelType.PREDICTIVE_ANALYTICS,
                hyperparameters={"learning_rate": 0.001},
            )

            # Add model to service
            service.models[model.model_id] = model

            # Test training
            training_data = {"dataset_size": 1000, "features": ["feature1", "feature2"]}
            job = await service.train_model(model.model_id, training_data)

            assert job.model_type == ModelType.PREDICTIVE_ANALYTICS
            assert job.training_data == training_data
            assert job.status == "training"
            assert job.progress == 0.0

    @pytest.mark.asyncio
    async def test_predict(self, service):
        """Test making predictions."""
        # Create a deployed model
        model = AIModel(
            model_id="test-model-001",
            name="Test Model",
            model_type=ModelType.PREDICTIVE_ANALYTICS,
            version="1.0.0",
            status=ModelStatus.DEPLOYED,
            performance=ModelPerformance.GOOD,
            accuracy=0.85,
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            training_data_size=1000,
            features=["feature1", "feature2"],
            hyperparameters={"learning_rate": 0.001},
            model_path="models/test-model-001_1.0.0.pkl",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        service.models[model.model_id] = model

        with patch.object(service, "_save_prediction_to_db", new_callable=AsyncMock):

            input_data = {"feature1": 0.5, "feature2": 0.3}
            prediction = await service.predict(model.model_id, input_data)

            assert prediction.model_id == model.model_id
            assert prediction.input_data == input_data
            assert prediction.confidence > 0
            assert prediction.processing_time > 0

    @pytest.mark.asyncio
    async def test_process_nlp(self, service):
        """Test NLP processing."""
        with patch.object(service, "_save_nlp_result_to_db", new_callable=AsyncMock):

            text = "This is a great betting opportunity"
            result = await service.process_nlp(text, "en")

            assert result.text == text
            assert result.language == "en"
            assert result.sentiment in ["positive", "negative", "neutral"]
            assert result.sentiment_score > 0
            assert result.processing_time > 0
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_process_computer_vision(self, service):
        """Test computer vision processing."""
        with patch.object(service, "_save_cv_result_to_db", new_callable=AsyncMock):

            image_path = "/images/test.jpg"
            result = await service.process_computer_vision(image_path)

            assert result.image_path == image_path
            assert result.image_quality > 0
            assert result.processing_time > 0
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_reinforcement_learning_step(self, service):
        """Test reinforcement learning step."""
        with patch.object(service, "_save_rl_state_to_db", new_callable=AsyncMock):

            state = {"user_engagement": 0.8, "betting_activity": 0.6}
            action = "recommend_bet"
            reward = 0.75

            result = await service.reinforcement_learning_step(state, action, reward)

            assert result.state == state
            assert result.action == action
            assert result.reward == reward
            assert result.episode > 0
            assert result.step > 0
            assert result.learning_rate > 0
            assert result.exploration_rate > 0

    @pytest.mark.asyncio
    async def test_get_model_performance(self, service):
        """Test getting model performance metrics."""
        # Create a model
        model = AIModel(
            model_id="test-model-001",
            name="Test Model",
            model_type=ModelType.PREDICTIVE_ANALYTICS,
            version="1.0.0",
            status=ModelStatus.DEPLOYED,
            performance=ModelPerformance.GOOD,
            accuracy=0.85,
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            training_data_size=1000,
            features=["feature1", "feature2"],
            hyperparameters={"learning_rate": 0.001},
            model_path="models/test-model-001_1.0.0.pkl",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        service.models[model.model_id] = model

        with patch.object(
            service, "_get_model_metrics_from_db", new_callable=AsyncMock
        ) as mock_metrics:
            mock_metrics.return_value = {
                "predictions_made": 150,
                "average_confidence": 0.85,
                "average_processing_time": 0.05,
            }

            performance = await service.get_model_performance(model.model_id)

            assert performance["model_id"] == model.model_id
            assert performance["name"] == model.name
            assert performance["type"] == model.model_type.value
            assert performance["status"] == model.status.value
            assert performance["performance"] == model.performance.value
            assert performance["accuracy"] == model.accuracy
            assert performance["precision"] == model.precision
            assert performance["recall"] == model.recall
            assert performance["f1_score"] == model.f1_score

    @pytest.mark.asyncio
    async def test_deploy_model(self, service):
        """Test deploying a model."""
        # Create a model in evaluating status
        model = AIModel(
            model_id="test-model-001",
            name="Test Model",
            model_type=ModelType.PREDICTIVE_ANALYTICS,
            version="1.0.0",
            status=ModelStatus.EVALUATING,
            performance=ModelPerformance.GOOD,
            accuracy=0.85,
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            training_data_size=1000,
            features=["feature1", "feature2"],
            hyperparameters={"learning_rate": 0.001},
            model_path="models/test-model-001_1.0.0.pkl",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        service.models[model.model_id] = model

        with patch.object(service, "_update_model_in_db", new_callable=AsyncMock):

            success = await service.deploy_model(model.model_id)

            assert success is True
            assert model.status == ModelStatus.DEPLOYED
            assert model.deployed_at is not None
            assert service.active_models[model.model_type] == model.model_id

    @pytest.mark.asyncio
    async def test_service_start_stop(self, service):
        """Test service start and stop methods."""
        with patch.object(
            service, "_load_models", new_callable=AsyncMock
        ), patch.object(
            service, "_initialize_models", new_callable=AsyncMock
        ), patch.object(
            service, "_save_models", new_callable=AsyncMock
        ):

            await service.start()
            await service.stop()

            # Verify methods were called
            service._load_models.assert_called_once()
            service._initialize_models.assert_called_once()
            service._save_models.assert_called_once()

    def test_update_prediction_stats(self, service):
        """Test updating prediction statistics."""
        prediction = Prediction(
            prediction_id="pred-001",
            model_id="test-model-001",
            input_data={"feature1": 0.5},
            prediction="win",
            confidence=0.85,
            probabilities={"win": 0.85, "loss": 0.15},
            features_used=["feature1"],
            prediction_time=datetime.now(),
            processing_time=0.05,
        )

        initial_stats = service.prediction_stats.copy()
        service._update_prediction_stats(prediction)

        assert (
            service.prediction_stats["total_predictions"]
            == initial_stats["total_predictions"] + 1
        )
        assert (
            service.prediction_stats["successful_predictions"]
            == initial_stats["successful_predictions"] + 1
        )
        assert service.prediction_stats["average_confidence"] > 0
        assert service.prediction_stats["average_processing_time"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
