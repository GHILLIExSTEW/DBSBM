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

class GameLineImageGenerator:
    def __init__(self, fonts=None, padding=0):
        """Initialize the GameLineImageGenerator with optional fonts and padding."""
        self.fonts = fonts
        self.padding = padding

    @staticmethod
    def generate_bet_slip_image(team1_name, team1_logo_path, team2_name, team2_logo_path, line, units, output_path):
        """Generates a game line bet slip image."""
        from PIL import Image, ImageDraw, ImageFont

        # Load fonts
        font_regular = ImageFont.truetype("betting-bot/assets/fonts/Roboto-Regular.ttf", 24)
        font_bold = ImageFont.truetype("betting-bot/assets/fonts/Roboto-Bold.ttf", 32)

        # Create a blank image
        image_width, image_height = 800, 400
        image = Image.new("RGB", (image_width, image_height), "black")
        draw = ImageDraw.Draw(image)

        # Draw team names
        team1_name_width, _ = draw.textsize(team1_name, font=font_bold)
        team2_name_width, _ = draw.textsize(team2_name, font=font_bold)
        draw.text(((image_width - team1_name_width) / 4, 20), team1_name, font=font_bold, fill="white")
        draw.text(((3 * image_width - team2_name_width) / 4, 20), team2_name, font=font_bold, fill="white")

        # Load and paste team logos
        team1_logo = Image.open(team1_logo_path).resize((100, 100))
        team2_logo = Image.open(team2_logo_path).resize((100, 100))
        image.paste(team1_logo, (100, 100))
        image.paste(team2_logo, (600, 100))

        # Draw line and units/footer section
        line_text = f"Line: {line}"
        units_text = f"Units: {units}"
        footer_text = "Bet responsibly."

        draw.text((50, 300), line_text, font=font_regular, fill="white")
        draw.text((50, 340), units_text, font=font_regular, fill="white")
        draw.text((image_width - 250, 340), footer_text, font=font_regular, fill="white")

        # Save the image
        image.save(output_path)

    @staticmethod
    def draw_teams_section(draw, team1_name, team2_name, y_position):
        """Draws the teams section on the image."""
        # Placeholder implementation
        draw.text((10, y_position), f"{team1_name} vs {team2_name}", fill="white")
        return y_position + 50