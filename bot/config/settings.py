import os

import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "..", "config", "settings.yaml"
)

with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)

API_KEY = os.getenv("API_KEY")


def get_config():
    return CONFIG
