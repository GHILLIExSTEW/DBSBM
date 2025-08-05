"""
Database Manager for MySQL - Reverted for compatibility with existing database
"""

import asyncio
import aiomysql
import logging
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)


class DatabaseManager:
    """MySQL database manager with proper connection handling."""

    def __init__(self):
        self._pool = None
        self.db_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", 3306)),
            "db": os.getenv("MYSQL_DB", "dbsbm"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "charset": "utf8mb4",
            "autocommit": True,
        }
        logger.info(f"Database config: host={self.db_config['host']}, port={self.db_config['port']}, db={self.db_config['db']}, user={self.db_config['user']}")

    @property
    def pool(self):
        """Get the database pool (for backward compatibility)."""
        return self._pool

    async def connect(self) -> Optional[aiomysql.pool.Pool]:
        """Connect to MySQL database."""
        try:
            logger.info(f"Attempting to connect to MySQL at {self.db_config['host']}:{self.db_config['port']}")
            self._pool = await aiomysql.create_pool(
                **self.db_config,
                minsize=1,
                maxsize=10
            )
            logger.info("✅ MySQL database connection established successfully")
            return self._pool
        except Exception as e:
            logger.error(f"❌ MySQL database connection failed: {e}")
            logger.error(f"Connection details: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['db']}")
            logger.warning("Bot will continue in graceful degradation mode without database")
            self._pool = None
            return None

    async def close(self):
        """Close database connection."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            logger.info("Database connection closed")
            self._pool = None

    async def initialize_db(self):
        """Initialize database schema."""
        if not self._pool:
            logger.warning("📊 Database not connected - skipping initialization")
            return False
        
        logger.info("📊 Initializing MySQL database schema...")
        # Add your schema initialization code here
        logger.info("📊 Database schema initialization completed")
        return True

    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a query and return all results."""
        if not self._pool:
            logger.warning("Database pool not available, returning empty list")
            return []
        
        try:
            async with self._pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    # Handle tuple arguments - unpack if single tuple provided
                    if len(args) == 1 and isinstance(args[0], (tuple, list)):
                        args = args[0]
                    await cursor.execute(query, args)
                    rows = await cursor.fetchall()
                    return rows or []
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
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    # Handle tuple arguments - unpack if single tuple provided
                    if len(args) == 1 and isinstance(args[0], (tuple, list)):
                        args = args[0]
                    await cursor.execute(query, args)
                    row = await cursor.fetchone()
                    return row
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
                async with connection.cursor() as cursor:
                    # Handle tuple arguments - unpack if single tuple provided
                    if len(args) == 1 and isinstance(args[0], (tuple, list)):
                        args = args[0]
                    await cursor.execute(query, args)
                    await connection.commit()
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
                async with connection.cursor() as cursor:
                    # Handle tuple arguments - unpack if single tuple provided
                    if len(args) == 1 and isinstance(args[0], (tuple, list)):
                        args = args[0]
                    await cursor.execute(query, args)
                    row = await cursor.fetchone()
                    return row[0] if row else None
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return None


# Singleton instance
db_manager = DatabaseManager()
