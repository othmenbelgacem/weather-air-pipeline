import json
import logging
import sys
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config

logger = logging.getLogger(__name__)


def setup_logging():
    config.LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.LOG_DIR / "pipeline.log"),
        ],
    )


def build_session():
    """Session that retries on temporary server errors with increasing delays."""
    retry = Retry(
        total=3,
        backoff_factor=1,  # waits 1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch(session, url, hourly_vars):
    params = {
        "latitude": config.CITY["latitude"],
        "longitude": config.CITY["longitude"],
        "hourly": hourly_vars,
        "past_days": config.PAST_DAYS,
        "forecast_days": config.FORECAST_DAYS,
        "timezone": config.TIMEZONE,
    }
    response = session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if "hourly" not in data:
        raise ValueError(f"Unexpected API response: missing 'hourly' key ({url})")
    return data


def save_raw(data, source):
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    city = config.CITY["name"].lower().replace(" ", "_")
    path = config.RAW_DIR / f"{city}_{source}_{stamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def main():
    setup_logging()
    logger.info("Starting extraction for %s", config.CITY["name"])

    sources = {
        "weather": (config.WEATHER_URL, config.WEATHER_VARS),
        "air_quality": (config.AIR_QUALITY_URL, config.AIR_QUALITY_VARS),
    }

    session = build_session()
    failures = 0

    for source, (url, variables) in sources.items():
        try:
            data = fetch(session, url, variables)
            path = save_raw(data, source)
            rows = len(data["hourly"]["time"])
            logger.info("%s: saved %d hourly rows to %s", source, rows, path.name)
        except (requests.RequestException, ValueError) as e:
            failures += 1
            logger.error("%s: extraction failed: %s", source, e)

    if failures:
        logger.error("Extraction finished with %d failure(s)", failures)
        sys.exit(1)  # non-zero exit lets GitHub Actions flag the run as failed

    logger.info("Extraction finished successfully")


if __name__ == "__main__":
    main()