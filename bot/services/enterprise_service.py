"""
Enterprise Service for DBSBM System.
Provides enterprise-level features and management capabilities.
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

# Enterprise-specific cache TTLs
ENTERPRISE_CACHE_TTLS = {
    'enterprise_configs': 3600,    # 1 hour
    'enterprise_features': 7200,    # 2 hours
    'enterprise_licenses': 1800,    # 30 minutes
    'enterprise_users': 900,        # 15 minutes
    'enterprise_billing': 3600,     # 1 hour
    'enterprise_support': 1800,     # 30 minutes
    'enterprise_analytics': 3600,   # 1 hour
    'enterprise_security': 1800,    # 30 minutes
    'enterprise_compliance': 7200,  # 2 hours
    'enterprise_reports': 3600,     # 1 hour
}

class EnterpriseStatus(Enum):
    """Enterprise status types."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    PENDING = "pending"

class LicenseType(Enum):
    """Enterprise license types."""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class FeatureType(Enum):
    """Enterprise feature types."""
    ADVANCED_ANALYTICS = "advanced_analytics"
    CUSTOM_BRANDING = "custom_branding"
    API_ACCESS = "api_access"
    WHITE_LABEL = "white_label"
    DEDICATED_SUPPORT = "dedicated_support"
    CUSTOM_INTEGRATIONS = "custom_integrations"
    ADVANCED_SECURITY = "advanced_security"
    COMPLIANCE_TOOLS = "compliance_tools"

@dataclass
class EnterpriseConfig:
    """Enterprise configuration."""
    id: int
    tenant_id: int
    company_name: str
    license_type: LicenseType
    max_users: int
    features: List[str]
    status: EnterpriseStatus
    created_at: datetime
    updated_at: datetime

@dataclass
class EnterpriseLicense:
    """Enterprise license information."""
    id: int
    tenant_id: int
    license_key: str
    license_type: LicenseType
    features: List[str]
    max_users: int
    expires_at: datetime
    is_active: bool
    created_at: datetime

@dataclass
class EnterpriseUser:
    """Enterprise user management."""
    id: int
    tenant_id: int
    user_id: int
    role: str
    permissions: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class EnterpriseBilling:
    """Enterprise billing information."""
    id: int
    tenant_id: int
    billing_cycle: str
    amount: float
    currency: str
    status: str
    next_billing_date: datetime
    created_at: datetime

