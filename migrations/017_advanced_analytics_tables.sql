-- Migration 017: Advanced Analytics Tables
-- Adds comprehensive advanced analytics and business intelligence infrastructure

-- Analytics Dashboards table
CREATE TABLE IF NOT EXISTS analytics_dashboards (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    dashboard_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    dashboard_type ENUM('real_time', 'historical', 'predictive', 'operational', 'executive', 'technical') NOT NULL,
    description TEXT NOT NULL,
    widgets JSON NOT NULL,
    layout JSON NOT NULL,
    refresh_interval INT DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON NOT NULL,
    INDEX idx_dashboard_id (dashboard_id),
    INDEX idx_dashboard_type (dashboard_type),
    INDEX idx_is_active (is_active),
    INDEX idx_created_at (created_at)
);

-- Analytics Widgets table
CREATE TABLE IF NOT EXISTS analytics_widgets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    widget_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    chart_type ENUM('line', 'bar', 'pie', 'scatter', 'area', 'heatmap', 'gauge', 'table', 'kpi', 'funnel') NOT NULL,
    data_source VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    config JSON NOT NULL,
    position JSON NOT NULL,
    size JSON NOT NULL,
    refresh_interval INT DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON NOT NULL,
    INDEX idx_widget_id (widget_id),
    INDEX idx_chart_type (chart_type),
    INDEX idx_is_active (is_active),
    INDEX idx_created_at (created_at)
);

-- Analytics Metrics table
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    metric_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    metric_type ENUM('counter', 'gauge', 'histogram', 'summary', 'percentile', 'rate', 'delta') NOT NULL,
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    tags JSON NOT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metric_id (metric_id),
    INDEX idx_name (name),
    INDEX idx_metric_type (metric_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_tags (tags(100))
);

-- Analytics Reports table
CREATE TABLE IF NOT EXISTS analytics_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    report_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    data JSON NOT NULL,
    charts JSON NOT NULL,
    insights JSON NOT NULL,
    recommendations JSON NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    scheduled BOOLEAN DEFAULT FALSE,
    schedule_config JSON NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_report_id (report_id),
    INDEX idx_report_type (report_type),
    INDEX idx_generated_at (generated_at),
    INDEX idx_scheduled (scheduled)
);

-- Analytics Forecasts table
CREATE TABLE IF NOT EXISTS analytics_forecasts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    forecast_id VARCHAR(255) NOT NULL UNIQUE,
    metric_name VARCHAR(255) NOT NULL,
    forecast_type VARCHAR(100) NOT NULL,
    predictions JSON NOT NULL,
    confidence_intervals JSON NOT NULL,
    timestamps JSON NOT NULL,
    accuracy DECIMAL(5,4) NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON NOT NULL,
    INDEX idx_forecast_id (forecast_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_forecast_type (forecast_type),
    INDEX idx_created_at (created_at)
);

-- Analytics Insights table
CREATE TABLE IF NOT EXISTS analytics_insights (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    insight_id VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    insight_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    data_points JSON NOT NULL,
    recommendations JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON NOT NULL,
    INDEX idx_insight_id (insight_id),
    INDEX idx_insight_type (insight_type),
    INDEX idx_severity (severity),
    INDEX idx_confidence (confidence),
    INDEX idx_created_at (created_at)
);

-- Analytics Alerts table
CREATE TABLE IF NOT EXISTS analytics_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    alert_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    alert_condition VARCHAR(255) NOT NULL,
    threshold DECIMAL(15,6) NOT NULL,
    current_value DECIMAL(15,6) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    triggered_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_alert_id (alert_id),
    INDEX idx_status (status),
    INDEX idx_severity (severity),
    INDEX idx_triggered_at (triggered_at)
);

-- Analytics Data Aggregations table
CREATE TABLE IF NOT EXISTS analytics_data_aggregations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    aggregation_id VARCHAR(255) NOT NULL UNIQUE,
    metric_name VARCHAR(255) NOT NULL,
    aggregation_type VARCHAR(100) NOT NULL,
    time_period VARCHAR(50) NOT NULL,
    aggregated_value DECIMAL(15,6) NOT NULL,
    data_points JSON NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON NOT NULL,
    INDEX idx_aggregation_id (aggregation_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_aggregation_type (aggregation_type),
    INDEX idx_time_period (time_period),
    INDEX idx_start_time (start_time)
);

-- Analytics Visualizations table
CREATE TABLE IF NOT EXISTS analytics_visualizations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    visualization_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    chart_type ENUM('line', 'bar', 'pie', 'scatter', 'area', 'heatmap', 'gauge', 'table', 'kpi', 'funnel') NOT NULL,
    data JSON NOT NULL,
    config JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON NOT NULL,
    INDEX idx_visualization_id (visualization_id),
    INDEX idx_chart_type (chart_type),
    INDEX idx_created_at (created_at)
);

