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

    # Load and paste team logo
    team_logo = Image.open(team_logo_path).resize((100, 100))
    image.paste(team_logo, (50, 100))

    # Load and paste player picture
    player_picture = Image.open(player_picture_path).resize((100, 100))
    image.paste(player_picture, (650, 100))

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
    def __init__(self, fonts=None, padding=0):
        """Initialize the GameLineImageGenerator with optional fonts and padding."""
        self.fonts = fonts
        self.padding = padding

    def generate_bet_slip_image(self, team1_name, team1_logo_path, team2_name, team2_logo_path, line, units, output_path, league, bet_id=None, odds=None, selected_team=None):
        """Generates a game line bet slip image."""
        from PIL import Image, ImageDraw, ImageFont
        from datetime import datetime, timezone
        import os

        # --- Reference values from image_generator copy.py ---
        image_width, image_height = 600, 400
        bg_color = "#232733"
        padding = 24
        logo_size = (120, 120)
        header_font_size = 36
        team_font_size = 24
        vs_font_size = 28
        line_font_size = 24
        odds_font_size = 28
        risk_font_size = 24
        footer_font_size = 18
        lock_icon_path = "betting-bot/static/lock_icon.png"

        # --- Fonts ---
        font_dir = "betting-bot/assets/fonts"
        font_bold = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", header_font_size)
        font_bold_team = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", team_font_size)
        font_vs = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", vs_font_size)
        font_line = ImageFont.truetype(f"{font_dir}/Roboto-Regular.ttf", line_font_size)
        font_odds = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", odds_font_size)
        font_risk = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", risk_font_size)
        font_footer = ImageFont.truetype(f"{font_dir}/Roboto-Regular.ttf", footer_font_size)

        # --- Create image ---
        image = Image.new("RGB", (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)

        # --- Header (centered block: logo + text, dynamic league) ---
        def get_sport_category(league):
            mapping = {
                "NBA": "BASKETBALL", "NCAAB": "BASKETBALL", "WNBA": "BASKETBALL", "EUROLEAGUE": "BASKETBALL", "CBA": "BASKETBALL",
                "NFL": "FOOTBALL", "NCAAF": "FOOTBALL", "CFL": "FOOTBALL", "XFL": "FOOTBALL",
                "MLB": "BASEBALL", "NCAAB_BASEBALL": "BASEBALL", "NPB": "BASEBALL", "KBO": "BASEBALL",
                "NHL": "HOCKEY", "KHL": "HOCKEY", "SHL": "HOCKEY",
                "MLS": "SOCCER", "EPL": "SOCCER", "LA_LIGA": "SOCCER", "SERIE_A": "SOCCER", "BUNDESLIGA": "SOCCER",
                "LIGUE_1": "SOCCER", "UEFA_CL": "SOCCER", "COPA_LIBERTADORES": "SOCCER", "A_LEAGUE": "SOCCER", "J_LEAGUE": "SOCCER",
                "ATP": "TENNIS", "WTA": "TENNIS", "ITF": "TENNIS", "GRAND_SLAM": "TENNIS",
                "UFC": "MMA", "BELLATOR": "MMA", "ONE_CHAMPIONSHIP": "MMA", "PFL": "MMA",
                "PGA": "GOLF", "LPGA": "GOLF", "EUROPEAN_TOUR": "GOLF", "MASTERS": "GOLF",
                "BOXING": "BOXING", "CRICKET": "CRICKET", "IPL": "CRICKET", "BBL": "CRICKET", "TEST_CRICKET": "CRICKET",
                "RUGBY_UNION": "RUGBY", "SUPER_RUGBY": "RUGBY", "SIX_NATIONS": "RUGBY",
                "RUGBY_LEAGUE": "RUGBY", "NRL": "RUGBY", "SUPER_LEAGUE": "RUGBY",
                "F1": "MOTORSPORTS", "NASCAR": "MOTORSPORTS", "INDYCAR": "MOTORSPORTS", "MOTOGP": "MOTORSPORTS",
                "DARTS": "DARTS", "PDC": "DARTS", "VOLLEYBALL": "VOLLEYBALL", "FIVB": "VOLLEYBALL",
                "TABLE_TENNIS": "TABLE_TENNIS", "ITTF": "TABLE_TENNIS", "CYCLING": "CYCLING",
                "TOUR_DE_FRANCE": "CYCLING", "GIRO_D_ITALIA": "CYCLING", "VUELTA_A_ESPANA": "CYCLING",
                "ESPORTS_CSGO": "ESPORTS", "ESPORTS_LOL": "ESPORTS", "ESPORTS_DOTA2": "ESPORTS",
                "ESPORTS_OVERWATCH": "ESPORTS", "ESPORTS_FIFA": "ESPORTS",
                "AUSSIE_RULES": "AUSTRALIAN_FOOTBALL", "AFL": "AUSTRALIAN_FOOTBALL",
                "HANDBALL": "HANDBALL", "EHF_CL": "HANDBALL", "SNOOKER": "SNOOKER",
                "WORLD_CHAMPIONSHIP_SNOOKER": "SNOOKER", "BADMINTON": "BADMINTON", "BWF": "BADMINTON",
                "LACROSSE": "LACROSSE", "NLL": "LACROSSE", "FIELD_HOCKEY": "FIELD_HOCKEY", "FIH_PRO_LEAGUE": "FIELD_HOCKEY"
            }
            return mapping.get(league.upper(), "OTHER_SPORTS")

        logo_display_size = (45, 45)
        league_upper = league.upper()
        league_lower = league.lower()
        sport_category = get_sport_category(league_upper)
        league_logo_path = f"betting-bot/static/logos/leagues/{sport_category}/{league_upper}/{league_lower}.png"
        league_logo = Image.open(league_logo_path).convert("RGBA").resize(logo_display_size)
        header_text = f"{league_upper} - Game Line"
        header_w, header_h = font_bold.getbbox(header_text)[2:]
        block_h = max(logo_display_size[1], header_h)
        block_w = logo_display_size[0] + 15 + header_w if league_logo else header_w
        block_x = (image_width - block_w) // 2
        block_y = 25
        # Vertically center logo and text in block
        if league_logo:
            logo_y = block_y + (block_h - logo_display_size[1]) // 2
            text_y = block_y + (block_h - header_h) // 2
            image.paste(league_logo, (block_x, logo_y), league_logo)
            text_x = block_x + logo_display_size[0] + 15
        else:
            text_x = block_x
            text_y = block_y
        draw.text((text_x, text_y), header_text, font=font_bold, fill="white", anchor="lt")

        # --- Teams Section ---
        y_base = 85
        section_width = image_width // 2 - padding * 1.5
        home_section_center_x = padding + section_width // 2
        away_section_center_x = image_width - padding - section_width // 2
        center_x = image_width // 2

        # Home logo
        try:
            home_logo = Image.open(team1_logo_path).resize(logo_size)
            home_logo_x = int(home_section_center_x - logo_size[0] // 2)
            image.paste(home_logo, (home_logo_x, y_base), home_logo if home_logo.mode == 'RGBA' else None)
        except Exception:
            pass
        # Away logo
        try:
            away_logo = Image.open(team2_logo_path).resize(logo_size)
            away_logo_x = int(away_section_center_x - logo_size[0] // 2)
            image.paste(away_logo, (away_logo_x, y_base), away_logo if away_logo.mode == 'RGBA' else None)
        except Exception:
            pass

        # VS
        vs_text = "VS"
        vs_w, vs_h = font_vs.getbbox(vs_text)[2:]
        vs_x = center_x - vs_w // 2
        vs_y = y_base + logo_size[1] // 2 - vs_h // 2
        draw.text((vs_x, vs_y), vs_text, font=font_vs, fill="#FFD700", anchor="lt")

        # Team names
        home_color = "#00FF00" if selected_team and selected_team.lower() == team1_name.lower() else "white"
        away_color = "#00FF00" if selected_team and selected_team.lower() == team2_name.lower() else "white"
        home_name_w, _ = font_bold_team.getbbox(team1_name)[2:]
        away_name_w, _ = font_bold_team.getbbox(team2_name)[2:]
        home_name_x = home_section_center_x - home_name_w // 2
        away_name_x = away_section_center_x - away_name_w // 2
        team_name_y = y_base + logo_size[1] + 8
        draw.text((home_name_x, team_name_y), team1_name, font=font_bold_team, fill=home_color, anchor="lt")
        draw.text((away_name_x, team_name_y), team2_name, font=font_bold_team, fill=away_color, anchor="lt")

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
        odds_w, odds_h = font_odds.getbbox(odds_text)[2:]
        odds_y = sep_above_odds_y + 24
        draw.text(((image_width - odds_w) // 2, odds_y), odds_text, font=font_odds, fill="white", anchor="lt")

        # To Risk/To Win row
        if odds_val < 0:
            risk_label = "To Risk"
            amount = units
        else:
            risk_label = "To Win"
            amount = units * abs(odds_val) / 100 if odds_val > 0 else units
        unit_label = "Unit" if round(amount, 2) == 1 else "Units"
        risk_text = f"{risk_label} {amount:.2f} {unit_label}"
        risk_w, risk_h = font_risk.getbbox(risk_text)[2:]
        # Lock icon PNG
        try:
            lock_img = Image.open(lock_icon_path).convert("RGBA")
            lock_img = lock_img.resize((risk_h, risk_h))
        except Exception:
            lock_img = None
        lock_w = risk_h
        total_w = lock_w + 8 + risk_w + 8 + lock_w
        risk_y = odds_y + odds_h + 24
        start_x = (image_width - total_w) // 2
        # Left lock
        if lock_img:
            image.paste(lock_img, (int(start_x), int(risk_y)), lock_img)
        # Risk text
        draw.text((start_x + lock_w + 8, risk_y), risk_text, font=font_risk, fill="#FFD700", anchor="lt")
        # Right lock
        if lock_img:
            image.paste(lock_img, (int(start_x + lock_w + 8 + risk_w + 8), int(risk_y)), lock_img)

        # Separator line below units text (above footer)
        sep_gap = 36  # Increased from 24 to 36
        sep_below_units_y = risk_y + risk_h + sep_gap
        draw.line([(padding, sep_below_units_y), (image_width - padding, sep_below_units_y)], fill="#aaaaaa", width=1)

        # Footer (flush with bottom edge)
        footer_padding = 8  # Increased from 4 to 8
        ascent, descent = font_footer.getmetrics()
        # The baseline of the text should be image_height - padding
        footer_y = image_height - footer_padding - descent

        if bet_id:
            bet_id_text = f"Bet #{bet_id}"
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            draw.text((padding, footer_y), bet_id_text, font=font_footer, fill="#aaaaaa", anchor="ls")
            draw.text((image_width - padding, footer_y), timestamp, font=font_footer, fill="#aaaaaa", anchor="rs")

        # Save or return
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