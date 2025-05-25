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