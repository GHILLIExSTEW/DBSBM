"""Metrics collection system for monitoring system performance."""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and stores system metrics."""

    def __init__(
        self, max_history: int = 1000, storage_path: str = "betting-bot/data/metrics"
    ):
        """
        Initialize the metrics collector.

        Args:
            max_history: Maximum number of data points to keep per metric
            storage_path: Path to store metrics data
        """
        self.max_history = max_history
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)

        # Collection intervals
        self.collection_task: Optional[asyncio.Task] = None
        self.running = False

        # Performance tracking
        self.request_times: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)

    async def start(self, interval: int = 60):
        """
        Start collecting metrics.

        Args:
            interval: Collection interval in seconds
        """
        if self.running:
            logger.warning("Metrics collector is already running")
            return

        self.running = True
        self.collection_task = asyncio.create_task(self._collect_loop(interval))
        logger.info(f"Started metrics collection with {interval}s interval")

    async def stop(self):
        """Stop collecting metrics."""
        if not self.running:
            return

        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

        # Save final metrics
        await self._save_metrics()
        logger.info("Stopped metrics collection")

    def record_counter(
        self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a counter metric.

        Args:
            name: Metric name
            value: Counter increment value
            labels: Optional labels
        """
        self.counters[name] += value
        self._record_metric(f"counter_{name}", value, labels or {})

    def record_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels
        """
        self.gauges[name] = value
        self._record_metric(f"gauge_{name}", value, labels or {})

    def record_request_time(self, endpoint: str, duration: float):
        """
        Record request duration.

        Args:
            endpoint: API endpoint
            duration: Request duration in seconds
        """
        self.request_times[endpoint].append(duration)
        # Keep only last 100 requests
        if len(self.request_times[endpoint]) > 100:
            self.request_times[endpoint] = self.request_times[endpoint][-100:]

        self._record_metric("request_duration", duration, {"endpoint": endpoint})

    def record_error(self, error_type: str, error_message: str = ""):
        """
        Record an error.

        Args:
            error_type: Type of error
            error_message: Error message
        """
        self.error_counts[error_type] += 1
        self._record_metric("error_count", 1, {"error_type": error_type})

    def _record_metric(self, name: str, value: float, labels: Dict[str, str]):
        """Record a metric data point."""
        metric_point = MetricPoint(timestamp=datetime.now(), value=value, labels=labels)
        self.metrics[name].append(metric_point)

    async def _collect_loop(self, interval: int):
        """Main collection loop."""
        while self.running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(interval)

    async def _collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_gauge("system_cpu_percent", cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.record_gauge("system_memory_percent", memory.percent)
            self.record_gauge(
                "system_memory_available_mb", memory.available / (1024 * 1024)
            )

            # Disk usage
            disk = psutil.disk_usage("/")
            self.record_gauge("system_disk_percent", disk.percent)
            self.record_gauge("system_disk_free_gb", disk.free / (1024 * 1024 * 1024))

            # Network I/O
            network = psutil.net_io_counters()
            self.record_gauge("system_network_bytes_sent", network.bytes_sent)
            self.record_gauge("system_network_bytes_recv", network.bytes_recv)

            # Process-specific metrics
            process = psutil.Process()
            self.record_gauge("process_cpu_percent", process.cpu_percent())
            self.record_gauge(
                "process_memory_mb", process.memory_info().rss / (1024 * 1024)
            )
            self.record_gauge("process_threads", process.num_threads())

            # Database connection metrics (if available)
            await self._collect_database_metrics()

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _collect_database_metrics(self):
        """Collect database-specific metrics."""
        try:
            # This would integrate with your database manager
            # For now, we'll add placeholder metrics
            self.record_gauge("database_connections", 0)  # Placeholder
            self.record_gauge("database_query_time_avg", 0.0)  # Placeholder
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "system": {},
            "application": {},
            "performance": {},
            "errors": {},
        }

        # System metrics
        if "gauge_system_cpu_percent" in self.metrics:
            cpu_values = [p.value for p in self.metrics["gauge_system_cpu_percent"]]
            summary["system"]["cpu_percent"] = {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
            }

        if "gauge_system_memory_percent" in self.metrics:
            memory_values = [
                p.value for p in self.metrics["gauge_system_memory_percent"]
            ]
            summary["system"]["memory_percent"] = {
                "current": memory_values[-1] if memory_values else 0,
                "average": (
                    sum(memory_values) / len(memory_values) if memory_values else 0
                ),
            }

        # Application metrics
        summary["application"]["counters"] = dict(self.counters)
        summary["application"]["gauges"] = dict(self.gauges)

        # Performance metrics
        for endpoint, times in self.request_times.items():
            if times:
                summary["performance"][endpoint] = {
                    "avg_response_time": sum(times) / len(times),
                    "max_response_time": max(times),
                    "min_response_time": min(times),
                    "request_count": len(times),
                }

        # Error metrics
        summary["errors"] = dict(self.error_counts)

        return summary

    async def get_metric_history(
        self, metric_name: str, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get historical data for a specific metric.

        Args:
            metric_name: Name of the metric
            hours: Number of hours of history to retrieve

        Returns:
            List of metric data points
        """
        if metric_name not in self.metrics:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = []

        for point in self.metrics[metric_name]:
            if point.timestamp >= cutoff_time:
                history.append(
                    {
                        "timestamp": point.timestamp.isoformat(),
                        "value": point.value,
                        "labels": point.labels,
                    }
                )

        return history

    async def _save_metrics(self):
        """Save metrics to disk."""
        try:
            summary = await self.get_metrics_summary()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save summary
            summary_file = self.storage_path / f"metrics_summary_{timestamp}.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)

            # Save detailed history
            history_file = self.storage_path / f"metrics_history_{timestamp}.json"
            history_data = {}
            for metric_name in self.metrics:
                history_data[metric_name] = await self.get_metric_history(
                    metric_name, 24
                )

            with open(history_file, "w") as f:
                json.dump(history_data, f, indent=2)

            logger.info(f"Saved metrics to {summary_file} and {history_file}")

        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    async def cleanup_old_files(self, days: int = 7):
        """Clean up old metrics files."""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            deleted_count = 0

            for file_path in self.storage_path.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old metrics files")

        except Exception as e:
            logger.error(f"Error cleaning up old metrics files: {e}")


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Decorator for automatic metrics collection
def track_metrics(metric_name: str, metric_type: str = "counter"):
    """
    Decorator to automatically track function metrics.

    Args:
        metric_name: Name of the metric
        metric_type: Type of metric (counter or gauge)
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                if metric_type == "counter":
                    metrics_collector.record_counter(metric_name)
                else:
                    metrics_collector.record_gauge(metric_name, duration)

                metrics_collector.record_request_time(func.__name__, duration)
                return result

            except Exception as e:
                metrics_collector.record_error(f"{func.__name__}_error", str(e))
                raise

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if metric_type == "counter":
                    metrics_collector.record_counter(metric_name)
                else:
                    metrics_collector.record_gauge(metric_name, duration)

                metrics_collector.record_request_time(func.__name__, duration)
                return result

            except Exception as e:
                metrics_collector.record_error(f"{func.__name__}_error", str(e))
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
