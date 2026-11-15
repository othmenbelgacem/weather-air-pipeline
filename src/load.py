import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

import config

logger = logging.getLogger(__name__)

COLUMNS = [
    "city",
    "observed_at",
    "temperature_c",
    "humidity_pct",
    "wind_kmh",
    "pm10",
    "pm2_5",
    "is_forecast",
]

DDL = """
CREATE TABLE IF NOT EXISTS hourly_readings (
    city          TEXT    NOT NULL,
    observed_at   TEXT    NOT NULL,   -- local time, YYYY-MM-DD HH:MM:SS
    temperature_c REAL,
    humidity_pct  REAL,
    wind_kmh      REAL,
    pm10          REAL,
    pm2_5         REAL,
    is_forecast   INTEGER NOT NULL,   -- 1 = model forecast, 0 = past hour
    updated_at    TEXT    NOT NULL,   -- UTC time of last write
    PRIMARY KEY (city, observed_at)
)
"""

UPSERT = """
INSERT INTO hourly_readings
    (city, observed_at, temperature_c, humidity_pct, wind_kmh, pm10, pm2_5, is_forecast, updated_at)
VALUES
        (
        :city,
        :observed_at,
        :temperature_c,
        :humidity_pct,
        :wind_kmh,
        :pm10,
        :pm2_5,
        :is_forecast,
        :updated_at
    )
ON CONFLICT (city, observed_at) DO UPDATE SET
    temperature_c = excluded.temperature_c,
    humidity_pct  = excluded.humidity_pct,
    wind_kmh      = excluded.wind_kmh,
    pm10          = excluded.pm10,
    pm2_5         = excluded.pm2_5,
    is_forecast   = excluded.is_forecast,
    updated_at    = excluded.updated_at
"""
RUNS_DDL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      TEXT NOT NULL,   -- UTC
    duration_s      REAL,
    status          TEXT NOT NULL,   -- success | failed
    rows_loaded     INTEGER,
    rows_total      INTEGER,
    newest_observed TEXT,
    error           TEXT
)
"""


def log_run(
    started_at,
    duration_s,
    status,
    rows_loaded=None,
    rows_total=None,
    newest_observed=None,
    error=None,
    db_path=None,
):
    db_path = db_path or config.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.execute(text(RUNS_DDL))
        conn.execute(
            text(
                "INSERT INTO pipeline_runs (started_at, duration_s, status, rows_loaded, "
                "rows_total, newest_observed, error) VALUES (:started_at, :duration_s, "
                ":status, :rows_loaded, :rows_total, :newest_observed, :error)"
            ),
            {
                "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_s": round(duration_s, 2),
                "status": status,
                "rows_loaded": rows_loaded,
                "rows_total": rows_total,
                "newest_observed": newest_observed,
                "error": error,
            },
        )


def load(df, db_path=None):
    db_path = db_path or config.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")

    out = df[COLUMNS].copy()
    out["observed_at"] = out["observed_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
    out["is_forecast"] = out["is_forecast"].astype(int)
    out["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    out = out.astype(object).where(out.notna(), None)  # NaN -> NULL

    with engine.begin() as conn:
        conn.execute(text(DDL))
        conn.execute(text(UPSERT), out.to_dict("records"))
        total = conn.execute(text("SELECT COUNT(*) FROM hourly_readings")).scalar()
    logger.info("Upserted %d rows into %s (%d rows in table)", len(out), db_path.name, total)
    return len(out), total