-- Insert default analytics dashboards
INSERT INTO analytics_dashboards (
    dashboard_id, name, dashboard_type, description, widgets, layout, refresh_interval, is_active, metadata
) VALUES
(
    'default-real-time-dashboard',
    'Real-Time Analytics',
    'real_time',
    'Real-time system performance and user activity monitoring',
    '[]',
    '{"type": "grid", "columns": 12, "rows": 8}',
    30,
    TRUE,
    '{"created_by": "system", "category": "monitoring"}'
),
(
    'default-executive-dashboard',
    'Executive Overview',
    'executive',
    'High-level business metrics and KPIs for executive decision making',
    '[]',
    '{"type": "grid", "columns": 12, "rows": 6}',
    60,
    TRUE,
    '{"created_by": "system", "category": "business"}'
),
(
    'default-operational-dashboard',
    'Operational Metrics',
    'operational',
    'Operational metrics and system health monitoring',
    '[]',
    '{"type": "grid", "columns": 12, "rows": 10}',
    15,
    TRUE,
    '{"created_by": "system", "category": "operations"}'
);

-- Insert sample analytics widgets
INSERT INTO analytics_widgets (
    widget_id, name, chart_type, data_source, query, config, position, size, refresh_interval, is_active, metadata
) VALUES
(
    'widget-system-performance',
    'System Performance',
    'gauge',
    'system_metrics',
    'SELECT AVG(performance) FROM system_metrics WHERE timestamp >= NOW() - INTERVAL 1 HOUR',
    '{"min": 0, "max": 100, "thresholds": {"warning": 70, "critical": 50}}',
    '{"x": 0, "y": 0}',
    '{"width": 4, "height": 3}',
    30,
    TRUE,
    '{"category": "performance", "priority": "high"}'
),
(
    'widget-user-activity',
    'User Activity',
    'line',
    'user_metrics',
    'SELECT timestamp, COUNT(*) as users FROM user_activity GROUP BY HOUR(timestamp)',
    '{"yAxis": {"title": "Active Users"}, "xAxis": {"title": "Time"}}',
    '{"x": 4, "y": 0}',
    '{"width": 8, "height": 3}',
    30,
    TRUE,
    '{"category": "users", "priority": "medium"}'
),
(
    'widget-revenue-metrics',
    'Revenue Metrics',
    'bar',
    'financial_metrics',
    'SELECT category, SUM(amount) as revenue FROM transactions GROUP BY category',
    '{"yAxis": {"title": "Revenue"}, "xAxis": {"title": "Category"}}',
    '{"x": 0, "y": 3}',
    '{"width": 6, "height": 4}',
    60,
    TRUE,
    '{"category": "finance", "priority": "high"}'
);

-- Insert sample analytics metrics
INSERT INTO analytics_metrics (
    metric_id, name, metric_type, value, unit, timestamp, tags, metadata
) VALUES
(
    'metric-system-performance-001',
    'system_performance',
    'gauge',
    85.500000,
    '%',
    NOW(),
    '{"component": "system", "type": "performance"}',
    '{"source": "system_monitor", "collection_method": "real_time"}'
),
(
    'metric-user-activity-001',
    'user_activity',
    'counter',
    150.000000,
    'users',
    NOW(),
    '{"component": "users", "type": "activity"}',
    '{"source": "user_tracker", "collection_method": "real_time"}'
),
(
    'metric-response-time-001',
    'response_time',
    'histogram',
    250.000000,
    'ms',
    NOW(),
    '{"component": "api", "type": "performance"}',
    '{"source": "api_monitor", "collection_method": "real_time"}'
),
(
    'metric-error-rate-001',
    'error_rate',
    'rate',
    0.025000,
    'errors/sec',
    NOW(),
    '{"component": "system", "type": "errors"}',
    '{"source": "error_tracker", "collection_method": "real_time"}'
);

