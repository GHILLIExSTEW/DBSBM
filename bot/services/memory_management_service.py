"""Memory management service for monitoring and optimizing memory usage."""

import asyncio
import gc
import logging
import psutil
import time
import weakref
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import threading
import tracemalloc

from bot.data.cache_manager import cache_manager

logger = logging.getLogger(__name__)


class MemoryThreshold(Enum):
    """Memory threshold levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemorySnapshot:
    """Represents a memory usage snapshot."""

    timestamp: datetime
    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    memory_percent: float
    process_memory_mb: float
    gc_objects: int
    gc_collections: Dict[str, int]
    threshold: MemoryThreshold


@dataclass
class MemoryLeak:
    """Represents a detected memory leak."""

    object_type: str
    count: int
    size_bytes: int
    first_detected: datetime
    last_updated: datetime
    growth_rate: float
    severity: str


class MemoryManager:
    """Comprehensive memory management service."""

    def __init__(
        self,
        monitoring_interval: int = 30,
        gc_threshold: int = 700,
        memory_thresholds: Optional[Dict[str, float]] = None,
        enable_tracemalloc: bool = True,
    ):
        """Initialize the memory manager."""
        self.monitoring_interval = monitoring_interval
        self.gc_threshold = gc_threshold
        self.enable_tracemalloc = enable_tracemalloc

        # Memory thresholds (percentages)
        self.memory_thresholds = memory_thresholds or {
            "low": 50.0,
            "medium": 70.0,
            "high": 85.0,
            "critical": 95.0,
        }

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.snapshots: deque = deque(maxlen=1000)
        self.memory_leaks: Dict[str, MemoryLeak] = {}
        self.cleanup_callbacks: List[Callable] = []

        # Performance tracking
        self.gc_stats = defaultdict(int)
        self.cleanup_stats = defaultdict(int)

        # Thread safety
        self._lock = threading.Lock()

        # Initialize tracemalloc if enabled
        if self.enable_tracemalloc:
            tracemalloc.start()
            logger.info("Tracemalloc enabled for memory leak detection")

        # Initialize garbage collection
        gc.set_threshold(self.gc_threshold)
        logger.info(f"Garbage collection threshold set to {self.gc_threshold}")

        logger.info("Memory manager initialized")

    async def start_monitoring(self) -> None:
        """Start continuous memory monitoring."""
        if self.is_monitoring:
            logger.warning("Memory monitoring is already active")
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Memory monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Memory monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._take_memory_snapshot()
                await self._check_memory_thresholds()
                await self._detect_memory_leaks()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _take_memory_snapshot(self) -> None:
        """Take a memory usage snapshot."""
        try:
            # Get system memory info
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024

            # Get garbage collection stats
            gc_stats = gc.get_stats()
            gc_collections = {
                stat["collections"]: stat["collections"] for stat in gc_stats
            }

            # Determine threshold level
            threshold = self._get_memory_threshold(memory.percent)

            snapshot = MemorySnapshot(
                timestamp=datetime.now(),
                total_memory_mb=memory.total / 1024 / 1024,
                available_memory_mb=memory.available / 1024 / 1024,
                used_memory_mb=memory.used / 1024 / 1024,
                memory_percent=memory.percent,
                process_memory_mb=process_memory,
                gc_objects=len(gc.get_objects()),
                gc_collections=gc_collections,
                threshold=threshold,
            )

            with self._lock:
                self.snapshots.append(snapshot)

            # Log if memory usage is high
            if memory.percent > self.memory_thresholds["high"]:
                logger.warning(
                    f"High memory usage: {memory.percent:.1f}% ({process_memory:.1f}MB)"
                )

        except Exception as e:
            logger.error(f"Error taking memory snapshot: {e}")

    def _get_memory_threshold(self, memory_percent: float) -> MemoryThreshold:
        """Determine memory threshold level."""
        if memory_percent >= self.memory_thresholds["critical"]:
            return MemoryThreshold.CRITICAL
        elif memory_percent >= self.memory_thresholds["high"]:
            return MemoryThreshold.HIGH
        elif memory_percent >= self.memory_thresholds["medium"]:
            return MemoryThreshold.MEDIUM
        else:
            return MemoryThreshold.LOW

    async def _check_memory_thresholds(self) -> None:
        """Check memory thresholds and trigger cleanup if needed."""
        if not self.snapshots:
            return

        latest_snapshot = self.snapshots[-1]

        if latest_snapshot.threshold in [
            MemoryThreshold.HIGH,
            MemoryThreshold.CRITICAL,
        ]:
            logger.warning(
                f"Memory threshold {latest_snapshot.threshold.value} exceeded: {latest_snapshot.memory_percent:.1f}%"
            )
            await self._trigger_memory_cleanup(latest_snapshot.threshold)

    async def _detect_memory_leaks(self) -> None:
        """Detect potential memory leaks using tracemalloc."""
        if not self.enable_tracemalloc:
            return

        try:
            # Get current tracemalloc snapshot
            current_snapshot = tracemalloc.take_snapshot()

            if hasattr(self, "_previous_snapshot") and self._previous_snapshot:
                # Compare with previous snapshot
                stats = current_snapshot.compare_to(self._previous_snapshot, "lineno")

                for stat in stats[:10]:  # Top 10 changes
                    if stat.size_diff > 1024 * 1024:  # 1MB threshold
                        await self._record_potential_leak(stat)

            self._previous_snapshot = current_snapshot

        except Exception as e:
            logger.error(f"Error detecting memory leaks: {e}")

    async def _record_potential_leak(self, stat) -> None:
        """Record a potential memory leak."""
        leak_key = f"{stat.traceback.format()}"

        with self._lock:
            if leak_key in self.memory_leaks:
                leak = self.memory_leaks[leak_key]
                leak.count += 1
                leak.size_bytes += stat.size_diff
                leak.last_updated = datetime.now()
                leak.growth_rate = leak.size_bytes / max(
                    1, (leak.last_updated - leak.first_detected).total_seconds()
                )
            else:
                leak = MemoryLeak(
                    object_type=str(stat.traceback),
                    count=1,
                    size_bytes=stat.size_diff,
                    first_detected=datetime.now(),
                    last_updated=datetime.now(),
                    growth_rate=stat.size_diff,
                    severity="medium" if stat.size_diff < 10 * 1024 * 1024 else "high",
                )
                self.memory_leaks[leak_key] = leak

                logger.warning(
                    f"Potential memory leak detected: {stat.size_diff / 1024 / 1024:.2f}MB"
                )

    async def _trigger_memory_cleanup(self, threshold: MemoryThreshold) -> None:
        """Trigger memory cleanup based on threshold."""
        logger.info(f"Triggering memory cleanup for threshold: {threshold.value}")

        # Execute cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                await callback(threshold)
            except Exception as e:
                logger.error(f"Error in cleanup callback: {e}")

        # Force garbage collection
        collected = gc.collect()
        self.gc_stats["forced_collections"] += 1
        self.gc_stats["objects_freed"] += collected

        logger.info(f"Garbage collection freed {collected} objects")

    def add_cleanup_callback(self, callback: Callable) -> None:
        """Add a cleanup callback function."""
        self.cleanup_callbacks.append(callback)
        logger.info("Cleanup callback added")

    async def optimize_garbage_collection(self) -> Dict[str, Any]:
        """Optimize garbage collection settings based on usage patterns."""
        try:
            # Analyze recent snapshots
            if len(self.snapshots) < 10:
                return {"status": "insufficient_data"}

            recent_snapshots = list(self.snapshots)[-10:]
            avg_memory_percent = sum(s.memory_percent for s in recent_snapshots) / len(
                recent_snapshots
            )

            # Adjust GC threshold based on memory pressure
            if avg_memory_percent > self.memory_thresholds["high"]:
                new_threshold = max(100, self.gc_threshold - 100)
                gc.set_threshold(new_threshold)
                self.gc_threshold = new_threshold
                logger.info(
                    f"Reduced GC threshold to {new_threshold} due to high memory pressure"
                )
            elif avg_memory_percent < self.memory_thresholds["low"]:
                new_threshold = min(1000, self.gc_threshold + 100)
                gc.set_threshold(new_threshold)
                self.gc_threshold = new_threshold
                logger.info(
                    f"Increased GC threshold to {new_threshold} due to low memory pressure"
                )

            return {
                "status": "optimized",
                "new_threshold": self.gc_threshold,
                "avg_memory_percent": avg_memory_percent,
            }

        except Exception as e:
            logger.error(f"Error optimizing garbage collection: {e}")
            return {"status": "error", "error": str(e)}

    def get_memory_stats(
        self, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get memory usage statistics."""
        with self._lock:
            if not self.snapshots:
                return {"error": "No snapshots available"}

            # Filter snapshots by time window
            if time_window:
                cutoff_time = datetime.now() - time_window
                filtered_snapshots = [
                    s for s in self.snapshots if s.timestamp >= cutoff_time
                ]
            else:
                filtered_snapshots = list(self.snapshots)

            if not filtered_snapshots:
                return {"error": "No snapshots in time window"}

            # Calculate statistics
            memory_percents = [s.memory_percent for s in filtered_snapshots]
            process_memories = [s.process_memory_mb for s in filtered_snapshots]

            return {
                "current_memory_percent": filtered_snapshots[-1].memory_percent,
                "current_process_memory_mb": filtered_snapshots[-1].process_memory_mb,
                "avg_memory_percent": sum(memory_percents) / len(memory_percents),
                "max_memory_percent": max(memory_percents),
                "avg_process_memory_mb": sum(process_memories) / len(process_memories),
                "max_process_memory_mb": max(process_memories),
                "snapshot_count": len(filtered_snapshots),
                "gc_threshold": self.gc_threshold,
                "gc_stats": dict(self.gc_stats),
                "cleanup_stats": dict(self.cleanup_stats),
            }

    def get_memory_leaks(self) -> List[Dict[str, Any]]:
        """Get detected memory leaks."""
        with self._lock:
            return [
                {
                    "object_type": leak.object_type,
                    "count": leak.count,
                    "size_mb": leak.size_bytes / 1024 / 1024,
                    "growth_rate_mb_per_second": leak.growth_rate / 1024 / 1024,
                    "severity": leak.severity,
                    "first_detected": leak.first_detected.isoformat(),
                    "last_updated": leak.last_updated.isoformat(),
                }
                for leak in self.memory_leaks.values()
            ]

    async def cleanup_memory(self, aggressive: bool = False) -> Dict[str, Any]:
        """Perform memory cleanup."""
        try:
            start_time = time.time()

            # Force garbage collection
            collected = gc.collect()

            # Clear caches if aggressive cleanup
            if aggressive:
                await self._clear_caches()

            # Clear memory leaks if they're old
            await self._clear_old_leaks()

            cleanup_time = time.time() - start_time

            self.cleanup_stats["cleanups_performed"] += 1
            self.cleanup_stats["total_objects_freed"] += collected
            self.cleanup_stats["total_cleanup_time"] += cleanup_time

            return {
                "objects_freed": collected,
                "cleanup_time_seconds": cleanup_time,
                "aggressive": aggressive,
            }

        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
            return {"error": str(e)}

    async def _clear_caches(self) -> None:
        """Clear various caches."""
        try:
            # Clear cache manager
            if hasattr(cache_manager, "clear_all"):
                await cache_manager.clear_all()
                logger.info("Cache manager cleared")

            # Clear any other caches in the system
            # This could be expanded based on specific cache implementations

        except Exception as e:
            logger.error(f"Error clearing caches: {e}")

    async def _clear_old_leaks(self) -> None:
        """Clear old memory leak records."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=1)

            with self._lock:
                old_leaks = [
                    key
                    for key, leak in self.memory_leaks.items()
                    if leak.last_updated < cutoff_time
                ]

                for key in old_leaks:
                    del self.memory_leaks[key]

                if old_leaks:
                    logger.info(f"Cleared {len(old_leaks)} old memory leak records")

        except Exception as e:
            logger.error(f"Error clearing old leaks: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get memory health status."""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024

            threshold = self._get_memory_threshold(memory.percent)

            return {
                "status": (
                    "healthy"
                    if threshold in [MemoryThreshold.LOW, MemoryThreshold.MEDIUM]
                    else "warning"
                ),
                "memory_percent": memory.percent,
                "process_memory_mb": process_memory,
                "threshold": threshold.value,
                "is_monitoring": self.is_monitoring,
                "snapshot_count": len(self.snapshots),
                "leak_count": len(self.memory_leaks),
            }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {"status": "error", "error": str(e)}

    async def shutdown(self) -> None:
        """Shutdown the memory manager."""
        await self.stop_monitoring()

        if self.enable_tracemalloc:
            tracemalloc.stop()
            logger.info("Tracemalloc stopped")

        logger.info("Memory manager shutdown complete")


