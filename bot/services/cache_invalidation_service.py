"""
Cache Invalidation Service for DBSBM System.
Implements intelligent cache invalidation patterns and strategies.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum

from data.db_manager import DatabaseManager
from utils.enhanced_cache_manager import EnhancedCacheManager
from services.performance_monitor import time_operation, record_metric

logger = logging.getLogger(__name__)


class InvalidationStrategy(Enum):
    """Cache invalidation strategies."""

    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    BATCH = "batch"
    INTELLIGENT = "intelligent"


class InvalidationTrigger(Enum):
    """Cache invalidation triggers."""

    DATA_UPDATE = "data_update"
    TIME_EXPIRY = "time_expiry"
    MEMORY_PRESSURE = "memory_pressure"
    MANUAL = "manual"
    SYSTEM_EVENT = "system_event"


@dataclass
class InvalidationRule:
    """Cache invalidation rule configuration."""

    name: str
    pattern: str
    strategy: InvalidationStrategy
    triggers: List[InvalidationTrigger]
    ttl: Optional[int] = None
    is_active: bool = True
    last_invalidation: Optional[datetime] = None


class CacheInvalidationService:
    """Service for intelligent cache invalidation patterns."""

    def __init__(
        self, db_manager: DatabaseManager, cache_manager: EnhancedCacheManager
    ):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.invalidation_rules: Dict[str, InvalidationRule] = {}
        self.invalidation_queue: List[Dict[str, Any]] = []
        self.invalidation_stats = {
            "total_invalidations": 0,
            "immediate_invalidations": 0,
            "delayed_invalidations": 0,
            "batch_invalidations": 0,
            "intelligent_invalidations": 0,
        }

    async def start(self):
        """Start the cache invalidation service."""
        logger.info("Starting CacheInvalidationService...")

        # Register default invalidation rules
        await self._register_default_rules()

        # Start background invalidation workers
        asyncio.create_task(self._delayed_invalidation_worker())
        asyncio.create_task(self._batch_invalidation_worker())
        asyncio.create_task(self._intelligent_invalidation_worker())

        logger.info("CacheInvalidationService started successfully")

    async def stop(self):
        """Stop the cache invalidation service."""
        logger.info("Stopping CacheInvalidationService...")
        logger.info("CacheInvalidationService stopped successfully")

    @time_operation("cache_invalidation_register_rule")
    async def register_invalidation_rule(self, rule: InvalidationRule) -> bool:
        """Register a new cache invalidation rule."""
        try:
            self.invalidation_rules[rule.name] = rule
            logger.info(f"Registered invalidation rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register invalidation rule {rule.name}: {e}")
            return False

    @time_operation("cache_invalidation_trigger")
    async def trigger_invalidation(
        self,
        pattern: str,
        trigger: InvalidationTrigger,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Trigger cache invalidation for a specific pattern."""
        try:
            # Find matching rules
            matching_rules = [
                rule
                for rule in self.invalidation_rules.values()
                if rule.is_active and trigger in rule.triggers
            ]

            for rule in matching_rules:
                if self._pattern_matches(rule.pattern, pattern):
                    await self._execute_invalidation(rule, pattern, data)

            return True

        except Exception as e:
            logger.error(f"Failed to trigger invalidation for pattern {pattern}: {e}")
            return False

    @time_operation("cache_invalidation_immediate")
    async def invalidate_immediate(
        self, pattern: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Immediately invalidate cache for a pattern."""
        try:
            logger.info(f"Immediate invalidation for pattern: {pattern}")

            # Clear cache for the pattern
            await self.cache_manager.clear_prefix(pattern)

            # Update statistics
            self.invalidation_stats["total_invalidations"] += 1
            self.invalidation_stats["immediate_invalidations"] += 1

            logger.info(f"Immediate invalidation completed for pattern: {pattern}")
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate immediately for pattern {pattern}: {e}")
            return False

    @time_operation("cache_invalidation_delayed")
    async def invalidate_delayed(
        self,
        pattern: str,
        delay_seconds: int = 300,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Schedule delayed cache invalidation."""
        try:
            invalidation_task = {
                "pattern": pattern,
                "scheduled_time": datetime.utcnow() + timedelta(seconds=delay_seconds),
                "data": data,
                "type": "delayed",
            }

            self.invalidation_queue.append(invalidation_task)

            logger.info(
                f"Scheduled delayed invalidation for pattern: {pattern} in {delay_seconds} seconds"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to schedule delayed invalidation for pattern {pattern}: {e}"
            )
            return False

    @time_operation("cache_invalidation_batch")
    async def invalidate_batch(
        self, patterns: List[str], data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Batch invalidate multiple cache patterns."""
        try:
            logger.info(f"Batch invalidation for {len(patterns)} patterns")

            # Group patterns by prefix for efficient clearing
            prefix_groups = {}
            for pattern in patterns:
                prefix = pattern.split(":")[0] if ":" in pattern else pattern
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(pattern)

            # Clear each prefix group
            for prefix, pattern_list in prefix_groups.items():
                await self.cache_manager.clear_prefix(prefix)
                logger.debug(
                    f"Cleared prefix group: {prefix} with {len(pattern_list)} patterns"
                )

            # Update statistics
            self.invalidation_stats["total_invalidations"] += len(patterns)
            self.invalidation_stats["batch_invalidations"] += 1

            logger.info(f"Batch invalidation completed for {len(patterns)} patterns")
            return True

        except Exception as e:
            logger.error(f"Failed to batch invalidate patterns: {e}")
            return False

    async def _register_default_rules(self):
        """Register default cache invalidation rules."""
        try:
            # User data invalidation
            user_rule = InvalidationRule(
                name="user_data_invalidation",
                pattern="user_data:*",
                strategy=InvalidationStrategy.IMMEDIATE,
                triggers=[InvalidationTrigger.DATA_UPDATE, InvalidationTrigger.MANUAL],
                ttl=1800,
            )
            await self.register_invalidation_rule(user_rule)

            # Game data invalidation
            game_rule = InvalidationRule(
                name="game_data_invalidation",
                pattern="game_data:*",
                strategy=InvalidationStrategy.DELAYED,
                triggers=[
                    InvalidationTrigger.DATA_UPDATE,
                    InvalidationTrigger.TIME_EXPIRY,
                ],
                ttl=900,
            )
            await self.register_invalidation_rule(game_rule)

            # Bet data invalidation
            bet_rule = InvalidationRule(
                name="bet_data_invalidation",
                pattern="bet_data:*",
                strategy=InvalidationStrategy.IMMEDIATE,
                triggers=[
                    InvalidationTrigger.DATA_UPDATE,
                    InvalidationTrigger.SYSTEM_EVENT,
                ],
                ttl=300,
            )
            await self.register_invalidation_rule(bet_rule)

            # Stats data invalidation
            stats_rule = InvalidationRule(
                name="stats_data_invalidation",
                pattern="stats_data:*",
                strategy=InvalidationStrategy.BATCH,
                triggers=[
                    InvalidationTrigger.DATA_UPDATE,
                    InvalidationTrigger.TIME_EXPIRY,
                ],
                ttl=3600,
            )
            await self.register_invalidation_rule(stats_rule)

            # API response invalidation
            api_rule = InvalidationRule(
                name="api_response_invalidation",
                pattern="api_response:*",
                strategy=InvalidationStrategy.INTELLIGENT,
                triggers=[
                    InvalidationTrigger.TIME_EXPIRY,
                    InvalidationTrigger.MEMORY_PRESSURE,
                ],
                ttl=300,
            )
            await self.register_invalidation_rule(api_rule)

            logger.info("Default invalidation rules registered successfully")

        except Exception as e:
            logger.error(f"Failed to register default invalidation rules: {e}")

    async def _execute_invalidation(
        self,
        rule: InvalidationRule,
        pattern: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Execute invalidation based on rule strategy."""
        try:
            if rule.strategy == InvalidationStrategy.IMMEDIATE:
                await self.invalidate_immediate(pattern, data)
            elif rule.strategy == InvalidationStrategy.DELAYED:
                await self.invalidate_delayed(pattern, rule.ttl or 300, data)
            elif rule.strategy == InvalidationStrategy.BATCH:
                # Add to batch queue
                self.invalidation_queue.append(
                    {
                        "pattern": pattern,
                        "scheduled_time": datetime.utcnow() + timedelta(minutes=5),
                        "data": data,
                        "type": "batch",
                    }
                )
            elif rule.strategy == InvalidationStrategy.INTELLIGENT:
                await self._intelligent_invalidation(rule, pattern, data)

            # Update rule statistics
            rule.last_invalidation = datetime.utcnow()

        except Exception as e:
            logger.error(f"Failed to execute invalidation for rule {rule.name}: {e}")

    async def _intelligent_invalidation(
        self,
        rule: InvalidationRule,
        pattern: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Perform intelligent cache invalidation based on usage patterns."""
        try:
            # Get cache statistics
            cache_stats = await self.cache_manager.get_stats()

            # Check if pattern is frequently accessed
            if cache_stats.get("hits", 0) > cache_stats.get("misses", 0) * 2:
                # High hit rate - use delayed invalidation
                await self.invalidate_delayed(pattern, 600)  # 10 minutes delay
                logger.info(
                    f"Intelligent invalidation: delayed for high-hit pattern {pattern}"
                )
            else:
                # Low hit rate - immediate invalidation
                await self.invalidate_immediate(pattern, data)
                logger.info(
                    f"Intelligent invalidation: immediate for low-hit pattern {pattern}"
                )

            # Update statistics
            self.invalidation_stats["intelligent_invalidations"] += 1

        except Exception as e:
            logger.error(f"Failed to perform intelligent invalidation: {e}")

    def _pattern_matches(self, rule_pattern: str, target_pattern: str) -> bool:
        """Check if a target pattern matches a rule pattern."""
        try:
            # Simple pattern matching with wildcards
            if rule_pattern.endswith("*"):
                return target_pattern.startswith(rule_pattern[:-1])
            elif rule_pattern.startswith("*"):
                return target_pattern.endswith(rule_pattern[1:])
            else:
                return rule_pattern == target_pattern
        except Exception:
            return False

    async def _delayed_invalidation_worker(self):
        """Background worker for delayed invalidations."""
        while True:
            try:
                current_time = datetime.utcnow()
                ready_invalidations = [
                    task
                    for task in self.invalidation_queue
                    if task["type"] == "delayed"
                    and current_time >= task["scheduled_time"]
                ]

                for task in ready_invalidations:
                    await self.invalidate_immediate(task["pattern"], task["data"])
                    self.invalidation_queue.remove(task)
                    self.invalidation_stats["delayed_invalidations"] += 1

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in delayed invalidation worker: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _batch_invalidation_worker(self):
        """Background worker for batch invalidations."""
        while True:
            try:
                current_time = datetime.utcnow()
                ready_batches = [
                    task
                    for task in self.invalidation_queue
                    if task["type"] == "batch"
                    and current_time >= task["scheduled_time"]
                ]

                if ready_batches:
                    # Group patterns for batch processing
                    all_patterns = []
                    for task in ready_batches:
                        all_patterns.append(task["pattern"])
                        self.invalidation_queue.remove(task)

                    if all_patterns:
                        await self.invalidate_batch(all_patterns)

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in batch invalidation worker: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error

    async def _intelligent_invalidation_worker(self):
        """Background worker for intelligent invalidations."""
        while True:
            try:
                # Check memory pressure
                cache_stats = await self.cache_manager.get_stats()

                # If cache size is high, trigger intelligent cleanup
                if cache_stats.get("size", 0) > 10000:  # Arbitrary threshold
                    logger.info(
                        "High cache size detected, triggering intelligent cleanup"
                    )
                    await self._cleanup_old_cache_entries()

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Error in intelligent invalidation worker: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _cleanup_old_cache_entries(self):
        """Clean up old cache entries based on access patterns."""
        try:
            # This would typically involve more sophisticated logic
            # For now, we'll clear some older patterns
            old_patterns = ["api_response:*", "temp_data:*", "session:*"]

            for pattern in old_patterns:
                await self.cache_manager.clear_prefix(pattern.split(":")[0])

            logger.info("Cleaned up old cache entries")

        except Exception as e:
            logger.error(f"Failed to cleanup old cache entries: {e}")

    async def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get cache invalidation statistics."""
        return {
            **self.invalidation_stats,
            "active_rules": len(
                [r for r in self.invalidation_rules.values() if r.is_active]
            ),
            "total_rules": len(self.invalidation_rules),
            "queue_size": len(self.invalidation_queue),
            "last_invalidation": max(
                [
                    r.last_invalidation
                    for r in self.invalidation_rules.values()
                    if r.last_invalidation
                ],
                default=None,
            ),
        }

    async def clear_invalidation_queue(self):
        """Clear the invalidation queue."""
        try:
            self.invalidation_queue.clear()
            logger.info("Invalidation queue cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing invalidation queue: {e}")

    async def get_invalidation_rules(self) -> List[Dict[str, Any]]:
        """Get all invalidation rules."""
        return [
            {
                "name": rule.name,
                "pattern": rule.pattern,
                "strategy": rule.strategy.value,
                "triggers": [trigger.value for trigger in rule.triggers],
                "ttl": rule.ttl,
                "is_active": rule.is_active,
                "last_invalidation": (
                    rule.last_invalidation.isoformat()
                    if rule.last_invalidation
                    else None
                ),
            }
            for rule in self.invalidation_rules.values()
        ]
