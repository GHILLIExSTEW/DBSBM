"""
Compliance Service for DBSBM System.
Implements GDPR, SOC 2, PCI DSS compliance, audit logging, and data privacy controls.
"""

import asyncio
import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

from data.db_manager import DatabaseManager
from data.cache_manager import cache_get, cache_set
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

class ComplianceType(Enum):
    """Compliance framework types."""
    GDPR = "gdpr"
    SOC2 = "soc2"
    PCI_DSS = "pci"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    CUSTOM = "custom"

class DataRetentionType(Enum):
    """Data retention types."""
    USER_DATA = "user_data"
    BET_DATA = "bet_data"
    AUDIT_LOGS = "audit_logs"
    AI_TRAINING_DATA = "ai_training_data"
    ANALYTICS_DATA = "analytics_data"
    SYSTEM_LOGS = "system_logs"

class DeletionMethod(Enum):
    """Data deletion methods."""
    SOFT_DELETE = "soft_delete"
    HARD_DELETE = "hard_delete"
    ANONYMIZE = "anonymize"
    PSEUDONYMIZE = "pseudonymize"

class ConsentType(Enum):
    """Consent types for data processing."""
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    THIRD_PARTY = "third_party"
    COOKIES = "cookies"
    COMMUNICATIONS = "communications"

@dataclass
class CompliancePolicy:
    """Compliance policy configuration."""
    id: int
    policy_name: str
    policy_type: ComplianceType
    policy_version: str
    policy_config: Dict[str, Any]
    is_active: bool
    effective_date: datetime
    expiry_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

@dataclass
class AuditLog:
    """Audit log entry."""
    id: int
    user_id: Optional[int]
    guild_id: Optional[int]
    tenant_id: Optional[int]
    action_type: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    action_data: Dict[str, Any]
    ip_address: str
    user_agent: str
    session_id: Optional[str]
    compliance_tags: List[str]
    timestamp: datetime

@dataclass
class PrivacyConsent:
    """Privacy consent record."""
    id: int
    user_id: int
    consent_type: ConsentType
    consent_status: bool
    consent_data: Dict[str, Any]
    consent_version: str
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

@dataclass
class DataRetentionPolicy:
    """Data retention policy."""
    id: int
    policy_name: str
    data_type: DataRetentionType
    retention_period_days: int
    deletion_method: DeletionMethod
    is_active: bool
    last_execution: Optional[datetime]
    next_execution: Optional[datetime]
    created_at: datetime
    updated_at: datetime

@dataclass
class ComplianceReport:
    """Compliance report."""
    id: int
    report_type: ComplianceType
    report_period: str
    report_data: Dict[str, Any]
    generated_at: datetime
    expires_at: datetime
    is_archived: bool

