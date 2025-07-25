-- =========================
-- Add Platinum Tier Channel Columns
-- =========================

-- Add additional embed channels for Platinum tier (total of 5)
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS embed_channel_3 BIGINT NULL,
ADD COLUMN IF NOT EXISTS embed_channel_4 BIGINT NULL,
ADD COLUMN IF NOT EXISTS embed_channel_5 BIGINT NULL;

-- Add additional command channels for Platinum tier (total of 5)
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS command_channel_3 BIGINT NULL,
ADD COLUMN IF NOT EXISTS command_channel_4 BIGINT NULL,
ADD COLUMN IF NOT EXISTS command_channel_5 BIGINT NULL;

-- Add additional admin channels for Platinum tier (total of 5)
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS admin_channel_2 BIGINT NULL,
ADD COLUMN IF NOT EXISTS admin_channel_3 BIGINT NULL,
ADD COLUMN IF NOT EXISTS admin_channel_4 BIGINT NULL,
ADD COLUMN IF NOT EXISTS admin_channel_5 BIGINT NULL;

-- Add Platinum-specific channel columns
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS platinum_webhook_channel_id BIGINT NULL,
ADD COLUMN IF NOT EXISTS platinum_analytics_channel_id BIGINT NULL,
ADD COLUMN IF NOT EXISTS platinum_export_channel_id BIGINT NULL,
ADD COLUMN IF NOT EXISTS platinum_api_channel_id BIGINT NULL,
ADD COLUMN IF NOT EXISTS platinum_alerts_channel_id BIGINT NULL;

-- Add comments to document the Platinum tier channel structure
ALTER TABLE guild_settings
MODIFY COLUMN embed_channel_1 BIGINT NULL COMMENT 'Primary embed channel (Free/Premium/Platinum)',
MODIFY COLUMN embed_channel_2 BIGINT NULL COMMENT 'Secondary embed channel (Premium/Platinum)',
MODIFY COLUMN embed_channel_3 BIGINT NULL COMMENT 'Tertiary embed channel (Platinum only)',
MODIFY COLUMN embed_channel_4 BIGINT NULL COMMENT 'Quaternary embed channel (Platinum only)',
MODIFY COLUMN embed_channel_5 BIGINT NULL COMMENT 'Quinary embed channel (Platinum only)',
MODIFY COLUMN command_channel_1 BIGINT NULL COMMENT 'Primary command channel (Free/Premium/Platinum)',
MODIFY COLUMN command_channel_2 BIGINT NULL COMMENT 'Secondary command channel (Premium/Platinum)',
MODIFY COLUMN command_channel_3 BIGINT NULL COMMENT 'Tertiary command channel (Platinum only)',
MODIFY COLUMN command_channel_4 BIGINT NULL COMMENT 'Quaternary command channel (Platinum only)',
MODIFY COLUMN command_channel_5 BIGINT NULL COMMENT 'Quinary command channel (Platinum only)',
MODIFY COLUMN admin_channel_1 BIGINT NULL COMMENT 'Primary admin channel (Free/Premium/Platinum)',
MODIFY COLUMN admin_channel_2 BIGINT NULL COMMENT 'Secondary admin channel (Platinum only)',
MODIFY COLUMN admin_channel_3 BIGINT NULL COMMENT 'Tertiary admin channel (Platinum only)',
MODIFY COLUMN admin_channel_4 BIGINT NULL COMMENT 'Quaternary admin channel (Platinum only)',
MODIFY COLUMN admin_channel_5 BIGINT NULL COMMENT 'Quinary admin channel (Platinum only)';

-- Add indexes for the new channel columns
CREATE INDEX IF NOT EXISTS idx_embed_channel_3 ON guild_settings(embed_channel_3);
CREATE INDEX IF NOT EXISTS idx_embed_channel_4 ON guild_settings(embed_channel_4);
CREATE INDEX IF NOT EXISTS idx_embed_channel_5 ON guild_settings(embed_channel_5);
CREATE INDEX IF NOT EXISTS idx_command_channel_3 ON guild_settings(command_channel_3);
CREATE INDEX IF NOT EXISTS idx_command_channel_4 ON guild_settings(command_channel_4);
CREATE INDEX IF NOT EXISTS idx_command_channel_5 ON guild_settings(command_channel_5);
CREATE INDEX IF NOT EXISTS idx_admin_channel_2 ON guild_settings(admin_channel_2);
CREATE INDEX IF NOT EXISTS idx_admin_channel_3 ON guild_settings(admin_channel_3);
CREATE INDEX IF NOT EXISTS idx_admin_channel_4 ON guild_settings(admin_channel_4);
CREATE INDEX IF NOT EXISTS idx_admin_channel_5 ON guild_settings(admin_channel_5);
CREATE INDEX IF NOT EXISTS idx_platinum_webhook_channel ON guild_settings(platinum_webhook_channel_id);
CREATE INDEX IF NOT EXISTS idx_platinum_analytics_channel ON guild_settings(platinum_analytics_channel_id);
CREATE INDEX IF NOT EXISTS idx_platinum_export_channel ON guild_settings(platinum_export_channel_id);
CREATE INDEX IF NOT EXISTS idx_platinum_api_channel ON guild_settings(platinum_api_channel_id);
CREATE INDEX IF NOT EXISTS idx_platinum_alerts_channel ON guild_settings(platinum_alerts_channel_id);
