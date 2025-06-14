from PIL import Image, ImageDraw, ImageFont
import os
import difflib
import logging

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
        # Defensive: ensure legs is a list, not None
        if legs is None:
            logging.error("[ParlayBetImageGenerator] 'legs' argument is None. Returning blank image.")
            legs = []
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
        image = Image.new("RGB", (int(image_width), int(image_height)), "#232733")
        draw = ImageDraw.Draw(image)

        # Header
        header_text = f"{n_legs}-Leg Parlay Bet"
        draw.text((int(image_width//2 - draw.textlength(header_text, font=self.font_bold)//2), 8), header_text, font=self.font_bold, fill="#ffffff")

        y = int(header_height + extra_header_padding)  # add extra space after header
        for i, leg in enumerate(legs):
            self._draw_leg(draw, image, leg, int(y), int(image_width))
            # Divider line between legs, move up to just below leg content
            if i < n_legs - 1:
                divider_y = int(y + leg_height - 60)  # move divider up even more
                draw.line([(40, divider_y), (int(image_width)-40, divider_y)], fill="#444444", width=2)
            y += leg_height

        if finalized:
            print(f"[DEBUG] Rendering finalized parlay image: odds={total_odds}, units={units}, bet_id={bet_id}, bet_datetime={bet_datetime}")
            # Odds and units
            if units is None:
                units = 1.00
            self._draw_odds_and_units(draw, image, total_odds, units, int(y), int(image_width))
            # Footer (bet id and timestamp)
            footer_padding = 12
            footer_y = int(image_height - footer_padding - self.font_mini.size)
            bet_id_text = f"Bet #{bet_id}" if bet_id else ""
            timestamp_text = bet_datetime if bet_datetime else ""
            # Draw bet ID bottom left
            draw.text((32, footer_y), bet_id_text, font=self.font_mini, fill="#888888")
            # Draw timestamp bottom right
            ts_bbox = self.font_mini.getbbox(timestamp_text)
            ts_width = ts_bbox[2] - ts_bbox[0]
            draw.text((int(image_width - 32 - ts_width), footer_y), timestamp_text, font=self.font_mini, fill="#888888")

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
        from PIL import Image, ImageDraw
        bet_type = str(leg.get('bet_type', 'game_line') or '')
        league = str(leg.get('league', '') or '')
        home_team = str(leg.get('home_team', '') or '')
        away_team = str(leg.get('away_team', '') or '')
        selected = str(leg.get('selected_team', '') or '')
        line = str(leg.get('line', '') or '')
        player_name = str(leg.get('player_name', '') or '')
        odds = str(leg.get('odds', ''))

        logo_size = (64, 64)
        team_font = self.font_small
        line_font = self.font_bold
        odds_font = self.font_bold
        badge_color = "#222b3a"
        badge_text_color = "#00d8ff"
        card_radius = 28
        card_margin_x = 24
        card_margin_y = 10
        card_height = 150
        card_y = y + card_margin_y
        card_x0 = card_margin_x
        card_x1 = image_width - card_margin_x
        card_y1 = card_y + card_height
        # Draw rounded rectangle background for the leg
        draw.rounded_rectangle([(card_x0, card_y), (card_x1, card_y1)], radius=card_radius, fill="#181c24")

        # Draw team logos and names
        if bet_type == 'game_line':
            margin_left = card_x0 + 24
            name_y = card_y + 32
            # Home team
            home_logo = self._load_team_logo(home_team, league)
            if home_logo:
                home_logo = home_logo.convert('RGBA').resize(logo_size)
                image.paste(home_logo, (margin_left, name_y - 8), home_logo)
            home_name_x = margin_left + logo_size[0] + 12
            home_color = "#00ff66" if selected and selected.lower() == home_team.lower() else "#ffffff"
            draw.text((home_name_x, name_y), home_team, font=team_font, fill=home_color)
            # VS and away team
            vs_text = "VS"
            vs_font = self.font_vs_small
            vs_x = home_name_x + draw.textlength(home_team, font=team_font) + 16
            draw.text((vs_x, name_y), vs_text, font=vs_font, fill="#888888")
            away_name_x = vs_x + draw.textlength(vs_text, font=vs_font) + 16
            away_color = "#00ff66" if selected and selected.lower() == away_team.lower() else "#ffffff"
            draw.text((away_name_x, name_y), away_team, font=team_font, fill=away_color)
            away_logo = self._load_team_logo(away_team, league)
            if away_logo:
                away_logo = away_logo.convert('RGBA').resize(logo_size)
                image.paste(away_logo, (card_x1 - logo_size[0] - 24, name_y - 8), away_logo)
            # Line (below names)
            line_y = name_y + 38
            draw.text((home_name_x, line_y), line, font=line_font, fill="#ffffff")
        elif bet_type == 'player_prop':
            margin_left = card_x0 + 24
            name_y = card_y + 32
            # Team logo
            team_logo = self._load_team_logo(home_team, league)
            if team_logo:
                team_logo = team_logo.convert('RGBA').resize(logo_size)
                image.paste(team_logo, (margin_left, name_y - 8), team_logo)
            # Player name
            player_name_x = margin_left + logo_size[0] + 12
            draw.text((player_name_x, name_y), player_name, font=team_font, fill="#ffffff")
            # Line (below player name)
            line_y = name_y + 38
            draw.text((player_name_x, line_y), line, font=line_font, fill="#ffffff")
        # Odds badge (right side, vertically centered)
        badge_w = 90
        badge_h = 48
        badge_x = card_x1 - badge_w - 32
        badge_y = card_y + card_height//2 - badge_h//2
        draw.rounded_rectangle([(badge_x, badge_y), (badge_x+badge_w, badge_y+badge_h)], radius=18, fill=badge_color)
        odds_text = odds if odds else "-"
        # Format odds with sign
        try:
            odds_val = int(float(odds_text))
            odds_text = f"+{odds_val}" if odds_val > 0 else str(odds_val)
        except Exception:
            pass
        odds_text_w = draw.textlength(odds_text, font=odds_font)
        odds_text_x = badge_x + badge_w//2 - odds_text_w//2
        odds_text_y = badge_y + badge_h//2 - self.font_bold.size//2 + 4
        draw.text((odds_text_x, odds_text_y), odds_text, font=odds_font, fill=badge_text_color)

    def _draw_odds_and_units(self, draw, image, total_odds, units, y, image_width, units_display_mode='auto', display_as_risk=None):
        # Format odds with sign, as whole number, or 'X' if not set
        if not total_odds:
            odds_text = "Total Odds: X"
        else:
            try:
                odds_val = int(float(total_odds))
                odds_text = f"Total Odds: +{odds_val}" if odds_val > 0 else f"Total Odds: {odds_val}"
            except Exception:
                odds_text = "Total Odds: X"
        odds_width = draw.textlength(odds_text, font=self.font_huge)
        draw.text((int(image_width//2 - odds_width//2), int(y+20)), odds_text, font=self.font_huge, fill="#ffffff")
        
        # Calculate profit to determine To Risk/To Win
        profit = 0.0
        try:
            odds_val = float(total_odds)
            if odds_val < 0:
                profit = units * (100.0 / abs(odds_val))
            elif odds_val > 0:
                profit = units * (odds_val / 100.0)
        except Exception:
            profit = 0.0
            
        # Format units text with proper Unit/Units label, or 'X' if not set
        if not units:
            payout_text = "Units: X"
        else:
            unit_label = "Unit" if units <= 1.0 else "Units"
            if units_display_mode == 'manual' and display_as_risk is not None:
                payout_text = f"To Risk {units:.2f} {unit_label}" if display_as_risk else f"To Win {units:.2f} {unit_label}"
            else:
                payout_text = f"To Risk {units:.2f} {unit_label}" if profit < 1.0 else f"To Win {units:.2f} {unit_label}"
            
        risk_width = draw.textlength(payout_text, font=self.font_bold)
        
        # Load lock icon
        from PIL import Image
        import os
        lock_icon_path = "betting-bot/static/lock_icon.png"
        lock_icon = None
        if os.path.exists(lock_icon_path):
            lock_icon = Image.open(lock_icon_path).convert("RGBA").resize((32, 32))
            
        total_width = int(risk_width + (lock_icon.width if lock_icon else 0)*2 + 16)  # 8px padding each side
        start_x = int(image_width//2 - total_width//2)
        icon_y = int(y+85)
        text_y = int(y+85 + (lock_icon.height//2 - self.font_bold.size//2)) if lock_icon else int(y+85)
        
        if lock_icon:
            image.paste(lock_icon, (start_x, icon_y), lock_icon)
            draw.text((start_x + lock_icon.width + 8, text_y), payout_text, font=self.font_bold, fill="#ffcc00")
            image.paste(lock_icon, (start_x + lock_icon.width + 8 + int(risk_width) + 8, icon_y), lock_icon)
        else:
            draw.text((start_x, text_y), payout_text, font=self.font_bold, fill="#ffcc00")

    def _draw_footer(self, draw, bet_id, bet_datetime, image_height, image_width):
        draw.text((40, image_height-40), f"Bet #{bet_id}", font=self.font_mini, fill="#aaaaaa")
        draw.text((image_width-260, image_height-40), bet_datetime, font=self.font_mini, fill="#aaaaaa")

    def _load_team_logo(self, team_name: str, league: str):
        import os
        from PIL import Image
        import difflib
        from config.team_mappings import normalize_team_name
        from config.asset_paths import get_sport_category_for_path
        from data.game_utils import normalize_team_name_any_league
        logger = logging.getLogger(__name__)

        # First normalize the team name using league dictionaries
        try:
            # Import the appropriate league dictionary based on the league
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

            # Try to find the team in the dictionary
            normalized_team = None
            team_name_lower = team_name.lower()
            
            # First try exact match
            if team_name_lower in league_dict:
                normalized_team = league_dict[team_name_lower]
            else:
                # Try fuzzy matching against dictionary keys
                matches = difflib.get_close_matches(team_name_lower, league_dict.keys(), n=1, cutoff=0.75)
                if matches:
                    normalized_team = league_dict[matches[0]]
                    logger.info(f"[LOGO] Fuzzy matched team name '{team_name}' to '{normalized_team}' using league dictionary")
        except Exception as e:
            logger.warning(f"[LOGO] Error using league dictionary for '{team_name}': {e}")
            normalized_team = None

        # If dictionary lookup failed, fall back to the original normalization
        if not normalized_team:
            normalized_team = normalize_team_name_any_league(team_name)

        sport = get_sport_category_for_path(league.upper())
        if not sport:
            # Always use guild-specific default if guild_id is available
            if self.guild_id:
                default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png"
            else:
                default_path = "betting-bot/static/logos/default_image.png"
            return Image.open(default_path).convert("RGBA")
            
        # First try exact match with normalized name
        normalized = normalized_team.replace(".", "").replace(" ", "_").lower()
        fname = f"{normalize_team_name(normalized)}.png"
        logo_path = os.path.join("betting-bot/static/logos/teams", sport, league.upper(), fname)
        
        if os.path.exists(logo_path):
            logger.info(f"[LOGO] Found exact logo match for '{team_name}' -> '{normalized_team}' at: {logo_path}")
            return Image.open(logo_path).convert("RGBA")
            
        # If exact match fails, try fuzzy matching
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
                
        # Always use guild-specific default if guild_id is available
        if self.guild_id:
            default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png"
        else:
            default_path = "betting-bot/static/logos/default_image.png"
        logger.warning(f"[LOGO] Logo not found for '{team_name}' (tried: {logo_path}). Using fallback: {default_path}")
        return Image.open(default_path).convert("RGBA")

    def _load_player_image(self, player_name: str, team_name: str, league: str):
        import os
        from PIL import Image
        from config.asset_paths import get_sport_category_for_path
        from data.game_utils import normalize_team_name_any_league
        sport = get_sport_category_for_path(league.upper())
        if not sport:
            if self.guild_id:
                default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png"
            else:
                default_path = "betting-bot/static/logos/default_image.png"
            return Image.open(default_path).convert("RGBA"), None
        normalized_team = normalize_team_name_any_league(team_name).lower().replace(" ", "_")
        normalized_player = normalize_team_name_any_league(player_name).lower().replace(" ", "_")
        sport_dir = sport.lower().replace(" ", "_")
        player_dir = os.path.join(
            "betting-bot/static/logos/players",
            sport_dir,
            normalized_team
        )
        # Try multiple filename patterns for player images
        player_name_variants = [
            player_name,
            player_name.replace(".", "").replace(",", ""),
            player_name.replace(".", "").replace(",", "").replace(" Jr", "_jr").replace(" Sr", "_sr"),
            player_name.replace(".", "").replace(",", "").replace(" Jr.", "_jr").replace(" Sr.", "_sr"),
            player_name.replace(".", "").replace(",", "").replace(" Jr", "_jr").replace(" Sr", "_sr").replace(" ", "_"),
            player_name.replace(".", "").replace(",", "").replace(" Jr.", "_jr").replace(" Sr.", "_sr").replace(" ", "_"),
            player_name.lower().replace(".", "").replace(",", "").replace(" ", "_"),
            normalized_player,
        ]
        # Remove duplicate variants
        seen = set()
        player_name_variants = [x for x in player_name_variants if not (x in seen or seen.add(x))]
        for variant in player_name_variants:
            variant = variant.strip('_').lower()
            img_path = os.path.join(player_dir, f"{variant}.png")
            if os.path.exists(img_path):
                return Image.open(img_path).convert("RGBA"), None
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
        if self.guild_id:
            default_path = f"betting-bot/static/guilds/{self.guild_id}/default_image.png"
        else:
            default_path = "betting-bot/static/logos/default_image.png"
        return Image.open(default_path).convert("RGBA"), None
