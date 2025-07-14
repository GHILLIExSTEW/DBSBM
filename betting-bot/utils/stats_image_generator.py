import logging
from typing import Dict, List
from PIL import Image, ImageDraw, ImageFont
import os

logger = logging.getLogger(__name__)

class StatsImageGenerator:
    def __init__(self):
        self.font_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts', 'arial.ttf')
        self.background_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'stats_bg.png')
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.font_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.background_path), exist_ok=True)

    async def generate_capper_stats_image(self, stats: Dict, username: str, profile_image_url: str = None) -> Image.Image:
        """Generate an image with capper statistics."""
        try:
            # Create a new image with a white background
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)

            # Load font
            try:
                font = ImageFont.truetype(self.font_path, 24)
                title_font = ImageFont.truetype(self.font_path, 32)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            # Load and display profile image if available
            profile_img = None
            if profile_image_url:
                try:
                    import requests
                    from io import BytesIO
                    response = requests.get(profile_image_url, timeout=10)
                    if response.status_code == 200:
                        profile_img = Image.open(BytesIO(response.content)).convert("RGBA")
                        # Resize profile image to reasonable size
                        profile_img.thumbnail((80, 80), Image.Resampling.LANCZOS)
                except Exception as e:
                    logger.warning(f"Failed to load profile image from {profile_image_url}: {e}")

            # Draw title with profile image if available
            title_text = f"{username}'s Stats"
            title_bbox = title_font.getbbox(title_text)
            title_w = title_bbox[2] - title_bbox[0]
            
            if profile_img:
                # Center title with profile image
                profile_size = profile_img.size[0]
                total_width = profile_size + 20 + title_w  # 20px gap
                start_x = (800 - total_width) // 2
                
                # Draw profile image
                profile_y = 50 - profile_size // 2
                img.paste(profile_img, (start_x, profile_y), profile_img)
                
                # Draw title next to profile image
                title_x = start_x + profile_size + 20
                draw.text((title_x, 50), title_text, fill='black', font=title_font, anchor="lt")
            else:
                # Center title without profile image
                draw.text((400, 50), title_text, fill='black', font=title_font, anchor="mm")

            # Draw stats
            y = 150
            stats_text = [
                f"Total Bets: {stats.get('total_bets', 0)}",
                f"Wins: {stats.get('wins', 0)}",
                f"Losses: {stats.get('losses', 0)}",
                f"Pushes: {stats.get('pushes', 0)}",
                f"Win Rate: {stats.get('win_rate', 0):.1f}%",
                f"Net Units: {stats.get('net_units', 0):.2f}",
                f"ROI: {stats.get('roi', 0):.1f}%"
            ]

            for text in stats_text:
                draw.text((400, y), text, fill='black', font=font, anchor="mm")
                y += 50

            return img
        except Exception as e:
            logger.error(f"Error generating capper stats image: {str(e)}")
            raise

    def generate_guild_stats_image(self, stats: Dict) -> Image.Image:
        """Generate an image with guild statistics."""
        try:
            # Create a new image with a white background
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)

            # Load font
            try:
                font = ImageFont.truetype(self.font_path, 24)
                title_font = ImageFont.truetype(self.font_path, 32)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            # Draw title
            draw.text((400, 50), "Guild Stats", fill='black', font=title_font, anchor="mm")

            # Draw stats
            y = 150
            stats_text = [
                f"Total Bets: {stats.get('total_bets', 0)}",
                f"Total Cappers: {stats.get('total_cappers', 0)}",
                f"Total Units Wagered: {stats.get('total_units', 0)}",
                f"Net Units: {stats.get('net_units', 0)}"
            ]

            for text in stats_text:
                draw.text((400, y), text, fill='black', font=font, anchor="mm")
                y += 50

            return img
        except Exception as e:
            logger.error(f"Error generating guild stats image: {str(e)}")
            raise

    def generate_top_cappers_image(self, cappers: List[Dict]) -> Image.Image:
        """Generate an image with top cappers."""
        try:
            # Create a new image with a white background
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)

            # Load font
            try:
                font = ImageFont.truetype(self.font_path, 24)
                title_font = ImageFont.truetype(self.font_path, 32)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            # Draw title
            draw.text((400, 50), "Top Cappers", fill='black', font=title_font, anchor="mm")

            # Draw cappers
            y = 150
            for capper in cappers:
                text = f"User ID: {capper['user_id']} - Net Units: {capper['net_units']}"
                draw.text((400, y), text, fill='black', font=font, anchor="mm")
                y += 50

            return img
        except Exception as e:
            logger.error(f"Error generating top cappers image: {str(e)}")
            raise 