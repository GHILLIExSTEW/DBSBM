-- Migration 018: System Integration Tables
-- This migration creates tables for comprehensive system integration including
-- microservices architecture, API gateways, load balancers, circuit breakers,
-- and deployment automation.

-- Service Instances Table
CREATE TABLE IF NOT EXISTS service_instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_id VARCHAR(255) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    instance_id VARCHAR(255) NOT NULL UNIQUE,
    host VARCHAR(255) NOT NULL,
    port INT NOT NULL,
    health_endpoint VARCHAR(255) DEFAULT '/health',
    status VARCHAR(50) NOT NULL DEFAULT 'starting',
    load_balancer_weight INT DEFAULT 1,
    max_connections INT DEFAULT 100,
    current_connections INT DEFAULT 0,
    response_time FLOAT DEFAULT 0.0,
    last_health_check DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_service_id (service_id),
    INDEX idx_service_type (service_type),
    INDEX idx_status (status),
    INDEX idx_host_port (host, port)
);

-- Service Registry Table
CREATE TABLE IF NOT EXISTS service_registry (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_id VARCHAR(255) NOT NULL UNIQUE,
    service_type VARCHAR(100) NOT NULL,
    health_check_interval INT DEFAULT 30,
    circuit_breaker_threshold INT DEFAULT 5,
    circuit_breaker_timeout INT DEFAULT 60,
    load_balancer_type VARCHAR(50) DEFAULT 'round_robin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_service_type (service_type),
    INDEX idx_load_balancer_type (load_balancer_type)
);

-- API Gateways Table
CREATE TABLE IF NOT EXISTS api_gateways (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gateway_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    routes JSON,
    rate_limits JSON,
    authentication_required BOOLEAN DEFAULT TRUE,
    cors_enabled BOOLEAN DEFAULT TRUE,
    logging_enabled BOOLEAN DEFAULT TRUE,
    monitoring_enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_gateway_id (gateway_id),
    INDEX idx_name (name)
);

-- Load Balancers Table
CREATE TABLE IF NOT EXISTS load_balancers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    balancer_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    balancer_type VARCHAR(50) NOT NULL,
    instances JSON,
    health_check_path VARCHAR(255) DEFAULT '/health',
    health_check_interval INT DEFAULT 30,
    session_sticky BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_balancer_id (balancer_id),
    INDEX idx_service_type (service_type),
    INDEX idx_balancer_type (balancer_type)
);

-- Circuit Breakers Table
CREATE TABLE IF NOT EXISTS circuit_breakers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    breaker_id VARCHAR(255) NOT NULL UNIQUE,
    service_id VARCHAR(255) NOT NULL,
    failure_threshold INT DEFAULT 5,
    timeout_seconds INT DEFAULT 60,
    state VARCHAR(50) DEFAULT 'closed',
    failure_count INT DEFAULT 0,
    last_failure_time DATETIME,
    last_success_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_breaker_id (breaker_id),
    INDEX idx_service_id (service_id),
    INDEX idx_state (state)
);

-- Deployment Configurations Table
CREATE TABLE IF NOT EXISTS deployment_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    deployment_id VARCHAR(255) NOT NULL UNIQUE,
    service_type VARCHAR(100) NOT NULL,
    container_image VARCHAR(500) NOT NULL,
    replicas INT DEFAULT 1,
    cpu_limit VARCHAR(50) DEFAULT '500m',
    memory_limit VARCHAR(50) DEFAULT '512Mi',
    environment_vars JSON,
    ports JSON,
    volumes JSON,
    health_check JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_deployment_id (deployment_id),
    INDEX idx_service_type (service_type)
);

-- Service Metrics Table
CREATE TABLE IF NOT EXISTS service_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_id VARCHAR(255) NOT NULL,
    instance_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_service_id (service_id),
    INDEX idx_instance_id (instance_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp)
);

-- Deployment History Table
CREATE TABLE IF NOT EXISTS deployment_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    deployment_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    manifest JSON,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    error_message TEXT,
    INDEX idx_deployment_id (deployment_id),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
);

-- Service Mesh Configuration Table
CREATE TABLE IF NOT EXISTS service_mesh_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mesh_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    routing_rules JSON,
    traffic_shifting JSON,
    fault_injection JSON,
    retry_policies JSON,
    timeout_policies JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_mesh_id (mesh_id),
    INDEX idx_service_type (service_type)
);

