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
from api.sports_api import SportsAPI

# --- Environment Variable Access ---
BOT_TOKEN = os.getenv('DISCORD_TOKEN')

if not BOT_TOKEN:
    logger.critical("FATAL: DISCORD_TOKEN not found in environment variables!")
    sys.exit("Missing DISCORD_TOKEN") 