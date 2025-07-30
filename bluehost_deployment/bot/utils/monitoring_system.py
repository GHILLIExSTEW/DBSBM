"""
Comprehensive monitoring and metrics system for DBSBM.

This module provides monitoring capabilities including metrics collection,
alerting, performance tracking, and business intelligence.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json


logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """A single metric measurement."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Alert:
    """An alert condition."""
    name: str
    condition: str
    threshold: float
    severity: str  # 'info', 'warning', 'critical'
    enabled: bool = True
    cooldown: int = 300  # seconds


class MetricsCollector:
    """Collects and stores metrics."""

    def __init__(self, max_metrics: int = 10000):
        self.metrics = deque(maxlen=max_metrics)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Record a metric."""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            metadata=metadata
        )
        self.metrics.append(metric)

        # Update counters and gauges
        if name.startswith('counter.'):
            self.counters[name] += int(value)
        elif name.startswith('gauge.'):
            self.gauges[name] = value
        elif name.startswith('histogram.'):
            self.histograms[name].append(value)

    def get_metric_summary(self, name: str, window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        cutoff = datetime.utcnow() - window
        relevant_metrics = [
            m for m in self.metrics
            if m.name == name and m.timestamp >= cutoff
        ]

        if not relevant_metrics:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0}

        values = [m.value for m in relevant_metrics]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values)
        }

    def get_all_metrics(self, window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get all metrics within a time window."""
        cutoff = datetime.utcnow() - window
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff]

        # Group by metric name
        grouped = defaultdict(list)
        for metric in recent_metrics:
            grouped[metric.name].append(metric)

        # Calculate summaries
        summaries = {}
        for name, metrics in grouped.items():
            values = [m.value for m in metrics]
            summaries[name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values),
                "latest": values[-1] if values else 0
            }

        return dict(summaries)


class AlertManager:
    """Manages alert conditions and notifications."""

    def __init__(self):
        self.alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.last_triggered = {}

    def add_alert(self, alert: Alert):
        """Add an alert condition."""
        self.alerts[alert.name] = alert

    def check_alerts(self, metrics_collector: MetricsCollector) -> List[Dict[str, Any]]:
        """Check all alert conditions against current metrics."""
        triggered_alerts = []

        for alert_name, alert in self.alerts.items():
            if not alert.enabled:
                continue

            # Check cooldown
            last_triggered = self.last_triggered.get(alert_name)
            if last_triggered and time.time() - last_triggered < alert.cooldown:
                continue

            # Get current metric value
            metric_summary = metrics_collector.get_metric_summary(
                alert.condition.split('.')[1])
            current_value = metric_summary.get('latest', 0)

            # Check threshold
            if self._evaluate_condition(current_value, alert.condition, alert.threshold):
                self.last_triggered[alert_name] = time.time()

                triggered_alert = {
                    "name": alert_name,
                    "severity": alert.severity,
                    "condition": alert.condition,
                    "threshold": alert.threshold,
                    "current_value": current_value,
                    "timestamp": datetime.utcnow().isoformat()
                }

                triggered_alerts.append(triggered_alert)
                self.alert_history.append(triggered_alert)

                # Log alert
                logger.warning(
                    f"Alert triggered: {alert_name} - {alert.condition} = {current_value} (threshold: {alert.threshold})")

        return triggered_alerts

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate an alert condition."""
        if '>' in condition:
            return value > threshold
        elif '<' in condition:
            return value < threshold
        elif '>=' in condition:
            return value >= threshold
        elif '<=' in condition:
            return value <= threshold
        elif '==' in condition:
            return value == threshold
        else:
            return False


class PerformanceMonitor:
    """Monitors system performance metrics."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.start_time = time.time()

    def record_api_call(self, endpoint: str, response_time: float, status_code: int, success: bool):
        """Record an API call metric."""
        tags = {
            "endpoint": endpoint,
            "status_code": str(status_code),
            "success": str(success)
        }

        self.metrics_collector.record_metric(
            "api.response_time", response_time, tags)
        self.metrics_collector.record_metric("api.calls", 1, tags)

        if not success:
            self.metrics_collector.record_metric("api.errors", 1, tags)

    def record_database_query(self, query_type: str, response_time: float, success: bool):
        """Record a database query metric."""
        tags = {
            "query_type": query_type,
            "success": str(success)
        }

        self.metrics_collector.record_metric(
            "db.query_time", response_time, tags)
        self.metrics_collector.record_metric("db.queries", 1, tags)

        if not success:
            self.metrics_collector.record_metric("db.errors", 1, tags)

    def record_cache_operation(self, operation: str, response_time: float, success: bool):
        """Record a cache operation metric."""
        tags = {
            "operation": operation,
            "success": str(success)
        }

        self.metrics_collector.record_metric(
            "cache.operation_time", response_time, tags)
        self.metrics_collector.record_metric("cache.operations", 1, tags)

        if not success:
            self.metrics_collector.record_metric("cache.errors", 1, tags)

    def record_business_metric(self, metric_name: str, value: float, category: str = "general"):
        """Record a business metric."""
        tags = {"category": category}
        self.metrics_collector.record_metric(
            f"business.{metric_name}", value, tags)

    def record_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """Record an error metric."""
        tags = {
            "error_type": error_type,
            "context": json.dumps(context) if context else "none"
        }

        self.metrics_collector.record_metric("errors.count", 1, tags)
        self.metrics_collector.record_metric(
            "errors.types", 1, {"error_type": error_type})


