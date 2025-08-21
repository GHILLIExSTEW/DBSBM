import os
import logging

logger = logging.getLogger(__name__)

# Add module-level PIL and asset_loader imports to avoid repeated/missing imports
from PIL import Image, ImageDraw, ImageFont
from utils.asset_loader import asset_loader


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
    # Local PIL imports removed; using module-level imports and asset_loader

    # Load fonts via asset_loader
    try:
        font_regular_path = asset_loader.get_font_path("Roboto-Regular.ttf")
        font_bold_path = asset_loader.get_font_path("Roboto-Bold.ttf")
        font_regular = ImageFont.truetype(font_regular_path, 24)
        font_bold = ImageFont.truetype(font_bold_path, 32)
    except Exception:
        font_regular = ImageFont.load_default()
        font_bold = ImageFont.load_default()

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

    # Determine if this is a non-team-based league (individual sport)
    from config.leagues import LEAGUE_CONFIG

    # Always use the league for sport_type lookup, not team_name
    league_key = None
    if team_logo_path:
        # Try to extract league from the path, e.g. path containing league code
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
        # Load player image via asset_loader if provided path is a URL or path
        try:
            player_img = None
            if player_picture_path:
                # If it's an absolute path under static, try loading directly
                candidate = (
                    player_picture_path
                    if os.path.isabs(player_picture_path)
                    else os.path.join(asset_loader.get_static_dir() or "", player_picture_path)
                )
                if candidate and os.path.exists(candidate):
                    player_img = Image.open(candidate).resize((100, 100))
            if player_img is None:
                player_img = asset_loader.load_player_image(player_name, team_name, league_key or team_name)[0]
                if player_img:
                    player_img = player_img.resize((100, 100))
        except Exception:
            player_img = Image.new("RGBA", (100, 100), (50, 50, 50))

        image.paste(player_img, (50, 100))

        default_sport_img = None
        default_sport_path = os.path.join(asset_loader.get_logo_dir(), f"default_{sport}.webp")
        if os.path.exists(default_sport_path):
            try:
                default_sport_img = Image.open(default_sport_path).resize((100, 100))
            except Exception:
                default_sport_img = None
        if default_sport_img is None:
            default_image_path = os.path.join(asset_loader.get_logo_dir(), "default_image.webp")
            try:
                default_sport_img = Image.open(default_image_path).resize((100, 100))
            except Exception:
                default_sport_img = Image.new("RGBA", (100, 100), (80, 80, 80))
        image.paste(default_sport_img, (650, 100))
    else:
        # Team-based: load team logo via asset_loader
        try:
            team_logo_img = asset_loader.load_team_logo(team_name, team_name)
            if team_logo_img:
                team_logo_img = team_logo_img.resize((100, 100))
            else:
                team_logo_img = Image.new("RGBA", (100, 100), (60, 60, 60))
        except Exception:
            team_logo_img = Image.new("RGBA", (100, 100), (60, 60, 60))

        try:
            player_picture_img = None
            candidate = (
                player_picture_path
                if player_picture_path and os.path.isabs(player_picture_path)
                else os.path.join(asset_loader.get_static_dir() or "", player_picture_path or "")
            )
            if candidate and os.path.exists(candidate):
                player_picture_img = Image.open(candidate).resize((100, 100))
            if player_picture_img is None:
                player_picture_img = asset_loader.load_player_image(player_name, team_name, league_key or team_name)[0]
                if player_picture_img:
                    player_picture_img = player_picture_img.resize((100, 100))
            if player_picture_img is None:
                player_picture_img = Image.new("RGBA", (100, 100), (80, 80, 80))
        except Exception:
            player_picture_img = Image.new("RGBA", (100, 100), (80, 80, 80))

        image.paste(team_logo_img, (50, 100))
        image.paste(player_picture_img, (650, 100))

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
        units=None,
    else:
        import io
        selected_team=None,
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()


from bot.data.db_manager import db_manager

