import logging

logger = logging.getLogger(__name__)


def generate_player_prop_bet_image(
    player_name,
    player_picture_path,
    team_name,
    team_logo_path,
    line,
    units,
    output_path,
):
    """Generates a player prop bet slip image."""
    from PIL import Image, ImageDraw, ImageFont

    # Load fonts
    font_regular = ImageFont.truetype(
        "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Regular.ttf", 24
    )
    font_bold = ImageFont.truetype(
        "../../../StaticFiles/DBSBM/assets/fonts/Roboto-Bold.ttf", 32
    )

    # Create a blank image
    image_width, image_height = 800, 400
    image = Image.new("RGB", (image_width, image_height), "black")
    draw = ImageDraw.Draw(image)

    # Draw team name
    team_name_width, team_name_height = draw.textsize(team_name, font=font_bold)
    draw.text(
        ((image_width - team_name_width) / 2, 20),
        team_name,
        font=font_bold,
        fill="white",
    )

    import os

    # Determine if this is a non-team-based league (individual sport)
    from config.leagues import LEAGUE_CONFIG

    # Always use the league for sport_type lookup, not team_name
    league_key = None
    if team_logo_path:
        # Try to extract league from the path, e.g. .../DARTS/PDC/...
        parts = team_logo_path.split(os.sep)
        for part in parts:
            if part.upper() in LEAGUE_CONFIG:
                league_key = part.upper()
                break
    if not league_key and team_name.upper() in LEAGUE_CONFIG:
        league_key = team_name.upper()
    sport_type = None
    if league_key:
        sport_type = LEAGUE_CONFIG[league_key].get("sport_type", None)
        sport = LEAGUE_CONFIG[league_key].get("sport", "darts").lower()
    else:
        # fallback to guessing from path
        sport = "darts"
        if team_logo_path and "darts" in team_logo_path.lower():
            sport = "darts"
        elif team_logo_path and "tennis" in team_logo_path.lower():
            sport = "tennis"
        elif team_logo_path and "golf" in team_logo_path.lower():
            sport = "golf"
        elif team_logo_path and "mma" in team_logo_path.lower():
            sport = "mma"
        elif team_logo_path and "f1" in team_logo_path.lower():
            sport = "f1"

    # Only use this logic for non-team-based leagues (player props for individual sports)
    if sport_type == "Individual Player":
        player_img = Image.open(player_picture_path).resize((100, 100))
        image.paste(player_img, (50, 100))
        default_sport_path = (
            f"../../../StaticFiles/DBSBM/static/logos/default_{sport}.webp"
        )
        if os.path.exists(default_sport_path):
            right_img = Image.open(default_sport_path).resize((100, 100))
        else:
            right_img = Image.open(
                "../../../StaticFiles/DBSBM/static/logos/default_image.webp"
            ).resize((100, 100))
        image.paste(right_img, (650, 100))
    else:
        # Team-based: show both images as before
        team_logo = Image.open(team_logo_path).resize((100, 100))
        image.paste(team_logo, (50, 100))
        player_picture = Image.open(player_picture_path).resize((100, 100))
        image.paste(player_picture, (650, 100))

    # Draw player name
    player_name_width, player_name_height = draw.textsize(player_name, font=font_bold)
    draw.text(
        ((image_width - player_name_width) / 2, 220),
        player_name,
        font=font_bold,
        fill="white",
    )

    # Draw line and units/footer section
    line_text = f"Line: {line}"
    units_text = f"Units: {units}"
    footer_text = "Bet responsibly."

    draw.text((50, 300), line_text, font=font_regular, fill="white")
    draw.text((50, 340), units_text, font=font_regular, fill="white")
    draw.text((image_width - 250, 340), footer_text, font=font_regular, fill="white")

    # Save the image
    if output_path:
        image.save(output_path)
        return None
    else:
        import io

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()


