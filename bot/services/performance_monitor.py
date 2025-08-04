"""Performance monitoring service for tracking system metrics."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque

from bot.data.cache_manager import cache_manager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Represents a single performance metric."""

    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryPerformance:
    """Represents database query performance data."""

    query: str
    execution_time: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    rows_affected: Optional[int] = None
    cache_hit: bool = False


@dataclass
class APIPerformance:
    """Represents API call performance data."""

    endpoint: str
    method: str
    response_time: float
    timestamp: datetime
    status_code: int
    success: bool
    cache_hit: bool = False
    error_message: Optional[str] = None


class PerformanceMonitor:
    """Monitors and tracks system performance metrics."""

    def __init__(self, max_history: int = 1000):
        """Initialize the performance monitor."""
        self.max_history = max_history
        self.metrics: deque = deque(maxlen=max_history)
        self.query_performance: deque = deque(maxlen=max_history)
        self.api_performance: deque = deque(maxlen=max_history)
        self.start_time = datetime.now()

        # Performance counters
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)

        # Alert thresholds
        self.thresholds = {
            "query_time_ms": 1000,  # 1 second
            "api_response_time_ms": 5000,  # 5 seconds
            "memory_usage_mb": 512,  # 512 MB
            "cache_hit_rate": 0.8,  # 80%
        }

        logger.info("Performance monitor initialized")

    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            metadata=metadata or {},
        )
        self.metrics.append(metric)
        self.counters[f"metric_{name}"] += 1

        # Check for threshold violations
        self._check_thresholds(metric)

    def record_query(
        self,
        query: str,
        execution_time: float,
        success: bool = True,
        error_message: Optional[str] = None,
        rows_affected: Optional[int] = None,
        cache_hit: bool = False,
    ) -> None:
        """Record database query performance."""
        query_perf = QueryPerformance(
            query=query,
            execution_time=execution_time,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message,
            rows_affected=rows_affected,
            cache_hit=cache_hit,
        )
        self.query_performance.append(query_perf)

        # Update counters
        self.counters["total_queries"] += 1
        if success:
            self.counters["successful_queries"] += 1
        else:
            self.counters["failed_queries"] += 1

        if cache_hit:
            self.counters["cache_hits"] += 1

        # Check for slow queries
        if execution_time > self.thresholds["query_time_ms"] / 1000:
            logger.warning(
                f"Slow query detected: {execution_time:.3f}s - {query[:100]}..."
            )

    def record_api_call(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        success: bool = True,
        error_message: Optional[str] = None,
        cache_hit: bool = False,
    ) -> None:
        """Record API call performance."""
        api_perf = APIPerformance(
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            timestamp=datetime.now(),
            status_code=status_code,
            success=success,
            cache_hit=cache_hit,
            error_message=error_message,
        )
        self.api_performance.append(api_perf)

        # Update counters
        self.counters["total_api_calls"] += 1
        if success:
            self.counters["successful_api_calls"] += 1
        else:
            self.counters["failed_api_calls"] += 1

        if cache_hit:
            self.counters["api_cache_hits"] += 1

        # Check for slow API calls
        if response_time > self.thresholds["api_response_time_ms"] / 1000:
            logger.warning(
                f"Slow API call detected: {response_time:.3f}s - {method} {endpoint}"
            )

    def time_operation(self, operation_name: str) -> Callable:
        """Decorator to time an operation."""

        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.record_metric(f"{operation_name}_time", execution_time)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_metric(
                        f"{operation_name}_time",
                        execution_time,
                        metadata={"error": str(e)},
                    )
                    raise

            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.record_metric(f"{operation_name}_time", execution_time)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_metric(
                        f"{operation_name}_time",
                        execution_time,
                        metadata={"error": str(e)},
                    )
                    raise

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def _check_thresholds(self, metric: PerformanceMetric) -> None:
        """Check if a metric violates any thresholds."""
        if (
            metric.name == "query_time"
            and metric.value > self.thresholds["query_time_ms"] / 1000
        ):
            logger.warning(f"Query time threshold exceeded: {metric.value:.3f}s")

        elif (
            metric.name == "api_response_time"
            and metric.value > self.thresholds["api_response_time_ms"] / 1000
        ):
            logger.warning(f"API response time threshold exceeded: {metric.value:.3f}s")

        elif (
            metric.name == "memory_usage"
            and metric.value > self.thresholds["memory_usage_mb"]
        ):
            logger.warning(f"Memory usage threshold exceeded: {metric.value:.1f}MB")

    def get_uptime(self) -> timedelta:
        """Get system uptime."""
        return datetime.now() - self.start_time

    def get_query_stats(
        self, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get database query statistics."""
        if not self.query_performance:
            return {"total_queries": 0, "avg_time": 0, "success_rate": 0}

        # Filter by time window if specified
        if time_window:
            cutoff = datetime.now() - time_window
            queries = [q for q in self.query_performance if q.timestamp >= cutoff]
        else:
            queries = list(self.query_performance)

        if not queries:
            return {"total_queries": 0, "avg_time": 0, "success_rate": 0}

        total_queries = len(queries)
        successful_queries = sum(1 for q in queries if q.success)
        avg_time = sum(q.execution_time for q in queries) / total_queries
        cache_hits = sum(1 for q in queries if q.cache_hit)

        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": total_queries - successful_queries,
            "success_rate": successful_queries / total_queries,
            "avg_time": avg_time,
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hits / total_queries if total_queries > 0 else 0,
            "slow_queries": sum(1 for q in queries if q.execution_time > 1.0),
        }

    def get_api_stats(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get API call statistics."""
        if not self.api_performance:
            return {"total_calls": 0, "avg_time": 0, "success_rate": 0}

        # Filter by time window if specified
        if time_window:
            cutoff = datetime.now() - time_window
            calls = [c for c in self.api_performance if c.timestamp >= cutoff]
        else:
            calls = list(self.api_performance)

        if not calls:
            return {"total_calls": 0, "avg_time": 0, "success_rate": 0}

        total_calls = len(calls)
        successful_calls = sum(1 for c in calls if c.success)
        avg_time = sum(c.response_time for c in calls) / total_calls
        cache_hits = sum(1 for c in calls if c.cache_hit)

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": total_calls - successful_calls,
            "success_rate": successful_calls / total_calls,
            "avg_time": avg_time,
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hits / total_calls if total_calls > 0 else 0,
            "slow_calls": sum(1 for c in calls if c.response_time > 5.0),
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        import psutil

        # Get system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage("/")

        # Get cache stats
        cache_stats = asyncio.run(cache_manager.get_stats())

        return {
            "uptime": str(self.get_uptime()),
            "memory_usage_mb": memory.used / (1024 * 1024),
            "memory_percent": memory.percent,
            "cpu_percent": cpu_percent,
            "disk_usage_percent": (disk.used / disk.total) * 100,
            "cache_stats": cache_stats,
            "total_metrics_recorded": len(self.metrics),
            "total_queries_recorded": len(self.query_performance),
            "total_api_calls_recorded": len(self.api_performance),
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        return {
            "system": self.get_system_stats(),
            "queries": self.get_query_stats(),
            "api_calls": self.get_api_stats(),
            "counters": dict(self.counters),
            "timestamp": datetime.now().isoformat(),
        }

    async def log_performance_report(self) -> None:
        """Log a performance report."""
        report = self.get_performance_report()

        logger.info("=== PERFORMANCE REPORT ===")
        logger.info(f"Uptime: {report['system']['uptime']}")
        logger.info(
            f"Memory Usage: {report['system']['memory_usage_mb']:.1f}MB ({report['system']['memory_percent']:.1f}%)"
        )
        logger.info(f"CPU Usage: {report['system']['cpu_percent']:.1f}%")

        query_stats = report["queries"]
        logger.info(
            f"Database Queries: {query_stats['total_queries']} total, "
            f"{query_stats['avg_time']:.3f}s avg, {query_stats['success_rate']:.1%} success rate"
        )

        api_stats = report["api_calls"]
        logger.info(
            f"API Calls: {api_stats['total_calls']} total, "
            f"{api_stats['avg_time']:.3f}s avg, {api_stats['success_rate']:.1%} success rate"
        )

        cache_stats = report["system"]["cache_stats"]
        if cache_stats.get("enabled"):
            logger.info(f"Cache Hit Rate: {cache_stats.get('hit_rate', 'N/A')}")

        logger.info("=== END REPORT ===")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Convenience functions
def record_metric(
    name: str, value: float, tags: Optional[Dict[str, str]] = None
) -> None:
    """Record a performance metric."""
    performance_monitor.record_metric(name, value, tags)


def record_query(
    query: str,
    execution_time: float,
    success: bool = True,
    error_message: Optional[str] = None,
    rows_affected: Optional[int] = None,
    cache_hit: bool = False,
) -> None:
    """Record database query performance."""
    performance_monitor.record_query(
        query,
        execution_time,
        success,
        error_message,
        rows_affected=rows_affected,
        cache_hit=cache_hit,
    )


def record_api_call(
    endpoint: str,
    method: str,
    response_time: float,
    status_code: int,
    success: bool = True,
    cache_hit: bool = False,
) -> None:
    """Record API call performance."""
    performance_monitor.record_api_call(
        endpoint, method, response_time, status_code, success, cache_hit=cache_hit
    )


def time_operation(operation_name: str):
    """Decorator to time an operation."""
    return performance_monitor.time_operation(operation_name)
