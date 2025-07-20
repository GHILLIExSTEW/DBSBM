import logging
import os

from PIL import ImageDraw, ImageFont

from bot.utils.asset_loader import asset_loader

logger = logging.getLogger(__name__)


class ParlayBetImageGenerator:
    """
    A class to generate parlay bet slip images styled like the provided example.
    """

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
        self.font_vs_small = ImageFont.truetype(
            os.path.join(font_dir, "Roboto-Regular.ttf"), 21
        )  # 3/4 of 28

    def generate_parlay_preview(self, legs, total_odds=None, units=None):
        """
        Generates a preview image for a parlay bet (before finalization).
        """
        return self.generate_image(
            legs=legs,
            output_path=None,
            total_odds=total_odds,
            units=units,
            bet_id=None,
            bet_datetime=None,
            finalized=False,
        )

    def generate_image(
        self,
        legs,
        output_path,
        total_odds,
        units,
        bet_id,
        bet_datetime,
        finalized=False,
        units_display_mode="auto",
        display_as_risk=None,
    ):
        """
        Generates a parlay bet slip image.
        Each leg in `legs` should be a dict with keys:
          - 'bet_type' ('game_line' or 'player_prop'), 'league', 'home_team', 'away_team', 'selected_team', 'line', 'player_name' (if player prop)
        """

        from PIL import Image

        # Defensive: ensure legs is a list, not None
        if legs is None:
            logging.error(
                "[ParlayBetImageGenerator] 'legs' argument is None. Returning blank image."
            )
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
        draw.text(
            (
                int(
                    image_width // 2
                    - draw.textlength(header_text, font=self.font_bold) // 2
                ),
                8,
            ),
            header_text,
            font=self.font_bold,
            fill="#ffffff",
        )

        y = int(header_height + extra_header_padding)  # add extra space after header
        for i, leg in enumerate(legs):
            self._draw_leg(draw, image, leg, int(y), int(image_width))
            # Divider line between legs, move up to just below leg content
            if i < n_legs - 1:
                divider_y = int(y + leg_height - 60)  # move divider up even more
                draw.line(
                    [(40, divider_y), (int(image_width) - 40, divider_y)],
                    fill="#444444",
                    width=2,
                )
            y += leg_height

        if finalized:
            logger.debug(
                f"Rendering finalized parlay image: odds={total_odds}, units={units}, bet_id={bet_id}, bet_datetime={bet_datetime}"
            )
            # Odds and units
            if units is None:
                units = 1.00
            self._draw_odds_and_units(
                draw,
                image,
                total_odds,
                units,
                int(y),
                int(image_width),
                units_display_mode,
                display_as_risk,
            )
            # Footer (bet id and timestamp)
            footer_padding = 12
            footer_y = int(image_height - footer_padding - self.font_mini.size)
            
            # Ensure bet_id is properly formatted
            if bet_id and str(bet_id).strip():
                bet_id_text = f"Bet #{str(bet_id).strip()}"
            else:
                bet_id_text = ""
                
            timestamp_text = bet_datetime if bet_datetime else ""
            
            # Draw bet ID bottom left
            if bet_id_text:
                draw.text((32, footer_y), bet_id_text, font=self.font_mini, fill="#888888")
                
            # Draw timestamp bottom right
            if timestamp_text:
                ts_bbox = self.font_mini.getbbox(timestamp_text)
                ts_width = ts_bbox[2] - ts_bbox[0]
                draw.text(
                    (int(image_width - 32 - ts_width), footer_y),
                    timestamp_text,
                    font=self.font_mini,
                    fill="#888888",
                )

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
        pass

        bet_type = str(leg.get("bet_type", "game_line") or "")
        league = str(leg.get("league", "") or "")
        home_team = str(leg.get("home_team", "") or "")
        away_team = str(leg.get("away_team", "") or "")
        selected = str(leg.get("selected_team", "") or "")
        line = str(leg.get("line", "") or "")
        player_name = str(leg.get("player_name", "") or "")
        odds = str(leg.get("odds", ""))

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
        draw.rounded_rectangle(
            [(card_x0, card_y), (card_x1, card_y1)], radius=card_radius, fill="#181c24"
        )

        if bet_type == "game_line":
            # Horizontal layout: Team | VS | Opponent | Line | Odds
            # Center everything vertically in the card
            card_center_y = card_y + card_height // 2
            logo_y = card_center_y - logo_size[1] // 2
            name_y = logo_y + logo_size[1] + 6
            line_y = name_y + 38
            
            # Calculate positions for horizontal layout
            left_margin = card_x0 + 20
            right_margin = card_x1 - 20
            available_width = right_margin - left_margin
            
            # Helper function to truncate text if needed
            def truncate_text(text, max_width, font):
                if draw.textlength(text, font=font) <= max_width:
                    return text
                # Try to find a good truncation point
                for i in range(len(text) - 1, 0, -1):
                    truncated = text[:i] + "..."
                    if draw.textlength(truncated, font=font) <= max_width:
                        return truncated
                return text[:10] + "..." if len(text) > 10 else text
            
            # Team (left-aligned)
            team_logo = self._load_team_logo(home_team, league)
            if team_logo:
                team_logo = team_logo.convert("RGBA").resize(logo_size)
                image.paste(team_logo, (int(left_margin), int(logo_y)), team_logo)
            
            team_display = truncate_text(home_team, 120, team_font)
            team_color = "#00ff66" if selected and selected.lower() == home_team.lower() else "#ffffff"
            draw.text((int(left_margin), int(name_y)), team_display, font=team_font, fill=team_color)
            
            # VS (to right of team)
            vs_text = "VS"
            vs_font = self.font_vs_small
            vs_width = draw.textlength(vs_text, font=vs_font)
            vs_x = left_margin + 140  # Position after team
            vs_y = card_center_y - self.font_vs_small.size // 2  # Center vertically
            draw.text((int(vs_x), int(vs_y)), vs_text, font=vs_font, fill="#888888")
            
            # Opponent (to right of VS)
            opponent_logo = self._load_team_logo(away_team, league)
            if opponent_logo:
                opponent_logo = opponent_logo.convert("RGBA").resize(logo_size)
                opponent_logo_x = vs_x + vs_width + 20
                image.paste(opponent_logo, (int(opponent_logo_x), int(logo_y)), opponent_logo)
            
            opponent_display = truncate_text(away_team, 120, team_font)
            opponent_color = "#00ff66" if selected and selected.lower() == away_team.lower() else "#ffffff"
            opponent_name_x = opponent_logo_x
            draw.text((int(opponent_name_x), int(name_y)), opponent_display, font=team_font, fill=opponent_color)
            
            # Line (to right of opponent)
            line_w = draw.textlength(line, font=line_font)
            line_x = opponent_name_x + 140  # Position after opponent
            draw.text((int(line_x), int(line_y)), line, font=line_font, fill="#ffffff")
        elif bet_type == "player_prop":
            margin_left = card_x0 + 24
            name_y = card_y + 32
            # Team logo
            team_logo = self._load_team_logo(home_team, league)
            if team_logo:
                team_logo = team_logo.convert("RGBA").resize(logo_size)
                image.paste(team_logo, (margin_left, name_y - 8), team_logo)
            # Player name
            player_name_x = margin_left + logo_size[0] + 12
            draw.text(
                (player_name_x, name_y), player_name, font=team_font, fill="#ffffff"
            )
            # Line (below player name)
            line_y = name_y + 38
            draw.text((player_name_x, line_y), line, font=line_font, fill="#ffffff")
        # Odds badge (right side, vertically centered)
        badge_w = 90
        badge_h = 48
        badge_x = card_x1 - badge_w - 32
        badge_y = card_y + card_height // 2 - badge_h // 2
        draw.rounded_rectangle(
            [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
            radius=18,
            fill=badge_color,
        )
        odds_text = odds if odds else "-"
        # Format odds with sign
        try:
            odds_val = int(float(odds_text))
            odds_text = f"+{odds_val}" if odds_val > 0 else str(odds_val)
        except Exception:
            pass
        odds_text_w = draw.textlength(odds_text, font=odds_font)
        odds_text_x = badge_x + badge_w // 2 - odds_text_w // 2
        odds_text_y = badge_y + badge_h // 2 - self.font_bold.size // 2 + 4
        draw.text(
            (odds_text_x, odds_text_y), odds_text, font=odds_font, fill=badge_text_color
        )

    def _draw_odds_and_units(
        self,
        draw,
        image,
        total_odds,
        units,
        y,
        image_width,
        units_display_mode="auto",
        display_as_risk=None,
    ):
        # Format odds with sign, as whole number, or 'X' if not set
        if not total_odds:
            odds_text = "Total Odds: X"
        else:
            try:
                odds_val = int(float(total_odds))
                odds_text = (
                    f"Total Odds: +{odds_val}"
                    if odds_val > 0
                    else f"Total Odds: {odds_val}"
                )
            except Exception:
                odds_text = "Total Odds: X"
        odds_width = draw.textlength(odds_text, font=self.font_huge)
        draw.text(
            (int(image_width // 2 - odds_width // 2), int(y + 20)),
            odds_text,
            font=self.font_huge,
            fill="#ffffff",
        )

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
            from bot.utils.bet_utils import (
                determine_risk_win_display_auto,
                format_units_display,
            )

            unit_label = "Unit" if units <= 1.0 else "Units"

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
                    payout_text = (
                        f"To Risk {units:.2f} {unit_label}"
                        if profit < 1.0
                        else f"To Win {units:.2f} {unit_label}"
                    )

        risk_width = draw.textlength(payout_text, font=self.font_bold)

        # Load lock icon
        import os

        from PIL import Image

        lock_icon_path = "bot/static/lock_icon.png"
        lock_icon = None
        if os.path.exists(lock_icon_path):
            lock_icon = Image.open(lock_icon_path).convert("RGBA").resize((32, 32))

        total_width = int(
            risk_width + (lock_icon.width if lock_icon else 0) * 2 + 16
        )  # 8px padding each side
        start_x = int(image_width // 2 - total_width // 2)
        icon_y = int(y + 85)
        text_y = (
            int(y + 85 + (lock_icon.height // 2 - self.font_bold.size // 2))
            if lock_icon
            else int(y + 85)
        )

        if lock_icon:
            image.paste(lock_icon, (start_x, icon_y), lock_icon)
            draw.text(
                (start_x + lock_icon.width + 8, text_y),
                payout_text,
                font=self.font_bold,
                fill="#ffcc00",
            )
            image.paste(
                lock_icon,
                (start_x + lock_icon.width + 8 + int(risk_width) + 8, icon_y),
                lock_icon,
            )
        else:
            draw.text(
                (start_x, text_y), payout_text, font=self.font_bold, fill="#ffcc00"
            )

    def _draw_footer(self, draw, bet_id, bet_datetime, image_height, image_width):
        draw.text(
            (40, image_height - 40),
            f"Bet #{bet_id}",
            font=self.font_mini,
            fill="#aaaaaa",
        )
        draw.text(
            (image_width - 260, image_height - 40),
            bet_datetime,
            font=self.font_mini,
            fill="#aaaaaa",
        )

    def _load_team_logo(self, team_name: str, league: str):
        return asset_loader.load_team_logo(
            team_name, league, getattr(self, "guild_id", None)
        )

    def _load_player_image(self, player_name: str, team_name: str, league: str):
        return asset_loader.load_player_image(
            player_name, team_name, league, getattr(self, "guild_id", None)
        )