class GameLineImageGenerator:
    def __init__(self, fonts=None, padding=0, guild_id=None, db_conn=None):
        """Initialize the GameLineImageGenerator with optional fonts, padding, and db connection."""
        self.fonts = fonts
        self.padding = padding
        self.guild_id = guild_id
        self.db_conn = None  # Use db_manager directly for async queries

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

        # Use asset_loader to load fonts (with fallback)
        fonts = {
            "bold": asset_loader.load_font("Roboto-Bold.ttf", header_font_size),
            "bold_team": asset_loader.load_font("Roboto-Bold.ttf", team_font_size),
            "vs": asset_loader.load_font("Roboto-Bold.ttf", vs_font_size),
            "line": asset_loader.load_font("Roboto-Regular.ttf", line_font_size),
            "odds": asset_loader.load_font("Roboto-Bold.ttf", odds_font_size),
            "risk": asset_loader.load_font("Roboto-Bold.ttf", risk_font_size),
            "footer": asset_loader.load_font("Roboto-Regular.ttf", footer_font_size),
            # older code expected specific keys, keep them as aliases
            "font_b_24": asset_loader.load_font("Roboto-Bold.ttf", 24),
            "font_b_18": asset_loader.load_font("Roboto-Bold.ttf", 18),
            "font_b_28": asset_loader.load_font("Roboto-Bold.ttf", 28),
        }

        # Ensure instance-level fonts are set so other instance methods can rely on self.fonts
        try:
            self.fonts = fonts
        except Exception:
            # In rare cases self may not be present; ignore and continue returning params
            pass

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

        # Try to find the logo file using asset_loader's logos_dir
        logos_root = asset_loader.get_logo_dir()
        if not logos_root:
            return None

        # First try direct paths
        for logo_file in logo_file_variants:
            logo_path = os.path.join(logos_root, "leagues", sport_category, logo_file)
            if os.path.exists(logo_path):
                return logo_path

        # Try subfolder and lowercase filename first, then fallback to direct file
        logo_path_subfolder = os.path.join(
            "StaticFiles", "DBSBM", "static", "logos", "leagues",
            sport_category, league_upper, f"{league_lower}.webp"
        )
        logo_path_direct = os.path.join(
            "StaticFiles", "DBSBM", "static", "logos", "leagues",
            sport_category, f"{league_lower}.webp"
        )
        logo_path_upper_direct = os.path.join(
            "StaticFiles", "DBSBM", "static", "logos", "leagues",
            sport_category, f"{league_upper}.webp"
        )
        logo_path = None
        if os.path.exists(logo_path_subfolder):
            logo_path = logo_path_subfolder
        elif os.path.exists(logo_path_direct):
            logo_path = logo_path_direct
        elif os.path.exists(logo_path_upper_direct):
            logo_path = logo_path_upper_direct
        else:
            # Fallback: search for any .webp file in the league folder (case-insensitive)
            league_dir = os.path.join("StaticFiles", "DBSBM", "static", "logos", "leagues", sport_category, league_upper)
            if os.path.isdir(league_dir):
                for fname in os.listdir(league_dir):
                    if fname.lower().endswith(".webp"):
                        logo_path = os.path.join(league_dir, fname)
                        break
            # Fallback: search for any .webp file in the sport_category folder
            if not logo_path:
                sport_dir = os.path.join("StaticFiles", "DBSBM", "static", "logos", "leagues", sport_category)
                if os.path.isdir(sport_dir):
                    for fname in os.listdir(sport_dir):
                        if fname.lower().endswith(".webp") and league_upper in fname.upper():
                            logo_path = os.path.join(sport_dir, fname)
                            break
        logger.debug(f"League logo path: {logo_path}")
        logger.debug(f"Logo exists: {os.path.exists(logo_path) if logo_path else False}")
        header_text = f"{league_upper} GAMELINE BET"
        logo_w, logo_h = 60, 50  # Wider logo
        font_bold = params["fonts"]["bold"]
        font_team = params["fonts"]["bold_team"]
        font_vs = params["fonts"]["vs"]
        font_line = params["fonts"]["line"]
        font_odds = params["fonts"]["odds"]
        font_footer = params["fonts"]["footer"]
        image_width = params["image_width"]
        image_height = params["image_height"]
        padding = params["padding"]
        logo_size = params["logo_size"]
        text_w, text_h = font_bold.getbbox(header_text)[2:]
        total_w = logo_w + 12 + text_w
        start_x = (image_width - total_w) // 2
        y = padding
        # Paste league logo only if found
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path).convert("RGBA")
                logger.debug(f"Loaded logo image size: {logo_img.size}, mode: {logo_img.mode}")
                # Pad logo to (60, 50) if needed
                if logo_img.size != (logo_w, logo_h):
                    padded_logo = Image.new("RGBA", (logo_w, logo_h), (0,0,0,0))
                    lw, lh = logo_img.size
                    px = (logo_w - lw) // 2
                    py = (logo_h - lh) // 2
                    logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                    padded_logo.paste(logo_img, (px, py), logo_img)
                    logo_img = padded_logo
                image.paste(logo_img, (start_x, y), logo_img)
                logger.debug(f"Logo pasted at: {(start_x, y)}")
                text_x = start_x + logo_w + 12
            except Exception as e:
                logger.error(f"Failed to load/paste league logo at {logo_path}: {e}")
                text_x = start_x
        else:
            logger.warning(f"League logo not found at path: {logo_path}")
            text_x = start_x
        text_y = y + (logo_h - text_h) // 2
        draw.text((text_x, text_y), header_text, font=font_bold, fill="white")

        # === Body: Team Logos, VS, Team Names ===
        base_logo_size = logo_size
        lw = int(base_logo_size[0]*1.2)
        lh = int(base_logo_size[1]*1.2)
        quarter_w = image_width//4
        left_x = quarter_w - lw//2
        right_x = 3*quarter_w - lw//2
        logo_y = y + logo_h + 30
        # Left team logo
        home_logo = self._load_team_logo(home_team, league)
        if home_logo:
            hl = home_logo.convert("RGBA").resize((lw,lh), Image.Resampling.LANCZOS)
            image.paste(hl, (left_x, logo_y), hl)
        # Right team logo
        away_logo = self._load_team_logo(away_team, league)
        if away_logo:
            al = away_logo.convert("RGBA").resize((lw,lh), Image.Resampling.LANCZOS)
            image.paste(al, (right_x, logo_y), al)
        # VS text
        vs = "VS"
        vw, vh = font_vs.getbbox(vs)[2:]
        vxx = (image_width - vw)//2
        vyy = logo_y + (lh - vh)//2
        draw.text((vxx, vyy), vs, font=font_vs, fill=(255,215,0))

        # Team names under logos (closer to logos)
        name_y = logo_y + lh - 10  # Move up by 18px compared to previous
        # Ensure selected_team is always defined
        selected_team = selected_team if selected_team is not None else ''
        for name, x_pos in [(home_team, left_x), (away_team, right_x)]:
            if not name: continue
            w = font_team.getbbox(name)[2]
            nx = x_pos + (lw - w)//2
            color = (0,230,0) if name.lower()==(selected_team or '').lower() else "white"
            draw.text((nx, name_y), name, font=font_team, fill=color)

        # === Line (no label), Separator, Odds (move up) ===
        line_y = name_y + 22  # Move up by 10px compared to previous
        line_text = f"{line if line is not None else ''}"
        lw_txt = font_line.getbbox(line_text)[2]
        lx = (image_width - lw_txt)//2
        draw.text((lx, line_y), line_text, font=font_line, fill="white")

        sep_y = line_y + font_line.getbbox(line_text)[3] + 12  # Move up by 8px
        draw.line([(padding, sep_y), (image_width-padding, sep_y)], fill="#aaaaaa", width=1)

        odds_y = sep_y + 12  # Move up by 8px
        odds_text = f"{odds if odds is not None else ''}"
        ow = font_odds.getbbox(odds_text)[2]
        ox = (image_width - ow)//2
        draw.text((ox, odds_y), odds_text, font=font_odds, fill="white")

        # === Payout row below odds ===
        # Calculate payout text and icons
        from bot.utils.bet_utils import calculate_profit_from_odds, determine_risk_win_display_auto, format_units_display
        odds_val = float(odds) if odds is not None else 0.0
        profit = calculate_profit_from_odds(odds_val, units)
        display_as_risk = determine_risk_win_display_auto(odds_val, units, profit)
        unit_label = "Unit" if units == 1 else "Units"
        payout_text = format_units_display(units, display_as_risk, unit_label)
        # lock icon path
        lock_icon_path = os.path.join("StaticFiles", "DBSBM", "static", "lock_icon.webp")
        payout_y = odds_y + font_odds.getbbox(odds_text)[3] + 12
        # load lock icon
        try:
            lock_img = Image.open(lock_icon_path).resize((24,24)).convert("RGBA") if os.path.exists(lock_icon_path) else None
        except Exception:
            lock_img = None
        pt_w = font_odds.getbbox(payout_text)[2]
        pt_x = (image_width - pt_w)//2
        # left icon
        if lock_img:
            image.paste(lock_img, (pt_x-28, payout_y), lock_img)
        draw.text((pt_x, payout_y), payout_text, font=font_odds, fill=(255,215,0))
        # right icon
        if lock_img:
            image.paste(lock_img, (pt_x+pt_w+8, payout_y), lock_img)

        # === Footer (move down) ===
        footer_font = font_footer
        sample_text = "Hg"
        bbox_sample = draw.textbbox((0, 0), sample_text, font=footer_font)
        footer_h = bbox_sample[3] - bbox_sample[1]
        f_y = image_height - footer_h - 5  # Move down by 10px compared to previous
        # Use bet_id argument for Bet# display
        # Use the full bet_id string for Bet#
        if bet_id:
            bid = f"Bet #{bet_id}"
        else:
            bid = "Bet #1"
        draw.text((padding, f_y), bid, font=footer_font, fill=(200, 200, 200))
        if timestamp:
            ts = timestamp.strftime("%Y-%m-%d %H:%M UTC")
            bbox_ts = draw.textbbox((0, 0), ts, font=footer_font)
            ts_w = bbox_ts[2] - bbox_ts[0]
            draw.text((image_width - padding - ts_w, f_y), ts, font=footer_font, fill=(200, 200, 200))

        # Save or return
        if output_path:
            image.save(output_path, "PNG")
            return output_path
        else:
            import io
            buf=io.BytesIO()
            image.save(buf, format="PNG")
            buf.seek(0)
            return buf.getvalue()

    def get_next_bet_id(self, db_conn):
        """Get the next Bet# from bets table."""
        try:
            with db_conn.cursor() as cur:
                cur.execute("SELECT MAX(id) FROM bets")
                max_id = cur.fetchone()[0]
                return (max_id or 0) + 1
        except Exception:
            return 1

    async def get_next_bet_id(self):
        """Get the next Bet# from bets table using db_manager (async)."""
        try:
            max_serial = await db_manager.fetchval("SELECT MAX(bet_serial) FROM bets")
            return (max_serial or 0) + 1
        except Exception as e:
            logger.error(f"Failed to fetch next bet_serial: {e}")
            return 1

    # Ensure generate_bet_slip_image is defined as a method of GameLineImageGenerator
    def generate_bet_slip_image(self, league, home_team, away_team, line, odds, units=None, bet_id=None, timestamp=None, selected_team=None, output_path=None, units_display_mode="auto", display_as_risk=None):
        """Generates a game line bet slip image strictly matching requested format."""
        # Use the main implementation from above, not a stub
        from PIL import Image, ImageDraw
        from config.image_settings import (
            BACKGROUND_COLOR,
            DEFAULT_PADDING,
            FOOTER_FONT_SIZE,
            HEADER_FONT_SIZE,
            IMAGE_HEIGHT,
            IMAGE_WIDTH,
            LINE_FONT_SIZE,
            LOGO_SIZE,
            TEAM_FONT_SIZE,
            VS_FONT_SIZE,
            ODDS_FONT_SIZE,
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
        footer_font_size = FOOTER_FONT_SIZE
        font_bold = asset_loader.load_font("Roboto-Bold.ttf", header_font_size)
        font_team = asset_loader.load_font("Roboto-Bold.ttf", team_font_size)
        font_vs = asset_loader.load_font("Roboto-Bold.ttf", vs_font_size)
        font_line = asset_loader.load_font("Roboto-Regular.ttf", line_font_size)
        font_odds = asset_loader.load_font("Roboto-Bold.ttf", odds_font_size)
        font_footer = asset_loader.load_font("Roboto-Regular.ttf", footer_font_size)
        image = Image.new("RGB", (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)
        from config.leagues import LEAGUE_CONFIG
        if units is None:
            units = 1
        league_upper = (league or "").upper()
        league_lower = (league or "").lower()
        # Force NFL to use FOOTBALL as sport_category
        sport_category = "FOOTBALL" if league_upper == "NFL" else LEAGUE_CONFIG.get(league_upper, {}).get("sport", "FOOTBALL").upper()
        logos_root = asset_loader.get_logo_dir()
        logger.debug(f"League logo root directory: {logos_root}")
        logo_path_subfolder = os.path.join(
            logos_root, "leagues", sport_category, league_upper, f"{league_lower}.webp"
        )
        logo_path_direct = os.path.join(
            logos_root, "leagues", sport_category, f"{league_lower}.webp"
        )
        logo_path_upper_direct = os.path.join(
            logos_root, "leagues", sport_category, f"{league_upper}.webp"
        )
        logo_path = None
        if logo_path_subfolder and os.path.exists(logo_path_subfolder):
            logo_path = logo_path_subfolder
        elif logo_path_direct and os.path.exists(logo_path_direct):
            logo_path = logo_path_direct
        elif logo_path_upper_direct and os.path.exists(logo_path_upper_direct):
            logo_path = logo_path_upper_direct
        else:
            league_dir = os.path.join(logos_root, "leagues", sport_category, league_upper)
            logger.debug(f"League logo fallback directory: {league_dir}")
            if os.path.isdir(league_dir):
                webp_files = [fname for fname in os.listdir(league_dir) if fname.lower().endswith(".webp")]
                if webp_files:
                    logo_path_candidate = os.path.join(league_dir, webp_files[0])
                    if logo_path_candidate and os.path.exists(logo_path_candidate):
                        logo_path = logo_path_candidate
            if not logo_path:
                sport_dir = os.path.join(logos_root, "leagues", sport_category)
                logger.debug(f"League logo sport fallback directory: {sport_dir}")
                if os.path.isdir(sport_dir):
                    webp_files = [fname for fname in os.listdir(sport_dir) if fname.lower().endswith(".webp") and league_upper in fname.upper()]
                    if webp_files:
                        logo_path_candidate = os.path.join(sport_dir, webp_files[0])
                        if logo_path_candidate and os.path.exists(logo_path_candidate):
                            logo_path = logo_path_candidate
        logger.debug(f"League logo path: {logo_path}")
        logger.debug(f"Logo exists: {os.path.exists(logo_path) if logo_path else False}")
        header_text = f"{league_upper} GAMELINE BET"
        logo_w, logo_h = 60, 50
        text_w, text_h = font_bold.getbbox(header_text)[2:]
        total_w = logo_w + 12 + text_w
        start_x = (image_width - total_w) // 2
        y = padding
        if logo_path and os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path).convert("RGBA")
                logger.debug(f"Loaded logo image size: {logo_img.size}, mode: {logo_img.mode}")
                # Maintain aspect ratio and center in (logo_w, logo_h)
                orig_w, orig_h = logo_img.size
                scale = min(logo_w / orig_w, logo_h / orig_h)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                logo_resized = logo_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                padded_logo = Image.new("RGBA", (logo_w, logo_h), (0,0,0,0))
                px = (logo_w - new_w) // 2
                py = (logo_h - new_h) // 2
                padded_logo.paste(logo_resized, (px, py), logo_resized)
                image.paste(padded_logo, (start_x, y), padded_logo)
                logger.debug(f"Logo pasted at: {(start_x, y)}")
                text_x = start_x + logo_w + 12
            except Exception as e:
                logger.error(f"Failed to load/paste league logo at {logo_path}: {e}")
                text_x = start_x
        else:
            logger.warning(f"League logo not found at path: {logo_path}")
            text_x = start_x
        text_y = y + (logo_h - text_h) // 2
        draw.text((text_x, text_y), header_text, font=font_bold, fill="white")

        # === Body: Team Logos, VS, Team Names ===
        base_logo_size = logo_size
        lw = int(base_logo_size[0]*1.2)
        lh = int(base_logo_size[1]*1.2)
        quarter_w = image_width//4
        left_x = quarter_w - lw//2
        right_x = 3*quarter_w - lw//2
        logo_y = y + logo_h + 30
        # Left team logo
        home_logo = self._load_team_logo(home_team, league)
        if home_logo:
            hl = home_logo.convert("RGBA").resize((lw,lh), Image.Resampling.LANCZOS)
            image.paste(hl, (left_x, logo_y), hl)
        # Right team logo
        away_logo = self._load_team_logo(away_team, league)
        if away_logo:
            al = away_logo.convert("RGBA").resize((lw,lh), Image.Resampling.LANCZOS)
            image.paste(al, (right_x, logo_y), al)
        # VS text
        vs = "VS"
        vw, vh = font_vs.getbbox(vs)[2:]
        vxx = (image_width - vw)//2
        vyy = logo_y + (lh - vh)//2
        draw.text((vxx, vyy), vs, font=font_vs, fill=(255,215,0))

        # Team names under logos (closer to logos)
        name_y = logo_y + lh - 10  # Move up by 18px compared to previous
        # Ensure selected_team is always defined
        selected_team = selected_team if selected_team is not None else ''
        for name, x_pos in [(home_team, left_x), (away_team, right_x)]:
            if not name: continue
            w = font_team.getbbox(name)[2]
            nx = x_pos + (lw - w)//2
            color = (0,230,0) if name.lower()==(selected_team or '').lower() else "white"
            draw.text((nx, name_y), name, font=font_team, fill=color)

        # === Line (no label), Separator, Odds (move up) ===
        line_y = name_y + 22  # Move up by 10px compared to previous
        line_text = f"{line if line is not None else ''}"
        lw_txt = font_line.getbbox(line_text)[2]
        lx = (image_width - lw_txt)//2
        draw.text((lx, line_y), line_text, font=font_line, fill="white")

        sep_y = line_y + font_line.getbbox(line_text)[3] + 12  # Move up by 8px
        draw.line([(padding, sep_y), (image_width-padding, sep_y)], fill="#aaaaaa", width=1)

        odds_y = sep_y + 12  # Move up by 8px
        odds_text = f"{odds if odds is not None else ''}"
        ow = font_odds.getbbox(odds_text)[2]
        ox = (image_width - ow)//2
        draw.text((ox, odds_y), odds_text, font=font_odds, fill="white")

        # === Payout row below odds ===
        # Calculate payout text and icons
        from bot.utils.bet_utils import calculate_profit_from_odds, determine_risk_win_display_auto, format_units_display
        odds_val = float(odds) if odds is not None else 0.0
        profit = calculate_profit_from_odds(odds_val, units)
        display_as_risk = determine_risk_win_display_auto(odds_val, units, profit)
        unit_label = "Unit" if units == 1 else "Units"
        payout_text = format_units_display(units, display_as_risk, unit_label)
        # lock icon path
        lock_icon_path = os.path.join("StaticFiles", "DBSBM", "static", "lock_icon.webp")
        payout_y = odds_y + font_odds.getbbox(odds_text)[3] + 12
        # load lock icon
        try:
            lock_img = Image.open(lock_icon_path).resize((24,24)).convert("RGBA") if os.path.exists(lock_icon_path) else None
        except Exception:
            lock_img = None
        pt_w = font_odds.getbbox(payout_text)[2]
        pt_x = (image_width - pt_w)//2
        # left icon
        if lock_img:
            image.paste(lock_img, (pt_x-28, payout_y), lock_img)
        draw.text((pt_x, payout_y), payout_text, font=font_odds, fill=(255,215,0))
        # right icon
        if lock_img:
            image.paste(lock_img, (pt_x+pt_w+8, payout_y), lock_img)

        # === Footer (move down) ===
        footer_font = font_footer
        sample_text = "Hg"
        bbox_sample = draw.textbbox((0, 0), sample_text, font=footer_font)
        footer_h = bbox_sample[3] - bbox_sample[1]
        f_y = image_height - footer_h - 5  # Move down by 10px compared to previous
        # Use bet_id argument if provided, else fallback to fetching next bet id
        if bet_id:
            bid = f"Bet #{bet_id}"
        else:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    bet_number = 1
                else:
                    bet_number = loop.run_until_complete(self.get_next_bet_id())
            except Exception:
                bet_number = 1
            bid = f"Bet #{bet_number}"
        draw.text((padding, f_y), bid, font=footer_font, fill=(200, 200, 200))
        if timestamp:
            ts = timestamp.strftime("%Y-%m-%d %H:%M UTC")
            bbox_ts = draw.textbbox((0, 0), ts, font=footer_font)
            ts_w = bbox_ts[2] - bbox_ts[0]
            draw.text((image_width - padding - ts_w, f_y), ts, font=footer_font, fill=(200, 200, 200))

        # Save or return
        if output_path:
            image.save(output_path, "PNG")
            return output_path
        else:
            import io
            buf=io.BytesIO()
            image.save(buf, format="PNG")
            buf.seek(0)
            return buf.getvalue()

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
        # ...existing code...
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
        from PIL import Image

        # Use asset_loader for all logo resolution/fallbacks
        # Special handling for manual entry
        if league.upper() == "MANUAL":
            return asset_loader._load_fallback_logo(getattr(self, "guild_id", None))

        # Special handling for individual sports - use specific logos
        elif league.lower() in ["darts", "tennis", "golf", "f1"] or any(
            sport in league.lower()
            for sport in ["darts", "tennis", "golf", "f1", "formula"]
        ):
            sport = "darts"
            if "tennis" in league.lower():
                sport = "tennis"
            elif "golf" in league.lower():
                sport = "golf"
            elif "f1" in league.lower() or "formula" in league.lower():
                sport = "f1"

            # For individual sports, use [sport]_all.webp or default_{sport}.webp
            sport_all_path = os.path.join(asset_loader.get_logo_dir(), f"{sport}_all.webp")
            default_sport_path = os.path.join(asset_loader.get_logo_dir(), f"default_{sport}.webp")

            if os.path.exists(sport_all_path):
                return Image.open(sport_all_path)
            elif os.path.exists(default_sport_path):
                return Image.open(default_sport_path)
            else:
                return asset_loader.load_team_logo(team_name, league, getattr(self, "guild_id", None))
        else:
            return asset_loader.load_team_logo(team_name, league, getattr(self, "guild_id", None))

    def _load_player_image(self, player_name: str, team_name: str, league: str):
        from utils.asset_loader import asset_loader

        return asset_loader.load_player_image(
            player_name, team_name, league, getattr(self, "guild_id", None)
        )
