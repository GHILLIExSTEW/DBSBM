"""
Multi-Tenancy Service for DBSBM System.
Implements tenant isolation, resource management, and enterprise features.
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
import hmac

from data.db_manager import DatabaseManager
from bot.data.cache_manager import cache_get, cache_set
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

class TenantStatus(Enum):
    """Tenant status types."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    PENDING = "pending"

class PlanType(Enum):
    """Tenant plan types."""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class ResourceType(Enum):
    """Resource types for quota management."""
    USERS = "users"
    BETS = "bets"
    API_CALLS = "api_calls"
    STORAGE = "storage"
    ANALYTICS = "analytics"
    ML_PREDICTIONS = "ml_predictions"
    WEBHOOKS = "webhooks"

@dataclass
class Tenant:
    """Tenant configuration."""
    id: int
    tenant_name: str
    tenant_code: str
    display_name: str
    status: TenantStatus
    plan_type: PlanType
    contact_email: Optional[str]
    contact_phone: Optional[str]
    settings: Dict[str, Any]
    custom_domain: Optional[str]
    timezone: str
    created_at: datetime
    updated_at: datetime

@dataclass
class TenantResource:
    """Tenant resource quota."""
    id: int
    tenant_id: int
    resource_type: ResourceType
    quota_limit: int
    current_usage: int
    reset_period: str
    last_reset: datetime
    next_reset: datetime
    is_active: bool

@dataclass
class TenantCustomization:
    """Tenant customization configuration."""
    id: int
    tenant_id: int
    customization_type: str
    customization_data: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class TenantBilling:
    """Tenant billing information."""
    id: int
    tenant_id: int
    plan_name: str
    billing_cycle: str
    amount: float
    currency: str
    status: str
    next_billing_date: datetime
    created_at: datetime
    updated_at: datetime

