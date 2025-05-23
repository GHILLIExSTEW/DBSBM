import os
import sys
import logging
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio
from typing import Optional
import subprocess
from datetime import datetime, timezone
from discord.ext import tasks
import signal
from api.sports_api import SportsAPI
import aiohttp
from services.live_game_channel_service import LiveGameChannelService

# --- Logging Setup ---
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
log_format = os.getenv("LOG_FORMAT", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This is betting-bot/
log_file_name = "bot_activity.log"
log_file_path = os.path.join(BASE_DIR, "logs", log_file_name) if not os.path.isabs(os.getenv("LOG_FILE", "")) else os.getenv("LOG_FILE", os.path.join(BASE_DIR, "logs", log_file_name))

log_dir = os.path.dirname(log_file_path)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Path Setup ---
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
        print(f"WARNING: .env file not found at {DOTENV_PATH} or {PARENT_DOTENV_PATH}")

from data.db_manager import DatabaseManager
from services.admin_service import AdminService
from services.analytics_service import AnalyticsService
from services.bet_service import BetService
from services.user_service import UserService
from services.voice_service import VoiceService
from services.data_sync_service import DataSyncService
from services.game_service import GameService
from utils.image_generator import BetSlipGenerator
from commands.sync_cog import setup_sync_cog

# --- Environment Variable Validation ---
REQUIRED_ENV_VARS = {
    "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
    "API_KEY": os.getenv("API_KEY"),
    "MYSQL_HOST": os.getenv("MYSQL_HOST"),
    "MYSQL_USER": os.getenv("MYSQL_USER"),
    "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
    "MYSQL_DB": os.getenv("MYSQL_DB"),
}
missing_vars = [key for key, value in REQUIRED_ENV_VARS.items() if not value]
if missing_vars:
    logger.critical("Missing required environment variables: %s", ", ".join(missing_vars))
    sys.exit("Missing required environment variables")

# --- Path for the logo download script and flag file ---
LOGO_DOWNLOAD_SCRIPT_PATH = os.path.join(BASE_DIR, "utils", "download_team_logos.py")
LOGO_DOWNLOAD_FLAG_FILE = os.path.join(BASE_DIR, "data", ".logos_downloaded_flag")

async def run_one_time_logo_download():
    """Checks if logos have been downloaded and runs the download script if not."""
    if not os.path.exists(LOGO_DOWNLOAD_FLAG_FILE):
        logger.info("First server start or flag file missing: Attempting to download team logos...")
        if not os.path.exists(LOGO_DOWNLOAD_SCRIPT_PATH):
            logger.error("Logo download script not found at: %s", LOGO_DOWNLOAD_SCRIPT_PATH)
            return

        try:
            logger.info("Executing %s to download logos...", LOGO_DOWNLOAD_SCRIPT_PATH)
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
                logger.warning("Logo Script STDERR:\n%s", stderr.decode().strip())

            if process.returncode == 0:
                logger.info("Logo download script finished (Return Code: 0).")
                os.makedirs(os.path.dirname(LOGO_DOWNLOAD_FLAG_FILE), exist_ok=True)
                with open(LOGO_DOWNLOAD_FLAG_FILE, "w") as f:
                    f.write(datetime.now(timezone.utc).isoformat())
                logger.info("Created flag file: %s", LOGO_DOWNLOAD_FLAG_FILE)
            else:
                logger.error("Logo download script failed. Return code: %d", process.returncode)
        except Exception as e:
            logger.error("Error running one-time logo download task: %s", e, exc_info=True)
    else:
        logger.info("Logos already downloaded (flag file '%s' exists). Skipping download.", LOGO_DOWNLOAD_FLAG_FILE)

# --- Path for the player data download script and flag file ---
PLAYER_DATA_DOWNLOAD_SCRIPT_PATH = os.path.join(BASE_DIR, "utils", "download_player_data.py")
PLAYER_DATA_DOWNLOAD_FLAG_FILE = os.path.join(BASE_DIR, "data", ".players_downloaded_flag")

async def run_one_time_player_data_download():
    """Checks if player data has been downloaded and runs the download script if not."""
    if not os.path.exists(PLAYER_DATA_DOWNLOAD_FLAG_FILE):
        logger.info("First server start or flag file missing: Attempting to download player data...")
        if not os.path.exists(PLAYER_DATA_DOWNLOAD_SCRIPT_PATH):
            logger.error("Player data download script not found at: %s", PLAYER_DATA_DOWNLOAD_SCRIPT_PATH)
            return

        try:
            logger.info("Executing %s to download player data...", PLAYER_DATA_DOWNLOAD_SCRIPT_PATH)
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                PLAYER_DATA_DOWNLOAD_SCRIPT_PATH,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=BASE_DIR,
            )
            stdout, stderr = await process.communicate()

            if stdout:
                logger.info("Player Data Script STDOUT:\n%s", stdout.decode().strip())
            if stderr:
                logger.warning("Player Data Script STDERR:\n%s", stderr.decode().strip())

            if process.returncode == 0:
                logger.info("Player data download script finished (Return Code: 0).")
                os.makedirs(os.path.dirname(PLAYER_DATA_DOWNLOAD_FLAG_FILE), exist_ok=True)
                with open(PLAYER_DATA_DOWNLOAD_FLAG_FILE, "w") as f:
                    f.write(datetime.now(timezone.utc).isoformat())
                logger.info("Created flag file: %s", PLAYER_DATA_DOWNLOAD_FLAG_FILE)
            else:
                logger.error("Player data download script failed. Return code: %d", process.returncode)
        except Exception as e:
            logger.error("Error running one-time player data download task: %s", e, exc_info=True)
    else:
        logger.info("Player data already downloaded (flag file '%s' exists). Skipping download.", PLAYER_DATA_DOWNLOAD_FLAG_FILE)

