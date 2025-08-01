"""
Logging configuration utilities for DBSBM system.

This module provides centralized logging configuration with proper
log levels, structured logging, and production-ready settings.
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional, Dict, Any
from datetime import datetime


class DailyRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Handler that creates a new log file each day."""

    def __init__(self, filename: str, when: str = "midnight", interval: int = 1, backup_count: int = 30):
        # Ensure the directory exists
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        super().__init__(filename, when=when, interval=interval, backupCount=backup_count)
        self.suffix = "%Y-%m-%d"
        self.namer = self._namer

    def _namer(self, default_name: str) -> str:
        """Custom namer to use date format in filename."""
        base_name = os.path.splitext(default_name)[0]
        extension = os.path.splitext(default_name)[1]
        return f"{base_name}{extension}"


class StructuredFormatter(logging.Formatter):
    """Structured formatter for JSON logging."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                           'filename', 'module', 'lineno', 'funcName', 'created',
                           'msecs', 'relativeCreated', 'thread', 'threadName',
                           'processName', 'process', 'getMessage', 'exc_info', 'exc_text',
                           'stack_info']:
                log_entry[key] = value

        return str(log_entry)


class ProductionFormatter(logging.Formatter):
    """Production formatter with minimal output."""

    def format(self, record):
        # Only include essential information in production
        if record.levelno >= logging.WARNING:
            return f"{record.levelname}: {record.getMessage()}"
        else:
            return record.getMessage()


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = False,
    production: bool = False,
    use_daily_logs: bool = True
) -> None:
    """Setup logging configuration for the application."""

    # Convert string level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if structured:
        formatter = StructuredFormatter()
    elif production:
        formatter = ProductionFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # File handler - use daily rotating logs if requested
    if use_daily_logs:
        # Create daily log file in db_logs directory
        daily_log_file = "db_logs/dbsbm_daily.log"
        file_handler = DailyRotatingFileHandler(
            daily_log_file,
            when="midnight",
            interval=1,
            backup_count=30  # Keep 30 days of logs
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Also add a console handler for critical errors only
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        # Original behavior - console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            # Create logs directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

    # Set specific logger levels for production
    if production:
        # Reduce debug logging for specific modules
        debug_loggers = [
            'bot.utils.enhanced_cache_manager',
            'bot.services.database_query_service',
            'bot.services.api_response_cache_service',
            'bot.services.bet_service',
            'bot.utils.multi_provider_api',
            'bot.utils.image_url_converter',
            'bot.utils.performance_monitor'
        ]

        for logger_name in debug_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)

    # Suppress noisy third-party loggers
    noisy_loggers = [
        'urllib3.connectionpool',
        'requests.packages.urllib3.connectionpool',
        'asyncio',
        'discord.gateway',
        'discord.client',
        'websockets.protocol'
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs):
    """Log performance metrics."""
    log_data = {
        "operation": operation,
        "duration_ms": round(duration * 1000, 2),
        **kwargs
    }
    logger.info(f"Performance: {log_data}")


def log_security_event(logger: logging.Logger, event: str, user_id: Optional[str] = None, **kwargs):
    """Log security events."""
    log_data = {
        "security_event": event,
        "user_id": user_id,
        **kwargs
    }
    logger.warning(f"Security: {log_data}")


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
):
    """Log errors with context information."""
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "user_id": user_id,
        **(context or {})
    }
    logger.error(f"Error: {error_data}", exc_info=True)


class LogLevelManager:
    """Manager for dynamic log level changes."""

    def __init__(self):
        self.original_levels = {}
        self.temporary_levels = {}

    def set_temporary_level(self, logger_name: str, level: str, duration: int = 300):
        """Set a temporary log level for a specific logger."""
        logger = logging.getLogger(logger_name)

        # Store original level if not already stored
        if logger_name not in self.original_levels:
            self.original_levels[logger_name] = logger.level

        # Set new level
        new_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(new_level)

        # Store temporary level info
        self.temporary_levels[logger_name] = {
            "level": new_level,
            "expires_at": datetime.now().timestamp() + duration
        }

    def restore_original_levels(self):
        """Restore original log levels."""
        current_time = datetime.now().timestamp()

        for logger_name, temp_info in list(self.temporary_levels.items()):
            if current_time > temp_info["expires_at"]:
                # Restore original level
                logger = logging.getLogger(logger_name)
                original_level = self.original_levels.get(
                    logger_name, logging.INFO)
                logger.setLevel(original_level)

                # Clean up
                del self.temporary_levels[logger_name]
                if logger_name in self.original_levels:
                    del self.original_levels[logger_name]


# Global log level manager
log_level_manager = LogLevelManager()


def configure_production_logging():
    """Configure logging for production environment."""
    setup_logging(
        log_level="INFO",
        log_file="logs/dbsbm.log",
        structured=True,
        production=True,
        use_daily_logs=True
    )


def configure_development_logging():
    """Configure logging for development environment."""
    setup_logging(
        log_level="DEBUG",
        log_file="logs/dbsbm_dev.log",
        structured=False,
        production=False,
        use_daily_logs=False  # Changed to False to enable DEBUG console output
    )


def configure_test_logging():
    """Configure logging for testing environment."""
    setup_logging(
        log_level="WARNING",
        log_file=None,
        structured=False,
        production=False,
        use_daily_logs=False  # Keep console output for tests
    )


# Auto-configure based on environment
def auto_configure_logging():
    """Automatically configure logging based on environment."""
    env = os.getenv("DBSBM_ENV", "development").lower()

    if env == "production":
        configure_production_logging()
    elif env == "testing":
        configure_test_logging()
    else:
        configure_development_logging()
