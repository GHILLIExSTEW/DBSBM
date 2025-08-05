"""Schedule image generator for displaying upcoming games."""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import pytz
from PIL import Image, ImageDraw, ImageFont

from config.asset_paths import get_sport_category_for_path
from utils.asset_loader import asset_loader

logger = logging.getLogger(__name__)


class ScheduleImageGenerator:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.fonts_dir = os.path.join(self.assets_dir, "fonts")
        self.logos_dir = os.path.join(self.base_dir, "static", "logos", "teams")

        # Load fonts
        self.title_font = ImageFont.truetype(
            os.path.join(self.fonts_dir, "Roboto-Bold.ttf"), 36
        )
        self.team_font = ImageFont.truetype(
            os.path.join(self.fonts_dir, "Roboto-Regular.ttf"), 24
        )
        self.time_font = ImageFont.truetype(
            os.path.join(self.fonts_dir, "Roboto-Regular.ttf"), 20
        )

        # Image settings
        self.image_width = 800
        self.image_height = 260  # More vertical space for each game
        self.padding = 40
        self.logo_size = 60
        self.background_color = "#1a1a1a"
        self.text_color = "#ffffff"

        # Cache for logos
        self.logo_cache = {}
        self.default_logo = None

    def _get_default_logo(self) -> Image.Image:
        """Get or create the default logo."""
        if self.default_logo is None:
            default_path = os.path.join(
                self.base_dir, "static", "logos", "default_logo.webp"
            )
            self.default_logo = Image.open(default_path).convert("RGBA")
        return self.default_logo

    @staticmethod
    def _load_team_logo(team_name: str, league: str, guild_id: str = None):
        return asset_loader.load_team_logo(team_name, league, guild_id)

    def _convert_times(self, games: List[Dict], user_timezone: str) -> List[Dict]:
        """Convert all game times to user's timezone in one batch."""
        user_tz = pytz.timezone(user_timezone)
        converted_games = []
        for game in games:
            start_time = game["start_time"]
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            if start_time.tzinfo is None:
                start_time = pytz.utc.localize(start_time)
            local_time = start_time.astimezone(user_tz)
            game["local_time"] = local_time.strftime("%I:%M %p")
            converted_games.append(game)
        return converted_games

    def _draw_game_elements(
        self,
        draw: ImageDraw.Draw,
        image: Image.Image,
        home_logo: Image.Image,
        away_logo: Image.Image,
        game: Dict,
        game_time: str,
        positions: Dict,
    ):
        """Draw all elements for a game in one pass."""
        # Draw home logo and name
        if home_logo:
            home_logo = home_logo.resize((self.logo_size, self.logo_size))
            image.paste(home_logo, (positions["x"], positions["logo_y"]), home_logo)
        draw.text(
            (
                positions["x"] + self.logo_size + 10,
                positions["logo_y"] + self.logo_size // 2 - 10,
            ),
            game["home_team_name"],
            font=self.team_font,
            fill=self.text_color,
        )

        # Draw 'vs'
        vs_text = "vs"
        try:
            bbox = draw.textbbox((0, 0), vs_text, font=self.team_font)
            vs_width, vs_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            vs_width, vs_height = draw.textsize(vs_text, font=self.team_font)
        draw.text(
            (positions["x"], positions["vs_y"]),
            vs_text,
            font=self.team_font,
            fill=self.text_color,
        )

        # Draw away logo and name
        away_logo_y = positions["vs_y"] + vs_height + 10
        if away_logo:
            away_logo = away_logo.resize((self.logo_size, self.logo_size))
            image.paste(away_logo, (positions["x"], away_logo_y), away_logo)
        draw.text(
            (
                positions["x"] + self.logo_size + 10,
                away_logo_y + self.logo_size // 2 - 10,
            ),
            game["away_team_name"],
            font=self.team_font,
            fill=self.text_color,
        )

        # Draw start time
        draw.text(
            (positions["x"], away_logo_y + self.logo_size + 18),
            game_time,
            font=self.time_font,
            fill=self.text_color,
        )

    def _create_game_image(self, game: Dict, game_time: str) -> Image.Image:
        """Create an image for a single game, left-aligned, with start time below teams."""
        # Pre-calculate all positions
        positions = {
            "x": self.padding,
            "logo_y": self.padding,
            "name_y": self.padding + self.logo_size + 10,
            "vs_y": self.padding + self.logo_size + 10,
            "time_y": self.padding + self.logo_size + 50,
        }

        # Create image once
        image = Image.new(
            "RGB", (self.image_width, self.image_height), self.background_color
        )
        draw = ImageDraw.Draw(image)

        # Load logos from cache
        home_logo = self._load_team_logo(game["home_team_name"], game["league_id"])
        away_logo = self._load_team_logo(game["away_team_name"], game["league_id"])

        # Draw everything in one pass
        self._draw_game_elements(
            draw, image, home_logo, away_logo, game, game_time, positions
        )

        return image

    async def generate_schedule_image(
        self, games: List[Dict], user_timezone: str
    ) -> Optional[str]:
        """Generate an image showing the schedule of games grouped by league, with league logo headers."""
        try:
            from collections import defaultdict

            # Convert all times in one batch
            games = self._convert_times(games, user_timezone)

            # Group games by league_id
            league_groups = defaultdict(list)
            for game in games:
                league_groups[game["league_id"]].append(game)

            # Calculate dimensions
            title_height = 100
            footer_height = 60
            league_header_height = 80
            game_height = self.image_height
            num_leagues = len(league_groups)
            num_games = len(games)
            total_height = (
                title_height
                + footer_height
                + num_leagues * league_header_height
                + num_games * game_height
            )

            # Create the final image
            final_image = Image.new(
                "RGB", (self.image_width, total_height), self.background_color
            )
            y_offset = 0

            # Draw title
            title_draw = ImageDraw.Draw(final_image)
            title_text = f"Games Scheduled for {datetime.now().strftime('%Y-%m-%d')}"
            title_draw.text(
                (self.padding, self.padding),
                title_text,
                font=self.title_font,
                fill=self.text_color,
            )
            y_offset += title_height

            # For each league, draw league logo header and games
            for league_id, league_games in league_groups.items():
                # Draw league header
                league_code = league_id.upper()
                sport = get_sport_category_for_path(league_code)
                league_logo_img = None
                if sport:
                    # Try all casing variants for directory and file
                    dir_variants = [
                        league_code,
                        league_code.capitalize(),
                        league_code.lower(),
                    ]
                    file_variants = [
                        league_code + ".webp",
                        league_code.capitalize() + ".webp",
                        league_code.lower() + ".webp",
                    ]
                    for dir_variant in dir_variants:
                        dir_path = os.path.join(
                            self.base_dir,
                            "static",
                            "logos",
                            "leagues",
                            sport,
                            dir_variant,
                        )
                        if os.path.exists(dir_path):
                            for file_variant in file_variants:
                                candidate_path = os.path.join(dir_path, file_variant)
                                if os.path.exists(candidate_path):
                                    league_logo_img = (
                                        Image.open(candidate_path)
                                        .convert("RGBA")
                                        .resize((60, 60))
                                    )
                                    break
                            if league_logo_img:
                                break

                # Draw header
                header_draw = ImageDraw.Draw(final_image)
                x = self.padding
                y = y_offset + self.padding // 2
                if league_logo_img:
                    final_image.paste(league_logo_img, (x, y), league_logo_img)
                    x += 60 + 10

                league_name = league_games[0].get("league_name", league_code)
                header_draw.text(
                    (x, y + 10), league_name, font=self.team_font, fill=self.text_color
                )
                y_offset += league_header_height

                # Draw all games for this league
                for game in league_games:
                    game_image = self._create_game_image(game, game["local_time"])
                    final_image.paste(game_image, (0, y_offset))
                    y_offset += game_height

            # Draw footer
            footer_draw = ImageDraw.Draw(final_image)
            footer_text = f"Total Games: {len(games)}"
            footer_draw.text(
                (self.padding, y_offset + self.padding),
                footer_text,
                font=self.team_font,
                fill=self.text_color,
            )

            # Save the image
            image_path = os.path.join(self.base_dir, "generated_schedule.webp")
            final_image.save(image_path, optimize=True)
            return image_path

        except Exception as e:
            logger.error(f"Error generating schedule image: {e}", exc_info=True)
            return None
