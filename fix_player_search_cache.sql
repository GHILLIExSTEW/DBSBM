-- Fix for player_search_cache table missing is_active column
-- This script adds the missing column that the application expects

-- Add is_active column to player_search_cache table
ALTER TABLE player_search_cache 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Add index for is_active column for better performance
CREATE INDEX IF NOT EXISTS idx_is_active ON player_search_cache(is_active);

-- Update all existing records to be active
UPDATE player_search_cache SET is_active = TRUE WHERE is_active IS NULL;

-- Verify the table structure
DESCRIBE player_search_cache; 