"""
Tests for the performance monitoring utility.
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from utils.performance_monitor import (
    HealthCheck,
    PerformanceMetric,
    PerformanceMonitor,
    _global_monitor,
    get_performance_monitor,
    monitor_performance,
)


class TestPerformanceMetric:
    """Test cases for PerformanceMetric."""

    def test_performance_metric_creation(self):
        """Test creating a performance metric."""
        metric = PerformanceMetric(
            name="test_metric",
            value=42.0,
            timestamp=datetime.now(),
            tags={"test": "true"},
        )

        assert metric.name == "test_metric"
        assert metric.value == 42.0
        assert isinstance(metric.timestamp, datetime)
        assert metric.tags == {"test": "true"}


class TestHealthCheck:
    """Test cases for HealthCheck."""

    def test_health_check_creation(self):
        """Test creating a health check."""
        check = HealthCheck(
            name="test_check",
            status="healthy",
            message="Test message",
            timestamp=datetime.now(),
            details={"test": "true"},
        )

        assert check.name == "test_check"
        assert check.status == "healthy"
        assert check.message == "Test message"
        assert isinstance(check.timestamp, datetime)
        assert check.details == {"test": "true"}


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor."""

    @pytest.fixture
    def monitor(self):
        """Create a performance monitor instance for testing."""
        # Reset global monitor to ensure clean state
        global _global_monitor
        _global_monitor = None
        return PerformanceMonitor(max_metrics=10, max_health_checks=5)

    def test_add_metric(self, monitor):
        """Test adding a metric."""
        monitor.add_metric("test_metric", 42.0, {"test": "true"})

        assert "test_metric" in monitor.metrics
        assert len(monitor.metrics["test_metric"]) == 1

        metric = monitor.metrics["test_metric"][0]
        assert metric.name == "test_metric"
        assert metric.value == 42.0
        assert metric.tags == {"test": "true"}

    def test_add_metric_without_tags(self, monitor):
        """Test adding a metric without tags."""
        monitor.add_metric("test_metric", 42.0)

        metric = monitor.metrics["test_metric"][0]
        assert metric.tags == {}

    def test_record_response_time(self, monitor):
        """Test recording response time."""
        monitor.record_response_time("test_operation", 1.5)

        assert "test_operation" in monitor.response_times
        assert len(monitor.response_times["test_operation"]) == 1
        assert monitor.response_times["test_operation"][0] == 1.5

        # Check that metric was also added
        assert "test_operation_response_time" in monitor.metrics

    def test_record_response_time_slow_operation(self, monitor, caplog):
        """Test recording slow response time."""
        with caplog.at_level("WARNING"):
            monitor.record_response_time("slow_operation", 6.0)
        assert any("slow_operation" in message and "Slow operation detected" in message for message in caplog.text.splitlines())

    def test_record_request_success(self, monitor):
        """Test recording successful request."""
        monitor.record_request("test_endpoint", True)

        assert monitor.request_counts["test_endpoint"] == 1
        assert monitor.error_counts["test_endpoint"] == 0

        # Check that metric was added
        assert "test_endpoint_requests" in monitor.metrics

    def test_record_request_failure(self, monitor):
        """Test recording failed request."""
        monitor.record_request("test_endpoint", False)

        assert monitor.request_counts["test_endpoint"] == 1
        assert monitor.error_counts["test_endpoint"] == 1

    def test_add_health_check(self, monitor):
        """Test adding a health check."""
        monitor.add_health_check("test_check", "healthy", "Test message")

        assert len(monitor.health_checks) == 1
        check = monitor.health_checks[0]
        assert check.name == "test_check"
        assert check.status == "healthy"
        assert check.message == "Test message"

    def test_add_health_check_critical(self, monitor, caplog):
        """Test adding critical health check."""
        with caplog.at_level("ERROR"):
            monitor.add_health_check("critical_check", "critical", "Critical message")
        assert any("critical_check" in message and "Critical health check" in message for message in caplog.text.splitlines())

    def test_add_health_check_warning(self, monitor, caplog):
        """Test adding warning health check."""
        with caplog.at_level("WARNING"):
            monitor.add_health_check("warning_check", "warning", "Warning message")
        assert any("warning_check" in message and "Warning health check" in message for message in caplog.text.splitlines())

    def test_health_check_limit(self, monitor):
        """Test that health checks respect the limit."""
        # Add more health checks than the limit
        for i in range(10):
            monitor.add_health_check(f"check_{i}", "healthy", f"Message {i}")

        # Should only keep the latest ones
        assert len(monitor.health_checks) == 5  # max_health_checks

    @pytest.mark.asyncio
    async def test_check_system_health(self, monitor):
        """Test system health check."""
        with patch("psutil.cpu_percent", return_value=50.0), patch(
            "psutil.virtual_memory"
        ) as mock_memory, patch("psutil.disk_usage") as mock_disk, patch(
            "psutil.net_io_counters"
        ) as mock_network, patch(
            "psutil.Process"
        ) as mock_process:

            # Mock memory
            mock_memory.return_value.percent = 60.0
            mock_memory.return_value.available = 1024 * 1024 * 1024  # 1GB

            # Mock disk
            mock_disk.return_value.used = 50 * 1024 * 1024 * 1024  # 50GB
            mock_disk.return_value.total = 100 * 1024 * 1024 * 1024  # 100GB
            mock_disk.return_value.free = 50 * 1024 * 1024 * 1024  # 50GB

            # Mock network
            mock_network.return_value.bytes_sent = 1000
            mock_network.return_value.bytes_recv = 2000

            # Mock process
            mock_process_instance = Mock()
            mock_process_instance.memory_info.return_value.rss = (
                1024 * 1024 * 100
            )  # 100MB
            mock_process.return_value = mock_process_instance

            result = await monitor.check_system_health()

            assert result["status"] == "healthy"
            assert "metrics" in result
            assert "cpu_percent" in result["metrics"]
            assert "memory_percent" in result["metrics"]

    @pytest.mark.asyncio
    async def test_check_system_health_critical_cpu(self, monitor):
        """Test system health check with critical CPU usage."""
        with patch("psutil.cpu_percent", return_value=95.0), patch(
            "psutil.virtual_memory"
        ) as mock_memory, patch("psutil.disk_usage") as mock_disk, patch(
            "psutil.net_io_counters"
        ) as mock_network, patch(
            "psutil.Process"
        ) as mock_process:

            # Mock other metrics as normal
            mock_memory.return_value.percent = 50.0
            mock_memory.return_value.available = 1024 * 1024 * 1024
            mock_disk.return_value.used = 50 * 1024 * 1024 * 1024
            mock_disk.return_value.total = 100 * 1024 * 1024 * 1024
            mock_disk.return_value.free = 50 * 1024 * 1024 * 1024
            mock_network.return_value.bytes_sent = 1000
            mock_network.return_value.bytes_recv = 2000
            mock_process_instance = Mock()
            mock_process_instance.memory_info.return_value.rss = 1024 * 1024 * 100
            mock_process.return_value = mock_process_instance

            result = await monitor.check_system_health()

            assert result["status"] == "critical"
            assert "High CPU usage" in result["message"]

    def test_get_metrics_summary(self, monitor):
        """Test getting metrics summary."""
        # Add some metrics
        monitor.add_metric("test_metric", 10.0)
        monitor.add_metric("test_metric", 20.0)
        monitor.add_metric("test_metric", 30.0)

        summary = monitor.get_metrics_summary()

        assert "test_metric" in summary
        assert summary["test_metric"]["count"] == 3
        assert summary["test_metric"]["min"] == 10.0
        assert summary["test_metric"]["max"] == 30.0
        assert summary["test_metric"]["avg"] == 20.0
        assert summary["test_metric"]["latest"] == 30.0

    def test_get_metrics_summary_time_window(self, monitor):
        """Test getting metrics summary with time window."""
        # Add old metric
        old_time = datetime.now() - timedelta(hours=2)
        old_metric = PerformanceMetric("test_metric", 10.0, old_time)
        monitor.metrics["test_metric"].append(old_metric)

        # Add recent metric
        monitor.add_metric("test_metric", 20.0)

        # Get summary for last hour
        summary = monitor.get_metrics_summary(timedelta(hours=1))

        assert "test_metric" in summary
        assert summary["test_metric"]["count"] == 1  # Only recent metric
        assert summary["test_metric"]["latest"] == 20.0

    def test_get_health_summary(self):
        """Test getting health summary."""
        # Create a completely fresh monitor for this test (no fixture)
        fresh_monitor = PerformanceMonitor(max_metrics=10, max_health_checks=5)

        # Add some health checks with small delays to ensure different timestamps
        fresh_monitor.add_health_check("check1", "healthy", "OK")
        import time

        time.sleep(0.001)  # Small delay to ensure different timestamps
        fresh_monitor.add_health_check("check2", "warning", "Warning")
        time.sleep(0.001)  # Small delay to ensure different timestamps
        fresh_monitor.add_health_check(
            "check1", "critical", "Critical"
        )  # Override check1

        summary = fresh_monitor.get_health_summary()

        assert summary["status"] == "critical"  # Most severe status
        assert len(summary["checks"]) == 2  # Only latest for each check
        assert summary["counts"]["critical"] == 1
        assert summary["counts"]["warning"] == 1

    def test_get_performance_summary(self, monitor):
        """Test getting performance summary."""
        # Add some data
        monitor.add_metric("test_metric", 42.0)
        monitor.record_response_time("test_op", 1.5)
        monitor.record_request("test_endpoint", True)
        monitor.record_request("test_endpoint", False)
        monitor.add_health_check("test_check", "healthy", "OK")

        summary = monitor.get_performance_summary()

        assert "uptime_seconds" in summary
        assert "system_metrics" in summary
        assert "response_times" in summary
        assert "request_stats" in summary
        assert "health_summary" in summary
        assert "metrics_summary" in summary

        # Check request stats
        assert summary["request_stats"]["test_endpoint"]["total_requests"] == 2
        assert summary["request_stats"]["test_endpoint"]["error_count"] == 1
        assert summary["request_stats"]["test_endpoint"]["success_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_trigger_alert(self, monitor):
        """Test triggering an alert."""
        alert_callback = Mock()
        monitor.add_alert_callback(alert_callback)

        await monitor.trigger_alert("test_alert", "Test message", "critical")

        alert_callback.assert_called_once()
        alert = alert_callback.call_args[0][0]
        assert alert["type"] == "test_alert"
        assert alert["message"] == "Test message"
        assert alert["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_trigger_alert_async_callback(self, monitor):
        """Test triggering an alert with async callback."""

        async def async_callback(alert):
            return "processed"

        monitor.add_alert_callback(async_callback)

        await monitor.trigger_alert("test_alert", "Test message")

        # Should not raise any exceptions

    @pytest.mark.asyncio
    async def test_trigger_alert_callback_error(self, monitor):
        """Test alert callback error handling."""

        def error_callback(alert):
            raise Exception("Callback error")

        monitor.add_alert_callback(error_callback)

        # Should not raise exception
        await monitor.trigger_alert("test_alert", "Test message")

    def test_export_metrics(self, monitor, tmp_path):
        """Test exporting metrics to file."""
        # Add some data
        monitor.add_metric("test_metric", 42.0, {"test": "true"})
        monitor.add_health_check("test_check", "healthy", "OK")

        # Export to temporary file
        export_file = tmp_path / "metrics.json"
        monitor.export_metrics(str(export_file))

        # Check file exists and contains data
        assert export_file.exists()

        import json

        with open(export_file, "r") as f:
            data = json.load(f)

        assert "export_timestamp" in data
        assert "metrics" in data
        assert "health_checks" in data
        assert "performance_summary" in data
        assert "test_metric" in data["metrics"]


class TestGlobalPerformanceMonitor:
    """Test cases for global performance monitor functions."""

    def test_get_performance_monitor_singleton(self):
        """Test that get_performance_monitor returns a singleton."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        assert monitor1 is monitor2


class TestMonitorPerformanceDecorator:
    """Test cases for the monitor_performance decorator."""

    @pytest.fixture
    def monitor(self):
        """Create a performance monitor instance for testing."""
        # Reset global monitor to ensure clean state
        global _global_monitor
        _global_monitor = None
        return PerformanceMonitor(max_metrics=10, max_health_checks=5)

    @pytest.mark.asyncio
    async def test_monitor_performance_async(self, monitor):
        """Test monitoring async function performance."""

        async def test_func():
            await asyncio.sleep(0.1)
            return "success"

        # Pass the monitor instance directly to the decorator
        decorated_func = monitor_performance("test_operation", monitor_instance=monitor)(test_func)
        result = await decorated_func()
        assert result == "success"
        assert "test_operation" in monitor.response_times
        assert len(monitor.response_times["test_operation"]) == 1

    def test_monitor_performance_sync(self, monitor):
        """Test monitoring sync function performance."""

        def test_func():
            time.sleep(0.1)
            return "success"

        # Pass the monitor instance directly to the decorator
        decorated_func = monitor_performance("test_operation", monitor_instance=monitor)(test_func)
        result = decorated_func()
        assert result == "success"
        assert "test_operation" in monitor.response_times
        assert len(monitor.response_times["test_operation"]) == 1

    @pytest.mark.asyncio
    async def test_monitor_performance_exception(self, monitor):
        """Test monitoring function that raises exception."""

        async def test_func():
            await asyncio.sleep(0.1)
            raise ValueError("Test error")

        # Pass the monitor instance directly to the decorator
        decorated_func = monitor_performance("test_operation", monitor_instance=monitor)(test_func)

        with pytest.raises(ValueError):
            await decorated_func()

        # Check that performance was still recorded
        assert "test_operation" in monitor.response_times
        assert len(monitor.response_times["test_operation"]) == 1


if __name__ == "__main__":
    pytest.main([__file__])