# --- Bot Definition ---
class BettingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        super().__init__(command_prefix=commands.when_mentioned_or("/"), intents=intents)
        self.db_manager = DatabaseManager()
        self.db = self.db_manager
        self.admin_service = AdminService(self, self.db_manager)
        self.analytics_service = AnalyticsService(self, self.db_manager)
        self.bet_service = BetService(self, self.db_manager)
        self.sports_api = SportsAPI(self.db_manager)
        self.game_service = GameService(self.sports_api, self.db_manager)
        self.user_service = UserService(self, self.db_manager)
        self.voice_service = VoiceService(self, self.db_manager)
        self.data_sync_service = DataSyncService(self.game_service, self.db_manager)
        self.bet_slip_generators = {}
        self.webapp_process = None
        self.fetcher_process = None
        self.live_game_channel_service = LiveGameChannelService(self, self.db_manager)

    async def get_bet_slip_generator(self, guild_id: int) -> BetSlipGenerator:
        if guild_id not in self.bet_slip_generators:
            self.bet_slip_generators[guild_id] = BetSlipGenerator(guild_id=guild_id)
        return self.bet_slip_generators[guild_id]

    async def load_extensions(self):
        commands_dir = os.path.join(BASE_DIR, "commands")
        cog_files = [
            "admin.py",
            "betting.py",
            "remove_user.py",
            "setid.py",
            "stats.py",
            "load_logos.py",
        ]
        loaded_commands = []
        for filename in cog_files:
            file_path = os.path.join(commands_dir, filename)
            if os.path.exists(file_path):
                extension = f"commands.{filename[:-3]}"
                try:
                    await self.load_extension(extension)
                    loaded_commands.append(extension)
                    logger.info("Successfully loaded extension: %s", extension)
                except Exception as e:
                    logger.error("Failed to load extension %s: %s", extension, e, exc_info=True)
            else:
                logger.warning("Command file not found: %s", file_path)
        logger.info("Total loaded extensions: %s", loaded_commands)
        commands_list = [cmd.name for cmd in self.tree.get_commands()]
        logger.info("Available commands after loading: %s", commands_list)

    async def sync_commands_with_retry(self, guild: Optional[discord.Guild] = None, retries: int = 3, delay: int = 5):
        for attempt in range(1, retries + 1):
            try:
                synced = await self.tree.sync()
                logger.info("Global commands synced: %s", [cmd.name for cmd in synced])
                return True
            except discord.HTTPException as e:
                logger.error("Sync attempt %d/%d failed: %s", attempt, retries, e, exc_info=True)
                if attempt < retries:
                    await asyncio.sleep(delay)
        logger.error("Failed to sync commands after %d attempts.", retries)
        return False

    def start_flask_webapp(self):
        if self.webapp_process is None or self.webapp_process.poll() is not None:
            webapp_log_path = os.path.join(BASE_DIR, "logs", "webapp.log")
            os.makedirs(os.path.dirname(webapp_log_path), exist_ok=True)
            with open(webapp_log_path, "a") as log_file:
                self.webapp_process = subprocess.Popen(
                    [sys.executable, os.path.join(BASE_DIR, "webapp.py")],
                    stdout=log_file,
                    stderr=log_file,
                    text=True,
                    bufsize=1,
                )
            logger.info("Started Flask web server (webapp.py) as a subprocess with logging to %s", webapp_log_path)

    def start_fetcher(self):
        if self.fetcher_process is None or self.fetcher_process.poll() is not None:
            fetcher_log_path = os.path.join(BASE_DIR, "logs", "fetcher.log")
            os.makedirs(os.path.dirname(fetcher_log_path), exist_ok=True)
            with open(fetcher_log_path, "a") as log_file:
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                env["LOG_LEVEL"] = "DEBUG"
                required_vars = {
                    "API_KEY": os.getenv("API_KEY"),
                    "MYSQL_HOST": os.getenv("MYSQL_HOST"),
                    "MYSQL_PORT": os.getenv("MYSQL_PORT"),
                    "MYSQL_USER": os.getenv("MYSQL_USER"),
                    "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
                    "MYSQL_DB": os.getenv("MYSQL_DB"),
                    "MYSQL_POOL_MIN_SIZE": os.getenv("MYSQL_POOL_MIN_SIZE", "1"),
                    "MYSQL_POOL_MAX_SIZE": os.getenv("MYSQL_POOL_MAX_SIZE", "10"),
                }
                for var, value in required_vars.items():
                    env[var] = value
                    logger.info("Passing %s to fetcher process", var)
                try:
                    self.fetcher_process = subprocess.Popen(
                        [sys.executable, os.path.join(BASE_DIR, "fetcher.py")],
                        stdout=log_file,
                        stderr=log_file,
                        text=True,
                        bufsize=1,
                        env=env,
                    )
                    logger.info("Started fetcher (fetcher.py) as a subprocess with logging to %s", fetcher_log_path)
                except Exception as e:
                    logger.error("Failed to start fetcher process: %s", e, exc_info=True)
                    return
            async def monitor_fetcher():
                while True:
                    if self.fetcher_process.poll() is not None:
                        return_code = self.fetcher_process.returncode
                        logger.error("Fetcher process ended unexpectedly with return code %d", return_code)
                        try:
                            with open(fetcher_log_path, "r") as f:
                                lines = f.readlines()
                                last_lines = lines[-20:] if len(lines) > 20 else lines
                                logger.error("Last few lines from fetcher.log:\n%s", "".join(last_lines))
                        except Exception as e:
                            logger.error("Failed to read fetcher.log: %s", e)
                        await asyncio.sleep(5)
                        logger.info("Restarting fetcher process...")
                        self.start_fetcher()
                    await asyncio.sleep(5)
            asyncio.create_task(monitor_fetcher())

    async def setup_hook(self):
        """Initialize the bot and load extensions."""
        logger.info("Starting setup_hook...")
        await run_one_time_logo_download()
        await run_one_time_player_data_download()

        await self.db_manager.connect()
        if not self.db_manager._pool:
            logger.critical("Database connection pool failed to initialize. Bot cannot continue.")
            await self.close()
            sys.exit("Database connection failed.")

        # Initialize required database tables
        await self.db_manager.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                live_game_updates INTEGER DEFAULT 0
            )
            """
        )
        logger.info("Ensured guild_settings table exists.")

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
                service_name = service_starts[i].__self__.__class__.__name__ if hasattr(service_starts[i], "__self__") else f"Service {i}"
                logger.error("Error starting %s: %s", service_name, result, exc_info=True)
        logger.info("Services startup initiated, including LiveGameChannelService.")
        self.start_flask_webapp()
        self.start_fetcher()
        logger.info("Bot setup_hook completed successfully - commands will be synced in on_ready")

    async def on_ready(self):
        logger.info("Logged in as %s (%s)", self.user.name, self.user.id)
        logger.info("discord.py API version: %s", discord.__version__)
        logger.info("Python version: %s", sys.version)
        logger.info("Connected to %d guilds.", len(self.guilds))
        for guild in self.guilds:
            logger.debug("- %s (%s)", guild.name, guild.id)
        logger.info("Latency: %.2f ms", self.latency * 1000)

        try:
            current_commands = [cmd.name for cmd in self.tree.get_commands()]
            logger.info("Current commands before sync: %s", current_commands)
            if not current_commands:
                logger.error("No commands found! Attempting to reload extensions...")
                await self.load_extensions()
                current_commands = [cmd.name for cmd in self.tree.get_commands()]
                logger.info("Commands after reloading: %s", current_commands)
            try:
                await self.sync_commands_with_retry()
                logger.info("Global commands synced successfully")
            except Exception as e:
                logger.error("Failed to sync global commands: %s", e)
                return
            global_commands = [cmd.name for cmd in self.tree.get_commands()]
            logger.info("Final global commands: %s", global_commands)
        except Exception as e:
            logger.error("Failed to sync command tree: %s", e, exc_info=True)
        logger.info("------ Bot is Ready ------")

    async def on_guild_join(self, guild: discord.Guild):
        logger.info("Joined new guild: %s (%s)", guild.name, guild.id)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.user.id:
            return
        if (
            hasattr(self, "bet_service")
            and hasattr(self.bet_service, "pending_reactions")
            and payload.message_id in self.bet_service.pending_reactions
        ):
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
            asyncio.create_task(self.bet_service.on_raw_reaction_remove(payload))

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
                        logger.error("Error stopping %s: %s", service_name, result, exc_info=True)
            except asyncio.TimeoutError:
                logger.warning("Timeout while waiting for services to stop")
            except Exception as e:
                logger.error("Error during service shutdown: %s", e, exc_info=True)
            logger.info("Services stopped.")

            if self.db_manager:
                logger.info("Closing database connection pool...")
                try:
                    await asyncio.wait_for(self.db_manager.close(), timeout=5.0)
                    logger.info("Database connection pool closed.")
                except asyncio.TimeoutError:
                    logger.warning("Timeout while closing database connection pool")
                except Exception as e:
                    logger.error("Error closing database connection pool: %s", e, exc_info=True)

            if self.webapp_process and self.webapp_process.poll() is None:
                self.webapp_process.send_signal(signal.SIGINT)
                self.webapp_process.wait(timeout=5)
                logger.info("Stopped Flask web server subprocess.")
            if self.fetcher_process and self.fetcher_process.poll() is None:
                self.fetcher_process.send_signal(signal.SIGINT)
                self.fetcher_process.wait(timeout=5)
                logger.info("Stopped fetcher subprocess.")
        except Exception as e:
            logger.exception("Error during shutdown: %s", e)
        finally:
            logger.info("Closing Discord client connection...")
            try:
                await super().close()
            except Exception as e:
                logger.error("Error closing Discord client: %s", e, exc_info=True)
            logger.info("Bot shutdown complete.")

# --- Manual Sync Command (as a Cog) ---
class SyncCog(commands.Cog):
    def __init__(self, bot: BettingBot):
        self.bot = bot

    @app_commands.command(name="sync", description="Manually sync bot commands (admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_command(self, interaction: discord.Interaction):
        logger.info("Manual sync initiated by %s in guild %s", interaction.user, interaction.guild_id)
        try:
            await interaction.response.defer(ephemeral=True)
            commands_list = [cmd.name for cmd in self.bot.tree.get_commands()]
            logger.debug("Commands to sync: %s", commands_list)
            await self.bot.sync_commands_with_retry()
            await interaction.followup.send("Global commands synced successfully!", ephemeral=True)
        except Exception as e:
            logger.error("Failed to sync commands: %s", e, exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Failed to sync commands: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"Failed to sync commands: {e}", ephemeral=True)

async def setup_sync_cog(bot: BettingBot):
    await bot.add_cog(SyncCog(bot))
    logger.info("SyncCog loaded")

# --- Main Execution ---
async def run_bot():
    """Run the bot with retry logic for connection issues."""
    retry_count = 0
    max_retries = 5
    retry_delay = 5  # seconds
    while retry_count < max_retries:
        try:
            bot = BettingBot()
            await setup_sync_cog(bot)
            await bot.start(REQUIRED_ENV_VARS["DISCORD_TOKEN"])
            break
        except discord.LoginFailure:
            logger.critical("Login failed: Invalid Discord token provided in .env file.")
            break
        except discord.PrivilegedIntentsRequired as e:
            shard_id_info = f" (Shard ID: {e.shard_id})" if e.shard_id else ""
            logger.critical(
                "Privileged Intents%s are required but not enabled in the Discord Developer Portal.",
                shard_id_info,
            )
            logger.critical("Enable 'Presence Intent', 'Server Members Intent', and 'Message Content Intent'.")
            break
        except (discord.HTTPException, aiohttp.ClientError, asyncio.TimeoutError) as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning("Connection error occurred (attempt %d/%d): %s", retry_count, max_retries, e)
                logger.info("Retrying in %d seconds...", retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.critical("Failed to connect after %d attempts. Last error: %s", max_retries, e)
                break
        except Exception as e:
            logger.critical("An unexpected error occurred while running the bot: %s", e, exc_info=True)
            break

def main():
    try:
        logger.info("Starting bot...")
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested via KeyboardInterrupt.")
    except Exception as e:
        logger.critical("An unexpected error occurred while running the bot: %s", e, exc_info=True)
    finally:
        logger.info("Bot process finished.")

if __name__ == "__main__":
    main()