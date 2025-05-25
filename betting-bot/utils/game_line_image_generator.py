# This file contains the logic for generating game line bet images.
from PIL import Image, ImageDraw, ImageFont
import os

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
        white_color = 'white'
        lime_color = 'lime'
        vs_color = '#FFD700'  # Gold color for VS
        section_width = image_width // 2 - self.padding * 1.5
        home_section_center_x = self.padding + section_width // 2
        away_section_center_x = image_width - self.padding - section_width // 2
        center_x = image_width // 2

        # Draw VS text
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
        home_color = lime_color if selected_team and selected_team.lower() == home_team.lower() else white_color
        draw.text((home_section_center_x, y_base + text_y_offset), home_team, font=team_name_font, fill=home_color, anchor="mt")

        # Draw away team section
        if away_logo:
            away_logo_resized = away_logo.resize(logo_size, Image.Resampling.LANCZOS)
            away_logo_x = away_section_center_x - logo_size[0] // 2
            img.paste(away_logo_resized, (int(away_logo_x), int(y_base)), away_logo_resized)
        away_color = lime_color if selected_team and selected_team.lower() == away_team.lower() else white_color
        draw.text((away_section_center_x, y_base + text_y_offset), away_team, font=team_name_font, fill=away_color, anchor="mt")

        # Return the y position after the team names section
        return y_base + text_y_offset + 20

    def draw_straight_details(self, draw, image_width, image_height, line, odds, units, bet_id, timestamp, img, start_y):
        y = start_y if start_y is not None else 100 + 70 + 10 + 24 + 30
        center_x = image_width / 2
        text_color = 'white'
        gold_color = '#FFD700'
        divider_color = '#606060'

        line_font = self.fonts['font_m_24']
        odds_font = self.fonts['font_b_28']
        units_font = self.fonts['font_b_24']

        # Draw "ML" text
        ml_text = "ML"
        ml_bbox = line_font.getbbox(ml_text)
        ml_h = ml_bbox[3] - ml_bbox[1]
        draw.text((center_x, y), ml_text, font=line_font, fill=text_color, anchor="mt")
        y += ml_h + 10

        # Draw separator line
        draw.line([(self.padding + 20, y), (image_width - self.padding - 20, y)], fill=divider_color, width=2)
        y += 20  # Space after separator

        # Draw odds
        odds_text = f"{odds}"
        odds_bbox = odds_font.getbbox(odds_text)
        odds_h = odds_bbox[3] - odds_bbox[1]
        draw.text((center_x, y), odds_text, font=odds_font, fill=text_color, anchor="mt")
        y += odds_h + 15

        # Calculate profit and determine text
        if odds < 0:  # Favorite
            profit = units * (100.0 / abs(odds))
        elif odds > 0:  # Underdog
            profit = units * (odds / 100.0)
        else:  # Even money
            profit = units

        # Determine units display text
        if profit < 1.0:
            payout_text = f"🔒 Risk {units:.2f} Units 🔒"
        else:
            payout_text = f"🔒 To Win {profit:.2f} Units 🔒"

        # Draw units text
        draw.text((center_x, y), payout_text, font=units_font, fill=gold_color, anchor="mt")
        payout_bbox = units_font.getbbox(payout_text)
        y += payout_bbox[3] - payout_bbox[1] + 40
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

    def save_image(self, img, file_path):
        """Save the generated image to a file."""
        img.save(file_path, format='PNG')
        print(f"Image saved to {file_path}")

if __name__ == "__main__":
    from datetime import datetime
    import os

    # Example setup
    font_dir = os.path.join(os.path.dirname(__file__), "../assets/fonts")
    fonts = {
        'font_b_24': ImageFont.truetype(os.path.join(font_dir, "Roboto-Bold.ttf"), 24),
        'font_b_28': ImageFont.truetype(os.path.join(font_dir, "Roboto-Bold.ttf"), 28),
        'font_m_24': ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 24),
        'font_m_18': ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 18),
    }
    padding = 20
    generator = GameLineImageGenerator(fonts, padding)

    # Create a blank image and initialize the draw object
    image_width = 800
    image_height = 600
    img = Image.new("RGB", (image_width, image_height), "black")
    draw = ImageDraw.Draw(img)

    # Example data
    home_team = "Team A"
    away_team = "Team B"
    home_logo = None  # Replace with Image.open("path_to_home_logo.png") if available
    away_logo = None  # Replace with Image.open("path_to_away_logo.png") if available
    selected_team = "Team A"
    line = None
    odds = -110
    units = 2.0
    bet_id = 12345
    timestamp = datetime.utcnow()

    # Draw sections
    y_position = generator.draw_teams_section(img, draw, image_width, home_team, away_team, home_logo, away_logo, selected_team)
    y_position = generator.draw_straight_details(draw, image_width, image_height, line, odds, units, bet_id, timestamp, img, y_position)
    generator.draw_footer(draw, image_width, image_height, bet_id, timestamp)

    # Save the image
    generator.save_image(img, "/workspaces/DBSBM/generated_bet_slip.png")
