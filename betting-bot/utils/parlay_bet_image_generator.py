from PIL import Image, ImageDraw, ImageFont
import os

class ParlayBetImageGenerator:
    """
    A class to generate parlay bet slip images styled like the provided example.
    """

    def __init__(self, font_dir="betting-bot/assets/fonts"):
        self.font_dir = font_dir
        self.font_regular = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 28)
        self.font_bold = ImageFont.truetype(os.path.join(font_dir, "Roboto-Bold.ttf"), 36)
        self.font_small = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 22)
        self.font_mini = ImageFont.truetype(os.path.join(font_dir, "Roboto-Regular.ttf"), 18)
        self.font_huge = ImageFont.truetype(os.path.join(font_dir, "Roboto-Bold.ttf"), 48)

    def generate_image(self, bets, output_path, odds_str, risk_amount, bet_id, bet_datetime):
        """
        Generates a parlay bet slip image.
        Each bet in `bets` should be a dict with keys:
          - 'league', 'bet_type', 'home_team', 'away_team', 'selected_team', 'line', 'ml'
          - 'player_name', 'player_stat', 'player_img_path' (optional for props)
          - 'logos': {'home', 'away', 'league'} (optional)
        """
        n_legs = len(bets)
        image_width, image_height = 800, 220 + n_legs * 140
        image = Image.new("RGB", (image_width, image_height), "#232733")
        draw = ImageDraw.Draw(image)

        # Header
        header_text = f"{n_legs}-Leg Parlay"
        draw.text((image_width//2 - draw.textlength(header_text, font=self.font_bold)//2, 24), header_text, font=self.font_bold, fill="#ffffff")

        y = 80
        for i, bet in enumerate(bets):
            self._draw_bet(draw, image, bet, y, image_width)
            y += 140

        # Odds and risk
        self._draw_odds_and_risk(draw, image, odds_str, risk_amount, y, image_width)

        # Footer
        self._draw_footer(draw, bet_id, bet_datetime, image_height, image_width)

        image.save(output_path)

    def _draw_bet(self, draw, image, bet, y, image_width):
        """Helper method to draw a single bet leg."""
        # League & Bet Type with League Logo
        league = bet.get('league', 'League')
        bet_type = bet.get('bet_type', 'Bet Type')
        logos = bet.get('logos', {})
        
        # League logo
        if logos.get('league') and os.path.exists(logos['league']):
            league_logo = Image.open(logos['league']).resize((32, 32))
            draw.text((85, y), f"{league} - {bet_type}", font=self.font_bold, fill="#ffffff")
        else:
            draw.text((40, y), f"{league} - {bet_type}", font=self.font_bold, fill="#ffffff")
        
        y += 40
        # Teams/Players
        home = bet.get('home_team', 'Home')
        away = bet.get('away_team', 'Away')
        selected = bet.get('selected_team', '')
        
        # Team logos with improved spacing
        logo_y = y
        if logos.get('home') and os.path.exists(logos['home']):
            home_logo = Image.open(logos['home']).resize((56, 56))  # Larger logos
            image.paste(home_logo, (40, logo_y-4), home_logo if home_logo.mode=='RGBA' else None)
        if logos.get('away') and os.path.exists(logos['away']):
            away_logo = Image.open(logos['away']).resize((56, 56))  # Larger logos
            image.paste(away_logo, (280, logo_y-4), away_logo if away_logo.mode=='RGBA' else None)
        
        # Team names with proper spacing
        draw.text((110, logo_y+10), home, font=self.font_regular, fill="#00ff66" if selected==home else "#ffffff")
        draw.text((350, logo_y+10), away, font=self.font_regular, fill="#00ff66" if selected==away else "#ffffff")
        
        # VS in yellow
        vs_text = "VS"
        vs_width = draw.textlength(vs_text, font=self.font_small)
        draw.text((240 - vs_width//2, logo_y+18), vs_text, font=self.font_small, fill="#ffcc00")
        
        # Line/ML with improved visibility
        ml = bet.get('ml')
        line = bet.get('line', '')
        if ml:
            draw.text((image_width-120, logo_y+10), ml, font=self.font_bold, fill="#ffffff")
        elif line:
            draw.text((image_width-320, logo_y+10), line, font=self.font_bold, fill="#ffffff")
        
        # Player prop
        if bet_type.lower().startswith('player'):
            pname = bet.get('player_name', '')
            pstat = bet.get('player_stat', '')
            draw.text((40, logo_y+70), f"{pname}", font=self.font_regular, fill="#ffffff")
            draw.text((image_width-320, logo_y+70), pstat, font=self.font_bold, fill="#ffffff")
            
            # Player image with improved positioning
            pimg = bet.get('player_img_path')
            if pimg and os.path.exists(pimg):
                player_img = Image.open(pimg).resize((56, 56))
                image.paste(player_img, (image_width//2-28, logo_y+60), player_img if player_img.mode=='RGBA' else None)
        
        # Divider
        draw.line([(40, y), (image_width-40, y)], fill="#444444", width=2)
        y += 20

    def _draw_odds_and_risk(self, draw, image, odds_str, risk_amount, y, image_width):
        """Helper method to draw odds and risk section."""
        # Odds and risk with improved styling
        odds_text = odds_str.replace(" ", "")  # Remove spaces for cleaner look
        odds_width = draw.textlength(odds_text, font=self.font_huge)
        draw.text((image_width//2 - odds_width//2, y+20), odds_text, font=self.font_huge, fill="#ffffff")

        # Risk amount with properly spaced lock emojis
        risk_text = f"To Risk {risk_amount} Units"
        risk_width = draw.textlength(risk_text, font=self.font_bold)
        total_width = risk_width + draw.textlength("🔒🔒", font=self.font_bold)
        start_x = image_width//2 - total_width//2
        draw.text((start_x, y+85), "🔒", font=self.font_bold, fill="#ffcc00")
        draw.text((start_x + draw.textlength("🔒", font=self.font_bold), y+85), risk_text, font=self.font_bold, fill="#ffcc00")
        draw.text((start_x + draw.textlength("🔒", font=self.font_bold) + risk_width, y+85), "🔒", font=self.font_bold, fill="#ffcc00")

    def _draw_footer(self, draw, bet_id, bet_datetime, image_height, image_width):
        """Helper method to draw the footer."""
        # Footer: Bet ID and datetime
        draw.text((40, image_height-40), f"Bet #{bet_id}", font=self.font_mini, fill="#aaaaaa")
        draw.text((image_width-260, image_height-40), bet_datetime, font=self.font_mini, fill="#aaaaaa")
