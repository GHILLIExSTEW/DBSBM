"""
API Performance Monitoring System for DBSBM.
Provides comprehensive monitoring of API performance, response times, and error tracking.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from bot.utils.enhanced_cache_manager import EnhancedCacheManager

logger = logging.getLogger(__name__)


class APIMetricType(Enum):
    """Types of API metrics."""
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    REQUEST_COUNT = "request_count"
    CACHE_HIT_RATE = "cache_hit_rate"
    THROUGHPUT = "throughput"


@dataclass
class APIMetric:
    """Individual API performance metric."""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    success: bool
    cache_hit: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[int] = None
    guild_id: Optional[int] = None
    error_message: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None


@dataclass
class APIAlert:
    """API performance alert."""
    alert_type: str
    message: str
    severity: str
    timestamp: datetime
    endpoint: Optional[str] = None
    threshold: Optional[float] = None
    current_value: Optional[float] = None


class APIPerformanceMonitor:
    """Comprehensive API performance monitoring system."""

    def __init__(self, max_history: int = 10000, alert_thresholds: Optional[Dict[str, float]] = None):
        """Initialize the API performance monitor."""
        self.max_history = max_history
        self.cache_manager = EnhancedCacheManager()

        # Storage for metrics and alerts
        self.metrics: deque = deque(maxlen=max_history)
        self.alerts: deque = deque(maxlen=1000)

        # Performance tracking
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0,
            'cache_hits': 0,
            'last_request': None,
            'error_counts': defaultdict(int)
        })

        # Alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'response_time_ms': 5000,  # 5 seconds
            'error_rate_percent': 10.0,  # 10%
            'throughput_requests_per_minute': 1000,  # 1000 requests per minute
            'cache_hit_rate_percent': 80.0,  # 80%
        }

        # Alert callbacks
        self.alert_callbacks: List[Callable] = []

        # Background monitoring
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None

        logger.info("API Performance Monitor initialized")

    async def start_monitoring(self) -> None:
        """Start continuous API performance monitoring."""
        if self.is_monitoring:
            logger.warning("API performance monitoring is already active")
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("API performance monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop API performance monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("API performance monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._check_performance_thresholds()
                await self._cleanup_old_metrics()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in API monitoring loop: {e}")
                await asyncio.sleep(5)

    def record_api_call(self, endpoint: str, method: str, response_time: float,
                        status_code: int, success: bool = True, cache_hit: bool = False,
                        user_id: Optional[int] = None, guild_id: Optional[int] = None,
                        error_message: Optional[str] = None, request_size: Optional[int] = None,
                        response_size: Optional[int] = None) -> None:
        """Record an API call metric."""
        metric = APIMetric(
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code,
            success=success,
            cache_hit=cache_hit,
            user_id=user_id,
            guild_id=guild_id,
            error_message=error_message,
            request_size=request_size,
            response_size=response_size
        )

        self.metrics.append(metric)

        # Update endpoint statistics
        endpoint_key = f"{method}:{endpoint}"
        stats = self.endpoint_stats[endpoint_key]

        stats['total_requests'] += 1
        stats['total_response_time'] += response_time
        stats['last_request'] = datetime.now()

        if success:
            stats['successful_requests'] += 1
        else:
            stats['failed_requests'] += 1
            if error_message:
                stats['error_counts'][error_message] += 1

        if cache_hit:
            stats['cache_hits'] += 1

        # Update min/max response times
        if response_time < stats['min_response_time']:
            stats['min_response_time'] = response_time
        if response_time > stats['max_response_time']:
            stats['max_response_time'] = response_time

        # Check for immediate alerts
        asyncio.create_task(self._check_immediate_alerts(metric))

    async def _check_immediate_alerts(self, metric: APIMetric) -> None:
        """Check for immediate alert conditions."""
        # Check response time threshold
        if metric.response_time > self.alert_thresholds['response_time_ms'] / 1000:
            await self._create_alert(
                "slow_response_time",
                f"Slow API response: {metric.endpoint} took {metric.response_time:.2f}s",
                "warning",
                metric.endpoint,
                self.alert_thresholds['response_time_ms'] / 1000,
                metric.response_time
            )

        # Check for high error rates
        if not metric.success:
            endpoint_key = f"{metric.method}:{metric.endpoint}"
            stats = self.endpoint_stats[endpoint_key]
            error_rate = (stats['failed_requests'] /
                          stats['total_requests']) * 100

            if error_rate > self.alert_thresholds['error_rate_percent']:
                await self._create_alert(
                    "high_error_rate",
                    f"High error rate for {metric.endpoint}: {error_rate:.1f}%",
                    "error",
                    metric.endpoint,
                    self.alert_thresholds['error_rate_percent'],
                    error_rate
                )

    async def _check_performance_thresholds(self) -> None:
        """Check performance thresholds and create alerts."""
        for endpoint_key, stats in self.endpoint_stats.items():
            if stats['total_requests'] == 0:
                continue

            # Calculate current metrics
            avg_response_time = stats['total_response_time'] / \
                stats['total_requests']
            error_rate = (stats['failed_requests'] /
                          stats['total_requests']) * 100
            cache_hit_rate = (stats['cache_hits'] /
                              stats['total_requests']) * 100

            # Check response time threshold
            if avg_response_time > self.alert_thresholds['response_time_ms'] / 1000:
                await self._create_alert(
                    "avg_response_time_high",
                    f"High average response time for {endpoint_key}: {avg_response_time:.2f}s",
                    "warning",
                    endpoint_key,
                    self.alert_thresholds['response_time_ms'] / 1000,
                    avg_response_time
                )

            # Check error rate threshold
            if error_rate > self.alert_thresholds['error_rate_percent']:
                await self._create_alert(
                    "error_rate_high",
                    f"High error rate for {endpoint_key}: {error_rate:.1f}%",
                    "error",
                    endpoint_key,
                    self.alert_thresholds['error_rate_percent'],
                    error_rate
                )

            # Check cache hit rate threshold
            if cache_hit_rate < self.alert_thresholds['cache_hit_rate_percent']:
                await self._create_alert(
                    "cache_hit_rate_low",
                    f"Low cache hit rate for {endpoint_key}: {cache_hit_rate:.1f}%",
                    "warning",
                    endpoint_key,
                    self.alert_thresholds['cache_hit_rate_percent'],
                    cache_hit_rate
                )

    async def _create_alert(self, alert_type: str, message: str, severity: str,
                            endpoint: Optional[str] = None, threshold: Optional[float] = None,
                            current_value: Optional[float] = None) -> None:
        """Create and store an alert."""
        alert = APIAlert(
            alert_type=alert_type,
            message=message,
            severity=severity,
            timestamp=datetime.now(),
            endpoint=endpoint,
            threshold=threshold,
            current_value=current_value
        )

        self.alerts.append(alert)

        # Log the alert
        log_level = logging.ERROR if severity == "error" else logging.WARNING
        logger.log(log_level, f"API Alert: {message}")

        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics to prevent memory issues."""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Remove old metrics
        old_metrics = [m for m in self.metrics if m.timestamp < cutoff_time]
        for metric in old_metrics:
            self.metrics.remove(metric)

        # Remove old alerts
        old_alerts = [a for a in self.alerts if a.timestamp < cutoff_time]
        for alert in old_alerts:
            self.alerts.remove(alert)

        if old_metrics or old_alerts:
            logger.debug(
                f"Cleaned up {len(old_metrics)} old metrics and {len(old_alerts)} old alerts")

    def add_alert_callback(self, callback: Callable) -> None:
        """Add an alert callback function."""
        self.alert_callbacks.append(callback)
        logger.info("Alert callback added")

    def get_endpoint_stats(self, endpoint: Optional[str] = None,
                           time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get statistics for specific endpoint or all endpoints."""
        if endpoint:
            endpoint_key = endpoint
            if endpoint_key not in self.endpoint_stats:
                return {"error": "Endpoint not found"}

            stats = self.endpoint_stats[endpoint_key]
            return self._calculate_endpoint_stats(stats, time_window)
        else:
            # Return stats for all endpoints
            all_stats = {}
            for endpoint_key, stats in self.endpoint_stats.items():
                all_stats[endpoint_key] = self._calculate_endpoint_stats(
                    stats, time_window)
            return all_stats

    def _calculate_endpoint_stats(self, stats: Dict[str, Any],
                                  time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Calculate statistics for an endpoint."""
        if stats['total_requests'] == 0:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "error_rate": 0.0,
                "cache_hit_rate": 0.0,
                "last_request": None
            }

        avg_response_time = stats['total_response_time'] / \
            stats['total_requests']
        error_rate = (stats['failed_requests'] / stats['total_requests']) * 100
        cache_hit_rate = (stats['cache_hits'] / stats['total_requests']) * 100

        return {
            "total_requests": stats['total_requests'],
            "successful_requests": stats['successful_requests'],
            "failed_requests": stats['failed_requests'],
            "avg_response_time": avg_response_time,
            "min_response_time": stats['min_response_time'] if stats['min_response_time'] != float('inf') else 0.0,
            "max_response_time": stats['max_response_time'],
            "error_rate": error_rate,
            "cache_hit_rate": cache_hit_rate,
            "last_request": stats['last_request'].isoformat() if stats['last_request'] else None,
            "error_counts": dict(stats['error_counts'])
        }

    def get_performance_summary(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get overall API performance summary."""
        if not self.metrics:
            return {"error": "No metrics available"}

        # Filter metrics by time window
        if time_window:
            cutoff_time = datetime.now() - time_window
            filtered_metrics = [
                m for m in self.metrics if m.timestamp >= cutoff_time]
        else:
            filtered_metrics = list(self.metrics)

        if not filtered_metrics:
            return {"error": "No metrics in time window"}

        # Calculate overall statistics
        total_requests = len(filtered_metrics)
        successful_requests = sum(1 for m in filtered_metrics if m.success)
        failed_requests = total_requests - successful_requests
        total_response_time = sum(m.response_time for m in filtered_metrics)
        cache_hits = sum(1 for m in filtered_metrics if m.cache_hit)

        avg_response_time = total_response_time / \
            total_requests if total_requests > 0 else 0
        error_rate = (failed_requests / total_requests) * \
            100 if total_requests > 0 else 0
        cache_hit_rate = (cache_hits / total_requests) * \
            100 if total_requests > 0 else 0

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "avg_response_time": avg_response_time,
            "error_rate": error_rate,
            "cache_hit_rate": cache_hit_rate,
            "endpoint_count": len(self.endpoint_stats),
            "alert_count": len(self.alerts),
            "time_window": str(time_window) if time_window else "all"
        }

    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]

        return [
            {
                "alert_type": alert.alert_type,
                "message": alert.message,
                "severity": alert.severity,
                "timestamp": alert.timestamp.isoformat(),
                "endpoint": alert.endpoint,
                "threshold": alert.threshold,
                "current_value": alert.current_value
            }
            for alert in recent_alerts
        ]

    async def export_metrics(self, file_path: str) -> bool:
        """Export metrics to a JSON file."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "metrics_count": len(self.metrics),
                "alerts_count": len(self.alerts),
                "endpoint_stats": dict(self.endpoint_stats),
                "performance_summary": self.get_performance_summary(),
                "recent_alerts": self.get_recent_alerts()
            }

            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"API metrics exported to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export API metrics: {e}")
            return False


