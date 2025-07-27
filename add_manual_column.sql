-- Add is_manual column to bets table
ALTER TABLE bets ADD COLUMN IF NOT EXISTS is_manual BOOLEAN DEFAULT FALSE COMMENT 'Whether this bet was entered manually';

-- Add home_team and away_team columns if they don't exist
ALTER TABLE bets ADD COLUMN IF NOT EXISTS home_team VARCHAR(150) DEFAULT NULL COMMENT 'Home team name for manual bets';
ALTER TABLE bets ADD COLUMN IF NOT EXISTS away_team VARCHAR(150) DEFAULT NULL COMMENT 'Away team name for manual bets';

-- Add bet_selection column if it doesn't exist
ALTER TABLE bets ADD COLUMN IF NOT EXISTS bet_selection VARCHAR(255) DEFAULT NULL COMMENT 'Bet selection for manual bets';

-- Add bet_amount column if it doesn't exist (rename units if needed)
ALTER TABLE bets ADD COLUMN IF NOT EXISTS bet_amount DECIMAL(10,2) DEFAULT NULL COMMENT 'Bet amount for manual bets';

SELECT 'Manual bet columns added successfully!' as status;
