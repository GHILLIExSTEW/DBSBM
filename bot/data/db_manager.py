from bot.config.database_mysql import (
    MYSQL_DB,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiomysql
import os

from bot.config.leagues import LEAGUE_CONFIG, LEAGUE_IDS
from bot.data.game_utils import get_league_abbreviation, normalize_team_name
from bot.utils.enhanced_cache_manager import EnhancedCacheManager
from bot.services.performance_monitor import record_query, time_operation

logger = logging.getLogger(__name__)


if not MYSQL_DB:
    logger.critical(
        "CRITICAL ERROR: MYSQL_DB environment variable is not set.")
    logger.critical(
        "Please set MYSQL_DB in your .env file or environment variables.")
    logger.critical("Example: MYSQL_DB=betting_bot")
logging.getLogger("aiomysql").setLevel(logging.WARNING)


class DatabaseManager:
    """Manages the connection pool and executes queries against the MySQL DB."""

    def __init__(self):
        """Initializes the DatabaseManager."""
        self._pool: Optional[aiomysql.Pool] = None
        self.db_name = MYSQL_DB
        self.cache_manager = EnhancedCacheManager()

        # Configurable pool settings from environment variables
        self.pool_min_size = int(os.getenv("MYSQL_POOL_MIN_SIZE", "1"))
        self.pool_max_size = int(os.getenv("MYSQL_POOL_MAX_SIZE", "10"))
        self.pool_max_overflow = int(os.getenv("MYSQL_POOL_MAX_OVERFLOW", "5"))
        self.pool_timeout = int(os.getenv("MYSQL_POOL_TIMEOUT", "30"))
        self.connect_timeout = int(os.getenv("MYSQL_CONNECT_TIMEOUT", "30"))

        # Query caching settings
        self.default_cache_ttl = int(
            os.getenv("DB_CACHE_TTL", "600"))  # 10 minutes
        self.enable_query_cache = os.getenv(
            "DB_ENABLE_QUERY_CACHE", "true").lower() == "true"
        self.query_cache_prefix = "db_query"

        # Performance monitoring settings
        self.slow_query_threshold = float(
            os.getenv("DB_SLOW_QUERY_THRESHOLD", "1.0"))  # 1 second
        self.enable_query_logging = os.getenv(
            "DB_ENABLE_QUERY_LOGGING", "true").lower() == "true"

        # Validate environment variables on initialization
        missing_vars = []
        if not MYSQL_HOST:
            missing_vars.append("MYSQL_HOST")
        if not MYSQL_USER:
            missing_vars.append("MYSQL_USER")
        if not MYSQL_PASSWORD:
            missing_vars.append("MYSQL_PASSWORD")
        if not self.db_name:
            missing_vars.append("MYSQL_DB")

        if missing_vars:
            logger.critical(
                f"Missing required MySQL environment variables: {', '.join(missing_vars)}"
            )
            logger.critical(
                "Please set all required variables in your .env file:")
            logger.critical("MYSQL_HOST=localhost")
            logger.critical("MYSQL_USER=your_username")
            logger.critical("MYSQL_PASSWORD=your_password")
            logger.critical("MYSQL_DB=your_database_name")
            raise ValueError(
                f"Missing required MySQL environment variables: {', '.join(missing_vars)}"
            )

        logger.info("MySQL DatabaseManager initialized successfully.")
        logger.debug(
            f"Database configuration: Host={MYSQL_HOST}, Port={MYSQL_PORT}, DB={self.db_name}, User={MYSQL_USER}"
        )
        logger.debug(
            f"Pool configuration: min_size={self.pool_min_size}, max_size={self.pool_max_size}, "
            f"max_overflow={self.pool_max_overflow}, timeout={self.pool_timeout}"
        )
        logger.debug(
            f"Cache configuration: enabled={self.enable_query_cache}, ttl={self.default_cache_ttl}s"
        )

    async def connect(self) -> Optional[aiomysql.Pool]:
        """Create or return existing MySQL connection pool."""
        if self._pool is None:
            logger.info("Attempting to create MySQL connection pool...")
            max_retries = 3
            retry_delay = 5  # seconds
            last_error = None

            # Initialize cache manager
            try:
                await self.cache_manager.connect()
                logger.info("Cache manager connected successfully.")
            except Exception as e:
                logger.warning(f"Failed to connect cache manager: {e}")

            for attempt in range(max_retries):
                try:
                    self._pool = await aiomysql.create_pool(
                        host=MYSQL_HOST,
                        port=MYSQL_PORT,
                        user=MYSQL_USER,
                        password=MYSQL_PASSWORD,
                        db=self.db_name,
                        minsize=self.pool_min_size,
                        maxsize=self.pool_max_size,
                        autocommit=True,
                        echo=False,
                        pool_recycle=3600,  # Recycle connections every hour
                        connect_timeout=self.connect_timeout,
                    )
                    logger.info("MySQL connection pool created successfully.")
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed to create MySQL pool: {e}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff

            if self._pool is None:
                logger.error(
                    f"Failed to create MySQL connection pool after {max_retries} attempts."
                )
                raise ConnectionError(
                    f"Failed to create MySQL connection pool: {last_error}"
                )

        return self._pool

    async def close(self):
        """Close the MySQL connection pool."""
        if self._pool:
            logger.info("Closing MySQL connection pool...")
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            logger.info("MySQL connection pool closed.")

        # Disconnect cache manager
        try:
            await self.cache_manager.disconnect()
            logger.info("Cache manager disconnected successfully.")
        except Exception as e:
            logger.warning(f"Error disconnecting cache manager: {e}")

    def _generate_cache_key(self, query: str, args: Tuple) -> str:
        """Generate a cache key for a query and its arguments."""
        query_hash = hash(query + str(args))
        return f"{self.query_cache_prefix}:{query_hash}"

    def _should_cache_query(self, query: str) -> bool:
        """Determine if a query should be cached based on its type."""
        if not self.enable_query_cache:
            return False

        # Don't cache write operations
        query_upper = query.strip().upper()
        if any(keyword in query_upper for keyword in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER']):
            return False

        # Don't cache queries with NOW() or similar time functions
        if any(func in query_upper for func in ['NOW()', 'CURRENT_TIMESTAMP', 'RAND()']):
            return False

        return True

    async def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result from the enhanced cache manager."""
        try:
            return await self.cache_manager.get("database", cache_key)
        except Exception as e:
            logger.warning(f"Error getting cached result: {e}")
            return None

    async def _set_cached_result(self, cache_key: str, result: Any, ttl: int = None) -> None:
        """Set cached result in the enhanced cache manager."""
        try:
            ttl = ttl or self.default_cache_ttl
            await self.cache_manager.set("database", cache_key, result, ttl=ttl)
        except Exception as e:
            logger.warning(f"Error setting cached result: {e}")

    async def _invalidate_cache_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching a pattern."""
        try:
            await self.cache_manager.clear_prefix("database", pattern)
            logger.debug(f"Invalidated cache pattern: {pattern}")
        except Exception as e:
            logger.warning(f"Error invalidating cache pattern {pattern}: {e}")

    @time_operation("db_execute")
    async def execute(self, query: str, *args) -> Tuple[Optional[int], Optional[int]]:
        """Execute a query and return affected rows and last insert ID."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot execute: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        if self.enable_query_logging:
            logger.debug("Executing DB Query: %s Args: %s", query, args)

        start_time = time.time()

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    affected_rows = cursor.rowcount
                    last_insert_id = cursor.lastrowid

                    execution_time = time.time() - start_time
                    record_query(query, execution_time,
                                 success=True, rows_affected=affected_rows)

                    # Invalidate cache for write operations
                    if self.enable_query_cache and any(keyword in query.strip().upper()
                                                       for keyword in ['INSERT', 'UPDATE', 'DELETE']):
                        await self._invalidate_cache_pattern("db_query")

                    # Log slow queries
                    if execution_time > self.slow_query_threshold:
                        logger.warning(
                            f"Slow query detected: {query[:100]}... (took {execution_time:.3f}s)"
                        )

                    return affected_rows, last_insert_id
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time,
                         success=False, error_message=str(e))

            logger.error(
                "[DB EXECUTE] Error executing query: %s Args: %s. Error: %s",
                query,
                args,
                str(e),
                exc_info=True,
            )
            raise

    @time_operation("db_executemany")
    async def executemany(self, query: str, args_list: List[Tuple]) -> Optional[int]:
        """Execute a query multiple times with different arguments."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot executemany: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if self.enable_query_logging:
            logger.debug("Executing Many DB Query: %s Batch size: %s",
                         query, len(args_list))

        start_time = time.time()

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.executemany(query, args_list)
                    affected_rows = cursor.rowcount

                    execution_time = time.time() - start_time
                    record_query(query, execution_time,
                                 success=True, rows_affected=affected_rows)

                    # Invalidate cache for write operations
                    if self.enable_query_cache and any(keyword in query.strip().upper()
                                                       for keyword in ['INSERT', 'UPDATE', 'DELETE']):
                        await self._invalidate_cache_pattern("db_query")

                    # Log slow queries
                    if execution_time > self.slow_query_threshold:
                        logger.warning(
                            f"Slow batch query detected: {query[:100]}... (took {execution_time:.3f}s, {len(args_list)} items)"
                        )

                    return affected_rows
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time,
                         success=False, error_message=str(e))

            logger.error(
                "[DB EXECUTEMANY] Error executing batch query: %s",
                str(e),
                exc_info=True,
            )
            logger.error("[DB EXECUTEMANY] Query that failed: %s", query)
            logger.error(
                "[DB EXECUTEMANY] Batch size that failed: %s", len(args_list))
            return None

    @time_operation("db_fetch_one")
    async def fetch_one(self, query: str, *args, cache_ttl: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetch one row as a dictionary with enhanced caching support."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetch_one: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        # Generate cache key and check cache
        cache_key = self._generate_cache_key(query, args)
        cache_hit = False

        if self._should_cache_query(query):
            cached_result = await self._get_cached_result(cache_key)
            if cached_result is not None:
                if self.enable_query_logging:
                    logger.debug(f"Cache HIT for fetch_one: {query[:50]}...")
                cache_hit = True
                record_query(query, 0.0, success=True, cache_hit=True)
                return cached_result

        if self.enable_query_logging:
            logger.debug("Fetching One DB Query: %s Args: %s", query, args)

        start_time = time.time()

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, args)
                    result = await cursor.fetchone()

                    execution_time = time.time() - start_time
                    record_query(query, execution_time,
                                 success=True, cache_hit=cache_hit)

                    # Cache the result if appropriate
                    if self._should_cache_query(query) and result is not None:
                        await self._set_cached_result(cache_key, result, cache_ttl)

                    # Log slow queries
                    if execution_time > self.slow_query_threshold:
                        logger.warning(
                            f"Slow fetch_one query detected: {query[:100]}... (took {execution_time:.3f}s)"
                        )

                    return result
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time,
                         success=False, error_message=str(e))

            logger.error(
                "Error fetching one row: %s Args: %s. Error: %s",
                query,
                args,
                e,
                exc_info=True,
            )
            return None

    @time_operation("db_fetch_all")
    async def fetch_all(self, query: str, *args, cache_ttl: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all rows as a list of dictionaries with enhanced caching support."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetch_all: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        # Generate cache key and check cache
        cache_key = self._generate_cache_key(query, args)
        cache_hit = False

        if self._should_cache_query(query):
            cached_result = await self._get_cached_result(cache_key)
            if cached_result is not None:
                if self.enable_query_logging:
                    logger.debug(f"Cache HIT for fetch_all: {query[:50]}...")
                cache_hit = True
                record_query(query, 0.0, success=True, cache_hit=True)
                return cached_result

        if self.enable_query_logging:
            logger.debug("Fetching All DB Query: %s Args: %s", query, args)

        start_time = time.time()

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, args)
                    result = await cursor.fetchall()

                    execution_time = time.time() - start_time
                    record_query(query, execution_time,
                                 success=True, cache_hit=cache_hit)

                    # Cache the result if appropriate
                    if self._should_cache_query(query) and result:
                        await self._set_cached_result(cache_key, result, cache_ttl)

                    # Log slow queries
                    if execution_time > self.slow_query_threshold:
                        logger.warning(
                            f"Slow fetch_all query detected: {query[:100]}... (took {execution_time:.3f}s, {len(result)} rows)"
                        )

                    return result
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time,
                         success=False, error_message=str(e))

            logger.error(
                "Error fetching all rows: %s Args: %s. Error: %s",
                query,
                args,
                e,
                exc_info=True,
            )
            return []

    @time_operation("db_fetchval")
    async def fetchval(self, query: str, *args, cache_ttl: Optional[int] = None) -> Optional[Any]:
        """Fetch a single value from the first row with enhanced caching support."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetchval: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        # Generate cache key and check cache
        cache_key = self._generate_cache_key(query, args)
        cache_hit = False

        if self._should_cache_query(query):
            cached_result = await self._get_cached_result(cache_key)
            if cached_result is not None:
                if self.enable_query_logging:
                    logger.debug(f"Cache HIT for fetchval: {query[:50]}...")
                cache_hit = True
                record_query(query, 0.0, success=True, cache_hit=True)
                return cached_result

        if self.enable_query_logging:
            logger.debug("Fetching Value DB Query: %s Args: %s", query, args)

        start_time = time.time()

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.Cursor) as cursor:
                    await cursor.execute(query, args)
                    row = await cursor.fetchone()
                    result = row[0] if row else None

                    execution_time = time.time() - start_time
                    record_query(query, execution_time,
                                 success=True, cache_hit=cache_hit)

                    # Cache the result if appropriate
                    if self._should_cache_query(query) and result is not None:
                        await self._set_cached_result(cache_key, result, cache_ttl)

                    # Log slow queries
                    if execution_time > self.slow_query_threshold:
                        logger.warning(
                            f"Slow fetchval query detected: {query[:100]}... (took {execution_time:.3f}s)"
                        )

                    return result
        except Exception as e:
            execution_time = time.time() - start_time
            record_query(query, execution_time,
                         success=False, error_message=str(e))

            logger.error(
                "Error fetching value: %s Args: %s. Error: %s",
                query,
                args,
                e,
                exc_info=True,
            )
            return None

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get database cache statistics."""
        try:
            stats = await self.cache_manager.get_stats()
            return {
                "cache_hits": stats.get("hits", 0),
                "cache_misses": stats.get("misses", 0),
                "cache_size": stats.get("size", 0),
                "cache_ttl": stats.get("ttl", 0),
                "query_cache_enabled": self.enable_query_cache,
                "default_cache_ttl": self.default_cache_ttl
            }
        except Exception as e:
            logger.error(f"Error getting database cache stats: {e}")
            return {}

    async def clear_query_cache(self) -> None:
        """Clear all database query cache."""
        try:
            await self.cache_manager.clear_prefix("database", "db_query")
            logger.info("Database query cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing database query cache: {e}")

    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get database connection pool statistics."""
        if not self._pool:
            return {"pool_status": "not_initialized"}

        try:
            return {
                "pool_status": "active",
                "pool_size": self._pool.size,
                "pool_free_size": self._pool.freesize,
                "pool_min_size": self.pool_min_size,
                "pool_max_size": self.pool_max_size,
                "pool_max_overflow": self.pool_max_overflow,
                "pool_timeout": self.pool_timeout
            }
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {"pool_status": "error", "error": str(e)}

    async def table_exists(self, conn, table_name: str) -> bool:
        """Check if a table exists in the database."""
        async with conn.cursor(aiomysql.Cursor) as cursor:
            try:
                await cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = %s AND table_name = %s",
                    (self.db_name, table_name),
                )
                result = await cursor.fetchone()
                return result[0] > 0 if result else False
            except Exception as e:
                logger.error(
                    "Error checking if table '%s' exists: %s",
                    table_name,
                    e,
                    exc_info=True,
                )
                raise

    async def _check_and_add_column(
        self,
        cursor,
        table_name,
        column_name,
        column_definition,
        after: Optional[str] = None,
    ):
        """Checks if a column exists and adds it if not, optionally after a specified column."""
        async with cursor.connection.cursor(aiomysql.DictCursor) as dict_cursor:
            await dict_cursor.execute(
                f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,)
            )
            exists = await dict_cursor.fetchone()

        if not exists:
            logger.info("Adding column '%s' to table '%s'...",
                        column_name, table_name)
            alter_statement = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_definition}"
            if after:
                alter_statement += f" AFTER `{after}`"
            try:
                await cursor.execute(alter_statement)
                logger.info("Successfully added column '%s'.", column_name)
            except aiomysql.Error as e:
                logger.error(
                    "Failed to add column '%s' to table '%s': %s",
                    column_name,
                    table_name,
                    e,
                    exc_info=True,
                )
                raise
        else:
            logger.debug("Column '%s' already exists in '%s'.",
                         column_name, table_name)

    async def _create_users_table(self, cursor) -> None:
        """Create the users table if it doesn't exist."""
        if not await self.table_exists(self._get_connection(), "users"):
            await cursor.execute(
                """
                CREATE TABLE users (
                    user_id BIGINT PRIMARY KEY COMMENT 'Discord User ID',
                    username VARCHAR(100) NULL COMMENT 'Last known Discord username',
                    balance DECIMAL(15, 2) DEFAULT 1000.00 NOT NULL,
                    frozen_balance DECIMAL(15, 2) DEFAULT 0.00 NOT NULL,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            )
            logger.info("Table 'users' created.")

    async def _create_games_table(self, cursor) -> None:
        """Create the games table if it doesn't exist."""
        if not await self.table_exists(self._get_connection(), "games"):
            await cursor.execute(
                """
                CREATE TABLE games (
                    id BIGINT PRIMARY KEY COMMENT 'API Fixture ID',
                    sport VARCHAR(50) NOT NULL,
                    league_id BIGINT NULL, league_name VARCHAR(150) NULL,
                    home_team_id BIGINT NULL, away_team_id BIGINT NULL,
                    home_team_name VARCHAR(150) NULL, away_team_name VARCHAR(150) NULL,
                    home_team_logo VARCHAR(255) NULL, away_team_logo VARCHAR(255) NULL,
                    start_time TIMESTAMP NULL COMMENT 'Game start time in UTC',
                    end_time TIMESTAMP NULL COMMENT 'Game end time in UTC (if known)',
                    status VARCHAR(20) NULL COMMENT 'Game status (e.g., NS, LIVE, FT)',
                    score JSON NULL COMMENT 'JSON storing scores',
                    venue VARCHAR(150) NULL, referee VARCHAR(100) NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            )
            await cursor.execute(
                "CREATE INDEX idx_games_league_status_time ON games (league_id, status, start_time)"
            )
            await cursor.execute(
                "CREATE INDEX idx_games_start_time ON games (start_time)"
            )
            await cursor.execute(
                "CREATE INDEX idx_games_status ON games (status)"
            )
            logger.info("Table 'games' created.")

            # Add columns to games table
            await self._add_games_table_columns(cursor)

    async def _add_games_table_columns(self, cursor) -> None:
        """Add additional columns to the games table."""
        columns_to_add = [
            ("sport", "VARCHAR(50) NOT NULL COMMENT 'Sport key' AFTER id"),
            ("league_name", "VARCHAR(150) NULL AFTER league_id"),
            ("home_team_name", "VARCHAR(150) NULL AFTER away_team_id"),
            ("away_team_name", "VARCHAR(150) NULL AFTER home_team_name"),
            ("home_team_logo", "VARCHAR(255) NULL AFTER away_team_name"),
            ("away_team_logo", "VARCHAR(255) NULL AFTER home_team_logo"),
            ("end_time", "TIMESTAMP NULL COMMENT 'Game end time' AFTER start_time"),
            ("score", "JSON NULL COMMENT 'JSON scores' AFTER status"),
            ("venue", "VARCHAR(150) NULL AFTER score"),
            ("referee", "VARCHAR(100) NULL AFTER venue")
        ]

        for column_name, column_definition in columns_to_add:
            await self._check_and_add_column(cursor, "games", column_name, column_definition)

    async def _create_bets_table(self, cursor, conn) -> None:
        """Create the bets table if it doesn't exist."""
        if not await self.table_exists(conn, "bets"):
            await cursor.execute(
                """
                CREATE TABLE bets (
                    bet_serial BIGINT(20) NOT NULL AUTO_INCREMENT,
                    event_id VARCHAR(255) DEFAULT NULL,
                    guild_id BIGINT(20) NOT NULL,
                    message_id BIGINT(20) DEFAULT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    user_id BIGINT(20) NOT NULL,
                    game_id BIGINT(20) DEFAULT NULL,
                    bet_type VARCHAR(50) DEFAULT NULL,
                    player_prop VARCHAR(255) DEFAULT NULL,
                    player_id VARCHAR(50) DEFAULT NULL,
                    league VARCHAR(50) NOT NULL,
                    team VARCHAR(100) DEFAULT NULL,
                    opponent VARCHAR(50) DEFAULT NULL,
                    line VARCHAR(255) DEFAULT NULL,
                    odds DECIMAL(10,2) DEFAULT NULL,
                    units DECIMAL(10,2) NOT NULL,
                    legs INT(11) DEFAULT NULL,
                    bet_won TINYINT(4) DEFAULT 0,
                    bet_loss TINYINT(4) DEFAULT 0,
                    confirmed TINYINT(4) DEFAULT 0,
                    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                    game_start DATETIME DEFAULT NULL,
                    result_value DECIMAL(15,2) DEFAULT NULL,
                    result_description TEXT,
                    expiration_time TIMESTAMP NULL DEFAULT NULL,
                    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    channel_id BIGINT(20) DEFAULT NULL,
                    bet_details LONGTEXT NOT NULL,
                    PRIMARY KEY (bet_serial),
                    KEY guild_id (guild_id),
                    KEY user_id (user_id),
                    KEY status (status),
                    KEY created_at (created_at),
                    KEY game_id (game_id),
                    CONSTRAINT bets_ibfk_1 FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            )
            logger.info("Table 'bets' created.")

            await self._add_bets_table_columns(cursor, conn)

    async def _add_bets_table_columns(self, cursor, conn) -> None:
        """Add additional columns to the bets table."""
        columns_to_add = [
            ("bet_details", "LONGTEXT NOT NULL COMMENT 'JSON containing specific bet details'"),
            ("channel_id", "BIGINT(20) DEFAULT NULL COMMENT 'Channel where bet was posted'")
        ]

        for column_name, column_definition in columns_to_add:
            await self._check_and_add_column(cursor, "bets", column_name, column_definition)

        # Add foreign key constraint if missing
        await self._ensure_bets_foreign_key(conn)

    async def _ensure_bets_foreign_key(self, conn) -> None:
        """Ensure the foreign key constraint exists for bets table."""
        async with conn.cursor(aiomysql.DictCursor) as dict_cursor:
            await dict_cursor.execute(
                "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'bets' AND COLUMN_NAME = 'game_id' AND REFERENCED_TABLE_NAME = 'games'",
                (self.db_name,),
            )
            fk_exists = await dict_cursor.fetchone()
            if not fk_exists:
                logger.warning(
                    "Foreign key constraint 'bets_ibfk_1' for bets.game_id -> games.id missing. Attempting to add."
                )
                try:
                    await conn.cursor().execute(
                        "ALTER TABLE bets ADD CONSTRAINT bets_ibfk_1 FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL"
                    )
                    logger.info(
                        "Added foreign key constraint for bets.game_id.")
                except aiomysql.Error as fk_err:
                    logger.error(
                        "Failed to add foreign key constraint for bets.game_id: %s",
                        fk_err,
                        exc_info=True,
                    )

    async def _create_unit_records_table(self, cursor, conn) -> bool:
        """Create the unit_records table if it doesn't exist. Returns True if created."""
        if not await self.table_exists(conn, "unit_records"):
            await cursor.execute(
                """
                CREATE TABLE unit_records (
                    record_id INT AUTO_INCREMENT PRIMARY KEY,
                    bet_serial BIGINT NOT NULL COMMENT 'FK to bets.bet_serial',
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    year INT NOT NULL COMMENT 'Year bet resolved',
                    month INT NOT NULL COMMENT 'Month bet resolved (1-12)',
                    units DECIMAL(15, 2) NOT NULL COMMENT 'Original stake',
                    odds DECIMAL(10, 2) NOT NULL COMMENT 'Original odds',
                    monthly_result_value DECIMAL(15, 2) NOT NULL COMMENT 'Net units won/lost for the bet',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp bet resolved',
                    INDEX idx_unit_records_guild_user_ym (guild_id, user_id, year, month),
                    INDEX idx_unit_records_year_month (year, month),
                    INDEX idx_unit_records_user_id (user_id),
                    INDEX idx_unit_records_guild_id (guild_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            )
            logger.info("Table 'unit_records' created.")
            return True
        return False

    async def _ensure_unit_records_foreign_key(self, cursor, was_created: bool) -> None:
        """Ensure the foreign key constraint exists for unit_records table."""
        if was_created:
            logger.info(
                "Attempting to add foreign key constraint for newly created 'unit_records' table..."
            )
            try:
                await cursor.execute(
                    "ALTER TABLE unit_records ADD CONSTRAINT unit_records_ibfk_1 FOREIGN KEY (bet_serial) REFERENCES bets(bet_serial) ON DELETE CASCADE"
                )
                logger.info(
                    "Added foreign key constraint for unit_records.bet_serial.")
            except aiomysql.Error as fk_err:
                logger.error(
                    "Failed to add foreign key constraint for unit_records.bet_serial: %s",
                    fk_err,
                    exc_info=True,
                )

    async def _create_guild_settings_table(self, cursor) -> None:
        """Create the guild_settings table if it doesn't exist."""
        if not await self.table_exists(self._get_connection(), "guild_settings"):
            await cursor.execute(
                """
                CREATE TABLE guild_settings (
                    guild_id BIGINT PRIMARY KEY,
                    is_active BOOLEAN DEFAULT TRUE,
                    subscription_level INTEGER DEFAULT 0,
                    is_paid BOOLEAN DEFAULT FALSE,
                    embed_channel_1 BIGINT NULL,
                    embed_channel_2 BIGINT NULL,
                    command_channel_1 BIGINT NULL,
                    command_channel_2 BIGINT NULL,
                    admin_channel_1 BIGINT NULL,
                    admin_role BIGINT NULL,
                    authorized_role BIGINT NULL,
                    voice_channel_id BIGINT NULL COMMENT 'Monthly VC',
                    yearly_channel_id BIGINT NULL COMMENT 'Yearly VC',
                    total_units_channel_id BIGINT NULL,
                    daily_report_time TEXT NULL,
                    member_role BIGINT NULL,
                    bot_name_mask TEXT NULL,
                    bot_image_mask TEXT NULL,
                    guild_default_image TEXT NULL,
                    default_parlay_thumbnail TEXT NULL,
                    total_result_value DECIMAL(15, 2) DEFAULT 0.0,
                    min_units DECIMAL(15, 2) DEFAULT 0.1,
                    max_units DECIMAL(15, 2) DEFAULT 10.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            )
            logger.info("Table 'guild_settings' created.")

            await self._add_guild_settings_table_columns(cursor)

    async def _add_guild_settings_table_columns(self, cursor) -> None:
        """Add additional columns to the guild_settings table."""
        columns_to_add = [
            ("voice_channel_id", "BIGINT NULL COMMENT 'Monthly VC'"),
            ("yearly_channel_id", "BIGINT NULL COMMENT 'Yearly VC'"),
            ("total_units_channel_id", "BIGINT NULL"),
            ("daily_report_time", "TEXT NULL"),
            ("member_role", "BIGINT NULL"),
            ("bot_name_mask", "TEXT NULL"),
            ("bot_image_mask", "TEXT NULL"),
            ("guild_default_image", "TEXT NULL"),
            ("default_parlay_thumbnail", "TEXT NULL"),
            ("total_result_value", "DECIMAL(15, 2) DEFAULT 0.0"),
            ("min_units", "DECIMAL(15, 2) DEFAULT 0.1"),
            ("max_units", "DECIMAL(15, 2) DEFAULT 10.0")
        ]

        for column_name, column_definition in columns_to_add:
            await self._check_and_add_column(cursor, "guild_settings", column_name, column_definition)

    def _get_connection(self):
        """Get a connection for table existence checks."""
        # This is a placeholder - in practice, you'd need to implement this
        # based on how your connection pool is managed
        return None

    async def initialize_db(self):
        """Initializes the database schema."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot initialize DB: Connection pool unavailable.")
            return
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.Cursor) as cursor:
                    logger.info(
                        "Attempting to initialize/verify database schema...")

                    # Create tables in order of dependencies
                    await self._create_users_table(cursor)
                    await self._create_games_table(cursor)
                    await self._create_bets_table(cursor, conn)

                    # Create unit_records table and ensure foreign key
                    unit_records_created = await self._create_unit_records_table(cursor, conn)
                    await self._ensure_unit_records_foreign_key(cursor, unit_records_created)

                    await self._create_guild_settings_table(cursor)

                    logger.info(
                        "Database schema initialization completed successfully.")

        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise

    async def _column_exists(self, conn, table_name: str, column_name: str) -> bool:
        """Helper to check if a column exists."""
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s AND column_name = %s",
                (self.db_name, table_name, column_name),
            )
            return await cursor.fetchone() is not None

    async def save_game(
        self,
        game_id: str,
        league_id: str,
        league_name: str,
        home_team: str,
        away_team: str,
        start_time: str,
        status: str = "Scheduled",
    ):
        """Save a game to the games table."""
        try:
            if not status or str(status).lower() in ("none", "null", "", "n/a"):
                status = "scheduled"
            sport = (
                "Baseball"
                if league_id == "4424"
                else (
                    "Hockey"
                    if league_id == "4380"
                    else (
                        "Football"
                        if league_id == "4405"
                        else (
                            "Basketball"
                            if league_id == "4388"
                            else (
                                "Soccer"
                                if league_id
                                in ["4387", "4391", "4392", "4393", "4394", "4395"]
                                else (
                                    "Baseball"
                                    if league_id in ["4429", "4430"]
                                    else (
                                        "Basketball"
                                        if league_id == "4389"
                                        else (
                                            "Hockey" if league_id == "4431" else "Other"
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )

            query = """
                INSERT INTO games (
                    id, sport, league_id, league_name, home_team_name, away_team_name,
                    start_time, status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                ) ON DUPLICATE KEY UPDATE
                    sport = VALUES(sport),
                    league_id = VALUES(league_id),
                    league_name = VALUES(league_name),
                    home_team_name = VALUES(home_team_name),
                    away_team_name = VALUES(home_team_name),
                    start_time = VALUES(start_time),
                    status = VALUES(status),
                    updated_at = CURRENT_TIMESTAMP
            """
            await self.execute(
                query,
                (
                    game_id,
                    sport,
                    league_id,
                    league_name,
                    home_team,
                    away_team,
                    start_time,
                    status,
                ),
            )
            logger.info(
                "Saved game %s to database with status '%s' and league_name '%s'",
                game_id,
                status,
                league_name,
            )
            return True
        except Exception as e:
            logger.error("Error saving game %s: %s", game_id, e, exc_info=True)
            return False

    async def upsert_api_game(self, game: dict):
        """Upsert a full API game record, storing all fields in their respective columns."""
        season = game.get("season")
        if not season:
            season = datetime.now().year
            if game.get("sport", "").lower() == "baseball":
                current_month = datetime.now().month
                if current_month >= 10 or current_month <= 2:
                    season = season + 1

        # Support both flat and nested structures
        def safe_get_team(game, key):
            # Try nested structure first
            teams = game.get("teams")
            if teams and isinstance(teams, dict):
                team = teams.get(key)
                if team and isinstance(team, dict):
                    return team.get("name")
            # Fallback to flat
            return game.get(f"{key}_team_name") or game.get(f"{key}_name")

        home_team_name = safe_get_team(game, "home")
        away_team_name = safe_get_team(game, "away")

        query = """
            INSERT INTO api_games (
                api_game_id, sport, league_id, season, home_team_name, away_team_name,
                start_time, end_time, status, score, raw_json, fetched_at, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON DUPLICATE KEY UPDATE
                sport=VALUES(sport),
                league_id=VALUES(league_id),
                season=VALUES(season),
                home_team_name=VALUES(home_team_name),
                away_team_name=VALUES(away_team_name),
                start_time=VALUES(start_time),
                end_time=VALUES(end_time),
                status=VALUES(status),
                score=VALUES(score),
                raw_json=VALUES(raw_json),
                fetched_at=VALUES(fetched_at),
                updated_at=CURRENT_TIMESTAMP
        """
        params = (
            str(game.get("api_game_id") or game.get("id")),
            game.get("sport", ""),
            str(game.get("league_id", "")),
            season,
            home_team_name,
            away_team_name,
            game.get("start_time"),
            game.get("end_time"),
            game.get("status", ""),
            game.get("score"),
            (
                game.get("raw_json")
                if isinstance(game.get("raw_json"), str)
                else json.dumps(game.get("raw_json", {}))
            ),
            game.get(
                "fetched_at", datetime.now(
                    timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            ),
        )
        await self.execute(query, params)

    async def save_team(self, team: dict):
        """Insert or update a team record in the teams table."""
        query = """
            INSERT INTO teams (
                id, name, sport, code, country, founded, national, logo,
                venue_id, venue_name, venue_address, venue_city, venue_capacity, venue_surface, venue_image
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                name=VALUES(name), sport=VALUES(sport), code=VALUES(code), country=VALUES(country),
                founded=VALUES(founded), national=VALUES(national), logo=VALUES(logo),
                venue_id=VALUES(venue_id), venue_name=VALUES(venue_name), venue_address=VALUES(venue_address),
                venue_city=VALUES(venue_city), venue_capacity=VALUES(venue_capacity),
                venue_surface=VALUES(venue_surface), venue_image=VALUES(venue_image)
        """
        params = (
            team.get("id"),
            team.get("name"),
            team.get("sport"),
            team.get("code"),
            team.get("country"),
            team.get("founded"),
            int(team.get("national", False)),
            team.get("logo"),
            team.get("venue_id"),
            team.get("venue_name"),
            team.get("venue_address"),
            team.get("venue_city"),
            team.get("venue_capacity"),
            team.get("venue_surface"),
            team.get("venue_image"),
        )
        await self.execute(query, *params)

    async def sync_games_from_api(self, force_season: int = None):
        """Sync games from API to database."""
        try:
            from bot.api.sports_api import SportsAPI

            api = SportsAPI(self)
            current_date = datetime.now().strftime("%Y-%m-%d")
            for league_name, league_info in LEAGUE_IDS.items():
                sport = league_info.get("sport", "").lower()
                if not sport:
                    continue
                try:
                    season = None
                    if force_season and sport == "baseball" and league_name == "MLB":
                        season = force_season
                        logger.info("Using forced season %s for MLB", season)
                    elif sport == "baseball" and league_name == "MLB":
                        current_year = datetime.now().year
                        current_month = datetime.now().month
                        if current_month >= 10 or current_month <= 2:
                            season = current_year + 1
                            logger.info(
                                "MLB: In offseason, using next season %s", season
                            )
                        else:
                            season = current_year
                            logger.info(
                                "MLB: In season, using current season %s", season
                            )
                    else:
                        season = datetime.now().year
                        logger.info(
                            "Using current year %s for %s/%s",
                            season,
                            sport,
                            league_name,
                        )
                    games = await api.fetch_games(
                        sport=sport,
                        league=league_name,
                        date=current_date,
                        season=season,
                    )
                    logger.info(
                        "Fetched %d games for %s/%s", len(
                            games), sport, league_name
                    )
                    for game in games:
                        try:
                            game["season"] = season
                            await self.upsert_api_game(game)
                            logger.info(
                                "Saved game %s to database", game.get("id"))
                        except Exception as e:
                            logger.error(
                                "Error saving game %s: %s",
                                game.get("id"),
                                e,
                                exc_info=True,
                            )
                            continue
                except Exception as e:
                    logger.error(
                        "Error syncing games for %s: %s", league_name, e, exc_info=True
                    )
                    continue
        except Exception as e:
            logger.error("Error in sync_games_from_api: %s", e, exc_info=True)
            raise

    async def get_normalized_games_for_dropdown(
        self, league_name: str, season: int = None
    ) -> List[Dict[str, Any]]:
        """Fetch and normalize games for a league from the api_games table for use in a bet dropdown."""
        logger.info(
            "[get_normalized_games_for_dropdown] Starting fetch for league_name=%s, season=%s",
            league_name,
            season,
        )
        dropdown_games = [
            {
                "id": "manual",
                "api_game_id": "manual",
                "home_team": "Manual Entry",
                "away_team": "Manual Entry",
                "start_time": datetime.now(timezone.utc),
                "status": "Manual",
                "home_team_name": "Manual Entry",
                "away_team_name": "Manual Entry",
            }
        ]
        sport = None
        league_key = None
        for key, league_info in LEAGUE_IDS.items():
            if key == league_name:
                sport = league_info.get("sport", "").capitalize()
                league_key = key
                league_name = (
                    LEAGUE_CONFIG.get(league_info.get("sport", ""), {})
                    .get(key, {})
                    .get("name", key)
                )
                if league_name == "MLB":
                    league_name = "Major League Baseball"
                logger.info(
                    "[get_normalized_games_for_dropdown] Found league info: sport=%s, league_key=%s, league_name=%s",
                    sport,
                    league_key,
                    league_name,
                )
                break
        if not sport or not league_name:
            logger.warning(
                "[get_normalized_games_for_dropdown] Could not find sport and league name for league_name=%s",
                league_name,
            )
            return dropdown_games
        league_abbr = get_league_abbreviation(league_name)
        logger.info(
            "[get_normalized_games_for_dropdown] Looking up games for %s/%s (abbreviation: %s, key: %s)",
            sport,
            league_name,
            league_abbr,
            league_key,
        )
        logger.info(
            "[get_normalized_games_for_dropdown] Starting sync_games_from_api")
        await self.sync_games_from_api(force_season=season)
        logger.info(
            "[get_normalized_games_for_dropdown] Completed sync_games_from_api")
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        logger.info(
            "[get_normalized_games_for_dropdown] Using today_start=%s", today_start
        )
        if sport.lower() == "baseball":
            finished_statuses = [
                "Match Finished",
                "Finished",
                "FT",
                "Game Finished",
                "Final",
            ]
        else:
            finished_statuses = [
                "Match Finished",
                "Finished",
                "FT",
                "Ended",
                "Game Finished",
                "Final",
            ]
        logger.info(
            "[get_normalized_games_for_dropdown] Using finished_statuses=%s",
            finished_statuses,
        )
        query = """
            SELECT id, api_game_id, home_team_name, away_team_name, start_time, status, score, league_name
            FROM api_games
            WHERE sport = %s
            AND league_id = %s
            AND UPPER(league_name) = UPPER(%s)
            AND start_time >= %s
            AND status NOT IN (%s, %s, %s, %s, %s)
            AND season = %s
            ORDER BY start_time ASC LIMIT 100
        """
        from bot.config.leagues import LEAGUE_ID_MAP

        league_id = LEAGUE_ID_MAP.get(league_name, "1")
        logger.info(
            "[get_normalized_games_for_dropdown] Using league_id=%s", league_id)
        if sport.lower() == "baseball" and league_key == "MLB":
            current_year = datetime.now().year
            current_month = datetime.now().month
            if season is not None:
                logger.info(
                    "[get_normalized_games_for_dropdown] MLB: Using provided season %s",
                    season,
                )
                rows = await self.fetch_all(
                    query,
                    (sport, league_id, league_name, today_start)
                    + tuple(finished_statuses)
                    + (season,),
                )
            elif current_month >= 10 or current_month <= 2:
                next_year = current_year + 1
                logger.info(
                    "[get_normalized_games_for_dropdown] MLB: In offseason, checking %s",
                    next_year,
                )
                rows = await self.fetch_all(
                    query,
                    (sport, league_id, league_name, today_start)
                    + tuple(finished_statuses)
                    + (next_year,),
                )
            else:
                logger.info(
                    "[get_normalized_games_for_dropdown] MLB: In season, checking %s",
                    current_year,
                )
                rows = await self.fetch_all(
                    query,
                    (sport, league_id, league_name, today_start)
                    + tuple(finished_statuses)
                    + (current_year,),
                )
        else:
            season = season if season is not None else datetime.now().year
            logger.info(
                "[get_normalized_games_for_dropdown] Non-MLB: Using season %s", season
            )
            rows = await self.fetch_all(
                query,
                (sport, league_id, league_name, today_start)
                + tuple(finished_statuses)
                + (season,),
            )
        if not rows:
            logger.warning(
                "[get_normalized_games_for_dropdown] No active games found for sport=%s, league_id=%s, league_name=%s",
                sport,
                league_id,
                league_name,
            )
            return dropdown_games
        for row in rows:
            try:
                # Always use normalize_team_name for all leagues
                home_team = normalize_team_name(
                    row["home_team_name"], sport, league_key
                )
                away_team = normalize_team_name(
                    row["away_team_name"], sport, league_key
                )
                logger.info(
                    "[get_normalized_games_for_dropdown] Normalized teams %s -> %s, %s -> %s",
                    row["home_team_name"],
                    home_team,
                    row["away_team_name"],
                    away_team,
                )

                game_data = {
                    "id": row["id"],
                    "api_game_id": str(row["api_game_id"]),
                    "home_team": home_team,  # Use normalized name for display
                    "away_team": away_team,  # Use normalized name for display
                    "start_time": row["start_time"],
                    "status": row["status"],
                    "home_team_name": home_team,  # Store normalized name
                    "away_team_name": away_team,  # Store normalized name
                }
                dropdown_games.append(game_data)
                logger.info(
                    "[get_normalized_games_for_dropdown] Added game to dropdown: %s",
                    game_data,
                )
            except Exception as e:
                logger.error(
                    "[get_normalized_games_for_dropdown] Error processing game data for league_id=%s, sport=%s, league_name=%s: %s",
                    league_id,
                    sport,
                    league_name,
                    e,
                    exc_info=True,
                )
                continue
        logger.info(
            "[get_normalized_games_for_dropdown] Returning %d normalized games for dropdown (including manual entry)",
            len(dropdown_games),
        )
        return dropdown_games

    async def get_open_bets_by_guild(self, guild_id: int):
        """Fetch open bets for a guild."""
        logger.info("Fetching open bets for guild_id=%s", guild_id)
        query = """
            SELECT DISTINCT COALESCE(b.api_game_id, l.api_game_id) as api_game_id,
                   g.home_team_name, g.away_team_name, g.start_time, g.status,
                   g.score, g.id as game_id
            FROM bets b
            LEFT JOIN bet_legs l ON b.bet_type = 'parlay' AND l.bet_id = b.bet_serial
            JOIN api_games g ON COALESCE(b.api_game_id, l.api_game_id) = g.api_game_id
            WHERE b.guild_id = %s AND b.confirmed = 1
            AND (b.bet_type = 'game_line' OR l.bet_type = 'game_line')
            AND g.status NOT IN ('finished', 'Match Finished', 'Final', 'Ended')
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (guild_id,))
                rows = await cursor.fetchall()
                logger.info("Fetched %d open bets for guild_id=%s",
                            len(rows), guild_id)
                return rows

    async def _get_or_create_game(self, api_game_id: str) -> int:
        row = await self.fetch_one("SELECT id FROM games WHERE id = %s", (api_game_id,))
        if row:
            return row["id"]

        src = await self.fetch_one(
            """
            SELECT sport, league_id, home_team_name, away_team_name,
                   start_time, status
            FROM api_games
            WHERE api_game_id = %s
            """,
            (api_game_id,),
        )
        if not src:
            raise ValueError(f"No api_games row for {api_game_id}")

        # Insert USING api_game_id as the PK
        insert_q = """
          INSERT INTO games (
            id, sport, league_id, home_team_name, away_team_name,
            start_time, status, created_at
          ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, NOW()
          )
        """
        await self.execute(
            insert_q,
            (
                int(api_game_id),
                src["sport"],
                src["league_id"],
                src["home_team_name"],
                src["away_team_name"],
                src["start_time"],
                src["status"],
            ),
        )
        return int(api_game_id)

    @property
    def db(self):
        """Returns the MySQL connection pool."""
        if self._pool is None:
            raise RuntimeError(
                "Database connection pool is not initialized. Call connect() first."
            )
        return self._pool

    async def get_next_bet_serial(self) -> Optional[int]:
        """Fetch the next AUTO_INCREMENT value for the bets table (the next bet_serial to be used)."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot get next bet serial: DB pool unavailable.")
            return None
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SHOW TABLE STATUS LIKE 'bets'")
                    row = await cursor.fetchone()
                    if row and "Auto_increment" in row:
                        return int(row["Auto_increment"])
        except Exception as e:
            logger.error(f"Error fetching next bet serial: {e}", exc_info=True)
        return None
