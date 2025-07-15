import aiomysql
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
import os
import asyncio
import json
from config.leagues import LEAGUE_CONFIG, LEAGUE_IDS
from data.game_utils import (
    get_league_abbreviation,
    sanitize_team_name,
    normalize_team_name,
)
from datetime import datetime, timezone

try:
    from ..config.database_mysql import (
        MYSQL_HOST,
        MYSQL_PORT,
        MYSQL_USER,
        MYSQL_PASSWORD,
        MYSQL_DB,
        MYSQL_POOL_MIN_SIZE,
        MYSQL_POOL_MAX_SIZE,
    )
except ImportError:
    from config.database_mysql import (
        MYSQL_HOST,
        MYSQL_PORT,
        MYSQL_USER,
        MYSQL_PASSWORD,
        MYSQL_DB,
        MYSQL_POOL_MIN_SIZE,
        MYSQL_POOL_MAX_SIZE,
    )

if not MYSQL_DB:
    logger.critical("CRITICAL ERROR: MYSQL_DB environment variable is not set.")
    logger.critical("Please set MYSQL_DB in your .env file or environment variables.")
    logger.critical("Example: MYSQL_DB=betting_bot")

logger = logging.getLogger(__name__)
logging.getLogger("aiomysql").setLevel(logging.WARNING)


