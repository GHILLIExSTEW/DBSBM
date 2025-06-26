-- Migration: Add result, result_description, and result_value columns to bets table
ALTER TABLE bets
  ADD COLUMN result VARCHAR(32) DEFAULT NULL,
  ADD COLUMN result_description TEXT DEFAULT NULL,
  ADD COLUMN result_value FLOAT DEFAULT NULL;
