"""
Custom exception classes for DBSBM system.

This module provides specific exception types for different error scenarios
to improve error handling and debugging capabilities.
"""

from typing import Optional, Dict, Any


class DBSBMBaseException(Exception):
    """Base exception class for DBSBM system."""

    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class DatabaseException(DBSBMBaseException):
    """Exception raised for database-related errors."""

    def __init__(self, message: str, query: Optional[str] = None, params: Optional[tuple] = None):
        super().__init__(message, "DB_ERROR", {
            "query": query, "params": params})


class CacheException(DBSBMBaseException):
    """Exception raised for cache-related errors."""

    def __init__(self, message: str, operation: Optional[str] = None, key: Optional[str] = None):
        super().__init__(message, "CACHE_ERROR", {
            "operation": operation, "key": key})


class APIException(DBSBMBaseException):
    """Exception raised for API-related errors."""

    def __init__(self, message: str, endpoint: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(message, "API_ERROR", {
            "endpoint": endpoint, "status_code": status_code})


class AuthenticationException(DBSBMBaseException):
    """Exception raised for authentication-related errors."""

    def __init__(self, message: str, user_id: Optional[str] = None, permission: Optional[str] = None):
        super().__init__(message, "AUTH_ERROR", {
            "user_id": user_id, "permission": permission})


class ValidationException(DBSBMBaseException):
    """Exception raised for data validation errors."""

    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR",
                         {"field": field, "value": value})


class ConfigurationException(DBSBMBaseException):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIG_ERROR", {"config_key": config_key})


class ServiceException(DBSBMBaseException):
    """Exception raised for service-related errors."""

    def __init__(self, message: str, service_name: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, "SERVICE_ERROR", {
            "service_name": service_name, "operation": operation})


class RateLimitException(DBSBMBaseException):
    """Exception raised for rate limiting errors."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, "RATE_LIMIT_ERROR",
                         {"retry_after": retry_after})


class NetworkException(DBSBMBaseException):
    """Exception raised for network-related errors."""

    def __init__(self, message: str, host: Optional[str] = None, port: Optional[int] = None):
        super().__init__(message, "NETWORK_ERROR",
                         {"host": host, "port": port})


class TimeoutException(DBSBMBaseException):
    """Exception raised for timeout errors."""

    def __init__(self, message: str, timeout_seconds: Optional[float] = None, operation: Optional[str] = None):
        super().__init__(message, "TIMEOUT_ERROR", {
            "timeout_seconds": timeout_seconds, "operation": operation})


class ResourceNotFoundException(DBSBMBaseException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        super().__init__(message, "NOT_FOUND_ERROR", {
            "resource_type": resource_type, "resource_id": resource_id})


class ConflictException(DBSBMBaseException):
    """Exception raised for resource conflicts."""

    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        super().__init__(message, "CONFLICT_ERROR", {
            "resource_type": resource_type, "resource_id": resource_id})


class SecurityException(DBSBMBaseException):
    """Exception raised for security-related errors."""

    def __init__(self, message: str, security_event: Optional[str] = None, severity: Optional[str] = None):
        super().__init__(message, "SECURITY_ERROR", {
            "security_event": security_event, "severity": severity})


class DataIntegrityException(DBSBMBaseException):
    """Exception raised for data integrity errors."""

    def __init__(self, message: str, table: Optional[str] = None, constraint: Optional[str] = None):
        super().__init__(message, "DATA_INTEGRITY_ERROR",
                         {"table": table, "constraint": constraint})


class ExternalServiceException(DBSBMBaseException):
    """Exception raised for external service errors."""

    def __init__(self, message: str, service_name: Optional[str] = None, endpoint: Optional[str] = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", {
            "service_name": service_name, "endpoint": endpoint})


# Utility functions for exception handling
def handle_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> DBSBMBaseException:
    """Convert generic exceptions to specific DBSBM exceptions."""
    if isinstance(exception, DBSBMBaseException):
        return exception

    # Map common exception types to specific DBSBM exceptions
    if isinstance(exception, (ConnectionError, OSError)):
        return NetworkException(str(exception))
    elif isinstance(exception, TimeoutError):
        return TimeoutException(str(exception))
    elif isinstance(exception, ValueError):
        return ValidationException(str(exception))
    elif isinstance(exception, KeyError):
        return ResourceNotFoundException(f"Resource not found: {exception}")
    elif isinstance(exception, PermissionError):
        return AuthenticationException(str(exception))
    else:
        return DBSBMBaseException(str(exception), "UNKNOWN_ERROR", context)


def is_retryable_exception(exception: Exception) -> bool:
    """Check if an exception is retryable."""
    if isinstance(exception, (NetworkException, TimeoutException, RateLimitException)):
        return True
    elif isinstance(exception, (ValidationException, AuthenticationException, ResourceNotFoundException)):
        return False
    else:
        # Default to retryable for unknown exceptions
        return True


def get_retry_delay(exception: Exception, attempt: int) -> float:
    """Calculate retry delay based on exception type and attempt number."""
    base_delay = 1.0

    if isinstance(exception, RateLimitException):
        # Use retry_after from exception if available
        retry_after = exception.details.get("retry_after")
        if retry_after:
            return float(retry_after)
        return base_delay * (2 ** attempt)  # Exponential backoff

    elif isinstance(exception, TimeoutException):
        return base_delay * (2 ** attempt)  # Exponential backoff

    elif isinstance(exception, NetworkException):
        return base_delay * (1.5 ** attempt)  # Moderate backoff

    else:
        return base_delay * (2 ** attempt)  # Default exponential backoff
