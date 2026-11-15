import logging
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import config

logger = logging.getLogger(__name__)

MAX_AGE_HOURS = 36
LOCAL_TZ = ZoneInfo("Africa/Tunis")


class CheckFailed(Exception):
    pass


def check_freshness(con):
    newest = con.execute(
        "SELECT MAX(observed_at) FROM hourly_readings WHERE is_forecast = 0"
    ).fetchone()[0]
    if newest is None:
        raise CheckFailed("No observed rows in hourly_readings")
    newest_dt = datetime.strptime(newest, "%Y-%m-%d %H:%M:%S")
    # observed_at is local time (UTC+1); the 1 h error is irrelevant for a 36 h limit
    now = datetime.now(LOCAL_TZ).replace(tzinfo=None)
    age_h = (now - newest_dt).total_seconds() / 3600
    if age_h > MAX_AGE_HOURS:
        raise CheckFailed(f"Newest observed hour is {age_h:.0f} h old (limit {MAX_AGE_HOURS} h)")
    logger.info("Freshness OK: newest observed hour %s (%.1f h old)", newest, age_h)
    return age_h


def check_row_count(con):
    total = con.execute("SELECT COUNT(*) FROM hourly_readings").fetchone()[0]
    try:
        previous = con.execute(
            "SELECT rows_total FROM pipeline_runs WHERE status = 'success' "
            "ORDER BY run_id DESC LIMIT 1"
        ).fetchone()
    except sqlite3.OperationalError:  # no run log yet (first run)
        previous = None
    if previous and previous[0] is not None and total < previous[0]:
        raise CheckFailed(f"Row count dropped from {previous[0]} to {total}")
    logger.info("Row count OK: %d rows", total)


def run_all():
    con = sqlite3.connect(config.DB_PATH)
    try:
        check_freshness(con)
        check_row_count(con)
    finally:
        con.close()
