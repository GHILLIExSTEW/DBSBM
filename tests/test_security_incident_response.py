"""
Test suite for Security Incident Response Service

This module tests the comprehensive security incident response capabilities including:
- Automated incident response workflows
- Security alert escalation procedures
- Incident tracking and resolution
- Post-incident analysis and reporting
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.data.db_manager import DatabaseManager
from bot.services.security_incident_response import (
    EscalationLevel,
    EscalationRule,
    IncidentSeverity,
    IncidentStatus,
    IncidentWorkflow,
    ResponseAction,
    SecurityIncident,
    SecurityIncidentResponseService,
)
from bot.utils.enhanced_cache_manager import EnhancedCacheManager


class TestSecurityIncidentResponseService:
    """Test cases for Security Incident Response Service."""

    @pytest.fixture
    async def service(self):
        """Create a test instance of SecurityIncidentResponseService."""
        db_manager = DatabaseManager()
        cache_manager = EnhancedCacheManager()

        # Mock database and cache connections
        with patch.object(db_manager, "connect", new_callable=AsyncMock), patch.object(
            cache_manager, "connect", new_callable=AsyncMock
        ):

            service = SecurityIncidentResponseService(db_manager, cache_manager)
            return service

    @pytest.fixture
    def sample_incident_data(self):
        """Sample incident data for testing."""
        return {
            "title": "Suspicious Login Attempt",
            "description": "Multiple failed login attempts detected from unknown IP",
            "severity": "high",
            "incident_type": "unauthorized_access",
            "affected_systems": ["web-server-01", "auth-service"],
            "affected_users": ["user123", "user456"],
            "indicators": {
                "source_ip": "192.168.1.100",
                "failed_attempts": 15,
                "time_window": "5 minutes",
            },
            "evidence": {
                "log_entries": ["Failed login attempt for user123"],
                "ip_geolocation": "Unknown location",
            },
        }

    @pytest.fixture
    def sample_escalation_rule_data(self):
        """Sample escalation rule data for testing."""
        return {
            "name": "Critical Data Breach Escalation",
            "conditions": {
                "min_severity": "critical",
                "incident_types": ["data_breach", "malware"],
            },
            "escalation_level": "level_3",
            "response_time_minutes": 15,
            "recipients": ["ciso@company.com", "security-manager@company.com"],
            "is_active": True,
        }

    @pytest.mark.asyncio
    async def test_create_incident(self, service, sample_incident_data):
        """Test creating a new security incident."""
        with patch.object(
            service, "_store_incident", new_callable=AsyncMock
        ), patch.object(
            service, "_trigger_response_workflow", new_callable=AsyncMock
        ), patch.object(
            service, "_check_escalation_rules", new_callable=AsyncMock
        ), patch.object(
            service, "_cache_incident", new_callable=AsyncMock
        ):

            incident = await service.create_incident(sample_incident_data)

            assert incident.incident_id is not None
            assert incident.title == sample_incident_data["title"]
            assert incident.description == sample_incident_data["description"]
            assert incident.severity.value == sample_incident_data["severity"]
            assert incident.status == IncidentStatus.DETECTED
            assert incident.incident_type == sample_incident_data["incident_type"]
            assert incident.affected_systems == sample_incident_data["affected_systems"]
            assert incident.affected_users == sample_incident_data["affected_users"]
            assert incident.indicators == sample_incident_data["indicators"]
            assert incident.evidence == sample_incident_data["evidence"]
            assert incident.escalation_level == EscalationLevel.LEVEL_1
            assert incident.assigned_to is None
            assert incident.resolved_at is None
            assert incident.resolution_notes is None
            assert incident.post_incident_analysis is None

    @pytest.mark.asyncio
    async def test_update_incident(self, service):
        """Test updating an existing security incident."""
        # Create a mock incident
        incident = SecurityIncident(
            incident_id="test-incident-123",
            title="Original Title",
            description="Original Description",
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.DETECTED,
            incident_type="test",
            detection_time=datetime.utcnow(),
            affected_systems=[],
            affected_users=[],
            indicators={},
            evidence={},
            response_actions=[],
            escalation_level=EscalationLevel.LEVEL_1,
            assigned_to=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            resolved_at=None,
            resolution_notes=None,
            post_incident_analysis=None,
        )

        with patch.object(service, "get_incident", return_value=incident), patch.object(
            service, "_update_incident", new_callable=AsyncMock
        ), patch.object(service, "_cache_incident", new_callable=AsyncMock):

            updates = {
                "title": "Updated Title",
                "severity": "high",
                "assigned_to": "security-analyst@company.com",
            }

            updated_incident = await service.update_incident(
                "test-incident-123", updates
            )

            assert updated_incident.title == "Updated Title"
            assert updated_incident.severity.value == "high"
            assert updated_incident.assigned_to == "security-analyst@company.com"

    @pytest.mark.asyncio
    async def test_get_incident(self, service):
        """Test retrieving a security incident."""
        incident_id = "test-incident-123"

        with patch.object(
            service, "_get_incident_from_db", return_value=None
        ), patch.object(service, "_cache_incident", new_callable=AsyncMock):

            incident = await service.get_incident(incident_id)
            assert incident is None

    @pytest.mark.asyncio
    async def test_list_incidents(self, service):
        """Test listing security incidents with filters."""
        with patch.object(
            service, "_get_incidents_from_db", return_value=[]
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            incidents = await service.list_incidents()
            assert incidents == []

            # Test with filters
            filters = {"severity": "high", "status": "detected"}
            incidents = await service.list_incidents(filters)
            assert incidents == []

    @pytest.mark.asyncio
    async def test_create_response_workflow(self, service):
        """Test creating an automated response workflow."""
        incident_id = "test-incident-123"
        workflow_type = "data_breach_response"

        with patch.object(
            service, "_get_workflow_steps", return_value=[]
        ), patch.object(
            service, "_store_workflow", new_callable=AsyncMock
        ), patch.object(
            service, "_execute_workflow", new_callable=AsyncMock
        ):

            workflow = await service.create_response_workflow(
                incident_id, workflow_type
            )

            assert workflow.workflow_id is not None
            assert workflow.incident_id == incident_id
            assert workflow.workflow_type == workflow_type
            assert workflow.current_step == 0
            assert workflow.status == "pending"
            assert workflow.completed_at is None
            assert workflow.execution_log == []

    @pytest.mark.asyncio
    async def test_escalate_incident(self, service):
        """Test escalating a security incident."""
        incident_id = "test-incident-123"
        escalation_level = EscalationLevel.LEVEL_2
        reason = "Multiple systems affected"

        # Create a mock incident
        incident = SecurityIncident(
            incident_id=incident_id,
            title="Test Incident",
            description="Test Description",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DETECTED,
            incident_type="test",
            detection_time=datetime.utcnow(),
            affected_systems=[],
            affected_users=[],
            indicators={},
            evidence={},
            response_actions=[],
            escalation_level=EscalationLevel.LEVEL_1,
            assigned_to=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            resolved_at=None,
            resolution_notes=None,
            post_incident_analysis=None,
        )

        with patch.object(service, "get_incident", return_value=incident), patch.object(
            service, "_store_escalation_event", new_callable=AsyncMock
        ), patch.object(
            service, "_notify_escalation_recipients", new_callable=AsyncMock
        ), patch.object(
            service, "_update_incident", new_callable=AsyncMock
        ), patch.object(
            service, "_cache_incident", new_callable=AsyncMock
        ):

            escalated_incident = await service.escalate_incident(
                incident_id, escalation_level, reason
            )

            assert escalated_incident.escalation_level == escalation_level
            assert escalated_incident.status == IncidentStatus.ESCALATED

    @pytest.mark.asyncio
    async def test_resolve_incident(self, service):
        """Test resolving a security incident."""
        incident_id = "test-incident-123"
        resolution_notes = "Incident contained and resolved"

        # Create a mock incident
        incident = SecurityIncident(
            incident_id=incident_id,
            title="Test Incident",
            description="Test Description",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.INVESTIGATING,
            incident_type="test",
            detection_time=datetime.utcnow(),
            affected_systems=[],
            affected_users=[],
            indicators={},
            evidence={},
            response_actions=[],
            escalation_level=EscalationLevel.LEVEL_1,
            assigned_to=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            resolved_at=None,
            resolution_notes=None,
            post_incident_analysis=None,
        )

        with patch.object(service, "get_incident", return_value=incident), patch.object(
            service, "_generate_post_incident_analysis", return_value={}
        ), patch.object(
            service, "_generate_incident_report", new_callable=AsyncMock
        ), patch.object(
            service, "_update_incident", new_callable=AsyncMock
        ), patch.object(
            service, "_cache_incident", new_callable=AsyncMock
        ):

            resolved_incident = await service.resolve_incident(
                incident_id, resolution_notes
            )

            assert resolved_incident.status == IncidentStatus.RESOLVED
            assert resolved_incident.resolved_at is not None
            assert resolved_incident.resolution_notes == resolution_notes
            assert resolved_incident.post_incident_analysis is not None

    @pytest.mark.asyncio
    async def test_create_escalation_rule(self, service, sample_escalation_rule_data):
        """Test creating an escalation rule."""
        with patch.object(service, "_store_escalation_rule", new_callable=AsyncMock):

            rule = await service.create_escalation_rule(sample_escalation_rule_data)

            assert rule.rule_id is not None
            assert rule.name == sample_escalation_rule_data["name"]
            assert rule.conditions == sample_escalation_rule_data["conditions"]
            assert (
                rule.escalation_level.value
                == sample_escalation_rule_data["escalation_level"]
            )
            assert (
                rule.response_time_minutes
                == sample_escalation_rule_data["response_time_minutes"]
            )
            assert rule.recipients == sample_escalation_rule_data["recipients"]
            assert rule.is_active == sample_escalation_rule_data["is_active"]

    @pytest.mark.asyncio
    async def test_get_incident_analytics(self, service):
        """Test getting incident response analytics."""
        time_period = "30_days"

        with patch.object(
            service,
            "_calculate_incident_analytics",
            return_value={
                "time_period": time_period,
                "total_incidents": 10,
                "resolved_incidents": 8,
                "resolution_rate": 80.0,
                "avg_resolution_time_hours": 4.5,
                "severity_distribution": {"high": 5, "medium": 3, "low": 2},
                "incident_type_distribution": {
                    "data_breach": 3,
                    "malware": 4,
                    "unauthorized_access": 3,
                },
                "escalation_rate": 20.0,
            },
        ), patch.object(service.cache_manager, "set", new_callable=AsyncMock):

            analytics = await service.get_incident_analytics(time_period)

            assert analytics["time_period"] == time_period
            assert analytics["total_incidents"] == 10
            assert analytics["resolved_incidents"] == 8
            assert analytics["resolution_rate"] == 80.0
            assert analytics["avg_resolution_time_hours"] == 4.5
            assert "severity_distribution" in analytics
            assert "incident_type_distribution" in analytics
            assert analytics["escalation_rate"] == 20.0

    @pytest.mark.asyncio
    async def test_workflow_execution(self, service):
        """Test workflow execution with multiple steps."""
        workflow = IncidentWorkflow(
            workflow_id="test-workflow-123",
            incident_id="test-incident-123",
            workflow_type="data_breach_response",
            steps=[
                {"step": 1, "action": "isolate_affected_systems", "timeout": 300},
                {"step": 2, "action": "backup_critical_data", "timeout": 600},
                {"step": 3, "action": "notify_security_team", "timeout": 60},
            ],
            current_step=0,
            status="pending",
            created_at=datetime.utcnow(),
            completed_at=None,
            execution_log=[],
        )

        with patch.object(
            service, "_update_workflow", new_callable=AsyncMock
        ), patch.object(
            service, "_execute_workflow_action", return_value={"status": "success"}
        ):

            await service._execute_workflow(workflow)

            assert workflow.status == "completed"
            assert workflow.completed_at is not None
            assert len(workflow.execution_log) == 3

    @pytest.mark.asyncio
    async def test_workflow_action_execution(self, service):
        """Test individual workflow action execution."""
        incident_id = "test-incident-123"

        # Test system isolation action
        result = await service._isolate_systems(incident_id)
        assert result["status"] == "success"
        assert "systems_isolated" in result

        # Test data backup action
        result = await service._backup_data(incident_id)
        assert result["status"] == "success"
        assert "backup_size" in result

        # Test security team notification
        result = await service._notify_security_team(incident_id)
        assert result["status"] == "success"
        assert "recipients" in result

        # Test impact assessment
        result = await service._assess_impact(incident_id)
        assert result["status"] == "success"
        assert "impact_level" in result

    @pytest.mark.asyncio
    async def test_escalation_rule_evaluation(self, service):
        """Test escalation rule evaluation logic."""
        # Create a test incident
        incident = SecurityIncident(
            incident_id="test-incident-123",
            title="Test Incident",
            description="Test Description",
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.DETECTED,
            incident_type="data_breach",
            detection_time=datetime.utcnow(),
            affected_systems=["server-001", "server-002", "server-003"],
            affected_users=["user123", "user456"],
            indicators={},
            evidence={},
            response_actions=[],
            escalation_level=EscalationLevel.LEVEL_1,
            assigned_to=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            resolved_at=None,
            resolution_notes=None,
            post_incident_analysis=None,
        )

        # Test rule that should trigger
        rule = EscalationRule(
            rule_id="test-rule-123",
            name="Critical Data Breach Rule",
            conditions={
                "min_severity": "critical",
                "incident_types": ["data_breach"],
                "min_affected_systems": 2,
            },
            escalation_level=EscalationLevel.LEVEL_3,
            response_time_minutes=15,
            recipients=["ciso@company.com"],
            is_active=True,
            created_at=datetime.utcnow(),
        )

        should_trigger = await service._evaluate_escalation_rule(incident, rule)
        assert should_trigger is True

        # Test rule that should not trigger (severity too low)
        rule.conditions["min_severity"] = "critical"
        incident.severity = IncidentSeverity.MEDIUM
        should_trigger = await service._evaluate_escalation_rule(incident, rule)
        assert should_trigger is False

    @pytest.mark.asyncio
    async def test_post_incident_analysis_generation(self, service):
        """Test post-incident analysis generation."""
        incident = SecurityIncident(
            incident_id="test-incident-123",
            title="Test Incident",
            description="Test Description",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.RESOLVED,
            incident_type="data_breach",
            detection_time=datetime.utcnow() - timedelta(hours=2),
            affected_systems=["server-001"],
            affected_users=["user123"],
            indicators={},
            evidence={},
            response_actions=[],
            escalation_level=EscalationLevel.LEVEL_1,
            assigned_to="analyst@company.com",
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow(),
            resolved_at=datetime.utcnow(),
            resolution_notes="Incident resolved",
            post_incident_analysis=None,
        )

        analysis = await service._generate_post_incident_analysis(incident)

        assert "analysis_date" in analysis
        assert "incident_duration" in analysis
        assert "response_effectiveness" in analysis
        assert "lessons_learned" in analysis
        assert "recommendations" in analysis
        assert "cost_analysis" in analysis
        assert analysis["incident_duration"] > 0

    @pytest.mark.asyncio
    async def test_incident_analytics_calculation(self, service):
        """Test incident analytics calculation."""
        time_period = "30_days"

        # Mock incidents data
        incidents = [
            SecurityIncident(
                incident_id="incident-1",
                title="Incident 1",
                description="Test incident 1",
                severity=IncidentSeverity.HIGH,
                status=IncidentStatus.RESOLVED,
                incident_type="data_breach",
                detection_time=datetime.utcnow() - timedelta(days=5),
                affected_systems=["server-001"],
                affected_users=["user123"],
                indicators={},
                evidence={},
                response_actions=[],
                escalation_level=EscalationLevel.LEVEL_1,
                assigned_to=None,
                created_at=datetime.utcnow() - timedelta(days=5),
                updated_at=datetime.utcnow(),
                resolved_at=datetime.utcnow() - timedelta(days=4),
                resolution_notes="Resolved",
                post_incident_analysis=None,
            ),
            SecurityIncident(
                incident_id="incident-2",
                title="Incident 2",
                description="Test incident 2",
                severity=IncidentSeverity.MEDIUM,
                status=IncidentStatus.ESCALATED,
                incident_type="malware",
                detection_time=datetime.utcnow() - timedelta(days=3),
                affected_systems=["server-002"],
                affected_users=["user456"],
                indicators={},
                evidence={},
                response_actions=[],
                escalation_level=EscalationLevel.LEVEL_2,
                assigned_to=None,
                created_at=datetime.utcnow() - timedelta(days=3),
                updated_at=datetime.utcnow(),
                resolved_at=None,
                resolution_notes=None,
                post_incident_analysis=None,
            ),
        ]

        with patch.object(service, "_get_incidents_from_db", return_value=incidents):
            analytics = await service._calculate_incident_analytics(time_period)

            assert analytics["time_period"] == time_period
            assert analytics["total_incidents"] == 2
            assert analytics["resolved_incidents"] == 1
            assert analytics["resolution_rate"] == 50.0
            assert analytics["escalation_rate"] == 50.0
            assert "severity_distribution" in analytics
            assert "incident_type_distribution" in analytics

    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """Test error handling in various scenarios."""
        # Test incident not found
        with patch.object(service, "get_incident", return_value=None):
            with pytest.raises(
                ValueError, match="Incident test-incident-123 not found"
            ):
                await service.update_incident("test-incident-123", {"title": "Updated"})

        # Test workflow execution error
        workflow = IncidentWorkflow(
            workflow_id="test-workflow-123",
            incident_id="test-incident-123",
            workflow_type="test",
            steps=[{"step": 1, "action": "invalid_action"}],
            current_step=0,
            status="pending",
            created_at=datetime.utcnow(),
            completed_at=None,
            execution_log=[],
        )

        with patch.object(
            service, "_update_workflow", new_callable=AsyncMock
        ), patch.object(
            service, "_execute_workflow_action", side_effect=Exception("Action failed")
        ):

            await service._execute_workflow(workflow)
            assert workflow.status == "failed"
            assert len(workflow.execution_log) > 0
            assert "error" in workflow.execution_log[-1]

    @pytest.mark.asyncio
    async def test_cache_integration(self, service):
        """Test cache integration for incident data."""
        incident_id = "test-incident-123"
        cached_data = {
            "incident_id": incident_id,
            "title": "Cached Incident",
            "description": "Cached description",
            "severity": "high",
            "status": "detected",
            "incident_type": "test",
            "detection_time": datetime.utcnow().isoformat(),
            "affected_systems": [],
            "affected_users": [],
            "indicators": {},
            "evidence": {},
            "response_actions": [],
            "escalation_level": "level_1",
            "assigned_to": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
            "resolution_notes": None,
            "post_incident_analysis": None,
        }

        with patch.object(
            service.cache_manager, "get", return_value=json.dumps(cached_data)
        ), patch.object(service, "_get_incident_from_db", new_callable=AsyncMock):

            incident = await service.get_incident(incident_id)
            assert incident is not None
            assert incident.incident_id == incident_id
            assert incident.title == "Cached Incident"

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, service):
        """Test performance monitoring integration."""
        # Test that time_operation decorator is applied
        assert hasattr(service.create_incident, "__wrapped__")
        assert hasattr(service.update_incident, "__wrapped__")
        assert hasattr(service.get_incident, "__wrapped__")
        assert hasattr(service.list_incidents, "__wrapped__")
        assert hasattr(service.create_response_workflow, "__wrapped__")
        assert hasattr(service.escalate_incident, "__wrapped__")
        assert hasattr(service.resolve_incident, "__wrapped__")
        assert hasattr(service.create_escalation_rule, "__wrapped__")
        assert hasattr(service.get_incident_analytics, "__wrapped__")


class TestSecurityIncidentDataStructures:
    """Test cases for security incident data structures."""

    def test_security_incident_creation(self):
        """Test SecurityIncident data structure creation."""
        incident = SecurityIncident(
            incident_id="test-123",
            title="Test Incident",
            description="Test description",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DETECTED,
            incident_type="test",
            detection_time=datetime.utcnow(),
            affected_systems=["server-001"],
            affected_users=["user123"],
            indicators={"ip": "192.168.1.100"},
            evidence={"logs": ["suspicious activity"]},
            response_actions=[ResponseAction.BLOCK_IP],
            escalation_level=EscalationLevel.LEVEL_1,
            assigned_to=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            resolved_at=None,
            resolution_notes=None,
            post_incident_analysis=None,
        )

        assert incident.incident_id == "test-123"
        assert incident.title == "Test Incident"
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.status == IncidentStatus.DETECTED
        assert incident.incident_type == "test"
        assert incident.affected_systems == ["server-001"]
        assert incident.affected_users == ["user123"]
        assert incident.indicators == {"ip": "192.168.1.100"}
        assert incident.evidence == {"logs": ["suspicious activity"]}
        assert incident.response_actions == [ResponseAction.BLOCK_IP]
        assert incident.escalation_level == EscalationLevel.LEVEL_1

    def test_incident_workflow_creation(self):
        """Test IncidentWorkflow data structure creation."""
        workflow = IncidentWorkflow(
            workflow_id="workflow-123",
            incident_id="incident-123",
            workflow_type="data_breach_response",
            steps=[{"step": 1, "action": "isolate_systems"}],
            current_step=0,
            status="pending",
            created_at=datetime.utcnow(),
            completed_at=None,
            execution_log=[],
        )

        assert workflow.workflow_id == "workflow-123"
        assert workflow.incident_id == "incident-123"
        assert workflow.workflow_type == "data_breach_response"
        assert workflow.current_step == 0
        assert workflow.status == "pending"
        assert workflow.completed_at is None
        assert workflow.execution_log == []

    def test_escalation_rule_creation(self):
        """Test EscalationRule data structure creation."""
        rule = EscalationRule(
            rule_id="rule-123",
            name="Critical Incident Rule",
            conditions={"min_severity": "critical"},
            escalation_level=EscalationLevel.LEVEL_3,
            response_time_minutes=15,
            recipients=["ciso@company.com"],
            is_active=True,
            created_at=datetime.utcnow(),
        )

        assert rule.rule_id == "rule-123"
        assert rule.name == "Critical Incident Rule"
        assert rule.conditions == {"min_severity": "critical"}
        assert rule.escalation_level == EscalationLevel.LEVEL_3
        assert rule.response_time_minutes == 15
        assert rule.recipients == ["ciso@company.com"]
        assert rule.is_active is True

    def test_enum_values(self):
        """Test enum values for various incident types."""
        # Test severity levels
        assert IncidentSeverity.LOW.value == "low"
        assert IncidentSeverity.MEDIUM.value == "medium"
        assert IncidentSeverity.HIGH.value == "high"
        assert IncidentSeverity.CRITICAL.value == "critical"

        # Test status levels
        assert IncidentStatus.DETECTED.value == "detected"
        assert IncidentStatus.INVESTIGATING.value == "investigating"
        assert IncidentStatus.CONTAINED.value == "contained"
        assert IncidentStatus.RESOLVED.value == "resolved"
        assert IncidentStatus.ESCALATED.value == "escalated"
        assert IncidentStatus.CLOSED.value == "closed"

        # Test escalation levels
        assert EscalationLevel.LEVEL_1.value == "level_1"
        assert EscalationLevel.LEVEL_2.value == "level_2"
        assert EscalationLevel.LEVEL_3.value == "level_3"
        assert EscalationLevel.LEVEL_4.value == "level_4"

        # Test response actions
        assert ResponseAction.BLOCK_IP.value == "block_ip"
        assert ResponseAction.DISABLE_ACCOUNT.value == "disable_account"
        assert ResponseAction.ISOLATE_SYSTEM.value == "isolate_system"
        assert ResponseAction.BACKUP_DATA.value == "backup_data"
        assert ResponseAction.NOTIFY_ADMIN.value == "notify_admin"
        assert ResponseAction.NOTIFY_LEGAL.value == "notify_legal"
        assert ResponseAction.NOTIFY_REGULATORY.value == "notify_regulatory"
        assert ResponseAction.ACTIVATE_DR.value == "activate_dr"


if __name__ == "__main__":
    pytest.main([__file__])
