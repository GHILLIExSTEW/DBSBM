import logging
import os
import time
import io
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import traceback

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from config.asset_paths import (
    get_sport_category_for_path,
    BASE_DIR
)
from config.team_mappings import normalize_team_name
from data.db_manager import DatabaseManager
from data.game_utils import normalize_team_name_any_league

from .game_line_image_generator import GameLineImageGenerator
from .player_prop_image_generator import PlayerPropImageGenerator
from .parlay_image_generator import ParlayImageGenerator

logger = logging.getLogger(__name__)

SPORT_CATEGORY_MAP = {
    "NBA": "BASKETBALL", "NCAAB": "BASKETBALL", "WNBA": "BASKETBALL", "EUROLEAGUE": "BASKETBALL", "CBA": "BASKETBALL",
    "BRITISH BASKETBALL LEAGUE": "BASKETBALL",
    "NFL": "FOOTBALL", "NCAAF": "FOOTBALL", "CFL": "FOOTBALL", "XFL": "FOOTBALL",
    "MLB": "BASEBALL", "NCAAB_BASEBALL": "BASEBALL", "NPB": "BASEBALL", "KBO": "BASEBALL",
    "NHL": "HOCKEY", "KHL": "HOCKEY", "SHL": "HOCKEY",
    "MLS": "SOCCER", "EPL": "SOCCER", "LA_LIGA": "SOCCER", "SERIE_A": "SOCCER", "BUNDESLIGA": "SOCCER",
    "LIGUE_1": "SOCCER", "UEFA_CL": "SOCCER", "COPA_LIBERTADORES": "SOCCER", "A_LEAGUE": "SOCCER", "J_LEAGUE": "SOCCER",
    "ATP": "TENNIS", "WTA": "TENNIS", "ITF": "TENNIS", "GRAND_SLAM": "TENNIS",
    "UFC": "MMA", "BELLATOR": "MMA", "ONE_CHAMPIONSHIP": "MMA", "PFL": "MMA",
    "PGA": "GOLF", "LPGA": "GOLF", "EUROPEAN_TOUR": "GOLF", "MASTERS": "GOLF",
    "BOXING": "BOXING", "CRICKET": "CRICKET", "IPL": "CRICKET", "BBL": "CRICKET", "TEST_CRICKET": "CRICKET",
    "RUGBY_UNION": "RUGBY", "SUPER_RUGBY": "RUGBY", "SIX_NATIONS": "RUGBY",
    "RUGBY_LEAGUE": "RUGBY", "NRL": "RUGBY", "SUPER_LEAGUE": "RUGBY",
    "F1": "MOTORSPORTS", "NASCAR": "MOTORSPORTS", "INDYCAR": "MOTORSPORTS", "MOTOGP": "MOTORSPORTS",
    "DARTS": "DARTS", "PDC": "DARTS", "VOLLEYBALL": "VOLLEYBALL", "FIVB": "VOLLEYBALL",
    "TABLE_TENNIS": "TABLE_TENNIS", "ITTF": "TABLE_TENNIS", "CYCLING": "CYCLING",
    "TOUR_DE_FRANCE": "CYCLING", "GIRO_D_ITALIA": "CYCLING", "VUELTA_A_ESPANA": "CYCLING",
    "ESPORTS_CSGO": "ESPORTS", "ESPORTS_LOL": "ESPORTS", "ESPORTS_DOTA2": "ESPORTS",
    "ESPORTS_OVERWATCH": "ESPORTS", "ESPORTS_FIFA": "ESPORTS",
    "AUSSIE_RULES": "AUSTRALIAN_FOOTBALL", "AFL": "AUSTRALIAN_FOOTBALL",
    "HANDBALL": "HANDBALL", "EHF_CL": "HANDBALL", "SNOOKER": "SNOOKER",
    "WORLD_CHAMPIONSHIP_SNOOKER": "SNOOKER", "BADMINTON": "BADMINTON", "BWF": "BADMINTON",
    "LACROSSE": "LACROSSE", "NLL": "LACROSSE", "FIELD_HOCKEY": "FIELD_HOCKEY", "FIH_PRO_LEAGUE": "FIELD_HOCKEY"
}
DEFAULT_FALLBACK_SPORT_CATEGORY = "OTHER_SPORTS"


def load_fonts():
    fonts = {}
    try:
        font_dir = os.path.join(BASE_DIR, "assets", "fonts")
        font_path = os.path.join(font_dir, "Roboto-Regular.ttf")
        bold_font_path = os.path.join(font_dir, "Roboto-Bold.ttf")
        emoji_font_path = os.path.join(font_dir, "NotoColorEmoji-Regular.ttf")

        missing_files = []
        for p, name in [(font_path, "Regular"), (bold_font_path, "Bold"), (emoji_font_path, "Emoji")]:
            if not os.path.exists(p):
                missing_files.append(f"{name} font at {p}")

        if missing_files:
            logger.error("Font files not found: %s", "; ".join(missing_files))
            raise FileNotFoundError(f"Font files not found: {', '.join(missing_files)}")

        fonts['font_m_18'] = ImageFont.truetype(font_path, 18)
        fonts['font_m_24'] = ImageFont.truetype(font_path, 24)
        fonts['font_b_18'] = ImageFont.truetype(bold_font_path, 18)
        fonts['font_b_24'] = ImageFont.truetype(bold_font_path, 24)
        fonts['font_b_28'] = ImageFont.truetype(bold_font_path, 28)
        fonts['font_b_36'] = ImageFont.truetype(bold_font_path, 36)
        fonts['emoji_font_24'] = ImageFont.truetype(emoji_font_path, 24)
        logger.info("Custom fonts loaded successfully for global FONTS.")
        return fonts

    except Exception as e:
        logger.error("Critical error loading custom fonts: %s. Falling back to default system fonts.", e, exc_info=True)
        default_font = ImageFont.load_default()
        fonts_fallback = {
            key: default_font
            for key in ['font_m_18', 'font_m_24', 'font_b_18', 'font_b_24', 'font_b_28', 'font_b_36']
        }
        fonts_fallback['emoji_font_24'] = default_font
        return fonts_fallback


FONTS = load_fonts()


class BetSlipGenerator:
    def __init__(self, guild_id: Optional[int] = None):
        self.guild_id = guild_id
        self.db_manager = DatabaseManager()
        self.padding = 10
        self.fonts = FONTS

        self.game_line_generator = GameLineImageGenerator(self.fonts, self.padding)
        self.player_prop_generator = PlayerPropImageGenerator(self.fonts, self.padding)
        self.parlay_generator = ParlayImageGenerator(self.fonts, self.padding)

    def _draw_teams_section(self, *args, **kwargs):
        return self.game_line_generator.draw_teams_section(*args, **kwargs)

    def _draw_player_prop_section(self, *args, **kwargs):
        return self.player_prop_generator.draw_player_prop_section(*args, **kwargs)

    def _draw_parlay_details(self, *args, **kwargs):
        return self.parlay_generator.draw_parlay_details(*args, **kwargs)