-- Migration 008: Add notification channel support
-- Add notification_channel_id column to guild_settings table

ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS notification_channel_id BIGINT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_guild_settings_notification_channel ON guild_settings(notification_channel_id);

-- Add comment to document the new column
ALTER TABLE guild_settings 
MODIFY COLUMN notification_channel_id BIGINT DEFAULT NULL COMMENT 'Channel ID for private push notifications'; 