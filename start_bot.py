#!/usr/bin/env python3
"""
Proper bot startup script that handles import paths correctly
"""

import sys
import os
from pathlib import Path

# Add the bot directory to Python path
bot_dir = Path(__file__).parent / "bot"
sys.path.insert(0, str(bot_dir))

# Change to bot directory
os.chdir(bot_dir)

# Now import and run the main bot
from main import main

if __name__ == "__main__":
    main() 