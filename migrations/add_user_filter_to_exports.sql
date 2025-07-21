-- Add user_filter column to data_exports table
ALTER TABLE data_exports ADD COLUMN user_filter BIGINT NULL COMMENT 'User ID to filter export data by specific user';

-- Update existing records to have NULL user_filter (all users)
UPDATE data_exports SET user_filter = NULL WHERE user_filter IS NULL; 