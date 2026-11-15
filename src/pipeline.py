import logging
import time
from datetime import datetime, timezone

import checks
import extract
import load
import transform
import validation

logger = logging.getLogger(__name__)


def main():
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    rows_loaded = rows_total = newest = None
    try:
        extract.main()  # exits with code 1 if extraction fails
        df = validation.validate(transform.run())
        rows_loaded, rows_total = load.load(df)
        observed = df.loc[~df["is_forecast"], "observed_at"]
        newest = observed.max().strftime("%Y-%m-%d %H:%M:%S") if not observed.empty else None
        checks.run_all()
        load.log_run(started, time.perf_counter() - t0, "success", rows_loaded, rows_total, newest)
        logger.info("Pipeline finished successfully")
    except (Exception, SystemExit) as e:
        logger.error("Pipeline failed: %s", e)
        load.log_run(
            started,
            time.perf_counter() - t0,
            "failed",
            rows_loaded,
            rows_total,
            newest,
            error=f"{type(e).__name__}: {e}"[:500],
        )
        raise


if __name__ == "__main__":
    main()