-- Insert sample analytics reports
INSERT INTO analytics_reports (
    report_id, name, report_type, description, data, charts, insights, recommendations, generated_at, scheduled, metadata
) VALUES
(
    'report-daily-performance-001',
    'Daily Performance Report',
    'daily',
    'Daily system performance and user activity summary',
    '{"performance": 85.5, "user_activity": 150, "response_time": 250, "error_rate": 0.025}',
    '[{"type": "line", "title": "Performance Trend", "data": {"labels": ["00:00", "06:00", "12:00", "18:00"], "datasets": [{"label": "Performance", "data": [80, 82, 85, 87]}]}}]',
    '["System performance is excellent", "High user activity detected", "Response time is within acceptable limits"]',
    '["Continue monitoring system performance", "Consider scaling for increased user activity", "Optimize API response times"]',
    NOW(),
    FALSE,
    '{"generated_by": "system", "report_frequency": "daily"}'
),
(
    'report-weekly-summary-001',
    'Weekly Business Summary',
    'weekly',
    'Weekly business metrics and KPIs summary',
    '{"revenue": 15000, "users": 1200, "transactions": 450, "growth_rate": 0.15}',
    '[{"type": "bar", "title": "Revenue by Category", "data": {"labels": ["Sports", "Casino", "Live"], "datasets": [{"label": "Revenue", "data": [8000, 5000, 2000]}]}}]',
    '["Revenue growth is strong", "User engagement is high", "Transaction volume is increasing"]',
    '["Focus on sports betting category", "Expand live betting features", "Implement user retention strategies"]',
    NOW(),
    TRUE,
    '{"generated_by": "system", "report_frequency": "weekly"}'
);

-- Insert sample analytics forecasts
INSERT INTO analytics_forecasts (
    forecast_id, metric_name, forecast_type, predictions, confidence_intervals, timestamps, accuracy, model_used, metadata
) VALUES
(
    'forecast-user-growth-001',
    'user_activity',
    'linear_regression',
    '[155, 160, 165, 170, 175, 180, 185, 190, 195, 200]',
    '[[150, 160], [155, 165], [160, 170], [165, 175], [170, 180], [175, 185], [180, 190], [185, 195], [190, 200], [195, 205]]',
    '["2024-01-01T00:00:00", "2024-01-02T00:00:00", "2024-01-03T00:00:00", "2024-01-04T00:00:00", "2024-01-05T00:00:00", "2024-01-06T00:00:00", "2024-01-07T00:00:00", "2024-01-08T00:00:00", "2024-01-09T00:00:00", "2024-01-10T00:00:00"]',
    0.8500,
    'linear_regression',
    '{"forecast_horizon": 10, "confidence_level": 0.95}'
),
(
    'forecast-revenue-001',
    'revenue',
    'time_series',
    '[16000, 16500, 17000, 17500, 18000, 18500, 19000, 19500, 20000, 20500]',
    '[[15500, 16500], [16000, 17000], [16500, 17500], [17000, 18000], [17500, 18500], [18000, 19000], [18500, 19500], [19000, 20000], [19500, 20500], [20000, 21000]]',
    '["2024-01-01T00:00:00", "2024-01-02T00:00:00", "2024-01-03T00:00:00", "2024-01-04T00:00:00", "2024-01-05T00:00:00", "2024-01-06T00:00:00", "2024-01-07T00:00:00", "2024-01-08T00:00:00", "2024-01-09T00:00:00", "2024-01-10T00:00:00"]',
    0.9000,
    'arima',
    '{"forecast_horizon": 10, "confidence_level": 0.95}'
);

-- Insert sample analytics insights
INSERT INTO analytics_insights (
    insight_id, title, description, insight_type, severity, confidence, data_points, recommendations, metadata
) VALUES
(
    'insight-performance-trend-001',
    'System Performance Trending Upward',
    'System performance has shown a consistent upward trend over the past 24 hours',
    'trend',
    'positive',
    0.8500,
    '[{"timestamp": "2024-01-01T00:00:00", "value": 80}, {"timestamp": "2024-01-01T06:00:00", "value": 82}, {"timestamp": "2024-01-01T12:00:00", "value": 85}, {"timestamp": "2024-01-01T18:00:00", "value": 87}]',
    '["Continue monitoring system performance", "Consider optimizing for even better performance", "Document successful configuration changes"]',
    '{"trend_direction": "upward", "trend_strength": "strong", "data_points_count": 4}'
),
(
    'insight-user-engagement-001',
    'High User Engagement Detected',
    'User activity has increased significantly compared to previous periods',
    'anomaly',
    'medium',
    0.7500,
    '[{"timestamp": "2024-01-01T00:00:00", "value": 120}, {"timestamp": "2024-01-01T06:00:00", "value": 135}, {"timestamp": "2024-01-01T12:00:00", "value": 150}, {"timestamp": "2024-01-01T18:00:00", "value": 165}]',
    '["Investigate cause of increased engagement", "Prepare for potential scaling needs", "Monitor system resources"]',
    '{"anomaly_type": "positive", "baseline_value": 100, "current_value": 165}'
);

