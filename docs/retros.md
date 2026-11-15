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

---

## Sprint 2: Transform & Load
**Dates:** [start] to [end]
**Goal:** Clean and merge the raw data, load it into SQLite without duplicates, and cover it with tests.

**Follow-up on the Sprint 1 retro**
- Did I write the data-quality tests before the cleaning code? Yes. I wrote the tests first and ran them to see them fail.
- Did I add `is_forecast`? Yes. Future hours are flagged in every row.

**Went well**
- Writing the tests first made it clear what "done" meant.
- The upsert with primary key `(city, observed_at)` makes the pipeline safe to rerun. Two runs in a row gave 72 rows both times, with `updated_at` refreshed.
- The `is_forecast` flag keeps future hours out of the analysis.
- Raw files and the clean database are separate, so I can reprocess the raw data if the cleaning rules change.

**Didn't go well**
- `DB_PATH` was added to `config.py` before `BASE_DIR` was defined, which raised a `NameError`.
- pytest was not installed in the virtual environment, so I used `python -m pytest`.
- `pipeline.py` was an empty file, so the pipeline ran silently and the table was never created.

**What I learned**
- Silent success is suspicious. If a script prints no logs, check that it actually ran.
- Passing unit tests do not prove the pipeline is wired together. Run it end to end too.
- Order matters in a Python config file, because variables must be defined before they are used.

**Change for next sprint**
- Check that each file has content (`Get-Content`) before running it.
- Add a smoke test that the pipeline creates the `hourly_readings` table.
- Plan where the database will live before scheduling the pipeline, because GitHub Actions starts from a fresh checkout every run.

---

## Sprint 3: Automation & Analysis
**Dates:** [start] to [end]
**Goal:** Run the pipeline daily on GitHub Actions, keep the database growing, and get the first findings from SQL.

**Follow-up on the Sprint 2 retro**
- Did I add a check that the pipeline creates the table? Yes, as a sanity step in the workflow that fails the run if `hourly_readings` is empty.
- Did I plan where the database lives before scheduling? Yes. The workflow commits it back to the repo, and local experiments use a separate file through `DB_PATH`.
- Did I check that each file had content before running it? [fill in honestly]

**Went well**
- The first workflow run was green in 25 seconds, with every step passing.
- A 60-day backfill gave 1,464 rows (61 days) with no missing values, so analysis could start right away instead of waiting weeks.
- Filtering on `is_forecast = 0` in every query kept predictions out of the findings.
- Using Spearman correlation and wind bands showed the wind effect clearly (about -0.5 correlation, 9.7 vs 6.0 µg/m³ PM2.5).

**Didn't go well**
- I did not know the difference between Command Prompt and PowerShell, so the `$env:` syntax for `DB_PATH` did not work at first.
- `scratch/check_db.py` had the database path hardcoded, so it showed the committed database while I thought it was reading my local one.
- The "strong wind" band has only 19 hours, so its numbers looked impressive but are not reliable.
- Only one manual run exists so far, so the scheduled trigger is not yet proven.

**What I learned**
- A tool that reads a path should use the same config as the pipeline, otherwise it can silently show the wrong data.
- Always report the sample size next to a result, and say when a group is too small.
- Wind, time of day, and humidity are tangled together, so a correlation alone cannot say which one matters.

**Change for next sprint**
- Make every script and the dashboard read the database path from `config.py`.
- Check the Actions tab for the scheduled runs, then update the README sprint table.
- Show the sample size and the `is_forecast = 0` filter in the dashboard too.

**Scheduled runs:** [fill in on Nov 18: dates of the 3 scheduled runs and whether the bot committed each time]