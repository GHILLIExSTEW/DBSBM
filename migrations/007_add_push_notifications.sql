-- Migration 007: Add push notifications table
-- This table tracks push notifications sent to member roles for analytics

CREATE TABLE IF NOT EXISTS push_notifications (
    notification_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    priority VARCHAR(20) DEFAULT 'normal',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_push_notifications_guild (guild_id),
    INDEX idx_push_notifications_type (notification_type),
    INDEX idx_push_notifications_time (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add member_role column to guild_settings if it doesn't exist
ALTER TABLE guild_settings 
ADD COLUMN IF NOT EXISTS member_role BIGINT DEFAULT NULL;

-- Add index for member_role lookups
CREATE INDEX IF NOT EXISTS idx_guild_settings_member_role ON guild_settings(member_role);

-- Insert sample data for testing (optional)
-- INSERT INTO push_notifications (guild_id, channel_id, notification_type, title, message, priority) 
-- VALUES (123456789, 987654321, 'community', 'Welcome to the Community!', 'Welcome to our betting community!', 'normal'); 