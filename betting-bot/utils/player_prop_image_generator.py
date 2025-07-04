# This file contains the logic for generating player prop bet images.
from PIL import Image, ImageDraw, ImageFont
import os
import difflib
import logging

class PlayerPropImageGenerator:
    def __init__(self, font_dir="betting-bot/assets/fonts", guild_id=None):
        self.font_dir = font_dir
        self.guild_id = guild_id
        self.font_regular = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 28)
        self.font_bold = ImageFont.truetype(os.path.join(font_dir, "Roboto-Bold.ttf"), 36)
        self.font_small = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 22)
        self.font_mini = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 18)
        self.font_huge = ImageFont.truetype(os.path.join(font_dir, "Roboto-Bold.ttf"), 48)

    def draw_player_prop_section(self, img, draw, image_width, display_vs, home_logo, away_logo, player_name, player_image, player_team, home_team, away_team, regenerate_logo):
        y_base = 85
        logo_size = (120, 120)
        player_img_max_size = (90, 90)  # Dynamically constrain player image
        text_y_offset = logo_size[1] + 16  # Adjusted for better spacing
        team_name_font = self.font_m_18
        player_name_font = self.font_b_24
        text_color = 'white'
        center_x = image_width // 2
        section_width = image_width // 2 - self.padding * 1.5
        home_section_center_x = self.padding + section_width // 2
        player_section_center_x = image_width - self.padding - section_width // 2

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
            if ' vs ' in display_vs.lower():
                parts = display_vs.split(' vs ')
                left_name = parts[0].strip()
                right_name = parts[1].strip()
            else:
                left_name = display_vs.strip()
                right_name = ''

        y_base_images = y_base
        y_base += logo_size[1] + 16  # Adjusted for better spacing

        # Draw left (player's team) name above left image
        left_name_w, left_name_h = draw.textsize(left_name, font=team_name_font)
        left_name_x = home_section_center_x - left_name_w // 2
        left_name_y = y_base_images - left_name_h - 8
        draw.text((left_name_x, left_name_y), left_name, font=team_name_font, fill=text_color, anchor="lt")

        # Draw right (opponent) name above right image
        if right_name:
            right_name_w, right_name_h = draw.textsize(right_name, font=team_name_font)
            right_name_x = player_section_center_x - right_name_w // 2
            right_name_y = y_base_images - right_name_h - 8
            draw.text((right_name_x, right_name_y), right_name, font=team_name_font, fill=text_color, anchor="lt")

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
                    home_logo_resized = logo_to_draw.resize(logo_size, Image.Resampling.LANCZOS)
                    home_logo_x = home_section_center_x - logo_size[0] // 2
                    img.paste(home_logo_resized, (int(home_logo_x), int(y_base_images)), home_logo_resized)
                except Exception as e:
                    print(f"Error pasting team logo: {e}")

        # Draw player image on the right (never opponent logo)
        if player_image:
            try:
                player_image_copy = player_image.copy()
                player_image_copy.thumbnail(player_img_max_size, Image.Resampling.LANCZOS)
                player_img_w, player_img_h = player_image_copy.size
                player_image_x = player_section_center_x - player_img_w // 2
                player_image_y = int(y_base_images + (logo_size[1] - player_img_h) // 2)
                img.paste(player_image_copy, (int(player_image_x), int(player_image_y)), player_image_copy)
            except Exception as e:
                print(f"Error pasting player image: {e}")

        # Draw player name below the images (centered)
        player_name_w, player_name_h = draw.textsize(player_name, font=player_name_font)
        player_name_x = center_x - player_name_w // 2
        draw.text((player_name_x, y_base + text_y_offset), player_name, font=player_name_font, fill=text_color, anchor="lt")

        return y_base + text_y_offset + 20  # Return y position for next section

    @staticmethod
    def _load_team_logo(team_name: str, league: str, guild_id: str = None):
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
                # Try fuzzy matching against dictionary keys (within this league only)
                matches = difflib.get_close_matches(team_name_lower, league_dict.keys(), n=1, cutoff=0.75)
                if matches:
                    normalized_team = league_dict[matches[0]]
                    logger.info(f"[LOGO] Fuzzy matched team name '{team_name}' to '{normalized_team}' using league dictionary")
        except Exception as e:
            logger.warning(f"[LOGO] Error using league dictionary for '{team_name}': {e}")
            normalized_team = None

        # If dictionary lookup failed, do NOT fall back to cross-league normalization
        if not normalized_team:
            normalized_team = team_name  # Use the original name as fallback

        sport = get_sport_category_for_path(league.upper())
        if not sport:
            default_path = f"betting-bot/static/guilds/{guild_id}/default_image.png" if guild_id else "betting-bot/static/logos/default_image.png"
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
                
        default_path = f"betting-bot/static/guilds/{guild_id}/default_image.png" if guild_id else "betting-bot/static/logos/default_image.png"
        logger.warning(f"[LOGO] Logo not found for '{team_name}' (tried: {logo_path}). Using fallback: {default_path}")
        return Image.open(default_path).convert("RGBA")

    @staticmethod
    def _load_player_image(player_name: str, team_name: str, league: str, guild_id: str = None):
        import os
        from PIL import Image
        import difflib
        from config.asset_paths import get_sport_category_for_path
        from data.game_utils import normalize_team_name_any_league
        sport = get_sport_category_for_path(league.upper())
        logger = logging.getLogger(__name__)
        if not sport:
            # Fallback logic for missing sport
            fallback_paths = []
            if guild_id:
                fallback_paths.append(f"betting-bot/static/guilds/{guild_id}/default_image.png")
            fallback_paths.append("betting-bot/static/logos/players/default_image.png")
            fallback_paths.append("betting-bot/static/logos/default_image.png")
            for path in fallback_paths:
                if os.path.exists(path):
                    logger.warning(f"[PLAYER_IMAGE] Using fallback image: {path}")
                    return Image.open(path).convert("RGBA"), player_name
            logger.error(f"[PLAYER_IMAGE] No fallback image found for player '{player_name}'. Returning blank image.")
            return Image.new("RGBA", (90, 90), (0, 0, 0, 0)), player_name
        normalized_team = normalize_team_name_any_league(team_name).replace(".", "").replace(" ", "_").lower()
        normalized_player = normalize_team_name_any_league(player_name).replace(".", "").replace(" ", "_").lower()
        player_dir = os.path.join("betting-bot/static/logos/players", sport.lower(), normalized_team)
        player_img_path = os.path.join(player_dir, f"{normalized_player}.png")

        logger.info(f"[PLAYER_IMAGE] Looking for player image. Inputs: player_name='{player_name}', team_name='{team_name}', league='{league}', guild_id='{guild_id}'")
        logger.info(f"[PLAYER_IMAGE] Normalized team: '{normalized_team}', Normalized player: '{normalized_player}'")
        logger.info(f"[PLAYER_IMAGE] Player dir: '{player_dir}', Player image path: '{player_img_path}'")

        if os.path.exists(player_img_path):
            logger.info(f"[PLAYER_IMAGE] Found exact player image: {player_img_path}")
            return Image.open(player_img_path).convert("RGBA"), player_name
        # Fuzzy match if exact not found
        if os.path.exists(player_dir):
            candidates = [f for f in os.listdir(player_dir) if f.endswith('.png')]
            candidate_names = [os.path.splitext(f)[0] for f in candidates]
            logger.info(f"[PLAYER_IMAGE] Candidates in dir: {candidate_names}")
            matches = difflib.get_close_matches(normalized_player, candidate_names, n=1, cutoff=0.75)
            if matches:
                match_file = matches[0] + '.png'
                match_path = os.path.join(player_dir, match_file)
                display_name = matches[0].replace('_', ' ').title()
                logger.info(f"[PLAYER_IMAGE] Fuzzy matched player image: {match_path}")
                return Image.open(match_path).convert("RGBA"), display_name
        logger.warning(f"[PLAYER_IMAGE] No player image found for '{player_name}' (team: '{team_name}', league: '{league}'). Trying fallback images.")
        fallback_paths = []
        if guild_id:
            fallback_paths.append(f"betting-bot/static/guilds/{guild_id}/default_image.png")
        fallback_paths.append("betting-bot/static/logos/players/default_image.png")
        fallback_paths.append("betting-bot/static/logos/default_image.png")
        for path in fallback_paths:
            if os.path.exists(path):
                logger.warning(f"[PLAYER_IMAGE] Using fallback image: {path}")
                return Image.open(path).convert("RGBA"), player_name
        logger.error(f"[PLAYER_IMAGE] No fallback image found for player '{player_name}'. Returning blank image.")
        return Image.new("RGBA", (90, 90), (0, 0, 0, 0)), player_name

    @staticmethod
    def generate_player_prop_bet_image(player_name, team_name, league, line, units, output_path=None, bet_id=None, timestamp=None, guild_id=None, odds=None, units_display_mode='auto', display_as_risk=None):
        """Generates a player prop bet slip image. Layout matches game line bet slip, except right side is player image and team/player names are white."""
        from PIL import Image, ImageDraw, ImageFont
        import os
        # Layout and font sizes match game line bet slip
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
        lock_icon_path = "betting-bot/static/lock_icon.png"
        font_dir = "betting-bot/assets/fonts"
        font_bold = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", header_font_size)
        font_bold_team = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", team_font_size)
        font_bold_player = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", player_font_size)
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
        from config.asset_paths import get_sport_category_for_path
        sport_category = get_sport_category_for_path(league_upper)
        league_logo_path = f"betting-bot/static/logos/leagues/{sport_category}/{league_upper}/{league_lower}.png"
        try:
            league_logo = Image.open(league_logo_path).convert("RGBA").resize(logo_display_size)
        except Exception:
            league_logo = None
        header_text = f"{league_upper} - Player Prop"
        header_bbox = font_bold.getbbox(header_text)
        header_w = header_bbox[2] - header_bbox[0]
        header_h = header_bbox[3] - header_bbox[1]
        logo_w = logo_display_size[0] if league_logo else 0
        gap = 12 if league_logo else 0
        total_header_w = logo_w + gap + header_w
        block_h = max(logo_display_size[1], header_h)
        block_x = (image_width - total_header_w) // 2
        block_y = 25
        if league_logo:
            logo_y = block_y + (block_h - logo_display_size[1]) // 2
            text_y = block_y + (block_h - header_h) // 2
            image.paste(league_logo, (block_x, logo_y), league_logo)
            text_x = block_x + logo_w + gap
        else:
            text_x = block_x
            text_y = block_y
        draw.text((text_x, text_y), header_text, font=font_bold, fill="white", anchor="lt")

        # Teams/Player Section
        y_base = 85
        section_width = image_width // 2 - padding * 1.5
        team_section_center_x = padding + section_width // 2
        player_section_center_x = image_width - padding - section_width // 2
        center_x = image_width // 2

        # Team logo (left)
        team_logo = PlayerPropImageGenerator._load_team_logo(team_name, league, guild_id)
        if team_logo:
            team_logo_resized = team_logo.convert('RGBA').resize(logo_size)
            team_logo_x = int(team_section_center_x - logo_size[0] // 2)
            image.paste(team_logo_resized, (team_logo_x, y_base), team_logo_resized)

        # Player image (right)
        player_image, display_name = PlayerPropImageGenerator._load_player_image(player_name, team_name, league, guild_id)
        if player_image:
            player_image_resized = player_image.convert('RGBA').resize(logo_size)
            player_image_x = int(player_section_center_x - logo_size[0] // 2)
            image.paste(player_image_resized, (player_image_x, y_base), player_image_resized)

        # Team name (left, white)
        team_name_w, _ = font_bold_team.getbbox(team_name)[2:]
        team_name_x = team_section_center_x - team_name_w // 2
        team_name_y = y_base + logo_size[1] + 8
        draw.text((team_name_x, team_name_y), team_name, font=font_bold_team, fill="white", anchor="lt")

        # Player name (right, white)
        player_name_w, _ = font_bold_player.getbbox(display_name)[2:]
        player_name_x = player_section_center_x - player_name_w // 2
        player_name_y = y_base + logo_size[1] + 8
        draw.text((player_name_x, player_name_y), display_name, font=font_bold_player, fill="white", anchor="lt")

        # Line (centered below)
        line_text = str(line)
        line_w, line_h = font_line.getbbox(line_text)[2:]
        line_y = team_name_y + 32
        draw.text(((image_width - line_w) // 2, line_y), line_text, font=font_line, fill="white", anchor="lt")

        # Separator line above odds
        sep_above_odds_y = line_y + line_h + 18
        draw.line([(padding, sep_above_odds_y), (image_width - padding, sep_above_odds_y)], fill="#aaaaaa", width=1)

        # Odds (displayed between separator and units line)
        odds_val = None
        odds_text = ""
        if odds is not None:
            try:
                odds_val = float(odds)
                odds_text = f"{int(odds_val):+d}" if odds_val > 0 else f"{int(odds_val):d}"
            except Exception:
                odds_text = ""
        odds_w, odds_h = font_odds.getbbox(odds_text)[2:] if odds_text else (0, 0)
        odds_y = sep_above_odds_y + 24
        if odds_text:
            draw.text(((image_width - odds_w) // 2, odds_y), odds_text, font=font_odds, fill="#FFD700", anchor="lt")

        # Risk/Units (yellow, lock icons) - move below odds
        profit = 0.0
        if odds_val is not None:
            if odds_val < 0:
                profit = units * (100.0 / abs(odds_val))
            elif odds_val > 0:
                profit = units * (odds_val / 100.0)
            else:
                profit = 0.0
        else:
            profit = 0.0
        unit_label = "Unit" if units <= 1 else "Units"
        if units_display_mode == 'manual' and display_as_risk is not None:
            payout_text = f"To Risk {units:.2f} {unit_label}" if display_as_risk else f"To Win {units:.2f} {unit_label}"
        else:
            if profit < 1.0:
                payout_text = f"To Risk {units:.2f} {unit_label}"
            else:
                payout_text = f"To Win {units:.2f} {unit_label}"
        payout_w, payout_h = font_risk.getbbox(payout_text)[2:]
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
        if timestamp:
            if isinstance(timestamp, str):
                timestamp_text = timestamp
            else:
                timestamp_text = timestamp.strftime("%Y-%m-%d %H:%M UTC")
        else:
            timestamp_text = ""
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
