"""Enhanced Security Monitoring Service for Advanced Threat Detection."""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac
import secrets
from collections import defaultdict, deque
import threading

from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib

from bot.services.security_service import (
    SecurityService,
    SecurityEvent,
    SecurityEventType,
    ThreatLevel,
)
from bot.services.performance_monitor import time_operation, record_metric
from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import EnhancedCacheManager

logger = logging.getLogger(__name__)

# Enhanced security monitoring cache TTLs
ENHANCED_SECURITY_CACHE_TTLS = {
    "behavioral_profiles": 3600,  # 1 hour
    "ml_models": 7200,  # 2 hours
    "anomaly_scores": 1800,  # 30 minutes
    "threat_patterns": 3600,  # 1 hour
    "fraud_indicators": 900,  # 15 minutes
    "behavioral_analysis": 1800,  # 30 minutes
    "ml_predictions": 300,  # 5 minutes
    "threat_intelligence": 3600,  # 1 hour
    "security_analytics": 1800,  # 30 minutes
    "incident_correlation": 900,  # 15 minutes
}


class ThreatPattern(Enum):
    """Advanced threat patterns for detection."""

    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    TEMPORAL_ANOMALY = "temporal_anomaly"
    SPATIAL_ANOMALY = "spatial_anomaly"
    SEQUENCE_ANOMALY = "sequence_anomaly"
    COLLUSION_PATTERN = "collusion_pattern"
    BOT_ACTIVITY = "bot_activity"
    ACCOUNT_TAKEOVER = "account_takeover"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    INSIDER_THREAT = "insider_threat"


class BehavioralMetric(Enum):
    """Behavioral metrics for analysis."""

    LOGIN_FREQUENCY = "login_frequency"
    SESSION_DURATION = "session_duration"
    COMMAND_USAGE = "command_usage"
    DATA_ACCESS_PATTERNS = "data_access_patterns"
    TIME_OF_DAY_ACTIVITY = "time_of_day_activity"
    GEOGRAPHIC_PATTERNS = "geographic_patterns"
    DEVICE_FINGERPRINT = "device_fingerprint"
    NETWORK_PATTERNS = "network_patterns"
    BETTING_PATTERNS = "betting_patterns"
    SOCIAL_INTERACTIONS = "social_interactions"


@dataclass
class BehavioralProfile:
    """User behavioral profile for anomaly detection."""

    user_id: int
    guild_id: Optional[int]
    metrics: Dict[str, float]
    baseline: Dict[str, float]
    last_updated: datetime
    confidence_score: float
    anomaly_score: float
    risk_level: str


@dataclass
class ThreatPattern:
    """Advanced threat pattern detection."""

    pattern_type: ThreatPattern
    confidence: float
    evidence: Dict[str, Any]
    affected_users: List[int]
    affected_guilds: List[int]
    severity: ThreatLevel
    timestamp: datetime
    is_active: bool
    mitigation_status: str


@dataclass
class MLPrediction:
    """Machine learning prediction result."""

    user_id: int
    guild_id: Optional[int]
    prediction_type: str
    confidence: float
    features: Dict[str, float]
    risk_score: float
    timestamp: datetime
    model_version: str


