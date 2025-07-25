-- Migration 010: Remove notification functionality tables and columns
-- This migration removes all tables and columns related to push notifications and SMS

-- Drop SMS-related tables
DROP TABLE IF EXISTS sms_logs;
DROP TABLE IF EXISTS user_phone_numbers;

-- Drop push notification table
DROP TABLE IF EXISTS push_notifications;

-- Remove notification-related columns from guild_settings
ALTER TABLE guild_settings
DROP COLUMN IF EXISTS member_role,
DROP COLUMN IF EXISTS notification_channel_id;

-- Remove any indexes related to notifications
DROP INDEX IF EXISTS idx_guild_settings_notification_channel ON guild_settings;
