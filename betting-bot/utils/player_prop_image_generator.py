# This file contains the logic for generating player prop bet images.
from PIL import Image, ImageDraw

class PlayerPropImageGenerator:
    def __init__(self, fonts, padding):
        self.fonts = fonts
        self.padding = padding

    def draw_player_prop_section(self, img, draw, image_width, display_vs, home_logo, away_logo, player_name, player_image, player_team, home_team, away_team, regenerate_logo):
        y_base = 85
        logo_size = (120, 120)
        player_img_max_size = (90, 90)  # Dynamically constrain player image
        text_y_offset = logo_size[1] + 16  # Adjusted for better spacing
        team_name_font = self.fonts['font_m_18']  # Smaller font for team names
        player_name_font = self.fonts['font_b_24']
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
                elif player_team.strip().lower() == away_team.strip().lower():
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
        image.save(output_path)
