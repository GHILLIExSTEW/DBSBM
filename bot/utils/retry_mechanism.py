"""
Retry mechanism utilities for DBSBM system.

This module provides retry mechanisms with exponential backoff,
circuit breaker patterns, and intelligent retry strategies.
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Optional, Type, Union, List, Any
from .exceptions import (
    DBSBMBaseException,
    NetworkException,
    TimeoutException,
    RateLimitException,
    is_retryable_exception,
    get_retry_delay,
)

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            NetworkException,
            TimeoutException,
            RateLimitException,
        ]


class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def on_success(self):
        """Record a successful execution."""
        self.failure_count = 0
        self.state = "CLOSED"

    def on_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for retry attempt."""
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    delay = min(delay, config.max_delay)

    if config.jitter:
        # Add jitter to prevent thundering herd
        import random

        delay *= 0.5 + random.random() * 0.5

    return delay


async def retry_async(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    **kwargs,
) -> Any:
    """Retry an async function with exponential backoff."""
    config = config or RetryConfig()
    circuit_breaker = circuit_breaker or CircuitBreaker()

    last_exception = None

    for attempt in range(1, config.max_attempts + 1):
        try:
            # Check circuit breaker
            if not circuit_breaker.can_execute():
                raise Exception("Circuit breaker is OPEN")

            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Record success
            circuit_breaker.on_success()
            return result

        except Exception as e:
            last_exception = e

            # Check if exception is retryable
            if not is_retryable_exception(e):
                logger.debug(f"Non-retryable exception: {e}")
                raise e

            # Record failure
            circuit_breaker.on_failure()

            if attempt < config.max_attempts:
                delay = calculate_delay(attempt, config)
                logger.warning(
                    f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed. Last error: {e}"
                )
                raise e

    raise last_exception


def retry(
    config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
):
    """Decorator for retrying functions."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_async(
                func, *args, config=config, circuit_breaker=circuit_breaker, **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'll use asyncio.run if needed
            if asyncio.iscoroutinefunction(func):
                return asyncio.run(async_wrapper(*args, **kwargs))
            else:
                # For truly sync functions, implement sync retry
                return _retry_sync(func, *args, config=config, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def _retry_sync(
    func: Callable, *args, config: Optional[RetryConfig] = None, **kwargs
) -> Any:
    """Retry a sync function with exponential backoff."""
    config = config or RetryConfig()
    last_exception = None

    for attempt in range(1, config.max_attempts + 1):
        try:
            result = func(*args, **kwargs)
            return result

        except Exception as e:
            last_exception = e

            # Check if exception is retryable
            if not is_retryable_exception(e):
                logger.debug(f"Non-retryable exception: {e}")
                raise e

            if attempt < config.max_attempts:
                delay = calculate_delay(attempt, config)
                logger.warning(
                    f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed. Last error: {e}"
                )
                raise e

    raise last_exception


class RetryManager:
    """Manager for retry operations with different strategies."""

    def __init__(self):
        self.circuit_breakers = {}
        self.retry_configs = {}

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a specific operation."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker()
        return self.circuit_breakers[name]

    def get_retry_config(self, name: str) -> RetryConfig:
        """Get or create a retry config for a specific operation."""
        if name not in self.retry_configs:
            self.retry_configs[name] = RetryConfig()
        return self.retry_configs[name]

    async def execute_with_retry(
        self, func: Callable, operation_name: str, *args, **kwargs
    ) -> Any:
        """Execute a function with retry logic."""
        circuit_breaker = self.get_circuit_breaker(operation_name)
        retry_config = self.get_retry_config(operation_name)

        return await retry_async(
            func, *args, config=retry_config, circuit_breaker=circuit_breaker, **kwargs
        )


# Global retry manager instance
retry_manager = RetryManager()


# Predefined retry configurations
DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=3, base_delay=0.5, max_delay=10.0, exponential_base=2.0
)

API_RETRY_CONFIG = RetryConfig(
    max_attempts=5, base_delay=1.0, max_delay=30.0, exponential_base=2.0
)

CACHE_RETRY_CONFIG = RetryConfig(
    max_attempts=2, base_delay=0.1, max_delay=5.0, exponential_base=1.5
)

NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=3, base_delay=1.0, max_delay=60.0, exponential_base=2.0
)
