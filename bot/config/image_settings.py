import os

import yaml

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "..", "config", "image_settings.yaml"
)

with open(CONFIG_PATH, "r") as f:
    IMAGE_CONFIG = yaml.safe_load(f)

# Export constants for direct import
BACKGROUND_COLOR = IMAGE_CONFIG["colors"]["background"]

# Add other relevant constants as needed, e.g.:
# IMAGE_WIDTH = IMAGE_CONFIG['image']['width']
# IMAGE_HEIGHT = IMAGE_CONFIG['image']['height']


def get_image_config():
    return IMAGE_CONFIG
