-- =========================
-- Add Platinum Tier Support
-- =========================

-- Add subscription_level column if it doesn't exist
ALTER TABLE guild_settings ADD COLUMN IF NOT EXISTS subscription_level VARCHAR(20) DEFAULT 'free';

-- Update existing premium subscriptions to ensure consistency
UPDATE guild_settings SET subscription_level = 'premium' WHERE is_paid = 1 AND subscription_level != 'premium';

-- Add Platinum-specific features table
CREATE TABLE IF NOT EXISTS platinum_features (
    guild_id BIGINT PRIMARY KEY,
    advanced_analytics BOOLEAN DEFAULT FALSE,
    custom_branding BOOLEAN DEFAULT FALSE,
    api_integration BOOLEAN DEFAULT FALSE,
    priority_support BOOLEAN DEFAULT FALSE,
    custom_commands BOOLEAN DEFAULT FALSE,
    advanced_reporting BOOLEAN DEFAULT FALSE,
    multi_guild_sync BOOLEAN DEFAULT FALSE,
    webhook_integration BOOLEAN DEFAULT FALSE,
    custom_embeds BOOLEAN DEFAULT FALSE,
    real_time_alerts BOOLEAN DEFAULT FALSE,
    data_export BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- Add Platinum-specific settings
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS platinum_features_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS custom_branding_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS advanced_analytics_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS api_access_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS priority_support_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS custom_commands_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS advanced_reporting_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS multi_guild_sync_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS webhook_integration_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS custom_embeds_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS real_time_alerts_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS data_export_enabled BOOLEAN DEFAULT FALSE;

-- Add Platinum-specific limits
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS max_embed_channels_platinum INTEGER DEFAULT 5,
ADD COLUMN IF NOT EXISTS max_command_channels_platinum INTEGER DEFAULT 5,
ADD COLUMN IF NOT EXISTS max_active_bets_platinum INTEGER DEFAULT 100,
ADD COLUMN IF NOT EXISTS max_custom_commands_platinum INTEGER DEFAULT 20,
ADD COLUMN IF NOT EXISTS max_webhooks_platinum INTEGER DEFAULT 10,
ADD COLUMN IF NOT EXISTS max_data_exports_platinum INTEGER DEFAULT 50;

-- Create Platinum analytics table
CREATE TABLE IF NOT EXISTS platinum_analytics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    INDEX idx_guild_feature (guild_id, feature_name)
);



-- Create webhook integrations table for Platinum
CREATE TABLE IF NOT EXISTS webhook_integrations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    webhook_name VARCHAR(100) NOT NULL,
    webhook_url VARCHAR(500) NOT NULL,
    webhook_type VARCHAR(50) NOT NULL, -- 'bet_created', 'bet_resulted', 'analytics', etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- Create real-time alerts table for Platinum
CREATE TABLE IF NOT EXISTS real_time_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'bet_created', 'bet_resulted', 'user_activity', etc.
    alert_conditions JSON NOT NULL,
    alert_channel_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- Create data exports table for Platinum
CREATE TABLE IF NOT EXISTS data_exports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    export_type VARCHAR(50) NOT NULL, -- 'bets', 'analytics', 'users', etc.
    export_format VARCHAR(20) NOT NULL, -- 'csv', 'json', 'xlsx'
    export_data JSON,
    file_path VARCHAR(500),
    is_completed BOOLEAN DEFAULT FALSE,
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);





-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_platinum_features_guild ON platinum_features(guild_id);
CREATE INDEX IF NOT EXISTS idx_webhook_integrations_guild ON webhook_integrations(guild_id);
CREATE INDEX IF NOT EXISTS idx_real_time_alerts_guild ON real_time_alerts(guild_id);
CREATE INDEX IF NOT EXISTS idx_data_exports_guild ON data_exports(guild_id);
