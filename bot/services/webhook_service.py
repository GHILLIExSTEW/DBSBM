"""
Webhook Service for DBSBM System.
Manages webhook delivery, retry logic, and webhook configurations.
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
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

# Webhook-specific cache TTLs
WEBHOOK_CACHE_TTLS = {
    "webhook_configs": 1800,  # 30 minutes
    "webhook_deliveries": 900,  # 15 minutes
    "webhook_events": 600,  # 10 minutes
    "webhook_stats": 1800,  # 30 minutes
    "webhook_retries": 300,  # 5 minutes
    "webhook_secrets": 3600,  # 1 hour
    "webhook_endpoints": 1800,  # 30 minutes
    "webhook_logs": 7200,  # 2 hours
    "webhook_health": 300,  # 5 minutes
    "webhook_performance": 600,  # 10 minutes
}


class WebhookStatus(Enum):
    """Webhook status types."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class DeliveryStatus(Enum):
    """Webhook delivery status."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    EXPIRED = "expired"


class EventType(Enum):
    """Webhook event types."""

    BET_PLACED = "bet_placed"
    BET_SETTLED = "bet_settled"
    USER_REGISTERED = "user_registered"
    PAYMENT_PROCESSED = "payment_processed"
    GAME_STARTED = "game_started"
    GAME_FINISHED = "game_finished"
    SYSTEM_ALERT = "system_alert"
    CUSTOM = "custom"


@dataclass
class WebhookConfig:
    """Webhook configuration."""

    id: int
    tenant_id: int
    name: str
    url: str
    secret: str
    events: List[str]
    status: WebhookStatus
    retry_count: int
    timeout: int
    created_at: datetime
    updated_at: datetime


@dataclass
class WebhookDelivery:
    """Webhook delivery record."""

    id: int
    webhook_id: int
    event_type: str
    payload: Dict[str, Any]
    status: DeliveryStatus
    response_code: Optional[int]
    response_body: Optional[str]
    retry_count: int
    next_retry: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime


@dataclass
class WebhookEvent:
    """Webhook event data."""

    id: int
    event_type: str
    tenant_id: int
    data: Dict[str, Any]
    processed: bool
    created_at: datetime


class WebhookService:
    """Webhook service for managing webhook delivery and configurations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

        # Initialize enhanced cache manager
        self.cache_manager = EnhancedCacheManager()
        self.cache_ttls = WEBHOOK_CACHE_TTLS

        # Background tasks
        self.delivery_task = None
        self.retry_task = None
        self.is_running = False

    async def start(self):
        """Start the webhook service."""
        try:
            self.is_running = True
            self.delivery_task = asyncio.create_task(self._process_webhook_queue())
            self.retry_task = asyncio.create_task(self._process_retry_queue())
            logger.info("Webhook service started successfully")
        except Exception as e:
            logger.error(f"Failed to start webhook service: {e}")
            raise

    async def stop(self):
        """Stop the webhook service."""
        self.is_running = False
        if self.delivery_task:
            self.delivery_task.cancel()
        if self.retry_task:
            self.retry_task.cancel()
        logger.info("Webhook service stopped")

    @time_operation("webhook_create_webhook")
    async def create_webhook(
        self,
        tenant_id: int,
        name: str,
        url: str,
        events: List[str],
        retry_count: int = 3,
        timeout: int = 30,
    ) -> Optional[WebhookConfig]:
        """Create a new webhook configuration."""
        try:
            # Generate webhook secret
            secret = self._generate_webhook_secret()

            query = """
            INSERT INTO webhook_configs (tenant_id, name, url, secret, events, status,
                                       retry_count, timeout, created_at, updated_at)
            VALUES (:tenant_id, :name, :url, :secret, :events, :status,
                    :retry_count, :timeout, NOW(), NOW())
            """

            result = await self.db_manager.execute(
                query,
                {
                    "tenant_id": tenant_id,
                    "name": name,
                    "url": url,
                    "secret": secret,
                    "events": json.dumps(events),
                    "status": WebhookStatus.ACTIVE.value,
                    "retry_count": retry_count,
                    "timeout": timeout,
                },
            )

            webhook_id = result.lastrowid

            # Get created webhook
            webhook = await self.get_webhook_by_id(webhook_id)

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(
                f"webhook_configs:{tenant_id}:*"
            )
            await self.cache_manager.clear_cache_by_pattern("webhook_endpoints:*")

            record_metric("webhooks_created", 1)
            return webhook

        except Exception as e:
            logger.error(f"Failed to create webhook: {e}")
            return None

    @time_operation("webhook_get_webhook")
    async def get_webhook_by_id(self, webhook_id: int) -> Optional[WebhookConfig]:
        """Get webhook configuration by ID."""
        try:
            # Try to get from cache first
            cache_key = f"webhook_config:{webhook_id}"
            cached_webhook = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_webhook:
                return WebhookConfig(**cached_webhook)

            # Get from database
            query = """
            SELECT * FROM webhook_configs WHERE id = :webhook_id
            """

            result = await self.db_manager.fetch_one(query, {"webhook_id": webhook_id})

            if not result:
                return None

            webhook = WebhookConfig(
                id=result["id"],
                tenant_id=result["tenant_id"],
                name=result["name"],
                url=result["url"],
                secret=result["secret"],
                events=json.loads(result["events"]) if result["events"] else [],
                status=WebhookStatus(result["status"]),
                retry_count=result["retry_count"],
                timeout=result["timeout"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )

            # Cache webhook config
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                {
                    "id": webhook.id,
                    "tenant_id": webhook.tenant_id,
                    "name": webhook.name,
                    "url": webhook.url,
                    "secret": webhook.secret,
                    "events": webhook.events,
                    "status": webhook.status.value,
                    "retry_count": webhook.retry_count,
                    "timeout": webhook.timeout,
                    "created_at": webhook.created_at.isoformat(),
                    "updated_at": webhook.updated_at.isoformat(),
                },
                ttl=self.cache_ttls["webhook_configs"],
            )

            return webhook

        except Exception as e:
            logger.error(f"Failed to get webhook by ID: {e}")
            return None

    @time_operation("webhook_get_webhooks")
    async def get_webhooks_by_tenant(
        self, tenant_id: int, status: Optional[WebhookStatus] = None
    ) -> List[WebhookConfig]:
        """Get webhooks for a tenant."""
        try:
            # Try to get from cache first
            cache_key = (
                f"webhook_configs:{tenant_id}:{status.value if status else 'all'}"
            )
            cached_webhooks = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_webhooks:
                return [WebhookConfig(**webhook) for webhook in cached_webhooks]

            # Build query
            query = "SELECT * FROM webhook_configs WHERE tenant_id = :tenant_id"
            params = {"tenant_id": tenant_id}

            if status:
                query += " AND status = :status"
                params["status"] = status.value

            results = await self.db_manager.fetch_all(query, params)

            webhooks = []
            for row in results:
                webhook = WebhookConfig(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    name=row["name"],
                    url=row["url"],
                    secret=row["secret"],
                    events=json.loads(row["events"]) if row["events"] else [],
                    status=WebhookStatus(row["status"]),
                    retry_count=row["retry_count"],
                    timeout=row["timeout"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                webhooks.append(webhook)

            # Cache webhook configs
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [
                    {
                        "id": w.id,
                        "tenant_id": w.tenant_id,
                        "name": w.name,
                        "url": w.url,
                        "secret": w.secret,
                        "events": w.events,
                        "status": w.status.value,
                        "retry_count": w.retry_count,
                        "timeout": w.timeout,
                        "created_at": w.created_at.isoformat(),
                        "updated_at": w.updated_at.isoformat(),
                    }
                    for w in webhooks
                ],
                ttl=self.cache_ttls["webhook_configs"],
            )

            return webhooks

        except Exception as e:
            logger.error(f"Failed to get webhooks by tenant: {e}")
            return []

    @time_operation("webhook_update_webhook")
    async def update_webhook(self, webhook_id: int, updates: Dict[str, Any]) -> bool:
        """Update webhook configuration."""
        try:
            # Build update query dynamically
            update_fields = []
            params = {"webhook_id": webhook_id}

            for field, value in updates.items():
                if field in [
                    "name",
                    "url",
                    "events",
                    "status",
                    "retry_count",
                    "timeout",
                ]:
                    update_fields.append(f"{field} = :{field}")
                    if field == "events":
                        params[field] = json.dumps(value)
                    elif field == "status":
                        params[field] = (
                            value.value if hasattr(value, "value") else value
                        )
                    else:
                        params[field] = value

            if not update_fields:
                return False

            query = f"""
            UPDATE webhook_configs
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = :webhook_id
            """

            result = await self.db_manager.execute(query, params)

            if result.rowcount == 0:
                return False

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(
                f"webhook_config:{webhook_id}"
            )
            await self.cache_manager.clear_cache_by_pattern("webhook_configs:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_endpoints:*")

            record_metric("webhooks_updated", 1)
            return True

        except Exception as e:
            logger.error(f"Failed to update webhook: {e}")
            return False

    @time_operation("webhook_delete_webhook")
    async def delete_webhook(self, webhook_id: int) -> bool:
        """Delete a webhook configuration."""
        try:
            query = """
            UPDATE webhook_configs SET status = :status, updated_at = NOW()
            WHERE id = :webhook_id
            """

            result = await self.db_manager.execute(
                query,
                {"webhook_id": webhook_id, "status": WebhookStatus.INACTIVE.value},
            )

            if result.rowcount == 0:
                return False

            # Clear related cache
            await self.cache_manager.clear_cache_by_pattern(
                f"webhook_config:{webhook_id}"
            )
            await self.cache_manager.clear_cache_by_pattern("webhook_configs:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_endpoints:*")

            record_metric("webhooks_deleted", 1)
            return True

        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False

    @time_operation("webhook_send_event")
    async def send_event(
        self, tenant_id: int, event_type: str, data: Dict[str, Any]
    ) -> bool:
        """Send a webhook event to all configured webhooks for a tenant."""
        try:
            # Get active webhooks for tenant
            webhooks = await self.get_webhooks_by_tenant(
                tenant_id, WebhookStatus.ACTIVE
            )

            if not webhooks:
                return True  # No webhooks configured, consider success

            # Filter webhooks that handle this event type
            relevant_webhooks = [w for w in webhooks if event_type in w.events]

            if not relevant_webhooks:
                return True  # No webhooks for this event type

            # Create webhook event record
            event_id = await self._create_webhook_event(tenant_id, event_type, data)

            # Queue deliveries for each webhook
            for webhook in relevant_webhooks:
                await self._queue_webhook_delivery(
                    webhook.id, event_id, event_type, data
                )

            record_metric("webhook_events_sent", len(relevant_webhooks))
            return True

        except Exception as e:
            logger.error(f"Failed to send webhook event: {e}")
            return False

    @time_operation("webhook_get_deliveries")
    async def get_webhook_deliveries(
        self, webhook_id: int, limit: int = 50
    ) -> List[WebhookDelivery]:
        """Get webhook delivery records."""
        try:
            # Try to get from cache first
            cache_key = f"webhook_deliveries:{webhook_id}:{limit}"
            cached_deliveries = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_deliveries:
                return [WebhookDelivery(**delivery) for delivery in cached_deliveries]

            # Get from database
            query = """
            SELECT * FROM webhook_deliveries
            WHERE webhook_id = :webhook_id
            ORDER BY created_at DESC
            LIMIT :limit
            """

            results = await self.db_manager.fetch_all(
                query, {"webhook_id": webhook_id, "limit": limit}
            )

            deliveries = []
            for row in results:
                delivery = WebhookDelivery(
                    id=row["id"],
                    webhook_id=row["webhook_id"],
                    event_type=row["event_type"],
                    payload=json.loads(row["payload"]) if row["payload"] else {},
                    status=DeliveryStatus(row["status"]),
                    response_code=row["response_code"],
                    response_body=row["response_body"],
                    retry_count=row["retry_count"],
                    next_retry=row["next_retry"],
                    delivered_at=row["delivered_at"],
                    created_at=row["created_at"],
                )
                deliveries.append(delivery)

            # Cache deliveries
            await self.cache_manager.enhanced_cache_set(
                cache_key,
                [
                    {
                        "id": d.id,
                        "webhook_id": d.webhook_id,
                        "event_type": d.event_type,
                        "payload": d.payload,
                        "status": d.status.value,
                        "response_code": d.response_code,
                        "response_body": d.response_body,
                        "retry_count": d.retry_count,
                        "next_retry": (
                            d.next_retry.isoformat() if d.next_retry else None
                        ),
                        "delivered_at": (
                            d.delivered_at.isoformat() if d.delivered_at else None
                        ),
                        "created_at": d.created_at.isoformat(),
                    }
                    for d in deliveries
                ],
                ttl=self.cache_ttls["webhook_deliveries"],
            )

            return deliveries

        except Exception as e:
            logger.error(f"Failed to get webhook deliveries: {e}")
            return []

    @time_operation("webhook_get_stats")
    async def get_webhook_stats(self, tenant_id: int, days: int = 30) -> Dict[str, Any]:
        """Get webhook statistics for a tenant."""
        try:
            # Try to get from cache first
            cache_key = f"webhook_stats:{tenant_id}:{days}"
            cached_stats = await self.cache_manager.enhanced_cache_get(cache_key)

            if cached_stats:
                return cached_stats

            # Get webhook configs
            webhooks = await self.get_webhooks_by_tenant(tenant_id)

            # Get delivery statistics
            query = """
            SELECT
                COUNT(*) as total_deliveries,
                COUNT(CASE WHEN status = 'delivered' THEN 1 END) as successful_deliveries,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_deliveries,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_deliveries,
                AVG(CASE WHEN response_code IS NOT NULL THEN response_code END) as avg_response_time
            FROM webhook_deliveries wd
            JOIN webhook_configs wc ON wd.webhook_id = wc.id
            WHERE wc.tenant_id = :tenant_id
            AND wd.created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            """

            result = await self.db_manager.fetch_one(
                query, {"tenant_id": tenant_id, "days": days}
            )

            stats = {
                "total_webhooks": len(webhooks),
                "active_webhooks": len(
                    [w for w in webhooks if w.status == WebhookStatus.ACTIVE]
                ),
                "total_deliveries": result["total_deliveries"] if result else 0,
                "successful_deliveries": (
                    result["successful_deliveries"] if result else 0
                ),
                "failed_deliveries": result["failed_deliveries"] if result else 0,
                "pending_deliveries": result["pending_deliveries"] if result else 0,
                "success_rate": (
                    (result["successful_deliveries"] / result["total_deliveries"] * 100)
                    if result and result["total_deliveries"] > 0
                    else 0
                ),
                "avg_response_time": result["avg_response_time"] if result else 0,
            }

            # Cache stats
            await self.cache_manager.enhanced_cache_set(
                cache_key, stats, ttl=self.cache_ttls["webhook_stats"]
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to get webhook stats: {e}")
            return {}

    async def clear_webhook_cache(self):
        """Clear all webhook-related cache entries."""
        try:
            await self.cache_manager.clear_cache_by_pattern("webhook_config:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_configs:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_deliveries:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_events:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_stats:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_retries:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_secrets:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_endpoints:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_logs:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_health:*")
            await self.cache_manager.clear_cache_by_pattern("webhook_performance:*")
            logger.info("Webhook cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear webhook cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get webhook service cache statistics."""
        try:
            return await self.cache_manager.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
