import asyncio
import logging
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from typing import Union

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Import the new centralized configuration
try:
    from config.settings import get_settings, validate_settings, get_logging_config
except ImportError:
    # Fallback - try to import from parent directory
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Add multiple possible paths for different execution contexts
    possible_paths = [
        os.path.dirname(current_dir),  # From bot/
        os.path.dirname(os.path.dirname(current_dir)),  # From root/
    ]
    for path in possible_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        from config.settings import get_settings, validate_settings, get_logging_config
    except ImportError:
        # Final fallback - create mock functions for testing
        def get_settings():
            return None

        def validate_settings():
            return []

        def get_logging_config():
            return {"level": "INFO", "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "file": None}

# Try to import with bot prefix first, then without
try:
    from bot.api.sports_api import SportsAPI
    from bot.services.live_game_channel_service import LiveGameChannelService
    from bot.utils.error_handler import (
        get_error_handler,
        initialize_default_recovery_strategies,
    )
    from bot.utils.game_line_image_generator import GameLineImageGenerator
    from bot.utils.parlay_image_generator import ParlayImageGenerator
    from bot.utils.performance_monitor import (
        background_monitoring,
        get_performance_monitor,
    )
    from bot.utils.player_prop_image_generator import PlayerPropImageGenerator
    from bot.utils.rate_limiter import cleanup_rate_limits, get_rate_limiter
except ImportError:
    from api.sports_api import SportsAPI
    from services.live_game_channel_service import LiveGameChannelService
    from utils.error_handler import (
        get_error_handler,
        initialize_default_recovery_strategies,
    )
    from utils.game_line_image_generator import GameLineImageGenerator
    from utils.parlay_image_generator import ParlayImageGenerator
    from utils.performance_monitor import background_monitoring, get_performance_monitor
    from utils.player_prop_image_generator import PlayerPropImageGenerator
    from utils.rate_limiter import cleanup_rate_limits, get_rate_limiter

# --- Logging Setup ---
# Use new centralized logging configuration
try:
    from bot.utils.logging_config import auto_configure_logging
    auto_configure_logging()
except ImportError:
    try:
        from utils.logging_config import auto_configure_logging
        auto_configure_logging()
    except ImportError:
        # Fallback to basic logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Path Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")

if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)
    print(f"Loaded environment variables from: {DOTENV_PATH}")
else:
    PARENT_DOTENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
    if os.path.exists(PARENT_DOTENV_PATH):
        load_dotenv(dotenv_path=PARENT_DOTENV_PATH)
        print(f"Loaded environment variables from: {PARENT_DOTENV_PATH}")
    else:
        print(
            f"WARNING: .env file not found at {DOTENV_PATH} or {PARENT_DOTENV_PATH}")

# Validate configuration
try:
    validation_errors = validate_settings()
    if validation_errors:
        logger.warning(f"Configuration validation errors: {validation_errors}")
        logger.warning(
            "Some features may not work correctly without proper configuration")
    else:
        logger.info("Configuration validation passed")
except Exception as e:
    logger.warning(f"Could not validate configuration: {e}")

# Try to import with bot prefix first, then without
try:
    from bot.commands.sync_cog import setup_sync_cog
    from bot.data.db_manager import DatabaseManager
    from bot.services.admin_service import AdminService
    from bot.services.analytics_service import AnalyticsService
    from bot.services.bet_service import BetService
    from bot.services.data_sync_service import DataSyncService
    from bot.services.game_service import GameService
    from bot.services.platinum_service import PlatinumService
    from bot.services.predictive_service import PredictiveService
    from bot.services.user_service import UserService
    from bot.services.voice_service import VoiceService
except ImportError:
    from bot.commands.sync_cog import setup_sync_cog
    from bot.data.db_manager import DatabaseManager
    from bot.services.admin_service import AdminService
    from bot.services.analytics_service import AnalyticsService
    from bot.services.bet_service import BetService
    from bot.services.data_sync_service import DataSyncService
    from bot.services.game_service import GameService
    from bot.services.platinum_service import PlatinumService
    from bot.services.predictive_service import PredictiveService
    from bot.services.user_service import UserService
    from bot.services.voice_service import VoiceService

# --- Environment Variable Validation ---
# Define required environment variables
REQUIRED_ENV_VARS = {
    "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
    "API_KEY": os.getenv("API_KEY"),
    "MYSQL_HOST": os.getenv("MYSQL_HOST"),
    "MYSQL_USER": os.getenv("MYSQL_USER"),
    "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
    "MYSQL_DB": os.getenv("MYSQL_DB"),
    "TEST_GUILD_ID": os.getenv("TEST_GUILD_ID"),
}

# TEMPORARY FIX: Disable Redis to prevent freezing
os.environ["REDIS_DISABLED"] = "true"
logger.info("TEMPORARY FIX: Redis disabled to prevent startup freezing")

try:
    try:
        from bot.utils.environment_validator import validate_environment
    except ImportError:
        from utils.environment_validator import validate_environment

    if not validate_environment():
        logger.critical(
            "Environment validation failed. Please check your .env file.")
        sys.exit("Environment validation failed")
except ImportError:
    # Fallback to basic validation if environment validator is not available
    missing_vars = [key for key,
                    value in REQUIRED_ENV_VARS.items() if not value]
    if missing_vars:
        logger.critical(
            "Missing required environment variables: %s", ", ".join(
                missing_vars)
        )
        sys.exit("Missing required environment variables")

