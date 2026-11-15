import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import config  # noqa: E402

WHO_PM25, WHO_PM10 = 15, 45  # WHO 24-hour guideline values (ug/m3)
WEATHER = {
    "Wind speed (km/h)": "wind_kmh",
    "Temperature (°C)": "temperature_c",
    "Humidity (%)": "humidity_pct",
}
POLLUTANT = {"PM2.5": "pm2_5", "PM10": "pm10"}

st.set_page_config(page_title="Fouchana air quality", page_icon="🌫️", layout="wide")


@st.cache_data
def load_data(db_path: str, modified: float) -> pd.DataFrame:
    # 'modified' is part of the cache key, so a new database file refreshes the data
    con = sqlite3.connect(db_path)
    df = pd.read_sql(
        "SELECT * FROM hourly_readings WHERE is_forecast = 0",
        con, parse_dates=["observed_at"],
    )
    con.close()
    return df


if not config.DB_PATH.exists():
    st.error(f"No database at {config.DB_PATH}. Run `python src/pipeline.py` first.")
    st.stop()

df = load_data(str(config.DB_PATH), config.DB_PATH.stat().st_mtime)
if df.empty:
    st.warning("The database has no observed rows yet.")
    st.stop()

# ---------- Sidebar: date filter ----------
st.sidebar.header("Filters")
min_d, max_d = df["observed_at"].min().date(), df["observed_at"].max().date()
picked = st.sidebar.date_input(
    "Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d
)
start, end = (picked[0], picked[1]) if len(picked) == 2 else (picked[0], picked[0])
day = df["observed_at"].dt.date
view = df[(day >= start) & (day <= end)]
if view.empty:
    st.warning("No data in this date range.")
    st.stop()

st.sidebar.caption(
    f"{len(view):,} observed hours selected. Forecast hours are excluded "
    "(`is_forecast = 0`)."
)

# ---------- Header ----------
city = view["city"].iloc[0]
st.title(f"Air quality vs. weather in {city}")
st.caption(
    f"Hourly data from Open-Meteo, {start} to {end}. "
    "Air-quality values are modelled concentrations, not sensor measurements."
)

# ---------- Daily table and KPIs ----------
daily = view.groupby(view["observed_at"].dt.floor("D")).agg(
    pm2_5=("pm2_5", "mean"), pm10=("pm10", "mean"), hours=("pm2_5", "size")
)
complete = daily[daily["hours"] >= 20]  # only (nearly) complete days
over = complete[(complete["pm2_5"] > WHO_PM25) | (complete["pm10"] > WHO_PM10)]
corr_wind = view[["wind_kmh", "pm2_5"]].corr(method="spearman").iloc[0, 1]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Average PM2.5", f"{view['pm2_5'].mean():.1f} µg/m³")
k2.metric("Peak hourly PM2.5", f"{view['pm2_5'].max():.1f} µg/m³")
k3.metric("Days above WHO guideline", f"{len(over)} of {len(complete)}")
k4.metric("Wind vs PM2.5 (Spearman)", f"{corr_wind:.2f}")
k5.metric("Hours in sample", f"{len(view):,}")

tab1, tab2, tab3 = st.tabs(["Daily trend", "Daily cycle", "Weather vs pollution"])

# ---------- Tab 1: daily trend ----------
with tab1:
    st.subheader("Daily average PM2.5 and PM10")
    trend = daily[["pm2_5", "pm10"]].rename(columns={"pm2_5": "PM2.5", "pm10": "PM10"})
    trend["WHO PM2.5 guideline (15)"] = WHO_PM25
    trend["WHO PM10 guideline (45)"] = WHO_PM10
    st.line_chart(trend)
    st.caption("Guideline lines are the WHO 24-hour values. Days with fewer than 20 hours "
               "are shown in the chart but not counted in the KPI.")

# ---------- Tab 2: hour of day ----------
with tab2:
    st.subheader("Typical day: average by hour")
    hour = view["observed_at"].dt.hour
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Particulate matter (µg/m³)**")
        st.line_chart(view.groupby(hour)[["pm2_5", "pm10"]].mean()
                      .rename(columns={"pm2_5": "PM2.5", "pm10": "PM10"}))
    with c2:
        st.markdown("**Wind (km/h) and temperature (°C)**")
        st.line_chart(view.groupby(hour)[["wind_kmh", "temperature_c"]].mean()
                      .rename(columns={"wind_kmh": "Wind", "temperature_c": "Temperature"}))
    st.caption("Pollution is lowest when wind peaks in the afternoon. Wind and time of day "
               "move together, so this view cannot separate them.")

# ---------- Tab 3: weather vs pollution ----------
with tab3:
    st.subheader("Pollution by wind speed")
    bins = [0, 5, 10, 20, float("inf")]
    labels = ["1. calm (<5)", "2. light (5-10)", "3. moderate (10-20)", "4. strong (20+)"]
    banded = view.assign(wind_band=pd.cut(view["wind_kmh"], bins=bins, labels=labels, right=False))
    bands = banded.groupby("wind_band", observed=True).agg(**{
        "hours": ("pm2_5", "size"), "PM2.5": ("pm2_5", "mean"), "PM10": ("pm10", "mean"),
    })
    bands.index = bands.index.astype(str)
    c1, c2 = st.columns([2, 1])
    c1.bar_chart(bands[["PM2.5", "PM10"]], stack=False)
    c2.dataframe(bands.round(1))
    if (bands["hours"] < 50).any():
        st.caption("Bands with fewer than 50 hours are unreliable on their own.")

    st.subheader("Explore a pair")
    s1, s2 = st.columns(2)
    w_label = s1.selectbox("Weather variable", list(WEATHER))
    p_label = s2.selectbox("Pollutant", list(POLLUTANT))
    st.scatter_chart(view, x=WEATHER[w_label], y=POLLUTANT[p_label])

    st.subheader("Spearman correlation")
    cols = list(WEATHER.values()) + list(POLLUTANT.values())
    corr = view[cols].corr(method="spearman").loc[list(WEATHER.values()), list(POLLUTANT.values())]
    corr.index = list(WEATHER)
    corr.columns = list(POLLUTANT)
    st.dataframe(corr.round(2))
    st.caption("Correlation is not causation. Season, traffic, and dust episodes can move "
               "weather and pollution together.")

st.divider()
st.caption(f"Database last updated (UTC): {df['updated_at'].max()} | "
           "Source: Open-Meteo | Pipeline: GitHub Actions, daily")