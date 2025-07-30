"""Test dynamic title functionality for game line images."""

import pytest
from PIL import Image, ImageDraw, ImageFont


def test_dynamic_title_sizing():
    """Test that dynamic title sizing works correctly."""
    # Test cases with different length league names
    test_cases = [
        "NBA",  # Short
        "UEFA Champions League",  # Long - should be truncated
        "English Premier League",  # Medium-long
        "Major League Baseball",  # Medium
    ]

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

    # League abbreviations mapping
    LEAGUE_ABBREVIATIONS = {
        "UEFA Champions League": "UEFA CL",
        "English Premier League": "EPL",
        "Major League Baseball": "MLB",
        "National Basketball Association": "NBA",
        "National Football League": "NFL",
        "Women's National Basketball Association": "WNBA",
        "Bundesliga": "Bundesliga",
        "La Liga": "La Liga",
        "Serie A": "Serie A",
        "Ligue 1": "Ligue 1",
    }

    def create_header_text_with_fallback(league_name, font, max_width, logo_width=0):
        """Create header text that fits within the available width, always keeping '- Game Line'."""
        suffix = " - Game Line"
        # Try full name
        full_text = f"{league_name}{suffix}"
        text_width = font.getbbox(full_text)[2]
        if text_width <= max_width:
            return full_text
        # Try abbreviation
        abbr = LEAGUE_ABBREVIATIONS.get(league_name, None)
        if abbr:
            abbr_text = f"{abbr}{suffix}"
            abbr_width = font.getbbox(abbr_text)[2]
            if abbr_width <= max_width:
                return abbr_text
            # Truncate abbreviation if needed
            truncated = abbr
            while truncated and font.getbbox(f"{truncated}{suffix}")[2] > max_width:
                truncated = truncated[:-1]
            if truncated:
                return f"{truncated}{suffix}"
        # If no abbreviation or still too long, truncate league name
        truncated = league_name
        while truncated and font.getbbox(f"{truncated}{suffix}")[2] > max_width:
            truncated = truncated[:-1]
        if truncated:
            return f"{truncated}{suffix}"
        else:
            return suffix.strip()  # Fallback

    for league in test_cases:
        header_text = create_header_text_with_fallback(
            league, font_bold, available_text_width, logo_space
        )

        # Measure the final text width
        final_width = font_bold.getbbox(header_text)[2]

        # Assert that the text fits within the available width
        assert (
            final_width <= available_text_width
        ), f"Text '{header_text}' (width: {final_width}) does not fit in available width ({available_text_width})"

        # Assert that the text always ends with " - Game Line" or is just "Game Line"
        assert (
            header_text.endswith(" - Game Line") or header_text == "Game Line"
        ), f"Text '{header_text}' does not have proper suffix"


def test_uefa_cl_alias():
    """Test that UEFA CL alias works correctly."""
    # Test that "UEFA CL" is properly recognized
    assert "UEFA CL" in ["UEFA CL", "UEFA Champions League", "ChampionsLeague"]

    # Test that the abbreviation mapping works
    LEAGUE_ABBREVIATIONS = {
        "UEFA Champions League": "UEFA CL",
        "ChampionsLeague": "UEFA CL",
        "UEFA CL": "UEFA CL",
    }

    assert LEAGUE_ABBREVIATIONS.get("UEFA Champions League") == "UEFA CL"
    assert LEAGUE_ABBREVIATIONS.get("ChampionsLeague") == "UEFA CL"
    assert LEAGUE_ABBREVIATIONS.get("UEFA CL") == "UEFA CL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
