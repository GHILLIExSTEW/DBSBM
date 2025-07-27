-- Quick fix for ml_models table error
-- Run this to resolve the "Table 'ml_models' doesn't exist" error

CREATE TABLE IF NOT EXISTS ml_models (
    model_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
    model_path VARCHAR(500),
    config JSON NOT NULL,
    features JSON NOT NULL,
    target_variable VARCHAR(100) NOT NULL,
    performance_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    trained_at TIMESTAMP NULL,
    deployed_at TIMESTAMP NULL
);

-- Insert a default model to prevent errors
INSERT IGNORE INTO ml_models (model_id, name, description, model_type, version, status, config, features, target_variable) VALUES
('default_model', 'Default Model', 'Default placeholder model', 'classification', '1.0.0', 'inactive',
 '{"algorithm": "placeholder"}',
 '["placeholder"]',
 'placeholder');

SELECT 'ml_models table created successfully!' as status;
