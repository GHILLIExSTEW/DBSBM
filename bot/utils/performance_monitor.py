"""
Performance monitoring utility for DBSBM.
Tracks metrics, response times, and system health.
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""

    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check result."""

    name: str
    status: str  # "healthy", "warning", "critical"
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Performance monitoring system."""

    def __init__(self, max_metrics: int = 1000, max_health_checks: int = 100):
        """
        Initialize the performance monitor.

        Args:
            max_metrics: Maximum number of metrics to store in memory
            max_health_checks: Maximum number of health checks to store
        """
        self.max_metrics = max_metrics
        self.max_health_checks = max_health_checks

        # Storage for metrics and health checks
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics))
        self.health_checks: List[HealthCheck] = []

        # Performance tracking
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.request_counts: Dict[str, int] = defaultdict(int)

        # System monitoring
        self.start_time = datetime.now()
        self.last_system_check = None
        self.system_metrics = {}

        # Callbacks for alerts
        self.alert_callbacks: List[Callable] = []

        logger.info("Performance monitor initialized")

    def add_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """
        Add a performance metric.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for the metric
        """
        metric = PerformanceMetric(
            name=name, value=value, timestamp=datetime.now(), tags=tags or {}
        )

        self.metrics[name].append(metric)
        logger.debug(f"Added metric: {name} = {value}")

    def record_response_time(self, operation: str, response_time: float):
        """
        Record response time for an operation.

        Args:
            operation: Operation name (e.g., "database_query", "api_call")
            response_time: Response time in seconds
        """
        self.response_times[operation].append(response_time)
        self.add_metric(
            f"{operation}_response_time", response_time, {"operation": operation}
        )

        # Check for slow operations
        if response_time > 5.0:  # 5 seconds threshold
            logger.warning(
                f"Slow operation detected: {operation} took {response_time:.2f}s"
            )

    def record_request(self, endpoint: str, success: bool = True):
        """
        Record a request to an endpoint.

        Args:
            endpoint: Endpoint name
            success: Whether the request was successful
        """
        self.request_counts[endpoint] += 1

        if not success:
            self.error_counts[endpoint] += 1

        self.add_metric(
            f"{endpoint}_requests", 1, {"endpoint": endpoint, "success": str(success)}
        )

    def add_health_check(
        self,
        name: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a health check result.

        Args:
            name: Health check name
            status: Status ("healthy", "warning", "critical")
            message: Status message
            details: Additional details
        """
        health_check = HealthCheck(
            name=name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            details=details or {},
        )

        self.health_checks.append(health_check)

        # Keep only the latest health checks
        if len(self.health_checks) > self.max_health_checks:
            self.health_checks.pop(0)

        # Log critical health checks
        if status == "critical":
            logger.error(f"Critical health check: {name} - {message}")
        elif status == "warning":
            logger.warning(f"Warning health check: {name} - {message}")
        else:
            logger.debug(f"Health check: {name} - {message}")

    async def check_system_health(self) -> Dict[str, Any]:
        """
        Check system health and return metrics.

        Returns:
            Dict containing system health information
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100

            # Network I/O
            network = psutil.net_io_counters()

            # Process info
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Store system metrics
            self.system_metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_mb": memory.available / 1024 / 1024,
                "disk_percent": disk_percent,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "process_memory_mb": process_memory,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            }

            # Add metrics
            for name, value in self.system_metrics.items():
                self.add_metric(f"system_{name}", value)

            # Health checks
            health_status = "healthy"
            health_message = "System is healthy"

            if cpu_percent > 90:
                health_status = "critical"
                health_message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > 80:
                health_status = "warning"
                health_message = f"Elevated CPU usage: {cpu_percent:.1f}%"

            if memory_percent > 95:
                health_status = "critical"
                health_message = f"Critical memory usage: {memory_percent:.1f}%"
            elif memory_percent > 85:
                health_status = "warning"
                health_message = f"High memory usage: {memory_percent:.1f}%"

            if disk_percent > 95:
                health_status = "critical"
                health_message = f"Critical disk usage: {disk_percent:.1f}%"
            elif disk_percent > 85:
                health_status = "warning"
                health_message = f"High disk usage: {disk_percent:.1f}%"

            self.add_health_check(
                "system_health", health_status, health_message, self.system_metrics
            )

            self.last_system_check = datetime.now()

            return {
                "status": health_status,
                "message": health_message,
                "metrics": self.system_metrics,
            }

        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            self.add_health_check(
                "system_health", "critical", f"Health check failed: {e}"
            )
            return {
                "status": "critical",
                "message": f"Health check failed: {e}",
                "metrics": {},
            }

    def get_metrics_summary(
        self, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of metrics for a time window.

        Args:
            time_window: Time window to consider (default: last hour)

        Returns:
            Dict containing metric summaries
        """
        if time_window is None:
            time_window = timedelta(hours=1)

        cutoff_time = datetime.now() - time_window
        summary = {}

        for metric_name, metrics in self.metrics.items():
            # Filter metrics within time window
            recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]

            if recent_metrics:
                values = [m.value for m in recent_metrics]
                summary[metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "latest": values[-1] if values else None,
                }

        return summary

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get a summary of health checks.

        Returns:
            Dict containing health check summary
        """
        if not self.health_checks:
            return {"status": "unknown", "checks": []}

        # Get latest health check for each type
        latest_checks = {}
        for check in self.health_checks:
            if (
                check.name not in latest_checks
                or check.timestamp > latest_checks[check.name].timestamp
            ):
                latest_checks[check.name] = check

        # Determine overall status
        status_counts = defaultdict(int)
        for check in latest_checks.values():
            status_counts[check.status] += 1

        overall_status = "healthy"
        if status_counts["critical"] > 0:
            overall_status = "critical"
        elif status_counts["warning"] > 0:
            overall_status = "warning"

        return {
            "status": overall_status,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status,
                    "message": check.message,
                    "timestamp": check.timestamp.isoformat(),
                    "details": check.details,
                }
                for check in latest_checks.values()
            ],
            "counts": dict(status_counts),
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive performance summary.

        Returns:
            Dict containing performance summary
        """
        # Response time statistics
        response_time_stats = {}
        for operation, times in self.response_times.items():
            if times:
                response_time_stats[operation] = {
                    "count": len(times),
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "latest": times[-1] if times else None,
                }

        # Request statistics
        request_stats = {}
        for endpoint, count in self.request_counts.items():
            error_count = self.error_counts.get(endpoint, 0)
            success_rate = ((count - error_count) / count * 100) if count > 0 else 100

            request_stats[endpoint] = {
                "total_requests": count,
                "error_count": error_count,
                "success_rate": success_rate,
            }

        return {
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "system_metrics": self.system_metrics,
            "response_times": response_time_stats,
            "request_stats": request_stats,
            "health_summary": self.get_health_summary(),
            "metrics_summary": self.get_metrics_summary(),
        }

    def add_alert_callback(self, callback: Callable):
        """
        Add a callback for alerts.

        Args:
            callback: Function to call when alerts are triggered
        """
        self.alert_callbacks.append(callback)

    async def trigger_alert(
        self, alert_type: str, message: str, severity: str = "warning"
    ):
        """
        Trigger an alert.

        Args:
            alert_type: Type of alert
            message: Alert message
            severity: Alert severity ("info", "warning", "critical")
        """
        alert = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        }

        logger.warning(f"Alert: {alert_type} - {message}")

        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def export_metrics(self, filepath: str):
        """
        Export metrics to a JSON file.

        Args:
            filepath: Path to export file
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "metrics": {
                    name: [
                        {
                            "value": m.value,
                            "timestamp": m.timestamp.isoformat(),
                            "tags": m.tags,
                        }
                        for m in metrics
                    ]
                    for name, metrics in self.metrics.items()
                },
                "health_checks": [
                    {
                        "name": check.name,
                        "status": check.status,
                        "message": check.message,
                        "timestamp": check.timestamp.isoformat(),
                        "details": check.details,
                    }
                    for check in self.health_checks
                ],
                "performance_summary": self.get_performance_summary(),
            }

            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Metrics exported to {filepath}")

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


# Decorator for monitoring function performance
def monitor_performance(operation_name: str):
    """
    Decorator to monitor function performance.

    Args:
        operation_name: Name of the operation being monitored
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                get_performance_monitor().record_response_time(
                    operation_name, time.time() - start_time
                )
                return result
            except Exception as e:
                get_performance_monitor().record_response_time(
                    operation_name, time.time() - start_time
                )
                raise

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                get_performance_monitor().record_response_time(
                    operation_name, time.time() - start_time
                )
                return result
            except Exception as e:
                get_performance_monitor().record_response_time(
                    operation_name, time.time() - start_time
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Background monitoring task
async def background_monitoring():
    """Background task for continuous monitoring."""
    monitor = get_performance_monitor()

    while True:
        try:
            await asyncio.sleep(60)  # Check every minute

            # Check system health
            health_result = await monitor.check_system_health()

            # Trigger alerts for critical issues
            if health_result["status"] == "critical":
                await monitor.trigger_alert(
                    "system_health", health_result["message"], "critical"
                )
            elif health_result["status"] == "warning":
                await monitor.trigger_alert(
                    "system_health", health_result["message"], "warning"
                )

            # Log performance summary periodically
            summary = monitor.get_performance_summary()
            logger.debug(f"Performance summary: {summary['health_summary']['status']}")

        except Exception as e:
            logger.error(f"Error in background monitoring: {e}")


if __name__ == "__main__":
    # Test the performance monitor
    async def test_performance_monitor():
        monitor = PerformanceMonitor()

        # Add some test metrics
        monitor.add_metric("test_metric", 42.0, {"test": "true"})
        monitor.record_response_time("test_operation", 1.5)
        monitor.record_request("test_endpoint", True)

        # Check system health
        health = await monitor.check_system_health()
        print(f"System health: {health}")

        # Get summaries
        metrics_summary = monitor.get_metrics_summary()
        health_summary = monitor.get_health_summary()
        performance_summary = monitor.get_performance_summary()

        print(f"Metrics summary: {metrics_summary}")
        print(f"Health summary: {health_summary}")
        print(f"Performance summary: {performance_summary}")

    asyncio.run(test_performance_monitor())
