-- =========================
-- Migration 011: Add Main Chat Channel for Achievement Notifications
-- =========================

-- Add main_chat_channel_id column to guild_settings table
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS main_chat_channel_id BIGINT NULL COMMENT 'Channel for achievement notifications and general community updates';

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_guild_settings_main_chat ON guild_settings(main_chat_channel_id);

-- Update existing guilds to use their first text channel as main_chat if not set
-- This will be handled by the application logic when the migration runs

-- Add comment to document the purpose
ALTER TABLE guild_settings
MODIFY COLUMN main_chat_channel_id BIGINT NULL COMMENT 'Channel for achievement notifications and general community updates';
