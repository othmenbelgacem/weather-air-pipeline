import sqlite3

con = sqlite3.connect("data/weather_air.db")
print(con.execute(
    "SELECT COUNT(*), MIN(observed_at), MAX(observed_at) FROM hourly_readings"
).fetchone())
for row in con.execute("SELECT * FROM hourly_readings ORDER BY observed_at DESC LIMIT 3"):
    print(row)
    print(con.execute(
    "SELECT is_forecast, COUNT(*) FROM hourly_readings GROUP BY is_forecast"
).fetchall())