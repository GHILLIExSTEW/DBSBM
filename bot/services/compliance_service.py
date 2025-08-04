"""
Compliance Service for DBSBM System.
Provides regulatory compliance and governance capabilities.
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
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

# Compliance-specific cache TTLs
COMPLIANCE_CACHE_TTLS = {
    "compliance_rules": 3600,  # 1 hour
    "compliance_checks": 1800,  # 30 minutes
    "compliance_reports": 7200,  # 2 hours
    "compliance_alerts": 300,  # 5 minutes
    "compliance_audits": 3600,  # 1 hour
    "compliance_policies": 7200,  # 2 hours
    "compliance_monitoring": 300,  # 5 minutes
    "compliance_analytics": 1800,  # 30 minutes
    "compliance_exports": 600,  # 10 minutes
    "compliance_performance": 1800,  # 30 minutes
}


class ComplianceType(Enum):
    """Compliance types."""

    GDPR = "gdpr"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    SOX = "sox"
    CUSTOM = "custom"


class ComplianceStatus(Enum):
    """Compliance status."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    REVIEW = "review"


class ComplianceSeverity(Enum):
    """Compliance severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceRule:
    """Compliance rule configuration."""

    id: int
    tenant_id: int
    name: str
    compliance_type: ComplianceType
    rule_type: str
    conditions: Dict[str, Any]
    actions: List[str]
    severity: ComplianceSeverity
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class ComplianceCheck:
    """Compliance check result."""

    id: int
    tenant_id: int
    rule_id: int
    check_type: str
    status: ComplianceStatus
    details: Dict[str, Any]
    severity: ComplianceSeverity
    created_at: datetime


@dataclass
class ComplianceReport:
    """Compliance report configuration."""

    id: int
    tenant_id: int
    name: str
    report_type: str
    parameters: Dict[str, Any]
    schedule: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class ComplianceAlert:
    """Compliance alert configuration."""

    id: int
    tenant_id: int
    name: str
    alert_type: str
    conditions: Dict[str, Any]
    actions: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ComplianceService:
    """Compliance service for regulatory compliance and governance."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = COMPLIANCE_CACHE_TTLS

        # Background tasks
        self.monitoring_task = None
        self.reporting_task = None
        self.is_running = False

    async def start(self):
        """Start the compliance service."""
        try:
            self.is_running = True
            self.monitoring_task = asyncio.create_task(self._monitor_compliance())
            self.reporting_task = asyncio.create_task(self._generate_reports())
            logger.info("Compliance service started successfully")
        except Exception as e:
            logger.error(f"Failed to start compliance service: {e}")
            raise

    async def stop(self):
        """Stop the compliance service."""
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.reporting_task:
            self.reporting_task.cancel()
        logger.info("Compliance service stopped")

    @time_operation("compliance_create_rule")
    async def create_compliance_rule(
        self,
        tenant_id: int,
        name: str,
        compliance_type: ComplianceType,
        rule_type: str,
        conditions: Dict[str, Any],
        actions: List[str],
        severity: ComplianceSeverity,
    ) -> Optional[ComplianceRule]:
        """Create a new compliance rule."""
        try:
            query = """
            INSERT INTO compliance_rules (tenant_id, name, compliance_type, rule_type,
                                        conditions, actions, severity, is_active, created_at, updated_at)
            VALUES (:tenant_id, :name, :compliance_type, :rule_type,
                    :conditions, :actions, :severity, 1, NOW(), NOW())
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": tenant_id,
                    "name": name,
                    "compliance_type": compliance_type.value,
                    "rule_type": rule_type,
                    "conditions": json.dumps(conditions),
                    "actions": json.dumps(actions),
                    "severity": severity.value,
                },
            )

            rule_id = result.lastrowid

            # Get created rule
            rule = await self.get_compliance_rule_by_id(rule_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(
                f"compliance_rules:{tenant_id}:*"
            )

            record_metric("compliance_rules_created", 1)
            return rule

        except Exception as e:
            logger.error(f"Failed to create compliance rule: {e}")
            return None

    @time_operation("compliance_get_rule")
    async def get_compliance_rule_by_id(self, rule_id: int) -> Optional[ComplianceRule]:
        """Get compliance rule by ID."""
        try:
            # Try to get from cache first
            cache_key = f"compliance_rule:{rule_id}"
            cached_rule = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_rule:
                return ComplianceRule(**cached_rule)

            # Get from database
            query = """
            SELECT * FROM compliance_rules WHERE id = :rule_id
            """

            result = await self.db_manager.fetch_one(query, {"rule_id": rule_id})

            if not result:
                return None

            rule = ComplianceRule(
                id=result["id"],
                tenant_id=result["tenant_id"],
                name=result["name"],
                compliance_type=ComplianceType(result["compliance_type"]),
                rule_type=result["rule_type"],
                conditions=(
                    json.loads(result["conditions"]) if result["conditions"] else {}
                ),
                actions=json.loads(result["actions"]) if result["actions"] else [],
                severity=ComplianceSeverity(result["severity"]),
                is_active=result["is_active"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )

            # Cache rule
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": rule.id,
                    "tenant_id": rule.tenant_id,
                    "name": rule.name,
                    "compliance_type": rule.compliance_type.value,
                    "rule_type": rule.rule_type,
                    "conditions": rule.conditions,
                    "actions": rule.actions,
                    "severity": rule.severity.value,
                    "is_active": rule.is_active,
                    "created_at": rule.created_at.isoformat(),
                    "updated_at": rule.updated_at.isoformat(),
                },
                ttl=self.cache_ttls["compliance_rules"],
            )

            return rule

        except Exception as e:
            logger.error(f"Failed to get compliance rule: {e}")
            return None

    @time_operation("compliance_get_rules")
    async def get_compliance_rules_by_tenant(
        self, tenant_id: int, compliance_type: Optional[ComplianceType] = None
    ) -> List[ComplianceRule]:
        """Get compliance rules for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"compliance_rules:{tenant_id}:{compliance_type.value if compliance_type else 'all'}"
            cached_rules = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_rules:
                return [ComplianceRule(**rule) for rule in cached_rules]

            # Build query
            query = "SELECT * FROM compliance_rules WHERE tenant_id = :tenant_id"
            params = {"tenant_id": tenant_id}

            if compliance_type:
                query += " AND compliance_type = :compliance_type"
                params["compliance_type"] = compliance_type.value

            results = await self.db_manager.fetch_all(query, params)

            rules = []
            for row in results:
                rule = ComplianceRule(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    name=row["name"],
                    compliance_type=ComplianceType(row["compliance_type"]),
                    rule_type=row["rule_type"],
                    conditions=(
                        json.loads(row["conditions"]) if row["conditions"] else {}
                    ),
                    actions=json.loads(row["actions"]) if row["actions"] else [],
                    severity=ComplianceSeverity(row["severity"]),
                    is_active=row["is_active"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                rules.append(rule)

            # Cache rules
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [
                    {
                        "id": r.id,
                        "tenant_id": r.tenant_id,
                        "name": r.name,
                        "compliance_type": r.compliance_type.value,
                        "rule_type": r.rule_type,
                        "conditions": r.conditions,
                        "actions": r.actions,
                        "severity": r.severity.value,
                        "is_active": r.is_active,
                        "created_at": r.created_at.isoformat(),
                        "updated_at": r.updated_at.isoformat(),
                    }
                    for r in rules
                ],
                ttl=self.cache_ttls["compliance_rules"],
            )

            return rules

        except Exception as e:
            logger.error(f"Failed to get compliance rules: {e}")
            return []

    @time_operation("compliance_run_check")
    async def run_compliance_check(
        self, tenant_id: int, rule_id: int, check_type: str, data: Dict[str, Any]
    ) -> Optional[ComplianceCheck]:
        """Run a compliance check."""
        try:
            # Get rule
            rule = await self.get_compliance_rule_by_id(rule_id)
            if not rule:
                return None

            # Run check
            check_result = await self._execute_compliance_check(rule, data)

            # Create check record
            query = """
            INSERT INTO compliance_checks (tenant_id, rule_id, check_type, status,
                                         details, severity, created_at)
            VALUES (:tenant_id, :rule_id, :check_type, :status,
                    :details, :severity, NOW())
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": tenant_id,
                    "rule_id": rule_id,
                    "check_type": check_type,
                    "status": check_result["status"].value,
                    "details": json.dumps(check_result["details"]),
                    "severity": check_result["severity"].value,
                },
            )

            check_id = result.lastrowid

            check = ComplianceCheck(
                id=check_id,
                tenant_id=tenant_id,
                rule_id=rule_id,
                check_type=check_type,
                status=check_result["status"],
                details=check_result["details"],
                severity=check_result["severity"],
                created_at=datetime.utcnow(),
            )

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(
                f"compliance_checks:{tenant_id}:*"
            )

            record_metric("compliance_checks_run", 1)
            return check

        except Exception as e:
            logger.error(f"Failed to run compliance check: {e}")
            return None

    @time_operation("compliance_create_report")
    async def create_compliance_report(
        self,
        tenant_id: int,
        name: str,
        report_type: str,
        parameters: Dict[str, Any],
        schedule: Optional[str] = None,
    ) -> Optional[ComplianceReport]:
        """Create a new compliance report."""
        try:
            query = """
            INSERT INTO compliance_reports (tenant_id, name, report_type, parameters, schedule,
                                           is_active, created_at, updated_at)
            VALUES (:tenant_id, :name, :report_type, :parameters, :schedule,
                    1, NOW(), NOW())
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": tenant_id,
                    "name": name,
                    "report_type": report_type,
                    "parameters": json.dumps(parameters),
                    "schedule": schedule,
                },
            )

            report_id = result.lastrowid

            # Get created report
            report = await self.get_compliance_report_by_id(report_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(
                f"compliance_reports:{tenant_id}:*"
            )

            record_metric("compliance_reports_created", 1)
            return report

        except Exception as e:
            logger.error(f"Failed to create compliance report: {e}")
            return None

    @time_operation("compliance_get_report")
    async def get_compliance_report_by_id(
        self, report_id: int
    ) -> Optional[ComplianceReport]:
        """Get compliance report by ID."""
        try:
            # Try to get from cache first
            cache_key = f"compliance_report:{report_id}"
            cached_report = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_report:
                return ComplianceReport(**cached_report)

            # Get from database
            query = """
            SELECT * FROM compliance_reports WHERE id = :report_id
            """

            result = await self.db_manager.fetch_one(query, {"report_id": report_id})

            if not result:
                return None

            report = ComplianceReport(
                id=result["id"],
                tenant_id=result["tenant_id"],
                name=result["name"],
                report_type=result["report_type"],
                parameters=(
                    json.loads(result["parameters"]) if result["parameters"] else {}
                ),
                schedule=result["schedule"],
                is_active=result["is_active"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )

            # Cache report
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": report.id,
                    "tenant_id": report.tenant_id,
                    "name": report.name,
                    "report_type": report.report_type,
                    "parameters": report.parameters,
                    "schedule": report.schedule,
                    "is_active": report.is_active,
                    "created_at": report.created_at.isoformat(),
                    "updated_at": report.updated_at.isoformat(),
                },
                ttl=self.cache_ttls["compliance_reports"],
            )

            return report

        except Exception as e:
            logger.error(f"Failed to get compliance report: {e}")
            return None

    @time_operation("compliance_generate_report")
    async def generate_compliance_report(
        self, report_id: int, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate a compliance report."""
        try:
            # Get report configuration
            report = await self.get_compliance_report_by_id(report_id)
            if not report:
                return None

            # Try to get from cache first
            cache_key = f"compliance_report_data:{report_id}:{hashlib.md5(str(parameters).encode()).hexdigest()}"
            cached_data = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_data:
                return cached_data

            # Generate report data based on type
            report_data = await self._generate_compliance_report_data(
                report, parameters or {}
            )

            # Cache report data
            await self.cache_manager.enhanced_cache_set(
                cache_key, report_data, ttl=self.cache_ttls["compliance_reports"]
            )

            record_metric("compliance_reports_generated", 1)
            return report_data

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return None

    @time_operation("compliance_create_alert")
    async def create_compliance_alert(
        self,
        tenant_id: int,
        name: str,
        alert_type: str,
        conditions: Dict[str, Any],
        actions: List[str],
    ) -> Optional[ComplianceAlert]:
        """Create a new compliance alert."""
        try:
            query = """
            INSERT INTO compliance_alerts (tenant_id, name, alert_type, conditions, actions,
                                         is_active, created_at, updated_at)
            VALUES (:tenant_id, :name, :alert_type, :conditions, :actions,
                    1, NOW(), NOW())
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": tenant_id,
                    "name": name,
                    "alert_type": alert_type,
                    "conditions": json.dumps(conditions),
                    "actions": json.dumps(actions),
                },
            )

            alert_id = result.lastrowid

            # Get created alert
            alert = await self.get_compliance_alert_by_id(alert_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(
                f"compliance_alerts:{tenant_id}:*"
            )

            record_metric("compliance_alerts_created", 1)
            return alert

        except Exception as e:
            logger.error(f"Failed to create compliance alert: {e}")
            return None

    @time_operation("compliance_get_alert")
    async def get_compliance_alert_by_id(
        self, alert_id: int
    ) -> Optional[ComplianceAlert]:
        """Get compliance alert by ID."""
        try:
            # Try to get from cache first
            cache_key = f"compliance_alert:{alert_id}"
            cached_alert = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_alert:
                return ComplianceAlert(**cached_alert)

            # Get from database
            query = """
            SELECT * FROM compliance_alerts WHERE id = :alert_id
            """

            result = await self.db_manager.fetch_one(query, {"alert_id": alert_id})

            if not result:
                return None

            alert = ComplianceAlert(
                id=result["id"],
                tenant_id=result["tenant_id"],
                name=result["name"],
                alert_type=result["alert_type"],
                conditions=(
                    json.loads(result["conditions"]) if result["conditions"] else {}
                ),
                actions=json.loads(result["actions"]) if result["actions"] else [],
                is_active=result["is_active"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )

            # Cache alert
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": alert.id,
                    "tenant_id": alert.tenant_id,
                    "name": alert.name,
                    "alert_type": alert.alert_type,
                    "conditions": alert.conditions,
                    "actions": alert.actions,
                    "is_active": alert.is_active,
                    "created_at": alert.created_at.isoformat(),
                    "updated_at": alert.updated_at.isoformat(),
                },
                ttl=self.cache_ttls["compliance_alerts"],
            )

            return alert

        except Exception as e:
            logger.error(f"Failed to get compliance alert: {e}")
            return None

    @time_operation("compliance_get_analytics")
    async def get_compliance_analytics(
        self, tenant_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Get compliance analytics for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"compliance_analytics:{tenant_id}:{days}"
            cached_analytics = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_analytics:
                return cached_analytics

            # Get rule statistics
            rule_query = """
            SELECT
                compliance_type,
                severity,
                COUNT(*) as count
            FROM compliance_rules
            WHERE tenant_id = :tenant_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY compliance_type, severity
            """

            rule_results = await self.db_manager.fetch_all(
                rule_query, {"tenant_id": tenant_id, "days": days}
            )

            # Get check statistics
            check_query = """
            SELECT
                status,
                severity,
                COUNT(*) as count
            FROM compliance_checks
            WHERE tenant_id = :tenant_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY status, severity
            """

            check_results = await self.db_manager.fetch_all(
                check_query, {"tenant_id": tenant_id, "days": days}
            )

            analytics = {
                "rule_statistics": {
                    "by_type": {
                        row["compliance_type"]: row["count"] for row in rule_results
                    },
                    "by_severity": {
                        row["severity"]: row["count"] for row in rule_results
                    },
                    "total_rules": sum(row["count"] for row in rule_results),
                },
                "check_statistics": {
                    "by_status": {row["status"]: row["count"] for row in check_results},
                    "by_severity": {
                        row["severity"]: row["count"] for row in check_results
                    },
                    "total_checks": sum(row["count"] for row in check_results),
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
                cache_key, analytics, ttl=self.cache_ttls["compliance_analytics"]
            )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get compliance analytics: {e}")
            return {}

    async def clear_compliance_cache(self):
        """Clear all compliance-related cache entries."""
        try:
            await self.cache_manager.clear_cache_by_pattern("compliance_rules:*")
            await self.cache_manager.clear_cache_by_pattern("compliance_checks:*")
            await self.cache_manager.clear_cache_by_pattern("compliance_reports:*")
            await self.cache_manager.clear_cache_by_pattern("compliance_alerts:*")
            await self.cache_manager.clear_cache_by_pattern("compliance_audits:*")
            await self.cache_manager.clear_cache_by_pattern("compliance_policies:*")
            await self.cache_manager.clear_cache_by_pattern("compliance_monitoring:*")
            await self.cache_manager.clear_cache_by_pattern("compliance_analytics:*")
            await self.cache_manager.clear_cache_by_pattern("compliance_exports:*")
            await self.cache_manager.clear_cache_by_pattern("compliance_performance:*")
            logger.info("Compliance cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear compliance cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get compliance service cache statistics."""
        try:
            return await self.cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
