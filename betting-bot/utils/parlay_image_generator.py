from PIL import Image, ImageDraw

class ParlayImageGenerator:
    def __init__(self, fonts, padding):
        self.fonts = fonts
        self.padding = padding

    def draw_parlay_details(self, draw, image_width, image_height, legs, odds, units, bet_id, timestamp, is_same_game, img, team_logos):
        y_base = 85
        logo_size = (50, 50)
        text_y_offset = logo_size[1] + 10
        leg_font = self.fonts['font_m_18']

        for i, leg in enumerate(legs):
            leg_text = f"Leg {i+1}: {leg['team']} {leg['line']} ({leg['league']})"
            draw.text((self.padding, y_base), leg_text, font=leg_font, fill="white")
            y_base += text_y_offset

        # Draw odds and units
        odds_text = f"Odds: {odds}"
        units_text = f"Units: {units}"
        draw.text((self.padding, y_base), odds_text, font=leg_font, fill="white")
        y_base += text_y_offset
        draw.text((self.padding, y_base), units_text, font=leg_font, fill="white")