-- Distributed Tracing Table
CREATE TABLE IF NOT EXISTS distributed_tracing (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trace_id VARCHAR(255) NOT NULL,
    span_id VARCHAR(255) NOT NULL,
    parent_span_id VARCHAR(255),
    service_name VARCHAR(100) NOT NULL,
    operation_name VARCHAR(255) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_ms INT,
    tags JSON,
    logs JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_trace_id (trace_id),
    INDEX idx_span_id (span_id),
    INDEX idx_service_name (service_name),
    INDEX idx_start_time (start_time)
);

-- Insert default configurations
INSERT INTO service_registry (service_id, service_type, health_check_interval, circuit_breaker_threshold, circuit_breaker_timeout, load_balancer_type) VALUES
('api_gateway_default', 'api_gateway', 30, 5, 60, 'round_robin'),
('user_service_default', 'user_service', 30, 5, 60, 'round_robin'),
('betting_service_default', 'betting_service', 30, 5, 60, 'round_robin'),
('analytics_service_default', 'analytics_service', 30, 5, 60, 'round_robin'),
('ai_service_default', 'ai_service', 30, 5, 60, 'round_robin'),
('integration_service_default', 'integration_service', 30, 5, 60, 'round_robin'),
('enterprise_service_default', 'enterprise_service', 30, 5, 60, 'round_robin'),
('security_service_default', 'security_service', 30, 5, 60, 'round_robin'),
('compliance_service_default', 'compliance_service', 30, 5, 60, 'round_robin'),
('cache_service_default', 'cache_service', 30, 5, 60, 'round_robin'),
('database_service_default', 'database_service', 30, 5, 60, 'round_robin'),
('monitoring_service_default', 'monitoring_service', 30, 5, 60, 'round_robin');

-- Insert default API gateway
INSERT INTO api_gateways (gateway_id, name, base_url, routes, rate_limits, authentication_required, cors_enabled, logging_enabled, monitoring_enabled) VALUES
('gateway_main', 'Main API Gateway', 'https://api.dbsbm.com',
 '[{"path": "/api/v1/users", "service": "user_service", "methods": ["GET", "POST", "PUT", "DELETE"]}, {"path": "/api/v1/betting", "service": "betting_service", "methods": ["GET", "POST"]}, {"path": "/api/v1/analytics", "service": "analytics_service", "methods": ["GET"]}, {"path": "/api/v1/ai", "service": "ai_service", "methods": ["GET", "POST"]}]',
 '{"default": 1000, "authenticated": 5000, "admin": 10000}',
 TRUE, TRUE, TRUE, TRUE);

-- Insert default load balancers
INSERT INTO load_balancers (balancer_id, name, service_type, balancer_type, instances, health_check_path, health_check_interval, session_sticky) VALUES
('lb_user_service', 'User Service Load Balancer', 'user_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_betting_service', 'Betting Service Load Balancer', 'betting_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_analytics_service', 'Analytics Service Load Balancer', 'analytics_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_ai_service', 'AI Service Load Balancer', 'ai_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_integration_service', 'Integration Service Load Balancer', 'integration_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_enterprise_service', 'Enterprise Service Load Balancer', 'enterprise_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_security_service', 'Security Service Load Balancer', 'security_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_compliance_service', 'Compliance Service Load Balancer', 'compliance_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_cache_service', 'Cache Service Load Balancer', 'cache_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_database_service', 'Database Service Load Balancer', 'database_service', 'round_robin', '[]', '/health', 30, FALSE),
('lb_monitoring_service', 'Monitoring Service Load Balancer', 'monitoring_service', 'round_robin', '[]', '/health', 30, FALSE);

