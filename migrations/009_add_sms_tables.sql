-- Migration 009: Add SMS functionality tables
-- Create tables for SMS notifications and phone number management

-- Table for storing user phone numbers
CREATE TABLE IF NOT EXISTS user_phone_numbers (
    user_id BIGINT PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    country_code VARCHAR(3) DEFAULT '+1',
    verified BOOLEAN DEFAULT FALSE,
    verification_code VARCHAR(6),
    verification_expires TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_phone_verified (verified),
    INDEX idx_user_phone_number (phone_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for SMS logs
CREATE TABLE IF NOT EXISTS sms_logs (
    sms_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    message_content TEXT NOT NULL,
    twilio_sid VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP NULL,
    error_message TEXT,
    INDEX idx_sms_logs_user (user_id),
    INDEX idx_sms_logs_status (status),
    INDEX idx_sms_logs_time (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add comments for documentation
ALTER TABLE user_phone_numbers 
MODIFY COLUMN phone_number VARCHAR(20) NOT NULL COMMENT 'User phone number for SMS notifications';

ALTER TABLE sms_logs 
MODIFY COLUMN twilio_sid VARCHAR(50) COMMENT 'Twilio message SID for tracking'; 