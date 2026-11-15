import logging

import pandas as pd

try:
    import pandera.pandas as pa
except ImportError:  # older pandera versions
    import pandera as pa
from pandera.errors import SchemaErrors

from transform import VALID_RANGES

logger = logging.getLogger(__name__)

MIN_ROWS = 24
MAX_NULL_SHARE = 0.2


class DataQualityError(ValueError):
    pass


def _no_gaps(df):
    return all(
        (g["observed_at"].sort_values().diff().dropna() == pd.Timedelta(hours=1)).all()
        for _, g in df.groupby("city")
    )


def _few_nulls(df):
    return bool(df[list(VALID_RANGES)].isna().mean().max() <= MAX_NULL_SHARE)


_columns = {
    "city": pa.Column(str, nullable=False),
    "observed_at": pa.Column(pa.DateTime, nullable=False),
    "is_forecast": pa.Column(bool, nullable=False),
}
for _col, (_lo, _hi) in VALID_RANGES.items():
    _columns[_col] = pa.Column(float, pa.Check.in_range(_lo, _hi), nullable=True)

SCHEMA = pa.DataFrameSchema(
    _columns,
    unique=["city", "observed_at"],
    coerce=True,
    checks=[
        pa.Check(lambda df: len(df) >= MIN_ROWS, error=f"fewer than {MIN_ROWS} rows"),
        pa.Check(_no_gaps, error="hourly timestamps have gaps"),
        pa.Check(_few_nulls, error=f"more than {MAX_NULL_SHARE:.0%} missing values in a column"),
    ],
)


def validate(df):
    try:
        out = SCHEMA.validate(df, lazy=True)
    except SchemaErrors as e:
        raise DataQualityError(f"Data validation failed:\n{e.failure_cases.head(10)}") from e
    logger.info("Validation passed (%d rows)", len(out))
    return out
