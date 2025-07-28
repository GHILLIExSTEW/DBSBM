"""
Audit Service for DBSBM System.
Provides comprehensive audit logging and compliance tracking.
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

# Audit-specific cache TTLs
AUDIT_CACHE_TTLS = {
    'audit_logs': 1800,             # 30 minutes
    'audit_events': 900,             # 15 minutes
    'audit_reports': 3600,           # 1 hour
    'audit_alerts': 300,             # 5 minutes
    'audit_compliance': 7200,        # 2 hours
    'audit_retention': 3600,         # 1 hour
    'audit_analytics': 1800,         # 30 minutes
    'audit_exports': 600,            # 10 minutes
    'audit_monitoring': 300,         # 5 minutes
    'audit_performance': 1800,       # 30 minutes
}

class AuditLevel(Enum):
    """Audit log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditCategory(Enum):
    """Audit event categories."""
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    ADMIN_ACTION = "admin_action"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    COMPLIANCE = "compliance"

class AuditStatus(Enum):
    """Audit event status."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"

@dataclass
class AuditLog:
    """Audit log entry."""
    id: int
    tenant_id: int
    user_id: Optional[int]
    event_type: str
    category: AuditCategory
    level: AuditLevel
    message: str
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

@dataclass
class AuditEvent:
    """Audit event configuration."""
    id: int
    tenant_id: int
    event_name: str
    event_type: str
    category: AuditCategory
    is_enabled: bool
    retention_days: int
    created_at: datetime
    updated_at: datetime

@dataclass
class AuditReport:
    """Audit report configuration."""
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
class AuditAlert:
    """Audit alert configuration."""
    id: int
    tenant_id: int
    name: str
    alert_type: str
    conditions: Dict[str, Any]
    actions: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class AuditService:
    """Audit service for comprehensive audit logging and compliance tracking."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = AUDIT_CACHE_TTLS

        # Background tasks
        self.retention_task = None
        self.monitoring_task = None
        self.is_running = False

    async def start(self):
        """Start the audit service."""
        try:
            self.is_running = True
            self.retention_task = asyncio.create_task(self._cleanup_expired_logs())
            self.monitoring_task = asyncio.create_task(self._monitor_audit_events())
            logger.info("Audit service started successfully")
        except Exception as e:
            logger.error(f"Failed to start audit service: {e}")
            raise

    async def stop(self):
        """Stop the audit service."""
        self.is_running = False
        if self.retention_task:
            self.retention_task.cancel()
        if self.monitoring_task:
            self.monitoring_task.cancel()
        logger.info("Audit service stopped")

    @time_operation("audit_log_event")
    async def log_event(self, tenant_id: int, event_type: str, category: AuditCategory,
                       level: AuditLevel, message: str, details: Dict[str, Any],
                       user_id: Optional[int] = None, ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None) -> Optional[AuditLog]:
        """Log an audit event."""
        try:
            query = """
            INSERT INTO audit_logs (tenant_id, user_id, event_type, category, level,
                                   message, details, ip_address, user_agent, created_at)
            VALUES (:tenant_id, :user_id, :event_type, :category, :level,
                    :message, :details, :ip_address, :user_agent, NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'user_id': user_id,
                'event_type': event_type,
                'category': category.value,
                'level': level.value,
                'message': message,
                'details': json.dumps(details),
                'ip_address': ip_address,
                'user_agent': user_agent
            })

            log_id = result.lastrowid

            log = AuditLog(
                id=log_id,
                tenant_id=tenant_id,
                user_id=user_id,
                event_type=event_type,
                category=category,
                level=level,
                message=message,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.utcnow()
            )

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"audit_logs:{tenant_id}:*")
            await self.cache_manager.clear_cache_by_pattern("audit_events:*")

            record_metric("audit_events_logged", 1)
            return log

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return None

    @time_operation("audit_get_logs")
    async def get_audit_logs(self, tenant_id: int, category: Optional[AuditCategory] = None,
                            level: Optional[AuditLevel] = None, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"audit_logs:{tenant_id}:{category.value if category else 'all'}:{level.value if level else 'all'}:{limit}"
            cached_logs = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_logs:
                return [AuditLog(**log) for log in cached_logs]

            # Build query
            query = "SELECT * FROM audit_logs WHERE tenant_id = :tenant_id"
            params = {'tenant_id': tenant_id}

            if category:
                query += " AND category = :category"
                params['category'] = category.value

            if level:
                query += " AND level = :level"
                params['level'] = level.value

            query += " ORDER BY created_at DESC LIMIT :limit"
            params['limit'] = limit

            results = await self.db_manager.fetch_all(query, params)

            logs = []
            for row in results:
                log = AuditLog(
                    id=row['id'],
                    tenant_id=row['tenant_id'],
                    user_id=row['user_id'],
                    event_type=row['event_type'],
                    category=AuditCategory(row['category']),
                    level=AuditLevel(row['level']),
                    message=row['message'],
                    details=json.loads(row['details']) if row['details'] else {},
                    ip_address=row['ip_address'],
                    user_agent=row['user_agent'],
                    created_at=row['created_at']
                )
                logs.append(log)

            # Cache logs
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [{
                    'id': l.id,
                    'tenant_id': l.tenant_id,
                    'user_id': l.user_id,
                    'event_type': l.event_type,
                    'category': l.category.value,
                    'level': l.level.value,
                    'message': l.message,
                    'details': l.details,
                    'ip_address': l.ip_address,
                    'user_agent': l.user_agent,
                    'created_at': l.created_at.isoformat()
                } for l in logs],
                ttl=self.cache_ttls['audit_logs']
            )

            return logs

        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []

    @time_operation("audit_create_event")
    async def create_audit_event(self, tenant_id: int, event_name: str, event_type: str,
                               category: AuditCategory, retention_days: int = 365) -> Optional[AuditEvent]:
        """Create a new audit event configuration."""
        try:
            query = """
            INSERT INTO audit_events (tenant_id, event_name, event_type, category,
                                     is_enabled, retention_days, created_at, updated_at)
            VALUES (:tenant_id, :event_name, :event_type, :category,
                    1, :retention_days, NOW(), NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'event_name': event_name,
                'event_type': event_type,
                'category': category.value,
                'retention_days': retention_days
            })

            event_id = result.lastrowid

            # Get created event
            event = await self.get_audit_event_by_id(event_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"audit_events:{tenant_id}:*")

            record_metric("audit_events_created", 1)
            return event

        except Exception as e:
            logger.error(f"Failed to create audit event: {e}")
            return None

    @time_operation("audit_get_event")
    async def get_audit_event_by_id(self, event_id: int) -> Optional[AuditEvent]:
        """Get audit event by ID."""
        try:
            # Try to get from cache first
            cache_key = f"audit_event:{event_id}"
            cached_event = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_event:
                return AuditEvent(**cached_event)

            # Get from database
            query = """
            SELECT * FROM audit_events WHERE id = :event_id
            """

            result = await self.db_manager.fetch_one(query, {'event_id': event_id})

            if not result:
                return None

            event = AuditEvent(
                id=result['id'],
                tenant_id=result['tenant_id'],
                event_name=result['event_name'],
                event_type=result['event_type'],
                category=AuditCategory(result['category']),
                is_enabled=result['is_enabled'],
                retention_days=result['retention_days'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )

            # Cache event
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': event.id,
                    'tenant_id': event.tenant_id,
                    'event_name': event.event_name,
                    'event_type': event.event_type,
                    'category': event.category.value,
                    'is_enabled': event.is_enabled,
                    'retention_days': event.retention_days,
                    'created_at': event.created_at.isoformat(),
                    'updated_at': event.updated_at.isoformat()
                },
                ttl=self.cache_ttls['audit_events']
            )

            return event

        except Exception as e:
            logger.error(f"Failed to get audit event: {e}")
            return None

    @time_operation("audit_get_events")
    async def get_audit_events_by_tenant(self, tenant_id: int, category: Optional[AuditCategory] = None) -> List[AuditEvent]:
        """Get audit events for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"audit_events:{tenant_id}:{category.value if category else 'all'}"
            cached_events = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_events:
                return [AuditEvent(**event) for event in cached_events]

            # Build query
            query = "SELECT * FROM audit_events WHERE tenant_id = :tenant_id"
            params = {'tenant_id': tenant_id}

            if category:
                query += " AND category = :category"
                params['category'] = category.value

            results = await self.db_manager.fetch_all(query, params)

            events = []
            for row in results:
                event = AuditEvent(
                    id=row['id'],
                    tenant_id=row['tenant_id'],
                    event_name=row['event_name'],
                    event_type=row['event_type'],
                    category=AuditCategory(row['category']),
                    is_enabled=row['is_enabled'],
                    retention_days=row['retention_days'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                events.append(event)

            # Cache events
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [{
                    'id': e.id,
                    'tenant_id': e.tenant_id,
                    'event_name': e.event_name,
                    'event_type': e.event_type,
                    'category': e.category.value,
                    'is_enabled': e.is_enabled,
                    'retention_days': e.retention_days,
                    'created_at': e.created_at.isoformat(),
                    'updated_at': e.updated_at.isoformat()
                } for e in events],
                ttl=self.cache_ttls['audit_events']
            )

            return events

        except Exception as e:
            logger.error(f"Failed to get audit events: {e}")
            return []

    @time_operation("audit_create_report")
    async def create_audit_report(self, tenant_id: int, name: str, report_type: str,
                                parameters: Dict[str, Any], schedule: Optional[str] = None) -> Optional[AuditReport]:
        """Create a new audit report."""
        try:
            query = """
            INSERT INTO audit_reports (tenant_id, name, report_type, parameters, schedule,
                                      is_active, created_at, updated_at)
            VALUES (:tenant_id, :name, :report_type, :parameters, :schedule,
                    1, NOW(), NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'name': name,
                'report_type': report_type,
                'parameters': json.dumps(parameters),
                'schedule': schedule
            })

            report_id = result.lastrowid

            # Get created report
            report = await self.get_audit_report_by_id(report_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"audit_reports:{tenant_id}:*")

            record_metric("audit_reports_created", 1)
            return report

        except Exception as e:
            logger.error(f"Failed to create audit report: {e}")
            return None

    @time_operation("audit_get_report")
    async def get_audit_report_by_id(self, report_id: int) -> Optional[AuditReport]:
        """Get audit report by ID."""
        try:
            # Try to get from cache first
            cache_key = f"audit_report:{report_id}"
            cached_report = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_report:
                return AuditReport(**cached_report)

            # Get from database
            query = """
            SELECT * FROM audit_reports WHERE id = :report_id
            """

            result = await self.db_manager.fetch_one(query, {'report_id': report_id})

            if not result:
                return None

            report = AuditReport(
                id=result['id'],
                tenant_id=result['tenant_id'],
                name=result['name'],
                report_type=result['report_type'],
                parameters=json.loads(result['parameters']) if result['parameters'] else {},
                schedule=result['schedule'],
                is_active=result['is_active'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )

            # Cache report
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': report.id,
                    'tenant_id': report.tenant_id,
                    'name': report.name,
                    'report_type': report.report_type,
                    'parameters': report.parameters,
                    'schedule': report.schedule,
                    'is_active': report.is_active,
                    'created_at': report.created_at.isoformat(),
                    'updated_at': report.updated_at.isoformat()
                },
                ttl=self.cache_ttls['audit_reports']
            )

            return report

        except Exception as e:
            logger.error(f"Failed to get audit report: {e}")
            return None

    @time_operation("audit_generate_report")
    async def generate_audit_report(self, report_id: int, parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Generate an audit report."""
        try:
            # Get report configuration
            report = await self.get_audit_report_by_id(report_id)
            if not report:
                return None

            # Try to get from cache first
            cache_key = f"audit_report_data:{report_id}:{hashlib.md5(str(parameters).encode()).hexdigest()}"
            cached_data = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_data:
                return cached_data

            # Generate report data based on type
            report_data = await self._generate_audit_report_data(report, parameters or {})

            # Cache report data
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                report_data,
                ttl=self.cache_ttls['audit_reports']
            )

            record_metric("audit_reports_generated", 1)
            return report_data

        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}")
            return None

    @time_operation("audit_create_alert")
    async def create_audit_alert(self, tenant_id: int, name: str, alert_type: str,
                               conditions: Dict[str, Any], actions: List[str]) -> Optional[AuditAlert]:
        """Create a new audit alert."""
        try:
            query = """
            INSERT INTO audit_alerts (tenant_id, name, alert_type, conditions, actions,
                                     is_active, created_at, updated_at)
            VALUES (:tenant_id, :name, :alert_type, :conditions, :actions,
                    1, NOW(), NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'name': name,
                'alert_type': alert_type,
                'conditions': json.dumps(conditions),
                'actions': json.dumps(actions)
            })

            alert_id = result.lastrowid

            # Get created alert
            alert = await self.get_audit_alert_by_id(alert_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"audit_alerts:{tenant_id}:*")

            record_metric("audit_alerts_created", 1)
            return alert

        except Exception as e:
            logger.error(f"Failed to create audit alert: {e}")
            return None

    @time_operation("audit_get_alert")
    async def get_audit_alert_by_id(self, alert_id: int) -> Optional[AuditAlert]:
        """Get audit alert by ID."""
        try:
            # Try to get from cache first
            cache_key = f"audit_alert:{alert_id}"
            cached_alert = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_alert:
                return AuditAlert(**cached_alert)

            # Get from database
            query = """
            SELECT * FROM audit_alerts WHERE id = :alert_id
            """

            result = await self.db_manager.fetch_one(query, {'alert_id': alert_id})

            if not result:
                return None

            alert = AuditAlert(
                id=result['id'],
                tenant_id=result['tenant_id'],
                name=result['name'],
                alert_type=result['alert_type'],
                conditions=json.loads(result['conditions']) if result['conditions'] else {},
                actions=json.loads(result['actions']) if result['actions'] else [],
                is_active=result['is_active'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )

            # Cache alert
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': alert.id,
                    'tenant_id': alert.tenant_id,
                    'name': alert.name,
                    'alert_type': alert.alert_type,
                    'conditions': alert.conditions,
                    'actions': alert.actions,
                    'is_active': alert.is_active,
                    'created_at': alert.created_at.isoformat(),
                    'updated_at': alert.updated_at.isoformat()
                },
                ttl=self.cache_ttls['audit_alerts']
            )

            return alert

        except Exception as e:
            logger.error(f"Failed to get audit alert: {e}")
            return None

    @time_operation("audit_get_analytics")
    async def get_audit_analytics(self, tenant_id: int, days: int = 30) -> Dict[str, Any]:
        """Get audit analytics for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"audit_analytics:{tenant_id}:{days}"
            cached_analytics = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_analytics:
                return cached_analytics

            # Get log statistics
            log_query = """
            SELECT
                category,
                level,
                COUNT(*) as count
            FROM audit_logs
            WHERE tenant_id = :tenant_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY category, level
            """

            log_results = await self.db_manager.fetch_all(log_query, {
                'tenant_id': tenant_id,
                'days': days
            })

            # Get event statistics
            event_query = """
            SELECT
                event_type,
                COUNT(*) as count
            FROM audit_logs
            WHERE tenant_id = :tenant_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY event_type
            """

            event_results = await self.db_manager.fetch_all(event_query, {
                'tenant_id': tenant_id,
                'days': days
            })

            analytics = {
                'log_statistics': {
                    'by_category': {row['category']: row['count'] for row in log_results},
                    'by_level': {row['level']: row['count'] for row in log_results},
                    'total_logs': sum(row['count'] for row in log_results)
                },
                'event_statistics': {
                    'by_type': {row['event_type']: row['count'] for row in event_results},
                    'total_events': sum(row['count'] for row in event_results)
                },
                'period': {
                    'days': days,
                    'start_date': (datetime.utcnow() - timedelta(days=days)).isoformat(),
                    'end_date': datetime.utcnow().isoformat()
                }
            }

            # Cache analytics
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                analytics,
                ttl=self.cache_ttls['audit_analytics']
            )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get audit analytics: {e}")
            return {}

    async def clear_audit_cache(self):
        """Clear all audit-related cache entries."""
        try:
            await self.cache_manager.clear_cache_by_pattern("audit_logs:*")
            await self.cache_manager.clear_cache_by_pattern("audit_events:*")
            await self.cache_manager.clear_cache_by_pattern("audit_reports:*")
            await self.cache_manager.clear_cache_by_pattern("audit_alerts:*")
            await self.cache_manager.clear_cache_by_pattern("audit_compliance:*")
            await self.cache_manager.clear_cache_by_pattern("audit_retention:*")
            await self.cache_manager.clear_cache_by_pattern("audit_analytics:*")
            await self.cache_manager.clear_cache_by_pattern("audit_exports:*")
            await self.cache_manager.clear_cache_by_pattern("audit_monitoring:*")
            await self.cache_manager.clear_cache_by_pattern("audit_performance:*")
            logger.info("Audit cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear audit cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get audit service cache statistics."""
        try:
            return await self.cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    # Private helper methods

    async def _cleanup_expired_logs(self):
        """Background task to clean up expired audit logs."""
        while self.is_running:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=365) # Example retention period
                query = "DELETE FROM audit_logs WHERE created_at < :cutoff_date"
                await self.db_manager.execute(query, {'cutoff_date': cutoff_date})
                logger.info(f"Cleaned up {await self.db_manager.rowcount} expired audit logs.")
                await asyncio.sleep(86400) # Run daily
            except Exception as e:
                logger.error(f"Error during log retention cleanup: {e}")
                await asyncio.sleep(3600) # Wait 1 hour on error

    async def _monitor_audit_events(self):
        """Background task to monitor for suspicious activity and compliance violations."""
        while self.is_running:
            try:
                # Example: Monitor for unusual user activity
                await self._detect_anomalies()

                # Example: Check compliance status
                await self._check_compliance_status()

                await asyncio.sleep(300) # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in audit event monitoring: {e}")
                await asyncio.sleep(600) # Wait 10 minutes on error

    async def _generate_audit_report_data(self, report: AuditReport, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for generating actual report data."""
        # In a real application, this would call a dedicated report generation service
        # and return the results.
        return {
            "report_id": report.id,
            "name": report.name,
            "type": report.report_type,
            "status": "completed",
            "generated_at": datetime.utcnow().isoformat(),
            "data": {
                "total_events": 100,
                "event_distribution": {"user_login": 20, "bet_placement": 30, "payment_processing": 20, "data_access": 30},
                "severity_distribution": {"low": 50, "medium": 30, "high": 10, "critical": 10},
                "top_users": [{"id": 1, "username": "User1", "count": 50}, {"id": 2, "username": "User2", "count": 30}],
                "top_guilds": [{"id": 1, "name": "Guild1", "count": 40}, {"id": 2, "name": "Guild2", "count": 20}],
                "compliance_status": "compliant",
                "findings": [],
                "recommendations": []
            }
        }

    async def _detect_anomalies(self):
        """Placeholder for anomaly detection logic."""
        # This would involve analyzing patterns, detecting unusual activity,
        # and logging alerts for suspicious behavior.
        logger.debug("Placeholder: Anomaly detection logic would go here.")

    async def _check_compliance_status(self):
        """Placeholder for compliance status checking."""
        # This would involve checking if all required audit events are enabled,
        # if retention periods are met, and if there are any compliance violations.
        logger.debug("Placeholder: Compliance status checking would go here.")

    async def _generate_automated_reports(self):
        """Placeholder for automated report generation."""
        # This would involve generating compliance reports based on the
        # configured retention periods and alert conditions.
        logger.debug("Placeholder: Automated report generation would go here.")

    async def cleanup(self):
        """Cleanup audit service resources."""
        self.is_running = False
        if self.retention_task:
            self.retention_task.cancel()
        if self.monitoring_task:
            self.monitoring_task.cancel()
        await self.clear_audit_cache()
        logger.info("Audit service resources cleaned up.")
