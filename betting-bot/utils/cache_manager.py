"""Caching system for performance optimization."""

import asyncio
import json
import logging
import time
from typing import Any, Optional, Dict, List
from functools import wraps
import hashlib
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for various data types."""

    def __init__(
        self, cache_dir: str = "betting-bot/data/cache", max_size_mb: int = 100
    ):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory for cache files
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()

    def _load_cache_index(self) -> Dict[str, Dict[str, Any]]:
        """Load the cache index from disk."""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache index: {e}")
        return {}

    def _save_cache_index(self):
        """Save the cache index to disk."""
        try:
            with open(self.cache_index_file, "w") as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache index: {e}")

    def _generate_cache_key(self, key: str) -> str:
        """Generate a cache key hash."""
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get the cache file path for a key."""
        cache_key = self._generate_cache_key(key)
        return self.cache_dir / f"{cache_key}.cache"

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(key)
            expiry_time = time.time() + ttl

            # Serialize and save the value
            cache_data = {"value": value, "expiry": expiry_time, "created": time.time()}

            with open(cache_path, "wb") as f:
                pickle.dump(cache_data, f)

            # Update cache index
            self.cache_index[key] = {
                "path": str(cache_path),
                "expiry": expiry_time,
                "size": cache_path.stat().st_size if cache_path.exists() else 0,
            }
            self._save_cache_index()

            # Clean up if cache is too large
            self._cleanup_if_needed()

            logger.debug(f"Cached value for key: {key}")
            return True

        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            cache_path = self._get_cache_path(key)

            if not cache_path.exists():
                return None

            # Check if expired
            if key in self.cache_index:
                if time.time() > self.cache_index[key]["expiry"]:
                    self.delete(key)
                    return None

            # Load cached data
            with open(cache_path, "rb") as f:
                cache_data = pickle.load(f)

            # Check expiry
            if time.time() > cache_data["expiry"]:
                self.delete(key)
                return None

            logger.debug(f"Retrieved cached value for key: {key}")
            return cache_data["value"]

        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(key)

            if cache_path.exists():
                cache_path.unlink()

            if key in self.cache_index:
                del self.cache_index[key]
                self._save_cache_index()

            logger.debug(f"Deleted cache for key: {key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove all cache files
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()

            # Clear index
            self.cache_index.clear()
            self._save_cache_index()

            logger.info("Cache cleared successfully")
            return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def _cleanup_if_needed(self):
        """Clean up cache if it exceeds maximum size."""
        try:
            total_size = sum(
                entry.get("size", 0) for entry in self.cache_index.values()
            )

            if total_size > self.max_size_bytes:
                # Remove oldest entries
                sorted_entries = sorted(
                    self.cache_index.items(), key=lambda x: x[1].get("created", 0)
                )

                for key, _ in sorted_entries:
                    self.delete(key)
                    total_size = sum(
                        entry.get("size", 0) for entry in self.cache_index.values()
                    )
                    if total_size <= self.max_size_bytes * 0.8:  # Leave 20% buffer
                        break

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            total_size = sum(
                entry.get("size", 0) for entry in self.cache_index.values()
            )
            active_entries = len(
                [
                    k
                    for k, v in self.cache_index.items()
                    if time.time() <= v.get("expiry", 0)
                ]
            )

            return {
                "total_entries": len(self.cache_index),
                "active_entries": active_entries,
                "total_size_mb": total_size / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "hit_rate": self._calculate_hit_rate(),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate (placeholder for now)."""
        # This would require tracking hits/misses over time
        return 0.0


# Global cache instance
cache_manager = CacheManager()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
