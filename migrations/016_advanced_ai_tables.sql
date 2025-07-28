-- Migration 016: Advanced AI Tables
-- Adds comprehensive advanced AI and machine learning infrastructure

-- AI Models table
CREATE TABLE IF NOT EXISTS advanced_ai_models (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    model_type ENUM('predictive_analytics', 'nlp', 'computer_vision', 'reinforcement_learning', 'multi_modal', 'deep_learning', 'transformer', 'generative_ai') NOT NULL,
    version VARCHAR(50) NOT NULL,
    status ENUM('training', 'evaluating', 'deployed', 'archived', 'failed', 'a_b_testing') NOT NULL,
    performance ENUM('excellent', 'good', 'average', 'poor', 'failed') NOT NULL,
    accuracy DECIMAL(5,4) DEFAULT 0.0000,
    model_precision DECIMAL(5,4) DEFAULT 0.0000,
    model_recall DECIMAL(5,4) DEFAULT 0.0000,
    f1_score DECIMAL(5,4) DEFAULT 0.0000,
    training_data_size INT DEFAULT 0,
    features JSON NOT NULL,
    hyperparameters JSON NOT NULL,
    model_path VARCHAR(500) NOT NULL,
    description TEXT NULL,
    tags JSON NOT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deployed_at TIMESTAMP NULL,
    INDEX idx_model_id (model_id),
    INDEX idx_model_type (model_type),
    INDEX idx_status (status),
    INDEX idx_performance (performance),
    INDEX idx_created_at (created_at)
);

-- AI Predictions table
CREATE TABLE IF NOT EXISTS ai_predictions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prediction_id VARCHAR(255) NOT NULL UNIQUE,
    model_id VARCHAR(255) NOT NULL,
    input_data JSON NOT NULL,
    prediction JSON NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    probabilities JSON NOT NULL,
    features_used JSON NOT NULL,
    prediction_time TIMESTAMP NOT NULL,
    processing_time DECIMAL(10,6) NOT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prediction_id (prediction_id),
    INDEX idx_model_id (model_id),
    INDEX idx_prediction_time (prediction_time),
    INDEX idx_confidence (confidence),
    FOREIGN KEY (model_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE
);

-- NLP Results table
CREATE TABLE IF NOT EXISTS nlp_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nlp_id VARCHAR(255) NOT NULL UNIQUE,
    text TEXT NOT NULL,
    sentiment VARCHAR(50) NOT NULL,
    sentiment_score DECIMAL(5,4) NOT NULL,
    entities JSON NOT NULL,
    keywords JSON NOT NULL,
    language VARCHAR(10) NOT NULL,
    processing_time DECIMAL(10,6) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_nlp_id (nlp_id),
    INDEX idx_sentiment (sentiment),
    INDEX idx_language (language),
    INDEX idx_created_at (created_at)
);

-- Computer Vision Results table
CREATE TABLE IF NOT EXISTS computer_vision_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cv_id VARCHAR(255) NOT NULL UNIQUE,
    image_path VARCHAR(500) NOT NULL,
    objects_detected JSON NOT NULL,
    text_extracted TEXT NOT NULL,
    face_analysis JSON NOT NULL,
    image_quality DECIMAL(5,4) NOT NULL,
    processing_time DECIMAL(10,6) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cv_id (cv_id),
    INDEX idx_image_quality (image_quality),
    INDEX idx_confidence (confidence),
    INDEX idx_created_at (created_at)
);

-- Reinforcement Learning States table
CREATE TABLE IF NOT EXISTS reinforcement_learning_states (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    rl_id VARCHAR(255) NOT NULL UNIQUE,
    state JSON NOT NULL,
    action VARCHAR(255) NOT NULL,
    reward DECIMAL(10,6) NOT NULL,
    next_state JSON NOT NULL,
    episode INT NOT NULL,
    step INT NOT NULL,
    learning_rate DECIMAL(10,6) NOT NULL,
    exploration_rate DECIMAL(10,6) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rl_id (rl_id),
    INDEX idx_episode (episode),
    INDEX idx_step (step),
    INDEX idx_timestamp (timestamp)
);

