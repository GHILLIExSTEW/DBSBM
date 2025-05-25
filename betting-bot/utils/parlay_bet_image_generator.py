def generate_parlay_bet_image(bets, output_path):
    """Generates a parlay bet slip image."""
    from PIL import Image, ImageDraw, ImageFont

    # Load fonts
    font_regular = ImageFont.truetype("betting-bot/assets/fonts/Roboto-Regular.ttf", 24)
    font_bold = ImageFont.truetype("betting-bot/assets/fonts/Roboto-Bold.ttf", 32)

    # Create a blank image
    image_width, image_height = 800, 400 + len(bets) * 50
    image = Image.new("RGB", (image_width, image_height), "black")
    draw = ImageDraw.Draw(image)

    # Draw header
    header_text = "Parlay Bet Slip"
    header_width, header_height = draw.textsize(header_text, font=font_bold)
    draw.text(((image_width - header_width) / 2, 20), header_text, font=font_bold, fill="white")

    # Draw each bet
    y_offset = 100
    for bet in bets:
        bet_text = f"{bet['team1']} vs {bet['team2']} - {bet['line']}"
        bet_width, bet_height = draw.textsize(bet_text, font=font_regular)
        draw.text(((image_width - bet_width) / 2, y_offset), bet_text, font=font_regular, fill="white")
        y_offset += 50

    # Draw footer
    footer_text = "Bet responsibly."
    footer_width, footer_height = draw.textsize(footer_text, font=font_regular)
    draw.text(((image_width - footer_width) / 2, image_height - 50), footer_text, font=font_regular, fill="white")

    # Save the image
    image.save(output_path)
