import logging
import json
import asyncio
import os
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
                
            # Create the export record
            result = await self.db_manager.execute(
                """
                INSERT INTO data_exports (guild_id, export_type, export_format, created_by)
                VALUES (%s, %s, %s, %s)
                """,
                guild_id, export_type, export_format, created_by
            )
            
            # Get the export ID
            export_id = await self.db_manager.fetch_one(
                "SELECT LAST_INSERT_ID() as id"
            )
            export_id = export_id['id'] if export_id else None
            
            if export_id:
                # Start the export generation in the background
                logger.info(f"Starting background export task for export_id={export_id}")
                try:
                    # Get the current event loop
                    loop = asyncio.get_event_loop()
                    
                    # Create the task with proper error handling
                    async def run_export_with_logging():
                        try:
                            logger.info(f"Background export task starting for export_id={export_id}")
                            await self._generate_export(export_id, guild_id, export_type, export_format, created_by)
                            logger.info(f"Background export task completed for export_id={export_id}")
                        except Exception as e:
                            logger.error(f"Background export task failed for export_id={export_id}: {e}", exc_info=True)
                            # Try to send error notification
                            try:
                                await self._send_export_notification(guild_id, created_by, export_type, export_format, False, f"Export failed: {e}")
                            except Exception as notify_error:
                                logger.error(f"Failed to send error notification for export_id={export_id}: {notify_error}")
                    
                    # Create and start the task
                    task = loop.create_task(run_export_with_logging())
                    logger.info(f"Background export task created and started for export_id={export_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to start background export task for export_id={export_id}: {e}", exc_info=True)
                    # Try to send immediate error notification
                    await self._send_export_notification(guild_id, created_by, export_type, export_format, False, f"Failed to start export: {e}")
                
            await self.track_feature_usage(guild_id, "data_exports")
            return export_id
        except Exception as e:
            logger.error(f"Error creating data export: {e}")
            return None

    def _handle_export_task_completion(self, task, export_id: int):
        """Handle completion of export background task."""
        try:
            if task.cancelled():
                logger.warning(f"Export task {export_id} was cancelled")
            elif task.exception():
                logger.error(f"Export task {export_id} failed with exception: {task.exception()}")
            else:
                logger.info(f"Export task {export_id} completed successfully")
        except Exception as e:
            logger.error(f"Error in export task completion handler for {export_id}: {e}")

    async def _generate_export(self, export_id: int, guild_id: int, export_type: str, export_format: str, created_by: int):
        """Generate the actual export file and send notification."""
        try:
            logger.info(f"Starting export generation for export_id={export_id}, type={export_type}, format={export_format}")
            
            # Generate the export data
            logger.info(f"Fetching export data for export_id={export_id}")
            export_data = await self._get_export_data(guild_id, export_type)
            
            logger.info(f"Export data fetched for export_id={export_id}: {len(export_data) if isinstance(export_data, list) else 'dict'} items")
            
            if not export_data:
                logger.warning(f"No data found for export_id={export_id}, type={export_type}")
                await self._update_export_status(export_id, False, "No data found for export")
                await self._send_export_notification(guild_id, created_by, export_type, export_format, False, "No data found")
                return
            
            # Create the export file
            logger.info(f"Creating export file for export_id={export_id}")
            file_path = await self._create_export_file(export_data, export_type, export_format, export_id)
            
            if file_path:
                logger.info(f"Export file created successfully for export_id={export_id}: {file_path}")
                # Update export status to completed
                await self._update_export_status(export_id, True, file_path)
                
                # Send success notification
                logger.info(f"Sending success notification for export_id={export_id}")
                await self._send_export_notification(guild_id, created_by, export_type, export_format, True, file_path)
                
                logger.info(f"Export {export_id} completed successfully: {file_path}")
            else:
                logger.error(f"Failed to create export file for export_id={export_id}")
                await self._update_export_status(export_id, False, "Failed to create file")
                await self._send_export_notification(guild_id, created_by, export_type, export_format, False, "Failed to create file")
                
        except Exception as e:
            logger.error(f"Error generating export {export_id}: {e}", exc_info=True)
            await self._update_export_status(export_id, False, str(e))
            await self._send_export_notification(guild_id, created_by, export_type, export_format, False, str(e))

    async def _get_export_data(self, guild_id: int, export_type: str) -> List[Dict[str, Any]]:
        """Get data for the specified export type."""
        try:
            if export_type == "bets":
                return await self.db_manager.fetch_all(
                    "SELECT * FROM bets WHERE guild_id = %s ORDER BY created_at DESC",
                    guild_id
                )
            elif export_type == "users":
                return await self.db_manager.fetch_all(
                    "SELECT * FROM users WHERE guild_id = %s ORDER BY created_at DESC",
                    guild_id
                )
            elif export_type == "analytics":
                return await self.db_manager.fetch_all(
                    "SELECT * FROM platinum_analytics WHERE guild_id = %s ORDER BY last_used DESC",
                    guild_id
                )
            elif export_type == "all":
                # Combine all data types
                bets = await self.db_manager.fetch_all("SELECT * FROM bets WHERE guild_id = %s", guild_id)
                users = await self.db_manager.fetch_all("SELECT * FROM users WHERE guild_id = %s", guild_id)
                analytics = await self.db_manager.fetch_all("SELECT * FROM platinum_analytics WHERE guild_id = %s", guild_id)
                
                return {
                    "bets": bets,
                    "users": users,
                    "analytics": analytics
                }
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting export data: {e}")
            return []

    async def _create_export_file(self, data: List[Dict[str, Any]], export_type: str, export_format: str, export_id: int) -> str:
        """Create the export file in the specified format."""
        try:
            import json
            import csv
            from datetime import datetime
            
            # Create exports directory if it doesn't exist
            exports_dir = "exports"
            os.makedirs(exports_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{export_type}_{export_format}_{timestamp}_{export_id}"
            
            if export_format == "csv":
                file_path = os.path.join(exports_dir, f"{filename}.csv")
                await self._write_csv_file(data, file_path, export_type)
            elif export_format == "json":
                file_path = os.path.join(exports_dir, f"{filename}.json")
                await self._write_json_file(data, file_path)
            elif export_format == "xlsx":
                file_path = os.path.join(exports_dir, f"{filename}.xlsx")
                await self._write_xlsx_file(data, file_path, export_type)
            else:
                return None
                
            return file_path
        except Exception as e:
            logger.error(f"Error creating export file: {e}")
            return None

    async def _write_csv_file(self, data: List[Dict[str, Any]], file_path: str, export_type: str):
        """Write data to CSV file."""
        if not data:
            return
            
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            if export_type == "all":
                # Handle multiple data types
                for data_type, data_list in data.items():
                    if data_list:
                        writer = csv.DictWriter(csvfile, fieldnames=data_list[0].keys())
                        writer.writeheader()
                        writer.writerows(data_list)
            else:
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

    async def _write_json_file(self, data: List[Dict[str, Any]], file_path: str):
        """Write data to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, default=str)

    async def _write_xlsx_file(self, data: List[Dict[str, Any]], file_path: str, export_type: str):
        """Write data to XLSX file."""
        try:
            import pandas as pd
            
            if export_type == "all":
                # Create Excel file with multiple sheets
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    for data_type, data_list in data.items():
                        if data_list:
                            df = pd.DataFrame(data_list)
                            df.to_excel(writer, sheet_name=data_type, index=False)
            else:
                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False)
        except ImportError:
            logger.error("pandas not available for XLSX export")
            raise

    async def _update_export_status(self, export_id: int, is_completed: bool, file_path: str = None):
        """Update the export status in the database."""
        try:
            if is_completed:
                await self.db_manager.execute(
                    """
                    UPDATE data_exports 
                    SET is_completed = TRUE, file_path = %s, completed_at = NOW()
                    WHERE id = %s
                    """,
                    file_path, export_id
                )
            else:
                await self.db_manager.execute(
                    """
                    UPDATE data_exports 
                    SET is_completed = FALSE, file_path = %s, completed_at = NOW()
                    WHERE id = %s
                    """,
                    file_path, export_id
                )
        except Exception as e:
            logger.error(f"Error updating export status: {e}")

    async def _send_export_notification(self, guild_id: int, user_id: int, export_type: str, export_format: str, success: bool, file_path: str = None):
        """Send notification to user about export completion."""
        try:
            logger.info(f"Sending export notification: guild_id={guild_id}, user_id={user_id}, success={success}")
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logger.error(f"Guild {guild_id} not found for export notification")
                return
                
            user = guild.get_member(user_id)
            if not user:
                logger.error(f"User {user_id} not found in guild {guild_id} for export notification")
                return
            
            embed = discord.Embed(
                title="📊 Export Complete" if success else "❌ Export Failed",
                description=f"Your {export_type} export in {export_format.upper()} format is ready!" if success else f"Failed to create {export_type} export in {export_format.upper()} format.",
                color=0x00ff00 if success else 0xff0000,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="Type", value=export_type, inline=True)
            embed.add_field(name="Format", value=export_format.upper(), inline=True)
            
            if success and file_path:
                embed.add_field(name="File", value=f"`{os.path.basename(file_path)}`", inline=False)
                embed.set_footer(text="File saved to server exports directory")
            else:
                embed.add_field(name="Error", value=file_path or "Unknown error", inline=False)
                embed.set_footer(text="Please try again or contact support")
            
            # Try to send DM first, then fallback to guild
            notification_sent = False
            try:
                logger.info(f"Attempting to send DM to user {user_id} for export notification")
                await user.send(embed=embed)
                notification_sent = True
                logger.info(f"Export notification sent via DM to user {user_id}")
            except Exception as dm_error:
                logger.warning(f"Failed to send DM to user {user_id}: {dm_error}")
                
                # If DM fails, try to send to a channel the user can see
                for channel in guild.text_channels:
                    if channel.permissions_for(user).read_messages:
                        try:
                            logger.info(f"Attempting to send notification to channel {channel.id}")
                            await channel.send(f"{user.mention}", embed=embed)
                            notification_sent = True
                            logger.info(f"Export notification sent to channel {channel.id}")
                            break
                        except Exception as channel_error:
                            logger.warning(f"Failed to send to channel {channel.id}: {channel_error}")
                            continue
            
            if not notification_sent:
                logger.error(f"Failed to send export notification to user {user_id} in guild {guild_id}")
            else:
                logger.info(f"Export notification successfully sent for export_id={export_id}")
                            
        except Exception as e:
            logger.error(f"Error sending export notification: {e}", exc_info=True)
            
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

    async def test_export_system(self, guild_id: int, user_id: int) -> bool:
        """Test the export system by creating a simple test export."""
        try:
            logger.info(f"Testing export system for guild_id={guild_id}")
            
            # Create a test export
            export_id = await self.create_data_export(guild_id, "analytics", "json", user_id)
            
            if export_id:
                logger.info(f"Test export created successfully with ID: {export_id}")
                return True
            else:
                logger.error("Test export creation failed")
                return False
                
        except Exception as e:
            logger.error(f"Test export system failed: {e}", exc_info=True)
            return False

    async def create_webhook(self, guild_id: int, webhook_name: str, webhook_url: str, webhook_type: str) -> bool:
        """Create a webhook integration (alias for create_webhook_integration)."""
        return await self.create_webhook_integration(guild_id, webhook_name, webhook_url, webhook_type)

    # Export Methods (fix method names)
    async def create_export(self, guild_id: int, export_type: str, export_format: str, created_by: int) -> bool:
        """Create a data export (alias for create_data_export)."""
        result = await self.create_data_export(guild_id, export_type, export_format, created_by)
        return result is not None 