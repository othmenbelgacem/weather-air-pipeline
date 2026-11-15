import sqlite3
import sys

sys.path.insert(0, "src")
import config

con = sqlite3.connect(config.DB_PATH)
print(config.DB_PATH)
print(con.execute(
    "SELECT COUNT(*), MIN(observed_at), MAX(observed_at) FROM hourly_readings"
).fetchone())
print(con.execute(
    "SELECT is_forecast, COUNT(*) FROM hourly_readings GROUP BY is_forecast"
).fetchall())