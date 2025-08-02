-- ============================================
-- PostgreSQL Migration Script for DBSBM Database
-- ============================================
-- This script creates all tables for the Discord Betting Sports Bot Manager
-- Combines all migrations into a single PostgreSQL-compatible script

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Core Tables (from all_schema.sql)
-- ============================================

-- Guilds table
CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY,
    guild_name VARCHAR(255) NOT NULL,
    commands_registered BOOLEAN DEFAULT FALSE,
    subscription_status VARCHAR(50) DEFAULT 'free',
    subscription_end_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guild Users table
CREATE TABLE IF NOT EXISTS guild_users (
    guild_id BIGINT,
    user_id BIGINT,
    is_admin BOOLEAN DEFAULT FALSE,
    is_capper BOOLEAN DEFAULT FALSE,
    units_balance FLOAT DEFAULT 0.0,
    lifetime_units FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id),
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Guild Settings table
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    voice_channel_id BIGINT,
    yearly_channel_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    is_paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- Games table
CREATE TABLE IF NOT EXISTS games (
    game_id VARCHAR(50) PRIMARY KEY,
    league VARCHAR(50) NOT NULL,
    home_team VARCHAR(255) NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    score JSONB,
    odds JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Team Logos table
CREATE TABLE IF NOT EXISTS team_logos (
    team_key VARCHAR(50) PRIMARY KEY,
    league VARCHAR(50) NOT NULL,
    logo_url VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Games table
CREATE TABLE IF NOT EXISTS api_games (
    id BIGSERIAL PRIMARY KEY,
    api_game_id VARCHAR(50) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    league_id VARCHAR(50) NOT NULL,
    league_name VARCHAR(150) NULL,
    home_team_id BIGINT NULL,
    away_team_id BIGINT NULL,
    home_team_name VARCHAR(150) NULL,
    away_team_name VARCHAR(150) NULL,
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    status VARCHAR(20) NULL,
    score JSONB NULL,
    venue VARCHAR(150) NULL,
    referee VARCHAR(100) NULL,
    season VARCHAR(10) NULL,
    raw_json JSONB NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (sport, league_id, api_game_id)
);

-- Bets table
CREATE TABLE IF NOT EXISTS bets (
    bet_serial BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    league VARCHAR(50) NOT NULL,
    bet_type VARCHAR(50) NOT NULL,
    bet_details JSONB NOT NULL,
    units FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    result VARCHAR(20) DEFAULT NULL,
    confirmed BOOLEAN DEFAULT FALSE,
    channel_id BIGINT,
    odds FLOAT,
    game_id BIGINT,
    result_description TEXT DEFAULT NULL,
    result_value FLOAT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Unit Records table
CREATE TABLE IF NOT EXISTS unit_records (
    record_id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    units FLOAT NOT NULL,
    total FLOAT DEFAULT 0,
    result_value FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (guild_id, user_id, year, month)
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    plan_type VARCHAR(50) NOT NULL DEFAULT 'premium',
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- ============================================
-- Platinum Tier Tables (from 004_add_platinum_tier.sql)
-- ============================================

-- Platinum Features table
CREATE TABLE IF NOT EXISTS platinum_features (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_type VARCHAR(50) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    UNIQUE (guild_id, feature_name)
);

-- Platinum Analytics table
CREATE TABLE IF NOT EXISTS platinum_analytics (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- Webhook Integrations table
CREATE TABLE IF NOT EXISTS webhook_integrations (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    webhook_url VARCHAR(500) NOT NULL,
    webhook_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    events JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- Real Time Alerts table
CREATE TABLE IF NOT EXISTS real_time_alerts (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_message TEXT NOT NULL,
    channel_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- Data Exports table
CREATE TABLE IF NOT EXISTS data_exports (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    export_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- API Usage Tracking table
CREATE TABLE IF NOT EXISTS api_usage_tracking (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    api_endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 0,
    last_request TIMESTAMP,
    rate_limit_remaining INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- Platinum Subscription History table
CREATE TABLE IF NOT EXISTS platinum_subscription_history (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    changed_by BIGINT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- ============================================
-- Predictive Service Tables (from 007_predictive_service_tables.sql)
-- ============================================

-- ML Models table
CREATE TABLE IF NOT EXISTS ml_models (
    id BIGSERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    accuracy FLOAT DEFAULT 0.0,
    precision FLOAT DEFAULT 0.0,
    recall FLOAT DEFAULT 0.0,
    f1_score FLOAT DEFAULT 0.0,
    training_data_size INTEGER DEFAULT 0,
    features JSONB NOT NULL,
    hyperparameters JSONB NOT NULL,
    model_path VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'training',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    model_id BIGINT NOT NULL,
    input_data JSONB NOT NULL,
    prediction JSONB NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES ml_models(id) ON DELETE CASCADE
);

-- Model Performance table
CREATE TABLE IF NOT EXISTS model_performance (
    id BIGSERIAL PRIMARY KEY,
    model_id BIGINT NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES ml_models(id) ON DELETE CASCADE
);

-- Feature Importance table
CREATE TABLE IF NOT EXISTS feature_importance (
    id BIGSERIAL PRIMARY KEY,
    model_id BIGINT NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    importance_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES ml_models(id) ON DELETE CASCADE
);

-- ============================================
-- Advanced AI Tables (from 016_advanced_ai_tables.sql)
-- ============================================

-- Advanced AI Models table
CREATE TABLE IF NOT EXISTS advanced_ai_models (
    id BIGSERIAL PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) NOT NULL CHECK (model_type IN ('predictive_analytics', 'nlp', 'computer_vision', 'reinforcement_learning', 'multi_modal', 'deep_learning', 'transformer', 'generative_ai')),
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('training', 'evaluating', 'deployed', 'archived', 'failed', 'a_b_testing')),
    performance VARCHAR(50) NOT NULL CHECK (performance IN ('excellent', 'good', 'average', 'poor', 'failed')),
    accuracy DECIMAL(5,4) DEFAULT 0.0000,
    model_precision DECIMAL(5,4) DEFAULT 0.0000,
    model_recall DECIMAL(5,4) DEFAULT 0.0000,
    f1_score DECIMAL(5,4) DEFAULT 0.0000,
    training_data_size INTEGER DEFAULT 0,
    features JSONB NOT NULL,
    hyperparameters JSONB NOT NULL,
    model_path VARCHAR(500) NOT NULL,
    description TEXT NULL,
    tags JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployed_at TIMESTAMP NULL
);

-- AI Predictions table
CREATE TABLE IF NOT EXISTS ai_predictions (
    id BIGSERIAL PRIMARY KEY,
    prediction_id VARCHAR(255) NOT NULL UNIQUE,
    model_id VARCHAR(255) NOT NULL,
    input_data JSONB NOT NULL,
    prediction JSONB NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    probabilities JSONB NOT NULL,
    features_used JSONB NOT NULL,
    prediction_time TIMESTAMP NOT NULL,
    processing_time DECIMAL(10,6) NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE
);

-- NLP Results table
CREATE TABLE IF NOT EXISTS nlp_results (
    id BIGSERIAL PRIMARY KEY,
    nlp_id VARCHAR(255) NOT NULL UNIQUE,
    text TEXT NOT NULL,
    sentiment VARCHAR(50) NOT NULL,
    sentiment_score DECIMAL(5,4) NOT NULL,
    entities JSONB NOT NULL,
    keywords JSONB NOT NULL,
    language VARCHAR(10) NOT NULL,
    processing_time DECIMAL(10,6) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Computer Vision Results table
CREATE TABLE IF NOT EXISTS computer_vision_results (
    id BIGSERIAL PRIMARY KEY,
    cv_id VARCHAR(255) NOT NULL UNIQUE,
    image_path VARCHAR(500) NOT NULL,
    objects_detected JSONB NOT NULL,
    text_extracted TEXT NOT NULL,
    face_analysis JSONB NOT NULL,
    image_quality DECIMAL(5,4) NOT NULL,
    processing_time DECIMAL(10,6) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reinforcement Learning States table
CREATE TABLE IF NOT EXISTS reinforcement_learning_states (
    id BIGSERIAL PRIMARY KEY,
    rl_id VARCHAR(255) NOT NULL UNIQUE,
    state JSONB NOT NULL,
    action VARCHAR(255) NOT NULL,
    reward DECIMAL(10,6) NOT NULL,
    next_state JSONB NOT NULL,
    episode INTEGER NOT NULL,
    step INTEGER NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    environment_id VARCHAR(255) NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model Training Jobs table
CREATE TABLE IF NOT EXISTS model_training_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(255) NOT NULL UNIQUE,
    model_id VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    error_message TEXT,
    config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE
);

-- AI Model Metrics table
CREATE TABLE IF NOT EXISTS ai_model_metrics (
    id BIGSERIAL PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_timestamp TIMESTAMP NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE
);

-- AI Model Versions table
CREATE TABLE IF NOT EXISTS ai_model_versions (
    id BIGSERIAL PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL,
    version_number VARCHAR(50) NOT NULL,
    version_description TEXT,
    model_path VARCHAR(500) NOT NULL,
    performance_metrics JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE
);

-- AI Model A/B Tests table
CREATE TABLE IF NOT EXISTS ai_model_ab_tests (
    id BIGSERIAL PRIMARY KEY,
    test_id VARCHAR(255) NOT NULL UNIQUE,
    test_name VARCHAR(255) NOT NULL,
    model_a_id VARCHAR(255) NOT NULL,
    model_b_id VARCHAR(255) NOT NULL,
    traffic_split DECIMAL(5,4) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('active', 'completed', 'stopped')),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    winner VARCHAR(255),
    metrics JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_a_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE,
    FOREIGN KEY (model_b_id) REFERENCES advanced_ai_models(model_id) ON DELETE CASCADE
);

-- ============================================
-- Advanced Analytics Tables (from 017_advanced_analytics_tables.sql)
-- ============================================

-- Analytics Dashboards table
CREATE TABLE IF NOT EXISTS analytics_dashboards (
    id BIGSERIAL PRIMARY KEY,
    dashboard_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    dashboard_type VARCHAR(50) NOT NULL CHECK (dashboard_type IN ('real_time', 'historical', 'predictive', 'operational', 'executive', 'technical')),
    description TEXT NOT NULL,
    widgets JSONB NOT NULL,
    layout JSONB NOT NULL,
    refresh_interval INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL
);

-- Analytics Widgets table
CREATE TABLE IF NOT EXISTS analytics_widgets (
    id BIGSERIAL PRIMARY KEY,
    widget_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    chart_type VARCHAR(50) NOT NULL CHECK (chart_type IN ('line', 'bar', 'pie', 'scatter', 'area', 'heatmap', 'gauge', 'table', 'kpi', 'funnel')),
    data_source VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    config JSONB NOT NULL,
    position JSONB NOT NULL,
    size JSONB NOT NULL,
    refresh_interval INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL
);

-- Analytics Metrics table
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL CHECK (metric_type IN ('counter', 'gauge', 'histogram', 'summary', 'percentile', 'rate', 'delta')),
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    tags JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Reports table
CREATE TABLE IF NOT EXISTS analytics_reports (
    id BIGSERIAL PRIMARY KEY,
    report_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    data JSONB NOT NULL,
    charts JSONB NOT NULL,
    insights JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    scheduled BOOLEAN DEFAULT FALSE,
    schedule_config JSONB NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Forecasts table
CREATE TABLE IF NOT EXISTS analytics_forecasts (
    id BIGSERIAL PRIMARY KEY,
    forecast_id VARCHAR(255) NOT NULL UNIQUE,
    metric_name VARCHAR(255) NOT NULL,
    forecast_type VARCHAR(100) NOT NULL,
    predictions JSONB NOT NULL,
    confidence_intervals JSONB NOT NULL,
    timestamps JSONB NOT NULL,
    accuracy DECIMAL(5,4) NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL
);

-- Analytics Insights table
CREATE TABLE IF NOT EXISTS analytics_insights (
    id BIGSERIAL PRIMARY KEY,
    insight_id VARCHAR(255) NOT NULL UNIQUE,
    insight_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    impact_score DECIMAL(5,4) NOT NULL,
    data_points JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL
);

-- Analytics Alerts table
CREATE TABLE IF NOT EXISTS analytics_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_id VARCHAR(255) NOT NULL UNIQUE,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('active', 'acknowledged', 'resolved')),
    threshold_value DECIMAL(15,6),
    current_value DECIMAL(15,6),
    triggered_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Data Aggregations table
CREATE TABLE IF NOT EXISTS analytics_data_aggregations (
    id BIGSERIAL PRIMARY KEY,
    aggregation_id VARCHAR(255) NOT NULL UNIQUE,
    metric_name VARCHAR(255) NOT NULL,
    time_period VARCHAR(50) NOT NULL,
    aggregation_type VARCHAR(50) NOT NULL,
    value DECIMAL(15,6) NOT NULL,
    count_records INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Visualizations table
CREATE TABLE IF NOT EXISTS analytics_visualizations (
    id BIGSERIAL PRIMARY KEY,
    visualization_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    visualization_type VARCHAR(100) NOT NULL,
    data_source VARCHAR(255) NOT NULL,
    config JSONB NOT NULL,
    rendered_image_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL
);

-- ============================================
-- System Integration Tables (from 018_system_integration_tables.sql)
-- ============================================

-- Service Instances table
CREATE TABLE IF NOT EXISTS service_instances (
    id BIGSERIAL PRIMARY KEY,
    service_id VARCHAR(255) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    instance_id VARCHAR(255) NOT NULL UNIQUE,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    health_endpoint VARCHAR(255) DEFAULT '/health',
    status VARCHAR(50) NOT NULL DEFAULT 'starting',
    load_balancer_weight INTEGER DEFAULT 1,
    max_connections INTEGER DEFAULT 100,
    current_connections INTEGER DEFAULT 0,
    response_time FLOAT DEFAULT 0.0,
    last_health_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service Registry table
CREATE TABLE IF NOT EXISTS service_registry (
    id BIGSERIAL PRIMARY KEY,
    service_id VARCHAR(255) NOT NULL UNIQUE,
    service_type VARCHAR(100) NOT NULL,
    health_check_interval INTEGER DEFAULT 30,
    circuit_breaker_threshold INTEGER DEFAULT 5,
    circuit_breaker_timeout INTEGER DEFAULT 60,
    load_balancer_type VARCHAR(50) DEFAULT 'round_robin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Gateways table
CREATE TABLE IF NOT EXISTS api_gateways (
    id BIGSERIAL PRIMARY KEY,
    gateway_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    routes JSONB,
    rate_limits JSONB,
    authentication_required BOOLEAN DEFAULT TRUE,
    cors_enabled BOOLEAN DEFAULT TRUE,
    logging_enabled BOOLEAN DEFAULT TRUE,
    monitoring_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Load Balancers table
CREATE TABLE IF NOT EXISTS load_balancers (
    id BIGSERIAL PRIMARY KEY,
    balancer_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    balancer_type VARCHAR(50) NOT NULL,
    instances JSONB,
    health_check_path VARCHAR(255) DEFAULT '/health',
    health_check_interval INTEGER DEFAULT 30,
    session_sticky BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Circuit Breakers table
CREATE TABLE IF NOT EXISTS circuit_breakers (
    id BIGSERIAL PRIMARY KEY,
    breaker_id VARCHAR(255) NOT NULL UNIQUE,
    service_id VARCHAR(255) NOT NULL,
    failure_threshold INTEGER DEFAULT 5,
    timeout_seconds INTEGER DEFAULT 60,
    state VARCHAR(50) DEFAULT 'closed',
    failure_count INTEGER DEFAULT 0,
    last_failure_time TIMESTAMP,
    last_success_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deployment Configurations table
CREATE TABLE IF NOT EXISTS deployment_configs (
    id BIGSERIAL PRIMARY KEY,
    config_id VARCHAR(255) NOT NULL UNIQUE,
    service_type VARCHAR(100) NOT NULL,
    environment VARCHAR(50) NOT NULL,
    config_data JSONB NOT NULL,
    version VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service Metrics table
CREATE TABLE IF NOT EXISTS service_metrics (
    id BIGSERIAL PRIMARY KEY,
    service_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    tags JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deployment History table
CREATE TABLE IF NOT EXISTS deployment_history (
    id BIGSERIAL PRIMARY KEY,
    deployment_id VARCHAR(255) NOT NULL UNIQUE,
    service_id VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'rolled_back')),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    logs TEXT,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service Mesh Config table
CREATE TABLE IF NOT EXISTS service_mesh_config (
    id BIGSERIAL PRIMARY KEY,
    service_type VARCHAR(100) NOT NULL,
    mesh_config JSONB NOT NULL,
    routing_rules JSONB NOT NULL,
    security_policies JSONB NOT NULL,
    observability_config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Distributed Tracing table
CREATE TABLE IF NOT EXISTS distributed_tracing (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(255) NOT NULL,
    span_id VARCHAR(255) NOT NULL,
    parent_span_id VARCHAR(255),
    service_name VARCHAR(255) NOT NULL,
    operation_name VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    tags JSONB NOT NULL,
    logs JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Guild Customization Tables (from 019_guild_customization_tables.sql)
-- ============================================

-- Guild Customization table
CREATE TABLE IF NOT EXISTS guild_customization (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    
    -- Page Settings
    page_title VARCHAR(255) DEFAULT NULL,
    page_description TEXT DEFAULT NULL,
    welcome_message TEXT DEFAULT NULL,
    
    -- Colors & Branding
    primary_color VARCHAR(7) DEFAULT '#667eea',
    secondary_color VARCHAR(7) DEFAULT '#764ba2',
    accent_color VARCHAR(7) DEFAULT '#5865F2',
    
    -- Images
    hero_image VARCHAR(255) DEFAULT NULL,
    logo_image VARCHAR(255) DEFAULT NULL,
    background_image VARCHAR(255) DEFAULT NULL,
    
    -- Content Sections
    about_section TEXT DEFAULT NULL,
    features_section TEXT DEFAULT NULL,
    rules_section TEXT DEFAULT NULL,
    
    -- Social Links
    discord_invite VARCHAR(255) DEFAULT NULL,
    website_url VARCHAR(255) DEFAULT NULL,
    twitter_url VARCHAR(255) DEFAULT NULL,
    
    -- Display Options
    show_leaderboard BOOLEAN DEFAULT TRUE,
    show_recent_bets BOOLEAN DEFAULT TRUE,
    show_stats BOOLEAN DEFAULT TRUE,
    public_access BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (guild_id),
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- Guild Images table
CREATE TABLE IF NOT EXISTS guild_images (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    image_type VARCHAR(50) NOT NULL CHECK (image_type IN ('hero', 'logo', 'background', 'gallery')),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    alt_text VARCHAR(255) DEFAULT NULL,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    uploaded_by BIGINT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- Guild Page Templates table
CREATE TABLE IF NOT EXISTS guild_page_templates (
    id BIGSERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL UNIQUE,
    template_description TEXT,
    template_config JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Core table indexes
CREATE INDEX IF NOT EXISTS idx_guilds_subscription_status ON guilds(subscription_status);
CREATE INDEX IF NOT EXISTS idx_guild_users_guild_id ON guild_users(guild_id);
CREATE INDEX IF NOT EXISTS idx_guild_users_user_id ON guild_users(user_id);
CREATE INDEX IF NOT EXISTS idx_bets_guild_user ON bets(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(status);
CREATE INDEX IF NOT EXISTS idx_bets_created_at ON bets(created_at);
CREATE INDEX IF NOT EXISTS idx_unit_records_guild_user ON unit_records(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_unit_records_year_month ON unit_records(year, month);
CREATE INDEX IF NOT EXISTS idx_api_games_sport_league ON api_games(sport, league_name);
CREATE INDEX IF NOT EXISTS idx_api_games_season ON api_games(season);
CREATE INDEX IF NOT EXISTS idx_api_games_start_time ON api_games(start_time);
CREATE INDEX IF NOT EXISTS idx_api_games_status ON api_games(status);

-- Platinum tier indexes
CREATE INDEX IF NOT EXISTS idx_platinum_features_guild_id ON platinum_features(guild_id);
CREATE INDEX IF NOT EXISTS idx_platinum_analytics_guild_id ON platinum_analytics(guild_id);
CREATE INDEX IF NOT EXISTS idx_webhook_integrations_guild_id ON webhook_integrations(guild_id);
CREATE INDEX IF NOT EXISTS idx_real_time_alerts_guild_id ON real_time_alerts(guild_id);
CREATE INDEX IF NOT EXISTS idx_data_exports_guild_id ON data_exports(guild_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_tracking_guild_id ON api_usage_tracking(guild_id);

-- ML/AI indexes
CREATE INDEX IF NOT EXISTS idx_ml_models_model_type ON ml_models(model_type);
CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_advanced_ai_models_model_id ON advanced_ai_models(model_id);
CREATE INDEX IF NOT EXISTS idx_advanced_ai_models_model_type ON advanced_ai_models(model_type);
CREATE INDEX IF NOT EXISTS idx_advanced_ai_models_status ON advanced_ai_models(status);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_model_id ON ai_predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_prediction_time ON ai_predictions(prediction_time);
CREATE INDEX IF NOT EXISTS idx_nlp_results_sentiment ON nlp_results(sentiment);
CREATE INDEX IF NOT EXISTS idx_cv_results_quality ON computer_vision_results(image_quality);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_analytics_dashboards_dashboard_id ON analytics_dashboards(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_analytics_dashboards_dashboard_type ON analytics_dashboards(dashboard_type);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_name ON analytics_metrics(name);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_timestamp ON analytics_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_reports_report_type ON analytics_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_analytics_alerts_status_severity ON analytics_alerts(status, severity);

-- System integration indexes
CREATE INDEX IF NOT EXISTS idx_service_instances_service_id ON service_instances(service_id);
CREATE INDEX IF NOT EXISTS idx_service_instances_status ON service_instances(status);
CREATE INDEX IF NOT EXISTS idx_circuit_breakers_service_id ON circuit_breakers(service_id);
CREATE INDEX IF NOT EXISTS idx_circuit_breakers_state ON circuit_breakers(state);
CREATE INDEX IF NOT EXISTS idx_service_metrics_service_id ON service_metrics(service_id);
CREATE INDEX IF NOT EXISTS idx_service_metrics_timestamp ON service_metrics(timestamp);

-- Guild customization indexes
CREATE INDEX IF NOT EXISTS idx_guild_customization_guild_id ON guild_customization(guild_id);
CREATE INDEX IF NOT EXISTS idx_guild_customization_public_access ON guild_customization(public_access);
CREATE INDEX IF NOT EXISTS idx_guild_images_guild_id ON guild_images(guild_id);
CREATE INDEX IF NOT EXISTS idx_guild_images_image_type ON guild_images(image_type);

-- ============================================
-- Insert Default Data
-- ============================================

-- Insert default guild page templates
INSERT INTO guild_page_templates (template_name, template_description, template_config, is_default) VALUES 
('modern', 'Modern design with gradients and animations', '{"layout": "hero-stats-leaderboard", "style": "modern", "animations": true}', TRUE),
('classic', 'Clean classic design', '{"layout": "header-content-sidebar", "style": "classic", "animations": false}', FALSE),
('gaming', 'Gaming-focused design with dark theme', '{"layout": "full-width", "style": "gaming", "animations": true}', FALSE)
ON CONFLICT (template_name) DO NOTHING;

-- ============================================
-- Create Update Triggers for Updated At Timestamps
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for tables with updated_at columns
CREATE TRIGGER update_guilds_updated_at BEFORE UPDATE ON guilds FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_guild_users_updated_at BEFORE UPDATE ON guild_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bets_updated_at BEFORE UPDATE ON bets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_team_logos_updated_at BEFORE UPDATE ON team_logos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_games_updated_at BEFORE UPDATE ON api_games FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_platinum_features_updated_at BEFORE UPDATE ON platinum_features FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_webhook_integrations_updated_at BEFORE UPDATE ON webhook_integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ml_models_updated_at BEFORE UPDATE ON ml_models FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_advanced_ai_models_updated_at BEFORE UPDATE ON advanced_ai_models FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analytics_dashboards_updated_at BEFORE UPDATE ON analytics_dashboards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_service_instances_updated_at BEFORE UPDATE ON service_instances FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_service_registry_updated_at BEFORE UPDATE ON service_registry FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_gateways_updated_at BEFORE UPDATE ON api_gateways FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_load_balancers_updated_at BEFORE UPDATE ON load_balancers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_circuit_breakers_updated_at BEFORE UPDATE ON circuit_breakers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deployment_configs_updated_at BEFORE UPDATE ON deployment_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_guild_customization_updated_at BEFORE UPDATE ON guild_customization FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analytics_visualizations_updated_at BEFORE UPDATE ON analytics_visualizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Migration Complete
-- ============================================

COMMENT ON DATABASE current_database() IS 'DBSBM - Discord Betting Sports Bot Manager Database'; 