class GameLineImageGenerator:
    def __init__(self, fonts=None, padding=0, guild_id=None):
        """Initialize the GameLineImageGenerator with optional fonts and padding."""
        self.fonts = fonts
        self.padding = padding
        self.guild_id = guild_id

    def _setup_image_parameters(self):
        """Setup image parameters and fonts."""
        from config.image_settings import (
            BACKGROUND_COLOR,
            DEFAULT_PADDING,
            FOOTER_FONT_SIZE,
            HEADER_FONT_SIZE,
            IMAGE_HEIGHT,
            IMAGE_WIDTH,
            LINE_FONT_SIZE,
            LOGO_SIZE,
            ODDS_FONT_SIZE,
            RISK_FONT_SIZE,
            TEAM_FONT_SIZE,
            VS_FONT_SIZE,
        )

        image_width, image_height = IMAGE_WIDTH, IMAGE_HEIGHT
        bg_color = BACKGROUND_COLOR
        padding = DEFAULT_PADDING
        logo_size = LOGO_SIZE
        header_font_size = HEADER_FONT_SIZE
        team_font_size = TEAM_FONT_SIZE
        vs_font_size = VS_FONT_SIZE
        line_font_size = LINE_FONT_SIZE
        odds_font_size = ODDS_FONT_SIZE
        risk_font_size = RISK_FONT_SIZE
        footer_font_size = FOOTER_FONT_SIZE

        font_dir = "../../../StaticFiles/DBSBM/assets/fonts"
        fonts = {
            "bold": ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", header_font_size),
            "bold_team": ImageFont.truetype(
                f"{font_dir}/Roboto-Bold.ttf", team_font_size
            ),
            "vs": ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", vs_font_size),
            "line": ImageFont.truetype(
                f"{font_dir}/Roboto-Regular.ttf", line_font_size
            ),
            "odds": ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", odds_font_size),
            "risk": ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", risk_font_size),
            "footer": ImageFont.truetype(
                f"{font_dir}/Roboto-Regular.ttf", footer_font_size
            ),
        }

        return {
            "image_width": image_width,
            "image_height": image_height,
            "bg_color": bg_color,
            "padding": padding,
            "logo_size": logo_size,
            "fonts": fonts,
        }

    def _find_league_logo(self, league):
        """Find the appropriate league logo file."""
        from config.asset_paths import get_sport_category_for_path

        league_upper = league.upper()
        league_cap = league.capitalize()
        league_lower = league.lower()
        sport_category = get_sport_category_for_path(league_upper)

        # Special handling for UEFA Champions League to match team folder structure
        if league_upper == "UEFA CHAMPIONS LEAGUE" or league == "ChampionsLeague":
            league_dir_variants = [
                "uefa champions league",
                league_upper,
                league_cap,
                league_lower,
            ]
            logo_file_variants = [
                "uefa champions league.webp",
                league_upper + ".webp",
                league_cap + ".webp",
                league_lower + ".webp",
            ]
        elif league_upper == "UEFA EUROPA LEAGUE" or league == "EuropaLeague":
            league_dir_variants = [
                "uefa_europa_league",
                league_upper,
                league_cap,
                league_lower,
            ]
            logo_file_variants = [
                "uefa_europa_league.webp",
                league_upper + ".webp",
                league_cap + ".webp",
                league_lower + ".webp",
            ]
        else:
            league_dir_variants = [league_upper, league_cap, league_lower]
            logo_file_variants = [
                league_upper + ".webp",
                league_cap + ".webp",
                league_lower + ".webp",
            ]

        # Try to find the logo file
        for logo_file in logo_file_variants:
            logo_path = f"../../../StaticFiles/DBSBM/static/logos/leagues/{sport_category}/{logo_file}"
            if os.path.exists(logo_path):
                return logo_path

        return None

    def _create_header_section(self, image, draw, params, league, logo_path):
        """Create the header section with league logo and text."""
        logo_display_size = (45, 45)

        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert("RGBA")
                logo = logo.resize(logo_display_size, Image.Resampling.LANCZOS)
                image.paste(logo, (params["padding"], params["padding"]), logo)
                text_x = params["padding"] + logo_display_size[0] + 10
            except Exception as e:
                logger.warning(f"Failed to load logo {logo_path}: {e}")
                text_x = params["padding"]
        else:
            text_x = params["padding"]

        # Create header text with fallback
        def create_header_text_with_fallback(
            league_name, font, max_width, logo_width=0
        ):
            """Create header text with fallback for long league names."""
            text = league_name
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]

            if text_width > max_width:
                # Try with shorter name
                if " " in league_name:
                    words = league_name.split(" ")
                    for i in range(len(words) - 1, 0, -1):
                        shorter_text = " ".join(words[:i])
                        bbox = draw.textbbox((0, 0), shorter_text, font=font)
                        if bbox[2] - bbox[0] <= max_width:
                            return shorter_text

                # If still too long, truncate
                while text_width > max_width and len(text) > 3:
                    text = text[:-1]
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]

            return text

        max_text_width = params["image_width"] - text_x - params["padding"]
        header_text = create_header_text_with_fallback(
            league, params["fonts"]["bold"], max_text_width, logo_display_size[0]
        )

        # Calculate text position
        bbox = draw.textbbox((0, 0), header_text, font=params["fonts"]["bold"])
        text_height = bbox[3] - bbox[1]
        text_y = params["padding"] + (logo_display_size[1] - text_height) // 2

        # Draw header text
        draw.text(
            (text_x, text_y),
            header_text,
            fill=(255, 255, 255),
            font=params["fonts"]["bold"],
        )

    def _create_teams_section(
        self, image, draw, params, home_team, away_team, selected_team
    ):
        """Create the teams section with logos and names."""
        # Load team logos
        home_logo = self._load_team_logo(home_team, league)
        away_logo = self._load_team_logo(away_team, league)

        # Draw teams section
        self.draw_teams_section(
            image,
            draw,
            params["image_width"],
            home_team,
            away_team,
            home_logo,
            away_logo,
            selected_team,
        )

    def _create_bet_details_section(
        self, draw, params, line, odds, units, units_display_mode, display_as_risk
    ):
        """Create the bet details section with line, odds, and units."""
        # Calculate positions
        line_y = 200
        odds_y = line_y + 40
        units_y = odds_y + 40

        # Draw line
        line_text = f"Line: {line}"
        draw.text(
            (params["padding"], line_y),
            line_text,
            fill=(255, 255, 255),
            font=params["fonts"]["line"],
        )

        # Draw odds
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

    def _create_footer_section(self, draw, params, bet_id, timestamp):
        """Create the footer section with bet ID and timestamp."""
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

    def generate_bet_slip_image(
        self,
        league,
        home_team,
        away_team,
        line,
        odds,
        units,
        bet_id=None,
        timestamp=None,
        selected_team=None,
        output_path=None,
        units_display_mode="auto",
        display_as_risk=None,
    ):
        """Generates a game line bet slip image."""
        import os
        from PIL import Image, ImageDraw, ImageFont

        # Setup image parameters and fonts
        params = self._setup_image_parameters()

        # Create base image
        image = Image.new(
            "RGB", (params["image_width"], params["image_height"]), params["bg_color"]
        )
        draw = ImageDraw.Draw(image)

        # Find league logo
        logo_path = self._find_league_logo(league)

        # Create header section
        self._create_header_section(image, draw, params, league, logo_path)

        # Create teams section
        self._create_teams_section(
            image, draw, params, home_team, away_team, selected_team
        )

        # Create bet details section
        self._create_bet_details_section(
            draw, params, line, odds, units, units_display_mode, display_as_risk
        )

        # Create footer section
        self._create_footer_section(draw, params, bet_id, timestamp)

        # Save or return the image
        if output_path:
            image.save(output_path, "PNG")
            return output_path
        else:
            return image

    def draw_teams_section(
        self,
        img,
        draw,
        image_width,
        home_team,
        away_team,
        home_logo,
        away_logo,
        selected_team=None,
    ):
        """Draws the teams section for game line bets."""
        from PIL import Image

        y_base = 85
        logo_size = (120, 120)
        text_y_offset = logo_size[1] + 8
        team_name_font_large = self.fonts["font_b_24"]
        team_name_font_small = self.fonts.get("font_b_18", self.fonts["font_b_24"])
        vs_font = self.fonts["font_b_28"]
        green_color = "#00FF00"  # Bright green
        white_color = "white"
        vs_color = "#FFD700"  # Gold color for VS

        section_width = image_width // 2 - self.padding * 1.5
        home_section_center_x = self.padding + section_width // 2
        away_section_center_x = image_width - self.padding - section_width // 2

        # Draw VS text in center
        center_x = image_width // 2
        vs_text = "VS"
        bbox_vs = vs_font.getbbox(vs_text)
        vs_w = bbox_vs[2] - bbox_vs[0]
        vs_h = bbox_vs[3] - bbox_vs[1]
        vs_x = center_x - vs_w // 2
        vs_y = y_base + logo_size[1] // 2 - vs_h // 2
        draw.text((vs_x, vs_y), vs_text, font=vs_font, fill=vs_color, anchor="lt")

        # Draw home team section
        if home_logo:
            try:
                home_logo_resized = home_logo.resize(
                    logo_size, Image.Resampling.LANCZOS
                )
                home_logo_x = home_section_center_x - logo_size[0] // 2
                if home_logo_resized.mode == "RGBA":
                    img.paste(
                        home_logo_resized,
                        (int(home_logo_x), int(y_base)),
                        home_logo_resized,
                    )
                else:
                    img.paste(home_logo_resized, (int(home_logo_x), int(y_base)))
            except Exception as e:
                pass  # Silently handle logo errors

        # Choose font size based on available width
        def _pick_font(name: str, max_width: int):
            bbox = team_name_font_large.getbbox(name)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                return team_name_font_large, w
            bbox_s = team_name_font_small.getbbox(name)
            return team_name_font_small, bbox_s[2] - bbox_s[0]

        # Home name
        font_home, home_name_w = _pick_font(home_team, section_width - 10)
        home_name_x = home_section_center_x - home_name_w // 2
        home_color = (
            green_color
            if selected_team and selected_team.lower() == home_team.lower()
            else white_color
        )
        draw.text(
            (home_name_x, y_base + text_y_offset),
            home_team,
            font=font_home,
            fill=home_color,
            anchor="lt",
        )

        # Draw away team section
        if away_logo:
            try:
                away_logo_resized = away_logo.resize(
                    logo_size, Image.Resampling.LANCZOS
                )
                away_logo_x = away_section_center_x - logo_size[0] // 2
                if away_logo_resized.mode == "RGBA":
                    img.paste(
                        away_logo_resized,
                        (int(away_logo_x), int(y_base)),
                        away_logo_resized,
                    )
                else:
                    img.paste(away_logo_resized, (int(away_logo_x), int(y_base)))
            except Exception as e:
                pass  # Silently handle logo errors

        # Away name
        font_away, away_name_w = _pick_font(away_team, section_width - 10)
        away_name_x = away_section_center_x - away_name_w // 2
        away_color = (
            green_color
            if selected_team and selected_team.lower() == away_team.lower()
            else white_color
        )
        draw.text(
            (away_name_x, y_base + text_y_offset),
            away_team,
            font=font_away,
            fill=away_color,
            anchor="lt",
        )

        return y_base + text_y_offset + 50  # Return y position for next section

    def _load_team_logo(self, team_name: str, league: str):
        import os

        from PIL import Image

        from utils.asset_loader import asset_loader

        # Special handling for manual entry
        if league.upper() == "MANUAL":
            default_logo_path = (
                "../../../StaticFiles/DBSBM/static/logos/default_image.webp"
            )
            if os.path.exists(default_logo_path):
                return Image.open(default_logo_path)
            else:
                logger.warning(f"Default logo not found at {default_logo_path}")
                return None
        # Special handling for individual sports - use specific logos
        elif league.lower() in ["darts", "tennis", "golf", "f1"] or any(
            sport in league.lower()
            for sport in ["darts", "tennis", "golf", "f1", "formula"]
        ):
            # Determine sport type for logo selection
            sport = "darts"  # default
            if "tennis" in league.lower():
                sport = "tennis"
            elif "golf" in league.lower():
                sport = "golf"
            elif "f1" in league.lower() or "formula" in league.lower():
                sport = "f1"

            # For individual sports, use [sport]_all.webp for the selected team and default_[sport].webp for opponent
            # This will be handled in the calling code based on selected_team
            sport_all_path = f"../../../StaticFiles/DBSBM/static/logos/{sport}_all.webp"
            default_sport_path = (
                f"../../../StaticFiles/DBSBM/static/logos/default_{sport}.webp"
            )

            if os.path.exists(sport_all_path):
                return Image.open(sport_all_path)
            else:
                logger.warning(
                    f"{sport.capitalize()} logo not found at {sport_all_path}"
                )
                return asset_loader.load_team_logo(
                    team_name, league, getattr(self, "guild_id", None)
                )
        else:
            return asset_loader.load_team_logo(
                team_name, league, getattr(self, "guild_id", None)
            )

    def _load_player_image(self, player_name: str, team_name: str, league: str):
        from utils.asset_loader import asset_loader

        return asset_loader.load_player_image(
            player_name, team_name, league, getattr(self, "guild_id", None)
        )
