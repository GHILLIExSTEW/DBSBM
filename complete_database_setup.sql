-- ============================================
-- COMPLETE DATABASE SETUP FOR BETTING BOT
-- ============================================
-- This script creates all necessary tables and structures for the Discord betting bot
-- Run this script on your MySQL database to set up the complete schema

-- Set character set and collation
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET collation_connection = 'utf8mb4_unicode_ci';

-- ============================================
-- CORE TABLES
-- ============================================

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

-- Create indexes for games table
CREATE INDEX IF NOT EXISTS idx_games_league_status_time ON games (league_id, status, start_time);
CREATE INDEX IF NOT EXISTS idx_games_start_time ON games (start_time);
CREATE INDEX IF NOT EXISTS idx_games_status ON games (status);

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
    KEY game_id (game_id),
    CONSTRAINT bets_ibfk_1 FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Unit Records Table
CREATE TABLE IF NOT EXISTS unit_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    bet_serial BIGINT NOT NULL COMMENT 'FK to bets.bet_serial',
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    year INT NOT NULL COMMENT 'Year bet resolved',
    month INT NOT NULL COMMENT 'Month bet resolved (1-12)',
    units DECIMAL(15, 2) NOT NULL COMMENT 'Original stake',
    odds DECIMAL(10, 2) NOT NULL COMMENT 'Original odds',
    monthly_result_value DECIMAL(15, 2) NOT NULL COMMENT 'Net units won/lost for the bet',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp bet resolved',
    INDEX idx_unit_records_guild_user_ym (guild_id, user_id, year, month),
    INDEX idx_unit_records_year_month (year, month),
    INDEX idx_unit_records_user_id (user_id),
    INDEX idx_unit_records_guild_id (guild_id),
    FOREIGN KEY (bet_serial) REFERENCES bets(bet_serial) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- GUILD SETTINGS AND CONFIGURATION
-- ============================================

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

-- ============================================
-- SPORTS DATA TABLES
-- ============================================

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