# Get test guild ID
TEST_GUILD_ID = (
    int(REQUIRED_ENV_VARS["TEST_GUILD_ID"])
    if REQUIRED_ENV_VARS["TEST_GUILD_ID"]
    else None
)
logger.info(
    f"Loaded TEST_GUILD_ID: {TEST_GUILD_ID} (type: {type(TEST_GUILD_ID)})")

# --- Path for the logo download script and flag file ---
LOGO_DOWNLOAD_SCRIPT_PATH = os.path.join(
    BASE_DIR, "utils", "download_team_logos.py")
LOGO_DOWNLOAD_FLAG_FILE = os.path.join(
    BASE_DIR, "data", ".logos_downloaded_flag")


async def run_one_time_logo_download():
    """Checks if logos have been downloaded and runs the download script if not."""
    if not os.path.exists(LOGO_DOWNLOAD_FLAG_FILE):
        logger.info(
            "First server start or flag file missing: Attempting to download team logos..."
        )
        if not os.path.exists(LOGO_DOWNLOAD_SCRIPT_PATH):
            logger.error(
                "Logo download script not found at: %s", LOGO_DOWNLOAD_SCRIPT_PATH
            )
            return

        try:
            logger.info("Executing %s to download logos...",
                        LOGO_DOWNLOAD_SCRIPT_PATH)
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                LOGO_DOWNLOAD_SCRIPT_PATH,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=BASE_DIR,
            )
            stdout, stderr = await process.communicate()

            if stdout:
                logger.info("Logo Script STDOUT:\n%s", stdout.decode().strip())
            if stderr:
                logger.warning("Logo Script STDERR:\n%s",
                               stderr.decode().strip())

            if process.returncode == 0:
                logger.info("Logo download script finished (Return Code: 0).")
                os.makedirs(os.path.dirname(
                    LOGO_DOWNLOAD_FLAG_FILE), exist_ok=True)
                with open(LOGO_DOWNLOAD_FLAG_FILE, "w") as f:
                    f.write(datetime.now(timezone.utc).isoformat())
                logger.info("Created flag file: %s", LOGO_DOWNLOAD_FLAG_FILE)
            else:
                logger.error(
                    "Logo download script failed. Return code: %d", process.returncode
                )
        except Exception as e:
            logger.error(
                "Error running one-time logo download task: %s", e, exc_info=True
            )
    else:
        logger.info(
            "Logos already downloaded (flag file '%s' exists). Skipping download.",
            LOGO_DOWNLOAD_FLAG_FILE,
        )


# --- Path for the player data download script and flag file ---
PLAYER_DATA_DOWNLOAD_SCRIPT_PATH = os.path.join(
    BASE_DIR, "utils", "download_player_data.py"
)
PLAYER_DATA_DOWNLOAD_FLAG_FILE = os.path.join(
    BASE_DIR, "data", ".players_downloaded_flag"
)


async def run_one_time_player_data_download():
    """Checks if player data has been downloaded and runs the download script if not."""
    if not os.path.exists(PLAYER_DATA_DOWNLOAD_FLAG_FILE):
        logger.info(
            "First server start or flag file missing: Attempting to download player data..."
        )
        if not os.path.exists(PLAYER_DATA_DOWNLOAD_SCRIPT_PATH):
            logger.error(
                "Player data download script not found at: %s",
                PLAYER_DATA_DOWNLOAD_SCRIPT_PATH,
            )
            return

        try:
            logger.info(
                "Executing %s to download player data...",
                PLAYER_DATA_DOWNLOAD_SCRIPT_PATH,
            )
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                PLAYER_DATA_DOWNLOAD_SCRIPT_PATH,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=BASE_DIR,
            )
            stdout, stderr = await process.communicate()

            if stdout:
                logger.info("Player Data Script STDOUT:\n%s",
                            stdout.decode().strip())
            if stderr:
                logger.warning(
                    "Player Data Script STDERR:\n%s", stderr.decode().strip()
                )

            if process.returncode == 0:
                logger.info(
                    "Player data download script finished (Return Code: 0).")
                os.makedirs(
                    os.path.dirname(PLAYER_DATA_DOWNLOAD_FLAG_FILE), exist_ok=True
                )
                with open(PLAYER_DATA_DOWNLOAD_FLAG_FILE, "w") as f:
                    f.write(datetime.now(timezone.utc).isoformat())
                logger.info("Created flag file: %s",
                            PLAYER_DATA_DOWNLOAD_FLAG_FILE)
            else:
                logger.error(
                    "Player data download script failed. Return code: %d",
                    process.returncode,
                )
        except Exception as e:
            logger.error(
                "Error running one-time player data download task: %s", e, exc_info=True
            )
    else:
        logger.info(
            "Player data already downloaded (flag file '%s' exists). Skipping download.",
            PLAYER_DATA_DOWNLOAD_FLAG_FILE,
        )


