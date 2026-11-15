# Sprint Retrospectives

## Sprint 0: Setup
**Dates:** [start] to [end]
**Goal:** Define the business question, set up the repo and board, and confirm the API works.

**Went well**
- The Open-Meteo API needs no key, and the first test call returned data right away.
- Writing user stories and acceptance criteria up front made the later sprints easy to plan.

**Didn't go well**
- I saved the API test script in `tests/`, where pytest would pick it up and call the live API on every test run.
- Setting up the project board and issues took longer than expected.

**What I learned**
- Throwaway scripts belong in a git-ignored `scratch/` folder, not in `tests/`.
- Always create a virtual environment before installing packages.

**Change for next sprint**
- Create the sprint's issues and milestone *before* writing any code.

---

## Sprint 1: Extract
**Dates:** [start] to [end]
**Goal:** Pull weather and air-quality data for Fouchana and save it as raw files, with retries and logging.

**Went well**
- `extract.py` ran on the first try and saved 72 hourly rows per source.
- Putting the city, coordinates, and API settings in `config.py` means changing city takes one line.
- Retries with backoff and logging make failures visible instead of silent.

**Didn't go well**
- I did not look at the raw data closely until after the run. The response includes hours that are still in the future, which are forecasts, not observations.
- The weather and air-quality APIs use slightly different grid points (about 2-3 km apart), which I only noticed by inspecting the JSON.

**What I learned**
- Always open the raw output and check its structure, units, and timestamps before building on it.
- The air-quality values are model-based estimates, not sensor readings, so this belongs in the README limitations.

**Change for next sprint**
- Inspect the data first and write the data-quality checks (duplicates, ranges, forecast flag) before writing the cleaning code.
- Add `is_forecast` to the data so future hours never pollute the analysis.