-- Insert default circuit breakers
INSERT INTO circuit_breakers (breaker_id, service_id, failure_threshold, timeout_seconds, state, failure_count) VALUES
('cb_user_service', 'user_service_default', 5, 60, 'closed', 0),
('cb_betting_service', 'betting_service_default', 5, 60, 'closed', 0),
('cb_analytics_service', 'analytics_service_default', 5, 60, 'closed', 0),
('cb_ai_service', 'ai_service_default', 5, 60, 'closed', 0),
('cb_integration_service', 'integration_service_default', 5, 60, 'closed', 0),
('cb_enterprise_service', 'enterprise_service_default', 5, 60, 'closed', 0),
('cb_security_service', 'security_service_default', 5, 60, 'closed', 0),
('cb_compliance_service', 'compliance_service_default', 5, 60, 'closed', 0),
('cb_cache_service', 'cache_service_default', 5, 60, 'closed', 0),
('cb_database_service', 'database_service_default', 5, 60, 'closed', 0),
('cb_monitoring_service', 'monitoring_service_default', 5, 60, 'closed', 0);

-- Insert default deployment configurations
INSERT INTO deployment_configs (deployment_id, service_type, container_image, replicas, cpu_limit, memory_limit, environment_vars, ports, volumes, health_check) VALUES
('deploy_user_service', 'user_service', 'dbsbm/user-service:latest', 2, '500m', '512Mi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8080]', '[]', '{"path": "/health", "port": 8080, "initial_delay": 30, "period": 10}'),
('deploy_betting_service', 'betting_service', 'dbsbm/betting-service:latest', 3, '1000m', '1Gi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8081]', '[]', '{"path": "/health", "port": 8081, "initial_delay": 30, "period": 10}'),
('deploy_analytics_service', 'analytics_service', 'dbsbm/analytics-service:latest', 2, '1000m', '1Gi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8082]', '[]', '{"path": "/health", "port": 8082, "initial_delay": 30, "period": 10}'),
('deploy_ai_service', 'ai_service', 'dbsbm/ai-service:latest', 2, '2000m', '2Gi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8083]', '[]', '{"path": "/health", "port": 8083, "initial_delay": 30, "period": 10}'),
('deploy_integration_service', 'integration_service', 'dbsbm/integration-service:latest', 2, '500m', '512Mi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8084]', '[]', '{"path": "/health", "port": 8084, "initial_delay": 30, "period": 10}'),
('deploy_enterprise_service', 'enterprise_service', 'dbsbm/enterprise-service:latest', 2, '500m', '512Mi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8085]', '[]', '{"path": "/health", "port": 8085, "initial_delay": 30, "period": 10}'),
('deploy_security_service', 'security_service', 'dbsbm/security-service:latest', 2, '500m', '512Mi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8086]', '[]', '{"path": "/health", "port": 8086, "initial_delay": 30, "period": 10}'),
('deploy_compliance_service', 'compliance_service', 'dbsbm/compliance-service:latest', 2, '500m', '512Mi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8087]', '[]', '{"path": "/health", "port": 8087, "initial_delay": 30, "period": 10}'),
('deploy_cache_service', 'cache_service', 'dbsbm/cache-service:latest', 2, '500m', '512Mi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8088]', '[]', '{"path": "/health", "port": 8088, "initial_delay": 30, "period": 10}'),
('deploy_database_service', 'database_service', 'dbsbm/database-service:latest', 2, '500m', '512Mi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8089]', '[]', '{"path": "/health", "port": 8089, "initial_delay": 30, "period": 10}'),
('deploy_monitoring_service', 'monitoring_service', 'dbsbm/monitoring-service:latest', 2, '500m', '512Mi', '{"ENV": "production", "LOG_LEVEL": "info"}', '[8090]', '[]', '{"path": "/health", "port": 8090, "initial_delay": 30, "period": 10}');

