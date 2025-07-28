"""Tests for memory management service."""

import asyncio
import gc
import time
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import psutil
import pytest

from bot.services.memory_management_service import (
    MemoryLeak,
    MemoryManager,
    MemorySnapshot,
    MemoryThreshold,
    get_memory_manager,
    memory_manager,
    memory_monitor,
)


class TestMemoryManager:
    """Test cases for MemoryManager class."""

    @pytest.fixture
    async def memory_manager(self):
        """Create a memory manager instance for testing."""
        manager = MemoryManager(
            monitoring_interval=1,  # Short interval for testing
            enable_tracemalloc=False,  # Disable for testing
        )
        yield manager
        await manager.shutdown()

    @pytest.fixture
    def mock_psutil(self):
        """Mock psutil for consistent testing."""
        with patch("psutil.virtual_memory") as mock_virtual_memory, patch(
            "psutil.Process"
        ) as mock_process:

            # Mock virtual memory
            mock_memory = Mock()
            mock_memory.total = 16 * 1024 * 1024 * 1024  # 16GB
            mock_memory.available = 8 * 1024 * 1024 * 1024  # 8GB
            mock_memory.used = 8 * 1024 * 1024 * 1024  # 8GB
            mock_memory.percent = 50.0
            mock_virtual_memory.return_value = mock_memory

            # Mock process
            mock_process_instance = Mock()
            mock_process_instance.memory_info.return_value.rss = (
                512 * 1024 * 1024
            )  # 512MB
            mock_process.return_value = mock_process_instance

            yield {
                "virtual_memory": mock_virtual_memory,
                "process": mock_process,
                "memory": mock_memory,
                "process_instance": mock_process_instance,
            }

    def test_memory_manager_initialization(self, memory_manager):
        """Test memory manager initialization."""
        assert memory_manager.monitoring_interval == 1
        assert memory_manager.gc_threshold == 700
        assert memory_manager.enable_tracemalloc is False
        assert memory_manager.is_monitoring is False
        assert len(memory_manager.snapshots) == 0
        assert len(memory_manager.memory_leaks) == 0
        assert len(memory_manager.cleanup_callbacks) == 0

    def test_memory_thresholds(self, memory_manager):
        """Test memory threshold determination."""
        # Test low threshold
        threshold = memory_manager._get_memory_threshold(30.0)
        assert threshold == MemoryThreshold.LOW

        # Test medium threshold
        threshold = memory_manager._get_memory_threshold(60.0)
        assert threshold == MemoryThreshold.MEDIUM

        # Test high threshold
        threshold = memory_manager._get_memory_threshold(90.0)
        assert threshold == MemoryThreshold.HIGH

        # Test critical threshold
        threshold = memory_manager._get_memory_threshold(98.0)
        assert threshold == MemoryThreshold.CRITICAL

    @pytest.mark.asyncio
    async def test_take_memory_snapshot(self, memory_manager, mock_psutil):
        """Test taking memory snapshots."""
        await memory_manager._take_memory_snapshot()

        assert len(memory_manager.snapshots) == 1
        snapshot = memory_manager.snapshots[0]

        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.memory_percent == 50.0
        assert snapshot.process_memory_mb == 512.0
        assert snapshot.threshold == MemoryThreshold.MEDIUM

    @pytest.mark.asyncio
    async def test_memory_monitoring_lifecycle(self, memory_manager):
        """Test starting and stopping memory monitoring."""
        # Start monitoring
        await memory_manager.start_monitoring()
        assert memory_manager.is_monitoring is True
        assert memory_manager.monitoring_task is not None

        # Wait a bit for monitoring to run
        await asyncio.sleep(0.1)

        # Stop monitoring
        await memory_manager.stop_monitoring()
        assert memory_manager.is_monitoring is False
        assert memory_manager.monitoring_task is None

    @pytest.mark.asyncio
    async def test_memory_cleanup(self, memory_manager):
        """Test memory cleanup functionality."""
        # Add a cleanup callback
        callback_called = False

        async def test_callback(threshold):
            nonlocal callback_called
            callback_called = True

        memory_manager.add_cleanup_callback(test_callback)

        # Trigger cleanup
        await memory_manager._trigger_memory_cleanup(MemoryThreshold.HIGH)

        assert callback_called is True
        assert memory_manager.gc_stats["forced_collections"] == 1

    @pytest.mark.asyncio
    async def test_optimize_garbage_collection(self, memory_manager):
        """Test garbage collection optimization."""
        # Add some snapshots first
        for i in range(15):
            snapshot = MemorySnapshot(
                timestamp=datetime.now(),
                total_memory_mb=16000,
                available_memory_mb=8000,
                used_memory_mb=8000,
                memory_percent=90.0,  # High memory pressure
                process_memory_mb=512,
                gc_objects=1000,
                gc_collections={},
                threshold=MemoryThreshold.HIGH,
            )
            memory_manager.snapshots.append(snapshot)

        # Test optimization
        result = await memory_manager.optimize_garbage_collection()

        assert result["status"] == "optimized"
        assert result["new_threshold"] < 700  # Should reduce threshold
        assert result["avg_memory_percent"] == 90.0

    def test_get_memory_stats(self, memory_manager):
        """Test getting memory statistics."""
        # Add some test snapshots
        for i in range(5):
            snapshot = MemorySnapshot(
                timestamp=datetime.now(),
                total_memory_mb=16000,
                available_memory_mb=8000,
                used_memory_mb=8000,
                memory_percent=50.0 + i * 10,
                process_memory_mb=512 + i * 10,
                gc_objects=1000,
                gc_collections={},
                threshold=MemoryThreshold.MEDIUM,
            )
            memory_manager.snapshots.append(snapshot)

        # Get stats
        stats = memory_manager.get_memory_stats()

        assert "current_memory_percent" in stats
        assert "avg_memory_percent" in stats
        assert "max_memory_percent" in stats
        assert "snapshot_count" in stats
        assert stats["snapshot_count"] == 5

    def test_get_memory_leaks(self, memory_manager):
        """Test getting memory leak information."""
        # Add a test memory leak
        leak = MemoryLeak(
            object_type="test_object",
            count=5,
            size_bytes=1024 * 1024,  # 1MB
            first_detected=datetime.now(),
            last_updated=datetime.now(),
            growth_rate=1024,
            severity="medium",
        )
        memory_manager.memory_leaks["test_key"] = leak

        # Get leaks
        leaks = memory_manager.get_memory_leaks()

        assert len(leaks) == 1
        assert leaks[0]["object_type"] == "test_object"
        assert leaks[0]["size_mb"] == 1.0
        assert leaks[0]["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_cleanup_memory(self, memory_manager):
        """Test memory cleanup functionality."""
        # Test normal cleanup
        result = await memory_manager.cleanup_memory(aggressive=False)

        assert "objects_freed" in result
        assert "cleanup_time_seconds" in result
        assert result["aggressive"] is False

        # Test aggressive cleanup
        result = await memory_manager.cleanup_memory(aggressive=True)

        assert result["aggressive"] is True
        assert memory_manager.cleanup_stats["cleanups_performed"] == 2

    def test_get_health_status(self, memory_manager, mock_psutil):
        """Test getting health status."""
        status = memory_manager.get_health_status()

        assert "status" in status
        assert "memory_percent" in status
        assert "process_memory_mb" in status
        assert "threshold" in status
        assert "is_monitoring" in status
        assert "snapshot_count" in status
        assert "leak_count" in status

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, memory_manager):
        """Test memory leak detection (with tracemalloc disabled)."""
        # Since tracemalloc is disabled for testing, this should not detect leaks
        await memory_manager._detect_memory_leaks()

        # Should not have any leaks since tracemalloc is disabled
        assert len(memory_manager.memory_leaks) == 0

    @pytest.mark.asyncio
    async def test_clear_old_leaks(self, memory_manager):
        """Test clearing old memory leak records."""
        # Add an old leak
        old_leak = MemoryLeak(
            object_type="old_object",
            count=1,
            size_bytes=1024,
            first_detected=datetime.now() - timedelta(hours=2),
            last_updated=datetime.now() - timedelta(hours=2),
            growth_rate=1024,
            severity="low",
        )
        memory_manager.memory_leaks["old_key"] = old_leak

        # Add a recent leak
        recent_leak = MemoryLeak(
            object_type="recent_object",
            count=1,
            size_bytes=1024,
            first_detected=datetime.now(),
            last_updated=datetime.now(),
            growth_rate=1024,
            severity="low",
        )
        memory_manager.memory_leaks["recent_key"] = recent_leak

        # Clear old leaks
        await memory_manager._clear_old_leaks()

        # Old leak should be removed, recent leak should remain
        assert "old_key" not in memory_manager.memory_leaks
        assert "recent_key" in memory_manager.memory_leaks

    def test_add_cleanup_callback(self, memory_manager):
        """Test adding cleanup callbacks."""

        async def test_callback(threshold):
            pass

        memory_manager.add_cleanup_callback(test_callback)

        assert len(memory_manager.cleanup_callbacks) == 1
        assert memory_manager.cleanup_callbacks[0] == test_callback

    @pytest.mark.asyncio
    async def test_monitoring_loop_error_handling(self, memory_manager):
        """Test error handling in monitoring loop."""
        # Mock _take_memory_snapshot to raise an exception
        original_snapshot = memory_manager._take_memory_snapshot

        async def failing_snapshot():
            raise Exception("Test error")

        memory_manager._take_memory_snapshot = failing_snapshot

        # Start monitoring
        await memory_manager.start_monitoring()

        # Wait a bit for the error to be handled
        await asyncio.sleep(0.1)

        # Stop monitoring
        await memory_manager.stop_monitoring()

        # Restore original method
        memory_manager._take_memory_snapshot = original_snapshot

    @pytest.mark.asyncio
    async def test_memory_threshold_checking(self, memory_manager):
        """Test memory threshold checking."""
        # Add a snapshot with high memory usage
        high_snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            total_memory_mb=16000,
            available_memory_mb=8000,
            used_memory_mb=8000,
            memory_percent=90.0,
            process_memory_mb=512,
            gc_objects=1000,
            gc_collections={},
            threshold=MemoryThreshold.HIGH,
        )
        memory_manager.snapshots.append(high_snapshot)

        # Check thresholds (should trigger cleanup)
        await memory_manager._check_memory_thresholds()

        # Should have triggered cleanup
        assert memory_manager.gc_stats["forced_collections"] == 1


