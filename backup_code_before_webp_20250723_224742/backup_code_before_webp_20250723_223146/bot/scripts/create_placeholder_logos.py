#!/usr/bin/env python3
"""
Create Placeholder Logos for Missing Leagues
Generates simple placeholder logos for leagues that don't have real logos yet.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from bot.config.asset_paths import get_sport_category_for_path


def create_placeholder_logo(league_name: str, league_code: str, size=(200, 200)):
    """Create a simple placeholder logo with text."""
    # Create a new image with a gradient background
    img = Image.new("RGBA", size, (240, 240, 240, 255))
    draw = ImageDraw.Draw(img)

    # Create a simple gradient effect
    for y in range(size[1]):
        alpha = int(255 * (1 - y / size[1] * 0.3))
        color = (200, 200, 200, alpha)
        draw.line([(0, y), (size[0], y)], fill=color)

    # Add text
    try:
        # Try to use a system font
        font_size = min(size) // 8
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Draw league name
    text = league_name.upper()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2

    # Draw text with shadow
    draw.text((x + 2, y + 2), text, fill=(100, 100, 100, 255), font=font)
    draw.text((x, y), text, fill=(50, 50, 50, 255), font=font)

    return img


def create_all_placeholder_logos():
    """Create placeholder logos for all missing leagues."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logos_dir = os.path.join(base_dir, "static", "logos", "leagues")

    # Define leagues that need placeholder logos
    leagues_to_create = {
        "GOLF": {
            "PGA": "PGA Tour",
            "LPGA": "LPGA Tour",
            "EUROPEAN_TOUR": "European Tour",
            "LIV_GOLF": "LIV Golf",
            "KORN_FERRY": "Korn Ferry Tour",
            "CHAMPIONS_TOUR": "Champions Tour",
            "RYDER_CUP": "Ryder Cup",
            "PRESIDENTS_CUP": "Presidents Cup",
            "SOLHEIM_CUP": "Solheim Cup",
            "OLYMPIC_GOLF": "Olympic Golf",
        },
        "RACING": {"FORMULA1": "Formula 1"},
    }

    created_count = 0

    for sport, leagues in leagues_to_create.items():
        print(f"Creating placeholders for {sport}...")

        for league_code, league_name in leagues.items():
            # Get sport category
            sport_category = get_sport_category_for_path(league_code.upper())
            if not sport_category:
                print(f"  ⚠️  No sport category found for {league_code}")
                continue

            # Create directory
            league_dir = os.path.join(
                logos_dir, sport_category.upper(), league_code.upper()
            )
            os.makedirs(league_dir, exist_ok=True)

            # Create logo filenames
            filenames = [
                f"{league_name.lower().replace(' ', '_')}.png",
                f"{league_code.lower()}.png",
            ]

            for filename in filenames:
                logo_path = os.path.join(league_dir, filename)

                if not os.path.exists(logo_path):
                    try:
                        # Create placeholder logo
                        logo_img = create_placeholder_logo(league_name, league_code)
                        logo_img.save(logo_path, "PNG", optimize=True)
                        print(f"  ✅ Created {filename}")
                        created_count += 1
                    except Exception as e:
                        print(f"  ❌ Error creating {filename}: {e}")
                else:
                    print(f"  ⏭️  {filename} already exists")

    print(f"\n🎉 Created {created_count} placeholder logos")
    return created_count


def main():
    """Main function."""
    print("🎨 Creating Placeholder Logos")
    print("=" * 40)

    try:
        created = create_all_placeholder_logos()
        print(f"\n✅ Successfully created {created} placeholder logos")
        print(
            "💡 You can replace these with real logos later using the collection scripts"
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
