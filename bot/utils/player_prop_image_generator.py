import os
import logging
from PIL import Image, ImageFont
from utils.asset_loader import asset_loader

logger = logging.getLogger(__name__)


class PlayerPropImageGenerator:
    def __init__(self, guild_id=None):
        # Use asset_loader for fonts and static paths
        self.guild_id = guild_id
        try:
            self.font_regular_path = asset_loader.get_font_path("Roboto-Regular.ttf")
            self.font_bold_path = asset_loader.get_font_path("Roboto-Bold.ttf")
            self.font_small_path = asset_loader.get_font_path("Roboto-Regular.ttf")
            self.font_mini_path = asset_loader.get_font_path("Roboto-Regular.ttf")
            self.font_huge_path = asset_loader.get_font_path("Roboto-Bold.ttf")

            self.font_regular = ImageFont.truetype(self.font_regular_path, 28)
            self.font_bold = ImageFont.truetype(self.font_bold_path, 36)
            self.font_small = ImageFont.truetype(self.font_small_path, 22)
            self.font_mini = ImageFont.truetype(self.font_mini_path, 18)
            self.font_huge = ImageFont.truetype(self.font_huge_path, 48)
        except Exception:
            # Fallback to default fonts
            self.font_regular = ImageFont.load_default()
            self.font_bold = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_mini = ImageFont.load_default()
            self.font_huge = ImageFont.load_default()

    def draw_player_prop_section(
        self,
        img,
        draw,
        image_width,
        display_vs,
        home_logo,
        away_logo,
        player_name,
        player_image,
        player_team,
        home_team,
        away_team,
        regenerate_logo,
    ):
        y_base = 85
        logo_size = (120, 120)
        player_img_max_size = (90, 90)  # Dynamically constrain player image
        text_y_offset = logo_size[1] + 16  # Adjusted for better spacing
        team_name_font = self.font_small
        player_name_font = self.font_bold
        text_color = "white"
        center_x = image_width // 2
        section_width = image_width // 2 - getattr(self, 'padding', 0) * 1.5
        home_section_center_x = getattr(self, 'padding', 0) + section_width // 2
        player_section_center_x = image_width - getattr(self, 'padding', 0) - section_width // 2

        # Determine left (player's team) and right (opponent) names for above images
        if player_team and home_team and away_team:
            if player_team.strip().lower() == home_team.strip().lower():
                left_name = home_team
                right_name = away_team
            else:
                left_name = away_team
                right_name = home_team
        else:
            # fallback to display_vs split
            if " vs " in display_vs.lower():
                parts = display_vs.split(" vs ")
                left_name = parts[0].strip()
                right_name = parts[1].strip()
            else:
                left_name = display_vs.strip()
                right_name = ""

        y_base_images = y_base
        y_base += logo_size[1] + 16  # Adjusted for better spacing

        # Draw left (player's team) name above left image
        left_name_w, left_name_h = draw.textsize(left_name, font=team_name_font)
        left_name_x = home_section_center_x - left_name_w // 2
        left_name_y = y_base_images - left_name_h - 8
        draw.text(
            (left_name_x, left_name_y),
            left_name,
            font=team_name_font,
            fill=text_color,
            anchor="lt",
        )

        # Draw right (opponent) name above right image
        if right_name:
            right_name_w, right_name_h = draw.textsize(right_name, font=team_name_font)
            right_name_x = player_section_center_x - right_name_w // 2
            right_name_y = y_base_images - right_name_h - 8
            draw.text(
                (right_name_x, right_name_y),
                right_name,
                font=team_name_font,
                fill=text_color,
                anchor="lt",
            )

        # Draw player's team logo on the left
        if regenerate_logo:
            logo_to_draw = None
            if player_team and home_team and away_team:
                if player_team.strip().lower() == home_team.strip().lower():
                    logo_to_draw = home_logo
                elif player_team.strip().lower() == away_logo.strip().lower():
                    logo_to_draw = away_logo
                else:
                    logo_to_draw = home_logo  # fallback
            else:
                logo_to_draw = home_logo
            if logo_to_draw:
                try:
                    home_logo_resized = logo_to_draw.resize(
                        logo_size, Image.Resampling.LANCZOS
                    )
                    home_logo_x = home_section_center_x - logo_size[0] // 2
                    img.paste(
                        home_logo_resized,
                        (int(home_logo_x), int(y_base_images)),
                        home_logo_resized,
                    )
                except Exception as e:
                    logger.error(f"Error pasting team logo: {e}")

        # Draw player image on the right (never opponent logo)
        if player_image:
            try:
                player_image_copy = player_image.copy()
                player_image_copy.thumbnail(
                    player_img_max_size, Image.Resampling.LANCZOS
                )
                player_img_w, player_img_h = player_image_copy.size
                player_image_x = player_section_center_x - player_img_w // 2
                player_image_y = int(y_base_images + (logo_size[1] - player_img_h) // 2)
                img.paste(
                    player_image_copy,
                    (int(player_image_x), int(player_image_y)),
                    player_image_copy,
                )
            except Exception as e:
                logger.error(f"Error pasting player image: {e}")

        # Draw player name below the images (centered)
        player_name_w, player_name_h = draw.textsize(player_name, font=player_name_font)
        player_name_x = center_x - player_name_w // 2
        draw.text(
            (player_name_x, y_base + text_y_offset),
            player_name,
            font=player_name_font,
            fill=text_color,
            anchor="lt",
        )

        return y_base + text_y_offset + 20  # Return y position for next section

    @staticmethod
    def _load_team_logo(team_name: str, league: str, guild_id: str = None):
        return asset_loader.load_team_logo(team_name, league, guild_id)

    @staticmethod
    def _load_player_image(
        player_name: str, team_name: str, league: str, guild_id: str = None
    ):
        return asset_loader.load_player_image(player_name, team_name, league, guild_id)

    @staticmethod
    def _setup_player_prop_image_parameters():
        """Setup image parameters and fonts for player prop images."""
        from PIL import ImageFont

        image_width, image_height = 600, 400
        bg_color = "#232733"
        padding = 24
        logo_size = (120, 120)
        header_font_size = 36
        team_font_size = 24
        player_font_size = 24
        line_font_size = 24
        odds_font_size = 28
        risk_font_size = 24
        footer_font_size = 18

        # Use asset_loader for font paths
        font_dir = asset_loader.get_font_path("") if hasattr(asset_loader, 'get_font_path') else None
        try:
            fonts = {
                "bold": ImageFont.truetype(asset_loader.get_font_path("Roboto-Bold.ttf"), header_font_size),
                "bold_team": ImageFont.truetype(asset_loader.get_font_path("Roboto-Bold.ttf"), team_font_size),
                "bold_player": ImageFont.truetype(asset_loader.get_font_path("Roboto-Bold.ttf"), player_font_size),
                "line": ImageFont.truetype(asset_loader.get_font_path("Roboto-Regular.ttf"), line_font_size),
                "odds": ImageFont.truetype(asset_loader.get_font_path("Roboto-Bold.ttf"), odds_font_size),
                "risk": ImageFont.truetype(asset_loader.get_font_path("Roboto-Bold.ttf"), risk_font_size),
                "footer": ImageFont.truetype(asset_loader.get_font_path("Roboto-Regular.ttf"), footer_font_size),
            }
        except Exception:
            fonts = {
                "bold": ImageFont.load_default(),
                "bold_team": ImageFont.load_default(),
                "bold_player": ImageFont.load_default(),
                "line": ImageFont.load_default(),
                "odds": ImageFont.load_default(),
                "risk": ImageFont.load_default(),
                "footer": ImageFont.load_default(),
            }

        return {
            "image_width": image_width,
            "image_height": image_height,
            "bg_color": bg_color,
            "padding": padding,
            "logo_size": logo_size,
            "fonts": fonts,
        }

    @staticmethod
    def _find_league_logo_for_player_prop(league):
        """Find the appropriate league logo file for player prop images."""
        from config.asset_paths import get_sport_category_for_path

        league_upper = league.upper()
        league_lower = league.lower()
        sport_category = get_sport_category_for_path(league_upper)

        # Use asset_loader to get league logo
        try:
            league_logo = asset_loader.load_league_logo(league_upper, sport_category)
            return league_logo
        except Exception:
            return None

    @staticmethod
    def _create_player_prop_header_section(image, draw, params, league, league_logo):
        """Create the header section for player prop images."""
        logo_display_size = (45, 45)

        # Get proper league display name
        from config.leagues import LEAGUE_CONFIG

        league_display_name = LEAGUE_CONFIG.get(league, {}).get("name", league.upper())

        # Dynamic header text sizing
        def create_header_text_with_fallback(
            league_name, font, max_width, logo_width=0
        ):
            """Create header text that fits within the available width."""
            # Start with full text
            full_text = f"{league_name} - Player Prop"
            text_width = font.getbbox(full_text)[2]

            # If it fits, use it
            if text_width <= max_width:
                return full_text

            # Try without " - Player Prop" suffix
            short_text = league_name
            text_width = font.getbbox(short_text)[2]
            if text_width <= max_width:
                return short_text

            # Try with abbreviated suffix
            medium_text = f"{league_name} - PP"
            text_width = font.getbbox(medium_text)[2]
            if text_width <= max_width:
                return medium_text

            # If still too long, truncate the league name
            available_width = max_width - font.getbbox(" - PP")[2] - 10  # 10px buffer
            truncated = league_name
            while truncated and font.getbbox(f"{truncated} - PP")[2] > max_width:
                truncated = truncated[:-1]
            if truncated:
                return f"{truncated} - PP"
            else:
                return " - PP"

        # Calculate available width for text
        logo_space = logo_display_size[0] + 15 if league_logo else 0
        available_text_width = params["image_width"] - 48 - logo_space

        header_text = create_header_text_with_fallback(
            league_display_name,
            params["fonts"]["bold"],
            available_text_width,
            logo_space,
        )

        # Calculate text position
        header_w, header_h = params["fonts"]["bold"].getbbox(header_text)[2:]
        block_h = max(logo_display_size[1], header_h)
        block_w = logo_display_size[0] + 15 + header_w if league_logo else header_w
        block_x = (params["image_width"] - block_w) // 2
        block_y = 25

        if league_logo:
            logo_y = block_y + (block_h - logo_display_size[1]) // 2
            text_y = block_y + (block_h - header_h) // 2
            if league_logo.mode == "RGBA":
                image.paste(league_logo, (block_x, logo_y), league_logo)
            else:
                image.paste(league_logo, (block_x, logo_y))
            text_x = block_x + logo_display_size[0] + 15
        else:
            text_x = block_x
            text_y = block_y

        draw.text(
            (text_x, text_y),
            header_text,
            font=params["fonts"]["bold"],
            fill="white",
            anchor="lt",
        )

    @staticmethod
    def _create_player_prop_teams_section(
        image,
        draw,
        params,
        home_team,
        away_team,
        player_name,
        player_image,
        player_team,
        league
    ):
        """Create the teams section for player prop images."""
        # Load team logos
        home_logo = PlayerPropImageGenerator._load_team_logo(home_team, league)
        away_logo = PlayerPropImageGenerator._load_team_logo(away_team, league)

        # Draw teams section using existing method
        PlayerPropImageGenerator.draw_player_prop_section(
            image,
            draw,
            params["image_width"],
            True,
            home_logo,
            away_logo,
            player_name,
            player_image,
            player_team,
            home_team,
            away_team,
            False,
        )

    @staticmethod
    def _create_player_prop_bet_details_section(
        draw, params, line, prop_type, odds, units, units_display_mode, display_as_risk
    ):
        """Create the bet details section for player prop images."""
        # Calculate positions
        line_y = 200
        odds_y = line_y + 40
        units_y = odds_y + 40

        # Draw line
        line_text = f"{prop_type}: {line}"
        draw.text(
            (params["padding"], line_y),
            line_text,
            fill=(255, 255, 255),
            font=params["fonts"]["line"],
        )

        # Draw odds if provided
        if odds:
            odds_text = f"Odds: {odds}"
            draw.text(
                (params["padding"], odds_y),
                odds_text,
                fill=(255, 255, 255),
                font=params["fonts"]["odds"],
            )

        # Draw units/risk
        if display_as_risk:
            risk_text = f"Risk: {units} units"
            draw.text(
                (params["padding"], units_y),
                risk_text,
                fill=(255, 255, 255),
                font=params["fonts"]["risk"],
            )
        else:
            units_text = f"Units: {units}"
            draw.text(
                (params["padding"], units_y),
                units_text,
                fill=(255, 255, 255),
                font=params["fonts"]["line"],
            )

    @staticmethod
    def _create_player_prop_footer_section(draw, params, bet_id, timestamp):
        """Create the footer section for player prop images."""
        footer_y = params["image_height"] - 50

        # Draw bet ID if provided
        if bet_id:
            bet_id_text = f"Bet ID: {bet_id}"
            draw.text(
                (params["padding"], footer_y),
                bet_id_text,
                fill=(200, 200, 200),
                font=params["fonts"]["footer"],
            )

        # Draw timestamp
        if timestamp:
            timestamp_text = f"Created: {timestamp}"
            bbox = draw.textbbox((0, 0), timestamp_text, font=params["fonts"]["footer"])
            text_width = bbox[2] - bbox[0]
            timestamp_x = params["image_width"] - text_width - params["padding"]
            draw.text(
                (timestamp_x, footer_y),
                timestamp_text,
                fill=(200, 200, 200),
                font=params["fonts"]["footer"],
            )

    @staticmethod
    def generate_player_prop_bet_image(
        player_name,
        team_name,
        league,
        line,
        prop_type,
        units,
        home_team=None,
        away_team=None,
        output_path=None,
        bet_id=None,
        timestamp=None,
        guild_id=None,
        odds=None,
        units_display_mode="auto",
        display_as_risk=None,
    ):
        """Generates a player prop bet slip image."""
        from PIL import Image, ImageDraw

        # Setup image parameters and fonts
        params = PlayerPropImageGenerator._setup_player_prop_image_parameters()

        # Create base image
        image = Image.new(
            "RGB", (params["image_width"], params["image_height"]), params["bg_color"]
        )
        draw = ImageDraw.Draw(image)

        # Find league logo
        league_logo = PlayerPropImageGenerator._find_league_logo_for_player_prop(league)

        # Create header section
        PlayerPropImageGenerator._create_player_prop_header_section(
            image, draw, params, league, league_logo
        )

        # Load player image
        player_image = PlayerPropImageGenerator._load_player_image(
            player_name, team_name, league, guild_id
        )

        # Create teams section
        PlayerPropImageGenerator._create_player_prop_teams_section(
            image,
            draw,
            params,
            home_team,
            away_team,
            player_name,
            player_image,
            team_name,
            league
        )

        # Create bet details section
        PlayerPropImageGenerator._create_player_prop_bet_details_section(
            draw,
            params,
            line,
            prop_type,
            odds,
            units,
            units_display_mode,
            display_as_risk,
        )

        # Create footer section
        PlayerPropImageGenerator._create_player_prop_footer_section(
            draw, params, bet_id, timestamp
        )

        # Save or return the image
        if output_path:
            image.save(output_path, "PNG")
            return output_path
        else:
            return image