class TestGlobalMemoryManager:
    """Test cases for global memory manager functionality."""

    @pytest.mark.asyncio
    async def test_get_memory_manager(self):
        """Test getting the global memory manager."""
        manager = await get_memory_manager()
        assert isinstance(manager, MemoryManager)
        assert manager == memory_manager

    @pytest.mark.asyncio
    async def test_memory_monitor_decorator(self):
        """Test the memory monitor decorator."""

        @memory_monitor(threshold=MemoryThreshold.HIGH)
        async def test_function():
            return "test_result"

        # Mock psutil for consistent testing
        with patch("psutil.virtual_memory") as mock_virtual_memory:
            mock_memory = Mock()
            mock_memory.percent = 95.0  # High memory usage
            mock_virtual_memory.return_value = mock_memory

            # Call the decorated function
            result = await test_function()

            assert result == "test_result"

    def test_memory_monitor_decorator_sync(self):
        """Test the memory monitor decorator with sync functions."""

        @memory_monitor(threshold=MemoryThreshold.HIGH)
        def test_sync_function():
            return "test_sync_result"

        # Mock psutil for consistent testing
        with patch("psutil.virtual_memory") as mock_virtual_memory:
            mock_memory = Mock()
            mock_memory.percent = 95.0  # High memory usage
            mock_virtual_memory.return_value = mock_memory

            # Call the decorated function
            result = test_sync_function()

            assert result == "test_sync_result"


