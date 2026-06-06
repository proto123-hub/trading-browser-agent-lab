"""Earnings features from an optional manual CSV (spec L194-199, L74, L83).

Earnings dates are supplied via a CSV with columns ``symbol,date,timing`` where
timing is one of ``bmo`` (before open), ``amc`` (after close), or ``unknown``.
Missing timestamps are explicitly marked ``unknown`` rather than guessed.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DRIFT_WINDOWS = [1, 3, 5, 10, 20]


def load_earnings_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    cols = {c.lower() for c in df.columns}
    if not {"symbol", "date"}.issubset(cols):
        raise ValueError("earnings CSV requires at least 'symbol' and 'date' columns")
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    if "timing" not in df.columns:
        df["timing"] = "unknown"
    df["timing"] = df["timing"].fillna("unknown").str.lower()
    return df


def earnings_features(
    frame: pd.DataFrame, earnings_dates: pd.Series | None
) -> pd.DataFrame:
    """Days-to/since earnings and an in-window flag.

    ``earnings_dates`` is a Series of Timestamps (for one symbol). If None, the
    features are emitted as NaN/unknown so downstream code can branch.
    """
    out = pd.DataFrame(index=frame.index)
    if earnings_dates is None or len(earnings_dates) == 0:
        out["days_to_earnings"] = pd.NA
        out["days_since_earnings"] = pd.NA
        out["earnings_known"] = False
        return out

    dates = pd.DatetimeIndex(sorted(pd.to_datetime(earnings_dates)))
    idx = frame.index
    days_to, days_since = [], []
    for d in idx:
        future = dates[dates >= d]
        past = dates[dates <= d]
        days_to.append((future[0] - d).days if len(future) else pd.NA)
        days_since.append((d - past[-1]).days if len(past) else pd.NA)
    out["days_to_earnings"] = days_to
    out["days_since_earnings"] = days_since
    out["earnings_known"] = True
    return out
