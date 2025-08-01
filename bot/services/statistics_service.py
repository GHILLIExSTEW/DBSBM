"""
Statistics Service for DBSBM.

This service provides system statistics and metrics collection.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SystemStats:
    """System statistics data class."""
    uptime: float
    memory_usage: float
    cpu_usage: float
    active_connections: int
    total_requests: int
    error_rate: float
    timestamp: datetime


class StatisticsService:
    """Service for collecting and managing system statistics."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.start_time = time.time()
        self.stats_history = []
        self.is_running = False
        self._task = None

    async def start(self):
        """Start the statistics service."""
        if self.is_running:
            logger.warning("Statistics service is already running")
            return

        logger.info("Starting statistics service...")
        self.is_running = True
        self._task = asyncio.create_task(self._collect_stats_loop())
        logger.info("Statistics service started successfully")

    async def stop(self):
        """Stop the statistics service."""
        if not self.is_running:
            logger.warning("Statistics service is not running")
            return

        logger.info("Stopping statistics service...")
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Statistics service stopped")

    async def _collect_stats_loop(self):
        """Main loop for collecting statistics."""
        while self.is_running:
            try:
                stats = await self._collect_current_stats()
                self.stats_history.append(stats)
                
                # Keep only last 100 entries to prevent memory issues
                if len(self.stats_history) > 100:
                    self.stats_history = self.stats_history[-100:]
                
                await asyncio.sleep(60)  # Collect stats every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting statistics: {e}")
                await asyncio.sleep(60)

    async def _collect_current_stats(self) -> SystemStats:
        """Collect current system statistics."""
        try:
            import psutil
            
            # Get basic system stats
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Calculate uptime
            uptime = time.time() - self.start_time
            
            # Get database connection info if available
            active_connections = 0
            if self.db_manager and hasattr(self.db_manager, 'pool'):
                try:
                    pool = self.db_manager.pool
                    if hasattr(pool, '_pool'):
                        active_connections = len([conn for conn in pool._pool if conn._con and not conn._con.closed])
                except Exception:
                    pass
            
            # Calculate basic metrics (these would be more sophisticated in a real implementation)
            total_requests = len(self.stats_history) * 60  # Rough estimate
            error_rate = 0.0  # Would be calculated from actual error tracking
            
            return SystemStats(
                uptime=uptime,
                memory_usage=memory.percent,
                cpu_usage=cpu_percent,
                active_connections=active_connections,
                total_requests=total_requests,
                error_rate=error_rate,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error collecting current stats: {e}")
            # Return default stats on error
            return SystemStats(
                uptime=time.time() - self.start_time,
                memory_usage=0.0,
                cpu_usage=0.0,
                active_connections=0,
                total_requests=0,
                error_rate=0.0,
                timestamp=datetime.utcnow()
            )

    async def get_current_stats(self) -> Dict[str, Any]:
        """Get current system statistics."""
        if not self.stats_history:
            return {
                "status": "initializing",
                "uptime": time.time() - self.start_time,
                "memory_usage": 0.0,
                "cpu_usage": 0.0,
                "active_connections": 0,
                "total_requests": 0,
                "error_rate": 0.0
            }
        
        latest = self.stats_history[-1]
        return {
            "status": "healthy" if self.is_running else "stopped",
            "uptime": latest.uptime,
            "memory_usage": latest.memory_usage,
            "cpu_usage": latest.cpu_usage,
            "active_connections": latest.active_connections,
            "total_requests": latest.total_requests,
            "error_rate": latest.error_rate,
            "timestamp": latest.timestamp.isoformat()
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status for the statistics service."""
        try:
            if not self.is_running:
                return {
                    "status": "unhealthy",
                    "error_message": "Statistics service is not running",
                    "response_time": 0.0
                }
            
            start_time = time.time()
            stats = await self.get_current_stats()
            response_time = time.time() - start_time
            
            # Determine health based on basic metrics
            if stats.get("memory_usage", 0) > 90 or stats.get("cpu_usage", 0) > 90:
                status = "degraded"
            elif stats.get("memory_usage", 0) > 80 or stats.get("cpu_usage", 0) > 80:
                status = "degraded"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "response_time": response_time,
                "details": stats
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error_message": f"Statistics service health check failed: {str(e)}",
                "response_time": 0.0
            } 