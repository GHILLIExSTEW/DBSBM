def generate_player_prop_bet_image(player_name, player_picture_path, team_name, team_logo_path, line, units, output_path):
    """Generates a player prop bet slip image."""
    from PIL import Image, ImageDraw, ImageFont

    # Load fonts
    font_regular = ImageFont.truetype("betting-bot/assets/fonts/Roboto-Regular.ttf", 24)
    font_bold = ImageFont.truetype("betting-bot/assets/fonts/Roboto-Bold.ttf", 32)

    # Create a blank image
    image_width, image_height = 800, 400
    image = Image.new("RGB", (image_width, image_height), "black")
    draw = ImageDraw.Draw(image)

    # Draw team name
    team_name_width, team_name_height = draw.textsize(team_name, font=font_bold)
    draw.text(((image_width - team_name_width) / 2, 20), team_name, font=font_bold, fill="white")


    # For single player props: if sport is darts/tennis/golf/etc, only post the player image once (left), right image is always default_{sport}.png
    import os
    # Try to infer sport from team_name or team_logo_path if possible, fallback to 'darts'
    sport = 'darts'
    if team_logo_path and 'darts' in team_logo_path.lower():
        sport = 'darts'
    elif team_logo_path and 'tennis' in team_logo_path.lower():
        sport = 'tennis'
    elif team_logo_path and 'golf' in team_logo_path.lower():
        sport = 'golf'
    elif team_logo_path and 'mma' in team_logo_path.lower():
        sport = 'mma'
    elif team_logo_path and 'f1' in team_logo_path.lower():
        sport = 'f1'
    # You can add more sports as needed
    player_img = Image.open(player_picture_path).resize((100, 100))
    image.paste(player_img, (50, 100))
    default_sport_path = f"betting-bot/static/logos/default_{sport}.png"
    if os.path.exists(default_sport_path):
        right_img = Image.open(default_sport_path).resize((100, 100))
    else:
        # fallback to default_image.png if not found
        right_img = Image.open("betting-bot/static/logos/default_image.png").resize((100, 100))
    image.paste(right_img, (650, 100))

    # Draw player name
    player_name_width, player_name_height = draw.textsize(player_name, font=font_bold)
    draw.text(((image_width - player_name_width) / 2, 220), player_name, font=font_bold, fill="white")

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

    def generate_bet_slip_image(self, league, home_team, away_team, line, odds, units, bet_id=None, timestamp=None, selected_team=None, output_path=None, units_display_mode='auto', display_as_risk=None):
        """Generates a game line bet slip image."""
        from PIL import Image, ImageDraw, ImageFont
        from datetime import datetime, timezone
        import os
        from config.asset_paths import get_sport_category_for_path
        from config.image_settings import (
            IMAGE_WIDTH, IMAGE_HEIGHT, BACKGROUND_COLOR, DEFAULT_PADDING, LOGO_SIZE,
            HEADER_FONT_SIZE, TEAM_FONT_SIZE, VS_FONT_SIZE, LINE_FONT_SIZE, 
            ODDS_FONT_SIZE, RISK_FONT_SIZE, FOOTER_FONT_SIZE, TEXT_COLOR, ODDS_COLOR
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
        lock_icon_path = "betting-bot/static/lock_icon.png"

        font_dir = "betting-bot/assets/fonts"
        font_bold = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", header_font_size)
        font_bold_team = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", team_font_size)
        font_vs = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", vs_font_size)
        font_line = ImageFont.truetype(f"{font_dir}/Roboto-Regular.ttf", line_font_size)
        font_odds = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", odds_font_size)
        font_risk = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", risk_font_size)
        font_footer = ImageFont.truetype(f"{font_dir}/Roboto-Regular.ttf", footer_font_size)

        image = Image.new("RGB", (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)

        # Header (league logo + text)
        logo_display_size = (45, 45)
        league_upper = league.upper()
        league_lower = league.lower()
        sport_category = get_sport_category_for_path(league_upper)
        league_logo_path = f"betting-bot/static/logos/leagues/{sport_category}/{league_upper}/{league_lower}.png"
        try:
            league_logo = Image.open(league_logo_path).convert("RGBA").resize(logo_display_size)
        except Exception:
            league_logo = None
        header_text = f"{league_upper} - Game Line"
        header_w, header_h = font_bold.getbbox(header_text)[2:]
        block_h = max(logo_display_size[1], header_h)
        block_w = logo_display_size[0] + 15 + header_w if league_logo else header_w
        block_x = (image_width - block_w) // 2
        block_y = 25
        if league_logo:
            logo_y = block_y + (block_h - logo_display_size[1]) // 2
            text_y = block_y + (block_h - header_h) // 2
            image.paste(league_logo, (block_x, logo_y), league_logo)
            text_x = block_x + logo_display_size[0] + 15
        else:
            text_x = block_x
            text_y = block_y
        draw.text((text_x, text_y), header_text, font=font_bold, fill="white", anchor="lt")

        # Teams Section
        y_base = 85
        section_width = image_width // 2 - padding * 1.5
        home_section_center_x = padding + section_width // 2
        away_section_center_x = image_width - padding - section_width // 2
        center_x = image_width // 2

        # Home logo
        home_logo = self._load_team_logo(home_team, league)
        if home_logo:
            home_logo_resized = home_logo.convert('RGBA').resize(logo_size)
            home_logo_x = int(home_section_center_x - logo_size[0] // 2)
            image.paste(home_logo_resized, (home_logo_x, y_base), home_logo_resized)
        # Away logo
        away_logo = self._load_team_logo(away_team, league)
        if away_logo:
            away_logo_resized = away_logo.convert('RGBA').resize(logo_size)
            away_logo_x = int(away_section_center_x - logo_size[0] // 2)
            image.paste(away_logo_resized, (away_logo_x, y_base), away_logo_resized)

        # VS
        vs_text = "VS"
        vs_w, vs_h = font_vs.getbbox(vs_text)[2:]
        vs_x = center_x - vs_w // 2
        vs_y = y_base + logo_size[1] // 2 - vs_h // 2
        draw.text((vs_x, vs_y), vs_text, font=font_vs, fill="#FFD700", anchor="lt")

        # Team names
        home_color = "#00FF00" if selected_team and selected_team.lower() == home_team.lower() else "white"
        away_color = "#00FF00" if selected_team and selected_team.lower() == away_team.lower() else "white"
        home_name_w, _ = font_bold_team.getbbox(home_team)[2:]
        away_name_w, _ = font_bold_team.getbbox(away_team)[2:]
        home_name_x = home_section_center_x - home_name_w // 2
        away_name_x = away_section_center_x - away_name_w // 2
        team_name_y = y_base + logo_size[1] + 8
        draw.text((home_name_x, team_name_y), home_team, font=font_bold_team, fill=home_color, anchor="lt")
        draw.text((away_name_x, team_name_y), away_team, font=font_bold_team, fill=away_color, anchor="lt")

        # ML line
        line_text = str(line)
        line_w, line_h = font_line.getbbox(line_text)[2:]
        line_y = team_name_y + 32
        draw.text(((image_width - line_w) // 2, line_y), line_text, font=font_line, fill="white", anchor="lt")

        # Separator line above odds
        sep_above_odds_y = line_y + line_h + 18  # 18px below the ML line
        draw.line([(padding, sep_above_odds_y), (image_width - padding, sep_above_odds_y)], fill="#aaaaaa", width=1)

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
        draw.text(((image_width - odds_w) // 2, odds_y), odds_text, font=font_odds, fill="white", anchor="lt")

        # Risk/Units (yellow, lock icons)
        from utils.bet_utils import determine_risk_win_display_auto, calculate_profit_from_odds, format_units_display
        
        profit = calculate_profit_from_odds(odds_val, units)
        unit_label = "Unit" if units <= 1 else "Units"
        
        if units_display_mode == 'manual' and display_as_risk is not None:
            payout_text = format_units_display(units, display_as_risk, unit_label)
        else:
            # Auto mode: intelligent determination based on odds and profit ratio
            if units_display_mode == 'auto':
                display_as_risk_auto = determine_risk_win_display_auto(odds_val, units, profit)
                payout_text = format_units_display(units, display_as_risk_auto, unit_label)
            else:
                # Fallback to old logic for backward compatibility
                if profit < 1.0:
                    payout_text = f"To Risk {units:.2f} {unit_label}"
                else:
                    payout_text = f"To Win {units:.2f} {unit_label}"
        payout_bbox = font_risk.getbbox(payout_text)
        payout_w, payout_h = payout_bbox[2] - payout_bbox[0], payout_bbox[3] - payout_bbox[1]
        payout_y = odds_y + odds_h + 8
        lock_icon = None
        try:
            lock_icon = Image.open(lock_icon_path).resize((24, 24))
        except Exception:
            lock_icon = None
        if lock_icon:
            image.paste(lock_icon, ((image_width - payout_w) // 2 - 28, payout_y), lock_icon)
            draw.text(((image_width - payout_w) // 2, payout_y), payout_text, font=font_risk, fill="#FFD700", anchor="lt")
            image.paste(lock_icon, ((image_width - payout_w) // 2 + payout_w + 8, payout_y), lock_icon)
        else:
            draw.text(((image_width - payout_w) // 2, payout_y), payout_text, font=font_risk, fill="#FFD700", anchor="lt")

        # Footer (bet id and timestamp)
        footer_padding = 12
        footer_y = image_height - footer_padding - font_footer.size
        bet_id_text = f"Bet #{bet_id}" if bet_id else ""
        timestamp_text = timestamp.strftime("%Y-%m-%d %H:%M UTC") if timestamp else ""
        # Draw bet ID bottom left
        draw.text((padding, footer_y), bet_id_text, font=font_footer, fill="#888888")
        # Draw timestamp bottom right
        ts_bbox = font_footer.getbbox(timestamp_text)
        ts_width = ts_bbox[2] - ts_bbox[0]
        draw.text((image_width - padding - ts_width, footer_y), timestamp_text, font=font_footer, fill="#888888")

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

    def draw_teams_section(self, img, draw, image_width, home_team, away_team, home_logo, away_logo, selected_team=None):
        """Draws the teams section for game line bets."""
        from PIL import Image
        
        y_base = 85
        logo_size = (120, 120)
        text_y_offset = logo_size[1] + 8
        team_name_font_large = self.fonts['font_b_24']
        team_name_font_small = self.fonts.get('font_b_18', self.fonts['font_b_24'])
        vs_font = self.fonts['font_b_28']
        green_color = '#00FF00'  # Bright green
        white_color = 'white'
        vs_color = '#FFD700'  # Gold color for VS
        
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
                home_logo_resized = home_logo.resize(logo_size, Image.Resampling.LANCZOS)
                home_logo_x = home_section_center_x - logo_size[0] // 2
                if home_logo_resized.mode == 'RGBA':
                    img.paste(home_logo_resized, (int(home_logo_x), int(y_base)), home_logo_resized)
                else:
                    img.paste(home_logo_resized, (int(home_logo_x), int(y_base)))
            except Exception as e:
                pass  # Silently handle logo errors
        
        # Choose font size based on available width
        def _pick_font(name:str, max_width:int):
            bbox = team_name_font_large.getbbox(name)
            w = bbox[2]-bbox[0]
            if w <= max_width:
                return team_name_font_large, w
            bbox_s = team_name_font_small.getbbox(name)
            return team_name_font_small, bbox_s[2]-bbox_s[0]

        # Home name
        font_home, home_name_w = _pick_font(home_team, section_width - 10)
        home_name_x = home_section_center_x - home_name_w // 2
        home_color = green_color if selected_team and selected_team.lower() == home_team.lower() else white_color
        draw.text((home_name_x, y_base + text_y_offset), home_team, font=font_home, fill=home_color, anchor="lt")
        
        # Draw away team section
        if away_logo:
            try:
                away_logo_resized = away_logo.resize(logo_size, Image.Resampling.LANCZOS)
                away_logo_x = away_section_center_x - logo_size[0] // 2
                if away_logo_resized.mode == 'RGBA':
                    img.paste(away_logo_resized, (int(away_logo_x), int(y_base)), away_logo_resized)
                else:
                    img.paste(away_logo_resized, (int(away_logo_x), int(y_base)))
            except Exception as e:
                pass  # Silently handle logo errors
        
        # Away name
        font_away, away_name_w = _pick_font(away_team, section_width - 10)
        away_name_x = away_section_center_x - away_name_w // 2
        away_color = green_color if selected_team and selected_team.lower() == away_team.lower() else white_color
        draw.text((away_name_x, y_base + text_y_offset), away_team, font=font_away, fill=away_color, anchor="lt")
        
        return y_base + text_y_offset + 50  # Return y position for next section

    def _load_team_logo(self, team_name: str, league: str):
        import os
        from PIL import Image
        from config.asset_paths import get_sport_category_for_path
        from data.game_utils import normalize_team_name_any_league
        import logging
        import difflib
        logger = logging.getLogger(__name__)
        # Helper to get sport_type from LEAGUE_CONFIG
        def get_league_sport_type(league):
            try:
                from config.leagues import LEAGUE_CONFIG
                return LEAGUE_CONFIG.get(league.upper(), {}).get("sport_type", "Unknown")
            except Exception:
                return "Unknown"

        sport_type = get_league_sport_type(league)
        sport = get_sport_category_for_path(league.upper())
        if not sport:
            default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if self.guild_id else "betting-bot/static/logos/default_image.png"
            logger.warning(f"[LOGO] No sport category for league '{league}'. Using fallback: {default_path}")
            return Image.open(default_path).convert("RGBA")

        # If this is an individual player league, use the player logo directory
        if sport_type == "Individual Player":
            # Use the player name as the logo (for game line, team_name is actually the player)
            normalized_player = normalize_team_name_any_league(team_name).replace(".", "").replace(" ", "_").lower()
            player_logo_path = os.path.join("betting-bot/static/logos/players", sport, league.upper(), f"{normalized_player}.png")
            if os.path.exists(player_logo_path):
                logger.info(f"[LOGO] Found player logo for '{team_name}' at: {player_logo_path}")
                return Image.open(player_logo_path).convert("RGBA")
            # Fuzzy match if exact not found
            player_logo_dir = os.path.join("betting-bot/static/logos/players", sport, league.upper())
            if os.path.exists(player_logo_dir):
                candidates = [f for f in os.listdir(player_logo_dir) if f.endswith('.png')]
                candidate_names = [os.path.splitext(f)[0] for f in candidates]
                matches = difflib.get_close_matches(normalized_player, candidate_names, n=1, cutoff=0.75)
                if matches:
                    match_file = matches[0] + '.png'
                    match_path = os.path.join(player_logo_dir, match_file)
                    logger.info(f"[LOGO] Found fuzzy player logo for '{team_name}' -> '{matches[0]}' at: {match_path}")
                    return Image.open(match_path).convert("RGBA")
            # Fallback to default
            default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if self.guild_id else "betting-bot/static/logos/default_image.png"
            logger.warning(f"[LOGO] Player logo not found for '{team_name}' (tried: {player_logo_path}). Using fallback: {default_path}")
            return Image.open(default_path).convert("RGBA")

        # Otherwise, use the team logo logic as before
        # First normalize the team name using league dictionaries
        try:
            league_lower = league.lower()
            if league_lower == 'mlb':
                from utils.league_dictionaries.baseball import TEAM_FULL_NAMES as league_dict
            elif league_lower == 'nba':
                from utils.league_dictionaries.basketball import TEAM_NAMES as league_dict
            elif league_lower == 'nfl':
                from utils.league_dictionaries.football import TEAM_NAMES as league_dict
            elif league_lower == 'nhl':
                from utils.league_dictionaries.hockey import TEAM_NAMES as league_dict
            else:
                league_dict = {}
            normalized_team = None
            team_name_lower = team_name.lower()
            if team_name_lower in league_dict:
                normalized_team = league_dict[team_name_lower]
            else:
                matches = difflib.get_close_matches(team_name_lower, league_dict.keys(), n=1, cutoff=0.75)
                if matches:
                    normalized_team = league_dict[matches[0]]
                    logger.info(f"[LOGO] Fuzzy matched team name '{team_name}' to '{normalized_team}' using league dictionary")
        except Exception as e:
            logger.warning(f"[LOGO] Error using league dictionary for '{team_name}': {e}")
            normalized_team = None
        if not normalized_team:
            normalized_team = team_name
        normalized = normalized_team.replace(".", "").replace(" ", "_").lower()
        fname = f"{normalized}.png"
        logo_path = os.path.join("betting-bot/static/logos/teams", sport, league.upper(), fname)
        if os.path.exists(logo_path):
            logger.info(f"[LOGO] Found exact logo match for '{team_name}' -> '{normalized_team}' at: {logo_path}")
            return Image.open(logo_path).convert("RGBA")
        logo_dir = os.path.join("betting-bot/static/logos/teams", sport, league.upper())
        if os.path.exists(logo_dir):
            candidates = [f for f in os.listdir(logo_dir) if f.endswith('.png')]
            candidate_names = [os.path.splitext(f)[0] for f in candidates]
            matches = difflib.get_close_matches(normalized, candidate_names, n=1, cutoff=0.75)
            if matches:
                match_file = matches[0] + '.png'
                match_path = os.path.join(logo_dir, match_file)
                logger.info(f"[LOGO] Found fuzzy match for '{team_name}' -> '{matches[0]}' at: {match_path}")
                return Image.open(match_path).convert("RGBA")
        default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if self.guild_id else "betting-bot/static/logos/default_image.png"
        logger.warning(f"[LOGO] Logo not found for '{team_name}' (tried: {logo_path}). Using fallback: {default_path}")
        return Image.open(default_path).convert("RGBA")

    def _load_player_image(self, player_name: str, team_name: str, league: str):
        import os
        from PIL import Image
        import difflib
        from config.asset_paths import get_sport_category_for_path
        from data.game_utils import normalize_team_name_any_league
        sport = get_sport_category_for_path(league.upper())
        if not sport:
            default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if getattr(self, 'guild_id', None) else "betting-bot/static/logos/default_image.png"
            return Image.open(default_path).convert("RGBA"), player_name
        normalized_team = normalize_team_name_any_league(team_name).replace(".", "").replace(" ", "_").lower()
        normalized_player = normalize_team_name_any_league(player_name).replace(".", "").replace(" ", "_").lower()
        player_dir = os.path.join("betting-bot/static/logos/players", sport.lower(), normalized_team)
        player_img_path = os.path.join(player_dir, f"{normalized_player}.png")
        if os.path.exists(player_img_path):
            return Image.open(player_img_path).convert("RGBA"), player_name
        # Fuzzy match if exact not found
        if os.path.exists(player_dir):
            candidates = [f for f in os.listdir(player_dir) if f.endswith('.png')]
            candidate_names = [os.path.splitext(f)[0] for f in candidates]
            matches = difflib.get_close_matches(normalized_player, candidate_names, n=1, cutoff=0.6)
            if matches:
                match_file = matches[0] + '.png'
                match_path = os.path.join(player_dir, match_file)
                display_name = matches[0].replace('_', ' ').title()
                return Image.open(match_path).convert("RGBA"), display_name
        default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if getattr(self, 'guild_id', None) else "betting-bot/static/logos/default_image.png"
        return Image.open(default_path).convert("RGBA"), player_name