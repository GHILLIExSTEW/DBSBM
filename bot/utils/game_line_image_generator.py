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
    font_regular = ImageFont.truetype("bot/assets/fonts/Roboto-Regular.ttf", 24)
    font_bold = ImageFont.truetype("bot/assets/fonts/Roboto-Bold.ttf", 32)

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
    from bot.config.leagues import LEAGUE_CONFIG

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
        default_sport_path = f"bot/static/logos/default_{sport}.webp"
        if os.path.exists(default_sport_path):
            right_img = Image.open(default_sport_path).resize((100, 100))
        else:
            right_img = Image.open("bot/static/logos/default_image.webp").resize(
                (100, 100)
            )
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

        from bot.config.asset_paths import get_sport_category_for_path
        from bot.config.image_settings import (
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
        lock_icon_path = "bot/static/lock_icon.webp"

        font_dir = "bot/assets/fonts"
        font_bold = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", header_font_size)
        font_bold_team = ImageFont.truetype(
            f"{font_dir}/Roboto-Bold.ttf", team_font_size
        )
        font_vs = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", vs_font_size)
        font_line = ImageFont.truetype(f"{font_dir}/Roboto-Regular.ttf", line_font_size)
        font_odds = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", odds_font_size)
        font_risk = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", risk_font_size)
        font_footer = ImageFont.truetype(
            f"{font_dir}/Roboto-Regular.ttf", footer_font_size
        )

        # Use default background color

        image = Image.new("RGB", (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)

        # Header (league logo + text)
        logo_display_size = (45, 45)
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

        league_logo_path = None
        for dir_variant in league_dir_variants:
            dir_path = f"bot/static/logos/leagues/{sport_category}/{dir_variant}"
            if os.path.exists(dir_path):
                for file_variant in logo_file_variants:
                    candidate_path = os.path.join(dir_path, file_variant)
                    if os.path.exists(candidate_path):
                        league_logo_path = candidate_path
                        logger.info(
                            f"[IMAGE GENERATOR] Found league logo: {league_logo_path}"
                        )
                        break
                if league_logo_path:
                    break
        league_logo = None
        if league_logo_path:
            try:
                league_logo_original = Image.open(league_logo_path).convert("RGBA")
                # Maintain aspect ratio when resizing
                league_logo_original.thumbnail(logo_display_size, Image.Resampling.LANCZOS)
                league_logo = league_logo_original
            except Exception:
                league_logo = None
        # Get proper league display name
        from bot.config.leagues import LEAGUE_CONFIG

        # Try to get display name from LEAGUE_CONFIG, but also check if the league itself is already a display name
        league_display_name = league  # Default to the league parameter
        if league in LEAGUE_CONFIG:
            league_display_name = LEAGUE_CONFIG[league].get("name", league)
        else:
            # If not found in LEAGUE_CONFIG, the league might already be a display name
            league_display_name = league

        logger.info(
            f"[IMAGE GENERATOR] League: {league}, Display name: {league_display_name}"
        )

        # Dynamic header text sizing with abbreviation support
        LEAGUE_ABBREVIATIONS = {
            "UEFA Champions League": "UEFA CL",
            "ChampionsLeague": "UEFA CL",
            "UEFA CL": "UEFA CL",
            "UEFA Europa League": "UEFA Europa",
            "EuropaLeague": "UEFA Europa",
            "English Premier League": "EPL",
            "Major League Baseball": "MLB",
            "National Basketball Association": "NBA",
            "National Football League": "NFL",
            "Women's National Basketball Association": "WNBA",
            "Bundesliga": "Bundesliga",
            "La Liga": "La Liga",
            "Serie A": "Serie A",
            "Ligue 1": "Ligue 1",
            # Add more as needed
        }

        def create_header_text_with_fallback(
            league_name, font, max_width, logo_width=0
        ):
            """Create header text that fits within the available width, always keeping '- Game Line'."""
            suffix = " - Game Line"
            # Try full name
            full_text = f"{league_name}{suffix}"
            text_width = font.getbbox(full_text)[2]
            if text_width <= max_width:
                return full_text
            # Try abbreviation
            abbr = LEAGUE_ABBREVIATIONS.get(league_name, None)
            if abbr:
                abbr_text = f"{abbr}{suffix}"
                abbr_width = font.getbbox(abbr_text)[2]
                if abbr_width <= max_width:
                    return abbr_text
                # Truncate abbreviation if needed
                truncated = abbr
                while truncated and font.getbbox(f"{truncated}{suffix}")[2] > max_width:
                    truncated = truncated[:-1]
                if truncated:
                    return f"{truncated}{suffix}"
            # If no abbreviation or still too long, truncate league name
            truncated = league_name
            while truncated and font.getbbox(f"{truncated}{suffix}")[2] > max_width:
                truncated = truncated[:-1]
            if truncated:
                return f"{truncated}{suffix}"
            else:
                return suffix.strip()  # Fallback

        # Calculate available width for text (accounting for logo and padding)
        logo_space = logo_display_size[0] + 15 if league_logo else 0
        available_text_width = (
            image_width - 48 - logo_space
        )  # 48px total padding (24px each side)
        header_text = create_header_text_with_fallback(
            league_display_name, font_bold, available_text_width, logo_space
        )

        header_w, header_h = font_bold.getbbox(header_text)[2:]
        block_h = max(logo_display_size[1], header_h)
        block_w = logo_display_size[0] + 15 + header_w if league_logo else header_w
        block_x = (image_width - block_w) // 2
        block_y = 25
        if league_logo:
            logo_y = block_y + (block_h - logo_display_size[1]) // 2
            text_y = block_y + (block_h - header_h) // 2
            # Use the RGBA image as the mask for proper transparency
            if league_logo.mode == "RGBA":
                image.paste(league_logo, (block_x, logo_y), league_logo)
            else:
                # Fallback if not RGBA
                image.paste(league_logo, (block_x, logo_y))
            text_x = block_x + logo_display_size[0] + 15
        else:
            text_x = block_x
            text_y = block_y
        draw.text(
            (text_x, text_y), header_text, font=font_bold, fill="white", anchor="lt"
        )

        # Teams Section
        y_base = 85
        section_width = image_width // 2 - padding * 1.5
        home_section_center_x = padding + section_width // 2
        away_section_center_x = image_width - padding - section_width // 2
        center_x = image_width // 2

        # Special handling for manual entry and darts logos
        if league.upper() == "MANUAL":
            # For manual entry, use default logos
            from PIL import Image
            import os

            default_logo_path = "bot/static/logos/default_image.webp"
            if os.path.exists(default_logo_path):
                default_logo = Image.open(default_logo_path)
                default_logo_resized = default_logo.convert("RGBA").resize(logo_size)

                # Use default logo for both teams
                home_logo_x = int(home_section_center_x - logo_size[0] // 2)
                away_logo_x = int(away_section_center_x - logo_size[0] // 2)
                # Use RGBA image as mask for proper transparency
                if default_logo_resized.mode == 'RGBA':
                    image.paste(default_logo_resized, (home_logo_x, y_base), default_logo_resized)
                    image.paste(default_logo_resized, (away_logo_x, y_base), default_logo_resized)
                else:
                    image.paste(default_logo_resized, (home_logo_x, y_base))
                    image.paste(default_logo_resized, (away_logo_x, y_base))
        elif league.lower() in ["darts", "tennis", "golf", "f1"] or any(sport in league.lower() for sport in ["darts", "tennis", "golf", "f1", "formula"]):
            from PIL import Image
            import os

            # Determine sport type for logo selection
            sport = "darts"  # default
            if "tennis" in league.lower():
                sport = "tennis"
            elif "golf" in league.lower():
                sport = "golf"
            elif "f1" in league.lower() or "formula" in league.lower():
                sport = "f1"

            # For individual sports, use [sport]_all.webp for selected team, default_[sport].webp for opponent
            sport_all_path = f"bot/static/logos/{sport}_all.webp"
            default_sport_path = f"bot/static/logos/default_{sport}.webp"

            # Load sport-specific logos
            home_logo = None
            away_logo = None

            if os.path.exists(sport_all_path):
                home_logo = Image.open(sport_all_path)
            if os.path.exists(default_sport_path):
                away_logo = Image.open(default_sport_path)

            # For individual sports, use [sport]_all.webp for selected team, default_[sport].webp for opponent
            if selected_team:
                if selected_team.lower() == home_team.lower():
                    # Home team is selected - use [sport]_all.webp for home, default_[sport].webp for away
                    if home_logo:
                        home_logo_resized = home_logo.convert("RGBA").resize(logo_size)
                        home_logo_x = int(home_section_center_x - logo_size[0] // 2)
                        # Use RGBA image as mask for proper transparency
                        if home_logo_resized.mode == 'RGBA':
                            image.paste(home_logo_resized, (home_logo_x, y_base), home_logo_resized)
                        else:
                            image.paste(home_logo_resized, (home_logo_x, y_base))
                    if away_logo:
                        away_logo_resized = away_logo.convert("RGBA").resize(logo_size)
                        away_logo_x = int(away_section_center_x - logo_size[0] // 2)
                        # Use RGBA image as mask for proper transparency
                        if away_logo_resized.mode == 'RGBA':
                            image.paste(away_logo_resized, (away_logo_x, y_base), away_logo_resized)
                        else:
                            image.paste(away_logo_resized, (away_logo_x, y_base))
                else:
                    # Away team is selected - use [sport]_all.webp for away, default_[sport].webp for home
                    if away_logo:
                        away_logo_resized = away_logo.convert("RGBA").resize(logo_size)
                        away_logo_x = int(away_section_center_x - logo_size[0] // 2)
                        # Use RGBA image as mask for proper transparency
                        if away_logo_resized.mode == 'RGBA':
                            image.paste(away_logo_resized, (away_logo_x, y_base), away_logo_resized)
                        else:
                            image.paste(away_logo_resized, (away_logo_x, y_base))
                    if home_logo:
                        home_logo_resized = home_logo.convert("RGBA").resize(logo_size)
                        home_logo_x = int(home_section_center_x - logo_size[0] // 2)
                        # Use RGBA image as mask for proper transparency
                        if home_logo_resized.mode == 'RGBA':
                            image.paste(home_logo_resized, (home_logo_x, y_base), home_logo_resized)
                        else:
                            image.paste(home_logo_resized, (home_logo_x, y_base))
            else:
                # No team selected yet - use default_[sport].webp for both
                if home_logo:
                    home_logo_resized = home_logo.convert("RGBA").resize(logo_size)
                    home_logo_x = int(home_section_center_x - logo_size[0] // 2)
                    # Use RGBA image as mask for proper transparency
                    if home_logo_resized.mode == 'RGBA':
                        image.paste(home_logo_resized, (home_logo_x, y_base), home_logo_resized)
                    else:
                        image.paste(home_logo_resized, (home_logo_x, y_base))
                if away_logo:
                    away_logo_resized = away_logo.convert("RGBA").resize(logo_size)
                    away_logo_x = int(away_section_center_x - logo_size[0] // 2)
                    # Use RGBA image as mask for proper transparency
                    if away_logo_resized.mode == 'RGBA':
                        image.paste(away_logo_resized, (away_logo_x, y_base), away_logo_resized)
                    else:
                        image.paste(away_logo_resized, (away_logo_x, y_base))
        else:
            # Normal logo loading for other sports
            home_logo = self._load_team_logo(home_team, league)
            if home_logo:
                home_logo_resized = home_logo.convert("RGBA").resize(logo_size)
                home_logo_x = int(home_section_center_x - logo_size[0] // 2)
                # Use RGBA image as mask for proper transparency
                if home_logo_resized.mode == 'RGBA':
                    image.paste(home_logo_resized, (home_logo_x, y_base), home_logo_resized)
                else:
                    image.paste(home_logo_resized, (home_logo_x, y_base))
            # Away logo
            away_logo = self._load_team_logo(away_team, league)
            if away_logo:
                away_logo_resized = away_logo.convert("RGBA").resize(logo_size)
                away_logo_x = int(away_section_center_x - logo_size[0] // 2)
                # Use RGBA image as mask for proper transparency
                if away_logo_resized.mode == 'RGBA':
                    image.paste(away_logo_resized, (away_logo_x, y_base), away_logo_resized)
                else:
                    image.paste(away_logo_resized, (away_logo_x, y_base))

        # VS
        vs_text = "VS"
        vs_w, vs_h = font_vs.getbbox(vs_text)[2:]
        vs_x = center_x - vs_w // 2
        vs_y = y_base + logo_size[1] // 2 - vs_h // 2
        draw.text((vs_x, vs_y), vs_text, font=font_vs, fill="#FFD700", anchor="lt")

        # Team names
        home_color = (
            "#00FF00"
            if selected_team and selected_team.lower() == home_team.lower()
            else "white"
        )
        away_color = (
            "#00FF00"
            if selected_team and selected_team.lower() == away_team.lower()
            else "white"
        )
        home_name_w, _ = font_bold_team.getbbox(home_team)[2:]
        away_name_w, _ = font_bold_team.getbbox(away_team)[2:]
        home_name_x = home_section_center_x - home_name_w // 2
        away_name_x = away_section_center_x - away_name_w // 2
        team_name_y = y_base + logo_size[1] + 8
        draw.text(
            (home_name_x, team_name_y),
            home_team,
            font=font_bold_team,
            fill=home_color,
            anchor="lt",
        )
        draw.text(
            (away_name_x, team_name_y),
            away_team,
            font=font_bold_team,
            fill=away_color,
            anchor="lt",
        )

        # ML line
        line_text = str(line)
        line_w, line_h = font_line.getbbox(line_text)[2:]
        line_y = team_name_y + 32
        draw.text(
            ((image_width - line_w) // 2, line_y),
            line_text,
            font=font_line,
            fill="white",
            anchor="lt",
        )

        # Separator line above odds
        sep_above_odds_y = line_y + line_h + 18  # 18px below the ML line
        draw.line(
            [(padding, sep_above_odds_y), (image_width - padding, sep_above_odds_y)],
            fill="#aaaaaa",
            width=1,
        )

        # Odds
        odds_val = -110
        try:
            odds_val = int(float(odds)) if odds is not None else -110
        except Exception:
            pass
        odds_text = f"{odds_val:+d}" if odds_val > 0 else f"{odds_val:d}"
        odds_bbox = font_odds.getbbox(odds_text)
        odds_w, odds_h = odds_bbox[2] - odds_bbox[0], odds_bbox[3] - odds_bbox[1]
        odds_y = sep_above_odds_y + 24
        draw.text(
            ((image_width - odds_w) // 2, odds_y),
            odds_text,
            font=font_odds,
            fill="white",
            anchor="lt",
        )

        # Risk/Units (yellow, lock icons)
        from bot.utils.bet_utils import (
            calculate_profit_from_odds,
            determine_risk_win_display_auto,
            format_units_display,
        )

        profit = calculate_profit_from_odds(odds_val, units)
        unit_label = "Unit" if units <= 1 else "Units"

        if units_display_mode == "manual" and display_as_risk is not None:
            payout_text = format_units_display(units, display_as_risk, unit_label)
        else:
            # Auto mode: intelligent determination based on odds and profit ratio
            if units_display_mode == "auto":
                display_as_risk_auto = determine_risk_win_display_auto(
                    odds_val, units, profit
                )
                payout_text = format_units_display(
                    units, display_as_risk_auto, unit_label
                )
            else:
                # Fallback to old logic for backward compatibility
                if profit < 1.0:
                    payout_text = f"To Risk {units:.2f} {unit_label}"
                else:
                    payout_text = f"To Win {units:.2f} {unit_label}"
        payout_bbox = font_risk.getbbox(payout_text)
        payout_w, payout_h = (
            payout_bbox[2] - payout_bbox[0],
            payout_bbox[3] - payout_bbox[1],
        )
        payout_y = odds_y + odds_h + 8
        lock_icon = None
        try:
            lock_icon = Image.open(lock_icon_path).resize((24, 24))
            # Convert to RGBA to ensure proper transparency handling
            if lock_icon.mode != 'RGBA':
                lock_icon = lock_icon.convert('RGBA')
        except Exception:
            lock_icon = None
        if lock_icon:
            # Use RGBA image as mask for proper transparency
            if lock_icon.mode == 'RGBA':
                image.paste(lock_icon, ((image_width - payout_w) // 2 - 28, payout_y), lock_icon)
            else:
                image.paste(lock_icon, ((image_width - payout_w) // 2 - 28, payout_y))
            draw.text(
                ((image_width - payout_w) // 2, payout_y),
                payout_text,
                font=font_risk,
                fill="#FFD700",
                anchor="lt",
            )
            # Use RGBA image as mask for proper transparency
            if lock_icon.mode == 'RGBA':
                image.paste(lock_icon, ((image_width - payout_w) // 2 + payout_w + 8, payout_y), lock_icon)
            else:
                image.paste(lock_icon, ((image_width - payout_w) // 2 + payout_w + 8, payout_y))
        else:
            draw.text(
                ((image_width - payout_w) // 2, payout_y),
                payout_text,
                font=font_risk,
                fill="#FFD700",
                anchor="lt",
            )

        # Footer (bet id and timestamp)
        footer_padding = 12
        footer_y = image_height - footer_padding - font_footer.size

        # Ensure bet_id is properly formatted
        if bet_id and str(bet_id).strip():
            bet_id_text = f"Bet #{str(bet_id).strip()}"
        else:
            bet_id_text = ""

        timestamp_text = timestamp.strftime("%Y-%m-%d %H:%M UTC") if timestamp else ""

        # Draw bet ID bottom left
        if bet_id_text:
            draw.text(
                (padding, footer_y), bet_id_text, font=font_footer, fill="#888888"
            )

        # Draw timestamp bottom right
        if timestamp_text:
            ts_bbox = font_footer.getbbox(timestamp_text)
            ts_width = ts_bbox[2] - ts_bbox[0]
            draw.text(
                (image_width - padding - ts_width, footer_y),
                timestamp_text,
                font=font_footer,
                fill="#888888",
            )

        # Save or return as bytes
        if output_path:
            image.save(output_path)
            return None
        else:
            import io

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.getvalue()

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

        from bot.utils.asset_loader import asset_loader

        # Special handling for manual entry
        if league.upper() == "MANUAL":
            default_logo_path = "bot/static/logos/default_image.webp"
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
            sport_all_path = f"bot/static/logos/{sport}_all.webp"
            default_sport_path = f"bot/static/logos/default_{sport}.webp"

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
        from bot.utils.asset_loader import asset_loader

        return asset_loader.load_player_image(
            player_name, team_name, league, getattr(self, "guild_id", None)
        )
