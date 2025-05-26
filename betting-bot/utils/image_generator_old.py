import os
import time
from typing import Optional, Union, Dict, List, Tuple
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import io
import logging
from pathlib import Path

from config.asset_paths import (
    get_sport_category_for_path,
    BASE_DIR
)
from config.team_mappings import normalize_team_name
from data.db_manager import DatabaseManager
from data.game_utils import normalize_team_name_any_league

from utils.game_line_image_generator import GameLineImageGenerator
from utils.player_prop_image_generator import PlayerPropImageGenerator
from utils.parlay_image_generator import ParlayImageGenerator

logger = logging.getLogger(__name__)

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
        self.MIN_CONTENT_FOOTER_DISTANCE = 10
        
        # Cache configuration
        self._logo_cache = {}
        self._cache_expiry = 3600  # 1 hour in seconds
        self._max_cache_size = 50  # Maximum number of logos to cache

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
        league: str,
        home_team: str,
        away_team: str,
        odds: Union[str, float],
        units: float,
        bet_type: str = "straight",
        selected_team: Optional[str] = None,
        market: Optional[str] = None,
        include_lock: bool = True,
        line: Optional[str] = None,
        bet_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        player_name: Optional[str] = None,
        player_image: Optional[Image.Image] = None,
        display_vs: Optional[str] = None
    ) -> Optional[bytes]:
        """Generate a bet slip image.
        
        Args:
            league (str): League name
            home_team (str): Home team name 
            away_team (str): Away team name
            odds (Union[str, float]): Bet odds
            units (float): Number of units
            bet_type (str, optional): Type of bet. Defaults to "straight"
            selected_team (Optional[str], optional): Selected team for the bet. Defaults to None
            market (Optional[str], optional): Market type. Defaults to None
            include_lock (bool, optional): Whether to include lock icon. Defaults to True
            line (Optional[str], optional): Betting line. Defaults to None
            bet_id (Optional[str], optional): Unique bet ID. Defaults to None
            timestamp (Optional[datetime], optional): Bet timestamp. Defaults to None
            player_name (Optional[str], optional): Player name for props. Defaults to None
            player_image (Optional[Image.Image], optional): Player image for props. Defaults to None
            display_vs (Optional[str], optional): Custom VS text. Defaults to None
        
        Returns:
            Optional[bytes]: Generated image as bytes
        """
        try:
            width = 600
            height = 400

            # Load league and team logos
            league_logo = None
            home_logo = None
            away_logo = None
            sport_category = get_sport_category_for_path(league)

            if sport_category:
                home_logo = self._load_team_logo(home_team, league)
                away_logo = self._load_team_logo(away_team, league) 
                league_logo = self._load_league_logo(league)

            # Create base image
            img = Image.new('RGBA', (width, height), "#2c2f36")  # Mid dark gray background
            draw = ImageDraw.Draw(img)

            # Draw header with league and sport type
            header_font = self.fonts['font_b_36']
            header_text = f"{league} - {bet_type.title()}"
            header_y = 25

            if league_logo:
                logo_size = (45, 45)
                logo_display = league_logo.resize(logo_size, Image.Resampling.LANCZOS)
                bbox = header_font.getbbox(header_text)
                text_w = bbox[2] - bbox[0]
                total_width = logo_size[0] + 15 + text_w
                start_x = (width - total_width) // 2
                img.paste(logo_display, (int(start_x), int(header_y)), logo_display)
                draw.text((start_x + logo_size[0] + 15, header_y), header_text, font=header_font, fill='white', anchor="lt")
            else:
                bbox = header_font.getbbox(header_text)
                text_w = bbox[2] - bbox[0]
                draw.text((width // 2 - text_w // 2, header_y), header_text, font=header_font, fill='white', anchor="lt")

            # Draw teams section with logos and vs text
            if bet_type.lower() == "player_prop" and player_name:
                y_after_content = self._draw_player_prop_section(
                    img, draw, width, display_vs or f"{home_team} vs {away_team}",
                    home_logo, away_logo, player_name, player_image,
                    player_team=selected_team, home_team=home_team, away_team=away_team
                )
                separator_y = y_after_content + 20
            else:
                game_line_gen = GameLineImageGenerator(self.fonts, padding=20)
                next_y = game_line_gen.draw_teams_section(
                    img, draw, width, home_team, away_team, home_logo, away_logo, selected_team
                )
                separator_y = next_y + 20

            # Draw separator line
            line_color = '#4a4a4a'  # Subtle gray for the line
            line_thickness = 2
            line_padding = 40  # Padding from edges
            draw.line([(line_padding, separator_y), (width - line_padding, separator_y)], 
                     fill=line_color, width=line_thickness)

            # Draw bet details section
            bet_details_y = separator_y + 30  # Space after the line
            details_font = self.fonts['font_b_24']
            units_color = 'white'
            odds_color = '#00FF00'  # Bright green for odds

            # Format units with lock icon if needed
            units_text = f"{units} Unit{'s' if units != 1 else ''}"
            if include_lock:
                units_text = f"🔒 {units_text}"

            # Format odds with market and line
            odds_display = str(odds)
            if line:
                odds_display = f"{odds} ({line})"
            elif market:
                odds_display = f"{odds} {market}"

            # Center and draw bet details
            units_bbox = details_font.getbbox(units_text)
            units_w = units_bbox[2] - units_bbox[0]
            odds_bbox = details_font.getbbox(odds_display)
            odds_w = odds_bbox[2] - odds_bbox[0]

            units_x = width // 4 - units_w // 2
            odds_x = (width * 3) // 4 - odds_w // 2

            draw.text((units_x, bet_details_y), units_text, font=details_font, fill=units_color, anchor="lt")
            draw.text((odds_x, bet_details_y), odds_display, font=details_font, fill=odds_color, anchor="lt")

            # Draw footer
            footer_text = "discord.gg/betting"
            bet_id_text = f" • Bet ID: {bet_id}" if bet_id else ""
            time_text = ""
            if timestamp:
                tz = timezone.utc  # Use UTC timezone
                formatted_time = timestamp.astimezone(tz).strftime("%Y-%m-%d %H:%M UTC")
                time_text = f" • {formatted_time}"
            footer_text = footer_text + bet_id_text + time_text
            
            footer_font = self.fonts['font_m_18']
            footer_color = '#808080'  # Gray color for footer
            footer_bbox = footer_font.getbbox(footer_text)
            footer_w = footer_bbox[2] - footer_bbox[0]
            footer_h = footer_bbox[3] - footer_bbox[1]
            footer_y = height - footer_h - 15  # 15px padding from bottom
            footer_x = width // 2 - footer_w // 2  # Center horizontally
            draw.text((footer_x, footer_y), footer_text, font=footer_font, fill=footer_color)

            # Convert to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG', optimize=True)
            img_byte_arr.seek(0)
            return img_byte_arr.getvalue()

        except Exception as e:
            logger.error("Error generating bet slip: %s", e, exc_info=True)
            return None

    def _cleanup_cache(self):
        """Remove expired entries from the logo cache"""
        now = time.time()
        expired_keys = [
            key for key, (_, ts) in self._logo_cache.items()
            if now - ts > self._cache_expiry
        ]
        for key in expired_keys:
            del self._logo_cache[key]

    def _ensure_team_dir_exists(self, league: str) -> Optional[str]:
        """Ensure team directory exists and return its path"""
        try:
            sport = get_sport_category_for_path(league.upper())
            if not sport:
                logger.warning(f"No sport category found for league '{league}'")
                return None
                
            team_dir = os.path.join(self.LEAGUE_TEAM_BASE_DIR, sport, league.upper())
            os.makedirs(team_dir, exist_ok=True)
            return team_dir
        except Exception as e:
            logger.error(f"Error ensuring team directory exists for league '{league}': {e}")
            return None

    def _load_team_logo(self, team_name: str, league: str) -> Optional[Image.Image]:
        """Load a team logo with caching and proper error handling"""
        try:
            cache_key = f"team_{league}_{team_name}"
            now = time.time()
            if cache_key in self._logo_cache:
                logo, ts = self._logo_cache[cache_key]
                if now - ts <= self._cache_expiry:
                    return logo.copy()
                else:
                    del self._logo_cache[cache_key]

            sport = get_sport_category_for_path(league.upper())
            if not sport:
                logger.error(
                    "Sport category not found for league '%s' (when loading team: %s)",
                    league,
                    team_name
                )
                return (
                    Image.open(self.DEFAULT_LOGO_PATH).convert("RGBA")
                    if os.path.exists(self.DEFAULT_LOGO_PATH)
                    else None
                )

            team_dir = self._ensure_team_dir_exists(league)
            if not team_dir:
                return (
                    Image.open(self.DEFAULT_LOGO_PATH).convert("RGBA")
                    if os.path.exists(self.DEFAULT_LOGO_PATH)
                    else None
                )

            normalized_team_name = normalize_team_name_any_league(team_name)
            normalized_team_name_no_period = normalized_team_name.replace('.', '')
            logo_filename = f"{normalize_team_name(normalized_team_name_no_period)}.png"
            logo_path = os.path.join(team_dir, logo_filename)
            absolute_logo_path = os.path.abspath(logo_path)

            if os.path.exists(absolute_logo_path):
                logo = Image.open(absolute_logo_path).convert("RGBA")
                self._cleanup_cache()
                if len(self._logo_cache) >= self._max_cache_size:
                    oldest_key = min(self._logo_cache, key=lambda k: self._logo_cache[k][1])
                    del self._logo_cache[oldest_key]
                self._logo_cache[cache_key] = (logo.copy(), now)
                return logo.copy()

            logger.warning(
                "Team logo not found for %s in %s (path: %s). Using default.",
                team_name,
                league,
                absolute_logo_path
            )
            return (
                Image.open(self.DEFAULT_LOGO_PATH).convert("RGBA")
                if os.path.exists(self.DEFAULT_LOGO_PATH)
                else None
            )
        except Exception as e:
            logger.error(
                "Error in _load_team_logo for %s (league %s): %s",
                team_name,
                league,
                e,
                exc_info=True
            )
            try:
                return (
                    Image.open(self.DEFAULT_LOGO_PATH).convert("RGBA")
                    if os.path.exists(self.DEFAULT_LOGO_PATH)
                    else None
                )
            except Exception as def_err:
                logger.error("Error loading default team logo during fallback: %s", def_err)
            return None

    def _load_league_logo(self, league: str) -> Optional[Image.Image]:
        """Load a league logo with caching and proper error handling"""
        if not league:
            return None
        try:
            cache_key = f"league_{league}"
            now = time.time()
            if cache_key in self._logo_cache:
                logo, ts = self._logo_cache[cache_key]
                if now - ts <= self._cache_expiry:
                    return logo.copy()
                else:
                    del self._logo_cache[cache_key]

            sport = get_sport_category_for_path(league.upper())
            if not sport:
                logger.warning(
                    "Sport category not found for league '%s'. Attempting to use default logo.",
                    league
                )
                return (
                    Image.open(self.DEFAULT_LOGO_PATH).convert("RGBA")
                    if os.path.exists(self.DEFAULT_LOGO_PATH)
                    else None
                )

            fname = f"{league.lower().replace(' ', '_')}.png"
            logo_dir = os.path.join(self.LEAGUE_LOGO_BASE_DIR, sport, league.upper())
            os.makedirs(logo_dir, exist_ok=True)

            logo_path = os.path.join(logo_dir, fname)
            absolute_logo_path = os.path.abspath(logo_path)
            file_exists = os.path.exists(absolute_logo_path)
            logger.info(
                "Loading league logo - League:'%s', Resolved Sport Category: '%s', Path:'%s', Exists:%s",
                league,
                sport,
                absolute_logo_path,
                file_exists
            )

            logo = None
            if file_exists:
                try:
                    logo = Image.open(absolute_logo_path).convert("RGBA")
                except Exception as e:
                    logger.error("Error opening league logo %s: %s", absolute_logo_path, e)

            if logo:
                self._cleanup_cache()
                if len(self._logo_cache) >= self._max_cache_size:
                    oldest_key = min(self._logo_cache, key=lambda k: self._logo_cache[k][1])
                    del self._logo_cache[oldest_key]
                self._logo_cache[cache_key] = (logo.copy(), now)
                return logo.copy()

            logger.warning(
                "No logo found for league %s (path: %s). Attempting to use default logo.",
                league,
                absolute_logo_path
            )
            return (
                Image.open(self.DEFAULT_LOGO_PATH).convert("RGBA")
                if os.path.exists(self.DEFAULT_LOGO_PATH)
                else None
            )
        except Exception as e:
            logger.error("Error in _load_league_logo for %s: %s", league, e, exc_info=True)
            try:
                return (
                    Image.open(self.DEFAULT_LOGO_PATH).convert("RGBA")
                    if os.path.exists(self.DEFAULT_LOGO_PATH)
                    else None
                )
            except Exception as def_err:
                logger.error("Error loading default logo during fallback: %s", def_err)
            return None

    def _format_odds_with_sign(self, odds: float) -> str:
        return f"+{int(odds)}" if odds > 0 else str(int(odds))