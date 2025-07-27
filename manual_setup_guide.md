# Manual Database Setup Guide

If the automated scripts are giving you 403 errors, follow this manual setup guide.

## Step 1: Connect to Your Database

Open your MySQL client (phpMyAdmin, MySQL Workbench, or command line) and connect to your database.

## Step 2: Run These Commands One by One

### Quick Fix for ml_models Error
```sql
CREATE TABLE IF NOT EXISTS ml_models (
    model_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
    model_path VARCHAR(500),
    config JSON NOT NULL,
    features JSON NOT NULL,
    target_variable VARCHAR(100) NOT NULL,
    performance_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    trained_at TIMESTAMP NULL,
    deployed_at TIMESTAMP NULL
);

INSERT IGNORE INTO ml_models (model_id, name, description, model_type, version, status, config, features, target_variable) VALUES
('default_model', 'Default Model', 'Default placeholder model', 'classification', '1.0.0', 'inactive',
 '{"algorithm": "placeholder"}',
 '["placeholder"]',
 'placeholder');
```

### Core Tables
```sql
-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY COMMENT 'Discord User ID',
    username VARCHAR(100) NULL COMMENT 'Last known Discord username',
    balance DECIMAL(15, 2) DEFAULT 1000.00 NOT NULL,
    frozen_balance DECIMAL(15, 2) DEFAULT 0.00 NOT NULL,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Games Table
CREATE TABLE IF NOT EXISTS games (
    id BIGINT PRIMARY KEY COMMENT 'API Fixture ID',
    sport VARCHAR(50) NOT NULL,
    league_id BIGINT NULL,
    league_name VARCHAR(150) NULL,
    home_team_id BIGINT NULL,
    away_team_id BIGINT NULL,
    home_team_name VARCHAR(150) NULL,
    away_team_name VARCHAR(150) NULL,
    home_team_logo VARCHAR(255) NULL,
    away_team_logo VARCHAR(255) NULL,
    start_time TIMESTAMP NULL COMMENT 'Game start time in UTC',
    end_time TIMESTAMP NULL COMMENT 'Game end time in UTC (if known)',
    status VARCHAR(20) NULL COMMENT 'Game status (e.g., NS, LIVE, FT)',
    score JSON NULL COMMENT 'JSON storing scores',
    venue VARCHAR(150) NULL,
    referee VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bets Table
CREATE TABLE IF NOT EXISTS bets (
    bet_serial BIGINT(20) NOT NULL AUTO_INCREMENT,
    event_id VARCHAR(255) DEFAULT NULL,
    guild_id BIGINT(20) NOT NULL,
    message_id BIGINT(20) DEFAULT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    user_id BIGINT(20) NOT NULL,
    game_id BIGINT(20) DEFAULT NULL,
    bet_type VARCHAR(50) DEFAULT NULL,
    player_prop VARCHAR(255) DEFAULT NULL,
    player_id VARCHAR(50) DEFAULT NULL,
    league VARCHAR(50) NOT NULL,
    team VARCHAR(100) DEFAULT NULL,
    opponent VARCHAR(50) DEFAULT NULL,
    line VARCHAR(255) DEFAULT NULL,
    odds DECIMAL(10,2) DEFAULT NULL,
    units DECIMAL(10,2) NOT NULL,
    legs INT(11) DEFAULT NULL,
    bet_won TINYINT(4) DEFAULT 0,
    bet_loss TINYINT(4) DEFAULT 0,
    confirmed TINYINT(4) DEFAULT 0,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    game_start DATETIME DEFAULT NULL,
    result_value DECIMAL(15,2) DEFAULT NULL,
    result_description TEXT,
    expiration_time TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    channel_id BIGINT(20) DEFAULT NULL,
    bet_details LONGTEXT NOT NULL,
    PRIMARY KEY (bet_serial),
    KEY guild_id (guild_id),
    KEY user_id (user_id),
    KEY status (status),
    KEY created_at (created_at),
    KEY game_id (game_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Guild Settings Table
```sql
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
```

## Step 3: Verify Setup

Run this query to check if tables were created:
```sql
SHOW TABLES;
```

You should see at least:
- ml_models
- users
- games
- bets
- guild_settings

## Step 4: Test the Bot

After running these commands, try starting your bot again. The ml_models error should be resolved.

## Troubleshooting

If you still get errors:
1. Check your MySQL version supports JSON data type
2. Make sure you have proper permissions on the database
3. Try running commands one at a time to identify which one fails
4. Check the MySQL error logs for more details
