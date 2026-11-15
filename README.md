# Weather & Air Quality Data Pipeline

An automated end-to-end data pipeline that collects daily weather and air-quality data, cleans it, stores it in a database, and visualizes it in a dashboard.

## Business Question
How do weather conditions (temperature, wind, humidity) affect air quality (PM2.5, PM10) in [YOUR CITY], and can we spot pollution trends over time?

## Tech Stack
- **Language:** Python (requests, pandas, SQLAlchemy)
- **Database:** SQLite / PostgreSQL
- **Automation:** GitHub Actions
- **Testing:** pytest
- **Dashboard:** Streamlit
- **Data source:** Open-Meteo Weather & Air Quality APIs

## Pipeline Overview
Extract (API) → Transform (pandas) → Load (database) → Analyze (SQL) → Visualize (Streamlit)

## Project Structure
```
data/        raw and sample data
src/         extract.py, transform.py, load.py
sql/         analysis queries
dashboard/   Streamlit app
tests/       data-quality tests
docs/        retrospectives
```

## Methodology
Built using Agile in 1-week sprints. Progress is tracked on the project board, and retrospectives are in `docs/retros.md`.

## Status
Sprint 0: setup complete. Sprint 1 (Extract): in progress.

## Key Findings
Coming soon.