# --- Bot Definition ---
class BettingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("/"), intents=intents
        )
        self.db_manager = DatabaseManager()
        self.db = self.db_manager
        self.admin_service = AdminService(self, self.db_manager)
        self.analytics_service = AnalyticsService(self.db_manager)
        self.bet_service = BetService(self, self.db_manager)
        self.sports_api = SportsAPI(self.db_manager)
        self.game_service = GameService(self.sports_api, self.db_manager)
        self.user_service = UserService(self, self.db_manager)
        self.voice_service = VoiceService(self, self.db_manager)
        # Initialize data_sync_service without the circular dependency
        self.data_sync_service = DataSyncService(None, self.db_manager)
        # Set up the circular dependency after initialization
        self.game_service.set_data_sync_service(self.data_sync_service)
        self.data_sync_service.game_service = self.game_service
        self.bet_slip_generators = {}
        self.webapp_process = None
        self.fetcher_process = None
        self.live_game_channel_service = LiveGameChannelService(
            self, self.db_manager)
        self.platinum_service = PlatinumService(self.db_manager, self)
        self.predictive_service = PredictiveService(self.db_manager)
        self.real_ml_service = None  # Will be initialized in setup_hook
        self.rate_limiter = None  # Will be initialized in setup_hook
        self.performance_monitor = None  # Will be initialized in setup_hook
        self.error_handler = None  # Will be initialized in setup_hook
        # Community engagement services will be initialized in setup_hook
        self.community_events_service = None
        self.community_analytics_service = None
        # System integration services will be initialized in setup_hook
        self.system_integration_service = None

    async def get_bet_slip_generator(
        self, guild_id: int, bet_type: str = "game_line"
    ) -> Union[GameLineImageGenerator, ParlayImageGenerator, PlayerPropImageGenerator]:
        if guild_id not in self.bet_slip_generators:
            if bet_type == "parlay":
                self.bet_slip_generators[guild_id] = ParlayImageGenerator(
                    guild_id=guild_id
                )
            elif bet_type == "player_prop":
                self.bet_slip_generators[guild_id] = PlayerPropImageGenerator(
                    guild_id=guild_id
                )
            else:
                self.bet_slip_generators[guild_id] = GameLineImageGenerator(
                    guild_id=guild_id
                )
        return self.bet_slip_generators[guild_id]

    async def load_extensions(self):
        commands_dir = os.path.join(BASE_DIR, "commands")
        cog_files = [
            "admin.py",  # Load admin.py first since it contains setup command
            "betting.py",
            "enhanced_player_props.py",  # Enhanced player props command
            "parlay_betting.py",  # Parlay betting command
            "remove_user.py",
            "setid.py",
            "add_user.py",
            "stats.py",
            "load_logos.py",
            "schedule.py",
            "maintenance.py",
            "odds.py",  # New odds command
            "platinum_fixed.py",  # Platinum tier commands (fixed version)
            "platinum_api.py",  # Platinum API commands
            "sync_cog.py",  # Sync commands
            "community.py",  # Community engagement commands
            "community_leaderboard.py",  # Community leaderboard commands
            "predictive.py",  # Predictive analytics commands
            "real_ml_commands.py",  # Real ML commands (Platinum only)
            "weather.py",  # Weather command for game venues
        ]
        loaded_commands = []
        for filename in cog_files:
            file_path = os.path.join(commands_dir, filename)
            if os.path.exists(file_path):
                extension = f"bot.commands.{filename[:-3]}"
                try:
                    await self.load_extension(extension)
                    loaded_commands.append(extension)
                    logger.info("Successfully loaded extension: %s", extension)
                except Exception as e:
                    logger.error(
                        "Failed to load extension %s: %s", extension, e, exc_info=True
                    )
            else:
                logger.warning("Command file not found: %s", file_path)
        logger.info("Total loaded extensions: %s", loaded_commands)
        commands_list = [cmd.name for cmd in self.tree.get_commands()]
        logger.info("Available commands after loading: %s", commands_list)

    async def sync_commands_with_retry(self, retries: int = 3, delay: int = 5):
        """Sync commands globally with retry logic."""
        for attempt in range(1, retries + 1):
            try:
                # Get all commands BEFORE clearing anything
                all_commands = self.tree.get_commands()
                if not all_commands:
                    logger.error("No commands found")
                    raise Exception("No commands found")

                # Get setup command
                setup_command = self.tree.get_command("setup")
                if not setup_command:
                    logger.error("Setup command not found")
                    raise Exception("Setup command not found")

                # Store command names that should go to guilds
                guild_command_names = []
                for cmd in all_commands:
                    if cmd.name not in ("setup", "load_logos", "down", "up"):
                        guild_command_names.append(cmd.name)

                logger.info(
                    f"Stored {len(guild_command_names)} command names for guild syncing: {guild_command_names}"
                )

                # Clear all commands globally first
                self.tree.clear_commands(guild=None)

                # Add setup command globally
                self.tree.add_command(setup_command, guild=None)
                await self.tree.sync()
                logger.info("Global setup command synced")

                # Get all guilds from the table
                guilds_query = """
                    SELECT guild_id, is_paid, subscription_level
                    FROM guild_settings
                """
                guilds = await self.db_manager.fetch_all(guilds_query)

                # Get all guild IDs that are in the database
                db_guild_ids = {guild["guild_id"] for guild in guilds}

                # Sync commands to each guild in the table
                for guild in guilds:
                    guild_id = guild["guild_id"]
                    is_paid = guild["is_paid"]
                    subscription_level = "premium" if is_paid else "initial"
                    logger.debug(
                        f"Processing guild {guild_id} (type: {type(guild_id)}) with subscription {subscription_level}"
                    )

                    # Update subscription level if needed
                    if is_paid and subscription_level != "premium":
                        await self.db_manager.execute(
                            """
                            UPDATE guild_settings
                            SET subscription_level = 'premium'
                            WHERE guild_id = %s
                            """,
                            (guild_id,),
                        )

                    guild_obj = discord.Object(id=guild_id)

                    # Clear existing commands for this guild
                    self.tree.clear_commands(guild=guild_obj)

                    # Special handling for test guild - only add restricted commands
                    logger.debug(
                        f"Checking guild {guild_id} against TEST_GUILD_ID {TEST_GUILD_ID} (types: {type(guild_id)} vs {type(TEST_GUILD_ID)})"
                    )
                    if guild_id == TEST_GUILD_ID:
                        restricted_commands = ["load_logos", "down", "up"]
                        for cmd_name in restricted_commands:
                            cmd = self.tree.get_command(cmd_name)
                            if cmd:
                                self.tree.add_command(cmd, guild=guild_obj)
                        logger.info(
                            f"Synced restricted commands to test guild {guild_id}"
                        )
                    else:
                        # Add all commands except setup, load_logos, and maintenance commands to the guild
                        commands_added = 0
                        for cmd_name in guild_command_names:
                            try:
                                # Get the command from the original all_commands list
                                cmd = next(
                                    (c for c in all_commands if c.name == cmd_name),
                                    None,
                                )
                                if cmd:
                                    self.tree.add_command(cmd, guild=guild_obj)
                                    commands_added += 1
                                else:
                                    logger.warning(
                                        f"Command {cmd_name} not found in all_commands"
                                    )
                            except Exception as e:
                                logger.error(
                                    f"Failed to add command {cmd_name} to guild {guild_id}: {e}"
                                )

                        logger.info(
                            f"Synced {commands_added} commands to guild {guild_id} (subscription: {subscription_level})"
                        )

                    # Sync commands to this guild
                    await self.tree.sync(guild=guild_obj)

                # Handle test guild if it's not in the database
                if TEST_GUILD_ID and TEST_GUILD_ID not in db_guild_ids:
                    logger.info(
                        f"Test guild {TEST_GUILD_ID} not in database, syncing restricted commands"
                    )
                    test_guild_obj = discord.Object(id=TEST_GUILD_ID)
                    self.tree.clear_commands(guild=test_guild_obj)

                    restricted_commands = ["load_logos", "down", "up"]
                    for cmd_name in restricted_commands:
                        cmd = self.tree.get_command(cmd_name)
                        if cmd:
                            self.tree.add_command(cmd, guild=test_guild_obj)

                    await self.tree.sync(guild=test_guild_obj)
                    logger.info(
                        f"Synced restricted commands to test guild {TEST_GUILD_ID} (not in database)"
                    )

                # Log all available commands
                global_commands = [
                    cmd.name for cmd in self.tree.get_commands()]
                logger.info("Final global commands: %s", global_commands)

                return True
            except Exception as e:
                logger.error(
                    "Sync attempt %d/%d failed: %s", attempt, retries, e, exc_info=True
                )
                if attempt < retries:
                    await asyncio.sleep(delay)
        logger.error("Failed to sync commands after %d attempts.", retries)
        return False

    def start_flask_webapp(self):
        """Start the Flask webapp as a subprocess with enhanced monitoring for PebbleHost."""
        if self.webapp_process is None or self.webapp_process.poll() is not None:
            webapp_log_path = os.path.join(BASE_DIR, "logs", "webapp.log")
            os.makedirs(os.path.dirname(webapp_log_path), exist_ok=True)

            # Prepare environment variables for the webapp
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["FLASK_ENV"] = "production"
            env["FLASK_DEBUG"] = "0"

            # Add any webapp-specific environment variables
            webapp_port = os.getenv("WEBAPP_PORT", "25594")
            env["WEBAPP_PORT"] = webapp_port

            try:
                with open(webapp_log_path, "a") as log_file:
                    # Get the correct path to webapp.py (it's in the root directory)
                    webapp_path = os.path.join(
                        os.path.dirname(BASE_DIR), "webapp.py")

                    if not os.path.exists(webapp_path):
                        logger.error(f"webapp.py not found at {webapp_path}")
                        return

                    self.webapp_process = subprocess.Popen(
                        [
                            sys.executable,
                            webapp_path,
                        ],
                        stdout=log_file,
                        stderr=log_file,
                        text=True,
                        bufsize=1,
                        env=env,
                        # Set working directory to project root where webapp.py is located
                        cwd=os.path.dirname(BASE_DIR),
                    )
                logger.info(
                    "Started Flask web server (webapp.py) as a subprocess with PID %d, logging to %s",
                    self.webapp_process.pid,
                    webapp_log_path,
                )

                # Create monitoring task if not already running
                if not hasattr(self, "_webapp_monitor_task"):
                    self._webapp_monitor_task = asyncio.create_task(
                        self._monitor_webapp(webapp_log_path)
                    )
                    logger.info("Created webapp monitoring task")

            except Exception as e:
                logger.error("Failed to start Flask webapp: %s",
                             e, exc_info=True)
                self.webapp_process = None

    async def _monitor_webapp(self, log_path: str):
        """Monitor the webapp process and restart it if it crashes."""
        while True:
            try:
                if self.webapp_process is None:
                    logger.warning(
                        "Webapp process is None, attempting to restart...")
                    self.start_flask_webapp()
                    await asyncio.sleep(10)  # Wait before checking again
                    continue

                # Check if process is still running
                if self.webapp_process.poll() is not None:
                    logger.warning(
                        "Webapp process (PID %d) has stopped with return code %d. Restarting...",
                        self.webapp_process.pid,
                        self.webapp_process.returncode,
                    )
                    self.webapp_process = None
                    self.start_flask_webapp()
                    await asyncio.sleep(5)  # Wait before checking again
                else:
                    # Process is running, check every 30 seconds
                    await asyncio.sleep(30)

            except Exception as e:
                logger.error("Error in webapp monitoring: %s",
                             e, exc_info=True)
                await asyncio.sleep(10)  # Wait before retrying

    def start_fetcher(self):
        """Start the fetcher process and monitor its status."""
        if self.fetcher_process is None or self.fetcher_process.poll() is not None:
            fetcher_log_path = os.path.join(BASE_DIR, "logs", "fetcher.log")
            os.makedirs(os.path.dirname(fetcher_log_path), exist_ok=True)
            logger.info(
                "Setting up fetcher process with log at: %s", fetcher_log_path)

            with open(fetcher_log_path, "a") as log_file:
                # Prepare environment variables
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                env["LOG_LEVEL"] = "DEBUG"

                # Critical environment variables for fetcher
                required_vars = {
                    "API_KEY": os.getenv("API_KEY"),
                    "MYSQL_HOST": os.getenv("MYSQL_HOST"),
                    "MYSQL_PORT": os.getenv("MYSQL_PORT", "3306"),
                    "MYSQL_USER": os.getenv("MYSQL_USER"),
                    "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
                    "MYSQL_DB": os.getenv("MYSQL_DB"),
                    "MYSQL_POOL_MIN_SIZE": os.getenv("MYSQL_POOL_MIN_SIZE", "1"),
                    "MYSQL_POOL_MAX_SIZE": os.getenv("MYSQL_POOL_MAX_SIZE", "10"),
                }

                # Validate all required variables are present
                missing_vars = [
                    var for var, value in required_vars.items() if not value
                ]
                if missing_vars:
                    logger.error(
                        "Missing required environment variables for fetcher: %s",
                        ", ".join(missing_vars),
                    )
                    return False

                # Add validated variables to environment
                for var, value in required_vars.items():
                    env[var] = str(value)
                    logger.info(
                        "Passing %s=%s to fetcher process",
                        var,
                        "*" * len(str(value)) if "PASSWORD" in var else value,
                    )

                try:
                    # Start the fetcher process with the validated environment
                    logger.info("Starting fetcher process...")
                    self.fetcher_process = subprocess.Popen(
                        [sys.executable, os.path.join(
                            BASE_DIR, "utils", "fetcher.py")],
                        stdout=log_file,
                        stderr=log_file,
                        text=True,
                        bufsize=1,
                        env=env,
                        cwd=BASE_DIR,
                    )
                    logger.info(
                        "Started fetcher (fetcher.py) as subprocess with PID %d",
                        self.fetcher_process.pid,
                    )

                    # Create monitoring task if not already running
                    if not hasattr(self, "_fetcher_monitor_task"):
                        self._fetcher_monitor_task = asyncio.create_task(
                            self._monitor_fetcher(fetcher_log_path)
                        )
                        logger.info("Created fetcher monitoring task")

                    return True
                except Exception as e:
                    logger.error(
                        "Failed to start fetcher process: %s", e, exc_info=True
                    )
                    return False

    async def _monitor_fetcher(self, log_path: str):
        """Monitor the fetcher process and restart it if it crashes."""
        while True:
            if self.fetcher_process is None:
                logger.error("Fetcher process object is None")
                await asyncio.sleep(5)
                self.start_fetcher()
                continue

            if self.fetcher_process.poll() is not None:
                return_code = self.fetcher_process.returncode

                if return_code == 0:
                    # Fetcher exited successfully - this might be unexpected since it should run continuously
                    logger.warning(
                        "Fetcher process exited with return code 0 - restarting to maintain continuous operation"
                    )
                    # Restart the fetcher to maintain continuous operation
                    await asyncio.sleep(5)
                    logger.info(
                        "Restarting fetcher process to maintain continuous operation..."
                    )
                    self.start_fetcher()
                else:
                    # Fetcher crashed with error - restart it
                    logger.error(
                        "Fetcher process crashed with return code %d",
                        return_code,
                    )

                    # Get last few lines of log for context
                    try:
                        with open(log_path, "r") as f:
                            lines = f.readlines()
                            last_lines = lines[-20:] if len(
                                lines) > 20 else lines
                            logger.error(
                                "Last few lines from fetcher.log:\n%s",
                                "".join(last_lines),
                            )
                    except Exception as e:
                        logger.error("Failed to read fetcher.log: %s", e)

                    # Wait a bit before restarting
                    await asyncio.sleep(5)
                    logger.info("Restarting crashed fetcher process...")
                    self.start_fetcher()

            await asyncio.sleep(5)  # Check every 5 seconds

    async def setup_hook(self):
        """Initialize the bot and load extensions."""
        logger.info("Starting setup_hook...")

        # Add timeout wrapper to prevent hanging
        try:
            await asyncio.wait_for(self._setup_hook_internal(), timeout=60.0)
        except asyncio.TimeoutError:
            logger.error("Bot setup_hook timed out after 60 seconds")
            raise RuntimeError("Bot initialization timed out")
        except Exception as e:
            logger.error(f"Bot setup_hook failed: {e}")
            raise

    async def _setup_hook_internal(self):
        """Internal setup_hook implementation."""
        logger.info("Step 1: Starting one-time downloads...")
        await run_one_time_logo_download()
        await run_one_time_player_data_download()
        logger.info("Step 1: One-time downloads completed")

        logger.info("Step 2: Connecting to database...")
        await self.db_manager.connect()
        if not self.db_manager._pool:
            logger.critical(
                "Database connection pool failed to initialize. Bot cannot continue."
            )
            await self.close()
            sys.exit("Database connection failed.")
        logger.info("Step 2: Database connection successful")

        # Initialize database schema
        try:
            logger.info("Step 3: Initializing database schema...")
            await self.db_manager.initialize_db()
            logger.info("Database schema initialized successfully.")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            # Don't exit, just log the error and continue
            # The bot can still function with basic features

        # Only load extensions if we're not in scheduler mode
        if not os.getenv("SCHEDULER_MODE"):
            logger.info("Step 4: Loading extensions...")
            await self.load_extensions()
            commands_list = [cmd.name for cmd in self.tree.get_commands()]
            logger.info("Registered commands: %s", commands_list)
        else:
            logger.info("Step 4: Skipping extension loading (scheduler mode)")

        logger.info("Step 5: Starting services...")

        # Initialize community engagement services
        try:
            logger.info("Step 5a: Initializing community services...")
            from bot.services.community_analytics import CommunityAnalyticsService
            from bot.services.community_events import CommunityEventsService

            self.community_events_service = CommunityEventsService(
                self, self.db_manager
            )
            self.community_analytics_service = CommunityAnalyticsService(
                self, self.db_manager
            )
            logger.info("Community engagement services initialized")
        except Exception as e:
            logger.error(
                f"Failed to initialize community engagement services: {e}")
            self.community_events_service = None
            self.community_analytics_service = None

        logger.info("Step 5b: Starting core services...")
        service_starts = [
            self.admin_service.start(),
            self.analytics_service.start(),
            self.bet_service.start(),
            self.user_service.start(),
            self.voice_service.start(),
            self.game_service.start(),
            self.data_sync_service.start(),
            self.live_game_channel_service.start(),
            self.platinum_service.start(),
            self.predictive_service.start(),
        ]

        # Initialize real ML service
        try:
            logger.info("Step 5c: Initializing ML service...")
            from bot.services.real_ml_service import RealMLService
            self.real_ml_service = RealMLService(
                self.db_manager, self.sports_api, self.predictive_service)
            logger.info("Real ML service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize real ML service: {e}")
            self.real_ml_service = None

        # Add community services if initialized
        if self.community_events_service:
            service_starts.append(self.community_events_service.start())
        if self.community_analytics_service:
            service_starts.append(self.community_analytics_service.start())

        # Initialize system integration service
        try:
            logger.info("Step 5d: Initializing system integration service...")
            from bot.services.system_integration_service import SystemIntegrationService
            self.system_integration_service = SystemIntegrationService(
                self.db_manager)
            service_starts.append(self.system_integration_service.start())
            logger.info("System integration service initialized")
        except Exception as e:
            logger.error(
                f"Failed to initialize system integration service: {e}")
            self.system_integration_service = None

        # Initialize rate limiter
        try:
            logger.info("Step 5e: Initializing rate limiter...")
            self.rate_limiter = get_rate_limiter()
            logger.info("Rate limiter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
            raise

        # Initialize performance monitor
        try:
            logger.info("Step 5f: Initializing performance monitor...")
            self.performance_monitor = get_performance_monitor()
            logger.info("Performance monitor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize performance monitor: {e}")
            raise

        # Initialize error handler
        try:
            logger.info("Step 5g: Initializing error handler...")
            self.error_handler = get_error_handler()
            initialize_default_recovery_strategies()
            logger.info("Error handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize error handler: {e}")
            raise

        logger.info("Step 5h: Starting all services...")
        results = await asyncio.gather(*service_starts, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = (
                    service_starts[i].__self__.__class__.__name__
                    if hasattr(service_starts[i], "__self__")
                    else f"Service {i}"
                )
                logger.error(
                    "Error starting %s: %s", service_name, result, exc_info=True
                )
        logger.info(
            "Services startup initiated, including LiveGameChannelService.")

        # Only start webapp and fetcher if not in scheduler mode
        if not os.getenv("SCHEDULER_MODE"):
            logger.info("Step 6: Starting webapp and fetcher...")
            self.start_flask_webapp()
            self.start_fetcher()
            logger.info(
                "Bot setup_hook completed successfully - commands will be synced in on_ready"
            )
        else:
            logger.info(
                "Bot setup_hook completed successfully in scheduler mode")

    async def on_ready(self):
        logger.info("Logged in as %s (%s)", self.user.name, self.user.id)
        logger.info("discord.py API version: %s", discord.__version__)
        logger.info("Python version: %s", sys.version)
        logger.info("Connected to %d guilds.", len(self.guilds))
        for guild in self.guilds:
            logger.debug("- %s (%s)", guild.name, guild.id)
        logger.info("Latency: %.2f ms", self.latency * 1000)

        # Only sync commands if not in scheduler mode
        if not os.getenv("SCHEDULER_MODE"):
            try:
                # Single point of command syncing
                success = await self.sync_commands_with_retry()
                if not success:
                    logger.error("Failed to sync commands after retries")
                    return
                global_commands = [
                    cmd.name for cmd in self.tree.get_commands()]
                logger.info("Final global commands: %s", global_commands)
            except Exception as e:
                logger.error("Failed to sync command tree: %s",
                             e, exc_info=True)
        logger.info("------ Bot is Ready ------")

    async def on_guild_join(self, guild: discord.Guild):
        """Handle when the bot joins a new guild."""
        logger.info("Joined new guild: %s (%s)", guild.name, guild.id)
        try:
            # Get setup command
            setup_command = self.tree.get_command("setup")
            if not setup_command:
                logger.error("Setup command not found")
                return

            # Add and sync setup command to new guild
            guild_obj = discord.Object(id=guild.id)
            self.tree.clear_commands(guild=guild_obj)
            self.tree.add_command(setup_command, guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            logger.info(
                f"Successfully synced setup command to new guild {guild.id}")
        except Exception as e:
            logger.error(
                f"Failed to sync setup command to new guild {guild.id}: {e}",
                exc_info=True,
            )

    async def on_setup_complete(self, guild_id: int):
        """Handle when a guild completes the setup process."""
        try:
            guild_obj = discord.Object(id=guild_id)
            # Add all commands except load_logos to the guild
            for cmd in self.tree.get_commands():
                if cmd.name != "load_logos":
                    self.tree.add_command(cmd, guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            logger.info(
                f"Successfully synced all commands to guild {guild_id} after setup completion"
            )
        except Exception as e:
            logger.error(
                f"Failed to sync commands to guild {guild_id} after setup: {e}",
                exc_info=True,
            )

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.user.id:
            return
        if hasattr(self, "bet_service"):
            logger.debug(
                "Processing reaction add: %s by %s on bot message %s",
                payload.emoji,
                payload.user_id,
                payload.message_id,
            )
            asyncio.create_task(self.bet_service.on_raw_reaction_add(payload))

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.user.id:
            return
        if (
            hasattr(self, "bet_service")
            and hasattr(self.bet_service, "pending_reactions")
            and payload.message_id in self.bet_service.pending_reactions
        ):
            logger.debug(
                "Processing reaction remove: %s by %s on bot message %s",
                payload.emoji,
                payload.user_id,
                payload.message_id,
            )
            asyncio.create_task(
                self.bet_service.on_raw_reaction_remove(payload))

    async def on_interaction(self, interaction: discord.Interaction):
        command_name = interaction.command.name if interaction.command else "N/A"
        logger.debug(
            "Interaction: type=%s, cmd=%s, user=%s(ID:%s), guild=%s, ch=%s",
            interaction.type,
            command_name,
            interaction.user,
            interaction.user.id,
            interaction.guild_id,
            interaction.channel_id,
        )

    async def close(self):
        logger.info("Initiating graceful shutdown...")
        try:
            logger.info("Stopping services...")
            stop_tasks = [
                self.admin_service.stop(),
                self.analytics_service.stop(),
                self.bet_service.stop(),
                self.user_service.stop(),
                self.voice_service.stop(),
                self.game_service.stop(),
                self.data_sync_service.stop(),
                self.live_game_channel_service.stop(),
            ]
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*stop_tasks, return_exceptions=True), timeout=15.0
                )
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        service_name = (
                            stop_tasks[i].__self__.__class__.__name__
                            if hasattr(stop_tasks[i], "__self__")
                            else f"Service {i}"
                        )
                        logger.error(
                            "Error stopping %s: %s", service_name, result, exc_info=True
                        )
            except asyncio.TimeoutError:
                logger.warning("Timeout while waiting for services to stop")
            except Exception as e:
                logger.error("Error during service shutdown: %s",
                             e, exc_info=True)
            logger.info("Services stopped.")

            if self.db_manager:
                logger.info("Closing database connection pool...")
                try:
                    await asyncio.wait_for(self.db_manager.close(), timeout=5.0)
                    logger.info("Database connection pool closed.")
                except asyncio.TimeoutError:
                    logger.warning(
                        "Timeout while closing database connection pool")
                except Exception as e:
                    logger.error(
                        "Error closing database connection pool: %s", e, exc_info=True
                    )

            # Stop webapp monitoring task
            if hasattr(self, "_webapp_monitor_task") and not self._webapp_monitor_task.done():
                self._webapp_monitor_task.cancel()
                try:
                    await self._webapp_monitor_task
                except asyncio.CancelledError:
                    pass
                logger.info("Stopped webapp monitoring task.")

            # Stop webapp process
            if self.webapp_process and self.webapp_process.poll() is None:
                try:
                    self.webapp_process.send_signal(signal.SIGINT)
                    self.webapp_process.wait(timeout=5)
                    logger.info("Stopped Flask web server subprocess.")
                except Exception as e:
                    logger.error("Error stopping webapp process: %s", e)
                    try:
                        self.webapp_process.terminate()
                        self.webapp_process.wait(timeout=3)
                    except Exception as e2:
                        logger.error(
                            "Error terminating webapp process: %s", e2)

            # Stop fetcher monitoring task
            if hasattr(self, "_fetcher_monitor_task") and not self._fetcher_monitor_task.done():
                self._fetcher_monitor_task.cancel()
                try:
                    await self._fetcher_monitor_task
                except asyncio.CancelledError:
                    pass
                logger.info("Stopped fetcher monitoring task.")

            # Stop fetcher process
            if self.fetcher_process and self.fetcher_process.poll() is None:
                try:
                    self.fetcher_process.send_signal(signal.SIGINT)
                    self.fetcher_process.wait(timeout=5)
                    logger.info("Stopped fetcher subprocess.")
                except Exception as e:
                    logger.error("Error stopping fetcher process: %s", e)
                    try:
                        self.fetcher_process.terminate()
                        self.fetcher_process.wait(timeout=3)
                    except Exception as e2:
                        logger.error(
                            "Error terminating fetcher process: %s", e2)
        except Exception as e:
            logger.exception("Error during shutdown: %s", e)
        finally:
            logger.info("Closing Discord client connection...")
            try:
                await super().close()
            except Exception as e:
                logger.error("Error closing Discord client: %s",
                             e, exc_info=True)
            logger.info("Bot shutdown complete.")


# --- Manual Sync Command (as a Cog) ---
class SyncCog(commands.Cog):
    def __init__(self, bot: BettingBot):
        self.bot = bot

    @app_commands.command(
        name="sync", description="Manually sync bot commands (admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_command(self, interaction: discord.Interaction):
        logger.info(
            "Manual sync initiated by %s in guild %s",
            interaction.user,
            interaction.guild_id,
        )
        try:
            await interaction.response.defer(ephemeral=True)
            commands_list = [cmd.name for cmd in self.bot.tree.get_commands()]
            logger.debug("Commands to sync: %s", commands_list)
            await self.bot.sync_commands_with_retry()
            await interaction.followup.send(
                "Global commands synced successfully!", ephemeral=True
            )
        except Exception as e:
            logger.error("Failed to sync commands: %s", e, exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"Failed to sync commands: {e}", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"Failed to sync commands: {e}", ephemeral=True
                )


async def setup_sync_cog(bot: BettingBot):
    await bot.add_cog(SyncCog(bot))
    logger.info("SyncCog loaded")


# Add a manual sync command to AdminService or a new AdminCog


class ManualSyncCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def synccommands(self, ctx):
        """Manually sync commands to the test guild."""
        test_guild_id = (
            int(os.getenv("TEST_GUILD_ID")) if os.getenv(
                "TEST_GUILD_ID") else None
        )
        if test_guild_id:
            await ctx.bot.tree.sync(guild=discord.Object(id=test_guild_id))
            await ctx.send(f"Commands synced to test guild {test_guild_id}!")
        else:
            await ctx.send("TEST_GUILD_ID not set. Cannot sync commands.")

    # Register the manual sync cog in BettingBot.setup_hook
    async def setup_hook(self):
        logger.info("Starting setup_hook...")
        await run_one_time_logo_download()
        await run_one_time_player_data_download()
        await self.db_manager.connect()
        if not self.db_manager._pool:
            logger.critical(
                "Database connection pool failed to initialize. Bot cannot continue."
            )
            await self.close()
            sys.exit("Database connection failed.")

            # Note: Database schema initialization is handled by DatabaseManager.initialize_db()
        # No need to create tables here as they already exist

        if not os.getenv("SCHEDULER_MODE"):
            await self.load_extensions()
            commands_list = [cmd.name for cmd in self.tree.get_commands()]
            logger.info("Registered commands: %s", commands_list)
        logger.info("Starting services...")
        service_starts = [
            self.admin_service.start(),
            self.analytics_service.start(),
            self.bet_service.start(),
            self.user_service.start(),
            self.voice_service.start(),
            self.game_service.start(),
            self.data_sync_service.start(),
            self.live_game_channel_service.start(),
        ]
        results = await asyncio.gather(*service_starts, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = (
                    service_starts[i].__self__.__class__.__name__
                    if hasattr(service_starts[i], "__self__")
                    else f"Service {i}"
                )
                logger.error(
                    "Error starting %s: %s", service_name, result, exc_info=True
                )
        logger.info(
            "Services startup initiated, including LiveGameChannelService.")
        # Register the manual sync cog
        self.add_cog(ManualSyncCog(self))
        if not os.getenv("SCHEDULER_MODE"):
            self.start_flask_webapp()
            self.start_fetcher()
            logger.info(
                "Bot setup_hook completed successfully - commands will be synced in on_ready"
            )
        else:
            logger.info(
                "Bot setup_hook completed successfully in scheduler mode")


# --- Main Execution ---
async def run_bot():
    """Run the bot with retry logic for connection issues."""
    retry_count = 0
    max_retries = 5
    retry_delay = 5  # seconds
    while retry_count < max_retries:
        try:
            logger.info("Attempting to start bot...")
            bot = BettingBot()

            # Add timeout to bot startup
            try:
                await asyncio.wait_for(bot.start(REQUIRED_ENV_VARS["DISCORD_TOKEN"]), timeout=120.0)
                logger.info("Bot started successfully")
                break
            except asyncio.TimeoutError:
                logger.error("Bot startup timed out after 120 seconds")
                await bot.close()
                raise RuntimeError("Bot startup timed out")
            except Exception as e:
                logger.error(f"Bot startup failed: {e}")
                await bot.close()
                raise

        except discord.LoginFailure:
            logger.critical(
                "Login failed: Invalid Discord token provided in .env file."
            )
            break
        except discord.PrivilegedIntentsRequired as e:
            shard_id_info = f" (Shard ID: {e.shard_id})" if e.shard_id else ""
            logger.critical(
                "Privileged Intents%s are required but not enabled in the Discord Developer Portal.",
                shard_id_info,
            )
            logger.critical(
                "Enable 'Presence Intent', 'Server Members Intent', and 'Message Content Intent'."
            )
            break
        except (discord.HTTPException, aiohttp.ClientError, asyncio.TimeoutError) as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    "Connection error occurred (attempt %d/%d): %s",
                    retry_count,
                    max_retries,
                    e,
                )
                logger.info("Retrying in %d seconds...", retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.critical(
                    "Failed to connect after %d attempts. Last error: %s",
                    max_retries,
                    e,
                )
                break
        except Exception as e:
            logger.critical(
                "An unexpected error occurred while running the bot: %s",
                e,
                exc_info=True,
            )
            break


def main():
    try:
        logger.info("Starting bot...")
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested via KeyboardInterrupt.")
    except Exception as e:
        logger.critical(
            "An unexpected error occurred while running the bot: %s", e, exc_info=True
        )
    finally:
        logger.info("Bot process finished.")


if __name__ == "__main__":
    main()
