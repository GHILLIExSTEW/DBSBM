"""
Centralized Configuration Management for DBSBM System

This module provides a centralized configuration system using Pydantic for
type validation, environment variable management, and configuration validation.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import Field, field_validator
from pydantic.types import SecretStr
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    host: str = Field("localhost", env="POSTGRES_HOST", description="PostgreSQL host address")
    port: int = Field(5432, env="POSTGRES_PORT", description="PostgreSQL port")
    user: str = Field("postgres", env="POSTGRES_USER", description="PostgreSQL username")
    password: SecretStr = Field(
        SecretStr(""), env="POSTGRES_PASSWORD", description="PostgreSQL password"
    )
    database: str = Field("dbsbm", env="POSTGRES_DB", description="PostgreSQL database name")

    # Connection pool settings
    pool_min_size: int = Field(
        1, env="PG_POOL_MIN_SIZE", ge=1, le=50, description="Minimum pool size"
    )
    pool_max_size: int = Field(
        10, env="PG_POOL_MAX_SIZE", ge=1, le=100, description="Maximum pool size"
    )
    pool_max_overflow: int = Field(
        5,
        env="PG_POOL_MAX_OVERFLOW",
        ge=0,
        le=50,
        description="Maximum overflow connections",
    )
    pool_timeout: int = Field(
        30,
        env="PG_POOL_TIMEOUT",
        ge=5,
        le=300,
        description="Connection pool timeout in seconds",
    )
    connect_timeout: int = Field(
        30,
        env="PG_CONNECT_TIMEOUT",
        ge=5,
        le=300,
        description="Connection timeout in seconds",
    )

    @field_validator("pool_max_size")
    @classmethod
    def validate_pool_max_size(cls, v, info):
        """Ensure max_size is greater than min_size."""
        if (
            info.data
            and "pool_min_size" in info.data
            and v < info.data["pool_min_size"]
        ):
            raise ValueError(
                "pool_max_size must be greater than or equal to pool_min_size"
            )
        return v

    model_config = {"env_prefix": "PG_", "case_sensitive": False}


class APISettings(BaseSettings):
    """API configuration settings."""

    key: SecretStr = Field(
        SecretStr(""), env="API_KEY", description="API Sports API key"
    )
    rapidapi_key: Optional[SecretStr] = Field(
        None, env="RAPIDAPI_KEY", description="RapidAPI key"
    )
    datagolf_key: Optional[SecretStr] = Field(
        None, env="DATAGOLF_API_KEY", description="DataGolf API key"
    )
    weather_key: Optional[SecretStr] = Field(
        None, env="WEATHER_API_KEY", description="WeatherAPI key"
    )
    timeout: int = Field(
        30,
        env="API_TIMEOUT",
        ge=5,
        le=300,
        description="API request timeout in seconds",
    )
    retry_attempts: int = Field(
        3, env="API_RETRY_ATTEMPTS", ge=1, le=10, description="Number of retry attempts"
    )
    retry_delay: int = Field(
        5,
        env="API_RETRY_DELAY",
        ge=1,
        le=60,
        description="Delay between retries in seconds",
    )
    enabled: bool = Field(
        True, env="API_ENABLED", description="Enable API functionality"
    )

    model_config = {"env_prefix": "API_", "case_sensitive": False}


class DiscordSettings(BaseSettings):
    """Discord bot configuration settings."""

    token: SecretStr = Field(
        SecretStr(""), env="DISCORD_TOKEN", description="Discord bot token"
    )
    test_guild_id: Optional[int] = Field(
        None, env="TEST_GUILD_ID", description="Test guild ID for development"
    )
    authorized_user_id: Optional[int] = Field(
        None, env="AUTHORIZED_USER_ID", description="Authorized user ID for maintenance"
    )
    authorized_load_logo_user_id: Optional[int] = Field(
        None,
        env="AUTHORIZED_LOAD_LOGO_USER_ID",
        description="Authorized user ID for logo loading",
    )

    @field_validator(
        "test_guild_id",
        "authorized_user_id",
        "authorized_load_logo_user_id",
        mode="before",
    )
    @classmethod
    def validate_discord_ids(cls, v):
        """Validate Discord IDs are positive integers."""
        if v is not None:
            try:
                v = int(v)
                if v <= 0:
                    raise ValueError("Discord ID must be a positive integer")
                return v
            except (ValueError, TypeError):
                raise ValueError("Discord ID must be a valid integer")
        return v

    model_config = {"env_prefix": "DISCORD_", "case_sensitive": False}


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    host: str = Field("localhost", env="REDIS_HOST", description="Redis host address")
    port: int = Field(6379, env="REDIS_PORT", description="Redis port")
    password: Optional[SecretStr] = Field(
        None, env="REDIS_PASSWORD", description="Redis password"
    )
    database: int = Field(
        0, env="REDIS_DB", ge=0, le=15, description="Redis database number"
    )
    enabled: bool = Field(
        False, env="REDIS_ENABLED", description="Enable Redis caching"
    )

    model_config = {"env_prefix": "REDIS_", "case_sensitive": False}


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: str = Field("INFO", env="LOG_LEVEL", description="Logging level")
    format: str = Field(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        env="LOG_FORMAT",
        description="Log format string",
    )
    file: Optional[str] = Field(None, env="LOG_FILE", description="Log file path")
    max_size: int = Field(
        10, env="LOG_MAX_SIZE", ge=1, le=100, description="Maximum log file size in MB"
    )
    backup_count: int = Field(
        5, env="LOG_BACKUP_COUNT", ge=0, le=20, description="Number of backup files"
    )

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {", ".join(valid_levels)}')
        return v.upper()

    model_config = {"env_prefix": "LOG_", "case_sensitive": False}


class WebAppSettings(BaseSettings):
    """Web application configuration settings."""

    port: int = Field(
        25594, env="WEBAPP_PORT", ge=1024, le=65535, description="Web app port"
    )
    host: str = Field("0.0.0.0", env="WEBAPP_HOST", description="Web app host")
    debug: bool = Field(False, env="FLASK_DEBUG", description="Enable Flask debug mode")
    env: str = Field("production", env="FLASK_ENV", description="Flask environment")
    web_server_url: Optional[str] = Field(
        None, env="WEB_SERVER_URL", description="Web server URL"
    )

    @field_validator("env")
    @classmethod
    def validate_flask_env(cls, v):
        """Validate Flask environment."""
        valid_envs = ["development", "production", "testing"]
        if v.lower() not in valid_envs:
            raise ValueError(
                f'Flask environment must be one of: {", ".join(valid_envs)}'
            )
        return v.lower()

    model_config = {"env_prefix": "WEBAPP_", "case_sensitive": False}


class SchedulerSettings(BaseSettings):
    """Scheduler configuration settings."""

    mode: Optional[str] = Field(
        None, env="SCHEDULER_MODE", description="Scheduler mode"
    )
    enabled: bool = Field(True, env="SCHEDULER_ENABLED", description="Enable scheduler")
    interval: int = Field(
        300,
        env="SCHEDULER_INTERVAL",
        ge=60,
        le=3600,
        description="Scheduler interval in seconds",
    )

    model_config = {"env_prefix": "SCHEDULER_", "case_sensitive": False}


class FeatureSettings(BaseSettings):
    """Feature flag configuration settings."""

    run_api_fetch_on_start: bool = Field(
        False, env="RUN_API_FETCH_ON_START", description="Run API fetch on startup"
    )
    api_enabled: bool = Field(
        True, env="API_ENABLED", description="Enable API functionality"
    )
    cache_enabled: bool = Field(
        False, env="CACHE_ENABLED", description="Enable caching"
    )
    monitoring_enabled: bool = Field(
        True, env="MONITORING_ENABLED", description="Enable monitoring"
    )

    model_config = {"env_prefix": "FEATURE_", "case_sensitive": False}


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: str = Field(
        "production", env="ENVIRONMENT", description="Application environment"
    )

    # Component settings - make them optional to avoid validation errors during import
    database: Optional[DatabaseSettings] = None
    api: Optional[APISettings] = None
    discord: Optional[DiscordSettings] = None
    redis: Optional[RedisSettings] = None
    logging: Optional[LoggingSettings] = None
    webapp: Optional[WebAppSettings] = None
    scheduler: Optional[SchedulerSettings] = None
    features: Optional[FeatureSettings] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize nested settings after main settings are loaded
        self.database = DatabaseSettings()
        self.api = APISettings()
        self.discord = DiscordSettings()
        self.redis = RedisSettings()
        self.logging = LoggingSettings()
        self.webapp = WebAppSettings()
        self.scheduler = SchedulerSettings()
        self.features = FeatureSettings()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ["development", "staging", "production", "testing"]
        if v.lower() not in valid_envs:
            raise ValueError(f'Environment must be one of: {", ".join(valid_envs)}')
        return v.lower()

    def get_masked_config(self) -> Dict[str, any]:
        """Get configuration with sensitive data masked for logging."""
        config = self.model_dump()

        # Mask sensitive fields
        sensitive_fields = ["password", "token", "key"]
        for section in config:
            if isinstance(config[section], dict):
                for field in config[section]:
                    if any(
                        sensitive in field.lower() for sensitive in sensitive_fields
                    ):
                        config[section][field] = "***MASKED***"

        return config

    def validate_required_settings(self) -> List[str]:
        """Validate all required settings and return list of missing/invalid settings."""
        errors = []

        # Check database settings
        if not self.database.host:
            errors.append("PG_HOST is required")
        if not self.database.user:
            errors.append("PG_USER is required")
        if not self.database.password.get_secret_value():
            errors.append("PG_PASSWORD is required")
        if not self.database.database:
            errors.append("PG_DATABASE is required")

        # Check Discord settings
        if not self.discord.token.get_secret_value():
            errors.append("DISCORD_TOKEN is required")

        # Check API settings
        if not self.api.key.get_secret_value():
            errors.append("API_KEY is required")

        return errors

    def get_connection_string(self) -> str:
        """Get database connection string (without password)."""
        return f"postgresql://{self.database.user}:***@{self.database.host}:{self.database.port}/{self.database.database}"

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == "testing"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings


def validate_settings() -> List[str]:
    """Validate all settings and return list of errors."""
    settings = get_settings()
    return settings.validate_required_settings()


def get_config_summary() -> Dict[str, any]:
    """Get a summary of the current configuration (with sensitive data masked)."""
    settings = get_settings()
    return settings.get_masked_config()


# Convenience functions for backward compatibility
def get_database_config() -> Dict[str, any]:
    """Get database configuration."""
    settings = get_settings()
    return {
        "host": settings.database.host,
        "port": settings.database.port,
        "user": settings.database.user,
        "password": settings.database.password.get_secret_value(),
        "database": settings.database.database,
        "pool_min_size": settings.database.pool_min_size,
        "pool_max_size": settings.database.pool_max_size,
        "pool_max_overflow": settings.database.pool_max_overflow,
        "pool_timeout": settings.database.pool_timeout,
        "connect_timeout": settings.database.connect_timeout,
    }


def get_api_config() -> Dict[str, any]:
    """Get API configuration."""
    settings = get_settings()
    return {
        "key": settings.api.key.get_secret_value(),
        "rapidapi_key": (
            settings.api.rapidapi_key.get_secret_value()
            if settings.api.rapidapi_key
            else None
        ),
        "datagolf_key": (
            settings.api.datagolf_key.get_secret_value()
            if settings.api.datagolf_key
            else None
        ),
        "timeout": settings.api.timeout,
        "retry_attempts": settings.api.retry_attempts,
        "retry_delay": settings.api.retry_delay,
        "enabled": settings.api.enabled,
    }


def get_discord_config() -> Dict[str, any]:
    """Get Discord configuration."""
    settings = get_settings()
    return {
        "token": settings.discord.token.get_secret_value(),
        "test_guild_id": settings.discord.test_guild_id,
        "authorized_user_id": settings.discord.authorized_user_id,
        "authorized_load_logo_user_id": settings.discord.authorized_load_logo_user_id,
    }


def get_redis_config() -> Dict[str, any]:
    """Get Redis configuration."""
    settings = get_settings()
    return {
        "host": settings.redis.host,
        "port": settings.redis.port,
        "password": (
            settings.redis.password.get_secret_value()
            if settings.redis.password
            else None
        ),
        "database": settings.redis.database,
        "enabled": settings.redis.enabled,
    }


def get_logging_config() -> Dict[str, any]:
    """Get logging configuration."""
    settings = get_settings()
    return {
        "level": settings.logging.level,
        "format": settings.logging.format,
        "file": settings.logging.file,
        "max_size": settings.logging.max_size,
        "backup_count": settings.logging.backup_count,
    }


def get_webapp_config() -> Dict[str, any]:
    """Get webapp configuration."""
    settings = get_settings()
    return {
        "port": settings.webapp.port,
        "host": settings.webapp.host,
        "debug": settings.webapp.debug,
        "env": settings.webapp.env,
        "web_server_url": settings.webapp.web_server_url,
    }
