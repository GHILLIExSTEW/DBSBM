from PIL import Image, ImageDraw, ImageFont
import os

class ParlayBetImageGenerator:
    """
    A class to generate parlay bet slip images styled like the provided example.
    """

    def __init__(self, font_dir="betting-bot/assets/fonts", guild_id=None):
        self.font_dir = font_dir
        self.guild_id = guild_id
        self.font_regular = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 28)
        self.font_bold = ImageFont.truetype(os.path.join(font_dir, "Roboto-Bold.ttf"), 36)
        self.font_small = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 22)
        self.font_mini = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 18)
        self.font_huge = ImageFont.truetype(os.path.join(font_dir, "Roboto-Bold.ttf"), 48)
        self.font_vs_small = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 21)  # 3/4 of 28

    def generate_image(self, legs, output_path, total_odds, units, bet_id, bet_datetime, finalized=False):
        """
        Generates a parlay bet slip image.
        Each leg in `legs` should be a dict with keys:
          - 'bet_type' ('game_line' or 'player_prop'), 'league', 'home_team', 'away_team', 'selected_team', 'line', 'player_name' (if player prop)
        """
        from PIL import Image
        import os
        n_legs = len(legs)
        image_width = 800
        leg_height = 170
        header_height = 40
        extra_header_padding = 64  # new: extra space after header
        odds_section_height = 120
        footer_height = 50
        image_height = header_height + extra_header_padding + n_legs * leg_height
        if finalized:
            image_height += odds_section_height + footer_height
        image = Image.new("RGB", (image_width, image_height), "#232733")
        draw = ImageDraw.Draw(image)

        # Header
        header_text = f"{n_legs}-Leg Parlay Bet"
        draw.text((image_width//2 - draw.textlength(header_text, font=self.font_bold)//2, 8), header_text, font=self.font_bold, fill="#ffffff")

        y = header_height + extra_header_padding  # add extra space after header
        for i, leg in enumerate(legs):
            self._draw_leg(draw, image, leg, y, image_width)
            # Divider line between legs, move up to just below leg content
            if i < n_legs - 1:
                divider_y = y + leg_height - 60  # move divider up even more
                draw.line([(40, divider_y), (image_width-40, divider_y)], fill="#444444", width=2)
            y += leg_height

        if finalized:
            print(f"[DEBUG] Rendering finalized parlay image: odds={total_odds}, units={units}, bet_id={bet_id}, bet_datetime={bet_datetime}")
            # Odds and units
            if units is None:
                units = 1.00
            self._draw_odds_and_units(draw, image, total_odds, units, y, image_width)
            # Footer (bet id and timestamp)
            footer_padding = 12
            footer_y = image_height - footer_padding - self.font_mini.size
            bet_id_text = f"Bet #{bet_id}" if bet_id else ""
            timestamp_text = bet_datetime if bet_datetime else ""
            # Draw bet ID bottom left
            draw.text((32, footer_y), bet_id_text, font=self.font_mini, fill="#888888")
            # Draw timestamp bottom right
            ts_bbox = self.font_mini.getbbox(timestamp_text)
            ts_width = ts_bbox[2] - ts_bbox[0]
            draw.text((image_width - 32 - ts_width, footer_y), timestamp_text, font=self.font_mini, fill="#888888")

        if output_path:
            image.save(output_path)
            return None
        else:
            import io
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.getvalue()

    def _draw_leg(self, draw, image, leg, y, image_width):
        from PIL import Image
        bet_type = leg.get('bet_type', 'game_line')
        league = leg.get('league', '')
        home_team = leg.get('home_team', '')
        away_team = leg.get('away_team', '')
        selected = leg.get('selected_team', '')
        line = leg.get('line', '')
        player_name = leg.get('player_name', '')

        logo_size = (112, 112)
        team_font = self.font_small
        line_font = self.font_bold
        # Game Line Leg
        if bet_type == 'game_line':
            margin_left = 40
            name_y = y + 80
            # Team name
            home_name_w, home_name_h = team_font.getbbox(home_team)[2:]
            home_name_x = margin_left
            home_name_y = name_y
            home_color = "#00ff66" if selected and selected.lower() == home_team.lower() else "#ffffff"
            draw.text((home_name_x, home_name_y), home_team, font=team_font, fill=home_color)
            # Team logo centered above name
            home_logo = self._load_team_logo(home_team, league)
            if home_logo:
                home_logo = home_logo.convert('RGBA')
                home_logo_resized = home_logo.resize(logo_size)
                logo_x = home_name_x + home_name_w//2 - logo_size[0]//2
                logo_y = name_y - logo_size[1] - 8
                image.paste(home_logo_resized, (logo_x, logo_y), home_logo_resized)
            # VS. 5px after team name
            vs_text = "VS."
            vs_font = self.font_vs_small
            vs_w, vs_h = vs_font.getbbox(vs_text)[2:]
            vs_x = home_name_x + home_name_w + 5
            vs_y = name_y
            draw.text((vs_x, vs_y), vs_text, font=vs_font, fill="#ffffff")
            # Opponent name 5px after VS.
            away_name_w, away_name_h = team_font.getbbox(away_team)[2:]
            away_name_x = vs_x + vs_w + 5
            away_name_y = name_y
            away_color = "#00ff66" if selected and selected.lower() == away_team.lower() else "#ffffff"
            draw.text((away_name_x, away_name_y), away_team, font=team_font, fill=away_color)
            # Opponent logo centered above opponent name
            away_logo = self._load_team_logo(away_team, league)
            if away_logo:
                away_logo = away_logo.convert('RGBA')
                away_logo_resized = away_logo.resize(logo_size)
                logo_x = away_name_x + away_name_w//2 - logo_size[0]//2
                logo_y = name_y - logo_size[1] - 8
                image.paste(away_logo_resized, (logo_x, logo_y), away_logo_resized)
            # Line (right-aligned, word-wrap if too close)
            line_text = line
            line_w, line_h = line_font.getbbox(line_text)[2:]
            line_x = image_width - 40 - line_w
            # Find the rightmost end of the names
            names_end_x = max(home_name_x + home_name_w, away_name_x + away_name_w)
            if line_x < names_end_x + 40:
                # Word-wrap to new line below names
                line_y = name_y + home_name_h + 8
                line_x = image_width - 40 - line_w
            else:
                line_y = y + 25
            draw.text((line_x, line_y), line_text, font=line_font, fill="#ffffff")
        # Player Prop Leg
        elif bet_type == 'player_prop':
            margin_left = 40
            name_y = y + 80
            # Team name
            home_name_w, home_name_h = team_font.getbbox(home_team)[2:]
            home_name_x = margin_left
            home_name_y = name_y
            draw.text((home_name_x, home_name_y), home_team, font=team_font, fill="#ffffff")
            # Team logo centered above name
            team_logo = self._load_team_logo(home_team, league)
            if team_logo:
                team_logo = team_logo.convert('RGBA')
                team_logo_resized = team_logo.resize(logo_size)
                logo_x = home_name_x + home_name_w//2 - logo_size[0]//2
                logo_y = name_y - logo_size[1] - 8
                image.paste(team_logo_resized, (logo_x, logo_y), team_logo_resized)
            # Player name 20px after team name
            player_name_w, player_name_h = team_font.getbbox(player_name)[2:]
            player_name_x = home_name_x + home_name_w + 20
            player_name_y = name_y
            draw.text((player_name_x, player_name_y), player_name, font=team_font, fill="#ffffff")
            # Player photo centered above player name
            player_img = self._load_player_image(player_name, home_team, league)
            if player_img:
                player_img = player_img.convert('RGBA')
                player_img_resized = player_img.resize(logo_size)
                logo_x = player_name_x + player_name_w//2 - logo_size[0]//2
                logo_y = name_y - logo_size[1] - 8
                image.paste(player_img_resized, (logo_x, logo_y), player_img_resized)
            # Line (right-aligned, word-wrap if too close)
            line_text = line
            line_w, line_h = line_font.getbbox(line_text)[2:]
            line_x = image_width - 40 - line_w
            names_end_x = player_name_x + player_name_w
            if line_x < names_end_x + 40:
                # Word-wrap to new line below names
                line_y = name_y + player_name_h + 8
                line_x = image_width - 40 - line_w
            else:
                line_y = y + 25
            draw.text((line_x, line_y), line_text, font=line_font, fill="#ffffff")

    def _draw_odds_and_units(self, draw, image, total_odds, units, y, image_width, units_display_mode='auto', display_as_risk=None):
        odds_text = f"Total Odds: {total_odds}"
        odds_width = draw.textlength(odds_text, font=self.font_huge)
        draw.text((image_width//2 - odds_width//2, y+20), odds_text, font=self.font_huge, fill="#ffffff")
        # Units line (yellow, lock icons)
        # Calculate profit using total_odds and units, but always display the user-selected units
        profit = 0.0
        try:
            odds_val = float(total_odds)
            if odds_val < 0:
                profit = units * (100.0 / abs(odds_val))
            elif odds_val > 0:
                profit = units * (odds_val / 100.0)
            else:
                profit = 0.0
        except Exception:
            profit = 0.0
        unit_label = "Unit" if units <= 1 else "Units"
        if units_display_mode == 'manual' and display_as_risk is not None:
            payout_text = f"To Risk {units:.2f} {unit_label}" if display_as_risk else f"To Win {units:.2f} {unit_label}"
        else:
            if profit < 1.0:
                payout_text = f"To Risk {units:.2f} {unit_label}"
            else:
                payout_text = f"To Win {units:.2f} {unit_label}"
        risk_width = draw.textlength(payout_text, font=self.font_bold)
        # Load lock icon
        from PIL import Image
        import os
        lock_icon_path = "betting-bot/static/lock_icon.png"
        lock_icon = None
        if os.path.exists(lock_icon_path):
            lock_icon = Image.open(lock_icon_path).convert("RGBA").resize((32, 32))
        total_width = risk_width + (lock_icon.width if lock_icon else 0)*2 + 16  # 8px padding each side
        start_x = image_width//2 - total_width//2
        icon_y = y+85
        text_y = y+85 + (lock_icon.height//2 - self.font_bold.size//2) if lock_icon else y+85
        if lock_icon:
            image.paste(lock_icon, (start_x, icon_y), lock_icon)
            draw.text((start_x + lock_icon.width + 8, text_y), payout_text, font=self.font_bold, fill="#ffcc00")
            image.paste(lock_icon, (start_x + lock_icon.width + 8 + risk_width + 8, icon_y), lock_icon)
        else:
            draw.text((start_x, text_y), payout_text, font=self.font_bold, fill="#ffcc00")

    def _draw_footer(self, draw, bet_id, bet_datetime, image_height, image_width):
        draw.text((40, image_height-40), f"Bet #{bet_id}", font=self.font_mini, fill="#aaaaaa")
        draw.text((image_width-260, image_height-40), bet_datetime, font=self.font_mini, fill="#aaaaaa")

    def _load_team_logo(self, team_name: str, league: str):
        import os
        from PIL import Image
        from config.team_mappings import normalize_team_name
        from config.asset_paths import get_sport_category_for_path
        from data.game_utils import normalize_team_name_any_league
        sport = get_sport_category_for_path(league.upper())
        if not sport:
            default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if self.guild_id else "betting-bot/static/logos/default_image.png"
            return Image.open(default_path).convert("RGBA")
        normalized = normalize_team_name_any_league(team_name).replace(".", "")
        fname = f"{normalize_team_name(normalized)}.png"
        logo_path = os.path.join("betting-bot/static/logos/teams", sport, league.upper(), fname)
        if os.path.exists(logo_path):
            return Image.open(logo_path).convert("RGBA")
        # Always use the correct default image location
        default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if self.guild_id else "betting-bot/static/logos/default_image.png"
        return Image.open(default_path).convert("RGBA")

    def _load_player_image(self, player_name: str, team_name: str, league: str):
        import os
        from PIL import Image
        from config.asset_paths import get_sport_category_for_path
        from data.game_utils import normalize_team_name_any_league
        sport = get_sport_category_for_path(league.upper())
        if not sport:
            default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if self.guild_id else "betting-bot/static/logos/default_image.png"
            return Image.open(default_path).convert("RGBA")
        normalized_team = normalize_team_name_any_league(team_name).lower().replace(" ", "_")
        normalized_player = normalize_team_name_any_league(player_name).lower().replace(" ", "_")
        sport_dir = sport.lower().replace(" ", "_")
        player_img_path = os.path.join(
            "betting-bot/static/logos/players",
            sport_dir,
            normalized_team,
            f"{normalized_player}.png"
        )
        if os.path.exists(player_img_path):
            return Image.open(player_img_path).convert("RGBA")
        # Always use the correct default image location
        default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if self.guild_id else "betting-bot/static/logos/default_image.png"
        return Image.open(default_path).convert("RGBA")