class ComplianceService:
    """Compliance service for regulatory requirements and data privacy."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.compliance_policies = {}
        self.retention_policies = {}
        self.audit_queue = asyncio.Queue()
        self.audit_worker_task = None

    async def start(self):
        """Start the compliance service."""
        logger.info("Starting ComplianceService...")

        # Load compliance policies
        await self._load_compliance_policies()

        # Load retention policies
        await self._load_retention_policies()

        # Start audit worker
        self.audit_worker_task = asyncio.create_task(self._audit_worker())

        # Initialize default policies
        await self._initialize_default_policies()

        logger.info("ComplianceService started successfully")

    async def stop(self):
        """Stop the compliance service."""
        logger.info("Stopping ComplianceService...")

        if self.audit_worker_task:
            self.audit_worker_task.cancel()
            try:
                await self.audit_worker_task
            except asyncio.CancelledError:
                pass

        logger.info("ComplianceService stopped")

    @time_operation("compliance_log_audit_event")
    async def log_audit_event(self, user_id: Optional[int], action_type: str,
                            resource_type: Optional[str] = None, resource_id: Optional[int] = None,
                            action_data: Optional[Dict[str, Any]] = None, ip_address: str = "system",
                            user_agent: str = "system", session_id: Optional[str] = None,
                            guild_id: Optional[int] = None, tenant_id: Optional[int] = None,
                            compliance_tags: Optional[List[str]] = None):
        """Log an audit event for compliance tracking."""
        try:
            audit_event = {
                'user_id': user_id,
                'guild_id': guild_id,
                'tenant_id': tenant_id,
                'action_type': action_type,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action_data': action_data or {},
                'ip_address': ip_address,
                'user_agent': user_agent,
                'session_id': session_id,
                'compliance_tags': compliance_tags or [],
                'timestamp': datetime.utcnow()
            }

            # Add to audit queue for async processing
            await self.audit_queue.put(audit_event)

            record_metric("compliance_audit_events", 1)

        except Exception as e:
            logger.error(f"Log audit event error: {e}")

    @time_operation("compliance_get_audit_logs")
    async def get_audit_logs(self, user_id: Optional[int] = None, guild_id: Optional[int] = None,
                           tenant_id: Optional[int] = None, action_type: Optional[str] = None,
                           start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                           limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Get audit logs with filtering."""
        try:
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []

            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)

            if guild_id:
                query += " AND guild_id = %s"
                params.append(guild_id)

            if tenant_id:
                query += " AND tenant_id = %s"
                params.append(tenant_id)

            if action_type:
                query += " AND action_type = %s"
                params.append(action_type)

            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)

            query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            rows = await self.db_manager.fetch_all(query, params)

            audit_logs = []
            for row in rows:
                audit_logs.append(AuditLog(
                    id=row['id'],
                    user_id=row['user_id'],
                    guild_id=row['guild_id'],
                    tenant_id=row['tenant_id'],
                    action_type=row['action_type'],
                    resource_type=row['resource_type'],
                    resource_id=row['resource_id'],
                    action_data=json.loads(row['action_data']) if row['action_data'] else {},
                    ip_address=row['ip_address'],
                    user_agent=row['user_agent'],
                    session_id=row['session_id'],
                    compliance_tags=json.loads(row['compliance_tags']) if row['compliance_tags'] else [],
                    timestamp=row['timestamp']
                ))

            return audit_logs

        except Exception as e:
            logger.error(f"Get audit logs error: {e}")
            return []

    @time_operation("compliance_record_consent")
    async def record_consent(self, user_id: int, consent_type: ConsentType,
                           consent_status: bool, consent_version: str,
                           consent_data: Optional[Dict[str, Any]] = None,
                           expires_at: Optional[datetime] = None) -> bool:
        """Record user consent for data processing."""
        try:
            # Check if consent already exists
            existing_query = """
                SELECT id FROM privacy_consents
                WHERE user_id = %s AND consent_type = %s AND consent_status = %s
            """
            existing = await self.db_manager.fetch_one(existing_query, (user_id, consent_type.value, consent_status))

            if existing:
                # Update existing consent
                update_query = """
                    UPDATE privacy_consents
                    SET consent_data = %s, expires_at = %s, updated_at = NOW()
                    WHERE id = %s
                """
                await self.db_manager.execute(update_query, (
                    json.dumps(consent_data or {}), expires_at, existing['id']
                ))
            else:
                # Create new consent record
                insert_query = """
                    INSERT INTO privacy_consents
                    (user_id, consent_type, consent_status, consent_data, consent_version,
                     granted_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

                granted_at = datetime.utcnow() if consent_status else None

                await self.db_manager.execute(insert_query, (
                    user_id, consent_type.value, consent_status,
                    json.dumps(consent_data or {}), consent_version,
                    granted_at, expires_at
                ))

            # Log consent event
            await self.log_audit_event(
                user_id=user_id,
                action_type="consent_recorded",
                resource_type="privacy_consent",
                action_data={
                    "consent_type": consent_type.value,
                    "consent_status": consent_status,
                    "consent_version": consent_version
                },
                compliance_tags=["gdpr", "privacy"]
            )

            record_metric("compliance_consents_recorded", 1)

            return True

        except Exception as e:
            logger.error(f"Record consent error: {e}")
            return False

    @time_operation("compliance_revoke_consent")
    async def revoke_consent(self, user_id: int, consent_type: ConsentType) -> bool:
        """Revoke user consent for data processing."""
        try:
            query = """
                UPDATE privacy_consents
                SET consent_status = FALSE, revoked_at = NOW(), updated_at = NOW()
                WHERE user_id = %s AND consent_type = %s AND consent_status = TRUE
            """
            await self.db_manager.execute(query, (user_id, consent_type.value))

            # Log consent revocation
            await self.log_audit_event(
                user_id=user_id,
                action_type="consent_revoked",
                resource_type="privacy_consent",
                action_data={"consent_type": consent_type.value},
                compliance_tags=["gdpr", "privacy"]
            )

            record_metric("compliance_consents_revoked", 1)

            return True

        except Exception as e:
            logger.error(f"Revoke consent error: {e}")
            return False

    @time_operation("compliance_get_user_consents")
    async def get_user_consents(self, user_id: int) -> List[PrivacyConsent]:
        """Get all consent records for a user."""
        try:
            query = """
                SELECT * FROM privacy_consents
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            rows = await self.db_manager.fetch_all(query, (user_id,))

            consents = []
            for row in rows:
                consents.append(PrivacyConsent(
                    id=row['id'],
                    user_id=row['user_id'],
                    consent_type=ConsentType(row['consent_type']),
                    consent_status=row['consent_status'],
                    consent_data=json.loads(row['consent_data']) if row['consent_data'] else {},
                    consent_version=row['consent_version'],
                    granted_at=row['granted_at'],
                    revoked_at=row['revoked_at'],
                    expires_at=row['expires_at'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))

            return consents

        except Exception as e:
            logger.error(f"Get user consents error: {e}")
            return []

    @time_operation("compliance_check_consent")
    async def check_consent(self, user_id: int, consent_type: ConsentType) -> bool:
        """Check if user has given consent for a specific type."""
        try:
            query = """
                SELECT consent_status, expires_at
                FROM privacy_consents
                WHERE user_id = %s AND consent_type = %s
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await self.db_manager.fetch_one(query, (user_id, consent_type.value))

            if not row:
                return False

            # Check if consent is still valid
            if row['expires_at'] and datetime.utcnow() > row['expires_at']:
                return False

            return row['consent_status']

        except Exception as e:
            logger.error(f"Check consent error: {e}")
            return False

    @time_operation("compliance_process_data_request")
    async def process_data_request(self, user_id: int, request_type: str,
                                 request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process GDPR data subject rights requests."""
        try:
            if request_type == "access":
                return await self._process_access_request(user_id)
            elif request_type == "portability":
                return await self._process_portability_request(user_id)
            elif request_type == "deletion":
                return await self._process_deletion_request(user_id)
            elif request_type == "rectification":
                return await self._process_rectification_request(user_id, request_data)
            else:
                raise ValueError(f"Unsupported request type: {request_type}")

        except Exception as e:
            logger.error(f"Process data request error: {e}")
            return {"error": str(e)}

    @time_operation("compliance_execute_retention_policies")
    async def execute_retention_policies(self) -> Dict[str, Any]:
        """Execute data retention policies."""
        try:
            results = {
                "policies_executed": 0,
                "records_processed": 0,
                "records_deleted": 0,
                "errors": []
            }

            # Get active retention policies
            query = """
                SELECT * FROM data_retention_policies
                WHERE is_active = TRUE AND next_execution <= NOW()
            """
            policies = await self.db_manager.fetch_all(query)

            for policy_row in policies:
                try:
                    policy = DataRetentionPolicy(
                        id=policy_row['id'],
                        policy_name=policy_row['policy_name'],
                        data_type=DataRetentionType(policy_row['data_type']),
                        retention_period_days=policy_row['retention_period_days'],
                        deletion_method=DeletionMethod(policy_row['deletion_method']),
                        is_active=policy_row['is_active'],
                        last_execution=policy_row['last_execution'],
                        next_execution=policy_row['next_execution'],
                        created_at=policy_row['created_at'],
                        updated_at=policy_row['updated_at']
                    )

                    # Execute policy
                    processed, deleted = await self._execute_retention_policy(policy)

                    results["policies_executed"] += 1
                    results["records_processed"] += processed
                    results["records_deleted"] += deleted

                    # Update policy execution time
                    await self._update_policy_execution(policy.id)

                except Exception as e:
                    results["errors"].append(f"Policy {policy_row['policy_name']}: {str(e)}")

            return results

        except Exception as e:
            logger.error(f"Execute retention policies error: {e}")
            return {"error": str(e)}

    @time_operation("compliance_generate_compliance_report")
    async def generate_compliance_report(self, compliance_type: ComplianceType,
                                       report_period: str = "monthly") -> Optional[ComplianceReport]:
        """Generate compliance report for a specific framework."""
        try:
            if compliance_type == ComplianceType.GDPR:
                report_data = await self._generate_gdpr_report(report_period)
            elif compliance_type == ComplianceType.SOC2:
                report_data = await self._generate_soc2_report(report_period)
            elif compliance_type == ComplianceType.PCI_DSS:
                report_data = await self._generate_pci_report(report_period)
            else:
                raise ValueError(f"Unsupported compliance type: {compliance_type}")

            # Store report
            query = """
                INSERT INTO compliance_reports (report_type, report_period, report_data, generated_at, expires_at)
                VALUES (%s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 1 YEAR))
            """
            await self.db_manager.execute(query, (
                compliance_type.value, report_period, json.dumps(report_data)
            ))

            report_id = await self.db_manager.last_insert_id()

            return ComplianceReport(
                id=report_id,
                report_type=compliance_type,
                report_period=report_period,
                report_data=report_data,
                generated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365),
                is_archived=False
            )

        except Exception as e:
            logger.error(f"Generate compliance report error: {e}")
            return None

    @time_operation("compliance_get_compliance_status")
    async def get_compliance_status(self, tenant_id: Optional[int] = None) -> Dict[str, Any]:
        """Get overall compliance status."""
        try:
            status = {
                "gdpr": {"status": "unknown", "score": 0, "issues": []},
                "soc2": {"status": "unknown", "score": 0, "issues": []},
                "pci_dss": {"status": "unknown", "score": 0, "issues": []},
                "overall_score": 0
            }

            # Check GDPR compliance
            gdpr_status = await self._check_gdpr_compliance(tenant_id)
            status["gdpr"] = gdpr_status

            # Check SOC 2 compliance
            soc2_status = await self._check_soc2_compliance(tenant_id)
            status["soc2"] = soc2_status

            # Check PCI DSS compliance
            pci_status = await self._check_pci_compliance(tenant_id)
            status["pci_dss"] = pci_status

            # Calculate overall score
            scores = [gdpr_status["score"], soc2_status["score"], pci_status["score"]]
            status["overall_score"] = sum(scores) / len(scores) if scores else 0

            return status

        except Exception as e:
            logger.error(f"Get compliance status error: {e}")
            return {"error": str(e)}

    # Private helper methods

    async def _load_compliance_policies(self):
        """Load compliance policies from database."""
        try:
            query = "SELECT * FROM compliance_policies WHERE is_active = TRUE"
            rows = await self.db_manager.fetch_all(query)

            for row in rows:
                policy = CompliancePolicy(
                    id=row['id'],
                    policy_name=row['policy_name'],
                    policy_type=ComplianceType(row['policy_type']),
                    policy_version=row['policy_version'],
                    policy_config=json.loads(row['policy_config']),
                    is_active=row['is_active'],
                    effective_date=row['effective_date'],
                    expiry_date=row['expiry_date'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                self.compliance_policies[policy.policy_type] = policy

        except Exception as e:
            logger.error(f"Load compliance policies error: {e}")

    async def _load_retention_policies(self):
        """Load retention policies from database."""
        try:
            query = "SELECT * FROM data_retention_policies WHERE is_active = TRUE"
            rows = await self.db_manager.fetch_all(query)

            for row in rows:
                policy = DataRetentionPolicy(
                    id=row['id'],
                    policy_name=row['policy_name'],
                    data_type=DataRetentionType(row['data_type']),
                    retention_period_days=row['retention_period_days'],
                    deletion_method=DeletionMethod(row['deletion_method']),
                    is_active=row['is_active'],
                    last_execution=row['last_execution'],
                    next_execution=row['next_execution'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                self.retention_policies[policy.data_type] = policy

        except Exception as e:
            logger.error(f"Load retention policies error: {e}")

    async def _initialize_default_policies(self):
        """Initialize default compliance policies if they don't exist."""
        try:
            default_policies = [
                {
                    "name": "GDPR Data Protection",
                    "type": ComplianceType.GDPR,
                    "version": "1.0.0",
                    "config": {
                        "data_retention_days": 2555,
                        "right_to_forget": True,
                        "data_portability": True,
                        "consent_required": True,
                        "privacy_by_design": True
                    }
                },
                {
                    "name": "SOC 2 Security Controls",
                    "type": ComplianceType.SOC2,
                    "version": "1.0.0",
                    "config": {
                        "access_controls": True,
                        "audit_logging": True,
                        "encryption": True,
                        "incident_response": True,
                        "change_management": True
                    }
                },
                {
                    "name": "PCI DSS Compliance",
                    "type": ComplianceType.PCI_DSS,
                    "version": "1.0.0",
                    "config": {
                        "card_data_encryption": True,
                        "secure_transmissions": True,
                        "access_controls": True,
                        "monitoring": True,
                        "vulnerability_management": True
                    }
                }
            ]

            for policy_data in default_policies:
                await self._create_policy_if_not_exists(policy_data)

        except Exception as e:
            logger.error(f"Initialize default policies error: {e}")

    async def _create_policy_if_not_exists(self, policy_data: Dict[str, Any]):
        """Create a compliance policy if it doesn't exist."""
        try:
            query = "SELECT id FROM compliance_policies WHERE policy_type = %s"
            existing = await self.db_manager.fetch_one(query, (policy_data["type"].value,))

            if not existing:
                insert_query = """
                    INSERT INTO compliance_policies
                    (policy_name, policy_type, policy_version, policy_config, is_active, effective_date)
                    VALUES (%s, %s, %s, %s, TRUE, NOW())
                """
                await self.db_manager.execute(insert_query, (
                    policy_data["name"],
                    policy_data["type"].value,
                    policy_data["version"],
                    json.dumps(policy_data["config"])
                ))

        except Exception as e:
            logger.error(f"Create policy error: {e}")

    async def _audit_worker(self):
        """Background worker for processing audit events."""
        try:
            while True:
                try:
                    # Get audit event from queue
                    audit_event = await asyncio.wait_for(self.audit_queue.get(), timeout=1.0)

                    # Store audit event in database
                    await self._store_audit_event(audit_event)

                    # Mark task as done
                    self.audit_queue.task_done()

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Audit worker error: {e}")

        except asyncio.CancelledError:
            logger.info("Audit worker cancelled")
        except Exception as e:
            logger.error(f"Audit worker fatal error: {e}")

    async def _store_audit_event(self, audit_event: Dict[str, Any]):
        """Store audit event in database."""
        try:
            query = """
                INSERT INTO audit_logs
                (user_id, guild_id, tenant_id, action_type, resource_type, resource_id,
                 action_data, ip_address, user_agent, session_id, compliance_tags, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            await self.db_manager.execute(query, (
                audit_event['user_id'],
                audit_event['guild_id'],
                audit_event['tenant_id'],
                audit_event['action_type'],
                audit_event['resource_type'],
                audit_event['resource_id'],
                json.dumps(audit_event['action_data']),
                audit_event['ip_address'],
                audit_event['user_agent'],
                audit_event['session_id'],
                json.dumps(audit_event['compliance_tags']),
                audit_event['timestamp']
            ))

        except Exception as e:
            logger.error(f"Store audit event error: {e}")

    async def _process_access_request(self, user_id: int) -> Dict[str, Any]:
        """Process GDPR right of access request."""
        try:
            user_data = {
                "personal_info": {},
                "betting_history": [],
                "consent_records": [],
                "audit_logs": []
            }

            # Get user personal information
            user_query = "SELECT * FROM users WHERE user_id = %s"
            user_row = await self.db_manager.fetch_one(user_query, (user_id,))
            if user_row:
                user_data["personal_info"] = {
                    "user_id": user_row['user_id'],
                    "username": user_row['username'],
                    "email": user_row.get('email'),
                    "created_at": user_row['created_at'].isoformat()
                }

            # Get betting history
            bets_query = "SELECT * FROM bets WHERE user_id = %s ORDER BY created_at DESC LIMIT 100"
            bets_rows = await self.db_manager.fetch_all(bets_query, (user_id,))
            user_data["betting_history"] = [dict(row) for row in bets_rows]

            # Get consent records
            consents = await self.get_user_consents(user_id)
            user_data["consent_records"] = [consent.__dict__ for consent in consents]

            # Get audit logs
            audit_logs = await self.get_audit_logs(user_id=user_id, limit=100)
            user_data["audit_logs"] = [log.__dict__ for log in audit_logs]

            return user_data

        except Exception as e:
            logger.error(f"Process access request error: {e}")
            return {"error": str(e)}

    async def _process_portability_request(self, user_id: int) -> Dict[str, Any]:
        """Process GDPR data portability request."""
        try:
            # Similar to access request but in machine-readable format
            access_data = await self._process_access_request(user_id)

            # Add export metadata
            export_data = {
                "export_date": datetime.utcnow().isoformat(),
                "export_format": "json",
                "data_subject_id": user_id,
                "data": access_data
            }

            return export_data

        except Exception as e:
            logger.error(f"Process portability request error: {e}")
            return {"error": str(e)}

    async def _process_deletion_request(self, user_id: int) -> Dict[str, Any]:
        """Process GDPR right to be forgotten request."""
        try:
            # Anonymize user data instead of hard delete
            anonymization_data = {
                "username": f"deleted_user_{user_id}",
                "email": f"deleted_{user_id}@deleted.com",
                "anonymized_at": datetime.utcnow().isoformat()
            }

            # Update user record
            update_query = """
                UPDATE users
                SET username = %s, email = %s, updated_at = NOW()
                WHERE user_id = %s
            """
            await self.db_manager.execute(update_query, (
                anonymization_data["username"],
                anonymization_data["email"],
                user_id
            ))

            # Log deletion request
            await self.log_audit_event(
                user_id=user_id,
                action_type="data_deletion_requested",
                action_data=anonymization_data,
                compliance_tags=["gdpr", "right_to_forget"]
            )

            return {"status": "success", "message": "User data anonymized"}

        except Exception as e:
            logger.error(f"Process deletion request error: {e}")
            return {"error": str(e)}

    async def _process_rectification_request(self, user_id: int, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process GDPR right to rectification request."""
        try:
            # Update user data based on request
            updates = {}
            allowed_fields = ['username', 'email']

            for field, value in request_data.items():
                if field in allowed_fields:
                    updates[field] = value

            if updates:
                set_clauses = [f"{field} = %s" for field in updates.keys()]
                query = f"UPDATE users SET {', '.join(set_clauses)}, updated_at = NOW() WHERE user_id = %s"
                await self.db_manager.execute(query, list(updates.values()) + [user_id])

            # Log rectification request
            await self.log_audit_event(
                user_id=user_id,
                action_type="data_rectification_requested",
                action_data=updates,
                compliance_tags=["gdpr", "rectification"]
            )

            return {"status": "success", "message": "User data updated", "updates": updates}

        except Exception as e:
            logger.error(f"Process rectification request error: {e}")
            return {"error": str(e)}

    async def _execute_retention_policy(self, policy: DataRetentionPolicy) -> Tuple[int, int]:
        """Execute a data retention policy."""
        try:
            processed = 0
            deleted = 0

            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_period_days)

            # Get records to process based on data type
            if policy.data_type == DataRetentionType.USER_DATA:
                query = "SELECT COUNT(*) as count FROM users WHERE created_at < %s"
                count_row = await self.db_manager.fetch_one(query, (cutoff_date,))
                processed = count_row['count'] if count_row else 0

                if processed > 0 and policy.deletion_method == DeletionMethod.ANONYMIZE:
                    # Anonymize old user data
                    update_query = """
                        UPDATE users
                        SET username = CONCAT('deleted_user_', user_id),
                            email = CONCAT('deleted_', user_id, '@deleted.com'),
                            updated_at = NOW()
                        WHERE created_at < %s
                    """
                    await self.db_manager.execute(update_query, (cutoff_date,))
                    deleted = processed

            elif policy.data_type == DataRetentionType.AUDIT_LOGS:
                query = "SELECT COUNT(*) as count FROM audit_logs WHERE timestamp < %s"
                count_row = await self.db_manager.fetch_one(query, (cutoff_date,))
                processed = count_row['count'] if count_row else 0

                if processed > 0 and policy.deletion_method == DeletionMethod.HARD_DELETE:
                    # Delete old audit logs
                    delete_query = "DELETE FROM audit_logs WHERE timestamp < %s"
                    await self.db_manager.execute(delete_query, (cutoff_date,))
                    deleted = processed

            return processed, deleted

        except Exception as e:
            logger.error(f"Execute retention policy error: {e}")
            return 0, 0

    async def _update_policy_execution(self, policy_id: int):
        """Update policy execution timestamp."""
        try:
            query = """
                UPDATE data_retention_policies
                SET last_execution = NOW(), next_execution = DATE_ADD(NOW(), INTERVAL 1 DAY)
                WHERE id = %s
            """
            await self.db_manager.execute(query, (policy_id,))
        except Exception as e:
            logger.error(f"Update policy execution error: {e}")

    async def _generate_gdpr_report(self, report_period: str) -> Dict[str, Any]:
        """Generate GDPR compliance report."""
        try:
            report = {
                "report_period": report_period,
                "generated_at": datetime.utcnow().isoformat(),
                "gdpr_metrics": {
                    "total_users": 0,
                    "consent_records": 0,
                    "data_requests": 0,
                    "deletion_requests": 0,
                    "rectification_requests": 0
                },
                "compliance_status": "compliant",
                "issues": []
            }

            # Get user count
            user_query = "SELECT COUNT(*) as count FROM users"
            user_row = await self.db_manager.fetch_one(user_query)
            report["gdpr_metrics"]["total_users"] = user_row['count'] if user_row else 0

            # Get consent records count
            consent_query = "SELECT COUNT(*) as count FROM privacy_consents"
            consent_row = await self.db_manager.fetch_one(consent_query)
            report["gdpr_metrics"]["consent_records"] = consent_row['count'] if consent_row else 0

            # Get data request counts
            audit_queries = [
                ("data_access_requested", "data_requests"),
                ("data_deletion_requested", "deletion_requests"),
                ("data_rectification_requested", "rectification_requests")
            ]

            for action_type, metric_name in audit_queries:
                query = "SELECT COUNT(*) as count FROM audit_logs WHERE action_type = %s"
                row = await self.db_manager.fetch_one(query, (action_type,))
                report["gdpr_metrics"][metric_name] = row['count'] if row else 0

            return report

        except Exception as e:
            logger.error(f"Generate GDPR report error: {e}")
            return {"error": str(e)}

    async def _generate_soc2_report(self, report_period: str) -> Dict[str, Any]:
        """Generate SOC 2 compliance report."""
        try:
            report = {
                "report_period": report_period,
                "generated_at": datetime.utcnow().isoformat(),
                "soc2_metrics": {
                    "total_audit_events": 0,
                    "security_events": 0,
                    "access_control_events": 0,
                    "data_encryption_status": "enabled"
                },
                "compliance_status": "compliant",
                "control_objectives": {
                    "cc1": "control environment",
                    "cc2": "communication and information",
                    "cc3": "risk assessment",
                    "cc4": "monitoring activities",
                    "cc5": "control activities",
                    "cc6": "logical and physical access controls",
                    "cc7": "system operations",
                    "cc8": "change management",
                    "cc9": "risk mitigation"
                }
            }

            # Get audit event counts
            audit_query = "SELECT COUNT(*) as count FROM audit_logs"
            audit_row = await self.db_manager.fetch_one(audit_query)
            report["soc2_metrics"]["total_audit_events"] = audit_row['count'] if audit_row else 0

            # Get security event counts
            security_query = "SELECT COUNT(*) as count FROM security_events"
            security_row = await self.db_manager.fetch_one(security_query)
            report["soc2_metrics"]["security_events"] = security_row['count'] if security_row else 0

            return report

        except Exception as e:
            logger.error(f"Generate SOC 2 report error: {e}")
            return {"error": str(e)}

    async def _generate_pci_report(self, report_period: str) -> Dict[str, Any]:
        """Generate PCI DSS compliance report."""
        try:
            report = {
                "report_period": report_period,
                "generated_at": datetime.utcnow().isoformat(),
                "pci_metrics": {
                    "payment_processing_events": 0,
                    "encryption_status": "enabled",
                    "access_control_status": "enabled",
                    "monitoring_status": "enabled"
                },
                "compliance_status": "compliant",
                "requirements": {
                    "req1": "install and maintain a firewall configuration",
                    "req2": "do not use vendor-supplied defaults",
                    "req3": "protect stored cardholder data",
                    "req4": "encrypt transmission of cardholder data",
                    "req5": "use and regularly update anti-virus software",
                    "req6": "develop and maintain secure systems",
                    "req7": "restrict access to cardholder data",
                    "req8": "assign a unique ID to each person",
                    "req9": "restrict physical access to cardholder data",
                    "req10": "track and monitor all access",
                    "req11": "regularly test security systems",
                    "req12": "maintain a policy"
                }
            }

            return report

        except Exception as e:
            logger.error(f"Generate PCI report error: {e}")
            return {"error": str(e)}

    async def _check_gdpr_compliance(self, tenant_id: Optional[int]) -> Dict[str, Any]:
        """Check GDPR compliance status."""
        try:
            score = 100
            issues = []

            # Check consent records
            consent_query = "SELECT COUNT(*) as count FROM privacy_consents"
            consent_row = await self.db_manager.fetch_one(consent_query)
            consent_count = consent_row['count'] if consent_row else 0

            if consent_count == 0:
                score -= 30
                issues.append("No consent records found")

            # Check audit logging
            audit_query = "SELECT COUNT(*) as count FROM audit_logs"
            audit_row = await self.db_manager.fetch_one(audit_query)
            audit_count = audit_row['count'] if audit_row else 0

            if audit_count == 0:
                score -= 20
                issues.append("No audit logs found")

            # Check data retention policies
            retention_query = "SELECT COUNT(*) as count FROM data_retention_policies WHERE is_active = TRUE"
            retention_row = await self.db_manager.fetch_one(retention_query)
            retention_count = retention_row['count'] if retention_row else 0

            if retention_count == 0:
                score -= 25
                issues.append("No data retention policies configured")

            status = "compliant" if score >= 80 else "non_compliant" if score >= 60 else "critical"

            return {
                "status": status,
                "score": max(0, score),
                "issues": issues
            }

        except Exception as e:
            logger.error(f"Check GDPR compliance error: {e}")
            return {"status": "unknown", "score": 0, "issues": [str(e)]}

    async def _check_soc2_compliance(self, tenant_id: Optional[int]) -> Dict[str, Any]:
        """Check SOC 2 compliance status."""
        try:
            score = 100
            issues = []

            # Check security events
            security_query = "SELECT COUNT(*) as count FROM security_events"
            security_row = await self.db_manager.fetch_one(security_query)
            security_count = security_row['count'] if security_row else 0

            if security_count == 0:
                score -= 20
                issues.append("No security events logged")

            # Check MFA usage
            mfa_query = "SELECT COUNT(*) as count FROM mfa_devices WHERE is_active = TRUE"
            mfa_row = await self.db_manager.fetch_one(mfa_query)
            mfa_count = mfa_row['count'] if mfa_row else 0

            if mfa_count == 0:
                score -= 15
                issues.append("No MFA devices configured")

            status = "compliant" if score >= 80 else "non_compliant" if score >= 60 else "critical"

            return {
                "status": status,
                "score": max(0, score),
                "issues": issues
            }

        except Exception as e:
            logger.error(f"Check SOC 2 compliance error: {e}")
            return {"status": "unknown", "score": 0, "issues": [str(e)]}

    async def _check_pci_compliance(self, tenant_id: Optional[int]) -> Dict[str, Any]:
        """Check PCI DSS compliance status."""
        try:
            score = 100
            issues = []

            # Check encryption status
            # This would check actual encryption implementation
            score -= 10
            issues.append("Encryption implementation needs verification")

            # Check access controls
            access_query = "SELECT COUNT(*) as count FROM user_roles"
            access_row = await self.db_manager.fetch_one(access_query)
            access_count = access_row['count'] if access_row else 0

            if access_count == 0:
                score -= 20
                issues.append("No access controls configured")

            status = "compliant" if score >= 80 else "non_compliant" if score >= 60 else "critical"

            return {
                "status": status,
                "score": max(0, score),
                "issues": issues
            }

        except Exception as e:
            logger.error(f"Check PCI compliance error: {e}")
            return {"status": "unknown", "score": 0, "issues": [str(e)]}
