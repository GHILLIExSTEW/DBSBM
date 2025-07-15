-- Enhanced Player Props Database Schema
-- This adds structured player prop data management

-- Player Props Table for storing available props
CREATE TABLE IF NOT EXISTS player_props (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    league VARCHAR(50) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    prop_type VARCHAR(50) NOT NULL COMMENT 'points, rebounds, assists, etc.',
    line_value DECIMAL(8,2) NOT NULL,
    over_odds DECIMAL(8,2),
    under_odds DECIMAL(8,2),
    game_id VARCHAR(50),
    api_game_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_player_team_league (player_name, team_name, league),
    INDEX idx_prop_type (prop_type),
    INDEX idx_game_id (game_id),
    INDEX idx_api_game_id (api_game_id),
    INDEX idx_is_active (is_active),
    INDEX idx_league_sport (league, sport)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Player Performance History Table
CREATE TABLE IF NOT EXISTS player_performance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    league VARCHAR(50) NOT NULL,
    game_id VARCHAR(50) NOT NULL,
    game_date DATE NOT NULL,
    prop_type VARCHAR(50) NOT NULL,
    actual_value DECIMAL(8,2) NOT NULL,
    line_value DECIMAL(8,2) NOT NULL,
    result ENUM('over', 'under', 'push') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_player_league_date (player_name, league, game_date),
    INDEX idx_prop_type (prop_type),
    INDEX idx_game_id (game_id),
    INDEX idx_result (result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Player Search Cache Table for fast autocomplete
CREATE TABLE IF NOT EXISTS player_search_cache (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    league VARCHAR(50) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    search_keywords TEXT NOT NULL COMMENT 'Normalized search terms',
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INT DEFAULT 1,

    UNIQUE KEY unique_player_team_league (player_name, team_name, league),
    INDEX idx_search_keywords (search_keywords(255)),
    INDEX idx_last_used (last_used),
    INDEX idx_usage_count (usage_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add columns to existing bets table if they don't exist
ALTER TABLE bets
ADD COLUMN IF NOT EXISTS player_prop_type VARCHAR(50) NULL COMMENT 'Type of player prop (points, rebounds, etc.)',
ADD COLUMN IF NOT EXISTS player_prop_line DECIMAL(8,2) NULL COMMENT 'The line value for the prop',
ADD COLUMN IF NOT EXISTS player_prop_direction ENUM('over', 'under') NULL COMMENT 'Over or under the line',
ADD COLUMN IF NOT EXISTS player_prop_result DECIMAL(8,2) NULL COMMENT 'Actual result for the prop';

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_bets_player_prop ON bets(player_prop_type, player_prop_line);
CREATE INDEX IF NOT EXISTS idx_bets_player_name ON bets(player_name);
