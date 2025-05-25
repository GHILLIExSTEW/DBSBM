from PIL import Image, ImageDraw, ImageFont
import os

def generate_parlay_bet_image(bets, output_path, odds_str, risk_amount, bet_id, bet_datetime):
    """
    Generates a parlay bet slip image styled like the provided example.
    Each bet in `bets` should be a dict with keys:
      - 'league' (e.g. 'MLB')
      - 'bet_type' (e.g. 'Game Line', 'Player Prop')
      - 'home_team', 'away_team', 'selected_team', 'line', 'ml' (optional)
      - 'player_name', 'player_stat', 'player_img_path' (for props, optional)
      - 'logos': {'home': path, 'away': path} (optional)
    """
    # Load fonts
    font_dir = "betting-bot/assets/fonts"
    font_regular = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 28)
    font_bold = ImageFont.truetype(os.path.join(font_dir, "Roboto-Bold.ttf"), 36)
    font_small = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 22)
    font_mini = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 18)

    n_legs = len(bets)
    image_width, image_height = 800, 220 + n_legs * 120
    image = Image.new("RGB", (image_width, image_height), "#232733")
    draw = ImageDraw.Draw(image)

    # Header
    header_text = f"{n_legs}-Leg Parlay"
    draw.text((image_width//2 - draw.textlength(header_text, font=font_bold)//2, 24), header_text, font=font_bold, fill="#cccccc")

    y = 80
    for i, bet in enumerate(bets):
        # League & Bet Type
        league = bet.get('league', 'League')
        bet_type = bet.get('bet_type', 'Bet Type')
        draw.text((40, y), f"{league} - {bet_type}", font=font_bold, fill="#fff")
        y += 36
        # Teams/Players
        home = bet.get('home_team', 'Home')
        away = bet.get('away_team', 'Away')
        selected = bet.get('selected_team', '')
        # Logos (optional)
        logos = bet.get('logos', {})
        logo_y = y
        if logos.get('home') and os.path.exists(logos['home']):
            home_logo = Image.open(logos['home']).resize((48,48))
            image.paste(home_logo, (40, logo_y), home_logo if home_logo.mode=='RGBA' else None)
        if logos.get('away') and os.path.exists(logos['away']):
            away_logo = Image.open(logos['away']).resize((48,48))
            image.paste(away_logo, (220, logo_y), away_logo if away_logo.mode=='RGBA' else None)
        # Team names
        draw.text((100, logo_y+10), home, font=font_regular, fill="#00ff66" if selected==home else "#fff")
        draw.text((280, logo_y+10), away, font=font_regular, fill="#00ff66" if selected==away else "#fff")
        # VS
        draw.text((190, logo_y+18), "vs", font=font_small, fill="#aaa")
        # Line/ML
        ml = bet.get('ml')
        line = bet.get('line', '')
        if ml:
            draw.text((image_width-120, logo_y+10), ml, font=font_bold, fill="#fff")
        elif line:
            draw.text((image_width-320, logo_y+10), line, font=font_bold, fill="#fff")
        # Player prop
        if bet_type.lower().startswith('player'):
            pname = bet.get('player_name', '')
            pstat = bet.get('player_stat', '')
            draw.text((40, logo_y+60), f"{pname}", font=font_regular, fill="#fff")
            draw.text((image_width-320, logo_y+60), pstat, font=font_bold, fill="#fff")
            # Player image (optional)
            pimg = bet.get('player_img_path')
            if pimg and os.path.exists(pimg):
                player_img = Image.open(pimg).resize((48,48))
                image.paste(player_img, (image_width//2-24, logo_y+50), player_img if player_img.mode=='RGBA' else None)
        y += 90
        # Divider
        draw.line([(40, y), (image_width-40, y)], fill="#444", width=2)
        y += 10

    # Odds and risk
    draw.text((image_width//2-60, y+20), odds_str, font=font_bold, fill="#fff")
    draw.text((image_width//2-120, y+70), f"\U0001F512To Risk {risk_amount} Units\U0001F512", font=font_bold, fill="#ffcc00")

    # Footer: Bet ID and datetime
    draw.text((40, image_height-40), f"Bet #{bet_id}", font=font_mini, fill="#aaa")
    draw.text((image_width-260, image_height-40), bet_datetime, font=font_mini, fill="#aaa")

    image.save(output_path)
