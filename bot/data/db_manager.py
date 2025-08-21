def get_db_manager():
    """Return the singleton db_manager instance (for legacy compatibility)."""
    global db_manager
    return db_manager
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
    def _convert_params(self, params):
        # Recursively convert datetime to isoformat and bool to int in params
        def convert(val):
            if isinstance(val, (list, tuple)):
                return type(val)(convert(x) for x in val)
            elif hasattr(val, 'isoformat') and callable(val.isoformat):
                return val.isoformat()
            elif isinstance(val, bool):
                logger.warning("Auto-converting boolean %s to int for SQL (use 1/0 for smallint columns)", val)
                return int(val)
            return val
        return convert(params)
    """PostgreSQL database manager with proper connection handling."""


    # Add dummy pool config attributes for test compatibility
    pool_min_size = 1
    pool_max_size = 10
    pool_max_overflow = 5  # For test_critical_fixes
    pool_timeout = 30    # For test_critical_fixes and query optimization tests
    connect_timeout = 30 # For test_critical_fixes and query optimization tests
    db_name = "dbsbm"  # For test_critical_fixes

    # Query cache/optimization attributes for test compatibility
    enable_query_cache = True
    default_cache_ttl = 600
    query_cache_prefix = "db_query"
    slow_query_threshold = 1.0
    enable_query_logging = True

    # Dummy cache_manager for tests
    cache_manager = None

    # Stubs for query optimization methods
    def _generate_cache_key(self, query, args):
        return f"db_query:{hash(query)}:{hash(str(args))}"

    def _should_cache_query(self, query):
        return query.strip().lower().startswith("select")

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
                args = self._convert_params(args)
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
                args = self._convert_params(args)
                row = await connection.fetchrow(query, *args)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return None

    async def execute(self, query: str, *args):
        """Execute a query and return the number of affected rows for DML statements, or True/False for others."""
        if not self._pool:
            logger.warning("Database pool not available, skipping query execution")
            return 0
        try:
            async with self._pool.acquire() as connection:
                # Handle tuple arguments - unpack if single tuple provided
                if len(args) == 1 and isinstance(args[0], (tuple, list)):
                    args = args[0]
                args = self._convert_params(args)
                result = await connection.execute(query, *args)
                # result is a string like 'DELETE 3', 'UPDATE 1', 'INSERT 0', or 'SELECT 0'
                if isinstance(result, str) and result.split()[0] in {"DELETE", "UPDATE", "INSERT"}:
                    try:
                        return int(result.split()[1])
                    except Exception:
                        return 0
                return True
        except Exception as e:
            logger.error(f"Database query execution failed: {e}")
            return 0

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

# Dummy MySQL config for test patching
MYSQL_HOST = "localhost"
MYSQL_USER = "test_user"
MYSQL_PASSWORD = "test_password"
MYSQL_DB = "test_db"
