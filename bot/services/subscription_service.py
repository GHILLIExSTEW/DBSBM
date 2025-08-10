import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    async def create_subscription(
        self, guild_id: int, user_id: int, plan_type: str = "premium"
    ) -> bool:
        """Create a new subscription for a guild."""
        try:
            # Calculate subscription end date (30 days from now)
            end_date = datetime.utcnow() + timedelta(days=30)

            await self.db_manager.execute(
                """
                INSERT INTO subscriptions (
                    guild_id, user_id, plan_type, start_date, end_date, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                guild_id,
                user_id,
                plan_type,
                datetime.utcnow(),
                end_date,
                True,
            )

            # Update guild settings based on plan type
            subscription_level = plan_type
            await self.db_manager.execute(
                "UPDATE guild_settings SET subscription_level = $1 WHERE guild_id = $2",
                subscription_level,
                guild_id,
            )

            # Enable Platinum features if applicable
            if plan_type == "platinum":
                await self.enable_platinum_features(guild_id)

            return True
        except Exception as e:
            logger.error(f"Error creating subscription for guild {guild_id}: {e}")
            return False

    async def get_subscription(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get the current subscription for a guild."""
        try:
            return await self.db_manager.fetch_one(
                """
                SELECT * FROM subscriptions
                WHERE guild_id = $1 AND is_active = 1
                ORDER BY end_date DESC LIMIT 1
                """,
                guild_id,
            )
        except Exception as e:
            logger.error(f"Error getting subscription for guild {guild_id}: {e}")
            return None

    async def cancel_subscription(self, guild_id: int) -> bool:
        """Cancel a guild's subscription."""
        try:
            # Mark current subscription as inactive
            await self.db_manager.execute(
                """
                UPDATE subscriptions
                SET is_active = 0
                WHERE guild_id = $1 AND is_active = 1
                """,
                guild_id,
            )

            # Update guild settings to mark as unpaid
            await self.db_manager.execute(
                "UPDATE guild_settings SET subscription_level = 'free' WHERE guild_id = $1",
                guild_id,
            )

            return True
        except Exception as e:
            logger.error(f"Error canceling subscription for guild {guild_id}: {e}")
            return False

    async def activate_subscription(self, guild_id: int) -> bool:
        """Activate a subscription for a guild."""
        try:
            await self.db_manager.execute(
                "UPDATE guild_settings SET subscription_level = 'premium' WHERE guild_id = $1",
                guild_id,
            )
            return True
        except Exception as e:
            logger.error(f"Error activating subscription for guild {guild_id}: {e}")
            return False

    async def deactivate_subscription(self, guild_id: int) -> bool:
        """Deactivate a subscription for a guild."""
        try:
            await self.db_manager.execute(
                "UPDATE guild_settings SET subscription_level = 'free' WHERE guild_id = $1",
                guild_id,
            )
            return True
        except Exception as e:
            logger.error(f"Error deactivating subscription for guild {guild_id}: {e}")
            return False

    async def check_subscription_status(self, guild_id: int) -> str:
        """Check if a guild has an active subscription and return the level."""
        try:
            result = await self.db_manager.fetch_one(
                "SELECT subscription_level FROM guild_settings WHERE guild_id = $1",
                guild_id,
            )
            return result.get("subscription_level", "free") if result else "free"
        except Exception as e:
            logger.error(
                f"Error checking subscription status for guild {guild_id}: {e}"
            )
            return "free"

    async def renew_subscription(self, guild_id: int) -> bool:
        """Renew a guild's subscription."""
        try:
            subscription = await self.get_subscription(guild_id)
            if not subscription:
                return False

            # Calculate new end date (30 days from current end date)
            new_end_date = subscription["end_date"] + timedelta(days=30)

            await self.db_manager.execute(
                """
                UPDATE subscriptions
                SET end_date = $1
                WHERE guild_id = $1 AND is_active = TRUE
                """,
                new_end_date,
                guild_id,
            )

            return True
        except Exception as e:
            logger.error(f"Error renewing subscription for guild {guild_id}: {e}")
            return False

    async def get_subscription_details(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed subscription information for a guild."""
        try:
            subscription = await self.get_subscription(guild_id)
            if not subscription:
                return None

            # Calculate days remaining
            days_remaining = (subscription["end_date"] - datetime.utcnow()).days

            return {
                "plan_type": subscription["plan_type"],
                "start_date": subscription["start_date"],
                "end_date": subscription["end_date"],
                "days_remaining": max(0, days_remaining),
                "is_active": subscription["is_active"],
            }
        except Exception as e:
            logger.error(
                f"Error getting subscription details for guild {guild_id}: {e}"
            )
            return None

    async def enable_platinum_features(self, guild_id: int) -> bool:
        """Enable all Platinum features for a guild."""
        try:
            # Enable Platinum features in guild_settings
            await self.db_manager.execute(
                """
                UPDATE guild_settings SET
                    platinum_features_enabled = TRUE,
                    custom_branding_enabled = TRUE,
                    advanced_analytics_enabled = TRUE,
                    api_access_enabled = TRUE,
                    priority_support_enabled = TRUE,
                    custom_commands_enabled = TRUE,
                    advanced_reporting_enabled = TRUE,
                    multi_guild_sync_enabled = TRUE,
                    webhook_integration_enabled = TRUE,
                    custom_embeds_enabled = TRUE,
                    real_time_alerts_enabled = TRUE,
                    data_export_enabled = TRUE
                WHERE guild_id = $1
                """,
                guild_id,
            )

            # Create Platinum features record
            await self.db_manager.execute(
                """
                INSERT INTO platinum_features (
                    guild_id, advanced_analytics, custom_branding, api_integration,
                    priority_support, custom_commands, advanced_reporting,
                    multi_guild_sync, webhook_integration, custom_embeds,
                    real_time_alerts, data_export
                ) VALUES ($1, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE)
                ON DUPLICATE KEY UPDATE
                    advanced_analytics = TRUE,
                    custom_branding = TRUE,
                    api_integration = TRUE,
                    priority_support = TRUE,
                    custom_commands = TRUE,
                    advanced_reporting = TRUE,
                    multi_guild_sync = TRUE,
                    webhook_integration = TRUE,
                    custom_embeds = TRUE,
                    real_time_alerts = TRUE,
                    data_export = TRUE
                """,
                guild_id,
            )

            return True
        except Exception as e:
            logger.error(f"Error enabling Platinum features for guild {guild_id}: {e}")
            return False

    async def disable_platinum_features(self, guild_id: int) -> bool:
        """Disable all Platinum features for a guild."""
        try:
            # Disable Platinum features in guild_settings
            await self.db_manager.execute(
                """
                UPDATE guild_settings SET
                    platinum_features_enabled = FALSE,
                    custom_branding_enabled = FALSE,
                    advanced_analytics_enabled = FALSE,
                    api_access_enabled = FALSE,
                    priority_support_enabled = FALSE,
                    custom_commands_enabled = FALSE,
                    advanced_reporting_enabled = FALSE,
                    multi_guild_sync_enabled = FALSE,
                    webhook_integration_enabled = FALSE,
                    custom_embeds_enabled = FALSE,
                    real_time_alerts_enabled = FALSE,
                    data_export_enabled = FALSE
                WHERE guild_id = $1
                """,
                guild_id,
            )

            # Disable Platinum features record
            await self.db_manager.execute(
                """
                UPDATE platinum_features SET
                    advanced_analytics = FALSE,
                    custom_branding = FALSE,
                    api_integration = FALSE,
                    priority_support = FALSE,
                    custom_commands = FALSE,
                    advanced_reporting = FALSE,
                    multi_guild_sync = FALSE,
                    webhook_integration = FALSE,
                    custom_embeds = FALSE,
                    real_time_alerts = FALSE,
                    data_export = FALSE
                WHERE guild_id = $1
                """,
                guild_id,
            )

            return True
        except Exception as e:
            logger.error(f"Error disabling Platinum features for guild {guild_id}: {e}")
            return False

    async def get_platinum_features(self, guild_id: int) -> Dict[str, Any]:
        """Get Platinum features status for a guild."""
        try:
            result = await self.db_manager.fetch_one(
                "SELECT * FROM platinum_features WHERE guild_id = $1",
                guild_id,
            )
            return result if result else {}
        except Exception as e:
            logger.error(f"Error getting Platinum features for guild {guild_id}: {e}")
            return {}

    async def is_platinum_guild(self, guild_id: int) -> bool:
        """Check if a guild has Platinum subscription."""
        try:
            subscription_level = await self.check_subscription_status(guild_id)
            return subscription_level == "platinum"
        except Exception as e:
            logger.error(f"Error checking Platinum status for guild {guild_id}: {e}")
            return False
