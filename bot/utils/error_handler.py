"""
Error handling utility for DBSBM.
Provides custom exceptions, error tracking, and recovery mechanisms.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""

    error_type: str
    message: str
    timestamp: datetime
    traceback: str
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[int] = None
    guild_id: Optional[int] = None
    command: Optional[str] = None
    severity: str = "error"  # "debug", "info", "warning", "error", "critical"


class DBSBMError(Exception):
    """Base exception for DBSBM."""

    def __init__(
        self,
        message: str,
        user_id: Optional[int] = None,
        guild_id: Optional[int] = None,
        command: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.user_id = user_id
        self.guild_id = guild_id
        self.command = command
        self.timestamp = datetime.now()


class DatabaseError(DBSBMError):
    """Database-related errors."""

    pass


class APIError(DBSBMError):
    """API-related errors."""

    def __init__(
        self, message: str, api_name: str, status_code: Optional[int] = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.api_name = api_name
        self.status_code = status_code


class RateLimitError(DBSBMError):
    """Rate limiting errors."""

    def __init__(self, message: str, retry_after: Optional[float] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ValidationError(DBSBMError):
    """Data validation errors."""

    pass


class AuthenticationError(DBSBMError):
    """Authentication and authorization errors."""

    pass


class ConfigurationError(DBSBMError):
    """Configuration-related errors."""

    pass


class InsufficientUnitsError(DBSBMError):
    """Insufficient units/balance errors."""

    pass


class BettingError(DBSBMError):
    """Betting-related errors."""

    pass


class ImageGenerationError(DBSBMError):
    """Image generation errors."""

    pass


class ErrorHandler:
    """Error handling and tracking system."""

    def __init__(self, max_errors: int = 1000, alert_threshold: int = 10):
        """
        Initialize the error handler.

        Args:
            max_errors: Maximum number of errors to store in memory
            alert_threshold: Number of errors before triggering alert
        """
        self.max_errors = max_errors
        self.alert_threshold = alert_threshold

        # Error storage
        self.errors: deque = deque(maxlen=max_errors)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recent_errors: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Recovery strategies
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}

        # Alert callbacks
        self.alert_callbacks: List[Callable] = []

        # Error patterns for analysis
        self.error_patterns: Dict[str, Dict[str, Any]] = defaultdict(dict)

        logger.info("Error handler initialized")

    def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        guild_id: Optional[int] = None,
        command: Optional[str] = None,
        severity: str = "error",
    ):
        """
        Record an error occurrence.

        Args:
            error: The exception that occurred
            context: Additional context information
            user_id: Discord user ID if applicable
            guild_id: Discord guild ID if applicable
            command: Command name if applicable
            severity: Error severity level
        """
        error_record = ErrorRecord(
            error_type=type(error).__name__,
            message=str(error),
            timestamp=datetime.now(),
            traceback=traceback.format_exc(),
            context=context or {},
            user_id=user_id,
            guild_id=guild_id,
            command=command,
            severity=severity,
        )

        self.errors.append(error_record)
        self.error_counts[error_record.error_type] += 1
        self.recent_errors[error_record.error_type].append(error_record)

        # Update error patterns
        self._update_error_patterns(error_record)

        # Log the error
        log_message = (
            f"Error recorded: {error_record.error_type} - {error_record.message}"
        )
        if user_id:
            log_message += f" (User: {user_id})"
        if guild_id:
            log_message += f" (Guild: {guild_id})"
        if command:
            log_message += f" (Command: {command})"

        if severity == "critical":
            logger.critical(log_message)
        elif severity == "error":
            logger.error(log_message)
        elif severity == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Check if we should trigger an alert
        if self.error_counts[error_record.error_type] >= self.alert_threshold:
            self._trigger_error_alert(error_record)

    def _update_error_patterns(self, error_record: ErrorRecord):
        """Update error pattern analysis."""
        pattern_key = f"{error_record.error_type}_{error_record.command or 'unknown'}"

        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = {
                "count": 0,
                "first_seen": error_record.timestamp,
                "last_seen": error_record.timestamp,
                "users_affected": set(),
                "guilds_affected": set(),
                "contexts": [],
            }

        pattern = self.error_patterns[pattern_key]
        pattern["count"] += 1
        pattern["last_seen"] = error_record.timestamp

        if error_record.user_id:
            pattern["users_affected"].add(error_record.user_id)
        if error_record.guild_id:
            pattern["guilds_affected"].add(error_record.guild_id)

        pattern["contexts"].append(error_record.context)

        # Keep only recent contexts
        if len(pattern["contexts"]) > 10:
            pattern["contexts"] = pattern["contexts"][-10:]

    def _trigger_error_alert(self, error_record: ErrorRecord):
        """Trigger an alert for repeated errors."""
        alert = {
            "type": "error_threshold_exceeded",
            "error_type": error_record.error_type,
            "count": self.error_counts[error_record.error_type],
            "threshold": self.alert_threshold,
            "message": f"Error threshold exceeded for {error_record.error_type}",
            "timestamp": datetime.now().isoformat(),
        }

        logger.warning(f"Error alert: {alert['message']} (Count: {alert['count']})")

        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(alert))
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def add_recovery_strategy(self, error_type: Type[Exception], strategy: Callable):
        """
        Add a recovery strategy for a specific error type.

        Args:
            error_type: The exception type to handle
            strategy: Recovery function to call
        """
        self.recovery_strategies[error_type] = strategy
        logger.info(f"Added recovery strategy for {error_type.__name__}")

    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        guild_id: Optional[int] = None,
        command: Optional[str] = None,
    ) -> bool:
        """
        Handle an error with recovery strategies.

        Args:
            error: The exception to handle
            context: Additional context
            user_id: Discord user ID if applicable
            guild_id: Discord guild ID if applicable
            command: Command name if applicable

        Returns:
            bool: True if error was recovered, False otherwise
        """
        # Record the error
        self.record_error(error, context, user_id, guild_id, command)

        # Try to find a recovery strategy
        for error_type, strategy in self.recovery_strategies.items():
            if isinstance(error, error_type):
                try:
                    if asyncio.iscoroutinefunction(strategy):
                        result = await strategy(
                            error, context, user_id, guild_id, command
                        )
                    else:
                        result = strategy(error, context, user_id, guild_id, command)

                    if result:
                        logger.info(
                            f"Error recovered using strategy for {error_type.__name__}"
                        )
                        return True
                except Exception as recovery_error:
                    logger.error(f"Recovery strategy failed: {recovery_error}")

        return False

    def get_error_summary(
        self, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of errors for a time window.

        Args:
            time_window: Time window to consider (default: last hour)

        Returns:
            Dict containing error summary
        """
        if time_window is None:
            time_window = timedelta(hours=1)

        cutoff_time = datetime.now() - time_window
        recent_errors = [e for e in self.errors if e.timestamp >= cutoff_time]

        summary = {
            "total_errors": len(recent_errors),
            "error_types": defaultdict(int),
            "severity_counts": defaultdict(int),
            "commands_affected": defaultdict(int),
            "users_affected": set(),
            "guilds_affected": set(),
            "time_window": str(time_window),
        }

        for error in recent_errors:
            summary["error_types"][error.error_type] += 1
            summary["severity_counts"][error.severity] += 1

            if error.command:
                summary["commands_affected"][error.command] += 1

            if error.user_id:
                summary["users_affected"].add(error.user_id)
            if error.guild_id:
                summary["guilds_affected"].add(error.guild_id)

        # Convert sets to lists for JSON serialization
        summary["users_affected"] = list(summary["users_affected"])
        summary["guilds_affected"] = list(summary["guilds_affected"])

        return dict(summary)

    def get_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get error pattern analysis."""
        patterns = {}

        for pattern_key, pattern_data in self.error_patterns.items():
            patterns[pattern_key] = {
                "count": pattern_data["count"],
                "first_seen": pattern_data["first_seen"].isoformat(),
                "last_seen": pattern_data["last_seen"].isoformat(),
                "users_affected": len(pattern_data["users_affected"]),
                "guilds_affected": len(pattern_data["guilds_affected"]),
                "recent_contexts": pattern_data["contexts"][-5:],  # Last 5 contexts
            }

        return patterns

    def add_alert_callback(self, callback: Callable):
        """Add a callback for error alerts."""
        self.alert_callbacks.append(callback)

    def clear_errors(self):
        """Clear all stored errors."""
        self.errors.clear()
        self.error_counts.clear()
        self.recent_errors.clear()
        self.error_patterns.clear()
        logger.info("All errors cleared")

    def export_errors(self, filepath: str):
        """Export errors to a JSON file."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "errors": [
                    {
                        "error_type": error.error_type,
                        "message": error.message,
                        "timestamp": error.timestamp.isoformat(),
                        "traceback": error.traceback,
                        "context": error.context,
                        "user_id": error.user_id,
                        "guild_id": error.guild_id,
                        "command": error.command,
                        "severity": error.severity,
                    }
                    for error in self.errors
                ],
                "error_counts": dict(self.error_counts),
                "error_patterns": self.get_error_patterns(),
            }

            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Errors exported to {filepath}")

        except Exception as e:
            logger.error(f"Error exporting errors: {e}")


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_errors(context: Optional[Dict[str, Any]] = None):
    """
    Decorator to handle errors in functions.

    Args:
        context: Additional context to include with errors
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Extract user_id and guild_id from args if possible
                user_id = None
                guild_id = None
                command = func.__name__

                # Try to extract from Discord interaction/context
                if args and hasattr(args[0], "user"):
                    user_id = args[0].user.id
                if args and hasattr(args[0], "guild_id"):
                    guild_id = args[0].guild_id

                # Handle the error
                error_handler = get_error_handler()
                recovered = await error_handler.handle_error(
                    e, context, user_id, guild_id, command
                )

                if not recovered:
                    # Re-raise the error if not recovered
                    raise

                return None

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extract user_id and guild_id from args if possible
                user_id = None
                guild_id = None
                command = func.__name__

                # Try to extract from Discord interaction/context
                if args and hasattr(args[0], "user"):
                    user_id = args[0].user.id
                if args and hasattr(args[0], "guild_id"):
                    guild_id = args[0].guild_id

                # Handle the error
                error_handler = get_error_handler()
                # For sync functions, we'll handle the error but not recover
                error_handler.record_error(e, context, user_id, guild_id, command)

                # Re-raise the error
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Default recovery strategies
async def database_recovery_strategy(
    error: Exception,
    context: Dict[str, Any],
    user_id: Optional[int],
    guild_id: Optional[int],
    command: Optional[str],
) -> bool:
    """Enhanced recovery strategy for database errors."""
    if isinstance(error, DatabaseError):
        logger.info("Attempting database recovery...")

        try:
            # Get database manager from context or global
            db_manager = context.get("db_manager")
            if not db_manager:
                logger.warning("No database manager available for recovery")
                return False

            # Attempt to reconnect
            logger.info("Attempting database reconnection...")
            await db_manager.close()  # Close existing connections
            await asyncio.sleep(1)  # Brief delay

            # Try to reconnect
            pool = await db_manager.connect()
            if pool:
                logger.info("Database recovery successful")
                return True
            else:
                logger.error("Database recovery failed - could not reconnect")
                return False

        except Exception as recovery_error:
            logger.error(f"Database recovery failed: {recovery_error}")
            return False

    return False


async def api_recovery_strategy(
    error: Exception,
    context: Dict[str, Any],
    user_id: Optional[int],
    guild_id: Optional[int],
    command: Optional[str],
) -> bool:
    """Enhanced recovery strategy for API errors."""
    if isinstance(error, APIError):
        logger.info(f"Attempting API recovery for {error.api_name}...")

        try:
            # Implement exponential backoff
            retry_count = context.get("retry_count", 0)
            max_retries = context.get("max_retries", 3)

            if retry_count >= max_retries:
                logger.warning(f"Max retries ({max_retries}) exceeded for API recovery")
                return False

            # Calculate backoff delay
            backoff_delay = min(2**retry_count, 60)  # Cap at 60 seconds
            logger.info(
                f"Waiting {backoff_delay} seconds before retry {retry_count + 1}"
            )

            await asyncio.sleep(backoff_delay)

            # Update retry count in context
            context["retry_count"] = retry_count + 1

            logger.info(f"API recovery attempt {retry_count + 1} completed")
            return True  # Allow retry

        except Exception as recovery_error:
            logger.error(f"API recovery failed: {recovery_error}")
            return False

    return False


async def memory_cleanup_strategy(
    error: Exception,
    context: Dict[str, Any],
    user_id: Optional[int],
    guild_id: Optional[int],
    command: Optional[str],
) -> bool:
    """Recovery strategy for memory-related errors."""
    try:
        import gc
        import psutil

        logger.info("Attempting memory cleanup...")

        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")

        # Get memory usage info
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        logger.info(f"Current memory usage: {memory_mb:.1f} MB")

        # If memory usage is high, try to clear caches
        if memory_mb > 500:  # 500MB threshold
            logger.warning("High memory usage detected, clearing caches...")

            # Clear any caches in context
            if "cache_manager" in context:
                cache_manager = context["cache_manager"]
                if hasattr(cache_manager, "clear_all"):
                    await cache_manager.clear_all()
                    logger.info("Cache cleared")

        return True

    except Exception as cleanup_error:
        logger.error(f"Memory cleanup failed: {cleanup_error}")
        return False


async def connection_recovery_strategy(
    error: Exception,
    context: Dict[str, Any],
    user_id: Optional[int],
    guild_id: Optional[int],
    command: Optional[str],
) -> bool:
    """Recovery strategy for connection-related errors."""
    try:
        logger.info("Attempting connection recovery...")

        # Check if it's a connection error
        if "connection" in str(error).lower() or "timeout" in str(error).lower():
            logger.info("Connection error detected, attempting recovery...")

            # Wait before retry
            await asyncio.sleep(2)

            # Try to reinitialize connections
            if "db_manager" in context:
                db_manager = context["db_manager"]
                await db_manager.close()
                await asyncio.sleep(1)
                await db_manager.connect()

            logger.info("Connection recovery completed")
            return True

        return False

    except Exception as recovery_error:
        logger.error(f"Connection recovery failed: {recovery_error}")
        return False


# Initialize default recovery strategies
def initialize_default_recovery_strategies():
    """Initialize default recovery strategies."""
    error_handler = get_error_handler()
    error_handler.add_recovery_strategy(DatabaseError, database_recovery_strategy)
    error_handler.add_recovery_strategy(APIError, api_recovery_strategy)
    error_handler.add_recovery_strategy(MemoryError, memory_cleanup_strategy)
    error_handler.add_recovery_strategy(ConnectionError, connection_recovery_strategy)
    error_handler.add_recovery_strategy(TimeoutError, connection_recovery_strategy)


if __name__ == "__main__":
    # Test the error handler
    async def test_error_handler():
        error_handler = get_error_handler()

        # Test error recording
        try:
            raise ValueError("Test error")
        except Exception as e:
            error_handler.record_error(
                e, {"test": "true"}, 123456789, 987654321, "test_command"
            )

        # Test error summary
        summary = error_handler.get_error_summary()
        print(f"Error summary: {summary}")

        # Test error patterns
        patterns = error_handler.get_error_patterns()
        print(f"Error patterns: {patterns}")

    asyncio.run(test_error_handler())
