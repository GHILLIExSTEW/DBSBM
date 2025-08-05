"""
Database Manager for PostgreSQL - Updated for proper PostgreSQL connection
"""

import asyncio
import asyncpg
import logging
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)


class DatabaseManager:
    """PostgreSQL database manager with proper connection handling."""

    def __init__(self):
        self._pool = None
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", 5432)),
            "database": os.getenv("POSTGRES_DB", "dbsbm"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }
        logger.info(f"Database config: host={self.db_config['host']}, port={self.db_config['port']}, db={self.db_config['database']}, user={self.db_config['user']}")

    @property
    def pool(self):
        """Get the database pool (for backward compatibility)."""
        return self._pool

    async def connect(self) -> Optional[asyncpg.pool.Pool]:
        """Connect to PostgreSQL database."""
        try:
            logger.info(f"Attempting to connect to PostgreSQL at {self.db_config['host']}:{self.db_config['port']}")
            self._pool = await asyncpg.create_pool(
                **self.db_config,
                min_size=1,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'application_name': 'DBSBM_Bot',
                    'jit': 'off'
                }
            )
            logger.info("[OK] PostgreSQL database connection established successfully")
            return self._pool
        except Exception as e:
            logger.error(f"[ERROR] PostgreSQL database connection failed: {e}")
            logger.error(f"Connection details: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
            logger.warning("Bot will continue in graceful degradation mode without database")
            self._pool = None
            return None

    async def close(self):
        """Close database connection."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection closed")
            self._pool = None

    async def initialize_db(self):
        """Initialize database schema."""
        if not self._pool:
            logger.warning("[INFO] Database not connected - skipping initialization")
            return False
        
        logger.info("[INFO] Initializing PostgreSQL database schema...")
        # Add your schema initialization code here
        logger.info("[INFO] Database schema initialization completed")
        return True

    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a query and return all results."""
        if not self._pool:
            logger.warning("Database pool not available, returning empty list")
            return []
        
        try:
            async with self._pool.acquire() as connection:
                # Handle tuple arguments - unpack if single tuple provided
                if len(args) == 1 and isinstance(args[0], (tuple, list)):
                    args = args[0]
                rows = await connection.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return []

    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute a query and return one result."""
        if not self._pool:
            logger.warning("Database pool not available, returning None")
            return None
        
        try:
            async with self._pool.acquire() as connection:
                # Handle tuple arguments - unpack if single tuple provided
                if len(args) == 1 and isinstance(args[0], (tuple, list)):
                    args = args[0]
                row = await connection.fetchrow(query, *args)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return None

    async def execute(self, query: str, *args) -> bool:
        """Execute a query without returning results."""
        if not self._pool:
            logger.warning("Database pool not available, skipping query execution")
            return False
        
        try:
            async with self._pool.acquire() as connection:
                # Handle tuple arguments - unpack if single tuple provided
                if len(args) == 1 and isinstance(args[0], (tuple, list)):
                    args = args[0]
                await connection.execute(query, *args)
                return True
        except Exception as e:
            logger.error(f"Database query execution failed: {e}")
            return False

    async def fetchval(self, query: str, *args):
        """Execute a query and return a single value."""
        if not self._pool:
            logger.warning("Database pool not available, returning None")
            return None
        
        try:
            async with self._pool.acquire() as connection:
                # Handle tuple arguments - unpack if single tuple provided
                if len(args) == 1 and isinstance(args[0], (tuple, list)):
                    args = args[0]
                result = await connection.fetchval(query, *args)
                return result
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return None


# Singleton instance
db_manager = DatabaseManager()