-- Model Training Jobs table
CREATE TABLE IF NOT EXISTS model_training_jobs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id VARCHAR(255) NOT NULL UNIQUE,
    model_type ENUM('predictive_analytics', 'nlp', 'computer_vision', 'reinforcement_learning', 'multi_modal', 'deep_learning', 'transformer', 'generative_ai') NOT NULL,
    training_data JSON NOT NULL,
    hyperparameters JSON NOT NULL,
    status VARCHAR(50) NOT NULL,
    progress DECIMAL(5,4) DEFAULT 0.0000,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NULL,
    metrics JSON NOT NULL,
    error_message TEXT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_job_id (job_id),
    INDEX idx_model_type (model_type),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
);

-- AI Model Performance Metrics table
CREATE TABLE IF NOT EXISTS ai_model_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_timestamp TIMESTAMP NOT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model_id (model_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_metric_timestamp (metric_timestamp),
    FOREIGN KEY (model_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE
);

-- AI Model Versions table
CREATE TABLE IF NOT EXISTS ai_model_versions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_data LONGBLOB NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model_id (model_id),
    INDEX idx_version (version),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (model_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE
);

-- AI Model A/B Tests table
CREATE TABLE IF NOT EXISTS ai_model_ab_tests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    test_id VARCHAR(255) NOT NULL UNIQUE,
    test_name VARCHAR(255) NOT NULL,
    model_a_id VARCHAR(255) NOT NULL,
    model_b_id VARCHAR(255) NOT NULL,
    traffic_split DECIMAL(5,4) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NULL,
    status ENUM('running', 'completed', 'stopped') NOT NULL,
    winner_model_id VARCHAR(255) NULL,
    test_metrics JSON NOT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_test_id (test_id),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time),
    FOREIGN KEY (model_a_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE,
    FOREIGN KEY (model_b_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE,
    FOREIGN KEY (winner_model_id) REFERENCES advanced_ai_models(model_id) ON DELETE SET NULL
);

-- Insert default AI models
INSERT INTO advanced_ai_models (
    model_id, name, model_type, version, status, performance,
    accuracy, model_precision, model_recall, f1_score, training_data_size,
    features, hyperparameters, model_path, description, tags, metadata
) VALUES
(
    'default-predictive-analytics-001',
    'Default Predictive Analytics Model',
    'predictive_analytics',
    '1.0.0',
    'deployed',
    'good',
    0.8500, 0.8200, 0.8800, 0.8500, 1000,
    '["feature1", "feature2", "feature3"]',
    '{"learning_rate": 0.001, "batch_size": 32, "epochs": 100}',
    'models/default-predictive-analytics-001_1.0.0.pkl',
    'Default predictive analytics model for betting insights',
    '["predictive_analytics", "default"]',
    '{"created_by": "system", "framework": "scikit-learn"}'
),
(
    'default-nlp-001',
    'Default NLP Model',
    'nlp',
    '1.0.0',
    'deployed',
    'good',
    0.8200, 0.8000, 0.8500, 0.8200, 500,
    '["text", "language", "context"]',
    '{"learning_rate": 0.001, "batch_size": 16, "epochs": 50}',
    'models/default-nlp-001_1.0.0.pkl',
    'Default natural language processing model',
    '["nlp", "default"]',
    '{"created_by": "system", "framework": "transformers"}'
),
(
    'default-computer-vision-001',
    'Default Computer Vision Model',
    'computer_vision',
    '1.0.0',
    'deployed',
    'good',
    0.8800, 0.8600, 0.9000, 0.8800, 2000,
    '["image", "resolution", "channels"]',
    '{"learning_rate": 0.0001, "batch_size": 8, "epochs": 100}',
    'models/default-computer-vision-001_1.0.0.pkl',
    'Default computer vision model for image analysis',
    '["computer_vision", "default"]',
    '{"created_by": "system", "framework": "pytorch"}'
),
(
    'default-reinforcement-learning-001',
    'Default Reinforcement Learning Model',
    'reinforcement_learning',
    '1.0.0',
    'deployed',
    'good',
    0.7500, 0.7300, 0.7800, 0.7500, 5000,
    '["state", "action", "reward"]',
    '{"learning_rate": 0.01, "discount_factor": 0.95, "epsilon": 0.1}',
    'models/default-reinforcement-learning-001_1.0.0.pkl',
    'Default reinforcement learning model for optimization',
    '["reinforcement_learning", "default"]',
    '{"created_by": "system", "framework": "stable-baselines3"}'
);

-- Insert sample training jobs
INSERT INTO model_training_jobs (
    job_id, model_type, training_data, hyperparameters, status,
    progress, start_time, metrics, metadata
) VALUES
(
    'training-job-001',
    'predictive_analytics',
    '{"dataset_size": 1000, "features": ["feature1", "feature2"]}',
    '{"learning_rate": 0.001, "batch_size": 32}',
    'completed',
    1.0000,
    NOW() - INTERVAL 1 HOUR,
    '{"accuracy": 0.85, "precision": 0.82, "recall": 0.88}',
    '{"dataset": "sample_data", "framework": "scikit-learn"}'
),
(
    'training-job-002',
    'nlp',
    '{"dataset_size": 500, "text_samples": 1000}',
    '{"learning_rate": 0.001, "batch_size": 16}',
    'completed',
    1.0000,
    NOW() - INTERVAL 2 HOUR,
    '{"accuracy": 0.82, "precision": 0.80, "recall": 0.85}',
    '{"dataset": "nlp_data", "framework": "transformers"}'
);

-- Insert sample predictions
INSERT INTO ai_predictions (
    prediction_id, model_id, input_data, prediction, confidence,
    probabilities, features_used, prediction_time, processing_time, metadata
) VALUES
(
    'pred-001',
    'default-predictive-analytics-001',
    '{"feature1": 0.5, "feature2": 0.3}',
    '"win"',
    0.8500,
    '{"win": 0.85, "loss": 0.15}',
    '["feature1", "feature2"]',
    NOW(),
    0.050000,
    '{"user_id": 123, "session_id": "abc123"}'
),
(
    'pred-002',
    'default-nlp-001',
    '{"text": "This is a great betting opportunity"}',
    '"positive"',
    0.8200,
    '{"positive": 0.82, "negative": 0.18}',
    '["text", "language"]',
    NOW(),
    0.030000,
    '{"user_id": 456, "session_id": "def456"}'
);

-- Insert sample NLP results
INSERT INTO nlp_results (
    nlp_id, text, sentiment, sentiment_score, entities, keywords,
    language, processing_time, confidence, metadata
) VALUES
(
    'nlp-001',
    'This is a great betting opportunity with high confidence',
    'positive',
    0.7500,
    '[{"text": "betting opportunity", "type": "OPPORTUNITY"}]',
    '["betting", "opportunity", "confidence"]',
    'en',
    0.025000,
    0.8200,
    '{"user_id": 123, "analysis_type": "sentiment"}'
),
(
    'nlp-002',
    'The odds are not favorable for this bet',
    'negative',
    0.6500,
    '[{"text": "odds", "type": "METRIC"}]',
    '["odds", "favorable", "bet"]',
    'en',
    0.020000,
    0.7800,
    '{"user_id": 456, "analysis_type": "sentiment"}'
);

-- Insert sample computer vision results
INSERT INTO computer_vision_results (
    cv_id, image_path, objects_detected, text_extracted, face_analysis,
    image_quality, processing_time, confidence, metadata
) VALUES
(
    'cv-001',
    '/images/betting_slip.jpg',
    '[{"name": "document", "confidence": 0.95}, {"name": "text", "confidence": 0.90}]',
    'Betting slip with odds and predictions',
    '{"count": 0, "emotions": []}',
    0.8500,
    0.150000,
    0.9000,
    '{"user_id": 123, "image_type": "betting_slip"}'
),
(
    'cv-002',
    '/images/sports_team.jpg',
    '[{"name": "person", "confidence": 0.88}, {"name": "uniform", "confidence": 0.92}]',
    'Team logo and player names',
    '{"count": 5, "emotions": ["happy", "confident"]}',
    0.9200,
    0.200000,
    0.8800,
    '{"user_id": 456, "image_type": "team_photo"}'
);

-- Insert sample reinforcement learning states
INSERT INTO reinforcement_learning_states (
    rl_id, state, action, reward, next_state, episode, step,
    learning_rate, exploration_rate, timestamp, metadata
) VALUES
(
    'rl-001',
    '{"user_engagement": 0.8, "betting_activity": 0.6}',
    'recommend_bet',
    0.7500,
    '{"user_engagement": 0.85, "betting_activity": 0.7}',
    1,
    10,
    0.010000,
    0.100000,
    NOW(),
    '{"user_id": 123, "session_id": "abc123"}'
),
(
    'rl-002',
    '{"system_performance": 0.9, "user_satisfaction": 0.7}',
    'optimize_interface',
    0.8500,
    '{"system_performance": 0.92, "user_satisfaction": 0.75}',
    1,
    15,
    0.010000,
    0.100000,
    NOW(),
    '{"system_id": "main", "optimization_type": "interface"}'
);

-- Insert sample model metrics
INSERT INTO ai_model_metrics (
    model_id, metric_name, metric_value, metric_timestamp, metadata
) VALUES
(
    'default-predictive-analytics-001',
    'predictions_per_hour',
    150.000000,
    NOW(),
    '{"period": "hourly", "source": "real_time"}'
),
(
    'default-predictive-analytics-001',
    'average_confidence',
    0.850000,
    NOW(),
    '{"period": "hourly", "source": "real_time"}'
),
(
    'default-nlp-001',
    'texts_processed',
    75.000000,
    NOW(),
    '{"period": "hourly", "source": "real_time"}'
),
(
    'default-nlp-001',
    'average_sentiment_accuracy',
    0.820000,
    NOW(),
    '{"period": "hourly", "source": "real_time"}'
);

-- Create indexes for better performance
CREATE INDEX idx_ai_predictions_model_time ON ai_predictions(model_id, prediction_time);
CREATE INDEX idx_nlp_results_sentiment_time ON nlp_results(sentiment, created_at);
CREATE INDEX idx_cv_results_quality_time ON computer_vision_results(image_quality, created_at);
CREATE INDEX idx_rl_states_episode_step ON reinforcement_learning_states(episode, step);
CREATE INDEX idx_training_jobs_type_status ON model_training_jobs(model_type, status);
CREATE INDEX idx_model_metrics_name_time ON ai_model_metrics(metric_name, metric_timestamp);

-- Add comments for documentation
ALTER TABLE advanced_ai_models COMMENT = 'Advanced AI models for predictive analytics, NLP, computer vision, and reinforcement learning';
ALTER TABLE ai_predictions COMMENT = 'AI model predictions with confidence scores and metadata';
ALTER TABLE nlp_results COMMENT = 'Natural language processing results including sentiment analysis';
ALTER TABLE computer_vision_results COMMENT = 'Computer vision analysis results for image processing';
ALTER TABLE reinforcement_learning_states COMMENT = 'Reinforcement learning states and actions for system optimization';
ALTER TABLE model_training_jobs COMMENT = 'AI model training jobs with progress tracking';
ALTER TABLE ai_model_metrics COMMENT = 'Performance metrics for AI models';
ALTER TABLE ai_model_versions COMMENT = 'Versioned AI model data for deployment and rollback';
ALTER TABLE ai_model_ab_tests COMMENT = 'A/B testing configuration for AI model comparison';