class TenantService:
    """Multi-tenancy service for enterprise management."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.default_quotas = self._load_default_quotas()
        self.tenant_cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def start(self):
        """Start the tenant service."""
        logger.info("Starting TenantService...")
        await self._initialize_default_tenant()
        await self._setup_resource_quotas()
        logger.info("TenantService started successfully")

    async def stop(self):
        """Stop the tenant service."""
        logger.info("Stopping TenantService...")
        self.tenant_cache.clear()
        logger.info("TenantService stopped")

    @time_operation("tenant_create_tenant")
    async def create_tenant(self, tenant_name: str, display_name: str, plan_type: PlanType,
                          contact_email: Optional[str] = None, contact_phone: Optional[str] = None,
                          custom_domain: Optional[str] = None, timezone: str = "UTC") -> Optional[Tenant]:
        """Create a new tenant."""
        try:
            # Generate unique tenant code
            tenant_code = self._generate_tenant_code()

            # Create tenant
            query = """
                INSERT INTO tenants (tenant_name, tenant_code, display_name, plan_type,
                                   contact_email, contact_phone, custom_domain, timezone, settings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            settings = {
                "features": self._get_plan_features(plan_type),
                "security": self._get_default_security_settings(),
                "integrations": self._get_default_integration_settings(),
                "notifications": self._get_default_notification_settings()
            }

            await self.db_manager.execute(query, (
                tenant_name, tenant_code, display_name, plan_type.value,
                contact_email, contact_phone, custom_domain, timezone, json.dumps(settings)
            ))

            # Get created tenant
            tenant_id = await self.db_manager.last_insert_id()
            tenant = await self.get_tenant_by_id(tenant_id)

            # Setup resource quotas
            await self._setup_tenant_quotas(tenant_id, plan_type)

            # Setup default customizations
            await self._setup_default_customizations(tenant_id, plan_type)

            # Setup billing
            await self._setup_tenant_billing(tenant_id, plan_type)

            record_metric("tenants_created", 1)

            return tenant

        except Exception as e:
            logger.error(f"Create tenant error: {e}")
            return None

    @time_operation("tenant_get_tenant")
    async def get_tenant_by_id(self, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID."""
        try:
            # Check cache first
            cache_key = f"tenant:{tenant_id}"
            cached = await cache_get(cache_key)
            if cached:
                return Tenant(**json.loads(cached))

            query = "SELECT * FROM tenants WHERE id = %s"
            row = await self.db_manager.fetch_one(query, (tenant_id,))

            if row:
                tenant = Tenant(
                    id=row['id'],
                    tenant_name=row['tenant_name'],
                    tenant_code=row['tenant_code'],
                    display_name=row['display_name'],
                    status=TenantStatus(row['status']),
                    plan_type=PlanType(row['plan_type']),
                    contact_email=row['contact_email'],
                    contact_phone=row['contact_phone'],
                    settings=json.loads(row['settings']) if row['settings'] else {},
                    custom_domain=row['custom_domain'],
                    timezone=row['timezone'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )

                # Cache tenant
                await cache_set(cache_key, json.dumps(tenant.__dict__), expire=self.cache_ttl)

                return tenant

            return None

        except Exception as e:
            logger.error(f"Get tenant error: {e}")
            return None

    @time_operation("tenant_get_tenant_by_code")
    async def get_tenant_by_code(self, tenant_code: str) -> Optional[Tenant]:
        """Get tenant by code."""
        try:
            query = "SELECT * FROM tenants WHERE tenant_code = %s"
            row = await self.db_manager.fetch_one(query, (tenant_code,))

            if row:
                return await self.get_tenant_by_id(row['id'])

            return None

        except Exception as e:
            logger.error(f"Get tenant by code error: {e}")
            return None

    @time_operation("tenant_update_tenant")
    async def update_tenant(self, tenant_id: int, updates: Dict[str, Any]) -> bool:
        """Update tenant configuration."""
        try:
            # Build update query
            set_clauses = []
            params = []

            allowed_fields = ['display_name', 'contact_email', 'contact_phone', 'custom_domain',
                            'timezone', 'settings', 'status', 'plan_type']

            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'settings' and isinstance(value, dict):
                        # Merge with existing settings
                        current_tenant = await self.get_tenant_by_id(tenant_id)
                        if current_tenant:
                            current_settings = current_tenant.settings
                            current_settings.update(value)
                            value = current_settings

                    set_clauses.append(f"{field} = %s")
                    params.append(value if field != 'settings' else json.dumps(value))

            if not set_clauses:
                return False

            set_clauses.append("updated_at = NOW()")
            params.append(tenant_id)

            query = f"UPDATE tenants SET {', '.join(set_clauses)} WHERE id = %s"
            await self.db_manager.execute(query, params)

            # Clear cache
            await cache_get(f"tenant:{tenant_id}", delete=True)

            # Update resource quotas if plan changed
            if 'plan_type' in updates:
                await self._update_tenant_quotas(tenant_id, PlanType(updates['plan_type']))

            record_metric("tenants_updated", 1)

            return True

        except Exception as e:
            logger.error(f"Update tenant error: {e}")
            return False

    @time_operation("tenant_delete_tenant")
    async def delete_tenant(self, tenant_id: int) -> bool:
        """Delete a tenant (soft delete)."""
        try:
            # Soft delete by setting status to inactive
            query = "UPDATE tenants SET status = %s, updated_at = NOW() WHERE id = %s"
            await self.db_manager.execute(query, (TenantStatus.INACTIVE.value, tenant_id))

            # Clear cache
            await cache_get(f"tenant:{tenant_id}", delete=True)

            record_metric("tenants_deleted", 1)

            return True

        except Exception as e:
            logger.error(f"Delete tenant error: {e}")
            return False

    @time_operation("tenant_get_resource_usage")
    async def get_resource_usage(self, tenant_id: int) -> Dict[str, TenantResource]:
        """Get resource usage for a tenant."""
        try:
            query = """
                SELECT * FROM tenant_resources
                WHERE tenant_id = %s AND is_active = TRUE
            """
            rows = await self.db_manager.fetch_all(query, (tenant_id,))

            resources = {}
            for row in rows:
                resources[row['resource_type']] = TenantResource(
                    id=row['id'],
                    tenant_id=row['tenant_id'],
                    resource_type=ResourceType(row['resource_type']),
                    quota_limit=row['quota_limit'],
                    current_usage=row['current_usage'],
                    reset_period=row['reset_period'],
                    last_reset=row['last_reset'],
                    next_reset=row['next_reset'],
                    is_active=row['is_active']
                )

            return resources

        except Exception as e:
            logger.error(f"Get resource usage error: {e}")
            return {}

    @time_operation("tenant_check_resource_quota")
    async def check_resource_quota(self, tenant_id: int, resource_type: ResourceType,
                                 required_amount: int = 1) -> bool:
        """Check if tenant has sufficient resource quota."""
        try:
            query = """
                SELECT quota_limit, current_usage, next_reset
                FROM tenant_resources
                WHERE tenant_id = %s AND resource_type = %s AND is_active = TRUE
            """
            row = await self.db_manager.fetch_one(query, (tenant_id, resource_type.value))

            if not row:
                # No quota set, allow unlimited usage
                return True

            # Check if quota has reset
            if row['next_reset'] and datetime.utcnow() > row['next_reset']:
                await self._reset_resource_quota(tenant_id, resource_type)
                return True

            # Check if quota is sufficient
            return (row['current_usage'] + required_amount) <= row['quota_limit']

        except Exception as e:
            logger.error(f"Check resource quota error: {e}")
            return False

    @time_operation("tenant_increment_resource_usage")
    async def increment_resource_usage(self, tenant_id: int, resource_type: ResourceType,
                                     amount: int = 1) -> bool:
        """Increment resource usage for a tenant."""
        try:
            query = """
                UPDATE tenant_resources
                SET current_usage = current_usage + %s, updated_at = NOW()
                WHERE tenant_id = %s AND resource_type = %s AND is_active = TRUE
            """
            await self.db_manager.execute(query, (amount, tenant_id, resource_type.value))

            return True

        except Exception as e:
            logger.error(f"Increment resource usage error: {e}")
            return False

    @time_operation("tenant_get_customizations")
    async def get_customizations(self, tenant_id: int) -> List[TenantCustomization]:
        """Get customizations for a tenant."""
        try:
            query = """
                SELECT * FROM tenant_customizations
                WHERE tenant_id = %s AND is_active = TRUE
            """
            rows = await self.db_manager.fetch_all(query, (tenant_id,))

            customizations = []
            for row in rows:
                customizations.append(TenantCustomization(
                    id=row['id'],
                    tenant_id=row['tenant_id'],
                    customization_type=row['customization_type'],
                    customization_data=json.loads(row['customization_data']),
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))

            return customizations

        except Exception as e:
            logger.error(f"Get customizations error: {e}")
            return []

    @time_operation("tenant_update_customization")
    async def update_customization(self, tenant_id: int, customization_type: str,
                                 customization_data: Dict[str, Any]) -> bool:
        """Update tenant customization."""
        try:
            # Check if customization exists
            query = """
                SELECT id FROM tenant_customizations
                WHERE tenant_id = %s AND customization_type = %s
            """
            existing = await self.db_manager.fetch_one(query, (tenant_id, customization_type))

            if existing:
                # Update existing
                update_query = """
                    UPDATE tenant_customizations
                    SET customization_data = %s, updated_at = NOW()
                    WHERE id = %s
                """
                await self.db_manager.execute(update_query, (json.dumps(customization_data), existing['id']))
            else:
                # Create new
                insert_query = """
                    INSERT INTO tenant_customizations (tenant_id, customization_type, customization_data)
                    VALUES (%s, %s, %s)
                """
                await self.db_manager.execute(insert_query, (tenant_id, customization_type, json.dumps(customization_data)))

            return True

        except Exception as e:
            logger.error(f"Update customization error: {e}")
            return False

    @time_operation("tenant_get_billing_info")
    async def get_billing_info(self, tenant_id: int) -> Optional[TenantBilling]:
        """Get billing information for a tenant."""
        try:
            query = """
                SELECT * FROM tenant_billing
                WHERE tenant_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await self.db_manager.fetch_one(query, (tenant_id,))

            if row:
                return TenantBilling(
                    id=row['id'],
                    tenant_id=row['tenant_id'],
                    plan_name=row['plan_name'],
                    billing_cycle=row['billing_cycle'],
                    amount=float(row['amount']),
                    currency=row['currency'],
                    status=row['status'],
                    next_billing_date=row['next_billing_date'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )

            return None

        except Exception as e:
            logger.error(f"Get billing info error: {e}")
            return None

    @time_operation("tenant_get_all_tenants")
    async def get_all_tenants(self, status: Optional[TenantStatus] = None,
                            plan_type: Optional[PlanType] = None, limit: int = 100) -> List[Tenant]:
        """Get all tenants with optional filtering."""
        try:
            query = "SELECT * FROM tenants WHERE 1=1"
            params = []

            if status:
                query += " AND status = %s"
                params.append(status.value)

            if plan_type:
                query += " AND plan_type = %s"
                params.append(plan_type.value)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            rows = await self.db_manager.fetch_all(query, params)

            tenants = []
            for row in rows:
                tenant = Tenant(
                    id=row['id'],
                    tenant_name=row['tenant_name'],
                    tenant_code=row['tenant_code'],
                    display_name=row['display_name'],
                    status=TenantStatus(row['status']),
                    plan_type=PlanType(row['plan_type']),
                    contact_email=row['contact_email'],
                    contact_phone=row['contact_phone'],
                    settings=json.loads(row['settings']) if row['settings'] else {},
                    custom_domain=row['custom_domain'],
                    timezone=row['timezone'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                tenants.append(tenant)

            return tenants

        except Exception as e:
            logger.error(f"Get all tenants error: {e}")
            return []

    @time_operation("tenant_get_tenant_stats")
    async def get_tenant_stats(self, tenant_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a tenant."""
        try:
            stats = {
                'resource_usage': {},
                'user_count': 0,
                'bet_count': 0,
                'revenue': 0.0,
                'active_features': [],
                'last_activity': None
            }

            # Get resource usage
            resources = await self.get_resource_usage(tenant_id)
            for resource_type, resource in resources.items():
                stats['resource_usage'][resource_type] = {
                    'current_usage': resource.current_usage,
                    'quota_limit': resource.quota_limit,
                    'usage_percentage': (resource.current_usage / resource.quota_limit * 100) if resource.quota_limit > 0 else 0
                }

            # Get user count
            user_query = """
                SELECT COUNT(*) as user_count
                FROM guild_settings
                WHERE tenant_id = %s
            """
            user_row = await self.db_manager.fetch_one(user_query, (tenant_id,))
            stats['user_count'] = user_row['user_count'] if user_row else 0

            # Get bet count
            bet_query = """
                SELECT COUNT(*) as bet_count
                FROM bets b
                JOIN guild_settings gs ON b.guild_id = gs.guild_id
                WHERE gs.tenant_id = %s
            """
            bet_row = await self.db_manager.fetch_one(bet_query, (tenant_id,))
            stats['bet_count'] = bet_row['bet_count'] if bet_row else 0

            # Get active features
            tenant = await self.get_tenant_by_id(tenant_id)
            if tenant and tenant.settings.get('features'):
                stats['active_features'] = list(tenant.settings['features'].keys())

            return stats

        except Exception as e:
            logger.error(f"Get tenant stats error: {e}")
            return {}

    # Private helper methods

    def _load_default_quotas(self) -> Dict[PlanType, Dict[ResourceType, int]]:
        """Load default resource quotas for each plan type."""
        return {
            PlanType.BASIC: {
                ResourceType.USERS: 100,
                ResourceType.BETS: 1000,
                ResourceType.API_CALLS: 10000,
                ResourceType.STORAGE: 1024,  # MB
                ResourceType.ANALYTICS: 100,
                ResourceType.ML_PREDICTIONS: 100,
                ResourceType.WEBHOOKS: 10
            },
            PlanType.PROFESSIONAL: {
                ResourceType.USERS: 1000,
                ResourceType.BETS: 10000,
                ResourceType.API_CALLS: 100000,
                ResourceType.STORAGE: 10240,  # MB
                ResourceType.ANALYTICS: 1000,
                ResourceType.ML_PREDICTIONS: 1000,
                ResourceType.WEBHOOKS: 100
            },
            PlanType.ENTERPRISE: {
                ResourceType.USERS: 10000,
                ResourceType.BETS: 100000,
                ResourceType.API_CALLS: 1000000,
                ResourceType.STORAGE: 102400,  # MB
                ResourceType.ANALYTICS: 10000,
                ResourceType.ML_PREDICTIONS: 10000,
                ResourceType.WEBHOOKS: 1000
            }
        }

    async def _initialize_default_tenant(self):
        """Initialize default tenant if none exists."""
        try:
            query = "SELECT COUNT(*) as count FROM tenants"
            result = await self.db_manager.fetch_one(query)

            if result['count'] == 0:
                await self.create_tenant(
                    tenant_name="Default Tenant",
                    display_name="Default System Tenant",
                    plan_type=PlanType.ENTERPRISE,
                    contact_email="admin@dbsbm.com"
                )
                logger.info("Default tenant created")
        except Exception as e:
            logger.error(f"Initialize default tenant error: {e}")

    async def _setup_resource_quotas(self):
        """Setup resource quotas for all tenants."""
        try:
            tenants = await self.get_all_tenants()
            for tenant in tenants:
                await self._setup_tenant_quotas(tenant.id, tenant.plan_type)
        except Exception as e:
            logger.error(f"Setup resource quotas error: {e}")

    def _generate_tenant_code(self) -> str:
        """Generate unique tenant code."""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            # Check if code exists (would need async check in real implementation)
            return code

    def _get_plan_features(self, plan_type: PlanType) -> Dict[str, bool]:
        """Get features available for plan type."""
        features = {
            'basic_betting': True,
            'analytics': False,
            'ml_predictions': False,
            'webhooks': False,
            'custom_branding': False,
            'enterprise_integrations': False,
            'compliance_features': False,
            'advanced_security': False
        }

        if plan_type == PlanType.PROFESSIONAL:
            features.update({
                'analytics': True,
                'ml_predictions': True,
                'webhooks': True,
                'custom_branding': True
            })
        elif plan_type == PlanType.ENTERPRISE:
            features.update({
                'analytics': True,
                'ml_predictions': True,
                'webhooks': True,
                'custom_branding': True,
                'enterprise_integrations': True,
                'compliance_features': True,
                'advanced_security': True
            })

        return features

    def _get_default_security_settings(self) -> Dict[str, Any]:
        """Get default security settings."""
        return {
            'mfa_required': False,
            'session_timeout': 24,  # hours
            'password_policy': 'standard',
            'ip_whitelist': [],
            'audit_logging': False
        }

    def _get_default_integration_settings(self) -> Dict[str, Any]:
        """Get default integration settings."""
        return {
            'webhooks_enabled': False,
            'api_rate_limit': 100,
            'third_party_integrations': [],
            'custom_endpoints': []
        }

    def _get_default_notification_settings(self) -> Dict[str, Any]:
        """Get default notification settings."""
        return {
            'email_notifications': True,
            'sms_notifications': False,
            'push_notifications': False,
            'notification_preferences': {
                'bet_confirmation': True,
                'bet_result': True,
                'system_alerts': True,
                'marketing': False
            }
        }

    async def _setup_tenant_quotas(self, tenant_id: int, plan_type: PlanType):
        """Setup resource quotas for a tenant."""
        try:
            quotas = self.default_quotas.get(plan_type, {})

            for resource_type, quota_limit in quotas.items():
                query = """
                    INSERT INTO tenant_resources (tenant_id, resource_type, quota_limit, next_reset)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE quota_limit = VALUES(quota_limit)
                """

                # Set next reset based on reset period
                next_reset = datetime.utcnow() + timedelta(days=30)  # Monthly reset

                await self.db_manager.execute(query, (
                    tenant_id, resource_type.value, quota_limit, next_reset
                ))
        except Exception as e:
            logger.error(f"Setup tenant quotas error: {e}")

    async def _update_tenant_quotas(self, tenant_id: int, new_plan_type: PlanType):
        """Update tenant quotas when plan changes."""
        try:
            quotas = self.default_quotas.get(new_plan_type, {})

            for resource_type, quota_limit in quotas.items():
                query = """
                    UPDATE tenant_resources
                    SET quota_limit = %s
                    WHERE tenant_id = %s AND resource_type = %s
                """
                await self.db_manager.execute(query, (quota_limit, tenant_id, resource_type.value))
        except Exception as e:
            logger.error(f"Update tenant quotas error: {e}")

    async def _setup_default_customizations(self, tenant_id: int, plan_type: PlanType):
        """Setup default customizations for a tenant."""
        try:
            customizations = {
                'branding': {
                    'logo_url': None,
                    'primary_color': '#007bff',
                    'secondary_color': '#6c757d',
                    'company_name': None
                },
                'features': {
                    'enable_chatbot': True,
                    'enable_analytics': plan_type != PlanType.BASIC,
                    'enable_ml': plan_type != PlanType.BASIC,
                    'enable_webhooks': plan_type != PlanType.BASIC
                }
            }

            for customization_type, data in customizations.items():
                await self.update_customization(tenant_id, customization_type, data)
        except Exception as e:
            logger.error(f"Setup default customizations error: {e}")

    async def _setup_tenant_billing(self, tenant_id: int, plan_type: PlanType):
        """Setup billing for a tenant."""
        try:
            billing_amounts = {
                PlanType.BASIC: 29.99,
                PlanType.PROFESSIONAL: 99.99,
                PlanType.ENTERPRISE: 299.99
            }

            amount = billing_amounts.get(plan_type, 0.0)

            query = """
                INSERT INTO tenant_billing (tenant_id, plan_name, billing_cycle, amount, currency, next_billing_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            next_billing = datetime.utcnow() + timedelta(days=30)

            await self.db_manager.execute(query, (
                tenant_id, plan_type.value, 'monthly', amount, 'USD', next_billing
            ))
        except Exception as e:
            logger.error(f"Setup tenant billing error: {e}")

    async def _reset_resource_quota(self, tenant_id: int, resource_type: ResourceType):
        """Reset resource quota for a tenant."""
        try:
            query = """
                UPDATE tenant_resources
                SET current_usage = 0, last_reset = NOW(), next_reset = DATE_ADD(NOW(), INTERVAL 30 DAY)
                WHERE tenant_id = %s AND resource_type = %s
            """
            await self.db_manager.execute(query, (tenant_id, resource_type.value))
        except Exception as e:
            logger.error(f"Reset resource quota error: {e}")
