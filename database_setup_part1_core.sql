-- ============================================
-- DATABASE SETUP PART 1: CORE TABLES
-- ============================================
-- Run this first to create the essential tables

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET collation_connection = 'utf8mb4_unicode_ci';

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
    KEY game_id (game_id)
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
    INDEX idx_unit_records_guild_id (guild_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT 'Part 1: Core tables created successfully!' as status;
