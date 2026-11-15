import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import pytest

import checks
import transform
import validation

TZ = "Africa/Tunis"


def make_clean(n=48):
    times = pd.date_range("2026-11-01", periods=n, freq="h")
    weather = pd.DataFrame(
        {
            "time": times,
            "temperature_2m": 20.0,
            "relative_humidity_2m": 60,
            "wind_speed_10m": 5.0,
        }
    )
    air = pd.DataFrame({"time": times, "pm10": 15.0, "pm2_5": 8.0})
    return transform.clean(weather, air, TZ)


def test_valid_data_passes():
    assert len(validation.validate(make_clean())) == 48


def test_gap_in_timestamps_fails():
    with pytest.raises(validation.DataQualityError):
        validation.validate(make_clean().drop(index=10))


def test_too_many_nulls_fails():
    df = make_clean()
    df["pm2_5"] = float("nan")
    with pytest.raises(validation.DataQualityError):
        validation.validate(df)


def test_too_few_rows_fails():
    with pytest.raises(validation.DataQualityError):
        validation.validate(make_clean(n=10))


def _db(tmp_path, hours_ago):
    con = sqlite3.connect(tmp_path / "t.db")
    con.execute("CREATE TABLE hourly_readings (observed_at TEXT, is_forecast INTEGER)")
    ts = datetime.now(checks.LOCAL_TZ).replace(tzinfo=None) - timedelta(hours=hours_ago)
    con.execute("INSERT INTO hourly_readings VALUES (?, 0)", (ts.strftime("%Y-%m-%d %H:%M:%S"),))
    con.commit()
    return con


def test_fresh_data_passes(tmp_path):
    age = checks.check_freshness(_db(tmp_path, hours_ago=2))
    assert 1.9 < age < 2.1


def test_stale_data_fails(tmp_path):
    with pytest.raises(checks.CheckFailed):
        checks.check_freshness(_db(tmp_path, hours_ago=100))


def test_row_count_drop_fails(tmp_path):
    con = _db(tmp_path, hours_ago=1)
    con.execute(
        """
    CREATE TABLE pipeline_runs (
        run_id INTEGER PRIMARY KEY,
        status TEXT,
        rows_total INTEGER
    )
    """
    )
    con.execute("INSERT INTO pipeline_runs (status, rows_total) VALUES ('success', 500)")
    with pytest.raises(checks.CheckFailed):
        checks.check_row_count(con)
