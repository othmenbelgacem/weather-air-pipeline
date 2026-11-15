import json
import logging

import numpy as np
import pandas as pd

import config

logger = logging.getLogger(__name__)

RENAME = {
    "time": "observed_at",
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "humidity_pct",
    "wind_speed_10m": "wind_kmh",
}

# Physically plausible limits; values outside become NULL
VALID_RANGES = {
    "temperature_c": (-50, 60),
    "humidity_pct": (0, 100),
    "wind_kmh": (0, 200),
    "pm10": (0, 1000),
    "pm2_5": (0, 1000),
}


def latest_raw_file(source):
    city = config.CITY["name"].lower().replace(" ", "_")
    files = sorted(config.RAW_DIR.glob(f"{city}_{source}_*.json"))
    if not files:
        raise FileNotFoundError(f"No raw {source} file found in {config.RAW_DIR}")
    return files[-1]  # timestamp in the filename makes the last one the newest


def read_raw(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df, data["timezone"]


def clean(weather, air, tz):
    # Drop duplicates BEFORE merging, otherwise the join multiplies rows
    weather = weather.drop_duplicates(subset="time", keep="last")
    air = air.drop_duplicates(subset="time", keep="last")

    df = weather.merge(air, on="time", how="outer", validate="one_to_one")
    df = df.rename(columns=RENAME)

    for col, (low, high) in VALID_RANGES.items():
        df[col] = pd.to_numeric(df[col], errors="coerce")
        invalid = df[col].notna() & ~df[col].between(low, high)
        if invalid.any():
            logger.warning("%s: %d out-of-range value(s) set to NULL", col, invalid.sum())
            df.loc[invalid, col] = np.nan

    df = df.sort_values("observed_at").reset_index(drop=True)

    # Hours that haven't happened yet are model forecasts, not observations
    now_local = pd.Timestamp.now(tz=tz).tz_localize(None)
    df["is_forecast"] = df["observed_at"] > now_local

    df.insert(0, "city", config.CITY["name"])

    missing = df[list(VALID_RANGES)].isna().sum()
    for col, n in missing[missing > 0].items():
        logger.warning("%s: %d missing value(s) kept as NULL", col, n)
    return df


def run():
    weather, tz = read_raw(latest_raw_file("weather"))
    air, _ = read_raw(latest_raw_file("air_quality"))
    df = clean(weather, air, tz)
    logger.info(
        "Transformed %d rows (%s to %s)",
        len(df), df["observed_at"].min(), df["observed_at"].max(),
    )
    return df