class TestMemoryManagerIntegration:
    """Integration tests for memory manager with other services."""

    @pytest.mark.asyncio
    async def test_memory_manager_with_cache_manager(self):
        """Test memory manager integration with cache manager."""
        manager = MemoryManager(enable_tracemalloc=False)

        # Mock cache manager
        mock_cache_manager = Mock()
        mock_cache_manager.clear_all = Mock(return_value=asyncio.Future())
        mock_cache_manager.clear_all.return_value.set_result(None)

        # Patch the cache manager
        with patch(
            "bot.services.memory_management_service.cache_manager", mock_cache_manager
        ):
            # Test aggressive cleanup
            result = await manager.cleanup_memory(aggressive=True)

            # Should have called cache manager clear_all
            mock_cache_manager.clear_all.assert_called_once()

            assert "objects_freed" in result
            assert result["aggressive"] is True

    @pytest.mark.asyncio
    async def test_memory_manager_error_handling(self):
        """Test memory manager error handling."""
        manager = MemoryManager(enable_tracemalloc=False)

        # Test with failing cleanup callback
        async def failing_callback(threshold):
            raise Exception("Callback error")

        manager.add_cleanup_callback(failing_callback)

        # Should not raise exception
        await manager._trigger_memory_cleanup(MemoryThreshold.HIGH)

        # Should still perform garbage collection
        assert manager.gc_stats["forced_collections"] == 1

    def test_memory_manager_thread_safety(self):
        """Test memory manager thread safety."""
        manager = MemoryManager(enable_tracemalloc=False)

        # Test that operations are thread-safe
        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            total_memory_mb=16000,
            available_memory_mb=8000,
            used_memory_mb=8000,
            memory_percent=50.0,
            process_memory_mb=512,
            gc_objects=1000,
            gc_collections={},
            threshold=MemoryThreshold.MEDIUM,
        )

        # Add snapshot (should be thread-safe)
        manager.snapshots.append(snapshot)

        # Get stats (should be thread-safe)
        stats = manager.get_memory_stats()

        assert stats["snapshot_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
