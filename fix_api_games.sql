-- Drop existing table and recreate with correct structure
DROP TABLE IF EXISTS api_games;

CREATE TABLE api_games (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_game_id VARCHAR(50) NOT NULL,  -- Changed to NOT NULL since it's required
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
    season VARCHAR(10) NULL,  -- Added season column
    raw_json JSON NOT NULL,
    fetched_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_game (sport, league_id, api_game_id)  -- Changed unique constraint
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Recreate indexes
CREATE INDEX idx_api_games_sport_league ON api_games (sport, league_name);
CREATE INDEX idx_api_games_season ON api_games (season);
CREATE INDEX idx_api_games_start_time ON api_games (start_time);
CREATE INDEX idx_api_games_status ON api_games (status); 