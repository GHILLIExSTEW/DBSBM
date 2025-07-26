import os

import yaml

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "..", "config", "image_settings.yaml"
)

with open(CONFIG_PATH, "r") as f:
    IMAGE_CONFIG = yaml.safe_load(f)


def get_image_config():
    return IMAGE_CONFIG
