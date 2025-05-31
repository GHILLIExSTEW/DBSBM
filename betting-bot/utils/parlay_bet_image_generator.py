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

    def generate_image(self, legs, output_path, total_odds, units, bet_id, bet_datetime):
        """
        Generates a parlay bet slip image.
        Each leg in `legs` should be a dict with keys:
          - 'bet_type' ('game_line' or 'player_prop'), 'league', 'home_team', 'away_team', 'selected_team', 'line', 'player_name' (if player prop)
        """
        from PIL import Image
        import os
        n_legs = len(legs)
        image_width = 800
        leg_height = 110
        header_height = 70
        odds_section_height = 120
        footer_height = 50
        image_height = header_height + n_legs * leg_height + odds_section_height + footer_height
        image = Image.new("RGB", (image_width, image_height), "#232733")
        draw = ImageDraw.Draw(image)

        # Header
        header_text = f"{n_legs}-Leg Parlay Bet"
        draw.text((image_width//2 - draw.textlength(header_text, font=self.font_bold)//2, 24), header_text, font=self.font_bold, fill="#ffffff")

        y = header_height
        for i, leg in enumerate(legs):
            self._draw_leg(draw, image, leg, y, image_width)
            y += leg_height
            # Divider line between legs
            if i < n_legs - 1:
                draw.line([(40, y-10), (image_width-40, y-10)], fill="#444444", width=2)

        # Odds and units
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

        logo_size = (56, 56)
        # Game Line Leg
        if bet_type == 'game_line':
            home_logo = self._load_team_logo(home_team, league)
            away_logo = self._load_team_logo(away_team, league)
            # Paste home logo
            if home_logo:
                image.paste(home_logo.resize(logo_size), (40, y+10), home_logo if home_logo.mode=='RGBA' else None)
            # Paste away logo
            if away_logo:
                image.paste(away_logo.resize(logo_size), (120, y+10), away_logo if away_logo.mode=='RGBA' else None)
            # Team names
            draw.text((190, y+25), home_team, font=self.font_regular, fill="#00ff66" if selected==home_team else "#ffffff")
            draw.text((350, y+25), away_team, font=self.font_regular, fill="#00ff66" if selected==away_team else "#ffffff")
            # Line (right-aligned)
            line_x = image_width - 320
            draw.text((line_x, y+25), line, font=self.font_bold, fill="#ffffff")
        # Player Prop Leg
        elif bet_type == 'player_prop':
            team_logo = self._load_team_logo(home_team, league)
            player_img = self._load_player_image(player_name, home_team, league)
            # Paste team logo
            if team_logo:
                image.paste(team_logo.resize((40, 40)), (40, y+20), team_logo if team_logo.mode=='RGBA' else None)
            # Paste player image
            if player_img:
                image.paste(player_img.resize((40, 40)), (90, y+20), player_img if player_img.mode=='RGBA' else None)
            # Team name and player name (all white)
            draw.text((150, y+25), home_team, font=self.font_regular, fill="#ffffff")
            draw.text((300, y+25), player_name, font=self.font_regular, fill="#ffffff")
            # Line (right-aligned)
            line_x = image_width - 320
            draw.text((line_x, y+25), line, font=self.font_bold, fill="#ffffff")

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
        total_width = risk_width + draw.textlength("🔒🔒", font=self.font_bold)
        start_x = image_width//2 - total_width//2
        draw.text((start_x, y+85), "🔒", font=self.font_bold, fill="#ffcc00")
        draw.text((start_x + draw.textlength("🔒", font=self.font_bold), y+85), payout_text, font=self.font_bold, fill="#ffcc00")
        draw.text((start_x + draw.textlength("🔒", font=self.font_bold) + risk_width, y+85), "🔒", font=self.font_bold, fill="#ffcc00")

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
        normalized_team = normalize_team_name_any_league(team_name).replace(".", "")
        normalized_player = normalize_team_name_any_league(player_name).replace(".", "")
        player_img_path = os.path.join("betting-bot/static/logos/players", sport.lower(), normalized_team, f"{normalized_player}.png")
        if os.path.exists(player_img_path):
            return Image.open(player_img_path).convert("RGBA")
        default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png" if self.guild_id else "betting-bot/static/logos/default_image.png"
        return Image.open(default_path).convert("RGBA")
