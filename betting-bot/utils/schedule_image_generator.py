"""Schedule image generator for displaying upcoming games."""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont
import os
import pytz

logger = logging.getLogger(__name__)

class ScheduleImageGenerator:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.fonts_dir = os.path.join(self.assets_dir, "fonts")
        self.logos_dir = os.path.join(self.assets_dir, "logos")
        
        # Load fonts
        self.title_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Bold.ttf"), 36)
        self.team_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Regular.ttf"), 24)
        self.time_font = ImageFont.truetype(os.path.join(self.fonts_dir, "Roboto-Regular.ttf"), 20)
        
        # Image settings
        self.image_width = 800
        self.padding = 40
        self.logo_size = (60, 60)
        self.game_spacing = 100
        self.title_height = 80
        self.footer_height = 40

    def _load_team_logo(self, team_name: str, league_code: str) -> Optional[Image.Image]:
        """Load a team's logo from the assets directory."""
        try:
            # Convert team name to filename format
            safe_name = team_name.lower().replace(' ', '_')
            logo_path = os.path.join(self.logos_dir, 'teams', league_code, f"{safe_name}.png")
            
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                logo = logo.resize(self.logo_size, Image.Resampling.LANCZOS)
                return logo
            return None
        except Exception as e:
            logger.error(f"Error loading logo for {team_name}: {e}")
            return None

    def _draw_game(self, draw: ImageDraw.ImageDraw, game: Dict, y_position: int, user_timezone: str) -> int:
        """Draw a single game entry on the image."""
        # Convert UTC time to user's timezone
        utc_time = datetime.fromisoformat(game['start_time'].replace('Z', '+00:00'))
        user_tz = pytz.timezone(user_timezone)
        local_time = utc_time.astimezone(user_tz)
        time_str = local_time.strftime("%I:%M %p %Z")

        # Draw home team
        home_logo = self._load_team_logo(game['home_team_name'], game['league_id'])
        if home_logo:
            draw.bitmap((self.padding, y_position), home_logo)
        draw.text((self.padding + self.logo_size[0] + 10, y_position + 20), 
                 game['home_team_name'], font=self.team_font, fill='white')

        # Draw away team
        away_logo = self._load_team_logo(game['away_team_name'], game['league_id'])
        if away_logo:
            draw.bitmap((self.padding, y_position + 50), away_logo)
        draw.text((self.padding + self.logo_size[0] + 10, y_position + 70), 
                 game['away_team_name'], font=self.team_font, fill='white')

        # Draw time
        draw.text((self.image_width - self.padding - 150, y_position + 35), 
                 time_str, font=self.time_font, fill='white')

        return y_position + self.game_spacing

    async def generate_schedule_image(self, games: List[Dict], user_timezone: str = 'UTC') -> Optional[str]:
        """Generate an image showing the schedule of upcoming games."""
        try:
            # Calculate required image height based on number of games
            required_height = (
                self.title_height +  # Title section
                (len(games) * self.game_spacing) +  # Games section
                self.footer_height  # Footer section
            )
            
            # Create new image with dark background
            image = Image.new('RGB', (self.image_width, required_height), '#1a1a1a')
            draw = ImageDraw.Draw(image)

            # Draw title
            current_time = datetime.now().strftime("%B %d, %Y %I:%M %p")
            title = f"Games Scheduled for {current_time}"
            title_width = draw.textlength(title, font=self.title_font)
            draw.text(((self.image_width - title_width) // 2, self.padding), 
                     title, font=self.title_font, fill='white')

            # Draw each game
            y_position = self.padding + 60
            for game in games:
                y_position = self._draw_game(draw, game, y_position, user_timezone)

            # Draw footer with total games count
            footer_text = f"Total Games: {len(games)}"
            footer_width = draw.textlength(footer_text, font=self.time_font)
            draw.text(
                ((self.image_width - footer_width) // 2, required_height - self.footer_height),
                footer_text,
                font=self.time_font,
                fill='white'
            )

            # Save the image
            output_path = os.path.join(self.base_dir, "generated_schedule.png")
            image.save(output_path)
            return output_path

        except Exception as e:
            logger.error(f"Error generating schedule image: {e}")
            return None 