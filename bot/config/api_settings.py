import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_ENABLED = os.getenv("API_ENABLED", "false").lower() == "true"

# API Hosts
API_HOSTS = {
    # Football (Soccer)
    "football": "https://v3.football.api-sports.io",
    "soccer": "https://v3.football.api-sports.io",
    # Basketball
    "basketball": "https://v1.basketball.api-sports.io",
    "nba": "https://v1.basketball.api-sports.io",
    # Baseball
    "baseball": "https://v1.baseball.api-sports.io",
    "mlb": "https://v1.baseball.api-sports.io",
    # American Football
    "american-football": "https://v1.american-football.api-sports.io",
    "nfl": "https://v1.american-football.api-sports.io",
    # Hockey
    "hockey": "https://v1.hockey.api-sports.io",
    "nhl": "https://v1.hockey.api-sports.io",
    # Tennis
    "tennis": "https://v1.tennis.api-sports.io",
    # Rugby
    "rugby": "https://v1.rugby.api-sports.io",
    # Volleyball
    "volleyball": "https://v1.volleyball.api-sports.io",
    # Handball
    "handball": "https://v1.handball.api-sports.io",
    # Cricket
    "cricket": "https://v1.cricket.api-sports.io",
    # Boxing
    "boxing": "https://v1.boxing.api-sports.io",
    # MMA
    "mma": "https://v1.mma.api-sports.io",
    # Formula 1
    "formula-1": "https://v1.formula-1.api-sports.io",
    "f1": "https://v1.formula-1.api-sports.io",
    # Golf
    "golf": "https://v1.golf.api-sports.io",
    # Cycling
    "cycling": "https://v1.cycling.api-sports.io",
}

# API Key
API_KEY = os.getenv("API_KEY")

# API Timeouts and Retries
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
API_RETRY_ATTEMPTS = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
API_RETRY_DELAY = int(os.getenv("API_RETRY_DELAY", "5"))
