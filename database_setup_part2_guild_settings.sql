-- ============================================
-- DATABASE SETUP PART 2: GUILD SETTINGS
-- ============================================
-- Run this after Part 1 to create guild configuration tables

-- Guild Settings Table
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    is_active BOOLEAN DEFAULT TRUE,
    subscription_level VARCHAR(20) DEFAULT 'free',
    is_paid BOOLEAN DEFAULT FALSE,
    embed_channel_1 BIGINT NULL,
    embed_channel_2 BIGINT NULL,
    command_channel_1 BIGINT NULL,
    command_channel_2 BIGINT NULL,
    admin_channel_1 BIGINT NULL,
    admin_role BIGINT NULL,
    authorized_role BIGINT NULL,
    voice_channel_id BIGINT NULL COMMENT 'Monthly VC',
    yearly_channel_id BIGINT NULL COMMENT 'Yearly VC',
    total_units_channel_id BIGINT NULL,
    daily_report_time TEXT NULL,
    member_role BIGINT NULL,
    bot_name_mask TEXT NULL,
    bot_image_mask TEXT NULL,
    guild_default_image TEXT NULL,
    default_parlay_thumbnail TEXT NULL,
    total_result_value DECIMAL(15, 2) DEFAULT 0.0,
    min_units DECIMAL(15, 2) DEFAULT 0.1,
    max_units DECIMAL(15, 2) DEFAULT 10.0,
    live_game_updates TINYINT(1) DEFAULT 0 COMMENT 'Enable 15s live game updates',
    main_chat_channel_id BIGINT NULL COMMENT 'Channel for achievement notifications and general community updates',
    embed_channel_id BIGINT NULL COMMENT 'Channel for general betting embeds',
    parlay_embed_channel_id BIGINT NULL COMMENT 'Channel for parlay betting embeds',
    player_prop_embed_channel_id BIGINT NULL COMMENT 'Channel for player prop betting embeds',
    platinum_webhook_url VARCHAR(500) NULL COMMENT 'Discord webhook URL for Platinum tier notifications',
    platinum_alert_channel_id BIGINT NULL COMMENT 'Channel for Platinum tier alerts and notifications',
    platinum_api_enabled BOOLEAN DEFAULT FALSE COMMENT 'Whether Platinum API features are enabled',
    auto_sync_commands BOOLEAN DEFAULT TRUE COMMENT 'Whether to automatically sync commands on guild join',
    embed_color VARCHAR(7) DEFAULT '#00FF00' COMMENT 'Default color for embeds (hex format)',
    timezone VARCHAR(50) DEFAULT 'UTC' COMMENT 'Timezone for date/time displays',
    platinum_features_enabled BOOLEAN DEFAULT FALSE,
    custom_branding_enabled BOOLEAN DEFAULT FALSE,
    advanced_analytics_enabled BOOLEAN DEFAULT FALSE,
    api_access_enabled BOOLEAN DEFAULT FALSE,
    priority_support_enabled BOOLEAN DEFAULT FALSE,
    custom_commands_enabled BOOLEAN DEFAULT FALSE,
    advanced_reporting_enabled BOOLEAN DEFAULT FALSE,
    multi_guild_sync_enabled BOOLEAN DEFAULT FALSE,
    webhook_integration_enabled BOOLEAN DEFAULT FALSE,
    custom_embeds_enabled BOOLEAN DEFAULT FALSE,
    real_time_alerts_enabled BOOLEAN DEFAULT FALSE,
    data_export_enabled BOOLEAN DEFAULT FALSE,
    max_embed_channels_platinum INTEGER DEFAULT 5,
    max_command_channels_platinum INTEGER DEFAULT 5,
    max_active_bets_platinum INTEGER DEFAULT 100,
    max_custom_commands_platinum INTEGER DEFAULT 20,
    max_webhooks_platinum INTEGER DEFAULT 10,
    max_data_exports_platinum INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes for guild_settings
CREATE INDEX IF NOT EXISTS idx_guild_settings_main_chat ON guild_settings(main_chat_channel_id);
CREATE INDEX IF NOT EXISTS idx_guild_settings_embed_channels ON guild_settings(embed_channel_id, parlay_embed_channel_id, player_prop_embed_channel_id);
CREATE INDEX IF NOT EXISTS idx_guild_settings_platinum ON guild_settings(platinum_alert_channel_id, platinum_api_enabled);

-- Cappers Table
CREATE TABLE IF NOT EXISTS cappers (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    display_name VARCHAR(100) NULL,
    image_path VARCHAR(255) NULL,
    banner_color VARCHAR(7) NULL DEFAULT '#0096FF',
    bet_won INTEGER DEFAULT 0 NOT NULL,
    bet_loss INTEGER DEFAULT 0 NOT NULL,
    bet_push INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT 'Part 2: Guild settings tables created successfully!' as status;
