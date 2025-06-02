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
        self.image_height = 200  # Height for each game
        self.padding = 40
        self.logo_size = 60
        self.background_color = '#1a1a1a'
        self.text_color = '#ffffff'

    def _load_team_logo(self, team_name: str, league_code: str) -> Optional[Image.Image]:
        """Load a team's logo from the assets directory."""
        try:
            # Convert team name to filename format
            safe_name = team_name.lower().replace(' ', '_')
            logo_path = os.path.join(self.logos_dir, 'teams', league_code, f"{safe_name}.png")
            
            if os.path.exists(logo_path):
                return Image.open(logo_path)
            return None
        except Exception as e:
            logger.error(f"Error loading logo for {team_name}: {e}")
            return None

    def _create_game_image(self, game: Dict, game_time: str) -> Image.Image:
        """Create an image for a single game."""
        # Create new image
        image = Image.new('RGB', (self.image_width, self.image_height), self.background_color)
        draw = ImageDraw.Draw(image)
        
        # Load team logos
        home_logo = self._load_team_logo(game['home_team_name'], str(game['league_id']))
        away_logo = self._load_team_logo(game['away_team_name'], str(game['league_id']))
        
        # Draw team logos
        if home_logo:
            home_logo = home_logo.resize((self.logo_size, self.logo_size))
            image.paste(home_logo, (self.padding, self.padding), home_logo if home_logo.mode == 'RGBA' else None)
        
        if away_logo:
            away_logo = away_logo.resize((self.logo_size, self.logo_size))
            image.paste(away_logo, (self.padding, self.padding * 2 + self.logo_size), away_logo if away_logo.mode == 'RGBA' else None)
        
        # Draw team names
        draw.text(
            (self.padding * 2 + self.logo_size, self.padding),
            game['home_team_name'],
            font=self.team_font,
            fill=self.text_color
        )
        
        draw.text(
            (self.padding * 2 + self.logo_size, self.padding * 2 + self.logo_size),
            game['away_team_name'],
            font=self.team_font,
            fill=self.text_color
        )
        
        # Draw game time
        draw.text(
            (self.image_width - self.padding - 100, self.image_height // 2),
            game_time,
            font=self.time_font,
            fill=self.text_color
        )
        
        return image

    async def generate_schedule_image(self, games: List[Dict], user_timezone: str) -> Optional[str]:
        """Generate an image showing the schedule of games."""
        try:
            # Create title image
            title_height = 100
            title_image = Image.new('RGB', (self.image_width, title_height), self.background_color)
            title_draw = ImageDraw.Draw(title_image)
            
            # Draw title
            title_text = f"Games Scheduled for {datetime.now().strftime('%Y-%m-%d')}"
            title_draw.text(
                (self.padding, self.padding),
                title_text,
                font=self.title_font,
                fill=self.text_color
            )
            
            # Create footer image
            footer_height = 60
            footer_image = Image.new('RGB', (self.image_width, footer_height), self.background_color)
            footer_draw = ImageDraw.Draw(footer_image)
            
            # Draw footer
            footer_text = f"Total Games: {len(games)}"
            footer_draw.text(
                (self.padding, self.padding),
                footer_text,
                font=self.team_font,
                fill=self.text_color
            )
            
            # Create game images
            game_images = []
            for game in games:
                # Convert start time to user's timezone
                start_time = game['start_time']
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                user_tz = pytz.timezone(user_timezone)
                local_time = start_time.astimezone(user_tz)
                
                # Create game image
                game_image = self._create_game_image(game, local_time.strftime('%I:%M %p'))
                game_images.append(game_image)
            
            # Combine all images
            total_height = title_height + (len(game_images) * self.image_height) + footer_height
            final_image = Image.new('RGB', (self.image_width, total_height), self.background_color)
            
            # Paste title
            final_image.paste(title_image, (0, 0))
            
            # Paste game images
            y_offset = title_height
            for game_image in game_images:
                final_image.paste(game_image, (0, y_offset))
                y_offset += self.image_height
            
            # Paste footer
            final_image.paste(footer_image, (0, y_offset))
            
            # Save the image
            image_path = os.path.join(self.base_dir, "generated_schedule.png")
            final_image.save(image_path)
            return image_path
            
        except Exception as e:
            logger.error(f"Error generating schedule image: {e}", exc_info=True)
            return None 