# Global memory manager instance
memory_manager = MemoryManager()


async def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    return memory_manager


def memory_monitor(threshold: MemoryThreshold = MemoryThreshold.HIGH):
    """Decorator to monitor memory usage of functions."""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            manager = await get_memory_manager()

            # Check memory before execution
            memory = psutil.virtual_memory()
            if memory.percent > manager.memory_thresholds[threshold.value]:
                logger.warning(
                    f"High memory usage before {func.__name__}: {memory.percent:.1f}%"
                )

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # Check memory after execution
                memory = psutil.virtual_memory()
                if memory.percent > manager.memory_thresholds[threshold.value]:
                    logger.warning(
                        f"High memory usage after {func.__name__}: {memory.percent:.1f}%"
                    )

        def sync_wrapper(*args, **kwargs):
            manager = memory_manager  # Use sync access for sync functions

            # Check memory before execution
            memory = psutil.virtual_memory()
            if memory.percent > manager.memory_thresholds[threshold.value]:
                logger.warning(
                    f"High memory usage before {func.__name__}: {memory.percent:.1f}%"
                )

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Check memory after execution
                memory = psutil.virtual_memory()
                if memory.percent > manager.memory_thresholds[threshold.value]:
                    logger.warning(
                        f"High memory usage after {func.__name__}: {memory.percent:.1f}%"
                    )

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
