# This file contains the logic for generating player prop bet images.
import logging
import os

from PIL import Image, ImageFont

from bot.utils.asset_loader import asset_loader

logger = logging.getLogger(__name__)


class PlayerPropImageGenerator:
    def __init__(self, font_dir="bot/assets/fonts", guild_id=None):
        self.font_dir = font_dir
        self.guild_id = guild_id
        self.font_regular = ImageFont.truetype(
            os.path.join(font_dir, "Roboto-Regular.ttf"), 28
        )
        self.font_bold = ImageFont.truetype(
            os.path.join(font_dir, "Roboto-Bold.ttf"), 36
        )
        self.font_small = ImageFont.truetype(
            os.path.join(font_dir, "Roboto-Regular.ttf"), 22
        )
        self.font_mini = ImageFont.truetype(
            os.path.join(font_dir, "Roboto-Regular.ttf"), 18
        )
        self.font_huge = ImageFont.truetype(
            os.path.join(font_dir, "Roboto-Bold.ttf"), 48
        )

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
        team_name_font = self.font_m_18
        player_name_font = self.font_b_24
        text_color = "white"
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
    def generate_player_prop_bet_image(
        player_name,
        team_name,
        league,
        line,
        prop_type,
        units,
        output_path=None,
        bet_id=None,
        timestamp=None,
        guild_id=None,
        odds=None,
        units_display_mode="auto",
        display_as_risk=None,
    ):
        """Generates a player prop bet slip image. Layout matches game line bet slip, except right side is player image and team/player names are white."""

        from PIL import Image, ImageDraw, ImageFont

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
        lock_icon_path = "bot/static/lock_icon.png"
        font_dir = "bot/assets/fonts"
        font_bold = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", header_font_size)
        font_bold_team = ImageFont.truetype(
            f"{font_dir}/Roboto-Bold.ttf", team_font_size
        )
        font_bold_player = ImageFont.truetype(
            f"{font_dir}/Roboto-Bold.ttf", player_font_size
        )
        font_line = ImageFont.truetype(f"{font_dir}/Roboto-Regular.ttf", line_font_size)
        font_odds = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", odds_font_size)
        font_risk = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", risk_font_size)
        font_footer = ImageFont.truetype(
            f"{font_dir}/Roboto-Regular.ttf", footer_font_size
        )

        image = Image.new("RGB", (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)

        # Header (league logo + text)
        logo_display_size = (45, 45)
        league_upper = league.upper()
        league_lower = league.lower()
        from bot.config.asset_paths import get_sport_category_for_path

        sport_category = get_sport_category_for_path(league_upper)
        league_logo_path = f"bot/static/logos/leagues/{sport_category}/{league_upper}/{league_lower}.png"
        try:
            league_logo_original = Image.open(league_logo_path).convert("RGBA")
            # Maintain aspect ratio when resizing
            league_logo_original.thumbnail(logo_display_size, Image.Resampling.LANCZOS)
            league_logo = league_logo_original
        except Exception:
            league_logo = None
        # Get proper league display name
        from bot.config.leagues import LEAGUE_CONFIG

        league_display_name = LEAGUE_CONFIG.get(league, {}).get("name", league_upper)

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
            truncated_name = league_name
            while (
                truncated_name and font.getbbox(f"{truncated_name} - PP")[2] > max_width
            ):
                truncated_name = truncated_name[:-1]

            if truncated_name:
                return f"{truncated_name} - PP"
            else:
                return "Player Prop"  # Fallback

        # Calculate available width for text (accounting for logo and padding)
        logo_space = logo_display_size[0] + 12 if league_logo else 0
        available_text_width = (
            image_width - 48 - logo_space
        )  # 48px total padding (24px each side)

        header_text = create_header_text_with_fallback(
            league_display_name, font_bold, available_text_width, logo_space
        )

        header_bbox = font_bold.getbbox(header_text)
        header_w = header_bbox[2] - header_bbox[0]
        header_h = header_bbox[3] - header_bbox[1]
        logo_w = league_logo.size[0] if league_logo else 0
        logo_h = league_logo.size[1] if league_logo else 0
        gap = 12 if league_logo else 0
        total_header_w = logo_w + gap + header_w
        block_h = max(logo_h, header_h)
        block_x = (image_width - total_header_w) // 2
        block_y = 25
        if league_logo:
            logo_y = block_y + (block_h - logo_h) // 2
            text_y = block_y + (block_h - header_h) // 2
            image.paste(league_logo, (block_x, logo_y), league_logo)
            text_x = block_x + logo_w + gap
        else:
            text_x = block_x
            text_y = block_y
        draw.text(
            (text_x, text_y), header_text, font=font_bold, fill="white", anchor="lt"
        )

        # Teams/Player Section
        y_base = 85
        section_width = image_width // 2 - padding * 1.5
        team_section_center_x = padding + section_width // 2
        player_section_center_x = image_width - padding - section_width // 2

        # Team logo (left)
        team_logo = PlayerPropImageGenerator._load_team_logo(
            team_name, league, guild_id
        )
        if team_logo:
            team_logo_copy = team_logo.convert("RGBA").copy()
            team_logo_copy.thumbnail(logo_size, Image.Resampling.LANCZOS)
            team_logo_x = int(team_section_center_x - team_logo_copy.size[0] // 2)
            team_logo_y = int(y_base + (logo_size[1] - team_logo_copy.size[1]) // 2)
            image.paste(team_logo_copy, (team_logo_x, team_logo_y), team_logo_copy)

        # Player image (right)
        player_image, display_name = PlayerPropImageGenerator._load_player_image(
            player_name, team_name, league, guild_id
        )
        if player_image:
            player_image_copy = player_image.convert("RGBA").copy()
            player_image_copy.thumbnail(logo_size, Image.Resampling.LANCZOS)
            player_image_x = int(player_section_center_x - player_image_copy.size[0] // 2)
            player_image_y = int(y_base + (logo_size[1] - player_image_copy.size[1]) // 2)
            image.paste(
                player_image_copy, (player_image_x, player_image_y), player_image_copy
            )

        # Team name (left, white)
        team_name_w, _ = font_bold_team.getbbox(team_name)[2:]
        team_name_x = team_section_center_x - team_name_w // 2
        team_name_y = y_base + logo_size[1] + 8
        draw.text(
            (team_name_x, team_name_y),
            team_name,
            font=font_bold_team,
            fill="white",
            anchor="lt",
        )

        # Player name (right, white)
        player_name_w, _ = font_bold_player.getbbox(display_name)[2:]
        player_name_x = player_section_center_x - player_name_w // 2
        player_name_y = y_base + logo_size[1] + 8
        draw.text(
            (player_name_x, player_name_y),
            display_name,
            font=font_bold_player,
            fill="white",
            anchor="lt",
        )

        # Remove prop_acronyms and use full, capitalized prop type
        prop_full = prop_type.replace('_', ' ').title()
        # Combine line and prop type for display
        line_and_prop = f"{line} {prop_full}"
        line_and_prop_w, line_and_prop_h = font_line.getbbox(line_and_prop)[2:]
        line_and_prop_y = team_name_y + 40  # Increased from 16 to 40 for more vertical space
        draw.text(
            ((image_width - line_and_prop_w) // 2, line_and_prop_y),
            line_and_prop,
            font=font_line,
            fill="white",
            anchor="lt",
        )

        # Separator line above odds
        sep_above_odds_y = line_and_prop_y + line_and_prop_h + 18
        draw.line(
            [(padding, sep_above_odds_y), (image_width - padding, sep_above_odds_y)],
            fill="#aaaaaa",
            width=1,
        )

        # Odds (displayed between separator and units line)
        odds_val = None
        odds_text = ""
        if odds is not None:
            try:
                odds_val = float(odds)
                odds_text = (
                    f"{int(odds_val):+d}" if odds_val > 0 else f"{int(odds_val):d}"
                )
            except Exception:
                odds_text = ""
        odds_w, odds_h = font_odds.getbbox(odds_text)[2:] if odds_text else (0, 0)
        odds_y = sep_above_odds_y + 24
        if odds_text:
            draw.text(
                ((image_width - odds_w) // 2, odds_y),
                odds_text,
                font=font_odds,
                fill="#FFD700",
                anchor="lt",
            )

        # Risk/Units (yellow, lock icons) - move below odds
        from bot.utils.bet_utils import (
            calculate_profit_from_odds,
            determine_risk_win_display_auto,
            format_units_display,
        )

        profit = (
            calculate_profit_from_odds(odds_val, units) if odds_val is not None else 0.0
        )
        unit_label = "Unit" if units <= 1 else "Units"

        if units_display_mode == "manual" and display_as_risk is not None:
            payout_text = format_units_display(units, display_as_risk, unit_label)
        else:
            # Auto mode: intelligent determination based on odds and profit ratio
            if units_display_mode == "auto":
                display_as_risk_auto = determine_risk_win_display_auto(
                    odds_val or 0, units, profit
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
        payout_w, payout_h = font_risk.getbbox(payout_text)[2:]
        payout_y = odds_y + odds_h + 8
        lock_icon = None
        try:
            lock_icon = Image.open(lock_icon_path).resize((24, 24))
        except Exception:
            lock_icon = None
        if lock_icon:
            image.paste(
                lock_icon, ((image_width - payout_w) // 2 - 28, payout_y), lock_icon
            )
            draw.text(
                ((image_width - payout_w) // 2, payout_y),
                payout_text,
                font=font_risk,
                fill="#FFD700",
                anchor="lt",
            )
            image.paste(
                lock_icon,
                ((image_width - payout_w) // 2 + payout_w + 8, payout_y),
                lock_icon,
            )
        else:
            draw.text(
                ((image_width - payout_w) // 2, payout_y),
                payout_text,
                font=font_risk,
                fill="#FFD700",
                anchor="lt",
            )

        # Footer (bet id and timestamp) - moved down to avoid overlap
        footer_padding = 25  # Increased from 12 to 25
        footer_y = image_height - footer_padding - font_footer.size
        
        # Add extra spacing from the content above
        content_bottom = payout_y + payout_h + 20  # Add 20px spacing after payout text
        if footer_y < content_bottom + 30:  # Ensure at least 30px gap
            footer_y = content_bottom + 30
        
        # Ensure bet_id is properly formatted
        if bet_id and str(bet_id).strip():
            bet_id_text = f"Bet #{str(bet_id).strip()}"
        else:
            bet_id_text = ""
            
        if timestamp:
            if isinstance(timestamp, str):
                timestamp_text = timestamp
            else:
                timestamp_text = timestamp.strftime("%Y-%m-%d %H:%M UTC")
        else:
            timestamp_text = ""
            
        # Draw bet ID bottom left
        if bet_id_text:
            draw.text((padding, footer_y), bet_id_text, font=font_footer, fill="#888888")
            
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
