#!/usr/bin/env python3
"""
Test script to check encoding issues with special characters in player names.
"""


def create_safe_filename(player_name):
    """Create a safe filename from player name."""
    # Create safe filename - handle special characters properly
    safe_name = player_name.lower().replace(" ", "_")
    # Handle special characters and accents
    replacements = {
        "ć": "c",
        "ś": "s",
        "ń": "n",
        "ó": "o",
        "ł": "l",
        "ż": "z",
        "ź": "z",
        "á": "a",
        "é": "e",
        "í": "i",
        "ú": "u",
        "ý": "y",
        "à": "a",
        "è": "e",
        "ì": "i",
        "ò": "o",
        "ù": "u",
        "â": "a",
        "ê": "e",
        "î": "i",
        "ô": "o",
        "û": "u",
        "ä": "a",
        "ë": "e",
        "ï": "i",
        "ö": "o",
        "ü": "u",
        "ã": "a",
        "ñ": "n",
        "õ": "o",
        "ç": "c",
        "ă": "a",
        "ș": "s",
        "ț": "t",
        "î": "i",
        "š": "s",
        "č": "c",
        "ř": "r",
        "ž": "z",
        "ě": "e",
        "ů": "u",
        "ň": "n",
        "ď": "d",
        "ť": "t",
        "ľ": "l",
    }
    for old, new in replacements.items():
        safe_name = safe_name.replace(old, new)
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    return safe_name


def test_player_names():
    """Test various player names with special characters."""
    test_names = [
        "Ons Jabeur",
        "Iga Świątek",
        "Aryna Sabalenka",
        "Markéta Vondroušová",
        "Karolína Muchová",
        "Barbora Krejčíková",
        "Veronika Kudermetova",
        "Liudmila Samsonova",
        "Victoria Azarenka",
        "Petra Kvitová",
        "Caroline Garcia",
        "Beatriz Haddad Maia",
        "Elina Svitolina",
    ]

    print("Testing player name encoding:")
    print("=" * 50)

    for name in test_names:
        safe_name = create_safe_filename(name)
        print(f"Original: {name}")
        print(f"Safe:     {safe_name}.png")
        print("-" * 30)


if __name__ == "__main__":
    test_player_names()