-- Insert default service mesh configurations
INSERT INTO service_mesh_config (mesh_id, name, service_type, routing_rules, traffic_shifting, fault_injection, retry_policies, timeout_policies) VALUES
('mesh_user_service', 'User Service Mesh', 'user_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "user-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "user-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_betting_service', 'Betting Service Mesh', 'betting_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "betting-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "betting-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_analytics_service', 'Analytics Service Mesh', 'analytics_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "analytics-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "analytics-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_ai_service', 'AI Service Mesh', 'ai_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "ai-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "ai-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_integration_service', 'Integration Service Mesh', 'integration_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "integration-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "integration-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_enterprise_service', 'Enterprise Service Mesh', 'enterprise_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "enterprise-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "enterprise-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_security_service', 'Security Service Mesh', 'security_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "security-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "security-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_compliance_service', 'Compliance Service Mesh', 'compliance_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "compliance-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "compliance-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_cache_service', 'Cache Service Mesh', 'cache_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "cache-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "cache-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_database_service', 'Database Service Mesh', 'database_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "database-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "database-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}'),
('mesh_monitoring_service', 'Monitoring Service Mesh', 'monitoring_service', '{"rules": [{"match": {"headers": {"user-agent": "mobile"}}, "route": [{"destination": {"host": "monitoring-service-mobile"}}]}]}', '{"shifts": [{"destination": {"host": "monitoring-service-v2"}, "weight": 10}]}', '{"faults": [{"abort": {"httpStatus": 500, "percentage": 5}}]}', '{"retries": [{"attempts": 3, "perTryTimeout": "2s"}]}', '{"timeouts": [{"timeout": "5s"}]}');

-- Create indexes for better performance
CREATE INDEX idx_service_instances_service_type_status ON service_instances(service_type, status);
CREATE INDEX idx_service_instances_host_port ON service_instances(host, port);
CREATE INDEX idx_service_instances_last_health_check ON service_instances(last_health_check);
CREATE INDEX idx_service_registry_service_type ON service_registry(service_type);
CREATE INDEX idx_api_gateways_name ON api_gateways(name);
CREATE INDEX idx_load_balancers_service_type ON load_balancers(service_type);
CREATE INDEX idx_circuit_breakers_service_id_state ON circuit_breakers(service_id, state);
CREATE INDEX idx_deployment_configs_service_type ON deployment_configs(service_type);
CREATE INDEX idx_service_metrics_service_id_timestamp ON service_metrics(service_id, timestamp);
CREATE INDEX idx_deployment_history_deployment_id_status ON deployment_history(deployment_id, status);
CREATE INDEX idx_service_mesh_config_service_type ON service_mesh_config(service_type);
CREATE INDEX idx_distributed_tracing_trace_id ON distributed_tracing(trace_id);
CREATE INDEX idx_distributed_tracing_service_name ON distributed_tracing(service_name);
CREATE INDEX idx_distributed_tracing_start_time ON distributed_tracing(start_time);

-- Add foreign key constraints for referential integrity
ALTER TABLE service_instances ADD CONSTRAINT fk_service_instances_registry
    FOREIGN KEY (service_id) REFERENCES service_registry(service_id) ON DELETE CASCADE;

ALTER TABLE load_balancers ADD CONSTRAINT fk_load_balancers_registry
    FOREIGN KEY (service_type) REFERENCES service_registry(service_type) ON DELETE CASCADE;

ALTER TABLE circuit_breakers ADD CONSTRAINT fk_circuit_breakers_registry
    FOREIGN KEY (service_id) REFERENCES service_registry(service_id) ON DELETE CASCADE;

ALTER TABLE deployment_configs ADD CONSTRAINT fk_deployment_configs_registry
    FOREIGN KEY (service_type) REFERENCES service_registry(service_type) ON DELETE CASCADE;

ALTER TABLE service_mesh_config ADD CONSTRAINT fk_service_mesh_config_registry
    FOREIGN KEY (service_type) REFERENCES service_registry(service_type) ON DELETE CASCADE;

-- Add comments for documentation
ALTER TABLE service_instances COMMENT = 'Stores individual service instances for microservices architecture';
ALTER TABLE service_registry COMMENT = 'Stores service registry information for service discovery';
ALTER TABLE api_gateways COMMENT = 'Stores API gateway configurations for enterprise API management';
ALTER TABLE load_balancers COMMENT = 'Stores load balancer configurations for traffic distribution';
ALTER TABLE circuit_breakers COMMENT = 'Stores circuit breaker configurations for fault tolerance';
ALTER TABLE deployment_configs COMMENT = 'Stores deployment configurations for containerization';
ALTER TABLE service_metrics COMMENT = 'Stores service performance metrics for monitoring';
ALTER TABLE deployment_history COMMENT = 'Stores deployment history for audit and rollback';
ALTER TABLE service_mesh_config COMMENT = 'Stores service mesh configurations for advanced routing';
ALTER TABLE distributed_tracing COMMENT = 'Stores distributed tracing data for observability';
