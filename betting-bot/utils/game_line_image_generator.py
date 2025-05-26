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
    def generate_bet_slip_image(team1_name, team1_logo_path, team2_name, team2_logo_path, line, units, output_path, bet_id=None):
        """Generates a game line bet slip image."""
        from PIL import Image, ImageDraw, ImageFont
        from datetime import datetime, timezone

        # Load fonts
        font_dir = "betting-bot/assets/fonts"
        font_regular = ImageFont.truetype(f"{font_dir}/Roboto-Regular.ttf", 24)
        font_bold = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", 32)
        font_small = ImageFont.truetype(f"{font_dir}/Roboto-Regular.ttf", 18)  # Smaller font for footer

        # Create a blank image
        image_width, image_height = 600, 220
        image = Image.new("RGB", (image_width, image_height), "#232733")
        draw = ImageDraw.Draw(image)

        # MLB logo
        mlb_logo_path = "betting-bot/assets/logos/mlb.png"  # Update this path if needed
        try:
            mlb_logo = Image.open(mlb_logo_path).convert("RGBA").resize((36, 36))
            image.paste(mlb_logo, (32, 13), mlb_logo)
        except Exception:
            mlb_logo = None  # If logo missing, skip

        # Draw header text next to MLB logo
        header_text = "MLB - Game Line"
        header_x = 32 + 36 + 10  # logo left + logo width + padding
        header_y = 15
        draw.text((header_x, header_y), header_text, font=font_bold, fill="white")

        # Team logos and VS
        logo_size = (70, 70)
        logos_y = 48
        center_x = image_width // 2
        team1_logo = Image.open(team1_logo_path).resize(logo_size)
        team2_logo = Image.open(team2_logo_path).resize(logo_size)
        team1_logo_x = center_x - 110 - logo_size[0] // 2
        team2_logo_x = center_x + 110 - logo_size[0] // 2
        if team1_logo.mode == 'RGBA':
            image.paste(team1_logo, (team1_logo_x, logos_y), team1_logo)
        else:
            image.paste(team1_logo, (team1_logo_x, logos_y))
        if team2_logo.mode == 'RGBA':
            image.paste(team2_logo, (team2_logo_x, logos_y), team2_logo)
        else:
            image.paste(team2_logo, (team2_logo_x, logos_y))

        # VS text
        vs_text = "VS"
        vs_width = draw.textlength(vs_text, font=font_bold)
        vs_height = font_bold.getbbox(vs_text)[3] - font_bold.getbbox(vs_text)[1]
        vs_x = center_x - vs_width // 2
        vs_y = logos_y + logo_size[1] // 2 - vs_height // 2
        draw.text((vs_x, vs_y), vs_text, font=font_bold, fill="#FFD700")

        # Team names
        names_y = logos_y + logo_size[1] + 2
        team1_width = draw.textlength(team1_name, font=font_bold)
        team2_width = draw.textlength(team2_name, font=font_bold)
        draw.text((team1_logo_x + logo_size[0] // 2 - team1_width // 2, names_y), team1_name, font=font_bold, fill="#00FF00")
        draw.text((team2_logo_x + logo_size[0] // 2 - team2_width // 2, names_y), team2_name, font=font_bold, fill="white")

        # ML under away team
        ml_text = "ML"
        ml_width = draw.textlength(ml_text, font=font_regular)
        ml_y = names_y + 26
        draw.text((team2_logo_x + logo_size[0] // 2 - ml_width // 2, ml_y), ml_text, font=font_regular, fill="white")

        # Horizontal line separator
        line_y = names_y + 22  # Adjusted to center under team names
        draw.line([(32, line_y), (image_width - 32, line_y)], fill="#666a77", width=2)

        # Odds
        odds_text = str(line)
        odds_width = draw.textlength(odds_text, font=font_bold)
        odds_y = line_y + 10
        draw.text((center_x - odds_width // 2, odds_y), odds_text, font=font_bold, fill="white")

        # To Risk text with lock icons
        risk_text = f"To Risk {units:.2f} Units"
        risk_y = odds_y + 32
        lock_icon = "\U0001F512"  # Unicode lock
        risk_width = draw.textlength(risk_text, font=font_bold)
        lock_width = draw.textlength(lock_icon, font=font_bold)
        total_width = lock_width + 6 + risk_width + 6 + lock_width
        start_x = center_x - total_width // 2
        draw.text((start_x, risk_y), lock_icon, font=font_bold, fill="#FFD700")
        draw.text((start_x + lock_width + 6, risk_y), risk_text, font=font_bold, fill="#FFD700")
        draw.text((start_x + lock_width + 6 + risk_width + 6, risk_y), lock_icon, font=font_bold, fill="#FFD700")

        # Footer
        if bet_id:
            bet_id_text = f"Bet #{bet_id}"
            from datetime import datetime, timezone
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            draw.text((24, image_height - 28), bet_id_text, font=font_small, fill="#aaaaaa")
            draw.text((image_width - 24, image_height - 28), timestamp, font=font_small, fill="#aaaaaa", anchor="ra")

        # Save the image
        image.save(output_path)

    def draw_teams_section(self, img, draw, image_width, home_team, away_team, home_logo, away_logo, selected_team=None):
        """Draws the teams section for game line bets."""
        from PIL import Image
        
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
        
        # Draw VS text in center
        center_x = image_width // 2
        vs_text = "VS"
        bbox = vs_font.getbbox(vs_text)
        vs_w = bbox[2] - bbox[0]
        vs_h = bbox[3] - bbox[1]
        vs_x = center_x - vs_w // 2
        vs_y = y_base + logo_size[1] // 2 - vs_h // 2
        draw.text((vs_x, vs_y), vs_text, font=vs_font, fill=vs_color, anchor="lt")
        
        # Draw home team section
        if home_logo:
            try:
                home_logo_resized = home_logo.resize(logo_size, Image.Resampling.LANCZOS)
                home_logo_x = home_section_center_x - logo_size[0] // 2
                if home_logo_resized.mode == 'RGBA':
                    img.paste(home_logo_resized, (int(home_logo_x), int(y_base)), home_logo_resized)
                else:
                    img.paste(home_logo_resized, (int(home_logo_x), int(y_base)))
            except Exception as e:
                pass  # Silently handle logo errors
        
        # Draw home team name
        bbox = team_name_font.getbbox(home_team)
        home_name_w = bbox[2] - bbox[0]
        home_name_x = home_section_center_x - home_name_w // 2
        home_color = green_color if selected_team and selected_team.lower() == home_team.lower() else white_color
        draw.text((home_name_x, y_base + text_y_offset), home_team, font=team_name_font, fill=home_color, anchor="lt")
        
        # Draw away team section
        if away_logo:
            try:
                away_logo_resized = away_logo.resize(logo_size, Image.Resampling.LANCZOS)
                away_logo_x = away_section_center_x - logo_size[0] // 2
                if away_logo_resized.mode == 'RGBA':
                    img.paste(away_logo_resized, (int(away_logo_x), int(y_base)), away_logo_resized)
                else:
                    img.paste(away_logo_resized, (int(away_logo_x), int(y_base)))
            except Exception as e:
                pass  # Silently handle logo errors
        
        # Draw away team name
        bbox = team_name_font.getbbox(away_team)
        away_name_w = bbox[2] - bbox[0]
        away_name_x = away_section_center_x - away_name_w // 2
        away_color = green_color if selected_team and selected_team.lower() == away_team.lower() else white_color
        draw.text((away_name_x, y_base + text_y_offset), away_team, font=team_name_font, fill=away_color, anchor="lt")
        
        return y_base + text_y_offset + 50  # Return y position for next section