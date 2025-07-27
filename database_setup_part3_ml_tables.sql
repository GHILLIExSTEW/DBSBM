-- ============================================
-- DATABASE SETUP PART 3: MACHINE LEARNING TABLES
-- ============================================
-- Run this to create ML tables and fix the ml_models error

-- ML Models Table
CREATE TABLE IF NOT EXISTS ml_models (
    model_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_type VARCHAR(50) NOT NULL COMMENT 'classification, regression, forecasting, clustering, recommendation, anomaly_detection',
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'inactive' COMMENT 'training, active, inactive, deprecated, error',
    model_path VARCHAR(500) COMMENT 'Path to model file',
    config JSON NOT NULL COMMENT 'Model configuration parameters',
    features JSON NOT NULL COMMENT 'List of feature names',
    target_variable VARCHAR(100) NOT NULL,
    performance_metrics JSON COMMENT 'Model performance metrics',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    trained_at TIMESTAMP NULL,
    deployed_at TIMESTAMP NULL,
    INDEX idx_model_type (model_type),
    INDEX idx_model_status (status),
    INDEX idx_model_name (name),
    INDEX idx_model_version (name, version),
    INDEX idx_model_created (created_at)
);

-- Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id VARCHAR(50) PRIMARY KEY,
    model_id VARCHAR(50) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL COMMENT 'bet_outcome, user_behavior, revenue_forecast, risk_assessment, churn_prediction, recommendation',
    input_data JSON NOT NULL COMMENT 'Input data for prediction',
    prediction_result JSON NOT NULL COMMENT 'Prediction output',
    confidence_score DECIMAL(5,4) NOT NULL COMMENT 'Confidence score 0.0-1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id BIGINT NULL,
    guild_id BIGINT NULL,
    INDEX idx_model_id (model_id),
    INDEX idx_prediction_type (prediction_type),
    INDEX idx_confidence_score (confidence_score),
    INDEX idx_created_at (created_at),
    INDEX idx_user_id (user_id),
    INDEX idx_guild_id (guild_id),
    FOREIGN KEY (model_id) REFERENCES ml_models(model_id) ON DELETE CASCADE
);

-- Model Performance Table
CREATE TABLE IF NOT EXISTS model_performance (
    performance_id VARCHAR(50) PRIMARY KEY,
    model_id VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,6) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dataset_size INT NOT NULL,
    evaluation_type VARCHAR(50) NOT NULL COMMENT 'train, test, validation',
    INDEX idx_model_id (model_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp),
    INDEX idx_evaluation_type (evaluation_type),
    FOREIGN KEY (model_id) REFERENCES ml_models(model_id) ON DELETE CASCADE
);

-- Feature Importance Table
CREATE TABLE IF NOT EXISTS feature_importance (
    feature_name VARCHAR(100) NOT NULL,
    importance_score DECIMAL(10,6) NOT NULL,
    rank INT NOT NULL,
    model_id VARCHAR(50) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_id, feature_name),
    INDEX idx_model_id (model_id),
    INDEX idx_importance_score (importance_score),
    INDEX idx_rank (rank),
    FOREIGN KEY (model_id) REFERENCES ml_models(model_id) ON DELETE CASCADE
);

-- Insert default model templates
INSERT IGNORE INTO ml_models (model_id, name, description, model_type, version, status, config, features, target_variable) VALUES
('bet_outcome_predictor_v1', 'Bet Outcome Predictor', 'Predicts the outcome of sports bets', 'classification', '1.0.0', 'inactive',
 '{"algorithm": "random_forest", "hyperparameters": {"n_estimators": 100, "max_depth": 10}}',
 '["odds", "team_stats", "player_stats", "historical_performance", "weather", "venue"]',
 'outcome'),

('user_churn_predictor_v1', 'User Churn Predictor', 'Predicts user churn probability', 'classification', '1.0.0', 'inactive',
 '{"algorithm": "gradient_boosting", "hyperparameters": {"n_estimators": 200, "learning_rate": 0.1}}',
 '["activity_frequency", "betting_history", "engagement_metrics", "support_tickets", "account_age"]',
 'churn_probability'),

('revenue_forecaster_v1', 'Revenue Forecaster', 'Forecasts future revenue', 'forecasting', '1.0.0', 'inactive',
 '{"algorithm": "time_series", "hyperparameters": {"seasonality": 12, "trend": "additive"}}',
 '["historical_revenue", "user_growth", "seasonal_factors", "marketing_spend", "market_conditions"]',
 'revenue'),

('risk_assessor_v1', 'Risk Assessor', 'Assesses betting risk', 'regression', '1.0.0', 'inactive',
 '{"algorithm": "neural_network", "hyperparameters": {"layers": [64, 32, 16], "activation": "relu"}}',
 '["bet_amount", "user_history", "odds", "market_volatility", "external_factors"]',
 'risk_score');

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_predictions_model_type ON predictions (model_id, prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_user_guild ON predictions (user_id, guild_id);
CREATE INDEX IF NOT EXISTS idx_model_performance_model_metric ON model_performance (model_id, metric_name);
CREATE INDEX IF NOT EXISTS idx_feature_importance_model_rank ON feature_importance (model_id, rank);

SELECT 'Part 3: ML tables created successfully! ml_models error should be resolved.' as status;
