# This file contains the logic for generating game line bet images.
from PIL import Image, ImageDraw

class GameLineImageGenerator:
    def __init__(self, fonts, padding):
        self.fonts = fonts
        self.padding = padding

    def draw_teams_section(self, img, draw, image_width, home_team, away_team, home_logo, away_logo, selected_team):
        y_base = 85
        logo_size = (120, 120)
        text_y_offset = logo_size[1] + 8
        team_name_font = self.fonts['font_b_24']
        vs_font = self.fonts['font_b_28']
        green_color = '#00FF00'  # Bright green
        white_color = 'white'
        vs_color = '#FFD700'  # Gold color for VS
        section_width = image_width // 2 - self.padding * 1.5
        home_section_center_x = self.padding + section_width // 2
        away_section_center_x = image_width - self.padding - section_width // 2
        center_x = image_width // 2
        vs_text = "VS"
        vs_bbox = vs_font.getbbox(vs_text)
        vs_w = vs_bbox[2] - vs_bbox[0]
        vs_h = vs_bbox[3] - vs_bbox[1]
        vs_x = center_x - vs_w // 2
        vs_y = y_base + logo_size[1] // 2 - vs_h // 2
        draw.text((vs_x, vs_y), vs_text, font=vs_font, fill=vs_color)

        # Draw home team section
        if home_logo:
            home_logo_resized = home_logo.resize(logo_size, Image.Resampling.LANCZOS)
            home_logo_x = home_section_center_x - logo_size[0] // 2
            img.paste(home_logo_resized, (int(home_logo_x), int(y_base)), home_logo_resized)
        home_bbox = team_name_font.getbbox(home_team)
        home_name_w = home_bbox[2] - home_bbox[0]
        home_name_h = home_bbox[3] - home_bbox[1]
        home_name_x = home_section_center_x - home_name_w // 2
        home_color = green_color if selected_team and selected_team.lower() == home_team.lower() else white_color
        draw.text((home_name_x, y_base + text_y_offset), home_team, font=team_name_font, fill=home_color)

        # Draw away team section
        if away_logo:
            away_logo_resized = away_logo.resize(logo_size, Image.Resampling.LANCZOS)
            away_logo_x = away_section_center_x - logo_size[0] // 2
            img.paste(away_logo_resized, (int(away_logo_x), int(y_base)), away_logo_resized)
        away_bbox = team_name_font.getbbox(away_team)
        away_name_w = away_bbox[2] - away_bbox[0]
        away_name_h = away_bbox[3] - away_bbox[1]
        away_name_x = away_section_center_x - away_name_w // 2
        away_color = green_color if selected_team and selected_team.lower() == away_team.lower() else white_color
        draw.text((away_name_x, y_base + text_y_offset), away_team, font=team_name_font, fill=away_color)

    def draw_straight_details(self, draw, image_width, image_height, line, odds, units, bet_id, timestamp, img, start_y):
        y = start_y if start_y is not None else 100 + 70 + 10 + 24 + 30
        center_x = image_width / 2
        text_color = 'white'
        gold_color = '#FFD700'
        divider_color = '#606060'

        line_font = self.fonts['font_m_24']
        odds_font = self.fonts['font_b_28']
        units_font = self.fonts['font_b_24']
        emoji_font = self.fonts['emoji_font_24']

        if line:
            line = line.upper()
            line_bbox = line_font.getbbox(line)
            line_w = line_bbox[2] - line_bbox[0]
            line_h = line_bbox[3] - line_bbox[1]
            y += 10  # Extra space after team names, before line
            draw.text((center_x, y), line, font=line_font, fill=text_color, anchor="mt")
            y += line_h + 24  # More space after line, before separator

        draw.line([(self.padding + 20, y), (image_width - self.padding - 20, y)], fill=divider_color, width=2)
        y += 18  # More space after separator

        odds_text = f"{odds}"  # Format odds
        odds_bbox = odds_font.getbbox(odds_text)
        odds_w = odds_bbox[2] - odds_bbox[0]
        odds_h = odds_bbox[3] - odds_bbox[1]
        draw.text((center_x, y), odds_text, font=odds_font, fill=text_color, anchor="mt")
        y += odds_h + 12

        # Stake / To Risk logic
        payout_text = f"To Risk {units:.2f} Units"
        payout_bbox = units_font.getbbox(payout_text)
        payout_text_w = payout_bbox[2] - payout_bbox[0]
        payout_text_h = payout_bbox[3] - payout_bbox[1]
        draw.text((center_x - payout_text_w / 2, y), payout_text, font=units_font, fill=gold_color)
        y += payout_text_h + 60
        return y

    def draw_footer(self, draw, image_width, image_height, bet_id, timestamp):
        footer_font = self.fonts['font_m_18']
        footer_color = '#CCCCCC'
        footer_text = f"Bet #{bet_id} | {timestamp.strftime('%Y-%m-%d %H:%M UTC')}"
        footer_bbox = footer_font.getbbox(footer_text)
        footer_w = footer_bbox[2] - footer_bbox[0]
        footer_h = footer_bbox[3] - footer_bbox[1]
        footer_x = (image_width - footer_w) // 2
        footer_y = image_height - footer_h - self.padding
        draw.text((footer_x, footer_y), footer_text, font=footer_font, fill=footer_color)
