-- =========================
-- ALL-IN-ONE DATABASE SCHEMA
-- =========================

-- =========================
-- Main Schema (schema.sql)
-- =========================
CREATE DATABASE IF NOT EXISTS betting_bot;
USE betting_bot;

ALTER TABLE bets ADD COLUMN IF NOT EXISTS bet_details JSON;

CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY,
    guild_name VARCHAR(255) NOT NULL,
    commands_registered BOOLEAN DEFAULT FALSE,
    subscription_status VARCHAR(50) DEFAULT 'free',
    subscription_end_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS guild_users (
    guild_id BIGINT,
    user_id BIGINT,
    is_admin BOOLEAN DEFAULT FALSE,
    is_capper BOOLEAN DEFAULT FALSE,
    units_balance FLOAT DEFAULT 0.0,
    lifetime_units FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id),
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bets (
    bet_serial BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    league VARCHAR(50) NOT NULL,
    bet_type VARCHAR(50) NOT NULL,
    bet_details JSON NOT NULL,
    units FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    result VARCHAR(20) DEFAULT NULL,
    confirmed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS unit_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    units FLOAT NOT NULL,
    total FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_monthly_record (guild_id, user_id, year, month)
);

CREATE TABLE IF NOT EXISTS games (
    game_id VARCHAR(50) PRIMARY KEY,
    league VARCHAR(50) NOT NULL,
    home_team VARCHAR(255) NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    score JSON,
    odds JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_logos (
    team_key VARCHAR(50) PRIMARY KEY,
    league VARCHAR(50) NOT NULL,
    logo_url VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =========================
-- SQLite Schema (sqlite_schema.sql)
-- =========================
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    voice_channel_id INTEGER,
    yearly_channel_id INTEGER,
    is_active INTEGER DEFAULT 1,
    is_paid INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS unit_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    result_value REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, user_id, year, month)
);

-- =========================
-- Add Subscriptions Table and Columns (003_add_subscriptions.sql)
-- =========================
ALTER TABLE guild_settings ADD COLUMN IF NOT EXISTS is_paid BOOLEAN DEFAULT FALSE;

ALTER TABLE subscriptions
    ADD COLUMN IF NOT EXISTS plan_type VARCHAR(50) NOT NULL DEFAULT 'premium',
    ADD COLUMN IF NOT EXISTS start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS end_date DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL 30 DAY),
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_guild_active ON subscriptions (guild_id, is_active);
CREATE INDEX IF NOT EXISTS idx_end_date ON subscriptions (end_date);

CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    plan_type VARCHAR(50) NOT NULL DEFAULT 'premium',
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    INDEX idx_guild_active (guild_id, is_active),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Fix Bets Table (fix_bets_table.sql)
-- =========================
DROP TABLE IF EXISTS bets;
CREATE TABLE bets (
    bet_serial BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    league VARCHAR(50) NOT NULL,
    bet_type VARCHAR(50) NOT NULL,
    bet_details JSON NOT NULL,
    units FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    result VARCHAR(20) DEFAULT NULL,
    confirmed BOOLEAN DEFAULT 0,
    channel_id BIGINT,
    odds FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_bets_guild_user ON bets(guild_id, user_id);
CREATE INDEX idx_bets_status ON bets(status);

CREATE TABLE IF NOT EXISTS api_games (
    id VARCHAR(50) PRIMARY KEY,
    league_id VARCHAR(50) NOT NULL,
    home_team_name VARCHAR(255) NOT NULL,
    away_team_name VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NULL,
    status VARCHAR(50) NOT NULL,
    score JSON,
    odds JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_games_league ON api_games(league_id);
CREATE INDEX idx_api_games_status ON api_games(status);
CREATE INDEX idx_api_games_start_time ON api_games(start_time);
CREATE INDEX idx_api_games_end_time ON api_games(end_time);
ALTER TABLE bets ADD COLUMN IF NOT EXISTS bet_details JSON;
CREATE INDEX idx_games_id ON games(id);
ALTER TABLE bets DROP FOREIGN KEY IF EXISTS bets_ibfk_1;
ALTER TABLE bets ADD CONSTRAINT bets_ibfk_1 FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL;

-- =========================
-- Add Game ID to Bets (004_add_game_id_to_bets.sql)
-- =========================
ALTER TABLE bets ADD COLUMN IF NOT EXISTS game_id BIGINT(20) DEFAULT NULL;
-- Optionally, add a foreign key constraint to api_games.id if desired:
-- ALTER TABLE bets ADD CONSTRAINT fk_bets_api_games FOREIGN KEY (game_id) REFERENCES api_games(id);

-- =========================
-- Fix Game ID Null (005_fix_game_id_null.sql)
-- =========================
ALTER TABLE bets MODIFY COLUMN game_id BIGINT(20) NULL DEFAULT NULL;
ALTER TABLE bets DROP FOREIGN KEY IF EXISTS bets_ibfk_1;
ALTER TABLE bets ADD CONSTRAINT bets_ibfk_1 FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL;

-- =========================
-- Add Result Columns to Bets (006_add_result_columns_to_bets.sql)
-- =========================
ALTER TABLE bets
  ADD COLUMN result VARCHAR(32) DEFAULT NULL,
  ADD COLUMN result_description TEXT DEFAULT NULL,
  ADD COLUMN result_value FLOAT DEFAULT NULL;

-- =========================
-- Fix API Games Table (fix_api_games.sql)
-- =========================
DROP TABLE IF EXISTS api_games;
CREATE TABLE api_games (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_game_id VARCHAR(50) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    league_id VARCHAR(50) NOT NULL,
    league_name VARCHAR(150) NULL,
    home_team_id BIGINT NULL,
    away_team_id BIGINT NULL,
    home_team_name VARCHAR(150) NULL,
    away_team_name VARCHAR(150) NULL,
    start_time TIMESTAMP NULL COMMENT 'Game start time in UTC',
    end_time TIMESTAMP NULL COMMENT 'Game end time in UTC (if known)',
    status VARCHAR(20) NULL COMMENT 'Game status (e.g., NS, LIVE, FT)',
    score JSON NULL COMMENT 'JSON storing scores',
    venue VARCHAR(150) NULL,
    referee VARCHAR(100) NULL,
    season VARCHAR(10) NULL,
    raw_json JSON NOT NULL,
    fetched_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_game (sport, league_id, api_game_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX idx_api_games_sport_league ON api_games (sport, league_name);
CREATE INDEX idx_api_games_season ON api_games (season);
CREATE INDEX idx_api_games_start_time ON api_games (start_time);
CREATE INDEX idx_api_games_status ON api_games (status);
