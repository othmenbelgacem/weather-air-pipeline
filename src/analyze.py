import sqlite3

import pandas as pd

import config


def main():
    if not config.DB_PATH.exists():
        print(f"No database at {config.DB_PATH}. Run the pipeline first.")
        return

    con = sqlite3.connect(config.DB_PATH)
    df = pd.read_sql("SELECT * FROM hourly_readings WHERE is_forecast = 0", con)
    if df.empty:
        print("No observed rows yet.")
        return
    print(f"Observed rows: {len(df)} | days: {df['observed_at'].str[:10].nunique()}")

    # 1. Run every SQL file in sql/
    for path in sorted((config.BASE_DIR / "sql").glob("*.sql")):
        print(f"\n=== {path.name} ===")
        result = pd.read_sql(path.read_text(encoding="utf-8"), con)
        print(result.to_string(index=False) if not result.empty else "(no rows)")

    # 2. Correlations (Spearman suits skewed pollution data)
    weather = ["temperature_c", "humidity_pct", "wind_kmh"]
    pollutants = ["pm10", "pm2_5"]
    corr = df[weather + pollutants].corr(method="spearman")
    print("\n=== Spearman correlation: weather vs particulate matter ===")
    print(corr.loc[weather, pollutants].round(2))

    con.close()


if __name__ == "__main__":
    main()