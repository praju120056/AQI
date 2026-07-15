import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# MongoDB connection string.
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# OpenWeatherMap API key
OWM_API_KEY = os.getenv("OWM_API_KEY", "")
