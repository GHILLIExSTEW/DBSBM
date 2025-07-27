"""Webhook Service for DBSBM System.

This service provides webhook functionality including:
- Real-time notifications to external services
- Mobile app integration via webhooks
- Third-party tool integration (Zapier, IFTTT)
- Custom webhook endpoints for advanced users
- Webhook security and authentication
"""

import asyncio
import json
import logging
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict
import aiohttp
from urllib.parse import urlparse

from data.db_manager import DatabaseManager
from bot.data.cache_manager import cache_get, cache_set
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)

@dataclass
class WebhookEvent:
    """Represents a webhook event to be sent."""
    event_type: str
    event_data: Dict[str, Any]
    guild_id: int
    user_id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: str = "normal"  # low, normal, high, critical

@dataclass
class WebhookDelivery:
    """Represents a webhook delivery attempt."""
    webhook_id: int
    event_type: str
    payload: Dict[str, Any]
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0
    delivered_at: Optional[datetime] = None

class WebhookService:
    """Webhook service for external integrations and notifications."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.active_webhooks = {}  # Cache for active webhooks
        self.delivery_stats = defaultdict(int)
        self._delivery_task = None
        self._is_running = False

        # Webhook configuration
        self.config = {
            'max_retries': 3,
            'retry_delay': 60,  # seconds
            'timeout': 30,  # seconds
            'batch_size': 50,
            'rate_limit': 100,  # requests per minute per webhook
            'max_payload_size': 1024 * 1024,  # 1MB
            'signature_header': 'X-DBSBM-Signature',
            'user_agent': 'DBSBM-Webhook/1.0'
        }

        # Rate limiting
        self.rate_limit_tracker = defaultdict(list)

        logger.info("WebhookService initialized")

    async def start(self):
        """Start the webhook service."""
        if self._is_running:
            logger.warning("WebhookService is already running")
            return

        self._is_running = True
        self._delivery_task = asyncio.create_task(self._process_webhook_queue())
        await self._load_active_webhooks()
        logger.info("WebhookService started")

    async def stop(self):
        """Stop the webhook service."""
        if not self._is_running:
            return

        self._is_running = False
        if self._delivery_task:
            self._delivery_task.cancel()
            try:
                await self._delivery_task
            except asyncio.CancelledError:
                pass
        logger.info("WebhookService stopped")

    @time_operation("webhook_send_event")
    async def send_event(self, event: WebhookEvent):
        """Send a webhook event to all registered webhooks."""
        try:
            # Add event to queue
            await self.event_queue.put(event)
            record_metric("webhook_events_queued", 1)
            logger.debug(f"Queued webhook event: {event.event_type}")

        except Exception as e:
            logger.error(f"Error queuing webhook event: {e}")
            record_metric("webhook_errors", 1)

    @time_operation("webhook_register_webhook")
    async def register_webhook(self, guild_id: int, webhook_url: str,
                             webhook_type: str, events: List[str],
                             secret_key: Optional[str] = None) -> bool:
        """Register a new webhook for a guild."""
        try:
            # Validate webhook URL
            if not self._validate_webhook_url(webhook_url):
                return False

            # Check webhook limits
            if not await self._check_webhook_limits(guild_id):
                return False

            # Generate secret key if not provided
            if not secret_key:
                secret_key = self._generate_secret_key()

            # Store webhook configuration
            query = """
                INSERT INTO webhook_integrations
                (guild_id, webhook_url, webhook_type, events, secret_key)
                VALUES (%s, %s, %s, %s, %s)
            """

            await self.db_manager.execute(
                query, guild_id, webhook_url, webhook_type,
                json.dumps(events), secret_key
            )

            # Update cache
            await self._load_active_webhooks()

            logger.info(f"Registered webhook for guild {guild_id}: {webhook_type}")
            return True

        except Exception as e:
            logger.error(f"Error registering webhook: {e}")
            return False

    @time_operation("webhook_unregister_webhook")
    async def unregister_webhook(self, webhook_id: int) -> bool:
        """Unregister a webhook."""
        try:
            query = "DELETE FROM webhook_integrations WHERE id = %s"
            await self.db_manager.execute(query, webhook_id)

            # Update cache
            await self._load_active_webhooks()

            logger.info(f"Unregistered webhook {webhook_id}")
            return True

        except Exception as e:
            logger.error(f"Error unregistering webhook: {e}")
            return False

    @time_operation("webhook_get_webhooks")
    async def get_webhooks(self, guild_id: int) -> List[Dict]:
        """Get all webhooks for a guild."""
        try:
            query = """
                SELECT id, webhook_url, webhook_type, events, is_active, created_at
                FROM webhook_integrations
                WHERE guild_id = %s
                ORDER BY created_at DESC
            """
            return await self.db_manager.fetch_all(query, guild_id)

        except Exception as e:
            logger.error(f"Error getting webhooks: {e}")
            return []

    @time_operation("webhook_test_webhook")
    async def test_webhook(self, webhook_id: int) -> Dict[str, Any]:
        """Test a webhook by sending a test event."""
        try:
            # Get webhook configuration
            query = "SELECT * FROM webhook_integrations WHERE id = %s"
            webhook = await self.db_manager.fetch_one(query, webhook_id)

            if not webhook:
                return {"success": False, "error": "Webhook not found"}

            # Create test event
            test_event = WebhookEvent(
                event_type="test",
                event_data={"message": "This is a test webhook event"},
                guild_id=webhook['guild_id'],
                priority="normal"
            )

            # Send test event
            delivery = await self._deliver_webhook(webhook, test_event)

            return {
                "success": delivery.success,
                "status_code": delivery.status_code,
                "response_time": delivery.response_time,
                "error_message": delivery.error_message
            }

        except Exception as e:
            logger.error(f"Error testing webhook: {e}")
            return {"success": False, "error": str(e)}

    @time_operation("webhook_get_delivery_stats")
    async def get_delivery_stats(self, guild_id: Optional[int] = None) -> Dict[str, Any]:
        """Get webhook delivery statistics."""
        try:
            if guild_id:
                query = """
                    SELECT
                        COUNT(*) as total_deliveries,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_deliveries,
                        AVG(response_time) as avg_response_time,
                        MAX(delivered_at) as last_delivery
                    FROM webhook_deliveries
                    WHERE guild_id = %s
                    AND delivered_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                """
                result = await self.db_manager.fetch_one(query, guild_id)
            else:
                query = """
                    SELECT
                        COUNT(*) as total_deliveries,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_deliveries,
                        AVG(response_time) as avg_response_time
                    FROM webhook_deliveries
                    WHERE delivered_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                """
                result = await self.db_manager.fetch_one(query)

            if result:
                success_rate = (result['successful_deliveries'] / result['total_deliveries']) * 100 if result['total_deliveries'] > 0 else 0
                return {
                    "total_deliveries": result['total_deliveries'],
                    "successful_deliveries": result['successful_deliveries'],
                    "success_rate": success_rate,
                    "avg_response_time": result['avg_response_time'],
                    "last_delivery": result.get('last_delivery')
                }

            return {}

        except Exception as e:
            logger.error(f"Error getting delivery stats: {e}")
            return {}

    async def _process_webhook_queue(self):
        """Background task to process webhook events."""
        while self._is_running:
            try:
                # Process events in batches
                events = []
                for _ in range(self.config['batch_size']):
                    try:
                        event = await asyncio.wait_for(
                            self.event_queue.get(), timeout=1.0
                        )
                        events.append(event)
                    except asyncio.TimeoutError:
                        break

                if events:
                    await self._process_events_batch(events)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in webhook queue processing: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def _process_events_batch(self, events: List[WebhookEvent]):
        """Process a batch of webhook events."""
        try:
            # Group events by guild
            guild_events = defaultdict(list)
            for event in events:
                guild_events[event.guild_id].append(event)

            # Process each guild's events
            for guild_id, guild_event_list in guild_events.items():
                await self._process_guild_events(guild_id, guild_event_list)

        except Exception as e:
            logger.error(f"Error processing events batch: {e}")

    async def _process_guild_events(self, guild_id: int, events: List[WebhookEvent]):
        """Process events for a specific guild."""
        try:
            # Get active webhooks for guild
            webhooks = self.active_webhooks.get(guild_id, [])

            if not webhooks:
                return

            # Process each event
            for event in events:
                await self._send_event_to_webhooks(event, webhooks)

        except Exception as e:
            logger.error(f"Error processing guild events: {e}")

    async def _send_event_to_webhooks(self, event: WebhookEvent, webhooks: List[Dict]):
        """Send an event to multiple webhooks."""
        try:
            # Filter webhooks by event type
            matching_webhooks = [
                webhook for webhook in webhooks
                if event.event_type in json.loads(webhook['events'])
            ]

            if not matching_webhooks:
                return

            # Send to each webhook
            delivery_tasks = []
            for webhook in matching_webhooks:
                task = asyncio.create_task(
                    self._deliver_webhook(webhook, event)
                )
                delivery_tasks.append(task)

            # Wait for all deliveries to complete
            if delivery_tasks:
                await asyncio.gather(*delivery_tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error sending event to webhooks: {e}")

    async def _deliver_webhook(self, webhook: Dict, event: WebhookEvent) -> WebhookDelivery:
        """Deliver a webhook event to a specific webhook."""
        delivery = WebhookDelivery(
            webhook_id=webhook['id'],
            event_type=event.event_type,
            payload=self._prepare_payload(event)
        )

        try:
            # Check rate limiting
            if not self._check_rate_limit(webhook['id']):
                delivery.error_message = "Rate limit exceeded"
                await self._store_delivery(delivery)
                return delivery

            # Prepare headers
            headers = self._prepare_headers(webhook, event)

            # Send webhook
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook['webhook_url'],
                    json=delivery.payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config['timeout'])
                ) as response:
                    delivery.status_code = response.status
                    delivery.response_time = time.time() - start_time
                    delivery.success = 200 <= response.status < 300

                    if not delivery.success:
                        delivery.error_message = await response.text()

            # Update rate limit tracker
            self._update_rate_limit(webhook['id'])

        except asyncio.TimeoutError:
            delivery.error_message = "Request timeout"
        except Exception as e:
            delivery.error_message = str(e)

        # Store delivery record
        await self._store_delivery(delivery)

        # Retry if failed
        if not delivery.success and delivery.retry_count < self.config['max_retries']:
            await self._schedule_retry(delivery)

        return delivery

    def _prepare_payload(self, event: WebhookEvent) -> Dict[str, Any]:
        """Prepare webhook payload."""
        return {
            "event_type": event.event_type,
            "event_data": event.event_data,
            "guild_id": event.guild_id,
            "user_id": event.user_id,
            "timestamp": event.timestamp.isoformat(),
            "priority": event.priority
        }

    def _prepare_headers(self, webhook: Dict, event: WebhookEvent) -> Dict[str, str]:
        """Prepare webhook headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.config['user_agent'],
            "X-DBSBM-Event": event.event_type,
            "X-DBSBM-Guild-ID": str(event.guild_id),
            "X-DBSBM-Timestamp": str(int(event.timestamp.timestamp()))
        }

        # Add signature if secret key exists
        if webhook.get('secret_key'):
            payload = json.dumps(self._prepare_payload(event))
            signature = self._generate_signature(payload, webhook['secret_key'])
            headers[self.config['signature_header']] = signature

        return headers

    def _generate_signature(self, payload: str, secret_key: str) -> str:
        """Generate HMAC signature for webhook payload."""
        return hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _validate_webhook_url(self, url: str) -> bool:
        """Validate webhook URL."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and parsed.netloc
        except Exception:
            return False

    def _generate_secret_key(self) -> str:
        """Generate a random secret key for webhook signing."""
        import secrets
        return secrets.token_urlsafe(32)

    async def _check_webhook_limits(self, guild_id: int) -> bool:
        """Check if guild has reached webhook limits."""
        try:
            # Get current webhook count
            query = "SELECT COUNT(*) as count FROM webhook_integrations WHERE guild_id = %s"
            result = await self.db_manager.fetch_one(query, guild_id)

            # Get guild settings for limits
            settings_query = "SELECT webhook_limit FROM guild_settings WHERE guild_id = %s"
            settings = await self.db_manager.fetch_one(settings_query, guild_id)

            current_count = result['count'] if result else 0
            limit = settings['webhook_limit'] if settings else 5  # Default limit

            return current_count < limit

        except Exception as e:
            logger.error(f"Error checking webhook limits: {e}")
            return False

    def _check_rate_limit(self, webhook_id: int) -> bool:
        """Check rate limiting for a webhook."""
        now = time.time()
        webhook_requests = self.rate_limit_tracker[webhook_id]

        # Remove old requests
        webhook_requests[:] = [req_time for req_time in webhook_requests
                             if now - req_time < 60]  # 1 minute window

        # Check if under limit
        return len(webhook_requests) < self.config['rate_limit']

    def _update_rate_limit(self, webhook_id: int):
        """Update rate limit tracker."""
        self.rate_limit_tracker[webhook_id].append(time.time())

    async def _store_delivery(self, delivery: WebhookDelivery):
        """Store webhook delivery record."""
        try:
            query = """
                INSERT INTO webhook_deliveries
                (webhook_id, event_type, payload, status_code, response_time,
                 success, error_message, retry_count, delivered_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            await self.db_manager.execute(
                query, delivery.webhook_id, delivery.event_type,
                json.dumps(delivery.payload), delivery.status_code,
                delivery.response_time, delivery.success,
                delivery.error_message, delivery.retry_count,
                delivery.delivered_at or datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error storing delivery record: {e}")

    async def _schedule_retry(self, delivery: WebhookDelivery):
        """Schedule a retry for failed delivery."""
        try:
            delivery.retry_count += 1

            # Create retry event
            retry_event = WebhookEvent(
                event_type=delivery.event_type,
                event_data=delivery.payload,
                guild_id=delivery.payload.get('guild_id'),
                user_id=delivery.payload.get('user_id'),
                priority="high" if delivery.retry_count > 1 else "normal"
            )

            # Schedule retry with exponential backoff
            delay = self.config['retry_delay'] * (2 ** (delivery.retry_count - 1))
            asyncio.create_task(self._delayed_retry(retry_event, delay))

        except Exception as e:
            logger.error(f"Error scheduling retry: {e}")

    async def _delayed_retry(self, event: WebhookEvent, delay: float):
        """Delayed retry for failed webhook delivery."""
        try:
            await asyncio.sleep(delay)
            await self.send_event(event)
        except Exception as e:
            logger.error(f"Error in delayed retry: {e}")

    async def _load_active_webhooks(self):
        """Load active webhooks from database."""
        try:
            query = """
                SELECT * FROM webhook_integrations
                WHERE is_active = 1
                ORDER BY guild_id, created_at
            """
            webhooks = await self.db_manager.fetch_all(query)

            # Group by guild
            self.active_webhooks.clear()
            for webhook in webhooks:
                guild_id = webhook['guild_id']
                if guild_id not in self.active_webhooks:
                    self.active_webhooks[guild_id] = []
                self.active_webhooks[guild_id].append(webhook)

            logger.info(f"Loaded {len(webhooks)} active webhooks")

        except Exception as e:
            logger.error(f"Error loading active webhooks: {e}")

    # Convenience methods for common events
    async def send_bet_placed_event(self, guild_id: int, user_id: int, bet_data: Dict[str, Any]):
        """Send bet placed event to webhooks."""
        event = WebhookEvent(
            event_type="bet_placed",
            event_data=bet_data,
            guild_id=guild_id,
            user_id=user_id
        )
        await self.send_event(event)

    async def send_bet_resulted_event(self, guild_id: int, user_id: int, bet_data: Dict[str, Any]):
        """Send bet resulted event to webhooks."""
        event = WebhookEvent(
            event_type="bet_resulted",
            event_data=bet_data,
            guild_id=guild_id,
            user_id=user_id
        )
        await self.send_event(event)

    async def send_high_value_bet_event(self, guild_id: int, user_id: int, bet_data: Dict[str, Any]):
        """Send high value bet event to webhooks."""
        event = WebhookEvent(
            event_type="high_value_bet",
            event_data=bet_data,
            guild_id=guild_id,
            user_id=user_id,
            priority="high"
        )
        await self.send_event(event)

    async def send_user_achievement_event(self, guild_id: int, user_id: int, achievement_data: Dict[str, Any]):
        """Send user achievement event to webhooks."""
        event = WebhookEvent(
            event_type="user_achievement",
            event_data=achievement_data,
            guild_id=guild_id,
            user_id=user_id
        )
        await self.send_event(event)

    async def send_system_alert_event(self, guild_id: int, alert_data: Dict[str, Any]):
        """Send system alert event to webhooks."""
        event = WebhookEvent(
            event_type="system_alert",
            event_data=alert_data,
            guild_id=guild_id,
            priority="critical"
        )
        await self.send_event(event)

# Global webhook service instance
webhook_service = None

async def initialize_webhook_service(db_manager: DatabaseManager):
    """Initialize the global webhook service."""
    global webhook_service
    webhook_service = WebhookService(db_manager)
    await webhook_service.start()
    logger.info("Webhook service initialized")

async def get_webhook_service() -> WebhookService:
    """Get the global webhook service instance."""
    return webhook_service