-- Insert sample analytics alerts
INSERT INTO analytics_alerts (
    alert_id, name, alert_condition, threshold, current_value, severity, status, triggered_at, metadata
) VALUES
(
    'alert-high-error-rate-001',
    'High Error Rate Alert',
    'error_rate > 0.05',
    0.050000,
    0.025000,
    'medium',
    'normal',
    NOW(),
    '{"alert_type": "threshold", "component": "system", "notification_channels": ["email", "slack"]}'
),
(
    'alert-low-performance-001',
    'Low Performance Alert',
    'system_performance < 70',
    70.000000,
    85.500000,
    'high',
    'normal',
    NOW(),
    '{"alert_type": "threshold", "component": "system", "notification_channels": ["email", "slack", "sms"]}'
);

-- Insert sample analytics data aggregations
INSERT INTO analytics_data_aggregations (
    aggregation_id, metric_name, aggregation_type, time_period, aggregated_value, data_points, start_time, end_time, metadata
) VALUES
(
    'agg-hourly-performance-001',
    'system_performance',
    'average',
    'hourly',
    85.500000,
    '[{"timestamp": "2024-01-01T00:00:00", "value": 85.5}, {"timestamp": "2024-01-01T01:00:00", "value": 86.2}, {"timestamp": "2024-01-01T02:00:00", "value": 84.8}]',
    '2024-01-01 00:00:00',
    '2024-01-01 03:00:00',
    '{"aggregation_method": "average", "data_points_count": 3}'
),
(
    'agg-daily-user-activity-001',
    'user_activity',
    'sum',
    'daily',
    3600.000000,
    '[{"timestamp": "2024-01-01T00:00:00", "value": 150}, {"timestamp": "2024-01-01T06:00:00", "value": 165}, {"timestamp": "2024-01-01T12:00:00", "value": 180}]',
    '2024-01-01 00:00:00',
    '2024-01-01 23:59:59',
    '{"aggregation_method": "sum", "data_points_count": 24}'
);

-- Insert sample analytics visualizations
INSERT INTO analytics_visualizations (
    visualization_id, name, chart_type, data, config, metadata
) VALUES
(
    'viz-performance-trend-001',
    'Performance Trend',
    'line',
    '{"labels": ["00:00", "06:00", "12:00", "18:00"], "datasets": [{"label": "Performance", "data": [80, 82, 85, 87], "borderColor": "rgb(75, 192, 192)", "backgroundColor": "rgba(75, 192, 192, 0.2)"}]}',
    '{"responsive": true, "scales": {"y": {"beginAtZero": true, "max": 100}}}',
    '{"created_by": "system", "category": "performance"}'
),
(
    'viz-user-activity-001',
    'User Activity',
    'bar',
    '{"labels": ["Sports", "Casino", "Live"], "datasets": [{"label": "Users", "data": [800, 500, 200], "backgroundColor": ["rgba(255, 99, 132, 0.8)", "rgba(54, 162, 235, 0.8)", "rgba(255, 205, 86, 0.8)"]}]}',
    '{"responsive": true, "scales": {"y": {"beginAtZero": true}}}',
    '{"created_by": "system", "category": "users"}'
);

-- Create indexes for better performance
CREATE INDEX idx_analytics_metrics_name_time ON analytics_metrics(name, timestamp);
CREATE INDEX idx_analytics_metrics_type_time ON analytics_metrics(metric_type, timestamp);
CREATE INDEX idx_analytics_reports_type_generated ON analytics_reports(report_type, generated_at);
CREATE INDEX idx_analytics_insights_type_created ON analytics_insights(insight_type, created_at);
CREATE INDEX idx_analytics_alerts_status_severity ON analytics_alerts(status, severity);
CREATE INDEX idx_analytics_forecasts_metric_created ON analytics_forecasts(metric_name, created_at);
CREATE INDEX idx_analytics_aggregations_metric_period ON analytics_data_aggregations(metric_name, time_period);

-- Add comments for documentation
ALTER TABLE analytics_dashboards COMMENT = 'Analytics dashboards for data visualization and monitoring';
ALTER TABLE analytics_widgets COMMENT = 'Analytics widgets for dashboard components';
ALTER TABLE analytics_metrics COMMENT = 'Analytics metrics for performance and business data';
ALTER TABLE analytics_reports COMMENT = 'Analytics reports with insights and recommendations';
ALTER TABLE analytics_forecasts COMMENT = 'Analytics forecasts for predictive modeling';
ALTER TABLE analytics_insights COMMENT = 'Analytics insights for data-driven decisions';
ALTER TABLE analytics_alerts COMMENT = 'Analytics alerts for monitoring and notifications';
ALTER TABLE analytics_data_aggregations COMMENT = 'Analytics data aggregations for time-series analysis';
ALTER TABLE analytics_visualizations COMMENT = 'Analytics visualizations for chart and graph data';
