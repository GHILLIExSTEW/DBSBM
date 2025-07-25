-- =========================
-- Migration 012: Comprehensive Guild Settings Update
-- Adds all missing columns for latest bot features
-- =========================

-- Main chat channel for community features
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS main_chat_channel_id BIGINT NULL
COMMENT 'Channel for achievement notifications and general community updates';

-- Embed channels for different types of embeds
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS embed_channel_id BIGINT NULL
COMMENT 'Channel for general betting embeds';

ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS parlay_embed_channel_id BIGINT NULL
COMMENT 'Channel for parlay betting embeds';

ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS player_prop_embed_channel_id BIGINT NULL
COMMENT 'Channel for player prop betting embeds';

-- Platinum tier features
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS platinum_webhook_url VARCHAR(500) NULL
COMMENT 'Discord webhook URL for Platinum tier notifications';

ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS platinum_alert_channel_id BIGINT NULL
COMMENT 'Channel for Platinum tier alerts and notifications';

ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS platinum_api_enabled BOOLEAN DEFAULT FALSE
COMMENT 'Whether Platinum API features are enabled';

-- Additional settings
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS auto_sync_commands BOOLEAN DEFAULT TRUE
COMMENT 'Whether to automatically sync commands on guild join';

ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS embed_color VARCHAR(7) DEFAULT '#00FF00'
COMMENT 'Default color for embeds (hex format)';

ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC'
COMMENT 'Timezone for date/time displays';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_guild_settings_main_chat
ON guild_settings(main_chat_channel_id);

CREATE INDEX IF NOT EXISTS idx_guild_settings_embed_channels
ON guild_settings(embed_channel_id, parlay_embed_channel_id, player_prop_embed_channel_id);

CREATE INDEX IF NOT EXISTS idx_guild_settings_platinum
ON guild_settings(platinum_alert_channel_id, platinum_api_enabled);

-- Update existing guilds with default values if needed
UPDATE guild_settings
SET auto_sync_commands = TRUE
WHERE auto_sync_commands IS NULL;

UPDATE guild_settings
SET embed_color = '#00FF00'
WHERE embed_color IS NULL;

UPDATE guild_settings
SET timezone = 'UTC'
WHERE timezone IS NULL;

UPDATE guild_settings
SET platinum_api_enabled = FALSE
WHERE platinum_api_enabled IS NULL;
