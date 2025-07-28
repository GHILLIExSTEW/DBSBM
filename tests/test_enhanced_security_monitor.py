"""Tests for enhanced security monitoring service."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from bot.data.db_manager import DatabaseManager
from bot.services.enhanced_security_monitor import (
    BehavioralMetric,
    BehavioralProfile,
    EnhancedSecurityMonitor,
    MLPrediction,
)
from bot.services.enhanced_security_monitor import ThreatPattern
from bot.services.enhanced_security_monitor import ThreatPattern as ThreatPatternEnum
from bot.services.enhanced_security_monitor import get_enhanced_security_monitor
from bot.services.security_service import (
    SecurityEvent,
    SecurityEventType,
    SecurityService,
    ThreatLevel,
)
from bot.utils.enhanced_cache_manager import EnhancedCacheManager


class TestEnhancedSecurityMonitor:
    """Test cases for EnhancedSecurityMonitor class."""

    @pytest.fixture
    async def enhanced_monitor(self):
        """Create an enhanced security monitor instance for testing."""
        # Mock dependencies
        mock_security_service = Mock(spec=SecurityService)
        mock_db_manager = Mock(spec=DatabaseManager)
        mock_cache_manager = Mock(spec=EnhancedCacheManager)

        # Setup cache manager mock
        mock_cache_manager.get = AsyncMock(return_value=None)
        mock_cache_manager.set = AsyncMock()

        monitor = EnhancedSecurityMonitor(
            security_service=mock_security_service,
            db_manager=mock_db_manager,
            cache_manager=mock_cache_manager,
        )

        yield monitor
        await monitor.cleanup()

    @pytest.fixture
    def mock_security_events(self):
        """Create mock security events for testing."""
        events = []

        # Create login events
        for i in range(5):
            event = Mock(spec=SecurityEvent)
            event.event_type = SecurityEventType.LOGIN_SUCCESS
            event.timestamp = datetime.now() - timedelta(hours=i)
            event.user_id = 123
            event.guild_id = 456
            event.ip_address = f"192.168.1.{i}"
            event.risk_score = 0.1
            events.append(event)

        # Create some suspicious events
        for i in range(2):
            event = Mock(spec=SecurityEvent)
            event.event_type = SecurityEventType.SUSPICIOUS_ACTIVITY
            event.timestamp = datetime.now() - timedelta(minutes=i * 30)
            event.user_id = 123
            event.guild_id = 456
            event.ip_address = f"192.168.1.{i+10}"
            event.risk_score = 0.8
            events.append(event)

        return events

    def test_enhanced_monitor_initialization(self, enhanced_monitor):
        """Test enhanced security monitor initialization."""
        assert enhanced_monitor.security_service is not None
        assert enhanced_monitor.db_manager is not None
        assert enhanced_monitor.cache_manager is not None
        assert enhanced_monitor.is_monitoring is False
        assert len(enhanced_monitor.behavioral_profiles) == 0
        assert len(enhanced_monitor.threat_patterns) == 0
        assert len(enhanced_monitor.ml_predictions) == 0

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, enhanced_monitor):
        """Test starting and stopping enhanced security monitoring."""
        # Start monitoring
        await enhanced_monitor.start_monitoring()
        assert enhanced_monitor.is_monitoring is True
        assert enhanced_monitor.monitoring_task is not None

        # Wait a bit for monitoring to run
        await asyncio.sleep(0.1)

        # Stop monitoring
        await enhanced_monitor.stop_monitoring()
        assert enhanced_monitor.is_monitoring is False
        assert enhanced_monitor.monitoring_task is None

    @pytest.mark.asyncio
    async def test_analyze_user_behavior(self, enhanced_monitor, mock_security_events):
        """Test user behavior analysis."""
        # Mock the _get_user_recent_events method
        enhanced_monitor._get_user_recent_events = AsyncMock(
            return_value=mock_security_events
        )

        # Analyze user behavior
        profile = await enhanced_monitor.analyze_user_behavior(
            user_id=123, guild_id=456
        )

        assert profile is not None
        assert profile.user_id == 123
        assert profile.guild_id == 456
        assert isinstance(profile.metrics, dict)
        assert "login_frequency" in profile.metrics
        assert "risk_score" in profile.metrics
        assert isinstance(profile.anomaly_score, float)
        assert isinstance(profile.confidence_score, float)

    @pytest.mark.asyncio
    async def test_calculate_behavioral_metrics(
        self, enhanced_monitor, mock_security_events
    ):
        """Test behavioral metrics calculation."""
        metrics = await enhanced_monitor._calculate_behavioral_metrics(
            mock_security_events, user_id=123, guild_id=456
        )

        assert isinstance(metrics, dict)
        assert "login_frequency" in metrics
        assert "activity_entropy" in metrics
        assert "geographic_diversity" in metrics
        assert "risk_score" in metrics
        assert metrics["login_frequency"] > 0
        assert metrics["geographic_diversity"] > 0

    def test_calculate_entropy(self, enhanced_monitor):
        """Test entropy calculation."""
        # Test with uniform distribution
        data = {"a": 1, "b": 1, "c": 1, "d": 1}
        entropy = enhanced_monitor._calculate_entropy(data)
        assert entropy == 2.0  # log2(4) = 2

        # Test with skewed distribution
        data = {"a": 3, "b": 1}
        entropy = enhanced_monitor._calculate_entropy(data)
        assert entropy < 2.0  # Less entropy for skewed distribution

        # Test with empty data
        data = {}
        entropy = enhanced_monitor._calculate_entropy(data)
        assert entropy == 0

    @pytest.mark.asyncio
    async def test_calculate_risk_score(self, enhanced_monitor, mock_security_events):
        """Test risk score calculation."""
        risk_score = await enhanced_monitor._calculate_risk_score(mock_security_events)

        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        assert risk_score > 0  # Should have some risk from suspicious events

    @pytest.mark.asyncio
    async def test_calculate_anomaly_score(self, enhanced_monitor):
        """Test anomaly score calculation."""
        # Create a behavioral profile
        profile = BehavioralProfile(
            user_id=123,
            guild_id=456,
            metrics={
                "login_frequency": 0.5,
                "risk_score": 0.3,
                "activity_entropy": 2.0,
            },
            baseline={
                "login_frequency": 0.2,
                "risk_score": 0.1,
                "activity_entropy": 1.5,
            },
            last_updated=datetime.now(),
            confidence_score=0.8,
            anomaly_score=0.0,
            risk_level="medium",
        )

        # Mock the anomaly detector
        enhanced_monitor.anomaly_detector = Mock()
        enhanced_monitor.anomaly_detector.decision_function.return_value = np.array(
            [-0.2]
        )

        anomaly_score = await enhanced_monitor._calculate_anomaly_score(profile)

        assert isinstance(anomaly_score, float)
        assert 0.0 <= anomaly_score <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_confidence_score(self, enhanced_monitor):
        """Test confidence score calculation."""
        profile = BehavioralProfile(
            user_id=123,
            guild_id=456,
            metrics={"metric1": 0.5, "metric2": 0.3, "metric3": 0.8},
            baseline={"metric1": 0.5, "metric2": 0.3, "metric3": 0.8},
            last_updated=datetime.now(),
            confidence_score=0.0,
            anomaly_score=0.0,
            risk_level="low",
        )

        confidence = await enhanced_monitor._calculate_confidence_score(profile)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_detect_advanced_threats(self, enhanced_monitor):
        """Test advanced threat detection."""
        # Mock behavioral analysis
        profile = BehavioralProfile(
            user_id=123,
            guild_id=456,
            metrics={"login_frequency": 0.8, "risk_score": 0.9},
            baseline={"login_frequency": 0.2, "risk_score": 0.1},
            last_updated=datetime.now(),
            confidence_score=0.8,
            anomaly_score=0.85,  # High anomaly score
            risk_level="high",
        )

        enhanced_monitor.analyze_user_behavior = AsyncMock(return_value=profile)
        enhanced_monitor._detect_temporal_anomalies = AsyncMock(return_value=None)
        enhanced_monitor._detect_collusion_patterns = AsyncMock(return_value=None)
        enhanced_monitor._detect_bot_activity = AsyncMock(return_value=None)

        threats = await enhanced_monitor.detect_advanced_threats(
            user_id=123, guild_id=456
        )

        assert isinstance(threats, list)
        assert len(threats) >= 1  # Should detect behavioral anomaly

        # Check the behavioral anomaly threat
        behavioral_threat = threats[0]
        assert behavioral_threat.pattern_type == ThreatPatternEnum.BEHAVIORAL_ANOMALY
        assert behavioral_threat.confidence > 0.7
        assert behavioral_threat.affected_users == [123]
        assert behavioral_threat.affected_guilds == [456]

    @pytest.mark.asyncio
    async def test_detect_temporal_anomalies(self, enhanced_monitor):
        """Test temporal anomaly detection."""
        # Create events with unusual timing
        events = []
        for i in range(10):
            event = Mock(spec=SecurityEvent)
            event.timestamp = datetime.now() - timedelta(hours=i)
            event.user_id = 123
            events.append(event)

        # Add unusual spike at hour 3
        for i in range(5):
            event = Mock(spec=SecurityEvent)
            event.timestamp = datetime.now() - timedelta(hours=3)
            event.user_id = 123
            events.append(event)

        enhanced_monitor._get_user_recent_events = AsyncMock(return_value=events)

        threat = await enhanced_monitor._detect_temporal_anomalies(
            user_id=123, guild_id=456
        )

        assert threat is not None
        assert threat.pattern_type == ThreatPatternEnum.TEMPORAL_ANOMALY
        assert threat.confidence > 0.0
        assert threat.affected_users == [123]

    @pytest.mark.asyncio
    async def test_detect_collusion_patterns(self, enhanced_monitor):
        """Test collusion pattern detection."""
        # Create coordinated events
        events = []
        base_time = datetime.now()

        # User 123 events
        for i in range(3):
            event = Mock(spec=SecurityEvent)
            event.timestamp = base_time - timedelta(minutes=i * 2)
            event.user_id = 123
            event.event_type = SecurityEventType.LOGIN_SUCCESS
            events.append(event)

        # User 456 events (coordinated)
        for i in range(3):
            event = Mock(spec=SecurityEvent)
            event.timestamp = base_time - timedelta(
                minutes=i * 2 + 1
            )  # Very close timing
            event.user_id = 456
            event.event_type = SecurityEventType.LOGIN_SUCCESS
            events.append(event)

        enhanced_monitor._get_guild_recent_events = AsyncMock(return_value=events)

        threat = await enhanced_monitor._detect_collusion_patterns(
            user_id=123, guild_id=789
        )

        assert threat is not None
        assert threat.pattern_type == ThreatPatternEnum.COLLUSION_PATTERN
        assert threat.confidence > 0.0
        assert 123 in threat.affected_users
        assert 456 in threat.affected_users

    @pytest.mark.asyncio
    async def test_detect_bot_activity(self, enhanced_monitor):
        """Test bot activity detection."""
        # Create events with very regular timing
        events = []
        base_time = datetime.now()

        for i in range(15):
            event = Mock(spec=SecurityEvent)
            # Very regular 30-second intervals
            event.timestamp = base_time - timedelta(seconds=i * 30)
            event.user_id = 123
            events.append(event)

        enhanced_monitor._get_user_recent_events = AsyncMock(return_value=events)

        threat = await enhanced_monitor._detect_bot_activity(user_id=123, guild_id=456)

        assert threat is not None
        assert threat.pattern_type == ThreatPatternEnum.BOT_ACTIVITY
        assert threat.confidence > 0.0
        assert threat.affected_users == [123]

    @pytest.mark.asyncio
    async def test_run_ml_predictions(self, enhanced_monitor):
        """Test ML prediction functionality."""
        # Mock behavioral profile
        profile = BehavioralProfile(
            user_id=123,
            guild_id=456,
            metrics={"feature1": 0.5, "feature2": 0.3, "feature3": 0.8},
            baseline={"feature1": 0.5, "feature2": 0.3, "feature3": 0.8},
            last_updated=datetime.now(),
            confidence_score=0.8,
            anomaly_score=0.2,
            risk_level="medium",
        )

        enhanced_monitor.analyze_user_behavior = AsyncMock(return_value=profile)
        enhanced_monitor._predict_fraud = AsyncMock(return_value=0.7)
        enhanced_monitor._predict_behavior = AsyncMock(return_value=0.6)

        prediction = await enhanced_monitor.run_ml_predictions(
            user_id=123, guild_id=456
        )

        assert prediction is not None
        assert prediction.user_id == 123
        assert prediction.guild_id == 456
        assert prediction.prediction_type == "comprehensive"
        assert isinstance(prediction.confidence, float)
        assert isinstance(prediction.risk_score, float)
        assert prediction.risk_score == 0.65  # (0.7 + 0.6) / 2

    @pytest.mark.asyncio
    async def test_predict_fraud(self, enhanced_monitor):
        """Test fraud prediction."""
        features = [0.5, 0.3, 0.8, 0.2]

        # Mock the fraud classifier
        enhanced_monitor.fraud_classifier = Mock()
        enhanced_monitor.fraud_classifier.predict_proba.return_value = np.array(
            [[0.3, 0.7]]
        )

        fraud_confidence = await enhanced_monitor._predict_fraud(features)

        assert isinstance(fraud_confidence, float)
        assert 0.0 <= fraud_confidence <= 1.0
        assert fraud_confidence == 0.7

    @pytest.mark.asyncio
    async def test_predict_behavior(self, enhanced_monitor):
        """Test behavioral prediction."""
        features = [0.5, 0.3, 0.8, 0.2]

        # Mock the behavioral classifier
        enhanced_monitor.behavioral_classifier = Mock()
        enhanced_monitor.behavioral_classifier.predict_proba.return_value = np.array(
            [[0.4, 0.6]]
        )

        behavior_confidence = await enhanced_monitor._predict_behavior(features)

        assert isinstance(behavior_confidence, float)
        assert 0.0 <= behavior_confidence <= 1.0
        assert behavior_confidence == 0.6

    @pytest.mark.asyncio
    async def test_get_enhanced_security_report(self, enhanced_monitor):
        """Test enhanced security report generation."""
        # Add some test data
        enhanced_monitor.behavioral_profiles[123] = BehavioralProfile(
            user_id=123,
            guild_id=456,
            metrics={"test": 0.5},
            baseline={"test": 0.5},
            last_updated=datetime.now(),
            confidence_score=0.8,
            anomaly_score=0.2,
            risk_level="low",
        )

        enhanced_monitor.threat_patterns.append(Mock(spec=ThreatPattern))
        enhanced_monitor.ml_predictions[123] = Mock(spec=MLPrediction)

        report = await enhanced_monitor.get_enhanced_security_report(
            guild_id=456, days=30
        )

        assert isinstance(report, dict)
        assert report["guild_id"] == 456
        assert report["report_period"] == "30 days"
        assert "generated_at" in report
        assert report["behavioral_profiles"] == 1
        assert report["threat_patterns"] == 1
        assert report["ml_predictions"] == 1

    @pytest.mark.asyncio
    async def test_ml_models_initialization(self, enhanced_monitor):
        """Test ML models initialization."""
        await enhanced_monitor._initialize_ml_models()

        assert enhanced_monitor.anomaly_detector is not None
        assert enhanced_monitor.fraud_classifier is not None
        assert enhanced_monitor.behavioral_classifier is not None

    @pytest.mark.asyncio
    async def test_monitoring_loop_error_handling(self, enhanced_monitor):
        """Test error handling in monitoring loop."""
        # Mock a method to raise an exception
        enhanced_monitor._update_behavioral_profiles = AsyncMock(
            side_effect=Exception("Test error")
        )

        # Start monitoring
        await enhanced_monitor.start_monitoring()

        # Wait a bit for the error to be handled
        await asyncio.sleep(0.1)

        # Stop monitoring
        await enhanced_monitor.stop_monitoring()

        # Should not have crashed
        assert True

    def test_entropy_calculation_edge_cases(self, enhanced_monitor):
        """Test entropy calculation with edge cases."""
        # Test with single value
        data = {"a": 1}
        entropy = enhanced_monitor._calculate_entropy(data)
        assert entropy == 0

        # Test with zero values
        data = {"a": 0, "b": 0}
        entropy = enhanced_monitor._calculate_entropy(data)
        assert entropy == 0

        # Test with mixed values
        data = {"a": 1, "b": 0, "c": 2}
        entropy = enhanced_monitor._calculate_entropy(data)
        assert entropy > 0

    @pytest.mark.asyncio
    async def test_behavioral_analysis_with_no_events(self, enhanced_monitor):
        """Test behavioral analysis when no events are available."""
        enhanced_monitor._get_user_recent_events = AsyncMock(return_value=[])

        profile = await enhanced_monitor.analyze_user_behavior(
            user_id=123, guild_id=456
        )

        assert profile is None

    @pytest.mark.asyncio
    async def test_threat_detection_with_no_profile(self, enhanced_monitor):
        """Test threat detection when no behavioral profile is available."""
        enhanced_monitor.analyze_user_behavior = AsyncMock(return_value=None)

        threats = await enhanced_monitor.detect_advanced_threats(
            user_id=123, guild_id=456
        )

        assert threats == []


class TestGlobalEnhancedSecurityMonitor:
    """Test cases for global enhanced security monitor functionality."""

    @pytest.mark.asyncio
    async def test_get_enhanced_security_monitor(self):
        """Test getting the global enhanced security monitor instance."""
        # Mock dependencies
        mock_security_service = Mock(spec=SecurityService)
        mock_db_manager = Mock(spec=DatabaseManager)
        mock_cache_manager = Mock(spec=EnhancedCacheManager)

        # Setup cache manager mock
        mock_cache_manager.get = AsyncMock(return_value=None)
        mock_cache_manager.set = AsyncMock()

        monitor = await get_enhanced_security_monitor(
            security_service=mock_security_service,
            db_manager=mock_db_manager,
            cache_manager=mock_cache_manager,
        )

        assert isinstance(monitor, EnhancedSecurityMonitor)
        assert monitor.security_service == mock_security_service
        assert monitor.db_manager == mock_db_manager
        assert monitor.cache_manager == mock_cache_manager


class TestEnhancedSecurityMonitorIntegration:
    """Integration tests for enhanced security monitor."""

    @pytest.mark.asyncio
    async def test_enhanced_monitor_with_real_security_service(self):
        """Test enhanced monitor integration with real security service."""
        # Mock dependencies
        mock_security_service = Mock(spec=SecurityService)
        mock_db_manager = Mock(spec=DatabaseManager)
        mock_cache_manager = Mock(spec=EnhancedCacheManager)

        # Setup cache manager mock
        mock_cache_manager.get = AsyncMock(return_value=None)
        mock_cache_manager.set = AsyncMock()

        monitor = EnhancedSecurityMonitor(
            security_service=mock_security_service,
            db_manager=mock_db_manager,
            cache_manager=mock_cache_manager,
        )

        # Test integration
        await monitor.start_monitoring()
        assert monitor.is_monitoring is True

        await monitor.stop_monitoring()
        assert monitor.is_monitoring is False

        await monitor.cleanup()

    @pytest.mark.asyncio
    async def test_enhanced_monitor_error_handling(self):
        """Test enhanced monitor error handling."""
        # Mock dependencies with failing methods
        mock_security_service = Mock(spec=SecurityService)
        mock_db_manager = Mock(spec=DatabaseManager)
        mock_cache_manager = Mock(spec=EnhancedCacheManager)

        # Setup cache manager mock to fail
        mock_cache_manager.get = AsyncMock(side_effect=Exception("Cache error"))
        mock_cache_manager.set = AsyncMock(side_effect=Exception("Cache error"))

        monitor = EnhancedSecurityMonitor(
            security_service=mock_security_service,
            db_manager=mock_db_manager,
            cache_manager=mock_cache_manager,
        )

        # Should handle errors gracefully
        profile = await monitor.analyze_user_behavior(user_id=123, guild_id=456)
        assert profile is None  # Should return None on error


if __name__ == "__main__":
    pytest.main([__file__])
