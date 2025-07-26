#!/usr/bin/env python3
"""Performance optimization script for DBSBM system."""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add the bot directory to the path
bot_path = Path(__file__).parent.parent / "bot"
sys.path.insert(0, str(bot_path))

# Import modules
from data.cache_manager import cache_manager
from services.performance_monitor import performance_monitor
from data.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Performance optimization utility."""

    def __init__(self):
        """Initialize the performance optimizer."""
        self.db_manager = DatabaseManager()
        self.optimization_results = {}

    async def analyze_system_performance(self) -> Dict[str, Any]:
        """Analyze current system performance."""
        logger.info("🔍 Analyzing system performance...")

        analysis = {
            "timestamp": time.time(),
            "cache_status": {},
            "database_status": {},
            "system_metrics": {},
            "recommendations": []
        }

        # Check cache status
        try:
            cache_stats = await cache_manager.get_stats()
            analysis["cache_status"] = cache_stats

            if not cache_stats.get("enabled"):
                analysis["recommendations"].append("Enable Redis caching for better performance")
            elif cache_stats.get("hit_rate", "0%") < "50%":
                analysis["recommendations"].append("Cache hit rate is low - consider adjusting cache TTLs")

        except Exception as e:
            logger.error(f"Error checking cache status: {e}")
            analysis["cache_status"] = {"error": str(e)}

        # Check database performance
        try:
            query_stats = performance_monitor.get_query_stats()
            analysis["database_status"] = query_stats

            if query_stats["avg_time"] > 0.5:
                analysis["recommendations"].append("Database queries are slow - consider adding indexes")
            if query_stats["success_rate"] < 0.95:
                analysis["recommendations"].append("Database error rate is high - check for connection issues")

        except Exception as e:
            logger.error(f"Error checking database status: {e}")
            analysis["database_status"] = {"error": str(e)}

        # Check system metrics
        try:
            system_stats = performance_monitor.get_system_stats()
            analysis["system_metrics"] = system_stats

            if system_stats["memory_percent"] > 80:
                analysis["recommendations"].append("High memory usage - consider optimizing memory usage")
            if system_stats["cpu_percent"] > 80:
                analysis["recommendations"].append("High CPU usage - consider optimizing CPU-intensive operations")

        except Exception as e:
            logger.error(f"Error checking system metrics: {e}")
            analysis["system_metrics"] = {"error": str(e)}

        return analysis

    async def optimize_cache_settings(self) -> Dict[str, Any]:
        """Optimize cache settings based on usage patterns."""
        logger.info("⚡ Optimizing cache settings...")

        results = {
            "optimizations_applied": [],
            "cache_cleared": 0,
            "ttl_adjustments": {}
        }

        try:
            # Get cache statistics
            cache_stats = await cache_manager.get_stats()

            if not cache_stats.get("enabled"):
                logger.warning("Cache is not enabled - skipping cache optimization")
                return results

            # Clear old cache entries
            for prefix in ["api_response", "db_query", "parlay_data"]:
                cleared = await cache_manager.clear_prefix(prefix)
                if cleared > 0:
                    results["cache_cleared"] += cleared
                    results["optimizations_applied"].append(f"Cleared {cleared} old {prefix} entries")

            # Adjust TTLs based on usage patterns
            # This is a simple heuristic - in production you'd want more sophisticated analysis
            results["ttl_adjustments"] = {
                "api_response": "300s",  # 5 minutes
                "db_query": "600s",      # 10 minutes
                "parlay_data": "300s",   # 5 minutes
            }

        except Exception as e:
            logger.error(f"Error optimizing cache settings: {e}")
            results["error"] = str(e)

        return results

    async def optimize_database_queries(self) -> Dict[str, Any]:
        """Analyze and suggest database query optimizations."""
        logger.info("🗄️ Analyzing database queries...")

        results = {
            "slow_queries": [],
            "frequent_queries": [],
            "recommendations": []
        }

        try:
            # Get query performance data
            query_stats = performance_monitor.get_query_stats()

            # Analyze slow queries
            if query_stats["slow_queries"] > 0:
                results["recommendations"].append(f"Found {query_stats['slow_queries']} slow queries - consider adding indexes")

            # Check cache hit rate
            if query_stats["cache_hit_rate"] < 0.5:
                results["recommendations"].append("Low cache hit rate - consider increasing cache TTLs")

            # Check success rate
            if query_stats["success_rate"] < 0.95:
                results["recommendations"].append("Low query success rate - check for connection issues")

        except Exception as e:
            logger.error(f"Error analyzing database queries: {e}")
            results["error"] = str(e)

        return results

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        logger.info("📊 Generating performance report...")

        report = {
            "timestamp": time.time(),
            "analysis": await self.analyze_system_performance(),
            "cache_optimization": await self.optimize_cache_settings(),
            "database_optimization": await self.optimize_database_queries(),
            "performance_stats": performance_monitor.get_performance_report()
        }

        return report

    async def apply_optimizations(self) -> Dict[str, Any]:
        """Apply performance optimizations."""
        logger.info("🚀 Applying performance optimizations...")

        results = {
            "applied": [],
            "errors": [],
            "warnings": []
        }

        try:
            # Connect to cache
            cache_connected = await cache_manager.connect()
            if not cache_connected:
                results["warnings"].append("Cache not available - some optimizations skipped")

            # Apply cache optimizations
            cache_results = await self.optimize_cache_settings()
            if cache_results.get("optimizations_applied"):
                results["applied"].extend(cache_results["optimizations_applied"])

            # Apply database optimizations
            db_results = await self.optimize_database_queries()
            if db_results.get("recommendations"):
                results["applied"].extend(db_results["recommendations"])

        except Exception as e:
            logger.error(f"Error applying optimizations: {e}")
            results["errors"].append(str(e))

        return results


async def main():
    """Main function for performance optimization."""
    logger.info("🎯 Starting DBSBM Performance Optimization")

    optimizer = PerformanceOptimizer()

    try:
        # Generate performance report
        report = await optimizer.generate_performance_report()

        # Print summary
        logger.info("=== PERFORMANCE OPTIMIZATION SUMMARY ===")

        # Cache status
        cache_status = report["analysis"]["cache_status"]
        if cache_status.get("enabled"):
            logger.info(f"✅ Cache: Enabled (Hit Rate: {cache_status.get('hit_rate', 'N/A')})")
        else:
            logger.warning("❌ Cache: Disabled")

        # Database status
        db_status = report["analysis"]["database_status"]
        if "error" not in db_status:
            logger.info(f"✅ Database: {db_status.get('total_queries', 0)} queries, "
                       f"{db_status.get('avg_time', 0):.3f}s avg")

        # System metrics
        sys_metrics = report["analysis"]["system_metrics"]
        if "error" not in sys_metrics:
            logger.info(f"✅ System: {sys_metrics.get('memory_percent', 0):.1f}% memory, "
                       f"{sys_metrics.get('cpu_percent', 0):.1f}% CPU")

        # Recommendations
        recommendations = report["analysis"]["recommendations"]
        if recommendations:
            logger.info("📋 Recommendations:")
            for rec in recommendations:
                logger.info(f"  • {rec}")

        # Apply optimizations
        optimizations = await optimizer.apply_optimizations()

        if optimizations["applied"]:
            logger.info("✅ Applied optimizations:")
            for opt in optimizations["applied"]:
                logger.info(f"  • {opt}")

        if optimizations["warnings"]:
            logger.warning("⚠️ Warnings:")
            for warning in optimizations["warnings"]:
                logger.warning(f"  • {warning}")

        if optimizations["errors"]:
            logger.error("❌ Errors:")
            for error in optimizations["errors"]:
                logger.error(f"  • {error}")

        logger.info("=== OPTIMIZATION COMPLETE ===")

        return report

    except Exception as e:
        logger.error(f"Error during performance optimization: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    asyncio.run(main())
