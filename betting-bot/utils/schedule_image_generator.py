"""Schedule image generator for displaying upcoming games."""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont
import os
import pytz
from config.asset_paths import get_sport_category_for_path
from data.game_utils import normalize_team_name_any_league
from config.team_mappings import normalize_team_name

logger = logging.getLogger(__name__)

class ScheduleImageGenerator:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.fonts_dir = os.path.join(self.assets_dir, "fonts")
        self.logos_dir = os.path.join(self.base_dir, "static", "logos", "teams")
        
        # Load fonts
        self.title_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Bold.ttf"), 36)
        self.team_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Regular.ttf"), 24)
        self.time_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Regular.ttf"), 20)
        
        # Image settings
        self.image_width = 800
        self.image_height = 260  # More vertical space for each game
        self.padding = 40
        self.logo_size = 60
        self.background_color = '#1a1a1a'
        self.text_color = '#ffffff'

    def _load_team_logo(self, team_name: str, league_code: str) -> Optional[Image.Image]:
        """Load a team's logo using the correct sport/league folder structure for all leagues."""
        try:
            # league_code is e.g. 'MLB', 'NBA', etc.
            sport = get_sport_category_for_path(league_code.upper())
            if not sport:
                default_path = os.path.join(self.base_dir, "static", "logos", "default_logo.png")
                return Image.open(default_path).convert("RGBA")
            normalized = normalize_team_name_any_league(team_name).replace(".", "")
            fname = f"{normalize_team_name(normalized)}.png"
            logo_path = os.path.join(self.base_dir, "static", "logos", "teams", sport, league_code.upper(), fname)
            if os.path.exists(logo_path):
                return Image.open(logo_path).convert("RGBA")
            default_path = os.path.join(self.base_dir, "static", "logos", "default_logo.png")
            return Image.open(default_path).convert("RGBA")
        except Exception as e:
            logger.error(f"Error loading logo for {team_name} ({league_code}): {e}")
            return None

    def _create_game_image(self, game: Dict, game_time: str) -> Image.Image:
        """Create an image for a single game, left-aligned, with start time below teams."""
        image = Image.new('RGB', (self.image_width, self.image_height), self.background_color)
        draw = ImageDraw.Draw(image)

        # Load team logos
        home_logo = self._load_team_logo(game['home_team_name'], game['league_id'])
        away_logo = self._load_team_logo(game['away_team_name'], game['league_id'])

        # Layout constants
        x = self.padding
        logo_y = self.padding
        name_y = logo_y + self.logo_size + 10
        vs_y = name_y
        time_y = name_y + 40
        logo_spacing = 30
        name_spacing = 30
        logo_size = (self.logo_size, self.logo_size)

        # Draw home logo and name
        if home_logo:
            home_logo = home_logo.resize(logo_size)
            image.paste(home_logo, (x, logo_y), home_logo if home_logo.mode == 'RGBA' else None)
        draw.text((x + self.logo_size + 10, logo_y + self.logo_size // 2 - 10), game['home_team_name'], font=self.team_font, fill=self.text_color)

        # Draw 'vs'
        vs_text = "vs"
        vs_font = self.team_font
        try:
            bbox = draw.textbbox((0, 0), vs_text, font=vs_font)
            vs_width, vs_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            vs_width, vs_height = draw.textsize(vs_text, font=vs_font)
        vs_x = x
        vs_y = logo_y + self.logo_size + 10
        draw.text((vs_x, vs_y), vs_text, font=vs_font, fill=self.text_color)

        # Draw away logo and name
        away_logo_y = vs_y + vs_height + 10
        if away_logo:
            away_logo = away_logo.resize(logo_size)
            image.paste(away_logo, (x, away_logo_y), away_logo if away_logo.mode == 'RGBA' else None)
        draw.text((x + self.logo_size + 10, away_logo_y + self.logo_size // 2 - 10), game['away_team_name'], font=self.team_font, fill=self.text_color)

        # Draw start time below teams, left-aligned
        draw.text((x, away_logo_y + self.logo_size + 18), game_time, font=self.time_font, fill=self.text_color)

        return image

    async def generate_schedule_image(self, games: List[Dict], user_timezone: str) -> Optional[str]:
        """Generate an image showing the schedule of games grouped by league, with league logo headers."""
        try:
            from collections import defaultdict
            # Group games by league_id
            league_groups = defaultdict(list)
            for game in games:
                league_groups[game['league_id']].append(game)

            # Prepare to calculate total height
            title_height = 100
            footer_height = 60
            league_header_height = 80
            game_height = self.image_height
            num_leagues = len(league_groups)
            num_games = len(games)
            total_height = title_height + footer_height + num_leagues * league_header_height + num_games * game_height

            # Create the final image
            final_image = Image.new('RGB', (self.image_width, total_height), self.background_color)
            y_offset = 0

            # Draw title
            title_image = Image.new('RGB', (self.image_width, title_height), self.background_color)
            title_draw = ImageDraw.Draw(title_image)
            title_text = f"Games Scheduled for {datetime.now().strftime('%Y-%m-%d')}"
            title_draw.text((self.padding, self.padding), title_text, font=self.title_font, fill=self.text_color)
            final_image.paste(title_image, (0, y_offset))
            y_offset += title_height

            # For each league, draw league logo header and games
            for league_id, league_games in league_groups.items():
                # Draw league logo header
                league_logo_img = None
                league_logo_path = None
                league_code = league_id.upper()
                # Try to get sport for this league
                sport = get_sport_category_for_path(league_code)
                if sport:
                    league_logo_path = os.path.join(self.base_dir, "static", "logos", "leagues", sport, league_code, f"{league_code.lower()}.png")
                if league_logo_path and os.path.exists(league_logo_path):
                    league_logo_img = Image.open(league_logo_path).convert("RGBA").resize((60, 60))
                # Draw header background
                league_header_img = Image.new('RGB', (self.image_width, league_header_height), self.background_color)
                league_header_draw = ImageDraw.Draw(league_header_img)
                x = self.padding
                y = self.padding // 2
                if league_logo_img:
                    league_header_img.paste(league_logo_img, (x, y), league_logo_img)
                    x += 60 + 10
                # Draw league name (from first game in group)
                league_name = league_games[0].get('league_name', league_code)
                league_header_draw.text((x, y + 10), league_name, font=self.team_font, fill=self.text_color)
                final_image.paste(league_header_img, (0, y_offset))
                y_offset += league_header_height
                # Draw all games for this league
                for game in league_games:
                    # Convert start time to user's timezone (not UTC!)
                    start_time = game['start_time']
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    import pytz
                    user_tz = pytz.timezone(user_timezone)
                    if start_time.tzinfo is None:
                        start_time = pytz.utc.localize(start_time)
                    local_time = start_time.astimezone(user_tz)
                    game_time = local_time.strftime('%I:%M %p')
                    game_image = self._create_game_image(game, game_time)
                    final_image.paste(game_image, (0, y_offset))
                    y_offset += game_height

            # Draw footer
            footer_image = Image.new('RGB', (self.image_width, footer_height), self.background_color)
            footer_draw = ImageDraw.Draw(footer_image)
            footer_text = f"Total Games: {len(games)}"
            footer_draw.text((self.padding, self.padding), footer_text, font=self.team_font, fill=self.text_color)
            final_image.paste(footer_image, (0, y_offset))

            # Save the image
            image_path = os.path.join(self.base_dir, "generated_schedule.png")
            final_image.save(image_path)
            return image_path
        except Exception as e:
            logger.error(f"Error generating schedule image: {e}", exc_info=True)
            return None 