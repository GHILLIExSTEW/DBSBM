# betting-bot/data/db_manager.py

import aiomysql
import logging
from typing import Optional, List, Dict, Any, Union, Tuple # Added Tuple
import os
import asyncio
import json
from config.leagues import LEAGUE_CONFIG, LEAGUE_IDS
from data.game_utils import get_league_abbreviation, normalize_mlb_team_name, sanitize_team_name

try:
    from ..config.database_mysql import (
        MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB,
        MYSQL_POOL_MIN_SIZE, MYSQL_POOL_MAX_SIZE
    )
except ImportError:
    from config.database_mysql import (
        MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB,
        MYSQL_POOL_MIN_SIZE, MYSQL_POOL_MAX_SIZE
    )

if not MYSQL_DB:
    print("CRITICAL ERROR: MYSQL_DB environment variable is not set.")

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages the connection pool and executes queries against the MySQL DB."""

    def __init__(self):
        """Initializes the DatabaseManager."""
        self._pool: Optional[aiomysql.Pool] = None
        self.db_name = MYSQL_DB
        logger.info("MySQL DatabaseManager initialized.")
        if not all([MYSQL_HOST, MYSQL_USER, self.db_name, MYSQL_PASSWORD is not None]):
            logger.critical(
                "Missing one or more MySQL environment variables "
                "(HOST, USER, PASSWORD, DB). DatabaseManager cannot connect."
            )

    async def connect(self) -> Optional[aiomysql.Pool]:
        """Create or return existing MySQL connection pool."""
        if self._pool is None:
            if not all([MYSQL_HOST, MYSQL_USER, self.db_name, MYSQL_PASSWORD is not None]):
                logger.critical(
                    "Cannot connect: MySQL environment variables are not "
                    "configured."
                )
                return None

            logger.info("Attempting to create MySQL connection pool...")
            try:
                self._pool = await aiomysql.create_pool(
                    host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                    password=MYSQL_PASSWORD, db=self.db_name,
                    minsize=MYSQL_POOL_MIN_SIZE, maxsize=MYSQL_POOL_MAX_SIZE,
                    autocommit=True, # Ensure autocommit is True for simplicity unless transactions needed
                    connect_timeout=10,
                    charset='utf8mb4',
                    # cursorclass=aiomysql.cursors.DictCursor # Setting default cursor class if desired
                )
                # Test connection
                async with self._pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT 1")
                logger.info(
                    "MySQL connection pool created and tested successfully."
                )
                await self.initialize_db() # Ensure schema is initialized
            except aiomysql.OperationalError as op_err:
                logger.critical(f"FATAL: OpError connecting to MySQL: {op_err}", exc_info=True)
                self._pool = None
                raise ConnectionError(f"Failed to connect (OperationalError): {op_err}") from op_err
            except Exception as e:
                logger.critical(f"FATAL: Failed to connect to MySQL: {e}", exc_info=True)
                self._pool = None
                raise ConnectionError(f"Failed to connect: {e}") from e
        return self._pool

    async def close(self):
        """Close the MySQL connection pool."""
        if self._pool is not None:
            logger.info("Closing MySQL connection pool...")
            try:
                # First, close all active connections in the pool
                async with self._pool.acquire() as conn:
                    await conn.close()
                
                # Then close the pool itself
                self._pool.close()
                
                # Wait for pool to close with timeout
                try:
                    await asyncio.wait_for(self._pool.wait_closed(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Timeout while waiting for MySQL pool to close")
                except RuntimeError as e:
                    if "Event loop is closed" in str(e):
                        logger.warning("Event loop was closed before pool could be properly closed")
                    else:
                        raise
                finally:
                    # Ensure pool is set to None even if wait_closed fails
                    self._pool = None
                    logger.info("MySQL connection pool closed.")
            except Exception as e:
                logger.error(f"Error closing MySQL pool: {e}")
                # Ensure pool is set to None even if there's an error
                self._pool = None

    async def execute(self, query: str, *args) -> Tuple[Optional[int], Optional[int]]:
        """
        Execute INSERT, UPDATE, DELETE.
        Returns a tuple: (rowcount, lastrowid).
        lastrowid will be None for UPDATE/DELETE or if INSERT failed/affected 0 rows.
        """
        pool = await self.connect() # Ensure pool exists
        if not pool:
            logger.error("Cannot execute: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        # Flatten nested tuple/list if only one argument is a tuple/list
        flat_args = tuple(args[0]) if len(args) == 1 and isinstance(args[0], (tuple, list)) else args

        logger.debug(f"Executing DB Query: {query} Args: {flat_args}")
        last_id = None
        rowcount = None
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    rowcount = await cursor.execute(query, flat_args)
                    if rowcount is not None and rowcount > 0 and query.strip().upper().startswith("INSERT"):
                         last_id = cursor.lastrowid
                    # Explicitly commit after any write operation
                    if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                        await conn.commit()
            return rowcount, last_id
        except Exception as e:
            logger.error(f"Error executing query: {query} Args: {flat_args}. Error: {e}", exc_info=True)
            # Return None for both in case of error
            return None, None

    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch one row as a dictionary."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetch_one: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        logger.debug(f"Fetching One DB Query: {query} Args: {args}")
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, args)
                    return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching one row: {query} Args: {args}. Error: {e}", exc_info=True)
            return None

    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch all rows as a list of dictionaries."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetch_all: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        logger.debug(f"Fetching All DB Query: {query} Args: {args}")
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, args)
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching all rows: {query} Args: {args}. Error: {e}", exc_info=True)
            return []

    async def fetchval(self, query: str, *args) -> Optional[Any]:
        """Fetch a single value from the first row."""
        pool = await self.connect()
        if not pool:
            logger.error("Cannot fetchval: DB pool unavailable.")
            raise ConnectionError("DB pool unavailable.")

        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            args = tuple(args[0])

        logger.debug(f"Fetching Value DB Query: {query} Args: {args}")
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.Cursor) as cursor: # Use standard cursor for single value
                    await cursor.execute(query, args)
                    row = await cursor.fetchone()
                    return row[0] if row else None
        except Exception as e:
            logger.error(f"Error fetching value: {query} Args: {args}. Error: {e}", exc_info=True)
            return None

    async def table_exists(self, conn, table_name: str) -> bool:
        """Check if a table exists in the database."""
        async with conn.cursor(aiomysql.Cursor) as cursor:
            try:
                await cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = %s AND table_name = %s",
                    (self.db_name, table_name)
                )
                result = await cursor.fetchone()
                return result[0] > 0 if result else False
            except Exception as e:
                logger.error(f"Error checking if table '{table_name}' exists: {e}", exc_info=True)
                raise

    async def _check_and_add_column(self, cursor, table_name, column_name, column_definition):
        """Checks if a column exists and adds it if not."""
        async with cursor.connection.cursor(aiomysql.DictCursor) as dict_cursor:
            await dict_cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,))
            exists = await dict_cursor.fetchone()

        if not exists:
            logger.info(f"Adding column '{column_name}' to table '{table_name}'...")
            alter_statement = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_definition}"
            await cursor.execute(alter_statement)
            logger.info(f"Successfully added column '{column_name}'.")
        else:
            logger.debug(f"Column '{column_name}' already exists in '{table_name}'.")

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
                    if not await self.table_exists(conn, 'users'):
                        await cursor.execute('''
                            CREATE TABLE users (
                                user_id BIGINT PRIMARY KEY COMMENT 'Discord User ID',
                                username VARCHAR(100) NULL COMMENT 'Last known Discord username',
                                balance DECIMAL(15, 2) DEFAULT 1000.00 NOT NULL,
                                frozen_balance DECIMAL(15, 2) DEFAULT 0.00 NOT NULL,
                                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        ''')
                        logger.info("Table 'users' created.")
                    else:
                        logger.info("Table 'users' already exists.")
                        # Add checks for specific columns if needed later

                    # --- Games Table ---
                    if not await self.table_exists(conn, 'games'):
                        await cursor.execute('''
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
                        ''')
                        await cursor.execute('CREATE INDEX idx_games_league_status_time ON games (league_id, status, start_time)')
                        await cursor.execute('CREATE INDEX idx_games_start_time ON games (start_time)')
                        await cursor.execute('CREATE INDEX idx_games_status ON games (status)')
                        logger.info("Table 'games' created.")
                    else:
                        logger.info("Table 'games' already exists.")
                        await self._check_and_add_column(cursor, 'games', 'sport', "VARCHAR(50) NOT NULL COMMENT 'Sport key' AFTER id")
                        await self._check_and_add_column(cursor, 'games', 'league_name', "VARCHAR(150) NULL AFTER league_id")
                        await self._check_and_add_column(cursor, 'games', 'home_team_name', "VARCHAR(150) NULL AFTER away_team_id")
                        await self._check_and_add_column(cursor, 'games', 'away_team_name', "VARCHAR(150) NULL AFTER home_team_name")
                        await self._check_and_add_column(cursor, 'games', 'home_team_logo', "VARCHAR(255) NULL AFTER away_team_name")
                        await self._check_and_add_column(cursor, 'games', 'away_team_logo', "VARCHAR(255) NULL AFTER home_team_logo")
                        await self._check_and_add_column(cursor, 'games', 'end_time', "TIMESTAMP NULL COMMENT 'Game end time' AFTER start_time")
                        # await self._check_and_add_column(cursor, 'games', 'status', "VARCHAR(20) NULL COMMENT 'Game status' AFTER end_time") # Already exists
                        await self._check_and_add_column(cursor, 'games', 'score', "JSON NULL COMMENT 'JSON scores' AFTER status")
                        await self._check_and_add_column(cursor, 'games', 'venue', "VARCHAR(150) NULL AFTER score")
                        await self._check_and_add_column(cursor, 'games', 'referee', "VARCHAR(100) NULL AFTER venue")

                    # --- Bets Table ---
                    bets_table_created = False
                    if not await self.table_exists(conn, 'bets'):
                        # Use the schema provided by user
                        await cursor.execute('''
                            CREATE TABLE bets (
                                bet_serial bigint(20) NOT NULL AUTO_INCREMENT,
                                event_id varchar(255) DEFAULT NULL,
                                guild_id bigint(20) NOT NULL,
                                message_id bigint(20) DEFAULT NULL,
                                status varchar(20) NOT NULL DEFAULT 'pending',
                                user_id bigint(20) NOT NULL,
                                game_id bigint(20) DEFAULT NULL,
                                bet_type varchar(50) DEFAULT NULL,
                                player_prop varchar(255) DEFAULT NULL,
                                player_id varchar(50) DEFAULT NULL,
                                league varchar(50) NOT NULL,
                                team varchar(100) DEFAULT NULL,
                                opponent varchar(50) DEFAULT NULL,
                                line varchar(255) DEFAULT NULL,
                                odds decimal(10,2) DEFAULT NULL,
                                units decimal(10,2) NOT NULL,
                                legs int(11) DEFAULT NULL,
                                bet_won tinyint(4) DEFAULT 0,
                                bet_loss tinyint(4) DEFAULT 0,
                                confirmed tinyint(4) DEFAULT 0,
                                created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                                game_start datetime DEFAULT NULL,
                                result_value decimal(15,2) DEFAULT NULL,
                                result_description text,
                                expiration_time timestamp NULL DEFAULT NULL,
                                updated_at timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                channel_id bigint(20) DEFAULT NULL,
                                bet_details longtext NOT NULL,
                                PRIMARY KEY (bet_serial),
                                KEY guild_id (guild_id),
                                KEY user_id (user_id),
                                KEY status (status),
                                KEY created_at (created_at),
                                KEY game_id (game_id),
                                CONSTRAINT bets_ibfk_1 FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE SET NULL
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        ''')
                        logger.info("Table 'bets' created using provided schema.")
                        bets_table_created = True # Mark as newly created
                    else:
                        logger.info("Table 'bets' already exists.")
                        # Check specific columns from provided schema
                        await self._check_and_add_column(cursor, 'bets', 'bet_details', "longtext NOT NULL COMMENT 'JSON containing specific bet details'")
                        await self._check_and_add_column(cursor, 'bets', 'channel_id', "bigint(20) DEFAULT NULL COMMENT 'Channel where bet was posted'")
                        # Verify game_id FK exists if table wasn't just created
                        async with conn.cursor(aiomysql.DictCursor) as dict_cursor:
                             await dict_cursor.execute(
                                 "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
                                 "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'bets' AND COLUMN_NAME = 'game_id' AND REFERENCED_TABLE_NAME = 'games'",
                                 (self.db_name,)
                             )
                             fk_exists = await dict_cursor.fetchone()
                             if not fk_exists:
                                 logger.warning("Foreign key constraint 'bets_ibfk_1' (or similar) for bets.game_id -> games.id might be missing. Attempting to add.")
                                 try:
                                     await cursor.execute("ALTER TABLE bets ADD CONSTRAINT bets_ibfk_1 FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE SET NULL")
                                     logger.info("Added foreign key constraint for bets.game_id.")
                                 except Exception as fk_err:
                                     logger.error(f"Failed to add foreign key constraint for bets.game_id: {fk_err}")

                    # --- Unit Records Table ---
                    unit_records_created = False
                    if not await self.table_exists(conn, 'unit_records'):
                        await cursor.execute('''
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
                                -- Foreign key added conditionally below --
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        ''')
                        logger.info("Table 'unit_records' created.")
                        unit_records_created = True # Mark as newly created
                    else:
                        logger.info("Table 'unit_records' already exists.")

                    # MODIFIED: Only attempt to add FK if unit_records table was newly created
                    if unit_records_created:
                        logger.info("Attempting to add foreign key constraint for newly created 'unit_records' table...")
                        try:
                             await cursor.execute("ALTER TABLE unit_records ADD CONSTRAINT unit_records_ibfk_1 FOREIGN KEY (bet_serial) REFERENCES bets(bet_serial) ON DELETE CASCADE")
                             logger.info("Added foreign key constraint for unit_records.bet_serial.")
                        except Exception as fk_err:
                             logger.error(f"Failed to add foreign key constraint for unit_records.bet_serial: {fk_err}. This might indicate orphaned records if the table existed before this run.", exc_info=True)
                    else:
                         logger.debug("Skipping foreign key check for 'unit_records' as table already existed.")
                         # Optionally, could add a check here to see if the FK exists already if the table existed


                    # --- Guild Settings Table ---
                    if not await self.table_exists(conn, 'guild_settings'):
                        await cursor.execute('''
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
                                total_units_channel_id BIGINT NULL, # Unused?
                                daily_report_time TEXT NULL,
                                member_role BIGINT NULL,
                                bot_name_mask TEXT NULL,
                                bot_image_mask TEXT NULL,
                                guild_default_image TEXT NULL,
                                default_parlay_thumbnail TEXT NULL,
                                total_result_value DECIMAL(15, 2) DEFAULT 0.0, # Unused? Calculated from records
                                min_units DECIMAL(15, 2) DEFAULT 0.1,
                                max_units DECIMAL(15, 2) DEFAULT 10.0,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        ''')
                        logger.info("Table 'guild_settings' created.")
                    else:
                        logger.info("Table 'guild_settings' already exists.")
                        await self._check_and_add_column(cursor, 'guild_settings', 'voice_channel_id', "BIGINT NULL COMMENT 'Monthly VC'")
                        await self._check_and_add_column(cursor, 'guild_settings', 'yearly_channel_id', "BIGINT NULL COMMENT 'Yearly VC'")

                    # --- Cappers Table ---
                    if not await self.table_exists(conn, 'cappers'):
                        await cursor.execute('''
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
                        ''')
                        logger.info("Table 'cappers' created.")
                    else:
                        logger.info("Table 'cappers' already exists.")
                        await self._check_and_add_column(cursor, 'cappers', 'bet_push', "INTEGER DEFAULT 0 NOT NULL COMMENT 'Count of pushed bets' AFTER bet_loss")


                    # --- Leagues Table ---
                    if not await self.table_exists(conn, 'leagues'):
                        await cursor.execute('''
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
                        ''')
                        await cursor.execute('CREATE INDEX idx_leagues_sport_country ON leagues (sport, country)')
                        logger.info("Table 'leagues' created.")
                    else:
                        logger.info("Table 'leagues' already exists.")

                    # --- Teams Table ---
                    if not await self.table_exists(conn, 'teams'):
                        await cursor.execute('''
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
                        ''')
                        await cursor.execute('CREATE INDEX idx_teams_sport_country ON teams (sport, country)')
                        await cursor.execute('CREATE INDEX idx_teams_name ON teams (name)')
                        logger.info("Table 'teams' created.")
                    else:
                        logger.info("Table 'teams' already exists.")

                    # --- Standings Table ---
                    if not await self.table_exists(conn, 'standings'):
                        await cursor.execute('''
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
                        ''')
                        await cursor.execute('CREATE INDEX idx_standings_league_season_rank ON standings (league_id, season, `rank`)')
                        logger.info("Table 'standings' created.")
                    else:
                        logger.info("Table 'standings' already exists.")
                        # Ensure composite PK with season exists
                        async with conn.cursor(aiomysql.DictCursor) as dict_cursor:
                            await dict_cursor.execute("SHOW INDEX FROM standings WHERE Key_name = 'PRIMARY'")
                            pk_cols = {row['Column_name'] for row in await dict_cursor.fetchall()}
                            if 'season' not in pk_cols:
                                logger.warning("Primary key for 'standings' might be missing 'season'. Attempting rebuild.")
                                try:
                                    await cursor.execute("ALTER TABLE standings DROP PRIMARY KEY")
                                    if not await self._column_exists(conn, 'standings', 'season'):
                                        await cursor.execute("ALTER TABLE standings ADD COLUMN season INT NOT NULL AFTER team_id")
                                    await cursor.execute("ALTER TABLE standings ADD PRIMARY KEY (league_id, team_id, season)")
                                    logger.info("Rebuilt 'standings' primary key including 'season'.")
                                except Exception as pk_err:
                                    logger.error(f"Failed to rebuild primary key for 'standings': {pk_err}. Manual check needed.")

                    # --- Game Events Table ---
                    if not await self.table_exists(conn, 'game_events'):
                        await cursor.execute('''
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
                        ''')
                        logger.info("Table 'game_events' created.")
                    else:
                        logger.info("Table 'game_events' already exists.")

                    # --- Bet Reactions Table ---
                    if not await self.table_exists(conn, 'bet_reactions'):
                        await cursor.execute('''
                            CREATE TABLE bet_reactions (
                                reaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                                bet_serial BIGINT NOT NULL,
                                user_id BIGINT NOT NULL,
                                emoji VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL, # Ensure correct charset for emoji
                                channel_id BIGINT NOT NULL,
                                message_id BIGINT NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                INDEX idx_bet_reactions_bet (bet_serial),
                                INDEX idx_bet_reactions_user (user_id),
                                INDEX idx_bet_reactions_message (message_id),
                                FOREIGN KEY (bet_serial) REFERENCES bets(bet_serial) ON DELETE CASCADE
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        ''')
                        logger.info("Table 'bet_reactions' created.")
                    else:
                        logger.info("Table 'bet_reactions' already exists.")

                    # --- API Games Table ---
                    if not await self.table_exists(conn, 'api_games'):
                        await cursor.execute('''
                            CREATE TABLE api_games (
                                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                                sport VARCHAR(50) NOT NULL,
                                league_id VARCHAR(50) NOT NULL,
                                season INT NOT NULL,
                                raw_json JSON NOT NULL,
                                fetched_at DATETIME NOT NULL,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                UNIQUE KEY unique_game (sport, league_id, season)
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        ''')
                        await cursor.execute('CREATE INDEX idx_api_games_sport_league ON api_games (sport, league_id)')
                        await cursor.execute('CREATE INDEX idx_api_games_season ON api_games (season)')
                        logger.info("Table 'api_games' created.")
                    else:
                        logger.info("Table 'api_games' already exists.")

                    # Create the players table
                    await cursor.execute('''
                        CREATE TABLE IF NOT EXISTS players (
                            player_name TEXT,
                            dateBorn TEXT,
                            idPlayeridTeam TEXT,
                            strCutouts TEXT,
                            trEthnicity TEXT,
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
                        )
                    ''')

                    logger.info("Database schema initialization/verification complete.")
        except Exception as e:
            logger.error(f"Error initializing/verifying database schema: {e}", exc_info=True)
            raise

    async def _column_exists(self, conn, table_name: str, column_name: str) -> bool:
        """Helper to check if a column exists."""
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s AND column_name = %s",
                (self.db_name, table_name, column_name)
            )
            return await cursor.fetchone() is not None

    async def save_game(self, game_id: str, league_id: str, league_name: str, home_team: str, away_team: str, start_time: str, status: str = "Scheduled"):
        """Save a game to the games table."""
        try:
            # Ensure status is always set to a valid value
            if not status or str(status).lower() in ("none", "null", "", "n/a"):
                status = "scheduled"
            # Map league_id to sport
            sport = "Baseball" if league_id == "4424" else \
                   "Hockey" if league_id == "4380" else \
                   "Football" if league_id == "4405" else \
                   "Basketball" if league_id == "4388" else \
                   "Soccer" if league_id in ["4387", "4391", "4392", "4393", "4394", "4395"] else \
                   "Baseball" if league_id in ["4429", "4430"] else \
                   "Basketball" if league_id == "4389" else \
                   "Hockey" if league_id == "4431" else "Other"

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
                    away_team_name = VALUES(away_team_name),
                    start_time = VALUES(start_time),
                    status = VALUES(status),
                    updated_at = CURRENT_TIMESTAMP
            """
            await self.execute(query, (
                game_id, sport, league_id, league_name, home_team, away_team, 
                start_time, status
            ))
            logger.info(f"Saved game {game_id} to database with status '{status}' and league_name '{league_name}'")
            return True
        except Exception as e:
            logger.error(f"Error saving game {game_id}: {str(e)}")
            return False

    async def upsert_api_game(self, game: dict):
        """Upsert a full API game record, storing all fields in their respective columns."""
        import json
        query = '''
            INSERT INTO api_games (
                id, api_game_id, sport, league_id, league_name, home_team_id, away_team_id, start_time, end_time, status, score, venue, referee, created_at, updated_at, raw_json,
                date, time, timestamp, timezone, week, status_long, status_short, country_id, country_name, country_code, country_flag, league_type, league_logo, league_season,
                home_team_name, home_team_logo, away_team_name, away_team_logo, home_hits, home_errors, home_total, away_hits, away_errors, away_total, home_innings, away_innings
            ) VALUES (
                %(id)s, %(api_game_id)s, %(sport)s, %(league_id)s, %(league_name)s, %(home_team_id)s, %(away_team_id)s, %(start_time)s, %(end_time)s, %(status)s, %(score)s, %(venue)s, %(referee)s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %(raw_json)s,
                %(date)s, %(time)s, %(timestamp)s, %(timezone)s, %(week)s, %(status_long)s, %(status_short)s, %(country_id)s, %(country_name)s, %(country_code)s, %(country_flag)s, %(league_type)s, %(league_logo)s, %(league_season)s,
                %(home_team_name)s, %(home_team_logo)s, %(away_team_name)s, %(away_team_logo)s, %(home_hits)s, %(home_errors)s, %(home_total)s, %(away_hits)s, %(away_errors)s, %(away_total)s, %(home_innings)s, %(away_innings)s
            )
            ON DUPLICATE KEY UPDATE
                sport=VALUES(sport), league_id=VALUES(league_id), league_name=VALUES(league_name), home_team_id=VALUES(home_team_id), away_team_id=VALUES(away_team_id),
                start_time=VALUES(start_time), end_time=VALUES(end_time), status=VALUES(status), score=VALUES(score), venue=VALUES(venue), referee=VALUES(referee), updated_at=CURRENT_TIMESTAMP, raw_json=VALUES(raw_json),
                date=VALUES(date), time=VALUES(time), timestamp=VALUES(timestamp), timezone=VALUES(timezone), week=VALUES(week), status_long=VALUES(status_long), status_short=VALUES(status_short),
                country_id=VALUES(country_id), country_name=VALUES(country_name), country_code=VALUES(country_code), country_flag=VALUES(country_flag), league_type=VALUES(league_type), league_logo=VALUES(league_logo), league_season=VALUES(league_season),
                home_team_name=VALUES(home_team_name), home_team_logo=VALUES(home_team_logo), away_team_name=VALUES(away_team_name), away_team_logo=VALUES(away_team_logo),
                home_hits=VALUES(home_hits), home_errors=VALUES(home_errors), home_total=VALUES(home_total), away_hits=VALUES(away_hits), away_errors=VALUES(away_errors), away_total=VALUES(away_total),
                home_innings=VALUES(home_innings), away_innings=VALUES(away_innings)
        '''
        
        params = {
            'id': str(game.get('id')),
            'api_game_id': str(game.get('id')),  # Use id as api_game_id
            'sport': game.get('sport', ''),
            'league_id': str(game.get('league', {}).get('id', '')),
            'league_name': game.get('league', {}).get('name', ''),
            'home_team_id': str(game.get('teams', {}).get('home', {}).get('id', '')),
            'away_team_id': str(game.get('teams', {}).get('away', {}).get('id', '')),
            'start_time': game.get('date'),
            'end_time': None,
            'status': game.get('status', {}).get('short', ''),
            'score': json.dumps(game.get('scores', {})),
            'venue': game.get('venue', None),
            'referee': None,
            'raw_json': json.dumps(game),
            'date': game.get('date'),
            'time': game.get('time'),
            'timestamp': game.get('timestamp'),
            'timezone': game.get('timezone'),
            'week': game.get('week'),
            'status_long': game.get('status', {}).get('long', ''),
            'status_short': game.get('status', {}).get('short', ''),
            'country_id': (game.get('country', {}) or {}).get('id'),
            'country_name': (game.get('country', {}) or {}).get('name'),
            'country_code': (game.get('country', {}) or {}).get('code'),
            'country_flag': (game.get('country', {}) or {}).get('flag'),
            'league_type': game.get('league', {}).get('type'),
            'league_logo': game.get('league', {}).get('logo'),
            'league_season': game.get('league', {}).get('season'),
            'home_team_name': (game.get('teams', {}) or {}).get('home', {}).get('name'),
            'home_team_logo': (game.get('teams', {}) or {}).get('home', {}).get('logo'),
            'away_team_name': (game.get('teams', {}) or {}).get('away', {}).get('name'),
            'away_team_logo': (game.get('teams', {}) or {}).get('away', {}).get('logo'),
            'home_hits': (game.get('scores', {}) or {}).get('home', {}).get('hits'),
            'home_errors': (game.get('scores', {}) or {}).get('home', {}).get('errors'),
            'home_total': (game.get('scores', {}) or {}).get('home', {}).get('total'),
            'away_hits': (game.get('scores', {}) or {}).get('away', {}).get('hits'),
            'away_errors': (game.get('scores', {}) or {}).get('away', {}).get('errors'),
            'away_total': (game.get('scores', {}) or {}).get('away', {}).get('total'),
            'home_innings': json.dumps((game.get('scores', {}) or {}).get('home', {}).get('innings')),
            'away_innings': json.dumps((game.get('scores', {}) or {}).get('away', {}).get('innings')),
        }
        await self.execute(query, params)

    async def save_team(self, team: dict):
        """Insert or update a team record in the teams table."""
        query = '''
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
        '''
        params = (
            team.get('id'),
            team.get('name'),
            team.get('sport'),
            team.get('code'),
            team.get('country'),
            team.get('founded'),
            int(team.get('national', False)),
            team.get('logo'),
            team.get('venue_id'),
            team.get('venue_name'),
            team.get('venue_address'),
            team.get('venue_city'),
            team.get('venue_capacity'),
            team.get('venue_surface'),
            team.get('venue_image'),
        )
        await self.execute(query, *params)

    async def sync_games_from_api(self):
        """Sync games from api_games to games table."""
        try:
            query = """
                INSERT INTO games (
                    id, sport, league_id, league_name, home_team_id, away_team_id,
                    home_team_name, away_team_name, start_time, status, score,
                    venue, referee, created_at, updated_at
                )
                SELECT 
                    id, sport, league_id, league_name, home_team_id, away_team_id,
                    home_team_name, away_team_name, start_time, status, score,
                    venue, referee, created_at, updated_at
                FROM api_games
                ON DUPLICATE KEY UPDATE
                    sport = VALUES(sport),
                    league_id = VALUES(league_id),
                    league_name = VALUES(league_name),
                    home_team_id = VALUES(home_team_id),
                    away_team_id = VALUES(away_team_id),
                    home_team_name = VALUES(home_team_name),
                    away_team_name = VALUES(away_team_name),
                    start_time = VALUES(start_time),
                    status = VALUES(status),
                    score = VALUES(score),
                    venue = VALUES(venue),
                    referee = VALUES(referee),
                    updated_at = CURRENT_TIMESTAMP
            """
            await self.execute(query)
            logger.info("Successfully synced games from api_games to games table")
            return True
        except Exception as e:
            logger.error(f"Error syncing games from api_games to games table: {e}")
            return False

    async def get_normalized_games_for_dropdown(self, league_id: str, season: int = None) -> List[Dict[str, Any]]:
        """
        Fetch and normalize games for a league from the api_games table for use in a bet dropdown.
        """
        logger.info(f"Fetching games for league_id={league_id}")
        
        # Get sport and league name from LEAGUE_IDS
        sport = None
        league_name = None
        league_key = None
        for key, league_info in LEAGUE_IDS.items():
            if str(league_info.get('id')) == str(league_id):
                sport = league_info.get('sport', '').capitalize()
                league_key = key
                # Use the full league name from LEAGUE_CONFIG
                league_name = LEAGUE_CONFIG.get(league_info.get('sport', ''), {}).get(key, {}).get('name', key)
                # Convert MLB to full name
                if league_name == "MLB":
                    league_name = "Major League Baseball"
                break
        
        if not sport or not league_name:
            logger.warning(f"Could not find sport and league name for league_id={league_id}")
            return []
        
        league_abbr = get_league_abbreviation(league_name)
        logger.info(f"Looking up games for {sport}/{league_name} (abbreviation: {league_abbr}, key: {league_key})")
        
        # First sync games from api_games to games table
        await self.sync_games_from_api()
        
        # Query by league_id, sport, and league_name with case-insensitive matching
        query = """
            SELECT id, home_team_name, away_team_name, start_time, status, score
            FROM api_games
            WHERE league_id = %s AND UPPER(sport) = UPPER(%s) AND UPPER(league_name) = UPPER(%s)
            ORDER BY start_time DESC LIMIT 100
        """
        rows = await self.fetch_all(query, (league_id, sport, league_name))
        if not rows:
            logger.warning(f"No games found in api_games table for league_id={league_id}, sport={sport}, league_name={league_name}")
            return []

        dropdown_games = []
        for row in rows:
            try:
                # For MLB games, normalize team names
                if sport.lower() == "baseball" and league_key == "MLB":
                    home_team = normalize_mlb_team_name(row['home_team_name'])
                    away_team = normalize_mlb_team_name(row['away_team_name'])
                else:
                    home_team = sanitize_team_name(row['home_team_name'])
                    away_team = sanitize_team_name(row['away_team_name'])
                    
                dropdown_games.append({
                    'id': row['id'],
                    'api_game_id': str(row['id']),  # Use the id from api_games as the api_game_id
                    'home_team': home_team,
                    'away_team': away_team,
                    'start_time': row['start_time'],
                    'status': row['status'],
                    'home_team_name': home_team,
                    'away_team_name': away_team,
                })
            except Exception as e:
                logger.error(f"Error processing game data for league_id={league_id}, sport={sport}, league_name={league_name}: {e}")
                continue
        
        logger.info(f"Returning {len(dropdown_games)} normalized games for dropdown")
        return dropdown_games