class BusinessIntelligence:
    """Business intelligence and analytics."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    def get_user_activity_summary(self, window: timedelta = timedelta(days=1)) -> Dict[str, Any]:
        """Get user activity summary."""
        metrics = self.metrics_collector.get_all_metrics(window)

        return {
            "total_users": metrics.get("business.active_users", {}).get("latest", 0),
            "new_users": metrics.get("business.new_users", {}).get("sum", 0),
            "active_guilds": metrics.get("business.active_guilds", {}).get("latest", 0),
            "total_bets": metrics.get("business.total_bets", {}).get("sum", 0),
            "total_volume": metrics.get("business.bet_volume", {}).get("sum", 0),
            "win_rate": metrics.get("business.win_rate", {}).get("latest", 0)
        }

    def get_performance_summary(self, window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get system performance summary."""
        metrics = self.metrics_collector.get_all_metrics(window)

        return {
            "api_response_time_avg": metrics.get("api.response_time", {}).get("avg", 0),
            "api_error_rate": self._calculate_error_rate("api.calls", "api.errors", metrics),
            "db_query_time_avg": metrics.get("db.query_time", {}).get("avg", 0),
            "db_error_rate": self._calculate_error_rate("db.queries", "db.errors", metrics),
            "cache_hit_rate": metrics.get("cache.hit_rate", {}).get("latest", 0),
            "error_rate": metrics.get("errors.count", {}).get("sum", 0)
        }

    def _calculate_error_rate(self, total_metric: str, error_metric: str, metrics: Dict[str, Any]) -> float:
        """Calculate error rate from metrics."""
        total = metrics.get(total_metric, {}).get("sum", 0)
        errors = metrics.get(error_metric, {}).get("sum", 0)

        if total == 0:
            return 0.0

        return (errors / total) * 100


class MonitoringSystem:
    """Main monitoring system that coordinates all monitoring components."""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.performance_monitor = PerformanceMonitor(self.metrics_collector)
        self.business_intelligence = BusinessIntelligence(
            self.metrics_collector)

        # Set up default alerts
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Set up default alert conditions."""
        default_alerts = [
            Alert("high_error_rate", "errors.count", 10, "critical"),
            Alert("slow_api_response", "api.response_time",
                  2000, "warning"),  # 2 seconds
            Alert("slow_db_queries", "db.query_time",
                  1000, "warning"),  # 1 second
            Alert("low_cache_hit_rate", "cache.hit_rate", 80, "warning"),  # 80%
            Alert("high_memory_usage", "system.memory_usage", 90, "critical"),
            Alert("high_disk_usage", "system.disk_usage", 90, "critical")
        ]

        for alert in default_alerts:
            self.alert_manager.add_alert(alert)

    def record_system_metrics(self):
        """Record system-level metrics."""
        try:
            import psutil

            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics_collector.record_metric(
                "system.memory_usage", memory.percent)
            self.metrics_collector.record_metric(
                "system.memory_available", memory.available / (1024**3))

            # Disk metrics
            disk = psutil.disk_usage('/')
            self.metrics_collector.record_metric(
                "system.disk_usage", disk.percent)
            self.metrics_collector.record_metric(
                "system.disk_free", disk.free / (1024**3))

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.record_metric(
                "system.cpu_usage", cpu_percent)

            # Process metrics
            process = psutil.Process()
            self.metrics_collector.record_metric(
                "system.process_memory", process.memory_info().rss / (1024**2))
            self.metrics_collector.record_metric(
                "system.process_cpu", process.cpu_percent())

        except Exception as e:
            logger.error(f"Error recording system metrics: {e}")

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check all alert conditions."""
        return self.alert_manager.check_alerts(self.metrics_collector)

    def get_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report."""
        # Get performance summary
        performance = self.business_intelligence.get_performance_summary()

        # Get business metrics
        business = self.business_intelligence.get_user_activity_summary()

        # Check alerts
        active_alerts = self.check_alerts()

        # Get system metrics
        system_metrics = self.metrics_collector.get_all_metrics(
            timedelta(minutes=5))

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "performance": performance,
            "business": business,
            "alerts": active_alerts,
            "system_metrics": system_metrics,
            "overall_status": "healthy" if not active_alerts else "degraded"
        }

    async def start_monitoring_loop(self, interval: int = 60):
        """Start the monitoring loop."""
        logger.info("Starting monitoring loop...")

        while True:
            try:
                # Record system metrics
                self.record_system_metrics()

                # Check alerts
                alerts = self.check_alerts()
                if alerts:
                    logger.warning(f"Active alerts: {len(alerts)}")

                # Generate health report
                health_report = self.get_health_report()

                # Log summary
                logger.info(f"Monitoring summary: {health_report['overall_status']} - "
                            f"API avg: {health_report['performance']['api_response_time_avg']:.2f}ms, "
                            f"Errors: {health_report['performance']['error_rate']}")

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)


# Global monitoring system instance
monitoring_system = MonitoringSystem()


def get_monitoring_system() -> MonitoringSystem:
    """Get the global monitoring system instance."""
    return monitoring_system


def record_api_call(endpoint: str, response_time: float, status_code: int, success: bool):
    """Record an API call metric."""
    monitoring_system.performance_monitor.record_api_call(
        endpoint, response_time, status_code, success)


def record_database_query(query_type: str, response_time: float, success: bool):
    """Record a database query metric."""
    monitoring_system.performance_monitor.record_database_query(
        query_type, response_time, success)


def record_cache_operation(operation: str, response_time: float, success: bool):
    """Record a cache operation metric."""
    monitoring_system.performance_monitor.record_cache_operation(
        operation, response_time, success)


def record_business_metric(metric_name: str, value: float, category: str = "general"):
    """Record a business metric."""
    monitoring_system.performance_monitor.record_business_metric(
        metric_name, value, category)


def record_error(error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
    """Record an error metric."""
    monitoring_system.performance_monitor.record_error(
        error_type, error_message, context)