# Global API performance monitor instance
api_performance_monitor = APIPerformanceMonitor()


def monitor_api_performance(endpoint: Optional[str] = None):
    """Decorator to monitor API performance."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                response_time = time.time() - start_time

                # Extract endpoint from function name or use provided endpoint
                func_endpoint = endpoint or func.__name__

                # Extract user_id and guild_id from kwargs if available
                user_id = kwargs.get('user_id')
                guild_id = kwargs.get('guild_id')

                api_performance_monitor.record_api_call(
                    endpoint=func_endpoint,
                    method="POST",  # Default to POST for decorated functions
                    response_time=response_time,
                    status_code=200 if success else 500,
                    success=success,
                    error_message=error_message,
                    user_id=user_id,
                    guild_id=guild_id
                )

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                response_time = time.time() - start_time

                # Extract endpoint from function name or use provided endpoint
                func_endpoint = endpoint or func.__name__

                # Extract user_id and guild_id from kwargs if available
                user_id = kwargs.get('user_id')
                guild_id = kwargs.get('guild_id')

                api_performance_monitor.record_api_call(
                    endpoint=func_endpoint,
                    method="POST",  # Default to POST for decorated functions
                    response_time=response_time,
                    status_code=200 if success else 500,
                    success=success,
                    error_message=error_message,
                    user_id=user_id,
                    guild_id=guild_id
                )

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


async def get_api_performance_monitor() -> APIPerformanceMonitor:
    """Get the global API performance monitor instance."""
    return api_performance_monitor
