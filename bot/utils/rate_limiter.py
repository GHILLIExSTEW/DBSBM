"""
Rate limiting utility for DBSBM.
Provides rate limiting for user actions to prevent abuse and spam.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_requests: int
    window_seconds: int
    action_name: str
    description: str = ""


@dataclass
class RateLimitEntry:
    """Individual rate limit entry."""
    timestamp: float
    user_id: int
    action: str


class RateLimiter:
    """Rate limiter for user actions."""
    
    # Default rate limit configurations
    DEFAULT_LIMITS = {
        "bet_placement": RateLimitConfig(
            max_requests=5,
            window_seconds=60,
            action_name="bet_placement",
            description="Bet placement rate limit"
        ),
        "stats_query": RateLimitConfig(
            max_requests=10,
            window_seconds=60,
            action_name="stats_query",
            description="Statistics query rate limit"
        ),
        "admin_command": RateLimitConfig(
            max_requests=3,
            window_seconds=60,
            action_name="admin_command",
            description="Admin command rate limit"
        ),
        "image_generation": RateLimitConfig(
            max_requests=10,
            window_seconds=60,
            action_name="image_generation",
            description="Image generation rate limit"
        ),
        "api_request": RateLimitConfig(
            max_requests=20,
            window_seconds=60,
            action_name="api_request",
            description="API request rate limit"
        ),
        "user_registration": RateLimitConfig(
            max_requests=1,
            window_seconds=300,  # 5 minutes
            action_name="user_registration",
            description="User registration rate limit"
        )
    }
    
    def __init__(self, custom_limits: Optional[Dict[str, RateLimitConfig]] = None):
        """
        Initialize the rate limiter.
        
        Args:
            custom_limits: Custom rate limit configurations
        """
        self.limits = {**self.DEFAULT_LIMITS}
        if custom_limits:
            self.limits.update(custom_limits)
        
        # Storage for rate limit data
        self.user_requests: Dict[Tuple[int, str], deque] = defaultdict(deque)
        self.lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "rate_limited_requests": 0,
            "cleanup_runs": 0
        }
        
        logger.info(f"Rate limiter initialized with {len(self.limits)} limit configurations")
    
    async def is_allowed(self, user_id: int, action: str) -> Tuple[bool, Optional[float]]:
        """
        Check if a user action is allowed.
        
        Args:
            user_id: Discord user ID
            action: Action being performed
            
        Returns:
            Tuple[bool, Optional[float]]: (is_allowed, retry_after_seconds)
        """
        if action not in self.limits:
            logger.warning(f"Unknown action '{action}' - allowing by default")
            return True, None
        
        config = self.limits[action]
        key = (user_id, action)
        
        async with self.lock:
            # Clean up old entries
            await self._cleanup_old_entries(key, config.window_seconds)
            
            # Check if user has exceeded the limit
            current_requests = len(self.user_requests[key])
            
            if current_requests >= config.max_requests:
                # Calculate retry time
                oldest_request = self.user_requests[key][0]
                retry_after = config.window_seconds - (time.time() - oldest_request.timestamp)
                
                self.stats["rate_limited_requests"] += 1
                logger.warning(
                    f"Rate limit exceeded for user {user_id}, action '{action}'. "
                    f"Retry after {retry_after:.1f} seconds"
                )
                
                return False, max(0, retry_after)
            
            # Add current request
            self.user_requests[key].append(
                RateLimitEntry(
                    timestamp=time.time(),
                    user_id=user_id,
                    action=action
                )
            )
            
            self.stats["total_requests"] += 1
            return True, None
    
    async def _cleanup_old_entries(self, key: Tuple[int, str], window_seconds: int):
        """Remove old rate limit entries."""
        if key not in self.user_requests:
            return
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Remove entries older than the window
        while (self.user_requests[key] and 
               self.user_requests[key][0].timestamp < cutoff_time):
            self.user_requests[key].popleft()
    
    async def cleanup_all_old_entries(self):
        """Clean up all old entries for all users and actions."""
        async with self.lock:
            current_time = time.time()
            
            for action, config in self.limits.items():
                cutoff_time = current_time - config.window_seconds
                
                # Find all keys for this action
                keys_to_clean = [
                    key for key in self.user_requests.keys() 
                    if key[1] == action
                ]
                
                for key in keys_to_clean:
                    while (self.user_requests[key] and 
                           self.user_requests[key][0].timestamp < cutoff_time):
                        self.user_requests[key].popleft()
            
            self.stats["cleanup_runs"] += 1
    
    def get_user_stats(self, user_id: int) -> Dict[str, Dict]:
        """Get rate limit statistics for a specific user."""
        stats = {}
        
        for action, config in self.limits.items():
            key = (user_id, action)
            current_requests = len(self.user_requests.get(key, []))
            
            stats[action] = {
                "current_requests": current_requests,
                "max_requests": config.max_requests,
                "window_seconds": config.window_seconds,
                "remaining": max(0, config.max_requests - current_requests),
                "description": config.description
            }
        
        return stats
    
    def get_global_stats(self) -> Dict:
        """Get global rate limiter statistics."""
        total_users = len(set(key[0] for key in self.user_requests.keys()))
        total_actions = len(set(key[1] for key in self.user_requests.keys()))
        
        return {
            "total_requests": self.stats["total_requests"],
            "rate_limited_requests": self.stats["rate_limited_requests"],
            "cleanup_runs": self.stats["cleanup_runs"],
            "total_users": total_users,
            "total_actions": total_actions,
            "active_limits": len(self.limits),
            "rate_limit_percentage": (
                (self.stats["rate_limited_requests"] / max(1, self.stats["total_requests"])) * 100
            )
        }
    
    def reset_user(self, user_id: int, action: Optional[str] = None):
        """Reset rate limit for a specific user and action."""
        if action:
            key = (user_id, action)
            if key in self.user_requests:
                del self.user_requests[key]
                logger.info(f"Reset rate limit for user {user_id}, action '{action}'")
        else:
            # Reset all actions for the user
            keys_to_remove = [key for key in self.user_requests.keys() if key[0] == user_id]
            for key in keys_to_remove:
                del self.user_requests[key]
            logger.info(f"Reset all rate limits for user {user_id}")


class RateLimitDecorator:
    """Decorator for applying rate limiting to functions."""
    
    def __init__(self, rate_limiter: RateLimiter, action: str):
        """
        Initialize the decorator.
        
        Args:
            rate_limiter: RateLimiter instance
            action: Action name for rate limiting
        """
        self.rate_limiter = rate_limiter
        self.action = action
    
    def __call__(self, func):
        """Apply rate limiting to the function."""
        async def wrapper(*args, **kwargs):
            # Extract user_id from the first argument (usually interaction or context)
            user_id = None
            
            # Try to get user_id from different argument types
            if args and hasattr(args[0], 'user'):
                user_id = args[0].user.id
            elif args and hasattr(args[0], 'author'):
                user_id = args[0].author.id
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            elif 'interaction' in kwargs:
                user_id = kwargs['interaction'].user.id
            
            if user_id is None:
                logger.warning(f"Could not extract user_id for rate limiting in {func.__name__}")
                return await func(*args, **kwargs)
            
            # Check rate limit
            is_allowed, retry_after = await self.rate_limiter.is_allowed(user_id, self.action)
            
            if not is_allowed:
                raise RateLimitExceededError(
                    f"Rate limit exceeded for action '{self.action}'. "
                    f"Retry after {retry_after:.1f} seconds"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper


class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter()
    return _global_rate_limiter


def rate_limit(action: str):
    """Decorator for rate limiting functions."""
    def decorator(func):
        return RateLimitDecorator(get_rate_limiter(), action)(func)
    return decorator


# Background cleanup task
async def cleanup_rate_limits():
    """Background task to clean up old rate limit entries."""
    rate_limiter = get_rate_limiter()
    
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            await rate_limiter.cleanup_all_old_entries()
            
            # Log statistics periodically
            stats = rate_limiter.get_global_stats()
            if stats["total_requests"] > 0:
                logger.debug(
                    f"Rate limiter stats: {stats['total_requests']} requests, "
                    f"{stats['rate_limited_requests']} rate limited "
                    f"({stats['rate_limit_percentage']:.1f}%)"
                )
                
        except Exception as e:
            logger.error(f"Error in rate limit cleanup: {e}")


if __name__ == "__main__":
    # Test the rate limiter
    async def test_rate_limiter():
        limiter = RateLimiter()
        
        # Test basic rate limiting
        user_id = 123456789
        
        # Should allow first 5 requests
        for i in range(5):
            allowed, retry_after = await limiter.is_allowed(user_id, "bet_placement")
            print(f"Request {i+1}: Allowed={allowed}, Retry after={retry_after}")
        
        # 6th request should be rate limited
        allowed, retry_after = await limiter.is_allowed(user_id, "bet_placement")
        print(f"Request 6: Allowed={allowed}, Retry after={retry_after}")
        
        # Test user stats
        stats = limiter.get_user_stats(user_id)
        print(f"User stats: {stats}")
        
        # Test global stats
        global_stats = limiter.get_global_stats()
        print(f"Global stats: {global_stats}")
    
    asyncio.run(test_rate_limiter()) 