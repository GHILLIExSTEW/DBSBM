-- Phase 3 Database Migration Script
-- DBSBM System Advanced Features & Scalability
-- Date: December 2024

-- =====================================================
-- ANALYTICS TABLES
-- =====================================================

-- User analytics tracking
CREATE TABLE IF NOT EXISTS user_analytics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_guild_time (user_id, guild_id, timestamp),
    INDEX idx_event_type_time (event_type, timestamp),
    INDEX idx_timestamp (timestamp)
);

-- Betting pattern analysis
CREATE TABLE IF NOT EXISTS betting_patterns (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_data JSON,
    confidence_score DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_pattern (user_id, pattern_type),
    INDEX idx_confidence_score (confidence_score),
    INDEX idx_guild_pattern (guild_id, pattern_type)
);

-- ML model predictions
CREATE TABLE IF NOT EXISTS ml_predictions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    model_type VARCHAR(50) NOT NULL,
    prediction_data JSON,
    confidence_score DECIMAL(5,4),
    actual_result JSON,
    accuracy_score DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model_type (model_type),
    INDEX idx_accuracy_score (accuracy_score),
    INDEX idx_created_at (created_at)
);

-- Analytics dashboards
CREATE TABLE IF NOT EXISTS analytics_dashboards (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    guild_id BIGINT NOT NULL,
    dashboard_name VARCHAR(100) NOT NULL,
    dashboard_config JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_guild_active (guild_id, is_active)
);

-- =====================================================
-- INTEGRATION TABLES
-- =====================================================

-- Webhook configurations
CREATE TABLE IF NOT EXISTS webhook_integrations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    guild_id BIGINT NOT NULL,
    webhook_url VARCHAR(500) NOT NULL,
    webhook_type VARCHAR(50) NOT NULL,
    events JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_guild_type (guild_id, webhook_type),
    INDEX idx_active (is_active)
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT,
    guild_id BIGINT,
    endpoint VARCHAR(100) NOT NULL,
    request_data JSON,
    response_time INT,
    status_code INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_endpoint (user_id, endpoint),
    INDEX idx_timestamp (timestamp),
    INDEX idx_guild_endpoint (guild_id, endpoint)
);

-- Third-party integrations
CREATE TABLE IF NOT EXISTS third_party_integrations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    guild_id BIGINT NOT NULL,
    integration_type VARCHAR(50) NOT NULL,
    integration_config JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_guild_type (guild_id, integration_type)
);

-- =====================================================
-- SCALING TABLES
-- =====================================================

-- Load balancing configuration
CREATE TABLE IF NOT EXISTS load_balancer_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    instance_id VARCHAR(100) NOT NULL,
    instance_type VARCHAR(50) NOT NULL,
    region VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    health_status VARCHAR(20) DEFAULT 'healthy',
    last_health_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_instance_active (instance_id, is_active),
    INDEX idx_health_status (health_status)
);

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metric_time (metric_name, timestamp),
    INDEX idx_timestamp (timestamp)
);

-- System health monitoring
CREATE TABLE IF NOT EXISTS system_health (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    service_name VARCHAR(50) NOT NULL,
    health_status VARCHAR(20) NOT NULL,
    response_time INT,
    error_count INT DEFAULT 0,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_service_status (service_name, health_status),
    INDEX idx_last_check (last_check)
);

-- =====================================================
-- REAL-TIME FEATURES TABLES
-- =====================================================

-- WebSocket connections
CREATE TABLE IF NOT EXISTS websocket_connections (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    connection_id VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    disconnected_at TIMESTAMP NULL,
    INDEX idx_user_active (user_id, is_active),
    INDEX idx_guild_active (guild_id, is_active)
);

-- Real-time notifications
CREATE TABLE IF NOT EXISTS real_time_notifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    notification_data JSON,
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_sent (user_id, is_sent),
    INDEX idx_guild_type (guild_id, notification_type)
);

-- =====================================================
-- ENHANCE EXISTING TABLES
-- =====================================================

-- Add Platinum tier columns to guild_settings
ALTER TABLE guild_settings
ADD COLUMN IF NOT EXISTS analytics_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ml_features_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS webhook_limit INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS api_rate_limit INT DEFAULT 100,
ADD COLUMN IF NOT EXISTS real_time_features BOOLEAN DEFAULT FALSE;

-- Add user preferences for advanced features
ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS notification_preferences JSON,
ADD COLUMN IF NOT EXISTS analytics_consent BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ml_recommendations_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS webhook_notifications BOOLEAN DEFAULT FALSE;

-- Add ML-related columns to bets table
ALTER TABLE bets
ADD COLUMN IF NOT EXISTS ml_prediction_used BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS prediction_confidence DECIMAL(5,4) NULL,
ADD COLUMN IF NOT EXISTS ml_model_version VARCHAR(20) NULL;

-- =====================================================
-- SAMPLE DATA INSERTION
-- =====================================================

-- Insert sample analytics dashboard for testing
INSERT INTO analytics_dashboards (guild_id, dashboard_name, dashboard_config) VALUES
(1, 'Default Analytics Dashboard', '{"widgets": ["user_activity", "betting_trends", "performance_metrics"], "refresh_interval": 300}');

-- Insert sample webhook integration for testing
INSERT INTO webhook_integrations (guild_id, webhook_url, webhook_type, events) VALUES
(1, 'https://example.com/webhook', 'bet_notifications', '["bet_placed", "bet_resulted", "high_value_bet"]');

-- Insert sample performance metrics
INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, tags) VALUES
('api_response_time', 150.5, 'ms', '{"endpoint": "/api/games", "method": "GET"}'),
('cache_hit_rate', 85.2, 'percent', '{"cache_type": "redis", "data_type": "game_data"}'),
('database_query_time', 45.8, 'ms', '{"query_type": "select", "table": "bets"}');

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

-- Log migration completion
INSERT INTO system_health (service_name, health_status, response_time) VALUES
('database_migration', 'healthy', 0);

SELECT 'Phase 3 database migration completed successfully!' as status;
