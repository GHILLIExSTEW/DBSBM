"""
Enhanced Player Prop Image Generator
Creates improved bet slip images with better styling, prop type icons, and performance stats.
"""

import logging
from io import BytesIO
from typing import Any, Dict, List, Optional

import requests
from PIL import Image, ImageDraw, ImageFont

from utils.asset_loader import AssetLoader

logger = logging.getLogger(__name__)


class EnhancedPlayerPropImageGenerator:
    """Enhanced image generator for player prop bets."""

    def __init__(self, asset_loader: AssetLoader):
        self.asset_loader = asset_loader
        self.base_width = 800
        self.base_height = 400

        # Color scheme
        self.colors = {
            "background": "#1a1a1a",
            "card_bg": "#2d2d2d",
            "text_primary": "#ffffff",
            "text_secondary": "#b0b0b0",
            "accent": "#4CAF50",
            "accent_red": "#f44336",
            "border": "#404040",
            "over_green": "#4CAF50",
            "under_red": "#f44336",
        }

        # Load fonts
        self.fonts = self._load_fonts()

        # Prop type icons mapping
        self.prop_icons = {
            "points": "🏀",
            "rebounds": "📊",
            "assists": "🤝",
            "threes": "🎯",
            "steals": "⚡",
            "blocks": "🛡️",
            "turnovers": "❌",
            "minutes": "⏱️",
            "passing_yards": "🏈",
            "rushing_yards": "🏃",
            "receiving_yards": "🤲",
            "receptions": "📥",
            "touchdowns": "🏆",
            "interceptions": "🚫",
            "hits": "⚾",
            "home_runs": "💥",
            "rbis": "🏠",
            "runs": "🏃",
            "strikeouts": "🔥",
            "walks": "🚶",
            "innings_pitched": "⚾",
            "goals": "🏒",
            "shots": "🎯",
            "saves": "🥅",
            "penalty_minutes": "⏰",
        }

    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts for the image generator."""
        try:
            fonts = {}

            # Load fonts from assets
            font_path = self.asset_loader.get_font_path("Roboto-Regular.ttf")
            fonts["regular"] = ImageFont.truetype(font_path, 16)
            fonts["medium"] = ImageFont.truetype(font_path, 18)
            fonts["large"] = ImageFont.truetype(font_path, 24)
            fonts["title"] = ImageFont.truetype(font_path, 32)

            # Load bold font
            bold_font_path = self.asset_loader.get_font_path("Roboto-Bold.ttf")
            fonts["bold"] = ImageFont.truetype(bold_font_path, 20)
            fonts["bold_large"] = ImageFont.truetype(bold_font_path, 28)

            return fonts

        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            # Fallback to default font
            return {
                "regular": ImageFont.load_default(),
                "medium": ImageFont.load_default(),
                "large": ImageFont.load_default(),
                "title": ImageFont.load_default(),
                "bold": ImageFont.load_default(),
                "bold_large": ImageFont.load_default(),
            }

    async def generate_player_prop_image(
        self,
        player_name: str,
        team_name: str,
        league: str,
        prop_type: str,
        line_value: float,
        bet_direction: str,
        odds: Optional[float] = None,
        player_image_url: Optional[str] = None,
        team_logo_url: Optional[str] = None,
        performance_stats: Optional[Dict[str, Any]] = None,
    ) -> Optional[BytesIO]:
        """
        Generate an enhanced player prop bet slip image.

        Args:
            player_name: Player's name
            team_name: Team name
            league: League name
            prop_type: Type of prop (points, rebounds, etc.)
            line_value: The line value
            bet_direction: 'over' or 'under'
            odds: Betting odds (optional)
            player_image_url: URL to player image (optional)
            team_logo_url: URL to team logo (optional)
            performance_stats: Player performance stats (optional)

        Returns:
            BytesIO object containing the image
        """
        try:
            # Create base image
            img = Image.new(
                "RGB", (self.base_width, self.base_height), self.colors["background"]
            )
            draw = ImageDraw.Draw(img)

            # Create card background
            self._draw_card_background(draw)

            # Load and position images
            await self._add_images(
                img, draw, player_image_url, team_logo_url, team_name, league
            )

            # Add main content
            self._add_player_info(draw, player_name, team_name, league)
            self._add_prop_details(draw, prop_type, line_value, bet_direction, odds)

            # Add performance stats if available
            if performance_stats:
                self._add_performance_stats(draw, performance_stats, prop_type)

            # Add decorative elements
            self._add_decorative_elements(draw, prop_type, bet_direction)

            # Convert to BytesIO
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format="PNG", optimize=True)
            img_byte_arr.seek(0)

            return img_byte_arr

        except Exception as e:
            logger.error(f"Error generating player prop image: {e}")
            return None

    def _draw_card_background(self, draw: ImageDraw.Draw):
        """Draw the card background with gradient effect."""
        # Main card
        card_rect = [20, 20, self.base_width - 20, self.base_height - 20]
        draw.rounded_rectangle(card_rect, radius=15, fill=self.colors["card_bg"])

        # Add subtle border
        border_rect = [18, 18, self.base_width - 18, self.base_height - 18]
        draw.rounded_rectangle(
            border_rect, radius=17, outline=self.colors["border"], width=2
        )

    async def _add_images(
        self,
        img: Image.Image,
        draw: ImageDraw.Draw,
        player_image_url: str,
        team_logo_url: str,
        team_name: str,
        league: str,
    ):
        """Add player image and team logo to the image."""
        try:
            # Add team logo (left side)
            if team_logo_url:
                team_logo = await self._load_image_from_url(team_logo_url)
            else:
                team_logo = self.asset_loader.get_team_logo(team_name, league)

            if team_logo:
                # Resize and position team logo
                team_logo = team_logo.resize((80, 80), Image.Resampling.LANCZOS)
                img.paste(
                    team_logo, (40, 40), team_logo if team_logo.mode == "RGBA" else None
                )

            # Add player image (right side)
            if player_image_url:
                player_image = await self._load_image_from_url(player_image_url)
                if player_image:
                    # Resize and position player image
                    player_image = player_image.resize(
                        (120, 120), Image.Resampling.LANCZOS
                    )
                    # Apply circular mask
                    player_image = self._apply_circular_mask(player_image)
                    img.paste(player_image, (self.base_width - 160, 30), player_image)

        except Exception as e:
            logger.error(f"Error adding images: {e}")

    async def _load_image_from_url(self, url: str) -> Optional[Image.Image]:
        """Load image from URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            logger.error(f"Error loading image from URL {url}: {e}")
            return None

    def _apply_circular_mask(self, image: Image.Image) -> Image.Image:
        """Apply circular mask to image."""
        try:
            # Create circular mask
            mask = Image.new("L", image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)

            # Apply mask
            output = Image.new("RGBA", image.size, (0, 0, 0, 0))
            output.paste(image, (0, 0))
            output.putalpha(mask)

            return output
        except Exception as e:
            logger.error(f"Error applying circular mask: {e}")
            return image

    def _add_player_info(
        self, draw: ImageDraw.Draw, player_name: str, team_name: str, league: str
    ):
        """Add player information section."""
        # Player name
        draw.text(
            (140, 50),
            player_name,
            font=self.fonts["bold_large"],
            fill=self.colors["text_primary"],
        )

        # Team and league
        team_league_text = f"{team_name} • {league}"
        draw.text(
            (140, 85),
            team_league_text,
            font=self.fonts["medium"],
            fill=self.colors["text_secondary"],
        )

    def _add_prop_details(
        self,
        draw: ImageDraw.Draw,
        prop_type: str,
        line_value: float,
        bet_direction: str,
        odds: Optional[float],
    ):
        """Add prop bet details."""
        # Prop type with icon
        prop_icon = self.prop_icons.get(prop_type, "📊")
        prop_text = f"{prop_icon} {prop_type.replace('_', ' ').title()}"
        draw.text(
            (140, 130),
            prop_text,
            font=self.fonts["bold"],
            fill=self.colors["text_primary"],
        )

        # Line value and direction
        direction_color = (
            self.colors["over_green"]
            if bet_direction == "over"
            else self.colors["under_red"]
        )
        direction_text = f"{bet_direction.upper()} {line_value}"
        draw.text(
            (140, 160), direction_text, font=self.fonts["large"], fill=direction_color
        )

        # Odds (if available)
        if odds:
            odds_text = f"Odds: {odds}"
            draw.text(
                (140, 200),
                odds_text,
                font=self.fonts["medium"],
                fill=self.colors["text_secondary"],
            )

    def _add_performance_stats(
        self, draw: ImageDraw.Draw, stats: Dict[str, Any], prop_type: str
    ):
        """Add player performance statistics."""
        # Stats section background
        stats_rect = [140, 280, self.base_width - 160, self.base_height - 40]
        draw.rounded_rectangle(stats_rect, radius=10, fill=self.colors["background"])

        # Stats title
        draw.text(
            (160, 290),
            "Recent Performance",
            font=self.fonts["bold"],
            fill=self.colors["text_primary"],
        )

        # Display relevant stats
        y_offset = 320
        relevant_stats = [
            ("Last 5 Games", stats.get("last_5_avg", "N/A")),
            ("Season Avg", stats.get("season_avg", "N/A")),
            ("Over Rate", f"{stats.get('over_rate', 0):.1%}"),
            ("Best Game", stats.get("best_game", "N/A")),
        ]

        for label, value in relevant_stats:
            draw.text(
                (160, y_offset),
                f"{label}: {value}",
                font=self.fonts["regular"],
                fill=self.colors["text_secondary"],
            )
            y_offset += 25

    def _add_decorative_elements(
        self, draw: ImageDraw.Draw, prop_type: str, bet_direction: str
    ):
        """Add decorative elements to the image."""
        # Prop type icon in corner
        prop_icon = self.prop_icons.get(prop_type, "📊")
        draw.text(
            (self.base_width - 60, 40),
            prop_icon,
            font=self.fonts["title"],
            fill=self.colors["accent"],
        )

        # Direction indicator
        direction_color = (
            self.colors["over_green"]
            if bet_direction == "over"
            else self.colors["under_red"]
        )
        direction_icon = "📈" if bet_direction == "over" else "📉"
        draw.text(
            (self.base_width - 60, 80),
            direction_icon,
            font=self.fonts["large"],
            fill=direction_color,
        )

        # Add subtle pattern
        self._add_pattern(draw)

    def _add_pattern(self, draw: ImageDraw.Draw):
        """Add subtle background pattern."""
        try:
            # Create a subtle grid pattern
            for x in range(0, self.base_width, 40):
                for y in range(0, self.base_height, 40):
                    if (x + y) % 80 == 0:
                        draw.point((x, y), fill=self.colors["border"])
        except Exception as e:
            logger.error(f"Error adding pattern: {e}")

    async def generate_prop_comparison_image(
        self,
        player_name: str,
        team_name: str,
        league: str,
        prop_type: str,
        line_value: float,
        recent_games: List[Dict[str, Any]],
    ) -> Optional[BytesIO]:
        """
        Generate a comparison image showing player's recent performance vs the line.

        Args:
            player_name: Player's name
            team_name: Team name
            league: League name
            prop_type: Type of prop
            line_value: The line value
            recent_games: List of recent game performances

        Returns:
            BytesIO object containing the image
        """
        try:
            # Create base image
            img = Image.new("RGB", (self.base_width, 600), self.colors["background"])
            draw = ImageDraw.Draw(img)

            # Create card background
            self._draw_card_background(draw)

            # Add player info
            self._add_player_info(draw, player_name, team_name, league)

            # Add comparison chart
            self._add_comparison_chart(draw, recent_games, line_value, prop_type)

            # Convert to BytesIO
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format="PNG", optimize=True)
            img_byte_arr.seek(0)

            return img_byte_arr

        except Exception as e:
            logger.error(f"Error generating comparison image: {e}")
            return None

    def _add_comparison_chart(
        self,
        draw: ImageDraw.Draw,
        recent_games: List[Dict[str, Any]],
        line_value: float,
        prop_type: str,
    ):
        """Add a simple bar chart comparing recent games to the line."""
        try:
            # Chart area
            chart_x = 140
            chart_y = 150
            chart_width = 500
            chart_height = 300

            # Draw chart background
            chart_rect = [
                chart_x,
                chart_y,
                chart_x + chart_width,
                chart_y + chart_height,
            ]
            draw.rounded_rectangle(
                chart_rect, radius=10, fill=self.colors["background"]
            )

            # Draw line value reference
            line_y = chart_y + chart_height - 50
            draw.line(
                [chart_x, line_y, chart_x + chart_width, line_y],
                fill=self.colors["border"],
                width=2,
            )
            draw.text(
                (chart_x + chart_width + 10, line_y - 10),
                f"Line: {line_value}",
                font=self.fonts["medium"],
                fill=self.colors["text_secondary"],
            )

            # Draw bars for each game
            if recent_games:
                bar_width = chart_width // len(recent_games)
                max_value = max(
                    [game.get("value", 0) for game in recent_games] + [line_value]
                )

                for i, game in enumerate(recent_games[:10]):  # Limit to 10 games
                    value = game.get("value", 0)
                    bar_height = (value / max_value) * (chart_height - 100)

                    bar_x = chart_x + (i * bar_width) + 10
                    bar_y = chart_y + chart_height - 50 - bar_height

                    # Color based on over/under
                    bar_color = (
                        self.colors["over_green"]
                        if value > line_value
                        else self.colors["under_red"]
                    )

                    draw.rectangle(
                        [
                            bar_x,
                            bar_y,
                            bar_x + bar_width - 20,
                            chart_y + chart_height - 50,
                        ],
                        fill=bar_color,
                    )

                    # Game label
                    game_label = f"G{i+1}"
                    draw.text(
                        (bar_x, chart_y + chart_height - 30),
                        game_label,
                        font=self.fonts["regular"],
                        fill=self.colors["text_secondary"],
                    )

        except Exception as e:
            logger.error(f"Error adding comparison chart: {e}")