class EnhancedSecurityMonitor:
    """Enhanced security monitoring with advanced threat detection."""

    def __init__(
        self,
        security_service: SecurityService,
        db_manager: DatabaseManager,
        cache_manager: EnhancedCacheManager,
    ):
        """Initialize the enhanced security monitor."""
        self.security_service = security_service
        self.db_manager = db_manager
        self.cache_manager = cache_manager

        # ML Models
        self.anomaly_detector = None
        self.fraud_classifier = None
        self.behavioral_classifier = None
        self.scaler = StandardScaler()

        # Behavioral analysis
        self.behavioral_profiles: Dict[int, BehavioralProfile] = {}
        self.threat_patterns: List[ThreatPattern] = []
        self.ml_predictions: Dict[int, MLPrediction] = {}

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None

        # Thread safety
        self._lock = threading.Lock()

        # Performance tracking
        self.analysis_stats = defaultdict(int)

        logger.info("Enhanced security monitor initialized")

    async def start_monitoring(self) -> None:
        """Start enhanced security monitoring."""
        if self.is_monitoring:
            logger.warning("Enhanced security monitoring is already active")
            return

        # Initialize ML models
        await self._initialize_ml_models()

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Enhanced security monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop enhanced security monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Enhanced security monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for enhanced security."""
        while self.is_monitoring:
            try:
                await self._update_behavioral_profiles()
                await self._detect_advanced_threats()
                await self._run_ml_predictions()
                await self._correlate_security_events()
                await asyncio.sleep(60)  # Run every minute
            except Exception as e:
                logger.error(f"Error in enhanced security monitoring loop: {e}")
                await asyncio.sleep(10)

    async def _initialize_ml_models(self) -> None:
        """Initialize machine learning models."""
        try:
            # Initialize anomaly detection model
            self.anomaly_detector = IsolationForest(
                contamination=0.1, random_state=42, n_estimators=100
            )

            # Initialize fraud classification model
            self.fraud_classifier = RandomForestClassifier(
                n_estimators=100, random_state=42, class_weight="balanced"
            )

            # Initialize behavioral classification model
            self.behavioral_classifier = RandomForestClassifier(
                n_estimators=50, random_state=42
            )

            logger.info("ML models initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")

    @time_operation("enhanced_behavioral_analysis")
    async def analyze_user_behavior(
        self, user_id: int, guild_id: Optional[int] = None
    ) -> BehavioralProfile:
        """Analyze user behavior and create/update behavioral profile."""
        try:
            # Get user's recent security events
            events = await self._get_user_recent_events(user_id, guild_id, hours=24)

            if not events:
                return None

            # Calculate behavioral metrics
            metrics = await self._calculate_behavioral_metrics(
                events, user_id, guild_id
            )

            # Get or create behavioral profile
            profile_key = f"behavioral_profile:{user_id}:{guild_id or 'global'}"
            cached_profile = await self.cache_manager.get(profile_key)

            if cached_profile:
                profile = BehavioralProfile(**cached_profile)
                # Update existing profile
                profile.metrics = metrics
                profile.last_updated = datetime.now()
                profile.anomaly_score = await self._calculate_anomaly_score(profile)
            else:
                # Create new profile
                profile = BehavioralProfile(
                    user_id=user_id,
                    guild_id=guild_id,
                    metrics=metrics,
                    baseline=metrics.copy(),  # Initial baseline
                    last_updated=datetime.now(),
                    confidence_score=0.5,
                    anomaly_score=0.0,
                    risk_level="low",
                )

            # Update confidence score
            profile.confidence_score = await self._calculate_confidence_score(profile)

            # Cache the profile
            await self.cache_manager.set(
                profile_key,
                profile.__dict__,
                ttl=ENHANCED_SECURITY_CACHE_TTLS["behavioral_profiles"],
            )

            with self._lock:
                self.behavioral_profiles[user_id] = profile

            return profile

        except Exception as e:
            logger.error(f"Error analyzing user behavior: {e}")
            return None

    async def _calculate_behavioral_metrics(
        self, events: List[SecurityEvent], user_id: int, guild_id: Optional[int]
    ) -> Dict[str, float]:
        """Calculate behavioral metrics from security events."""
        try:
            metrics = {}

            # Login frequency
            login_events = [
                e for e in events if e.event_type == SecurityEventType.LOGIN_SUCCESS
            ]
            metrics["login_frequency"] = len(login_events) / 24.0  # per hour

            # Session duration (if available)
            session_durations = []
            for event in events:
                if hasattr(event, "session_duration"):
                    session_durations.append(event.session_duration)
            metrics["avg_session_duration"] = (
                np.mean(session_durations) if session_durations else 0
            )

            # Time of day activity
            hour_activity = defaultdict(int)
            for event in events:
                hour = event.timestamp.hour
                hour_activity[hour] += 1
            metrics["activity_entropy"] = self._calculate_entropy(hour_activity)

            # Geographic patterns (if IP data available)
            unique_ips = set()
            for event in events:
                if event.ip_address:
                    unique_ips.add(event.ip_address)
            metrics["geographic_diversity"] = len(unique_ips)

            # Command usage patterns
            command_usage = defaultdict(int)
            for event in events:
                if hasattr(event, "command"):
                    command_usage[event.command] += 1
            metrics["command_entropy"] = self._calculate_entropy(command_usage)

            # Risk score
            metrics["risk_score"] = await self._calculate_risk_score(events)

            return metrics

        except Exception as e:
            logger.error(f"Error calculating behavioral metrics: {e}")
            return {}

    def _calculate_entropy(self, data: Dict[str, int]) -> float:
        """Calculate entropy of a distribution."""
        try:
            total = sum(data.values())
            if total == 0:
                return 0

            probabilities = [count / total for count in data.values()]
            entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
            return entropy
        except Exception:
            return 0

    async def _calculate_risk_score(self, events: List[SecurityEvent]) -> float:
        """Calculate risk score based on security events."""
        try:
            risk_score = 0.0

            # High-risk events
            high_risk_events = [
                SecurityEventType.LOGIN_FAILURE,
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                SecurityEventType.FRAUD_DETECTED,
            ]

            for event in events:
                if event.event_type in high_risk_events:
                    risk_score += 0.3
                elif event.risk_score:
                    risk_score += event.risk_score * 0.1

            return min(risk_score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.0

    async def _calculate_anomaly_score(self, profile: BehavioralProfile) -> float:
        """Calculate anomaly score for behavioral profile."""
        try:
            if not self.anomaly_detector:
                return 0.0

            # Prepare features for anomaly detection
            features = list(profile.metrics.values())
            if not features:
                return 0.0

            # Reshape for sklearn
            features_array = np.array(features).reshape(1, -1)

            # Get anomaly score (lower is more anomalous)
            anomaly_score = self.anomaly_detector.decision_function(features_array)[0]

            # Convert to 0-1 scale where 1 is most anomalous
            normalized_score = 1 - (anomaly_score + 0.5)  # Normalize to 0-1

            return max(0.0, min(1.0, normalized_score))

        except Exception as e:
            logger.error(f"Error calculating anomaly score: {e}")
            return 0.0

    async def _calculate_confidence_score(self, profile: BehavioralProfile) -> float:
        """Calculate confidence score for behavioral profile."""
        try:
            # Base confidence on amount of data
            event_count = len(profile.metrics)
            base_confidence = min(event_count / 10.0, 1.0)

            # Adjust based on data quality
            quality_score = 0.0
            for metric, value in profile.metrics.items():
                if value > 0:
                    quality_score += 0.1

            confidence = (base_confidence + quality_score) / 2.0
            return min(confidence, 1.0)

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5

    @time_operation("enhanced_threat_detection")
    async def detect_advanced_threats(
        self, user_id: int, guild_id: Optional[int] = None
    ) -> List[ThreatPattern]:
        """Detect advanced threats using behavioral analysis and ML."""
        try:
            threats = []

            # Get user's behavioral profile
            profile = await self.analyze_user_behavior(user_id, guild_id)
            if not profile:
                return threats

            # Check for behavioral anomalies
            if profile.anomaly_score > 0.7:
                threat = ThreatPattern(
                    pattern_type=ThreatPattern.BEHAVIORAL_ANOMALY,
                    confidence=profile.anomaly_score,
                    evidence={
                        "anomaly_score": profile.anomaly_score,
                        "metrics": profile.metrics,
                    },
                    affected_users=[user_id],
                    affected_guilds=[guild_id] if guild_id else [],
                    severity=(
                        ThreatLevel.HIGH
                        if profile.anomaly_score > 0.8
                        else ThreatLevel.MEDIUM
                    ),
                    timestamp=datetime.now(),
                    is_active=True,
                    mitigation_status="pending",
                )
                threats.append(threat)

            # Check for temporal anomalies
            temporal_threat = await self._detect_temporal_anomalies(user_id, guild_id)
            if temporal_threat:
                threats.append(temporal_threat)

            # Check for collusion patterns
            collusion_threat = await self._detect_collusion_patterns(user_id, guild_id)
            if collusion_threat:
                threats.append(collusion_threat)

            # Check for bot activity
            bot_threat = await self._detect_bot_activity(user_id, guild_id)
            if bot_threat:
                threats.append(bot_threat)

            # Store threats
            with self._lock:
                self.threat_patterns.extend(threats)

            return threats

        except Exception as e:
            logger.error(f"Error detecting advanced threats: {e}")
            return []

    async def _detect_temporal_anomalies(
        self, user_id: int, guild_id: Optional[int]
    ) -> Optional[ThreatPattern]:
        """Detect temporal anomalies in user behavior."""
        try:
            # Get user's recent events
            events = await self._get_user_recent_events(user_id, guild_id, hours=24)

            if len(events) < 5:
                return None

            # Analyze time patterns
            hours = [event.timestamp.hour for event in events]
            hour_counts = defaultdict(int)
            for hour in hours:
                hour_counts[hour] += 1

            # Check for unusual activity patterns
            avg_activity = np.mean(list(hour_counts.values()))
            std_activity = np.std(list(hour_counts.values()))

            # Detect unusual spikes
            unusual_hours = []
            for hour, count in hour_counts.items():
                if count > avg_activity + 2 * std_activity:
                    unusual_hours.append(hour)

            if unusual_hours:
                return ThreatPattern(
                    pattern_type=ThreatPattern.TEMPORAL_ANOMALY,
                    confidence=0.8,
                    evidence={
                        "unusual_hours": unusual_hours,
                        "hour_counts": dict(hour_counts),
                    },
                    affected_users=[user_id],
                    affected_guilds=[guild_id] if guild_id else [],
                    severity=ThreatLevel.MEDIUM,
                    timestamp=datetime.now(),
                    is_active=True,
                    mitigation_status="pending",
                )

            return None

        except Exception as e:
            logger.error(f"Error detecting temporal anomalies: {e}")
            return None

    async def _detect_collusion_patterns(
        self, user_id: int, guild_id: Optional[int]
    ) -> Optional[ThreatPattern]:
        """Detect collusion patterns between users."""
        try:
            # Get recent events for the guild
            if not guild_id:
                return None

            guild_events = await self._get_guild_recent_events(guild_id, hours=24)

            # Look for coordinated activities
            user_events = [e for e in guild_events if e.user_id == user_id]
            other_events = [e for e in guild_events if e.user_id != user_id]

            # Check for synchronized activities
            collusion_indicators = []

            for user_event in user_events:
                for other_event in other_events:
                    time_diff = abs(
                        (user_event.timestamp - other_event.timestamp).total_seconds()
                    )

                    # If events happen within 5 minutes and are similar
                    if (
                        time_diff < 300
                        and user_event.event_type == other_event.event_type
                    ):
                        collusion_indicators.append(
                            {
                                "user_id": other_event.user_id,
                                "event_type": other_event.event_type,
                                "time_diff": time_diff,
                            }
                        )

            if len(collusion_indicators) >= 3:
                return ThreatPattern(
                    pattern_type=ThreatPattern.COLLUSION_PATTERN,
                    confidence=0.7,
                    evidence={"collusion_indicators": collusion_indicators},
                    affected_users=[user_id]
                    + list(set(i["user_id"] for i in collusion_indicators)),
                    affected_guilds=[guild_id],
                    severity=ThreatLevel.HIGH,
                    timestamp=datetime.now(),
                    is_active=True,
                    mitigation_status="pending",
                )

            return None

        except Exception as e:
            logger.error(f"Error detecting collusion patterns: {e}")
            return None

    async def _detect_bot_activity(
        self, user_id: int, guild_id: Optional[int]
    ) -> Optional[ThreatPattern]:
        """Detect bot-like activity patterns."""
        try:
            # Get user's recent events
            events = await self._get_user_recent_events(user_id, guild_id, hours=1)

            if len(events) < 10:
                return None

            # Analyze timing patterns
            timestamps = [event.timestamp for event in events]
            intervals = []

            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i - 1]).total_seconds()
                intervals.append(interval)

            # Check for regular intervals (bot-like behavior)
            if intervals:
                mean_interval = np.mean(intervals)
                std_interval = np.std(intervals)

                # If intervals are very regular (low standard deviation)
                if std_interval < mean_interval * 0.1:  # Very regular timing
                    return ThreatPattern(
                        pattern_type=ThreatPattern.BOT_ACTIVITY,
                        confidence=0.9,
                        evidence={
                            "mean_interval": mean_interval,
                            "std_interval": std_interval,
                            "event_count": len(events),
                        },
                        affected_users=[user_id],
                        affected_guilds=[guild_id] if guild_id else [],
                        severity=ThreatLevel.HIGH,
                        timestamp=datetime.now(),
                        is_active=True,
                        mitigation_status="pending",
                    )

            return None

        except Exception as e:
            logger.error(f"Error detecting bot activity: {e}")
            return None

    @time_operation("enhanced_ml_predictions")
    async def run_ml_predictions(
        self, user_id: int, guild_id: Optional[int] = None
    ) -> MLPrediction:
        """Run machine learning predictions for user."""
        try:
            # Get user's behavioral profile
            profile = await self.analyze_user_behavior(user_id, guild_id)
            if not profile:
                return None

            # Prepare features for ML
            features = list(profile.metrics.values())
            if not features:
                return None

            # Run fraud prediction
            fraud_confidence = await self._predict_fraud(features)

            # Run behavioral prediction
            behavioral_confidence = await self._predict_behavior(features)

            # Calculate overall risk score
            risk_score = (fraud_confidence + behavioral_confidence) / 2.0

            prediction = MLPrediction(
                user_id=user_id,
                guild_id=guild_id,
                prediction_type="comprehensive",
                confidence=risk_score,
                features=profile.metrics,
                risk_score=risk_score,
                timestamp=datetime.now(),
                model_version="1.0",
            )

            # Cache prediction
            prediction_key = f"ml_prediction:{user_id}:{guild_id or 'global'}"
            await self.cache_manager.set(
                prediction_key,
                prediction.__dict__,
                ttl=ENHANCED_SECURITY_CACHE_TTLS["ml_predictions"],
            )

            with self._lock:
                self.ml_predictions[user_id] = prediction

            return prediction

        except Exception as e:
            logger.error(f"Error running ML predictions: {e}")
            return None

    async def _predict_fraud(self, features: List[float]) -> float:
        """Predict fraud probability using ML model."""
        try:
            if not self.fraud_classifier:
                return 0.5

            # Reshape features for prediction
            features_array = np.array(features).reshape(1, -1)

            # Get fraud probability
            fraud_prob = self.fraud_classifier.predict_proba(features_array)[0]

            # Return probability of fraud class (assuming binary classification)
            return fraud_prob[1] if len(fraud_prob) > 1 else fraud_prob[0]

        except Exception as e:
            logger.error(f"Error predicting fraud: {e}")
            return 0.5

    async def _predict_behavior(self, features: List[float]) -> float:
        """Predict behavioral risk using ML model."""
        try:
            if not self.behavioral_classifier:
                return 0.5

            # Reshape features for prediction
            features_array = np.array(features).reshape(1, -1)

            # Get behavioral risk probability
            behavior_prob = self.behavioral_classifier.predict_proba(features_array)[0]

            # Return probability of risky behavior
            return behavior_prob[1] if len(behavior_prob) > 1 else behavior_prob[0]

        except Exception as e:
            logger.error(f"Error predicting behavior: {e}")
            return 0.5

    async def _get_user_recent_events(
        self, user_id: int, guild_id: Optional[int], hours: int = 24
    ) -> List[SecurityEvent]:
        """Get recent security events for a user."""
        try:
            # This would typically query the security service or database
            # For now, return empty list as placeholder
            return []
        except Exception as e:
            logger.error(f"Error getting user recent events: {e}")
            return []

    async def _get_guild_recent_events(
        self, guild_id: int, hours: int = 24
    ) -> List[SecurityEvent]:
        """Get recent security events for a guild."""
        try:
            # This would typically query the security service or database
            # For now, return empty list as placeholder
            return []
        except Exception as e:
            logger.error(f"Error getting guild recent events: {e}")
            return []

    async def _update_behavioral_profiles(self) -> None:
        """Update behavioral profiles for active users."""
        try:
            # This would typically iterate through active users
            # For now, this is a placeholder
            pass
        except Exception as e:
            logger.error(f"Error updating behavioral profiles: {e}")

    async def _detect_advanced_threats(self) -> None:
        """Detect advanced threats across all monitored users."""
        try:
            # This would typically iterate through monitored users
            # For now, this is a placeholder
            pass
        except Exception as e:
            logger.error(f"Error detecting advanced threats: {e}")

    async def _run_ml_predictions(self) -> None:
        """Run ML predictions for monitored users."""
        try:
            # This would typically iterate through monitored users
            # For now, this is a placeholder
            pass
        except Exception as e:
            logger.error(f"Error running ML predictions: {e}")

    async def _correlate_security_events(self) -> None:
        """Correlate security events across the system."""
        try:
            # This would typically analyze patterns across multiple users/events
            # For now, this is a placeholder
            pass
        except Exception as e:
            logger.error(f"Error correlating security events: {e}")

    async def get_enhanced_security_report(
        self, guild_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive enhanced security report."""
        try:
            report = {
                "guild_id": guild_id,
                "report_period": f"{days} days",
                "generated_at": datetime.now().isoformat(),
                "behavioral_profiles": len(self.behavioral_profiles),
                "threat_patterns": len(self.threat_patterns),
                "ml_predictions": len(self.ml_predictions),
                "analysis_stats": dict(self.analysis_stats),
                "active_threats": len([t for t in self.threat_patterns if t.is_active]),
                "high_risk_users": len(
                    [
                        p
                        for p in self.behavioral_profiles.values()
                        if p.anomaly_score > 0.7
                    ]
                ),
            }

            return report

        except Exception as e:
            logger.error(f"Error generating enhanced security report: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup enhanced security monitor resources."""
        await self.stop_monitoring()
        logger.info("Enhanced security monitor cleanup completed")


# Global enhanced security monitor instance
enhanced_security_monitor = None


async def get_enhanced_security_monitor(
    security_service: SecurityService,
    db_manager: DatabaseManager,
    cache_manager: EnhancedCacheManager,
) -> EnhancedSecurityMonitor:
    """Get the global enhanced security monitor instance."""
    global enhanced_security_monitor

    if enhanced_security_monitor is None:
        enhanced_security_monitor = EnhancedSecurityMonitor(
            security_service=security_service,
            db_manager=db_manager,
            cache_manager=cache_manager,
        )

    return enhanced_security_monitor
