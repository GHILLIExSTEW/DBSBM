import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import discord
from discord import Webhook, Embed

logger = logging.getLogger(__name__)


class PlatinumService:
    """Service for handling Platinum tier advanced features."""
    
    def __init__(self, db_manager, bot):
        self.db_manager = db_manager
        self.bot = bot
        self.active_webhooks = {}
        self.active_alerts = {}
        
    async def start(self):
        """Initialize the Platinum service."""
        logger.info("Starting Platinum service...")
        await self.load_active_webhooks()
        await self.load_active_alerts()
        logger.info("Platinum service started successfully")
        
    async def load_active_webhooks(self):
        """Load active webhook integrations from database."""
        try:
            webhooks = await self.db_manager.fetch_all(
                "SELECT * FROM webhook_integrations WHERE is_active = TRUE"
            )
            for webhook in webhooks:
                self.active_webhooks[webhook['id']] = webhook
            logger.info(f"Loaded {len(webhooks)} active webhooks")
        except Exception as e:
            logger.error(f"Error loading webhooks: {e}")
            
    async def load_active_alerts(self):
        """Load active real-time alerts from database."""
        try:
            alerts = await self.db_manager.fetch_all(
                "SELECT * FROM real_time_alerts WHERE is_active = TRUE"
            )
            for alert in alerts:
                self.active_alerts[alert['id']] = alert
            logger.info(f"Loaded {len(alerts)} active alerts")
        except Exception as e:
            logger.error(f"Error loading alerts: {e}")



    # Webhook Integrations
    async def create_webhook_integration(self, guild_id: int, webhook_name: str,
                                       webhook_url: str, webhook_type: str) -> bool:
        """Create a webhook integration for a Platinum guild."""
        try:
            if not await self.is_platinum_guild(guild_id):
                return False
                
            # Check webhook limit
            current_webhooks = await self.get_webhook_integrations(guild_id)
            if len(current_webhooks) >= 10:  # Platinum limit
                return False
                
            await self.db_manager.execute(
                """
                INSERT INTO webhook_integrations (guild_id, webhook_name, webhook_url, webhook_type)
                VALUES (%s, %s, %s, %s)
                """,
                guild_id, webhook_name, webhook_url, webhook_type
            )
            
            await self.load_active_webhooks()  # Refresh cache
            await self.track_feature_usage(guild_id, "webhook_integrations")
            
            return True
        except Exception as e:
            logger.error(f"Error creating webhook integration: {e}")
            return False
            
    async def get_webhook_integrations(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all webhook integrations for a guild."""
        try:
            return await self.db_manager.fetch_all(
                "SELECT * FROM webhook_integrations WHERE guild_id = %s AND is_active = TRUE",
                guild_id
            )
        except Exception as e:
            logger.error(f"Error getting webhook integrations: {e}")
            return []
            
    async def send_webhook_notification(self, webhook_id: int, data: Dict[str, Any]) -> bool:
        """Send a notification to a webhook."""
        try:
            webhook_data = self.active_webhooks.get(webhook_id)
            if not webhook_data:
                return False
                
            webhook = Webhook.from_url(webhook_data['webhook_url'], session=self.bot.session)
            
            embed = Embed(
                title=f"{webhook_data['webhook_name']} - {data.get('type', 'Notification')}",
                description=data.get('message', ''),
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            if data.get('fields'):
                for field in data['fields']:
                    embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))
                    
            await webhook.send(embed=embed)
            return True
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False

    # Real-Time Alerts
    async def create_real_time_alert(self, guild_id: int, alert_type: str,
                                   alert_conditions: Dict[str, Any], 
                                   alert_channel_id: int) -> bool:
        """Create a real-time alert for a Platinum guild."""
        try:
            if not await self.is_platinum_guild(guild_id):
                return False
                
            await self.db_manager.execute(
                """
                INSERT INTO real_time_alerts (guild_id, alert_type, alert_conditions, alert_channel_id)
                VALUES (%s, %s, %s, %s)
                """,
                guild_id, alert_type, json.dumps(alert_conditions), alert_channel_id
            )
            
            await self.load_active_alerts()  # Refresh cache
            await self.track_feature_usage(guild_id, "real_time_alerts")
            
            return True
        except Exception as e:
            logger.error(f"Error creating real-time alert: {e}")
            return False
            
    async def get_real_time_alerts(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all real-time alerts for a guild."""
        try:
            return await self.db_manager.fetch_all(
                "SELECT * FROM real_time_alerts WHERE guild_id = %s AND is_active = TRUE",
                guild_id
            )
        except Exception as e:
            logger.error(f"Error getting real-time alerts: {e}")
            return []
            
    async def trigger_alert(self, alert_id: int, data: Dict[str, Any]) -> bool:
        """Trigger a real-time alert."""
        try:
            alert_data = self.active_alerts.get(alert_id)
            if not alert_data:
                return False
                
            channel = self.bot.get_channel(alert_data['alert_channel_id'])
            if not channel:
                return False
                
            embed = Embed(
                title=f"🚨 {alert_data['alert_type'].title()} Alert",
                description=data.get('message', ''),
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            
            if data.get('fields'):
                for field in data['fields']:
                    embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))
                    
            await channel.send(embed=embed)
            return True
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
            return False

    # Data Export
    async def create_data_export(self, guild_id: int, export_type: str,
                               export_format: str, created_by: int) -> int:
        """Create a data export request for a Platinum guild."""
        try:
            if not await self.is_platinum_guild(guild_id):
                return None
                
            # Check export limit
            recent_exports = await self.get_recent_exports(guild_id)
            if len(recent_exports) >= 50:  # Platinum limit
                return None
                
            result = await self.db_manager.execute(
                """
                INSERT INTO data_exports (guild_id, export_type, export_format, created_by)
                VALUES (%s, %s, %s, %s)
                """,
                guild_id, export_type, export_format, created_by
            )
            
            await self.track_feature_usage(guild_id, "data_exports")
            return result
        except Exception as e:
            logger.error(f"Error creating data export: {e}")
            return None
            
    async def get_recent_exports(self, guild_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent data exports for a guild."""
        try:
            return await self.db_manager.fetch_all(
                """
                SELECT * FROM data_exports 
                WHERE guild_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY created_at DESC
                """,
                guild_id, days
            )
        except Exception as e:
            logger.error(f"Error getting recent exports: {e}")
            return []



    # Analytics and Usage Tracking
    async def track_feature_usage(self, guild_id: int, feature_name: str) -> bool:
        """Track usage of a Platinum feature."""
        try:
            await self.db_manager.execute(
                """
                INSERT INTO platinum_analytics (guild_id, feature_name, usage_count, last_used)
                VALUES (%s, %s, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    usage_count = usage_count + 1,
                    last_used = NOW()
                """,
                guild_id, feature_name
            )
            return True
        except Exception as e:
            logger.error(f"Error tracking feature usage: {e}")
            return False
            
    async def get_feature_analytics(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get analytics for all Platinum features."""
        try:
            return await self.db_manager.fetch_all(
                """
                SELECT feature_name, usage_count, last_used
                FROM platinum_analytics 
                WHERE guild_id = %s
                ORDER BY usage_count DESC
                """,
                guild_id
            )
        except Exception as e:
            logger.error(f"Error getting feature analytics: {e}")
            return []

    # Utility Methods
    async def is_platinum_guild(self, guild_id: int) -> bool:
        """Check if a guild has Platinum subscription."""
        try:
            result = await self.db_manager.fetch_one(
                "SELECT subscription_level FROM guild_settings WHERE guild_id = %s",
                guild_id
            )
            return bool(result and result.get("subscription_level") == "platinum")
        except Exception as e:
            logger.error(f"Error checking Platinum status: {e}")
            return False
            
    async def get_platinum_limits(self, guild_id: int) -> Dict[str, int]:
        """Get Platinum tier limits for a guild."""
        try:
            result = await self.db_manager.fetch_one(
                """
                SELECT max_embed_channels_platinum, max_command_channels_platinum,
                       max_active_bets_platinum, max_custom_commands_platinum,
                       max_webhooks_platinum, max_data_exports_platinum
                FROM guild_settings WHERE guild_id = %s
                """,
                guild_id
            )
            return result if result else {}
        except Exception as e:
            logger.error(f"Error getting Platinum limits: {e}")
            return {}

    # Analytics Methods
    async def get_analytics(self, guild_id: int) -> Dict[str, Any]:
        """Get comprehensive analytics for a Platinum guild."""
        try:
            analytics = {}
            
            # Get webhook count
            webhooks = await self.get_webhook_integrations(guild_id)
            analytics['webhook_count'] = len(webhooks)
            
            # Get export count for current month
            from datetime import datetime
            current_month = datetime.now().month
            exports = await self.get_recent_exports(guild_id, days=30)
            analytics['export_count'] = len(exports)
            
            # Get API usage (placeholder for now)
            analytics['api_requests'] = 0
            
            # Get top features
            feature_analytics = await self.get_feature_analytics(guild_id)
            if feature_analytics:
                top_features = [f"{feat['feature_name']}: {feat['usage_count']}" for feat in feature_analytics[:3]]
                analytics['top_features'] = '\n'.join(top_features)
            else:
                analytics['top_features'] = 'No data available'
            
            return analytics
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {
                'webhook_count': 0,
                'export_count': 0,
                'api_requests': 0,
                'top_features': 'Error loading data'
            }

    async def get_webhook_count(self, guild_id: int) -> int:
        """Get the number of active webhooks for a guild."""
        try:
            webhooks = await self.get_webhook_integrations(guild_id)
            return len(webhooks)
        except Exception as e:
            logger.error(f"Error getting webhook count: {e}")
            return 0

    async def get_export_count(self, guild_id: int, month: int) -> int:
        """Get the number of exports for a specific month."""
        try:
            from datetime import datetime
            current_year = datetime.now().year
            start_date = datetime(current_year, month, 1)
            
            if month == 12:
                end_date = datetime(current_year + 1, 1, 1)
            else:
                end_date = datetime(current_year, month + 1, 1)
            
            exports = await self.db_manager.fetch_all(
                """
                SELECT COUNT(*) as count FROM data_exports 
                WHERE guild_id = %s AND created_at >= %s AND created_at < %s
                """,
                guild_id, start_date, end_date
            )
            
            return exports[0]['count'] if exports else 0
        except Exception as e:
            logger.error(f"Error getting export count: {e}")
            return 0

    # Webhook Methods (fix method names)
    async def create_webhook(self, guild_id: int, webhook_name: str, webhook_url: str, webhook_type: str) -> bool:
        """Create a webhook integration (alias for create_webhook_integration)."""
        return await self.create_webhook_integration(guild_id, webhook_name, webhook_url, webhook_type)

    # Export Methods (fix method names)
    async def create_export(self, guild_id: int, export_type: str, export_format: str, created_by: int) -> bool:
        """Create a data export (alias for create_data_export)."""
        result = await self.create_data_export(guild_id, export_type, export_format, created_by)
        return result is not None 