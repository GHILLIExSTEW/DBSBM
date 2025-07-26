import os

import yaml

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "..", "config", "image_settings.yaml"
)

with open(CONFIG_PATH, "r") as f:
    IMAGE_CONFIG = yaml.safe_load(f)

# Export constants for direct import
BACKGROUND_COLOR = IMAGE_CONFIG["colors"]["background"]
DEFAULT_PADDING = IMAGE_CONFIG["padding"]["default"]
IMAGE_WIDTH = IMAGE_CONFIG["image"]["width"]
IMAGE_HEIGHT = IMAGE_CONFIG["image"]["height"]
LOGO_SIZE = IMAGE_CONFIG["logo_size"]
HEADER_FONT_SIZE = IMAGE_CONFIG["font_sizes"]["header"]
TEAM_FONT_SIZE = IMAGE_CONFIG["font_sizes"]["team"]
VS_FONT_SIZE = IMAGE_CONFIG["font_sizes"]["vs"]
LINE_FONT_SIZE = IMAGE_CONFIG["font_sizes"]["line"]
ODDS_FONT_SIZE = IMAGE_CONFIG["font_sizes"]["odds"]
RISK_FONT_SIZE = IMAGE_CONFIG["font_sizes"]["risk"]
FOOTER_FONT_SIZE = IMAGE_CONFIG["font_sizes"]["footer"]


def get_image_config():
    return IMAGE_CONFIG
