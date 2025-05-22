import mysql.connector
import os
from dotenv import load_dotenv

# Load .env file from the betting-bot directory
dotenv_path = os.path.join('betting-bot', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Database connection configuration
config = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DB')
}

# SQL statements
sql_statements = """
-- Drop existing table and recreate with correct structure
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
"""

def apply_fix():
    try:
        # Connect to the database
        print("Attempting to connect with config:", {k: v if k != 'password' else '***' for k, v in config.items()})
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Execute each statement
        for statement in sql_statements.split(';'):
            if statement.strip():
                cursor.execute(statement.strip() + ';')
        
        # Commit the changes
        conn.commit()
        print("Database fix applied successfully!")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    apply_fix() 