class EnterpriseService:
    """Enterprise service for managing enterprise-level features."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = ENTERPRISE_CACHE_TTLS

        # Background tasks
        self.license_check_task = None
        self.billing_task = None
        self.is_running = False

    async def start(self):
        """Start the enterprise service."""
        try:
            self.is_running = True
            self.license_check_task = asyncio.create_task(self._check_license_expiry())
            self.billing_task = asyncio.create_task(self._process_billing())
            logger.info("Enterprise service started successfully")
        except Exception as e:
            logger.error(f"Failed to start enterprise service: {e}")
            raise

    async def stop(self):
        """Stop the enterprise service."""
        self.is_running = False
        if self.license_check_task:
            self.license_check_task.cancel()
        if self.billing_task:
            self.billing_task.cancel()
        logger.info("Enterprise service stopped")

    @time_operation("enterprise_create_config")
    async def create_enterprise_config(self, tenant_id: int, company_name: str,
                                    license_type: LicenseType, max_users: int,
                                    features: List[str]) -> Optional[EnterpriseConfig]:
        """Create enterprise configuration."""
        try:
            # Generate license key
            license_key = self._generate_license_key()

            query = """
            INSERT INTO enterprise_configs (tenant_id, company_name, license_type, max_users,
                                          features, status, created_at, updated_at)
            VALUES (:tenant_id, :company_name, :license_type, :max_users,
                    :features, :status, NOW(), NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'company_name': company_name,
                'license_type': license_type.value,
                'max_users': max_users,
                'features': json.dumps(features),
                'status': EnterpriseStatus.ACTIVE.value
            })

            config_id = result.lastrowid

            # Create license
            await self._create_enterprise_license(tenant_id, license_key, license_type, features, max_users)

            # Get created config
            config = await self.get_enterprise_config(tenant_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"enterprise_configs:{tenant_id}")
            await self.cache_manager.clear_cache_by_pattern("enterprise_licenses:*")

            record_metric("enterprise_configs_created", 1)
            return config

        except Exception as e:
            logger.error(f"Failed to create enterprise config: {e}")
            return None

    @time_operation("enterprise_get_config")
    async def get_enterprise_config(self, tenant_id: int) -> Optional[EnterpriseConfig]:
        """Get enterprise configuration by tenant ID."""
        try:
            # Try to get from cache first
            cache_key = f"enterprise_configs:{tenant_id}"
            cached_config = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_config:
                return EnterpriseConfig(**cached_config)

            # Get from database
            query = """
            SELECT * FROM enterprise_configs WHERE tenant_id = :tenant_id
            """

            result = await self.db_manager.fetch_one(query, {'tenant_id': tenant_id})

            if not result:
                return None

            config = EnterpriseConfig(
                id=result['id'],
                tenant_id=result['tenant_id'],
                company_name=result['company_name'],
                license_type=LicenseType(result['license_type']),
                max_users=result['max_users'],
                features=json.loads(result['features']) if result['features'] else [],
                status=EnterpriseStatus(result['status']),
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )

            # Cache config
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': config.id,
                    'tenant_id': config.tenant_id,
                    'company_name': config.company_name,
                    'license_type': config.license_type.value,
                    'max_users': config.max_users,
                    'features': config.features,
                    'status': config.status.value,
                    'created_at': config.created_at.isoformat(),
                    'updated_at': config.updated_at.isoformat()
                },
                ttl=self.cache_ttls['enterprise_configs']
            )

            return config

        except Exception as e:
            logger.error(f"Failed to get enterprise config: {e}")
            return None

    @time_operation("enterprise_update_config")
    async def update_enterprise_config(self, tenant_id: int, updates: Dict[str, Any]) -> bool:
        """Update enterprise configuration."""
        try:
            # Build update query dynamically
            update_fields = []
            params = {'tenant_id': tenant_id}

            for field, value in updates.items():
                if field in ['company_name', 'license_type', 'max_users', 'features', 'status']:
                    update_fields.append(f"{field} = :{field}")
                    if field == 'features':
                        params[field] = json.dumps(value)
                    elif field == 'license_type':
                        params[field] = value.value if hasattr(value, 'value') else value
                    elif field == 'status':
                        params[field] = value.value if hasattr(value, 'value') else value
                    else:
                        params[field] = value

            if not update_fields:
                return False

            query = f"""
            UPDATE enterprise_configs
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE tenant_id = :tenant_id
            """

            result = await self.db_manager.execute(query, params)

            if result.rowcount == 0:
                return False

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"enterprise_configs:{tenant_id}")
            await self.cache_manager.clear_cache_by_pattern("enterprise_licenses:*")

            record_metric("enterprise_configs_updated", 1)
            return True

        except Exception as e:
            logger.error(f"Failed to update enterprise config: {e}")
            return False

    @time_operation("enterprise_get_license")
    async def get_enterprise_license(self, tenant_id: int) -> Optional[EnterpriseLicense]:
        """Get enterprise license by tenant ID."""
        try:
            # Try to get from cache first
            cache_key = f"enterprise_licenses:{tenant_id}"
            cached_license = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_license:
                return EnterpriseLicense(**cached_license)

            # Get from database
            query = """
            SELECT * FROM enterprise_licenses
            WHERE tenant_id = :tenant_id AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
            """

            result = await self.db_manager.fetch_one(query, {'tenant_id': tenant_id})

            if not result:
                return None

            license_obj = EnterpriseLicense(
                id=result['id'],
                tenant_id=result['tenant_id'],
                license_key=result['license_key'],
                license_type=LicenseType(result['license_type']),
                features=json.loads(result['features']) if result['features'] else [],
                max_users=result['max_users'],
                expires_at=result['expires_at'],
                is_active=result['is_active'],
                created_at=result['created_at']
            )

            # Cache license
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': license_obj.id,
                    'tenant_id': license_obj.tenant_id,
                    'license_key': license_obj.license_key,
                    'license_type': license_obj.license_type.value,
                    'features': license_obj.features,
                    'max_users': license_obj.max_users,
                    'expires_at': license_obj.expires_at.isoformat(),
                    'is_active': license_obj.is_active,
                    'created_at': license_obj.created_at.isoformat()
                },
                ttl=self.cache_ttls['enterprise_licenses']
            )

            return license_obj

        except Exception as e:
            logger.error(f"Failed to get enterprise license: {e}")
            return None

    @time_operation("enterprise_check_feature")
    async def check_feature_access(self, tenant_id: int, feature: str) -> bool:
        """Check if tenant has access to a specific feature."""
        try:
            # Try to get from cache first
            cache_key = f"enterprise_feature:{tenant_id}:{feature}"
            cached_access = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_access is not None:
                return cached_access

            # Get license
            license_obj = await self.get_enterprise_license(tenant_id)

            if not license_obj:
                return False

            # Check if license is active and not expired
            if not license_obj.is_active or license_obj.expires_at < datetime.utcnow():
                return False

            # Check if feature is included
            has_access = feature in license_obj.features

            # Cache result
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                has_access,
                ttl=self.cache_ttls['enterprise_features']
            )

            return has_access

        except Exception as e:
            logger.error(f"Failed to check feature access: {e}")
            return False

    @time_operation("enterprise_get_users")
    async def get_enterprise_users(self, tenant_id: int, limit: int = 100) -> List[EnterpriseUser]:
        """Get enterprise users for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"enterprise_users:{tenant_id}:{limit}"
            cached_users = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_users:
                return [EnterpriseUser(**user) for user in cached_users]

            # Get from database
            query = """
            SELECT * FROM enterprise_users
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit
            """

            results = await self.db_manager.fetch_all(query, {
                'tenant_id': tenant_id,
                'limit': limit
            })

            users = []
            for row in results:
                user = EnterpriseUser(
                    id=row['id'],
                    tenant_id=row['tenant_id'],
                    user_id=row['user_id'],
                    role=row['role'],
                    permissions=json.loads(row['permissions']) if row['permissions'] else [],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                users.append(user)

            # Cache users
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [{
                    'id': u.id,
                    'tenant_id': u.tenant_id,
                    'user_id': u.user_id,
                    'role': u.role,
                    'permissions': u.permissions,
                    'is_active': u.is_active,
                    'created_at': u.created_at.isoformat(),
                    'updated_at': u.updated_at.isoformat()
                } for u in users],
                ttl=self.cache_ttls['enterprise_users']
            )

            return users

        except Exception as e:
            logger.error(f"Failed to get enterprise users: {e}")
            return []

    @time_operation("enterprise_add_user")
    async def add_enterprise_user(self, tenant_id: int, user_id: int, role: str,
                                permissions: List[str]) -> bool:
        """Add user to enterprise."""
        try:
            query = """
            INSERT INTO enterprise_users (tenant_id, user_id, role, permissions, is_active, created_at, updated_at)
            VALUES (:tenant_id, :user_id, :role, :permissions, 1, NOW(), NOW())
            """

            result = await self.db_manager.execute(query, {
                'tenant_id': tenant_id,
                'user_id': user_id,
                'role': role,
                'permissions': json.dumps(permissions)
            })

            if result.rowcount == 0:
                return False

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(f"enterprise_users:{tenant_id}:*")

            record_metric("enterprise_users_added", 1)
            return True

        except Exception as e:
            logger.error(f"Failed to add enterprise user: {e}")
            return False

    @time_operation("enterprise_get_billing")
    async def get_enterprise_billing(self, tenant_id: int) -> Optional[EnterpriseBilling]:
        """Get enterprise billing information."""
        try:
            # Try to get from cache first
            cache_key = f"enterprise_billing:{tenant_id}"
            cached_billing = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_billing:
                return EnterpriseBilling(**cached_billing)

            # Get from database
            query = """
            SELECT * FROM enterprise_billing
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT 1
            """

            result = await self.db_manager.fetch_one(query, {'tenant_id': tenant_id})

            if not result:
                return None

            billing = EnterpriseBilling(
                id=result['id'],
                tenant_id=result['tenant_id'],
                billing_cycle=result['billing_cycle'],
                amount=result['amount'],
                currency=result['currency'],
                status=result['status'],
                next_billing_date=result['next_billing_date'],
                created_at=result['created_at']
            )

            # Cache billing
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    'id': billing.id,
                    'tenant_id': billing.tenant_id,
                    'billing_cycle': billing.billing_cycle,
                    'amount': billing.amount,
                    'currency': billing.currency,
                    'status': billing.status,
                    'next_billing_date': billing.next_billing_date.isoformat(),
                    'created_at': billing.created_at.isoformat()
                },
                ttl=self.cache_ttls['enterprise_billing']
            )

            return billing

        except Exception as e:
            logger.error(f"Failed to get enterprise billing: {e}")
            return None

    @time_operation("enterprise_get_analytics")
    async def get_enterprise_analytics(self, tenant_id: int, days: int = 30) -> Dict[str, Any]:
        """Get enterprise analytics for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"enterprise_analytics:{tenant_id}:{days}"
            cached_analytics = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_analytics:
                return cached_analytics

            # Get enterprise config
            config = await self.get_enterprise_config(tenant_id)

            # Get license
            license_obj = await self.get_enterprise_license(tenant_id)

            # Get users
            users = await self.get_enterprise_users(tenant_id)

            # Get billing
            billing = await self.get_enterprise_billing(tenant_id)

            analytics = {
                'config': {
                    'company_name': config.company_name if config else None,
                    'license_type': config.license_type.value if config else None,
                    'max_users': config.max_users if config else 0,
                    'active_features': config.features if config else []
                },
                'license': {
                    'is_active': license_obj.is_active if license_obj else False,
                    'expires_at': license_obj.expires_at.isoformat() if license_obj else None,
                    'features': license_obj.features if license_obj else []
                },
                'users': {
                    'total': len(users),
                    'active': len([u for u in users if u.is_active]),
                    'roles': list(set(u.role for u in users))
                },
                'billing': {
                    'cycle': billing.billing_cycle if billing else None,
                    'amount': billing.amount if billing else 0,
                    'currency': billing.currency if billing else None,
                    'status': billing.status if billing else None,
                    'next_billing': billing.next_billing_date.isoformat() if billing else None
                } if billing else None
            }

            # Cache analytics
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                analytics,
                ttl=self.cache_ttls['enterprise_analytics']
            )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get enterprise analytics: {e}")
            return {}

    async def clear_enterprise_cache(self):
        """Clear all enterprise-related cache entries."""
        try:
            await self.cache_manager.clear_cache_by_pattern("enterprise_configs:*")
            await self.cache_manager.clear_cache_by_pattern("enterprise_features:*")
            await self.cache_manager.clear_cache_by_pattern("enterprise_licenses:*")
            await self.cache_manager.clear_cache_by_pattern("enterprise_users:*")
            await self.cache_manager.clear_cache_by_pattern("enterprise_billing:*")
            await self.cache_manager.clear_cache_by_pattern("enterprise_support:*")
            await self.cache_manager.clear_cache_by_pattern("enterprise_analytics:*")
            await self.cache_manager.clear_cache_by_pattern("enterprise_security:*")
            await self.cache_manager.clear_cache_by_pattern("enterprise_compliance:*")
            await self.cache_manager.clear_cache_by_pattern("enterprise_reports:*")
            logger.info("Enterprise cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear enterprise cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get enterprise service cache statistics."""
        try:
            return await self.cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
