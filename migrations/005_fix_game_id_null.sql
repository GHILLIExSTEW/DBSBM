-- Ensure game_id column is properly defined as NULL
ALTER TABLE bets MODIFY COLUMN game_id BIGINT(20) NULL DEFAULT NULL;

-- Drop and recreate the foreign key constraint to ensure it allows NULL values
ALTER TABLE bets DROP FOREIGN KEY IF EXISTS bets_ibfk_1;
ALTER TABLE bets ADD CONSTRAINT bets_ibfk_1 FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL; 