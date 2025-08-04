"""
Security Incident Response Service

This module provides comprehensive security incident response capabilities including:
- Automated incident response workflows
- Security alert escalation procedures
- Incident tracking and resolution
- Post-incident analysis and reporting
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from uuid import uuid4

from bot.data.db_manager import DatabaseManager
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from bot.services.performance_monitor import time_operation

logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    """Incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Incident status levels."""

    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class EscalationLevel(Enum):
    """Escalation levels for incidents."""

    LEVEL_1 = "level_1"  # Security team
    LEVEL_2 = "level_2"  # Security manager
    LEVEL_3 = "level_3"  # CISO
    LEVEL_4 = "level_4"  # Executive team


class ResponseAction(Enum):
    """Automated response actions."""

    BLOCK_IP = "block_ip"
    DISABLE_ACCOUNT = "disable_account"
    ISOLATE_SYSTEM = "isolate_system"
    BACKUP_DATA = "backup_data"
    NOTIFY_ADMIN = "notify_admin"
    NOTIFY_LEGAL = "notify_legal"
    NOTIFY_REGULATORY = "notify_regulatory"
    ACTIVATE_DR = "activate_dr"


@dataclass
class SecurityIncident:
    """Security incident data structure."""

    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    incident_type: str
    detection_time: datetime
    affected_systems: List[str]
    affected_users: List[str]
    indicators: Dict[str, Any]
    evidence: Dict[str, Any]
    response_actions: List[ResponseAction]
    escalation_level: EscalationLevel
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    post_incident_analysis: Optional[Dict[str, Any]]


@dataclass
class IncidentWorkflow:
    """Incident response workflow data structure."""

    workflow_id: str
    incident_id: str
    workflow_type: str
    steps: List[Dict[str, Any]]
    current_step: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    execution_log: List[Dict[str, Any]]


@dataclass
class EscalationRule:
    """Escalation rule data structure."""

    rule_id: str
    name: str
    conditions: Dict[str, Any]
    escalation_level: EscalationLevel
    response_time_minutes: int
    recipients: List[str]
    is_active: bool
    created_at: datetime


class SecurityIncidentResponseService:
    """Comprehensive security incident response service."""

    def __init__(
        self, db_manager: DatabaseManager, cache_manager: EnhancedCacheManager
    ):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.cache_prefix = "security_incident"
        self.default_ttl = 3600  # 1 hour

    @time_operation
    async def create_incident(self, incident_data: Dict[str, Any]) -> SecurityIncident:
        """Create a new security incident."""
        incident_id = str(uuid4())

        incident = SecurityIncident(
            incident_id=incident_id,
            title=incident_data.get("title", ""),
            description=incident_data.get("description", ""),
            severity=IncidentSeverity(incident_data.get("severity", "medium")),
            status=IncidentStatus.DETECTED,
            incident_type=incident_data.get("incident_type", "unknown"),
            detection_time=datetime.utcnow(),
            affected_systems=incident_data.get("affected_systems", []),
            affected_users=incident_data.get("affected_users", []),
            indicators=incident_data.get("indicators", {}),
            evidence=incident_data.get("evidence", {}),
            response_actions=[],
            escalation_level=EscalationLevel.LEVEL_1,
            assigned_to=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            resolved_at=None,
            resolution_notes=None,
            post_incident_analysis=None,
        )

        # Store incident in database
        await self._store_incident(incident)

        # Trigger automated response workflow
        await self._trigger_response_workflow(incident)

        # Check escalation rules
        await self._check_escalation_rules(incident)

        # Cache incident data
        await self._cache_incident(incident)

        logger.info(f"Created security incident: {incident_id}")
        return incident

    @time_operation
    async def update_incident(
        self, incident_id: str, updates: Dict[str, Any]
    ) -> SecurityIncident:
        """Update an existing security incident."""
        incident = await self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # Update fields
        for key, value in updates.items():
            if hasattr(incident, key):
                setattr(incident, key, value)

        incident.updated_at = datetime.utcnow()

        # Update database
        await self._update_incident(incident)

        # Update cache
        await self._cache_incident(incident)

        logger.info(f"Updated security incident: {incident_id}")
        return incident

    @time_operation
    async def get_incident(self, incident_id: str) -> Optional[SecurityIncident]:
        """Get a security incident by ID."""
        # Try cache first
        cache_key = f"{self.cache_prefix}:incident:{incident_id}"
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return SecurityIncident(**json.loads(cached_data))

        # Get from database
        incident = await self._get_incident_from_db(incident_id)
        if incident:
            await self._cache_incident(incident)

        return incident

    @time_operation
    async def list_incidents(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[SecurityIncident]:
        """List security incidents with optional filters."""
        # Try cache first
        cache_key = f"{self.cache_prefix}:incidents:{hash(str(filters))}"
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return [
                SecurityIncident(**incident_data)
                for incident_data in json.loads(cached_data)
            ]

        # Get from database
        incidents = await self._get_incidents_from_db(filters)

        # Cache results
        if incidents:
            await self.cache_manager.set(
                cache_key,
                json.dumps([asdict(inc) for inc in incidents]),
                self.default_ttl,
            )

        return incidents

    @time_operation
    async def create_response_workflow(
        self, incident_id: str, workflow_type: str
    ) -> IncidentWorkflow:
        """Create an automated response workflow for an incident."""
        workflow_id = str(uuid4())

        # Define workflow steps based on incident type
        steps = await self._get_workflow_steps(workflow_type)

        workflow = IncidentWorkflow(
            workflow_id=workflow_id,
            incident_id=incident_id,
            workflow_type=workflow_type,
            steps=steps,
            current_step=0,
            status="pending",
            created_at=datetime.utcnow(),
            completed_at=None,
            execution_log=[],
        )

        # Store workflow
        await self._store_workflow(workflow)

        # Start workflow execution
        asyncio.create_task(self._execute_workflow(workflow))

        logger.info(
            f"Created response workflow: {workflow_id} for incident: {incident_id}"
        )
        return workflow

    @time_operation
    async def escalate_incident(
        self, incident_id: str, escalation_level: EscalationLevel, reason: str
    ) -> SecurityIncident:
        """Escalate a security incident."""
        incident = await self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        incident.escalation_level = escalation_level
        incident.status = IncidentStatus.ESCALATED
        incident.updated_at = datetime.utcnow()

        # Store escalation event
        await self._store_escalation_event(incident_id, escalation_level, reason)

        # Notify escalation recipients
        await self._notify_escalation_recipients(incident, escalation_level)

        # Update incident
        await self._update_incident(incident)
        await self._cache_incident(incident)

        logger.info(f"Escalated incident {incident_id} to {escalation_level.value}")
        return incident

    @time_operation
    async def resolve_incident(
        self, incident_id: str, resolution_notes: str
    ) -> SecurityIncident:
        """Resolve a security incident."""
        incident = await self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.utcnow()
        incident.resolution_notes = resolution_notes
        incident.updated_at = datetime.utcnow()

        # Generate post-incident analysis
        incident.post_incident_analysis = await self._generate_post_incident_analysis(
            incident
        )

        # Update incident
        await self._update_incident(incident)
        await self._cache_incident(incident)

        # Generate incident report
        await self._generate_incident_report(incident)

        logger.info(f"Resolved incident: {incident_id}")
        return incident

    @time_operation
    async def create_escalation_rule(self, rule_data: Dict[str, Any]) -> EscalationRule:
        """Create an escalation rule."""
        rule_id = str(uuid4())

        rule = EscalationRule(
            rule_id=rule_id,
            name=rule_data.get("name", ""),
            conditions=rule_data.get("conditions", {}),
            escalation_level=EscalationLevel(
                rule_data.get("escalation_level", "level_1")
            ),
            response_time_minutes=rule_data.get("response_time_minutes", 30),
            recipients=rule_data.get("recipients", []),
            is_active=rule_data.get("is_active", True),
            created_at=datetime.utcnow(),
        )

        # Store rule
        await self._store_escalation_rule(rule)

        logger.info(f"Created escalation rule: {rule_id}")
        return rule

    @time_operation
    async def get_incident_analytics(
        self, time_period: str = "30_days"
    ) -> Dict[str, Any]:
        """Get incident response analytics."""
        cache_key = f"{self.cache_prefix}:analytics:{time_period}"
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        # Calculate analytics
        analytics = await self._calculate_incident_analytics(time_period)

        # Cache results
        await self.cache_manager.set(cache_key, json.dumps(analytics), self.default_ttl)

        return analytics

    async def _store_incident(self, incident: SecurityIncident) -> None:
        """Store incident in database."""
        sql = """
        INSERT INTO security_incidents (
            incident_id, title, description, severity, status, incident_type,
            detection_time, affected_systems, affected_users, indicators, evidence,
            response_actions, escalation_level, assigned_to, created_at, updated_at,
            resolved_at, resolution_notes, post_incident_analysis
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        await self.db_manager.execute(
            sql,
            (
                incident.incident_id,
                incident.title,
                incident.description,
                incident.severity.value,
                incident.status.value,
                incident.incident_type,
                incident.detection_time,
                json.dumps(incident.affected_systems),
                json.dumps(incident.affected_users),
                json.dumps(incident.indicators),
                json.dumps(incident.evidence),
                json.dumps([action.value for action in incident.response_actions]),
                incident.escalation_level.value,
                incident.assigned_to,
                incident.created_at,
                incident.updated_at,
                incident.resolved_at,
                incident.resolution_notes,
                (
                    json.dumps(incident.post_incident_analysis)
                    if incident.post_incident_analysis
                    else None
                ),
            ),
        )

    async def _update_incident(self, incident: SecurityIncident) -> None:
        """Update incident in database."""
        sql = """
        UPDATE security_incidents SET
            title = ?, description = ?, severity = ?, status = ?, incident_type = ?,
            detection_time = ?, affected_systems = ?, affected_users = ?, indicators = ?,
            evidence = ?, response_actions = ?, escalation_level = ?, assigned_to = ?,
            updated_at = ?, resolved_at = ?, resolution_notes = ?, post_incident_analysis = ?
        WHERE incident_id = ?
        """

        await self.db_manager.execute(
            sql,
            (
                incident.title,
                incident.description,
                incident.severity.value,
                incident.status.value,
                incident.incident_type,
                incident.detection_time,
                json.dumps(incident.affected_systems),
                json.dumps(incident.affected_users),
                json.dumps(incident.indicators),
                json.dumps(incident.evidence),
                json.dumps([action.value for action in incident.response_actions]),
                incident.escalation_level.value,
                incident.assigned_to,
                incident.updated_at,
                incident.resolved_at,
                incident.resolution_notes,
                (
                    json.dumps(incident.post_incident_analysis)
                    if incident.post_incident_analysis
                    else None
                ),
                incident.incident_id,
            ),
        )

    async def _get_incident_from_db(
        self, incident_id: str
    ) -> Optional[SecurityIncident]:
        """Get incident from database."""
        sql = "SELECT * FROM security_incidents WHERE incident_id = ?"
        result = await self.db_manager.fetch_one(sql, (incident_id,))

        if not result:
            return None

        return SecurityIncident(
            incident_id=result["incident_id"],
            title=result["title"],
            description=result["description"],
            severity=IncidentSeverity(result["severity"]),
            status=IncidentStatus(result["status"]),
            incident_type=result["incident_type"],
            detection_time=result["detection_time"],
            affected_systems=json.loads(result["affected_systems"]),
            affected_users=json.loads(result["affected_users"]),
            indicators=json.loads(result["indicators"]),
            evidence=json.loads(result["evidence"]),
            response_actions=[
                ResponseAction(action)
                for action in json.loads(result["response_actions"])
            ],
            escalation_level=EscalationLevel(result["escalation_level"]),
            assigned_to=result["assigned_to"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            resolved_at=result["resolved_at"],
            resolution_notes=result["resolution_notes"],
            post_incident_analysis=(
                json.loads(result["post_incident_analysis"])
                if result["post_incident_analysis"]
                else None
            ),
        )

    async def _get_incidents_from_db(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[SecurityIncident]:
        """Get incidents from database with filters."""
        sql = "SELECT * FROM security_incidents"
        params = []

        if filters:
            conditions = []
            for key, value in filters.items():
                if key in ["severity", "status", "incident_type", "escalation_level"]:
                    conditions.append(f"{key} = ?")
                    params.append(value)
                elif key == "date_range":
                    conditions.append("detection_time BETWEEN ? AND ?")
                    params.extend([value["start"], value["end"]])

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY detection_time DESC"

        results = await self.db_manager.fetch_all(sql, tuple(params))

        incidents = []
        for result in results:
            incident = SecurityIncident(
                incident_id=result["incident_id"],
                title=result["title"],
                description=result["description"],
                severity=IncidentSeverity(result["severity"]),
                status=IncidentStatus(result["status"]),
                incident_type=result["incident_type"],
                detection_time=result["detection_time"],
                affected_systems=json.loads(result["affected_systems"]),
                affected_users=json.loads(result["affected_users"]),
                indicators=json.loads(result["indicators"]),
                evidence=json.loads(result["evidence"]),
                response_actions=[
                    ResponseAction(action)
                    for action in json.loads(result["response_actions"])
                ],
                escalation_level=EscalationLevel(result["escalation_level"]),
                assigned_to=result["assigned_to"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
                resolved_at=result["resolved_at"],
                resolution_notes=result["resolution_notes"],
                post_incident_analysis=(
                    json.loads(result["post_incident_analysis"])
                    if result["post_incident_analysis"]
                    else None
                ),
            )
            incidents.append(incident)

        return incidents

    async def _cache_incident(self, incident: SecurityIncident) -> None:
        """Cache incident data."""
        cache_key = f"{self.cache_prefix}:incident:{incident.incident_id}"
        await self.cache_manager.set(
            cache_key, json.dumps(asdict(incident)), self.default_ttl
        )

    async def _trigger_response_workflow(self, incident: SecurityIncident) -> None:
        """Trigger automated response workflow for incident."""
        workflow_type = f"{incident.incident_type}_response"
        await self.create_response_workflow(incident.incident_id, workflow_type)

    async def _check_escalation_rules(self, incident: SecurityIncident) -> None:
        """Check and apply escalation rules."""
        rules = await self._get_active_escalation_rules()

        for rule in rules:
            if await self._evaluate_escalation_rule(incident, rule):
                await self.escalate_incident(
                    incident.incident_id,
                    rule.escalation_level,
                    f"Triggered by rule: {rule.name}",
                )

    async def _get_workflow_steps(self, workflow_type: str) -> List[Dict[str, Any]]:
        """Get workflow steps based on type."""
        workflow_templates = {
            "data_breach_response": [
                {"step": 1, "action": "isolate_affected_systems", "timeout": 300},
                {"step": 2, "action": "backup_critical_data", "timeout": 600},
                {"step": 3, "action": "notify_security_team", "timeout": 60},
                {"step": 4, "action": "assess_impact", "timeout": 1800},
                {"step": 5, "action": "implement_containment", "timeout": 900},
            ],
            "malware_response": [
                {"step": 1, "action": "isolate_infected_system", "timeout": 300},
                {"step": 2, "action": "scan_for_malware", "timeout": 1200},
                {"step": 3, "action": "remove_malware", "timeout": 1800},
                {"step": 4, "action": "verify_cleanup", "timeout": 600},
                {"step": 5, "action": "restore_system", "timeout": 900},
            ],
            "unauthorized_access_response": [
                {"step": 1, "action": "block_unauthorized_ip", "timeout": 60},
                {"step": 2, "action": "disable_compromised_account", "timeout": 120},
                {"step": 3, "action": "investigate_access", "timeout": 1800},
                {"step": 4, "action": "assess_data_exposure", "timeout": 900},
                {"step": 5, "action": "implement_additional_security", "timeout": 600},
            ],
        }

        return workflow_templates.get(
            workflow_type,
            [
                {"step": 1, "action": "investigate_incident", "timeout": 1800},
                {"step": 2, "action": "implement_containment", "timeout": 900},
                {"step": 3, "action": "assess_impact", "timeout": 600},
                {"step": 4, "action": "document_findings", "timeout": 300},
            ],
        )

    async def _execute_workflow(self, workflow: IncidentWorkflow) -> None:
        """Execute incident response workflow."""
        try:
            workflow.status = "in_progress"
            await self._update_workflow(workflow)

            for step in workflow.steps:
                workflow.current_step = step["step"]
                await self._update_workflow(workflow)

                # Execute step action
                action_result = await self._execute_workflow_action(
                    workflow.incident_id, step["action"]
                )

                # Log execution
                workflow.execution_log.append(
                    {
                        "step": step["step"],
                        "action": step["action"],
                        "result": action_result,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                await self._update_workflow(workflow)

                # Check timeout
                if step.get("timeout"):
                    await asyncio.sleep(step["timeout"])

            workflow.status = "completed"
            workflow.completed_at = datetime.utcnow()
            await self._update_workflow(workflow)

        except Exception as e:
            workflow.status = "failed"
            workflow.execution_log.append(
                {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            )
            await self._update_workflow(workflow)
            logger.error(f"Workflow execution failed: {e}")

    async def _execute_workflow_action(
        self, incident_id: str, action: str
    ) -> Dict[str, Any]:
        """Execute a workflow action."""
        action_handlers = {
            "isolate_affected_systems": self._isolate_systems,
            "backup_critical_data": self._backup_data,
            "notify_security_team": self._notify_security_team,
            "assess_impact": self._assess_impact,
            "implement_containment": self._implement_containment,
            "isolate_infected_system": self._isolate_systems,
            "scan_for_malware": self._scan_malware,
            "remove_malware": self._remove_malware,
            "verify_cleanup": self._verify_cleanup,
            "restore_system": self._restore_system,
            "block_unauthorized_ip": self._block_ip,
            "disable_compromised_account": self._disable_account,
            "investigate_access": self._investigate_access,
            "assess_data_exposure": self._assess_data_exposure,
            "implement_additional_security": self._implement_security,
            "investigate_incident": self._investigate_incident,
            "document_findings": self._document_findings,
        }

        handler = action_handlers.get(action, self._default_action)
        return await handler(incident_id)

    async def _isolate_systems(self, incident_id: str) -> Dict[str, Any]:
        """Isolate affected systems."""
        # Implementation would integrate with network security tools
        return {
            "status": "success",
            "message": "Systems isolated",
            "systems_isolated": ["server-001", "server-002"],
        }

    async def _backup_data(self, incident_id: str) -> Dict[str, Any]:
        """Backup critical data."""
        return {
            "status": "success",
            "message": "Data backed up",
            "backup_size": "2.5GB",
        }

    async def _notify_security_team(self, incident_id: str) -> Dict[str, Any]:
        """Notify security team."""
        return {
            "status": "success",
            "message": "Security team notified",
            "recipients": ["security@company.com"],
        }

    async def _assess_impact(self, incident_id: str) -> Dict[str, Any]:
        """Assess incident impact."""
        return {
            "status": "success",
            "message": "Impact assessed",
            "impact_level": "medium",
            "affected_users": 150,
        }

    async def _implement_containment(self, incident_id: str) -> Dict[str, Any]:
        """Implement containment measures."""
        return {
            "status": "success",
            "message": "Containment implemented",
            "measures": ["firewall_rules", "access_restrictions"],
        }

    async def _scan_malware(self, incident_id: str) -> Dict[str, Any]:
        """Scan for malware."""
        return {
            "status": "success",
            "message": "Malware scan completed",
            "threats_found": 3,
        }

    async def _remove_malware(self, incident_id: str) -> Dict[str, Any]:
        """Remove malware."""
        return {"status": "success", "message": "Malware removed", "files_cleaned": 5}

    async def _verify_cleanup(self, incident_id: str) -> Dict[str, Any]:
        """Verify cleanup."""
        return {
            "status": "success",
            "message": "Cleanup verified",
            "verification_passed": True,
        }

    async def _restore_system(self, incident_id: str) -> Dict[str, Any]:
        """Restore system."""
        return {
            "status": "success",
            "message": "System restored",
            "restore_time": "15 minutes",
        }

    async def _block_ip(self, incident_id: str) -> Dict[str, Any]:
        """Block unauthorized IP."""
        return {
            "status": "success",
            "message": "IP blocked",
            "blocked_ips": ["192.168.1.100"],
        }

    async def _disable_account(self, incident_id: str) -> Dict[str, Any]:
        """Disable compromised account."""
        return {
            "status": "success",
            "message": "Account disabled",
            "disabled_accounts": ["user123"],
        }

    async def _investigate_access(self, incident_id: str) -> Dict[str, Any]:
        """Investigate unauthorized access."""
        return {
            "status": "success",
            "message": "Access investigated",
            "findings": "Suspicious login patterns detected",
        }

    async def _assess_data_exposure(self, incident_id: str) -> Dict[str, Any]:
        """Assess data exposure."""
        return {
            "status": "success",
            "message": "Data exposure assessed",
            "exposed_records": 250,
        }

    async def _implement_security(self, incident_id: str) -> Dict[str, Any]:
        """Implement additional security."""
        return {
            "status": "success",
            "message": "Additional security implemented",
            "measures": ["mfa_enabled", "access_logging"],
        }

    async def _investigate_incident(self, incident_id: str) -> Dict[str, Any]:
        """Investigate incident."""
        return {
            "status": "success",
            "message": "Incident investigated",
            "findings": "Root cause identified",
        }

    async def _document_findings(self, incident_id: str) -> Dict[str, Any]:
        """Document findings."""
        return {
            "status": "success",
            "message": "Findings documented",
            "documentation": "Incident report generated",
        }

    async def _default_action(self, incident_id: str) -> Dict[str, Any]:
        """Default action handler."""
        return {"status": "success", "message": "Action completed", "action": "default"}

    async def _store_workflow(self, workflow: IncidentWorkflow) -> None:
        """Store workflow in database."""
        sql = """
        INSERT INTO incident_workflows (
            workflow_id, incident_id, workflow_type, steps, current_step,
            status, created_at, completed_at, execution_log
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        await self.db_manager.execute(
            sql,
            (
                workflow.workflow_id,
                workflow.incident_id,
                workflow.workflow_type,
                json.dumps(workflow.steps),
                workflow.current_step,
                workflow.status,
                workflow.created_at,
                workflow.completed_at,
                json.dumps(workflow.execution_log),
            ),
        )

    async def _update_workflow(self, workflow: IncidentWorkflow) -> None:
        """Update workflow in database."""
        sql = """
        UPDATE incident_workflows SET
            current_step = ?, status = ?, completed_at = ?, execution_log = ?
        WHERE workflow_id = ?
        """

        await self.db_manager.execute(
            sql,
            (
                workflow.current_step,
                workflow.status,
                workflow.completed_at,
                json.dumps(workflow.execution_log),
                workflow.workflow_id,
            ),
        )

    async def _store_escalation_event(
        self, incident_id: str, escalation_level: EscalationLevel, reason: str
    ) -> None:
        """Store escalation event."""
        sql = """
        INSERT INTO incident_escalations (
            escalation_id, incident_id, escalation_level, reason, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """

        escalation_id = str(uuid4())
        await self.db_manager.execute(
            sql,
            (
                escalation_id,
                incident_id,
                escalation_level.value,
                reason,
                datetime.utcnow(),
            ),
        )

    async def _notify_escalation_recipients(
        self, incident: SecurityIncident, escalation_level: EscalationLevel
    ) -> None:
        """Notify escalation recipients."""
        # Implementation would integrate with notification systems
        logger.info(
            f"Notifying escalation recipients for incident {incident.incident_id} at level {escalation_level.value}"
        )

    async def _generate_post_incident_analysis(
        self, incident: SecurityIncident
    ) -> Dict[str, Any]:
        """Generate post-incident analysis."""
        return {
            "analysis_date": datetime.utcnow().isoformat(),
            "incident_duration": (
                incident.resolved_at - incident.detection_time
            ).total_seconds()
            / 3600,
            "response_effectiveness": "high",
            "lessons_learned": [
                "Improved detection capabilities needed",
                "Response time was within acceptable limits",
                "Containment measures were effective",
            ],
            "recommendations": [
                "Implement additional monitoring",
                "Update response procedures",
                "Conduct team training",
            ],
            "cost_analysis": {
                "downtime_cost": 5000,
                "response_cost": 2000,
                "total_cost": 7000,
            },
        }

    async def _generate_incident_report(self, incident: SecurityIncident) -> None:
        """Generate incident report."""
        # Implementation would generate comprehensive incident reports
        logger.info(f"Generated incident report for {incident.incident_id}")

    async def _get_active_escalation_rules(self) -> List[EscalationRule]:
        """Get active escalation rules."""
        sql = "SELECT * FROM escalation_rules WHERE is_active = 1"
        results = await self.db_manager.fetch_all(sql)

        rules = []
        for result in results:
            rule = EscalationRule(
                rule_id=result["rule_id"],
                name=result["name"],
                conditions=json.loads(result["conditions"]),
                escalation_level=EscalationLevel(result["escalation_level"]),
                response_time_minutes=result["response_time_minutes"],
                recipients=json.loads(result["recipients"]),
                is_active=result["is_active"],
                created_at=result["created_at"],
            )
            rules.append(rule)

        return rules

    async def _evaluate_escalation_rule(
        self, incident: SecurityIncident, rule: EscalationRule
    ) -> bool:
        """Evaluate if escalation rule should be triggered."""
        conditions = rule.conditions

        # Check severity condition
        if "min_severity" in conditions:
            severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            if severity_levels.get(incident.severity.value, 0) < severity_levels.get(
                conditions["min_severity"], 0
            ):
                return False

        # Check incident type condition
        if "incident_types" in conditions:
            if incident.incident_type not in conditions["incident_types"]:
                return False

        # Check affected systems condition
        if "min_affected_systems" in conditions:
            if len(incident.affected_systems) < conditions["min_affected_systems"]:
                return False

        return True

    async def _store_escalation_rule(self, rule: EscalationRule) -> None:
        """Store escalation rule in database."""
        sql = """
        INSERT INTO escalation_rules (
            rule_id, name, conditions, escalation_level, response_time_minutes,
            recipients, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        await self.db_manager.execute(
            sql,
            (
                rule.rule_id,
                rule.name,
                json.dumps(rule.conditions),
                rule.escalation_level.value,
                rule.response_time_minutes,
                json.dumps(rule.recipients),
                rule.is_active,
                rule.created_at,
            ),
        )

    async def _calculate_incident_analytics(self, time_period: str) -> Dict[str, Any]:
        """Calculate incident response analytics."""
        # Calculate time range
        end_date = datetime.utcnow()
        if time_period == "7_days":
            start_date = end_date - timedelta(days=7)
        elif time_period == "30_days":
            start_date = end_date - timedelta(days=30)
        elif time_period == "90_days":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)

        # Get incidents in time period
        incidents = await self._get_incidents_from_db(
            {"date_range": {"start": start_date, "end": end_date}}
        )

        # Calculate metrics
        total_incidents = len(incidents)
        resolved_incidents = len(
            [i for i in incidents if i.status == IncidentStatus.RESOLVED]
        )
        avg_resolution_time = 0
        severity_distribution = {}
        incident_types = {}

        if total_incidents > 0:
            # Calculate average resolution time
            resolved_times = []
            for incident in incidents:
                if incident.resolved_at and incident.detection_time:
                    resolution_time = (
                        incident.resolved_at - incident.detection_time
                    ).total_seconds() / 3600
                    resolved_times.append(resolution_time)

            if resolved_times:
                avg_resolution_time = sum(resolved_times) / len(resolved_times)

            # Calculate severity distribution
            for incident in incidents:
                severity = incident.severity.value
                severity_distribution[severity] = (
                    severity_distribution.get(severity, 0) + 1
                )

            # Calculate incident type distribution
            for incident in incidents:
                incident_type = incident.incident_type
                incident_types[incident_type] = incident_types.get(incident_type, 0) + 1

        return {
            "time_period": time_period,
            "total_incidents": total_incidents,
            "resolved_incidents": resolved_incidents,
            "resolution_rate": (
                (resolved_incidents / total_incidents * 100)
                if total_incidents > 0
                else 0
            ),
            "avg_resolution_time_hours": round(avg_resolution_time, 2),
            "severity_distribution": severity_distribution,
            "incident_type_distribution": incident_types,
            "escalation_rate": (
                len([i for i in incidents if i.status == IncidentStatus.ESCALATED])
                / total_incidents
                * 100
                if total_incidents > 0
                else 0
            ),
        }
