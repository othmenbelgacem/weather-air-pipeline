import pandas as pd
from sqlalchemy import create_engine, text

import load
import transform

TZ = "Africa/Tunis"


def make_frames():
    # Note the duplicated 01:00 row
    times = pd.to_datetime(["2026-11-13 00:00", "2026-11-13 01:00", "2026-11-13 01:00"])
    weather = pd.DataFrame(
        {
            "time": times,
            "temperature_2m": [19.1, 18.7, 18.7],
            "relative_humidity_2m": [70, 72, 72],
            "wind_speed_10m": [4.3, 5.2, 5.2],
        }
    )
    air = pd.DataFrame(
        {
            "time": times,
            "pm10": [21.4, 18.5, 18.5],
            "pm2_5": [8.3, 7.2, 7.2],
        }
    )
    return weather, air


def test_no_duplicate_timestamps():
    df = transform.clean(*make_frames(), TZ)
    assert df["observed_at"].is_unique
    assert len(df) == 2


def test_out_of_range_values_become_null():
    weather, air = make_frames()
    weather.loc[0, "relative_humidity_2m"] = 250
    air.loc[0, "pm2_5"] = -5
    df = transform.clean(weather, air, TZ)
    assert pd.isna(df.loc[0, "humidity_pct"])
    assert pd.isna(df.loc[0, "pm2_5"])


def test_expected_columns_and_sorted():
    df = transform.clean(*make_frames(), TZ)
    for col in [
        "city",
        "observed_at",
        "temperature_c",
        "humidity_pct",
        "wind_kmh",
        "pm10",
        "pm2_5",
        "is_forecast",
    ]:
        assert col in df.columns
    assert df["observed_at"].is_monotonic_increasing


def test_load_twice_does_not_duplicate(tmp_path):
    df = transform.clean(*make_frames(), TZ)
    db = tmp_path / "test.db"
    load.load(df, db_path=db)
    load.load(df, db_path=db)
    with create_engine(f"sqlite:///{db}").connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM hourly_readings")).scalar()
    assert count == 2
