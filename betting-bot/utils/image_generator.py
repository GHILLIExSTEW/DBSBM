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
        self.LEAGUE_TEAM_BASE_DIR = os.path.join(BASE_DIR, "static", "logos", "teams")
        self.LEAGUE_LOGO_BASE_DIR = os.path.join(BASE_DIR, "static", "logos", "leagues")
        self.DEFAULT_LOGO_PATH = os.path.join(BASE_DIR, "static", "logos", "default_logo.png")

        self.game_line_generator = GameLineImageGenerator(self.fonts, self.padding)
        self.player_prop_generator = PlayerPropImageGenerator(self.fonts, self.padding)
        self.parlay_generator = ParlayImageGenerator(self.fonts, self.padding)

    def _draw_teams_section(self, *args, **kwargs):
        return self.game_line_generator.draw_teams_section(*args, **kwargs)

    def _draw_player_prop_section(self, *args, **kwargs):
        return self.player_prop_generator.draw_player_prop_section(*args, **kwargs)

    def _draw_parlay_details(self, *args, **kwargs):
        return self.parlay_generator.draw_parlay_details(*args, **kwargs)

    async def generate_bet_slip(
        self,
        home_team: str,
        away_team: str,
        league: str,
        odds: float,
        units: float,
        bet_id: str,
        timestamp: datetime,
        bet_type: str = "straight",
        line: Optional[str] = None,
        parlay_legs: Optional[List[Dict]] = None,
        is_same_game: bool = False,
        team_logo_paths: Optional[List[str]] = None,
        selected_team: Optional[str] = None,
        player_name: Optional[str] = None,
        player_image: Optional[Image.Image] = None,
        display_vs: Optional[str] = None
    ) -> Optional[Image.Image]:
        try:
            if line:
                line = line.upper()

            # Validate units
            if units <= 0:
                logger.error("Invalid units value %s for bet ID %s. Units must be positive.", units, bet_id)
                raise ValueError(f"Units must be positive, got {units}")

            width = 600
            height = 400

            # Load team logos
            home_logo = None
            away_logo = None
            sport_category = get_sport_category_for_path(league)
            if sport_category:
                home_logo_path = os.path.join(self.LEAGUE_TEAM_BASE_DIR, sport_category, league, f"{normalize_team_name_any_league(home_team)}.png")
                away_logo_path = os.path.join(self.LEAGUE_TEAM_BASE_DIR, sport_category, league, f"{normalize_team_name_any_league(away_team)}.png")
                try:
                    if os.path.exists(home_logo_path):
                        home_logo = Image.open(home_logo_path).convert("RGBA")
                    if os.path.exists(away_logo_path):
                        away_logo = Image.open(away_logo_path).convert("RGBA")
                except Exception as e:
                    logger.error(f"Error loading team logos: {e}")

            # Load league logo
            league_logo = None
            league_logo_path = os.path.join(self.LEAGUE_LOGO_BASE_DIR, sport_category, league, f"{league.lower()}.png")
            try:
                if os.path.exists(league_logo_path):
                    league_logo = Image.open(league_logo_path).convert("RGBA")
            except Exception as e:
                logger.error(f"Error loading league logo: {e}")

            img = Image.new('RGBA', (width, height), "#2c2f36")  # Mid dark gray background
            draw = ImageDraw.Draw(img)

            # Draw header with league logo
            header_font = self.fonts['font_b_36']
            header_text = f"{league} - Game Line"
            header_y = 25
            if league_logo:
                logo_size = (45, 45)
                logo_display = league_logo.resize(logo_size, Image.Resampling.LANCZOS)
                bbox = header_font.getbbox(header_text)
                text_w = bbox[2] - bbox[0]
                total_width = logo_size[0] + 15 + text_w
                start_x = (width - total_width) // 2
                img.paste(logo_display, (int(start_x), header_y), logo_display)
                draw.text((start_x + logo_size[0] + 15, header_y), header_text, font=header_font, fill="white")

            # Draw based on bet type
            if bet_type.lower() == "parlay" and parlay_legs:
                parlay_team_logos = []
                for team_logo_path in team_logo_paths:
                    try:
                        logo = Image.open(team_logo_path).convert("RGBA")
                        parlay_team_logos.append(logo)
                    except:
                        parlay_team_logos.append(None)
                self._draw_parlay_details(draw, width, height, parlay_legs, odds, units, bet_id, timestamp, is_same_game, img, parlay_team_logos)
            elif bet_type.lower() == "player_prop" and player_name:
                # Draw team/opponent names above images, player name only below player image
                self._draw_player_prop_section(img, draw, width, display_vs or f"{home_team} vs {away_team}", home_logo, away_logo, player_name, player_image)
            else:
                self._draw_teams_section(img, draw, width, home_team, away_team, home_logo, away_logo, selected_team=selected_team)
                if line:
                    y = 260  # Position below teams
                    center_x = width / 2
                    line_font = self.fonts['font_m_24']
                    draw.text((center_x, y), line, font=line_font, fill="white", anchor="mt")
                    
                    y += 40
                    odds_font = self.fonts['font_b_28']
                    odds_text = f"{odds}"
                    draw.text((center_x, y), odds_text, font=odds_font, fill="white", anchor="mt")

                    y += 40
                    units_font = self.fonts['font_b_24']
                    units_text = f"🔒To Risk {units:.2f} Units🔒"
                    draw.text((center_x, y), units_text, font=units_font, fill="gold", anchor="mt")

            logger.info("Bet slip generated OK for bet ID: %s with units: %s", bet_id, units)
            return img.convert("RGB")

        except Exception as e:
            logger.error("Error in generate_bet_slip: %s", str(e), exc_info=True)
            try:
                err_img = Image.new('RGB', (600, 100), "darkred")
                err_draw = ImageDraw.Draw(err_img)
                err_draw.text(
                    (10, 10),
                    f"Error creating slip:\n{str(e)[:100]}",
                    font=ImageFont.load_default(),
                    fill="white"
                )
                return err_img
            except Exception as final_err:
                logger.error("Fallback image failed: %s", final_err)
            return None