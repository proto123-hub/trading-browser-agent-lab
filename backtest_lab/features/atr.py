"""Average True Range, Wilder 14-day (spec L167-170, framework v2 L138-141)."""

from __future__ import annotations

import pandas as pd

DEFAULT_PERIOD = 14


def true_range(frame: pd.DataFrame) -> pd.Series:
    high, low, close = frame["high"], frame["low"], frame["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def atr(frame: pd.DataFrame, period: int = DEFAULT_PERIOD) -> pd.Series:
    """Wilder-smoothed ATR. Seed = SMA of first `period` true ranges."""
    tr = true_range(frame)
    arr = tr.to_numpy(dtype="float64", copy=True)
    out = [float("nan")] * len(arr)
    if len(arr) <= period:
        return pd.Series(out, index=frame.index, name="atr")
    seed = arr[1 : period + 1].mean()  # TR[0] has no prev close
    out[period] = seed
    prev = seed
    for i in range(period + 1, len(arr)):
        prev = (prev * (period - 1) + arr[i]) / period
        out[i] = prev
    return pd.Series(out, index=frame.index, name="atr")
