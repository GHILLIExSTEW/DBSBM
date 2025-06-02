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
        """Create an image for a single game with teams side-by-side and logos."""
        image = Image.new('RGB', (self.image_width, self.image_height), self.background_color)
        draw = ImageDraw.Draw(image)

        # Load team logos
        home_logo = self._load_team_logo(game['home_team_name'], str(game['league_id']))
        away_logo = self._load_team_logo(game['away_team_name'], str(game['league_id']))

        # Calculate positions
        center_x = self.image_width // 2
        logo_y = self.padding
        name_y = logo_y + self.logo_size + 10
        vs_text = "vs"
        vs_font = self.team_font
        try:
            # Pillow >= 8.0.0
            bbox = draw.textbbox((0, 0), vs_text, font=vs_font)
            vs_width, vs_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            # Older Pillow
            vs_width, vs_height = draw.textsize(vs_text, font=vs_font)

        # Home team (left)
        home_x = center_x - 200
        if home_logo:
            home_logo = home_logo.resize((self.logo_size, self.logo_size))
            image.paste(home_logo, (home_x, logo_y), home_logo if home_logo.mode == 'RGBA' else None)
        draw.text((home_x, name_y), game['home_team_name'], font=self.team_font, fill=self.text_color)

        # Away team (right)
        away_x = center_x + 100
        if away_logo:
            away_logo = away_logo.resize((self.logo_size, self.logo_size))
            image.paste(away_logo, (away_x, logo_y), away_logo if away_logo.mode == 'RGBA' else None)
        draw.text((away_x, name_y), game['away_team_name'], font=self.team_font, fill=self.text_color)

        # VS text (center)
        draw.text((center_x - vs_width // 2, name_y), vs_text, font=vs_font, fill=self.text_color)

        # Game time (right side, vertically centered)
        draw.text((self.image_width - self.padding - 120, self.image_height // 2 - 10), game_time, font=self.time_font, fill=self.text_color)

        return image

    async def generate_schedule_image(self, games: List[Dict], user_timezone: str) -> Optional[str]:
        """Generate an image showing the schedule of games with logos and local times."""
        try:
            # Create title image
            title_height = 100
            title_image = Image.new('RGB', (self.image_width, title_height), self.background_color)
            title_draw = ImageDraw.Draw(title_image)
            title_text = f"Games Scheduled for {datetime.now().strftime('%Y-%m-%d')}"
            title_draw.text((self.padding, self.padding), title_text, font=self.title_font, fill=self.text_color)

            # Create footer image
            footer_height = 60
            footer_image = Image.new('RGB', (self.image_width, footer_height), self.background_color)
            footer_draw = ImageDraw.Draw(footer_image)
            footer_text = f"Total Games: {len(games)}"
            footer_draw.text((self.padding, self.padding), footer_text, font=self.team_font, fill=self.text_color)

            # Create game images
            game_images = []
            for game in games:
                # Convert start time to user's timezone
                start_time = game['start_time']
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                user_tz = pytz.timezone(user_timezone)
                local_time = start_time.astimezone(user_tz)
                # Format as e.g. 10:40 PM
                game_time = local_time.strftime('%I:%M %p')
                game_image = self._create_game_image(game, game_time)
                game_images.append(game_image)

            # Combine all images
            total_height = title_height + (len(game_images) * self.image_height) + footer_height
            final_image = Image.new('RGB', (self.image_width, total_height), self.background_color)
            final_image.paste(title_image, (0, 0))
            y_offset = title_height
            for game_image in game_images:
                final_image.paste(game_image, (0, y_offset))
                y_offset += self.image_height
            final_image.paste(footer_image, (0, y_offset))

            # Save the image
            image_path = os.path.join(self.base_dir, "generated_schedule.png")
            final_image.save(image_path)
            return image_path
        except Exception as e:
            logger.error(f"Error generating schedule image: {e}", exc_info=True)
            return None 