-- Leagues Table
CREATE TABLE IF NOT EXISTS leagues (
    id BIGINT PRIMARY KEY COMMENT 'API League ID',
    name VARCHAR(150) NULL,
    sport VARCHAR(50) NOT NULL,
    type VARCHAR(50) NULL,
    logo VARCHAR(255) NULL,
    country VARCHAR(100) NULL,
    country_code CHAR(3) NULL,
    country_flag VARCHAR(255) NULL,
    season INTEGER NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX IF NOT EXISTS idx_leagues_sport_country ON leagues (sport, country);

-- Teams Table
CREATE TABLE IF NOT EXISTS teams (
    id BIGINT PRIMARY KEY COMMENT 'API Team ID',
    name VARCHAR(150) NULL,
    sport VARCHAR(50) NOT NULL,
    code VARCHAR(10) NULL,
    country VARCHAR(100) NULL,
    founded INTEGER NULL,
    national BOOLEAN DEFAULT FALSE,
    logo VARCHAR(255) NULL,
    venue_id BIGINT NULL,
    venue_name VARCHAR(150) NULL,
    venue_address VARCHAR(255) NULL,
    venue_city VARCHAR(100) NULL,
    venue_capacity INTEGER NULL,
    venue_surface VARCHAR(50) NULL,
    venue_image VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX IF NOT EXISTS idx_teams_sport_country ON teams (sport, country);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams (name);

-- Standings Table
CREATE TABLE IF NOT EXISTS standings (
    league_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,
    season INT NOT NULL,
    sport VARCHAR(50) NOT NULL,
    `rank` INTEGER NULL,
    points INTEGER NULL,
    goals_diff INTEGER NULL,
    form VARCHAR(20) NULL,
    status VARCHAR(50) NULL,
    description VARCHAR(100) NULL,
    group_name VARCHAR(100) NULL,
    played INTEGER DEFAULT 0,
    won INTEGER DEFAULT 0,
    draw INTEGER DEFAULT 0,
    lost INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (league_id, team_id, season)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX IF NOT EXISTS idx_standings_league_season_rank ON standings (league_id, season, `rank`);

-- ============================================
-- COMMUNITY AND EVENTS TABLES
-- ============================================

-- Game Events Table
CREATE TABLE IF NOT EXISTS game_events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    game_id BIGINT NOT NULL,
    guild_id BIGINT NULL,
    event_type VARCHAR(50) NOT NULL,
    details TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_game_events_game_time (game_id, created_at),
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bet Reactions Table
CREATE TABLE IF NOT EXISTS bet_reactions (
    reaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    bet_serial BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    emoji VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bet_reactions_bet (bet_serial),
    INDEX idx_bet_reactions_user (user_id),
    INDEX idx_bet_reactions_message (message_id),
    FOREIGN KEY (bet_serial) REFERENCES bets(bet_serial) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Community Metrics Table
CREATE TABLE IF NOT EXISTS community_metrics (
    metric_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_community_metrics_guild (guild_id),
    INDEX idx_community_metrics_type (metric_type),
    INDEX idx_community_metrics_time (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Community Achievements Table
CREATE TABLE IF NOT EXISTS community_achievements (
    achievement_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    achievement_type VARCHAR(50) NOT NULL,
    achievement_name VARCHAR(100) NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_community_achievements_user (user_id),
    INDEX idx_community_achievements_type (achievement_type),
    INDEX idx_community_achievements_guild (guild_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User Metrics Table
CREATE TABLE IF NOT EXISTS user_metrics (
    metric_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_metrics_user (user_id),
    INDEX idx_user_metrics_type (metric_type),
    INDEX idx_user_metrics_guild (guild_id),
    UNIQUE KEY unique_user_metric (guild_id, user_id, metric_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Community Events Table
CREATE TABLE IF NOT EXISTS community_events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_community_events_guild (guild_id),
    INDEX idx_community_events_type (event_type),
    INDEX idx_community_events_time (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- API AND DATA TABLES
-- ============================================

-- API Games Table
CREATE TABLE IF NOT EXISTS api_games (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_game_id VARCHAR(50) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    league_id VARCHAR(50) NOT NULL,
    season INT NOT NULL,
    home_team_name VARCHAR(150) NULL,
    away_team_name VARCHAR(150) NULL,
    start_time DATETIME NULL,
    end_time DATETIME NULL,
    status VARCHAR(50) NULL,
    score VARCHAR(20) NULL,
    raw_json JSON NOT NULL,
    fetched_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_game (sport, league_id, season, api_game_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX IF NOT EXISTS idx_api_games_sport_league ON api_games (sport, league_id);
CREATE INDEX IF NOT EXISTS idx_api_games_season ON api_games (season);

-- Players Table
CREATE TABLE IF NOT EXISTS players (
    player_name TEXT,
    dateBorn TEXT,
    idPlayeridTeam TEXT,
    strCutouts TEXT,
    strEthnicity TEXT,
    strGender TEXT,
    strHeight TEXT,
    strNationality TEXT,
    strNumber TEXT,
    strPlayer TEXT,
    strPosition TEXT,
    strSport TEXT,
    strTeam TEXT,
    strThumb TEXT,
    strWeight TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bet Legs Table
CREATE TABLE IF NOT EXISTS bet_legs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    bet_serial BIGINT NOT NULL,
    api_game_id VARCHAR(50) NULL,
    bet_type VARCHAR(50) NOT NULL,
    player_prop VARCHAR(255) NULL,
    player_id VARCHAR(50) NULL,
    line VARCHAR(255) NULL,
    odds DECIMAL(10,2) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bet_serial) REFERENCES bets(bet_serial) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PLATINUM TIER TABLES
-- ============================================

-- Platinum Features Table
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

-- Platinum Analytics Table
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

-- Webhook Integrations Table
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

-- Real-time Alerts Table
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

-- Data Exports Table
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

-- ============================================
-- MACHINE LEARNING TABLES
-- ============================================

-- ML Models Table
CREATE TABLE IF NOT EXISTS ml_models (
    model_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_type VARCHAR(50) NOT NULL COMMENT 'classification, regression, forecasting, clustering, recommendation, anomaly_detection',
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'inactive' COMMENT 'training, active, inactive, deprecated, error',
    model_path VARCHAR(500) COMMENT 'Path to model file',
    config JSON NOT NULL COMMENT 'Model configuration parameters',
    features JSON NOT NULL COMMENT 'List of feature names',
    target_variable VARCHAR(100) NOT NULL,
    performance_metrics JSON COMMENT 'Model performance metrics',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    trained_at TIMESTAMP NULL,
    deployed_at TIMESTAMP NULL,
    INDEX idx_model_type (model_type),
    INDEX idx_model_status (status),
    INDEX idx_model_name (name),
    INDEX idx_model_version (name, version),
    INDEX idx_model_created (created_at)
);

-- Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id VARCHAR(50) PRIMARY KEY,
    model_id VARCHAR(50) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL COMMENT 'bet_outcome, user_behavior, revenue_forecast, risk_assessment, churn_prediction, recommendation',
    input_data JSON NOT NULL COMMENT 'Input data for prediction',
    prediction_result JSON NOT NULL COMMENT 'Prediction output',
    confidence_score DECIMAL(5,4) NOT NULL COMMENT 'Confidence score 0.0-1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id BIGINT NULL,
    guild_id BIGINT NULL,
    INDEX idx_model_id (model_id),
    INDEX idx_prediction_type (prediction_type),
    INDEX idx_confidence_score (confidence_score),
    INDEX idx_created_at (created_at),
    INDEX idx_user_id (user_id),
    INDEX idx_guild_id (guild_id),
    FOREIGN KEY (model_id) REFERENCES ml_models(model_id) ON DELETE CASCADE
);

-- Model Performance Table
CREATE TABLE IF NOT EXISTS model_performance (
    performance_id VARCHAR(50) PRIMARY KEY,
    model_id VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,6) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dataset_size INT NOT NULL,
    evaluation_type VARCHAR(50) NOT NULL COMMENT 'train, test, validation',
    INDEX idx_model_id (model_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp),
    INDEX idx_evaluation_type (evaluation_type),
    FOREIGN KEY (model_id) REFERENCES ml_models(model_id) ON DELETE CASCADE
);

-- Feature Importance Table
CREATE TABLE IF NOT EXISTS feature_importance (
    feature_name VARCHAR(100) NOT NULL,
    importance_score DECIMAL(10,6) NOT NULL,
    rank INT NOT NULL,
    model_id VARCHAR(50) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_id, feature_name),
    INDEX idx_model_id (model_id),
    INDEX idx_importance_score (importance_score),
    INDEX idx_rank (rank),
    FOREIGN KEY (model_id) REFERENCES ml_models(model_id) ON DELETE CASCADE
);

-- ============================================
-- ADDITIONAL INDEXES FOR PERFORMANCE
-- ============================================

-- Platinum indexes
CREATE INDEX IF NOT EXISTS idx_platinum_features_guild ON platinum_features(guild_id);
CREATE INDEX IF NOT EXISTS idx_webhook_integrations_guild ON webhook_integrations(guild_id);
CREATE INDEX IF NOT EXISTS idx_real_time_alerts_guild ON real_time_alerts(guild_id);
CREATE INDEX IF NOT EXISTS idx_data_exports_guild ON data_exports(guild_id);

-- ML indexes
CREATE INDEX IF NOT EXISTS idx_predictions_model_type ON predictions (model_id, prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_user_guild ON predictions (user_id, guild_id);
CREATE INDEX IF NOT EXISTS idx_model_performance_model_metric ON model_performance (model_id, metric_name);
CREATE INDEX IF NOT EXISTS idx_feature_importance_model_rank ON feature_importance (model_id, rank);

-- ============================================
-- INSERT DEFAULT ML MODELS
-- ============================================

INSERT IGNORE INTO ml_models (model_id, name, description, model_type, version, status, config, features, target_variable) VALUES
('bet_outcome_predictor_v1', 'Bet Outcome Predictor', 'Predicts the outcome of sports bets', 'classification', '1.0.0', 'inactive',
 '{"algorithm": "random_forest", "hyperparameters": {"n_estimators": 100, "max_depth": 10}}',
 '["odds", "team_stats", "player_stats", "historical_performance", "weather", "venue"]',
 'outcome'),

('user_churn_predictor_v1', 'User Churn Predictor', 'Predicts user churn probability', 'classification', '1.0.0', 'inactive',
 '{"algorithm": "gradient_boosting", "hyperparameters": {"n_estimators": 200, "learning_rate": 0.1}}',
 '["activity_frequency", "betting_history", "engagement_metrics", "support_tickets", "account_age"]',
 'churn_probability'),

('revenue_forecaster_v1', 'Revenue Forecaster', 'Forecasts future revenue', 'forecasting', '1.0.0', 'inactive',
 '{"algorithm": "time_series", "hyperparameters": {"seasonality": 12, "trend": "additive"}}',
 '["historical_revenue", "user_growth", "seasonal_factors", "marketing_spend", "market_conditions"]',
 'revenue'),

('risk_assessor_v1', 'Risk Assessor', 'Assesses betting risk', 'regression', '1.0.0', 'inactive',
 '{"algorithm": "neural_network", "hyperparameters": {"layers": [64, 32, 16], "activation": "relu"}}',
 '["bet_amount", "user_history", "odds", "market_volatility", "external_factors"]',
 'risk_score');

-- ============================================
-- UPDATE DEFAULT VALUES
-- ============================================

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

-- ============================================
-- COMPLETION MESSAGE
-- ============================================

SELECT 'Database setup completed successfully!' as status;
SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = DATABASE();
