#!/usr/bin/env python3
"""
Test script to verify dynamic title sizing for game line images.
"""

import os
import sys

sys.path.append("bot")

from PIL import Image, ImageDraw, ImageFont


def test_dynamic_title_sizing():
    """Test the dynamic title sizing with various league names."""

    # Test cases with different length league names
    test_cases = [
        "NBA",  # Short
        "UEFA Champions League",  # Long - should be truncated
        "English Premier League",  # Medium-long
        "Major League Baseball",  # Medium
        "Super Long League Name That Should Definitely Be Truncated",  # Very long
    ]

    # Test the dynamic sizing logic

    print("Testing dynamic title sizing...")
    print("=" * 50)

    for league in test_cases:
        print(f"\nLeague: {league}")

        # Create a test image to measure text
        image_width = 600
        image_height = 400
        image = Image.new("RGB", (image_width, image_height), "#232733")
        draw = ImageDraw.Draw(image)

        # Load font
        font_dir = "bot/assets/fonts"
        font_bold = ImageFont.truetype(f"{font_dir}/Roboto-Bold.ttf", 36)

        # Test the dynamic sizing logic
        logo_display_size = (45, 45)
        logo_space = logo_display_size[0] + 15  # Assume logo exists
        available_text_width = image_width - 48 - logo_space

        # Simulate the dynamic sizing function
        def create_header_text_with_fallback(
            league_name, font, max_width, logo_width=0
        ):
            """Create header text that fits within the available width."""
            # Start with full text
            full_text = f"{league_name} - Game Line"
            text_width = font.getbbox(full_text)[2]

            # If it fits, use it
            if text_width <= max_width:
                return full_text

            # Try without " - Game Line" suffix
            short_text = league_name
            text_width = font.getbbox(short_text)[2]
            if text_width <= max_width:
                return short_text

            # Try with abbreviated suffix
            medium_text = f"{league_name} - GL"
            text_width = font.getbbox(medium_text)[2]
            if text_width <= max_width:
                return medium_text

            # If still too long, truncate the league name
            available_width = max_width - font.getbbox(" - GL")[2] - 10  # 10px buffer
            truncated_name = league_name
            while (
                truncated_name and font.getbbox(f"{truncated_name} - GL")[2] > max_width
            ):
                truncated_name = truncated_name[:-1]

            if truncated_name:
                return f"{truncated_name} - GL"
            else:
                return "Game Line"  # Fallback

        header_text = create_header_text_with_fallback(
            league, font_bold, available_text_width, logo_space
        )

        # Measure the final text width
        final_width = font_bold.getbbox(header_text)[2]

        print(f"  Original: {league}")
        print(f"  Final: {header_text}")
        print(f"  Width: {final_width}px / {available_text_width}px available")
        print(f"  Fits: {'✓' if final_width <= available_text_width else '✗'}")

        # Draw the text to visualize
        text_x = 24 + logo_space
        text_y = 25
        draw.text(
            (text_x, text_y), header_text, font=font_bold, fill="white", anchor="lt"
        )

        # Save test image
        output_path = f"test_title_{league.replace(' ', '_').lower()}.png"
        image.save(output_path)
        print(f"  Saved: {output_path}")


if __name__ == "__main__":
    test_dynamic_title_sizing()
    print("\nTest completed! Check the generated PNG files to see the results.")
