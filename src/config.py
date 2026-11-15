from pathlib import Path


CITY = {"name": "Fouchana", "latitude": 36.70, "longitude": 10.17}

# --- API settings ---
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

WEATHER_VARS = "temperature_2m,relative_humidity_2m,wind_speed_10m"
AIR_QUALITY_VARS = "pm10,pm2_5"

PAST_DAYS = 2        
FORECAST_DAYS = 1
TIMEZONE = "auto"
REQUEST_TIMEOUT = 15

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
LOG_DIR = BASE_DIR / "logs"
DB_PATH = BASE_DIR / "data" / "weather_air.db"