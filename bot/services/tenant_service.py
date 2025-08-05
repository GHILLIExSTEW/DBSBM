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
from utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

# Tenant-specific cache TTLs
TENANT_CACHE_TTLS = {
    "tenant_data": 1800,  # 30 minutes
    "tenant_resources": 900,  # 15 minutes
    "tenant_customizations": 3600,  # 1 hour
    "tenant_billing": 7200,  # 2 hours
    "tenant_stats": 1800,  # 30 minutes
    "resource_quotas": 300,  # 5 minutes
    "tenant_list": 900,  # 15 minutes
    "tenant_settings": 3600,  # 1 hour
    "tenant_features": 7200,  # 2 hours
    "tenant_usage": 600,  # 10 minutes
}


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


class TenantService:
    """Multi-tenancy service for managing tenant isolation and resources."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = TENANT_CACHE_TTLS

        # Default quotas for each plan
        self.default_quotas = self._load_default_quotas()

        # Background tasks
        self.cleanup_task = None
        self.is_running = False

    async def start(self):
        """Start the tenant service."""
        try:
            await self._initialize_default_tenant()
            await self._setup_resource_quotas()
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_expired_data())
            logger.info("Tenant service started successfully")
        except Exception as e:
            logger.error(f"Failed to start tenant service: {e}")
            raise

    async def stop(self):
        """Stop the tenant service."""
        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
        logger.info("Tenant service stopped")

    @time_operation("tenant_create_tenant")
    async def create_tenant(
        self,
        tenant_name: str,
        display_name: str,
        plan_type: PlanType,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        custom_domain: Optional[str] = None,
        timezone: str = "UTC",
    ) -> Optional[Tenant]:
        """Create a new tenant."""
        try:
            # Generate unique tenant code
            tenant_code = self._generate_tenant_code()

            # Create tenant record
            query = """
            INSERT INTO tenants (tenant_name, tenant_code, display_name, status, plan_type,
                               contact_email, contact_phone, settings, custom_domain, timezone, created_at, updated_at)
            VALUES (:tenant_name, :tenant_code, :display_name, :status, :plan_type,
                    :contact_email, :contact_phone, :settings, :custom_domain, :timezone, NOW(), NOW())
            """

            settings = {
                "features": self._get_plan_features(plan_type),
                "security": self._get_default_security_settings(),
                "integrations": self._get_default_integration_settings(),
                "notifications": self._get_default_notification_settings(),
            }

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_name": tenant_name,
                    "tenant_code": tenant_code,
                    "display_name": display_name,
                    "status": TenantStatus.ACTIVE.value,
                    "plan_type": plan_type.value,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "settings": json.dumps(settings),
                    "custom_domain": custom_domain,
                    "timezone": timezone,
                },
            )

            tenant_id = result.lastrowid

            # Setup tenant quotas
            await self._setup_tenant_quotas(tenant_id, plan_type)

            # Setup default customizations
            await self._setup_default_customizations(tenant_id, plan_type)

            # Setup billing
            await self._setup_tenant_billing(tenant_id, plan_type)

            # Get created tenant
            tenant = await self.get_tenant_by_id(tenant_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern("tenant_list:*")
            await self.cache_manager.clear_cache_by_pattern("tenant_stats:*")

            record_metric("tenants_created", 1)
            return tenant

        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            return None

    @time_operation("tenant_get_tenant")
    async def get_tenant_by_id(self, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID."""
        try:
            # Try to get from cache first
            cache_key = f"tenant_data:{tenant_id}"
            cached_tenant = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_tenant:
                return Tenant(**cached_tenant)

            # Get from database
            query = """
            SELECT * FROM tenants WHERE id = :tenant_id
            """

            result = await self.db_manager.fetch_one(query, {"tenant_id": tenant_id})

            if not result:
                return None

            tenant = Tenant(
                id=result["id"],
                tenant_name=result["tenant_name"],
                tenant_code=result["tenant_code"],
                display_name=result["display_name"],
                status=TenantStatus(result["status"]),
                plan_type=PlanType(result["plan_type"]),
                contact_email=result["contact_email"],
                contact_phone=result["contact_phone"],
                settings=json.loads(result["settings"]) if result["settings"] else {},
                custom_domain=result["custom_domain"],
                timezone=result["timezone"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )

            # Cache tenant data
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": tenant.id,
                    "tenant_name": tenant.tenant_name,
                    "tenant_code": tenant.tenant_code,
                    "display_name": tenant.display_name,
                    "status": tenant.status.value,
                    "plan_type": tenant.plan_type.value,
                    "contact_email": tenant.contact_email,
                    "contact_phone": tenant.contact_phone,
                    "settings": tenant.settings,
                    "custom_domain": tenant.custom_domain,
                    "timezone": tenant.timezone,
                    "created_at": tenant.created_at.isoformat(),
                    "updated_at": tenant.updated_at.isoformat(),
                },
                ttl=self.cache_ttls["tenant_data"],
            )

            return tenant

        except Exception as e:
            logger.error(f"Failed to get tenant by ID: {e}")
            return None

    @time_operation("tenant_get_tenant_by_code")
    async def get_tenant_by_code(self, tenant_code: str) -> Optional[Tenant]:
        """Get tenant by tenant code."""
        try:
            # Try to get from cache first
            cache_key = f"tenant_by_code:{tenant_code}"
            cached_tenant_id = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_tenant_id:
                return await self.get_tenant_by_id(cached_tenant_id)

            # Get from database
            query = """
            SELECT id FROM tenants WHERE tenant_code = :tenant_code
            """

            result = await self.db_manager.fetch_one(
                query, {"tenant_code": tenant_code}
            )

            if not result:
                return None

            # Cache tenant ID mapping
            await self.cache_manager.enhanced_cache_set(
                cache_key, result["id"], ttl=self.cache_ttls["tenant_data"]
            )

            return await self.get_tenant_by_id(result["id"])

        except Exception as e:
            logger.error(f"Failed to get tenant by code: {e}")
            return None

    @time_operation("tenant_update_tenant")
    async def update_tenant(self, tenant_id: int, updates: Dict[str, Any]) -> bool:
        """Update tenant information."""
        try:
            # Build update query dynamically
            update_fields = []
            params = {"tenant_id": tenant_id}

            for field, value in updates.items():
                if field in [
                    "tenant_name",
                    "display_name",
                    "status",
                    "plan_type",
                    "contact_email",
                    "contact_phone",
                    "custom_domain",
                    "timezone",
                ]:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = value
                elif field == "settings":
                    update_fields.append("settings = :settings")
                    params["settings"] = json.dumps(value)

            if not update_fields:
                return False

            query = f"""
            UPDATE tenants
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = :tenant_id
            """

            result = await self.db_manager.execute(query, params)

            if result.rowcount == 0:
                return False

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"tenant_data:{tenant_id}")
            await self.cache_manager.clear_cache_by_pattern("tenant_list:*")
            await self.cache_manager.clear_cache_by_pattern("tenant_stats:*")

            # If plan type changed, update quotas
            if "plan_type" in updates:
                await self._update_tenant_quotas(
                    tenant_id, PlanType(updates["plan_type"])
                )

            record_metric("tenants_updated", 1)
            return True

        except Exception as e:
            logger.error(f"Failed to update tenant: {e}")
            return False

    @time_operation("tenant_delete_tenant")
    async def delete_tenant(self, tenant_id: int) -> bool:
        """Delete a tenant."""
        try:
            # Soft delete - mark as inactive
            query = """
            UPDATE tenants SET status = :status, updated_at = NOW()
            WHERE id = :tenant_id
            """

            result = await self.db_manager.execute(
                query, {"tenant_id": tenant_id, "status": TenantStatus.INACTIVE.value}
            )

            if result.rowcount == 0:
                return False

            # Clear all related cache
            await self.cache_manager.clear_cache_by_pattern(f"tenant_data:{tenant_id}")
            await self.cache_manager.clear_cache_by_pattern(
                f"tenant_resources:{tenant_id}:*"
            )
            await self.cache_manager.clear_cache_by_pattern(
                f"tenant_customizations:{tenant_id}:*"
            )
            await self.cache_manager.clear_cache_by_pattern(
                f"tenant_billing:{tenant_id}"
            )
            await self.cache_manager.clear_cache_by_pattern(f"tenant_stats:{tenant_id}")
            await self.cache_manager.clear_cache_by_pattern("tenant_list:*")

            record_metric("tenants_deleted", 1)
            return True

        except Exception as e:
            logger.error(f"Failed to delete tenant: {e}")
            return False

    @time_operation("tenant_get_resource_usage")
    async def get_resource_usage(self, tenant_id: int) -> Dict[str, TenantResource]:
        """Get resource usage for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"tenant_resources:{tenant_id}"
            cached_resources = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_resources:
                return {
                    resource_type: TenantResource(**resource)
                    for resource_type, resource in cached_resources.items()
                }

            # Get from database
            query = """
            SELECT * FROM tenant_resources
            WHERE tenant_id = :tenant_id AND is_active = 1
            """

            results = await self.db_manager.fetch_all(query, {"tenant_id": tenant_id})

            resources = {}
            for row in results:
                resource = TenantResource(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    resource_type=ResourceType(row["resource_type"]),
                    quota_limit=row["quota_limit"],
                    current_usage=row["current_usage"],
                    reset_period=row["reset_period"],
                    last_reset=row["last_reset"],
                    next_reset=row["next_reset"],
                    is_active=row["is_active"],
                )
                resources[resource.resource_type.value] = resource

            # Cache resources
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    resource_type: {
                        "id": resource.id,
                        "tenant_id": resource.tenant_id,
                        "resource_type": resource.resource_type.value,
                        "quota_limit": resource.quota_limit,
                        "current_usage": resource.current_usage,
                        "reset_period": resource.reset_period,
                        "last_reset": resource.last_reset.isoformat(),
                        "next_reset": resource.next_reset.isoformat(),
                        "is_active": resource.is_active,
                    }
                    for resource_type, resource in resources.items()
                },
                ttl=self.cache_ttls["tenant_resources"],
            )

            return resources

        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            return {}

    @time_operation("tenant_check_resource_quota")
    async def check_resource_quota(
        self, tenant_id: int, resource_type: ResourceType, required_amount: int = 1
    ) -> bool:
        """Check if tenant has sufficient resource quota."""
        try:
            # Try to get from cache first
            cache_key = f"resource_quota:{tenant_id}:{resource_type.value}"
            cached_quota = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_quota:
                return cached_quota["available"] >= required_amount

            # Get current usage
            resources = await self.get_resource_usage(tenant_id)
            resource = resources.get(resource_type.value)

            if not resource:
                return False

            # Check if quota is available
            available = resource.quota_limit - resource.current_usage
            has_quota = available >= required_amount

            # Cache quota check
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {"available": available, "has_quota": has_quota},
                ttl=self.cache_ttls["resource_quotas"],
            )

            return has_quota

        except Exception as e:
            logger.error(f"Failed to check resource quota: {e}")
            return False

    @time_operation("tenant_increment_resource_usage")
    async def increment_resource_usage(
        self, tenant_id: int, resource_type: ResourceType, amount: int = 1
    ) -> bool:
        """Increment resource usage for a tenant."""
        try:
            # Update database
            query = """
            UPDATE tenant_resources
            SET current_usage = current_usage + :amount, updated_at = NOW()
            WHERE tenant_id = :tenant_id AND resource_type = :resource_type AND is_active = 1
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": tenant_id,
                    "resource_type": resource_type.value,
                    "amount": amount,
                },
            )

            if result.rowcount == 0:
                return False

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(
                f"tenant_resources:{tenant_id}"
            )
            await self.cache_manager.clear_cache_by_pattern(
                f"resource_quota:{tenant_id}:{resource_type.value}"
            )
            await self.cache_manager.clear_cache_by_pattern(f"tenant_stats:{tenant_id}")

            record_metric("resource_usage_incremented", 1)
            return True

        except Exception as e:
            logger.error(f"Failed to increment resource usage: {e}")
            return False

    @time_operation("tenant_get_customizations")
    async def get_customizations(self, tenant_id: int) -> List[TenantCustomization]:
        """Get customizations for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"tenant_customizations:{tenant_id}"
            cached_customizations = await self.cache_manager.enhanced_cache_get(
                cache_key
            )

            if cached_customizations:
                return [
                    TenantCustomization(**customization)
                    for customization in cached_customizations
                ]

            # Get from database
            query = """
            SELECT * FROM tenant_customizations
            WHERE tenant_id = :tenant_id AND is_active = 1
            """

            results = await self.db_manager.fetch_all(query, {"tenant_id": tenant_id})

            customizations = []
            for row in results:
                customization = TenantCustomization(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    customization_type=row["customization_type"],
                    customization_data=(
                        json.loads(row["customization_data"])
                        if row["customization_data"]
                        else {}
                    ),
                    is_active=row["is_active"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                customizations.append(customization)

            # Cache customizations
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [
                    {
                        "id": c.id,
                        "tenant_id": c.tenant_id,
                        "customization_type": c.customization_type,
                        "customization_data": c.customization_data,
                        "is_active": c.is_active,
                        "created_at": c.created_at.isoformat(),
                        "updated_at": c.updated_at.isoformat(),
                    }
                    for c in customizations
                ],
                ttl=self.cache_ttls["tenant_customizations"],
            )

            return customizations

        except Exception as e:
            logger.error(f"Failed to get customizations: {e}")
            return []

    @time_operation("tenant_update_customization")
    async def update_customization(
        self,
        tenant_id: int,
        customization_type: str,
        customization_data: Dict[str, Any],
    ) -> bool:
        """Update customization for a tenant."""
        try:
            # Check if customization exists
            query = """
            SELECT id FROM tenant_customizations
            WHERE tenant_id = :tenant_id AND customization_type = :customization_type
            """

            existing = await self.db_manager.fetch_one(
                query,
                {"tenant_id": tenant_id, "customization_type": customization_type},
            )

            if existing:
                # Update existing
                update_query = """
                UPDATE tenant_customizations
                SET customization_data = :customization_data, updated_at = NOW()
                WHERE tenant_id = :tenant_id AND customization_type = :customization_type
                """
            else:
                # Create new
                update_query = """
                INSERT INTO tenant_customizations (tenant_id, customization_type, customization_data, is_active, created_at, updated_at)
                VALUES (:tenant_id, :customization_type, :customization_data, 1, NOW(), NOW())
                """

            await self.db_manager.execute(
                update_query,
                {
                    "tenant_id": tenant_id,
                    "customization_type": customization_type,
                    "customization_data": json.dumps(customization_data),
                },
            )

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(
                f"tenant_customizations:{tenant_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to update customization: {e}")
            return False

    @time_operation("tenant_get_billing_info")
    async def get_billing_info(self, tenant_id: int) -> Optional[TenantBilling]:
        """Get billing information for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"tenant_billing:{tenant_id}"
            cached_billing = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_billing:
                return TenantBilling(**cached_billing)

            # Get from database
            query = """
            SELECT * FROM tenant_billing
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT 1
            """

            result = await self.db_manager.fetch_one(query, {"tenant_id": tenant_id})

            if not result:
                return None

            billing = TenantBilling(
                id=result["id"],
                tenant_id=result["tenant_id"],
                plan_name=result["plan_name"],
                billing_cycle=result["billing_cycle"],
                amount=result["amount"],
                currency=result["currency"],
                status=result["status"],
                next_billing_date=result["next_billing_date"],
                created_at=result["created_at"],
            )

            # Cache billing info
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": billing.id,
                    "tenant_id": billing.tenant_id,
                    "plan_name": billing.plan_name,
                    "billing_cycle": billing.billing_cycle,
                    "amount": billing.amount,
                    "currency": billing.currency,
                    "status": billing.status,
                    "next_billing_date": billing.next_billing_date.isoformat(),
                    "created_at": billing.created_at.isoformat(),
                },
                ttl=self.cache_ttls["tenant_billing"],
            )

            return billing

        except Exception as e:
            logger.error(f"Failed to get billing info: {e}")
            return None

    @time_operation("tenant_get_all_tenants")
    async def get_all_tenants(
        self,
        status: Optional[TenantStatus] = None,
        plan_type: Optional[PlanType] = None,
        limit: int = 100,
    ) -> List[Tenant]:
        """Get all tenants with optional filtering."""
        try:
            # Try to get from cache first
            cache_key = f"tenant_list:{status.value if status else 'all'}:{plan_type.value if plan_type else 'all'}:{limit}"
            cached_tenants = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_tenants:
                return [Tenant(**tenant) for tenant in cached_tenants]

            # Build query
            query = "SELECT * FROM tenants WHERE 1=1"
            params = {}

            if status:
                query += " AND status = :status"
                params["status"] = status.value

            if plan_type:
                query += " AND plan_type = :plan_type"
                params["plan_type"] = plan_type.value

            query += " ORDER BY created_at DESC LIMIT :limit"
            params["limit"] = limit

            results = await self.db_manager.fetch_all(query, params)

            tenants = []
            for row in results:
                tenant = Tenant(
                    id=row["id"],
                    tenant_name=row["tenant_name"],
                    tenant_code=row["tenant_code"],
                    display_name=row["display_name"],
                    status=TenantStatus(row["status"]),
                    plan_type=PlanType(row["plan_type"]),
                    contact_email=row["contact_email"],
                    contact_phone=row["contact_phone"],
                    settings=json.loads(row["settings"]) if row["settings"] else {},
                    custom_domain=row["custom_domain"],
                    timezone=row["timezone"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                tenants.append(tenant)

            # Cache tenant list
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [
                    {
                        "id": tenant.id,
                        "tenant_name": tenant.tenant_name,
                        "tenant_code": tenant.tenant_code,
                        "display_name": tenant.display_name,
                        "status": tenant.status.value,
                        "plan_type": tenant.plan_type.value,
                        "contact_email": tenant.contact_email,
                        "contact_phone": tenant.contact_phone,
                        "settings": tenant.settings,
                        "custom_domain": tenant.custom_domain,
                        "timezone": tenant.timezone,
                        "created_at": tenant.created_at.isoformat(),
                        "updated_at": tenant.updated_at.isoformat(),
                    }
                    for tenant in tenants
                ],
                ttl=self.cache_ttls["tenant_list"],
            )

            return tenants

        except Exception as e:
            logger.error(f"Failed to get all tenants: {e}")
            return []

    @time_operation("tenant_get_tenant_stats")
    async def get_tenant_stats(self, tenant_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"tenant_stats:{tenant_id}"
            cached_stats = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_stats:
                return cached_stats

            # Get tenant info
            tenant = await self.get_tenant_by_id(tenant_id)
            if not tenant:
                return {}

            # Get resource usage
            resources = await self.get_resource_usage(tenant_id)

            # Get customizations
            customizations = await self.get_customizations(tenant_id)

            # Get billing info
            billing = await self.get_billing_info(tenant_id)

            # Calculate statistics
            total_resources = len(resources)
            active_resources = len([r for r in resources.values() if r.is_active])
            usage_percentages = {}

            for resource_type, resource in resources.items():
                if resource.quota_limit > 0:
                    usage_percentages[resource_type] = (
                        resource.current_usage / resource.quota_limit
                    ) * 100

            stats = {
                "tenant_info": {
                    "id": tenant.id,
                    "name": tenant.tenant_name,
                    "display_name": tenant.display_name,
                    "status": tenant.status.value,
                    "plan_type": tenant.plan_type.value,
                    "created_at": tenant.created_at.isoformat(),
                },
                "resources": {
                    "total": total_resources,
                    "active": active_resources,
                    "usage_percentages": usage_percentages,
                    "details": {
                        resource_type: {
                            "quota_limit": resource.quota_limit,
                            "current_usage": resource.current_usage,
                            "available": resource.quota_limit - resource.current_usage,
                            "usage_percentage": (
                                (resource.current_usage / resource.quota_limit * 100)
                                if resource.quota_limit > 0
                                else 0
                            ),
                        }
                        for resource_type, resource in resources.items()
                    },
                },
                "customizations": {
                    "total": len(customizations),
                    "active": len([c for c in customizations if c.is_active]),
                    "types": list(set(c.customization_type for c in customizations)),
                },
                "billing": (
                    {
                        "plan_name": billing.plan_name if billing else None,
                        "billing_cycle": billing.billing_cycle if billing else None,
                        "amount": billing.amount if billing else None,
                        "currency": billing.currency if billing else None,
                        "status": billing.status if billing else None,
                        "next_billing_date": (
                            billing.next_billing_date.isoformat() if billing else None
                        ),
                    }
                    if billing
                    else None
                ),
            }

            # Cache stats
            await self.cache_manager.enhanced_cache_set(
                cache_key, stats, ttl=self.cache_ttls["tenant_stats"]
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to get tenant stats: {e}")
            return {}

    async def clear_tenant_cache(self):
        """Clear all tenant-related cache entries."""
        try:
            await self.cache_manager.clear_cache_by_pattern("tenant_data:*")
            await self.cache_manager.clear_cache_by_pattern("tenant_by_code:*")
            await self.cache_manager.clear_cache_by_pattern("tenant_resources:*")
            await self.cache_manager.clear_cache_by_pattern("tenant_customizations:*")
            await self.cache_manager.clear_cache_by_pattern("tenant_billing:*")
            await self.cache_manager.clear_cache_by_pattern("tenant_stats:*")
            await self.cache_manager.clear_cache_by_pattern("tenant_list:*")
            await self.cache_manager.clear_cache_by_pattern("resource_quota:*")
            logger.info("Tenant cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear tenant cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get tenant service cache statistics."""
        try:
            return await self.cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
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
                ResourceType.WEBHOOKS: 10,
            },
            PlanType.PROFESSIONAL: {
                ResourceType.USERS: 1000,
                ResourceType.BETS: 10000,
                ResourceType.API_CALLS: 100000,
                ResourceType.STORAGE: 10240,  # MB
                ResourceType.ANALYTICS: 1000,
                ResourceType.ML_PREDICTIONS: 1000,
                ResourceType.WEBHOOKS: 100,
            },
            PlanType.ENTERPRISE: {
                ResourceType.USERS: 10000,
                ResourceType.BETS: 100000,
                ResourceType.API_CALLS: 1000000,
                ResourceType.STORAGE: 102400,  # MB
                ResourceType.ANALYTICS: 10000,
                ResourceType.ML_PREDICTIONS: 10000,
                ResourceType.WEBHOOKS: 1000,
            },
        }

    async def _initialize_default_tenant(self):
        """Initialize default tenant if none exists."""
        try:
            query = "SELECT COUNT(*) as count FROM tenants"
            result = await self.db_manager.fetch_one(query)

            if result["count"] == 0:
                await self.create_tenant(
                    tenant_name="Default Tenant",
                    display_name="Default System Tenant",
                    plan_type=PlanType.ENTERPRISE,
                    contact_email="admin@dbsbm.com",
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
            code = "".join(
                secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)
            )
            # Check if code exists (would need async check in real implementation)
            return code

    def _get_plan_features(self, plan_type: PlanType) -> Dict[str, bool]:
        """Get features available for plan type."""
        features = {
            "basic_betting": True,
            "analytics": False,
            "ml_predictions": False,
            "webhooks": False,
            "custom_branding": False,
            "enterprise_integrations": False,
            "compliance_features": False,
            "advanced_security": False,
        }

        if plan_type == PlanType.PROFESSIONAL:
            features.update(
                {
                    "analytics": True,
                    "ml_predictions": True,
                    "webhooks": True,
                    "custom_branding": True,
                }
            )
        elif plan_type == PlanType.ENTERPRISE:
            features.update(
                {
                    "analytics": True,
                    "ml_predictions": True,
                    "webhooks": True,
                    "custom_branding": True,
                    "enterprise_integrations": True,
                    "compliance_features": True,
                    "advanced_security": True,
                }
            )

        return features

    def _get_default_security_settings(self) -> Dict[str, Any]:
        """Get default security settings."""
        return {
            "mfa_required": False,
            "session_timeout": 24,  # hours
            "password_policy": "standard",
            "ip_whitelist": [],
            "audit_logging": False,
        }

    def _get_default_integration_settings(self) -> Dict[str, Any]:
        """Get default integration settings."""
        return {
            "webhooks_enabled": False,
            "api_rate_limit": 100,
            "third_party_integrations": [],
            "custom_endpoints": [],
        }

    def _get_default_notification_settings(self) -> Dict[str, Any]:
        """Get default notification settings."""
        return {
            "email_notifications": True,
            "sms_notifications": False,
            "push_notifications": False,
            "notification_preferences": {
                "bet_confirmation": True,
                "bet_result": True,
                "system_alerts": True,
                "marketing": False,
            },
        }

    async def _setup_tenant_quotas(self, tenant_id: int, plan_type: PlanType):
        """Setup resource quotas for a tenant."""
        try:
            quotas = self.default_quotas.get(plan_type, {})

            for resource_type, quota_limit in quotas.items():
                query = """
                    INSERT INTO tenant_resources (tenant_id, resource_type, quota_limit, next_reset)
                    VALUES ($1, $2, $3, $4)
                    ON DUPLICATE KEY UPDATE quota_limit = VALUES(quota_limit)
                """

                # Set next reset based on reset period
                next_reset = datetime.utcnow() + timedelta(days=30)  # Monthly reset

                await self.db_manager.execute(
                    query, (tenant_id, resource_type.value, quota_limit, next_reset)
                )
        except Exception as e:
            logger.error(f"Setup tenant quotas error: {e}")

    async def _update_tenant_quotas(self, tenant_id: int, new_plan_type: PlanType):
        """Update tenant quotas when plan changes."""
        try:
            quotas = self.default_quotas.get(new_plan_type, {})

            for resource_type, quota_limit in quotas.items():
                query = """
                    UPDATE tenant_resources
                    SET quota_limit = $1
                    WHERE tenant_id = $1 AND resource_type = $2
                """
                await self.db_manager.execute(
                    query, (quota_limit, tenant_id, resource_type.value)
                )
        except Exception as e:
            logger.error(f"Update tenant quotas error: {e}")

    async def _setup_default_customizations(self, tenant_id: int, plan_type: PlanType):
        """Setup default customizations for a tenant."""
        try:
            customizations = {
                "branding": {
                    "logo_url": None,
                    "primary_color": "#007bff",
                    "secondary_color": "#6c757d",
                    "company_name": None,
                },
                "features": {
                    "enable_chatbot": True,
                    "enable_analytics": plan_type != PlanType.BASIC,
                    "enable_ml": plan_type != PlanType.BASIC,
                    "enable_webhooks": plan_type != PlanType.BASIC,
                },
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
                PlanType.ENTERPRISE: 299.99,
            }

            amount = billing_amounts.get(plan_type, 0.0)

            query = """
                INSERT INTO tenant_billing (tenant_id, plan_name, billing_cycle, amount, currency, next_billing_date)
                VALUES ($1, $2, $3, $4, $5, $6)
            """

            next_billing = datetime.utcnow() + timedelta(days=30)

            await self.db_manager.execute(
                query,
                (tenant_id, plan_type.value, "monthly", amount, "USD", next_billing),
            )
        except Exception as e:
            logger.error(f"Setup tenant billing error: {e}")

    async def _reset_resource_quota(self, tenant_id: int, resource_type: ResourceType):
        """Reset resource quota for a tenant."""
        try:
            query = """
                UPDATE tenant_resources
                SET current_usage = 0, last_reset = NOW(), next_reset = DATE_ADD(NOW(), INTERVAL 30 DAY)
                WHERE tenant_id = $1 AND resource_type = $2
            """
            await self.db_manager.execute(query, (tenant_id, resource_type.value))
        except Exception as e:
            logger.error(f"Reset resource quota error: {e}")
