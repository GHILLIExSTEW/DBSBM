-- Migration: Add game_id column to bets table if it does not exist
ALTER TABLE bets ADD COLUMN IF NOT EXISTS game_id BIGINT(20) DEFAULT NULL;
-- Optionally, add a foreign key constraint to api_games.id if desired:
-- ALTER TABLE bets ADD CONSTRAINT fk_bets_api_games FOREIGN KEY (game_id) REFERENCES api_games(id);
