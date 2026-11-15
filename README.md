# Weather & Air Quality Data Pipeline

An automated end-to-end data pipeline that collects hourly weather and air-quality data for **Fouchana (Ben Arous, Tunisia)**, cleans it, stores it in a database, and visualizes it in a dashboard.

## Business Question
How do weather conditions (temperature, wind, humidity) affect air quality (PM2.5, PM10) in Fouchana, Ben Arous (Tunisia), and can we spot pollution trends over time?

## Data Source
[Open-Meteo](https://open-meteo.com) free APIs (no API key needed):
- **Weather API:** temperature (2 m), relative humidity (2 m), wind speed (10 m)
- **Air Quality API:** PM10 and PM2.5

## Tech Stack
| Layer | Tool | Status |
|---|---|---|
| Extract | Python, `requests` (retries, logging) | Done |
| Transform | pandas | Done |
| Load | SQLite via SQLAlchemy (upsert) | Done |
| Testing | pytest | Done |
| Automation | GitHub Actions | Planned (Sprint 3) |
| Analysis | SQL | Planned (Sprint 3) |
| Dashboard | Streamlit | Planned (Sprint 4) |

## Pipeline Overview
```
Extract (API) → Transform (pandas) → Load (SQLite) → Analyze (SQL) → Visualize (Streamlit)
   ✅ done         ✅ done            ✅ done          ⏳ Sprint 3      ⏳ Sprint 4
```

## Project Structure
```
weather-air-pipeline/
├── data/
│   ├── raw/            # raw API responses (JSON), not tracked by git
│   ├── sample/         # one example raw file
│   └── weather_air.db  # SQLite database, not tracked by git
├── src/
│   ├── config.py       # city, coordinates, API settings, paths
│   ├── extract.py      # calls both APIs and saves raw JSON
│   ├── transform.py    # cleans, validates, and merges the raw data
│   ├── load.py         # upserts clean rows into SQLite
│   └── pipeline.py     # runs extract -> transform -> load
├── sql/                # analysis queries (Sprint 3)
├── dashboard/          # Streamlit app (Sprint 4)
├── tests/
│   └── test_pipeline.py  # data-quality tests
├── docs/
│   └── retros.md       # sprint retrospectives
├── pytest.ini
├── requirements.txt
└── README.md
```

## Getting Started

**1. Clone and enter the project**
```bash
git clone https://github.com/<your-username>/weather-air-pipeline.git
cd weather-air-pipeline
```

**2. Create a virtual environment and install dependencies**
```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
pip install -r requirements.txt
```

**3. Run the full pipeline**
```bash
python src/pipeline.py
```

This fetches the data, saves raw JSON in `data/raw/`, cleans it, loads it into `data/weather_air.db`, and writes a log to `logs/pipeline.log`.

Example output:
```
2026-11-15 17:04:31 | INFO | Starting extraction for Fouchana
2026-11-15 17:04:32 | INFO | weather: saved 72 hourly rows to fouchana_weather_20261115T160432Z.json
2026-11-15 17:04:39 | INFO | air_quality: saved 72 hourly rows to fouchana_air_quality_20261115T160439Z.json
2026-11-15 17:04:39 | INFO | Extraction finished successfully
2026-11-15 17:04:39 | INFO | Transformed 72 rows (2026-11-13 00:00:00 to 2026-11-15 23:00:00)
2026-11-15 17:04:39 | INFO | Upserted 72 rows into weather_air.db
2026-11-15 17:04:39 | INFO | Pipeline finished successfully
```

**4. Run the tests**
```bash
python -m pytest
```

## Configuration
All settings live in `src/config.py`. To analyze another city, change one line:
```python
CITY = {"name": "Fouchana", "latitude": 36.70, "longitude": 10.17}
```

## How the Pipeline Works

**Extract** (`extract.py`)
- Requests the last 2 days plus today (72 hourly rows), so a missed run leaves no gaps.
- Retries up to 3 times on temporary server errors (429, 5xx) with increasing delays.
- Validates that each response contains hourly data.
- Exits with a non-zero code on failure, so GitHub Actions can flag a failed run.

**Transform** (`transform.py`)
- Reads the newest raw file for each source and removes duplicate timestamps.
- Merges weather and air quality on the timestamp (one-to-one join).
- Sets physically implausible values to NULL (for example humidity above 100%).
- Keeps missing values as NULL instead of imputing them.
- Adds an `is_forecast` flag for hours that had not happened yet at run time.

**Load** (`load.py`)
- Writes to the `hourly_readings` table with primary key `(city, observed_at)`.
- Uses an upsert (insert, or update if the row exists), so rerunning the pipeline never creates duplicates and forecast rows get refreshed with newer values.

## Data Dictionary (table `hourly_readings`)
| Column | Description |
|---|---|
| city | City name |
| observed_at | Local time (Africa/Tunis, UTC+1) |
| temperature_c | Air temperature at 2 m (°C) |
| humidity_pct | Relative humidity (%) |
| wind_kmh | Wind speed at 10 m (km/h) |
| pm10, pm2_5 | Particulate matter (µg/m³) |
| is_forecast | 1 if the hour was still in the future when loaded, otherwise 0 |
| updated_at | UTC time of the last write |

## Data Quality Tests
`tests/test_pipeline.py` checks that:
- duplicate timestamps are removed
- out-of-range values become NULL
- the output has the expected columns and is sorted by time
- loading the same data twice does not create duplicate rows

## Methodology
Built with Agile in 1-week sprints, tracked on the GitHub project board. Retrospectives are in [`docs/retros.md`](docs/retros.md).

| Sprint | Goal | Status |
|---|---|---|
| 0 | Setup, user stories, API test | Done |
| 1 | Extract: API calls, retries, logging, raw storage | Done |
| 2 | Transform & load: cleaning, database, tests | Done |
| 3 | Automation (GitHub Actions) & SQL analysis | Planned |
| 4 | Dashboard & polish | Planned |

**Sprint 2 demo:** `python src/pipeline.py` loads 72 rows, a second run still gives 72 rows (no duplicates), and `pytest` shows 4 passed.

## Limitations
- Air-quality values are model-based estimates, not ground-sensor measurements.
- Weather and air quality come from slightly different grid points (about 2-3 km apart).
- Timestamps are in local time (Africa/Tunis, UTC+1).
- Hours that were still in the future at run time are forecasts, flagged with `is_forecast = 1`. Exclude them from the analysis.
- Missing values are kept as NULL, not imputed.
- Only a few days of data exist so far, so no conclusions can be drawn yet.

## Key Findings
Coming soon (Sprint 3), once the pipeline has collected enough data.