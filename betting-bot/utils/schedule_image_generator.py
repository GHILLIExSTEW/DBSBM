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

    async def _draw_game(
        self,
        draw: ImageDraw,
        game: Dict,
        home_logo: Optional[Image.Image],
        away_logo: Optional[Image.Image],
        game_time: str,
        y_offset: int
    ) -> None:
        """Draw a single game entry on the image."""
        try:
            # Draw team logos
            if home_logo:
                home_logo = home_logo.resize((self.logo_size, self.logo_size))
                image.paste(home_logo, (self.padding, y_offset), home_logo if home_logo.mode == 'RGBA' else None)
            
            if away_logo:
                away_logo = away_logo.resize((self.logo_size, self.logo_size))
                image.paste(away_logo, (self.padding, y_offset + self.logo_size + self.padding), away_logo if away_logo.mode == 'RGBA' else None)
            
            # Draw team names
            draw.text(
                (self.padding * 2 + self.logo_size, y_offset),
                game['home_team_name'],
                font=self.font,
                fill=self.text_color
            )
            
            draw.text(
                (self.padding * 2 + self.logo_size, y_offset + self.logo_size + self.padding),
                game['away_team_name'],
                font=self.font,
                fill=self.text_color
            )
            
            # Draw game time
            draw.text(
                (self.image_width - self.padding - 100, y_offset + self.logo_size // 2),
                game_time,
                font=self.time_font,
                fill=self.text_color
            )
            
        except Exception as e:
            logger.error(f"Error drawing game: {e}", exc_info=True)
            raise

    async def generate_schedule_image(self, games: List[Dict], user_timezone: str) -> Optional[str]:
        """Generate an image showing the schedule of games."""
        try:
            # Calculate required image height based on number of games
            game_height = self.padding * 2 + self.logo_size + self.font_size * 2
            total_height = self.title_height + (len(games) * game_height) + self.footer_height
            
            # Create new image with calculated height
            image = Image.new('RGB', (self.image_width, total_height), self.background_color)
            draw = ImageDraw.Draw(image)
            
            # Draw title
            title_text = f"Games Scheduled for {datetime.now().strftime('%Y-%m-%d')}"
            draw.text(
                (self.padding, self.padding),
                title_text,
                font=self.title_font,
                fill=self.text_color
            )
            
            # Draw each game
            y_offset = self.title_height
            for game in games:
                # Convert start time to user's timezone
                start_time = game['start_time']
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                user_tz = pytz.timezone(user_timezone)
                local_time = start_time.astimezone(user_tz)
                
                # Load team logos
                home_logo = self._load_team_logo(game['home_team_name'], str(game['league_id']))
                away_logo = self._load_team_logo(game['away_team_name'], str(game['league_id']))
                
                # Draw game entry
                await self._draw_game(
                    draw,
                    game,
                    home_logo,
                    away_logo,
                    local_time.strftime('%I:%M %p'),
                    y_offset
                )
                
                y_offset += game_height
            
            # Draw footer with total games
            footer_text = f"Total Games: {len(games)}"
            draw.text(
                (self.padding, total_height - self.footer_height + self.padding),
                footer_text,
                font=self.font,
                fill=self.text_color
            )
            
            # Save the image
            image_path = os.path.join(self.base_dir, "generated_schedule.png")
            image.save(image_path)
            return image_path
            
        except Exception as e:
            logger.error(f"Error generating schedule image: {e}", exc_info=True)
            return None 