class DatabaseManager:
    """Manages the connection pool and executes queries against the MySQL DB."""

    def __init__(self):
        """Initializes the DatabaseManager."""
        self._pool: Optional[aiomysql.Pool] = None
        self.db_name = MYSQL_DB

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
            logger.critical("Please set all required variables in your .env file:")
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

    async def connect(self) -> Optional[aiomysql.Pool]:
        """Create or return existing MySQL connection pool."""
        if self._pool is None:
            logger.info("Attempting to create MySQL connection pool...")
            max_retries = 3
            retry_delay = 5  # seconds
            last_error = None

            for attempt in range(max_retries):
                try:
                    self._pool = await aiomysql.create_pool(
                        host=MYSQL_HOST,
                        port=MYSQL_PORT,
                        user=MYSQL_USER,
                        password=MYSQL_PASSWORD,
                        db=self.db_name,
                        minsize=1,
                        maxsize=5,
                        autocommit=True,
                        connect_timeout=30,
                        echo=False,
                        charset="utf8mb4",
                    )
                    async with self._pool.acquire() as conn:
                        async with conn.cursor() as cursor:
                            await cursor.execute("SELECT 1")
                    logger.info(
                        "MySQL connection pool created and tested successfully."
                    )
                    await self.initialize_db()
                    return self._pool
                except aiomysql.OperationalError as op_err:
                    last_error = op_err
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed to connect to MySQL: {op_err}"
                    )
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                except Exception as e:
                    last_error = e
                    logger.critical(
                        "FATAL: Failed to connect to MySQL: %s", e, exc_info=True
                    )
                    self._pool = None
                    raise ConnectionError(f"Failed to connect: {e}") from e

            if last_error:
                logger.critical("FATAL: All connection attempts failed")
                self._pool = None
                raise ConnectionError(
                    f"Failed to connect after {max_retries} attempts: {last_error}"
                ) from last_error

        return self._pool

    async def close(self):
        """Close the MySQL connection pool."""
        if self._pool is not None:
            logger.info("Closing MySQL connection pool...")
            try:
                self._pool.close()
                try:
                    await asyncio.wait_for(self._pool.wait_closed(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Timeout while waiting for MySQL pool to close")
                except RuntimeError as e:
                    if "Event loop is closed" in str(e):
                        logger.warning(
                            "Event loop was closed before pool could be properly closed"
                        )
                    else:
                        raise
                finally:
                    self._pool = None
                    logger.info("MySQL connection pool closed.")
            except Exception as e:
                logger.error("Error closing MySQL pool: %s", e)
                self._pool = None

    async def execute(self, query: str, *args) -> Tuple[Optional[int], Optional[int]]:
        """Execute INSERT, UPDATE, DELETE. Returns (rowcount, lastrowid)."""
        pool = await self.connect()
        if not pool:
            logger.error("[DB EXECUTE] Cannot execute: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        flat_args = (
            tuple(args[0])
            if len(args) == 1 and isinstance(args[0], (tuple, list))
            else args
        )

        logger.info("[DB EXECUTE] Starting query execution")
        logger.debug("[DB EXECUTE] Query: %s", query)
        logger.debug("[DB EXECUTE] Args: %s", flat_args)

        last_id = None
        rowcount = None
        try:
            async with pool.acquire() as conn:
                logger.debug("[DB EXECUTE] Acquired connection from pool")
                async with conn.cursor() as cursor:
                    logger.debug("[DB EXECUTE] Executing query...")
                    rowcount = await cursor.execute(query, flat_args)
                    logger.info("[DB EXECUTE] Query executed. Rowcount: %s", rowcount)

                    if (
                        rowcount is not None
                        and rowcount > 0
                        and query.strip().upper().startswith("INSERT")
                    ):
                        last_id = cursor.lastrowid
                        logger.info(
                            "[DB EXECUTE] Insert successful. Last ID: %s", last_id
                        )

                    if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                        logger.debug("[DB EXECUTE] Committing transaction...")
                        await conn.commit()
                        logger.info("[DB EXECUTE] Transaction committed successfully")

            logger.info(
                "[DB EXECUTE] Query execution completed. Rowcount: %s, Last ID: %s",
                rowcount,
                last_id,
            )
            return rowcount, last_id
        except Exception as e:
            logger.error(
                "[DB EXECUTE] Error executing query: %s", str(e), exc_info=True
            )
            logger.error("[DB EXECUTE] Query that failed: %s", query)
            logger.error("[DB EXECUTE] Args that failed: %s", flat_args)
            return None, None

    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch one row as a dictionary."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetch_one: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        logger.debug("Fetching One DB Query: %s Args: %s", query, args)
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, args)
                    return await cursor.fetchone()
        except Exception as e:
            logger.error(
                "Error fetching one row: %s Args: %s. Error: %s",
                query,
                args,
                e,
                exc_info=True,
            )
            return None

    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch all rows as a list of dictionaries."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetch_all: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        logger.debug("Fetching All DB Query: %s Args: %s", query, args)
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, args)
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(
                "Error fetching all rows: %s Args: %s. Error: %s",
                query,
                args,
                e,
                exc_info=True,
            )
            return []

    async def fetchval(self, query: str, *args) -> Optional[Any]:
        """Fetch a single value from the first row."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetchval: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        logger.debug("Fetching Value DB Query: %s Args: %s", query, args)
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.Cursor) as cursor:
                    await cursor.execute(query, args)
                    row = await cursor.fetchone()
                    return row[0] if row else None
        except Exception as e:
            logger.error(
                "Error fetching value: %s Args: %s. Error: %s",
                query,
                args,
                e,
                exc_info=True,
            )
            return None

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
            logger.info("Adding column '%s' to table '%s'...", column_name, table_name)
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
            logger.debug("Column '%s' already exists in '%s'.", column_name, table_name)

    async def initialize_db(self):
        """Initializes the database schema."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot initialize DB: Connection pool unavailable.")
            return
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.Cursor) as cursor:
                    logger.info("Attempting to initialize/verify database schema...")

                    # --- Users Table ---
                    if not await self.table_exists(conn, "users"):
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

                    # --- Games Table ---
                    if not await self.table_exists(conn, "games"):
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

                        await self._check_and_add_column(
                            cursor,
                            "games",
                            "sport",
                            "VARCHAR(50) NOT NULL COMMENT 'Sport key' AFTER id",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "games",
                            "league_name",
                            "VARCHAR(150) NULL AFTER league_id",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "games",
                            "home_team_name",
                            "VARCHAR(150) NULL AFTER away_team_id",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "games",
                            "away_team_name",
                            "VARCHAR(150) NULL AFTER home_team_name",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "games",
                            "home_team_logo",
                            "VARCHAR(255) NULL AFTER away_team_name",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "games",
                            "away_team_logo",
                            "VARCHAR(255) NULL AFTER home_team_logo",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "games",
                            "end_time",
                            "TIMESTAMP NULL COMMENT 'Game end time' AFTER start_time",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "games",
                            "score",
                            "JSON NULL COMMENT 'JSON scores' AFTER status",
                        )
                        await self._check_and_add_column(
                            cursor, "games", "venue", "VARCHAR(150) NULL AFTER score"
                        )
                        await self._check_and_add_column(
                            cursor, "games", "referee", "VARCHAR(100) NULL AFTER venue"
                        )

                    # --- Bets Table ---
                    bets_table_created = False
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
                        bets_table_created = True

                        await self._check_and_add_column(
                            cursor,
                            "bets",
                            "bet_details",
                            "LONGTEXT NOT NULL COMMENT 'JSON containing specific bet details'",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "bets",
                            "channel_id",
                            "BIGINT(20) DEFAULT NULL COMMENT 'Channel where bet was posted'",
                        )
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
                                    await cursor.execute(
                                        "ALTER TABLE bets ADD CONSTRAINT bets_ibfk_1 FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL"
                                    )
                                    logger.info(
                                        "Added foreign key constraint for bets.game_id."
                                    )
                                except aiomysql.Error as fk_err:
                                    logger.error(
                                        "Failed to add foreign key constraint for bets.game_id: %s",
                                        fk_err,
                                        exc_info=True,
                                    )

                    # --- Unit Records Table ---
                    unit_records_created = False
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
                        unit_records_created = True

                    if unit_records_created:
                        logger.info(
                            "Attempting to add foreign key constraint for newly created 'unit_records' table..."
                        )
                        try:
                            await cursor.execute(
                                "ALTER TABLE unit_records ADD CONSTRAINT unit_records_ibfk_1 FOREIGN KEY (bet_serial) REFERENCES bets(bet_serial) ON DELETE CASCADE"
                            )
                            logger.info(
                                "Added foreign key constraint for unit_records.bet_serial."
                            )
                        except aiomysql.Error as fk_err:
                            logger.error(
                                "Failed to add foreign key constraint for unit_records.bet_serial: %s",
                                fk_err,
                                exc_info=True,
                            )

                    # --- Guild Settings Table ---
                    if not await self.table_exists(conn, "guild_settings"):
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

                        await self._check_and_add_column(
                            cursor,
                            "guild_settings",
                            "voice_channel_id",
                            "BIGINT NULL COMMENT 'Monthly VC'",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "guild_settings",
                            "yearly_channel_id",
                            "BIGINT NULL COMMENT 'Yearly VC'",
                        )
                        await self._check_and_add_column(
                            cursor,
                            "guild_settings",
                            "live_game_updates",
                            "TINYINT(1) DEFAULT 0 COMMENT 'Enable 15s live game updates'",
                            after="yearly_channel_id",
                        )

                    # --- Cappers Table ---
                    if not await self.table_exists(conn, "cappers"):
                        await cursor.execute(
                            """
                            CREATE TABLE cappers (
                                guild_id BIGINT NOT NULL,
                                user_id BIGINT NOT NULL,
                                display_name VARCHAR(100) NULL,
                                image_path VARCHAR(255) NULL,
                                banner_color VARCHAR(7) NULL DEFAULT '#0096FF',
                                bet_won INTEGER DEFAULT 0 NOT NULL,
                                bet_loss INTEGER DEFAULT 0 NOT NULL,
                                bet_push INTEGER DEFAULT 0 NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                PRIMARY KEY (guild_id, user_id)
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        )
                        logger.info("Table 'cappers' created.")

                        await self._check_and_add_column(
                            cursor,
                            "cappers",
                            "bet_push",
                            "INTEGER DEFAULT 0 NOT NULL COMMENT 'Count of pushed bets'",
                        )

                    # --- Leagues Table ---
                    if not await self.table_exists(conn, "leagues"):
                        await cursor.execute(
                            """
                            CREATE TABLE leagues (
                                id BIGINT PRIMARY KEY COMMENT 'API League ID',
                                name VARCHAR(150) NULL,
                                sport VARCHAR(50) NOT NULL,
                                type VARCHAR(50) NULL,
                                logo VARCHAR(255) NULL,
                                country VARCHAR(100) NULL,
                                country_code CHAR(3) NULL,
                                country_flag VARCHAR(255) NULL,
                                season INTEGER NULL
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        )
                        await cursor.execute(
                            "CREATE INDEX idx_leagues_sport_country ON leagues (sport, country)"
                        )
                        logger.info("Table 'leagues' created.")

                    # --- Teams Table ---
                    if not await self.table_exists(conn, "teams"):
                        await cursor.execute(
                            """
                            CREATE TABLE teams (
                                id BIGINT PRIMARY KEY COMMENT 'API Team ID',
                                name VARCHAR(150) NULL,
                                sport VARCHAR(50) NOT NULL,
                                code VARCHAR(10) NULL,
                                country VARCHAR(100) NULL,
                                founded INTEGER NULL,
                                national BOOLEAN DEFAULT FALSE,
                                logo VARCHAR(255) NULL,
                                venue_id BIGINT NULL,
                                venue_name VARCHAR(150) NULL,
                                venue_address VARCHAR(255) NULL,
                                venue_city VARCHAR(100) NULL,
                                venue_capacity INTEGER NULL,
                                venue_surface VARCHAR(50) NULL,
                                venue_image VARCHAR(255) NULL
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        )
                        await cursor.execute(
                            "CREATE INDEX idx_teams_sport_country ON teams (sport, country)"
                        )
                        await cursor.execute(
                            "CREATE INDEX idx_teams_name ON teams (name)"
                        )
                        logger.info("Table 'teams' created.")

                    # --- Standings Table ---
                    if not await self.table_exists(conn, "standings"):
                        await cursor.execute(
                            """
                            CREATE TABLE standings (
                                league_id BIGINT NOT NULL,
                                team_id BIGINT NOT NULL,
                                season INT NOT NULL,
                                sport VARCHAR(50) NOT NULL,
                                `rank` INTEGER NULL,
                                points INTEGER NULL,
                                goals_diff INTEGER NULL,
                                form VARCHAR(20) NULL,
                                status VARCHAR(50) NULL,
                                description VARCHAR(100) NULL,
                                group_name VARCHAR(100) NULL,
                                played INTEGER DEFAULT 0,
                                won INTEGER DEFAULT 0,
                                draw INTEGER DEFAULT 0,
                                lost INTEGER DEFAULT 0,
                                goals_for INTEGER DEFAULT 0,
                                goals_against INTEGER DEFAULT 0,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                PRIMARY KEY (league_id, team_id, season)
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        )
                        await cursor.execute(
                            "CREATE INDEX idx_standings_league_season_rank ON standings (league_id, season, `rank`)"
                        )
                        logger.info("Table 'standings' created.")

                        async with conn.cursor(aiomysql.DictCursor) as dict_cursor:
                            await dict_cursor.execute(
                                "SHOW INDEX FROM standings WHERE Key_name = 'PRIMARY'"
                            )
                            pk_cols = {
                                row["Column_name"]
                                for row in await dict_cursor.fetchall()
                            }
                            if "season" not in pk_cols:
                                logger.warning(
                                    "Primary key for 'standings' missing 'season'. Attempting rebuild."
                                )
                                try:
                                    await cursor.execute(
                                        "ALTER TABLE standings DROP PRIMARY KEY"
                                    )
                                    if not await self._column_exists(
                                        conn, "standings", "season"
                                    ):
                                        await cursor.execute(
                                            "ALTER TABLE standings ADD COLUMN season INT NOT NULL AFTER team_id"
                                        )
                                    await cursor.execute(
                                        "ALTER TABLE standings ADD PRIMARY KEY (league_id, team_id, season)"
                                    )
                                    logger.info(
                                        "Rebuilt 'standings' primary key including 'season'."
                                    )
                                except aiomysql.Error as pk_err:
                                    logger.error(
                                        "Failed to rebuild primary key for 'standings': %s",
                                        pk_err,
                                        exc_info=True,
                                    )

                    # --- Game Events Table ---
                    if not await self.table_exists(conn, "game_events"):
                        await cursor.execute(
                            """
                            CREATE TABLE game_events (
                                event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                                game_id BIGINT NOT NULL,
                                guild_id BIGINT NULL,
                                event_type VARCHAR(50) NOT NULL,
                                details TEXT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                INDEX idx_game_events_game_time (game_id, created_at),
                                FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        )
                        logger.info("Table 'game_events' created.")

                    # --- Bet Reactions Table ---
                    if not await self.table_exists(conn, "bet_reactions"):
                        await cursor.execute(
                            """
                            CREATE TABLE bet_reactions (
                                reaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                                bet_serial BIGINT NOT NULL,
                                user_id BIGINT NOT NULL,
                                emoji VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
                                channel_id BIGINT NOT NULL,
                                message_id BIGINT NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                INDEX idx_bet_reactions_bet (bet_serial),
                                INDEX idx_bet_reactions_user (user_id),
                                INDEX idx_bet_reactions_message (message_id),
                                FOREIGN KEY (bet_serial) REFERENCES bets(bet_serial) ON DELETE CASCADE
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        )
                        logger.info("Table 'bet_reactions' created.")

                    # --- API Games Table ---
                    if not await self.table_exists(conn, "api_games"):
                        await cursor.execute(
                            """
                            CREATE TABLE api_games (
                                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                                api_game_id VARCHAR(50) NOT NULL,
                                sport VARCHAR(50) NOT NULL,
                                league_id VARCHAR(50) NOT NULL,
                                season INT NOT NULL,
                                home_team_name VARCHAR(150) NULL,
                                away_team_name VARCHAR(150) NULL,
                                start_time DATETIME NULL,
                                end_time DATETIME NULL,
                                status VARCHAR(50) NULL,
                                score VARCHAR(20) NULL,
                                raw_json JSON NOT NULL,
                                fetched_at DATETIME NOT NULL,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                UNIQUE KEY unique_game (sport, league_id, season, api_game_id)
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        )
                        await cursor.execute(
                            "CREATE INDEX idx_api_games_sport_league ON api_games (sport, league_id)"
                        )
                        await cursor.execute(
                            "CREATE INDEX idx_api_games_season ON api_games (season)"
                        )
                        logger.info("Table 'api_games' created.")

                        await self._check_and_add_column(
                            cursor, "api_games", "home_team_name", "VARCHAR(150) NULL"
                        )
                        await self._check_and_add_column(
                            cursor, "api_games", "away_team_name", "VARCHAR(150) NULL"
                        )
                        await self._check_and_add_column(
                            cursor, "api_games", "start_time", "DATETIME NULL"
                        )
                        await self._check_and_add_column(
                            cursor, "api_games", "end_time", "DATETIME NULL"
                        )
                        await self._check_and_add_column(
                            cursor, "api_games", "status", "VARCHAR(50) NULL"
                        )
                        await self._check_and_add_column(
                            cursor, "api_games", "score", "VARCHAR(20) NULL"
                        )

                    # --- Players Table ---
                    if not await self.table_exists(conn, "players"):
                        await cursor.execute(
                            """
                            CREATE TABLE players (
                                player_name TEXT,
                                dateBorn TEXT,
                                idPlayeridTeam TEXT,
                                strCutouts TEXT,
                                strEthnicity TEXT,
                                strGender TEXT,
                                strHeight TEXT,
                                strNationality TEXT,
                                strNumber TEXT,
                                strPlayer TEXT,
                                strPosition TEXT,
                                strSport TEXT,
                                strTeam TEXT,
                                strThumb TEXT,
                                strWeight TEXT
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        )
                        logger.info("Table 'players' created.")

                    # --- Bet Legs Table ---
                    if not await self.table_exists(conn, "bet_legs"):
                        await cursor.execute(
                            """
                            CREATE TABLE bet_legs (
                                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                                bet_serial BIGINT NOT NULL,
                                api_game_id VARCHAR(50) NULL,
                                bet_type VARCHAR(50) NOT NULL,
                                player_prop VARCHAR(255) NULL,
                                player_id VARCHAR(50) NULL,
                                line VARCHAR(255) NULL,
                                odds DECIMAL(10,2) NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (bet_serial) REFERENCES bets(bet_serial) ON DELETE CASCADE
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        )
                        logger.info("Table 'bet_legs' created.")

                        await self._check_and_add_column(
                            cursor, "bet_legs", "player_prop", "VARCHAR(255) NULL"
                        )
                        await self._check_and_add_column(
                            cursor, "bet_legs", "player_id", "VARCHAR(50) NULL"
                        )
                        await self._check_and_add_column(
                            cursor, "bet_legs", "line", "VARCHAR(255) NULL"
                        )
                        await self._check_and_add_column(
                            cursor, "bet_legs", "odds", "DECIMAL(10,2) NULL"
                        )

                    logger.info("Database schema initialization/verification complete.")
        except Exception as e:
            logger.error(
                "Error initializing/verifying database schema: %s", e, exc_info=True
            )
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
            str(game.get("id")),
            game.get("sport", ""),
            str(game.get("league", {}).get("id", "")),
            season,
            (game.get("teams", {}) or {}).get("home", {}).get("name"),
            (game.get("teams", {}) or {}).get("away", {}).get("name"),
            game.get("date"),
            None,
            game.get("status", {}).get("short", ""),
            json.dumps(game.get("scores", {})),
            json.dumps(game),
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
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
            from api.sports_api import SportsAPI

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
                        "Fetched %d games for %s/%s", len(games), sport, league_name
                    )
                    for game in games:
                        try:
                            game["season"] = season
                            await self.upsert_api_game(game)
                            logger.info("Saved game %s to database", game.get("id"))
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
        logger.info("[get_normalized_games_for_dropdown] Starting sync_games_from_api")
        await self.sync_games_from_api(force_season=season)
        logger.info("[get_normalized_games_for_dropdown] Completed sync_games_from_api")
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
        from config.leagues import LEAGUE_ID_MAP

        league_id = LEAGUE_ID_MAP.get(league_name, "1")
        logger.info("[get_normalized_games_for_dropdown] Using league_id=%s", league_id)
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
                logger.info("Fetched %d open bets for guild_id=%s", len(rows), guild_id)
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
            raise BetServiceError(f"No api_games row for {api_game_id}")

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
