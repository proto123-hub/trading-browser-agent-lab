"""RSI. Wilder 14-day is canonical (spec L181-183, framework v2 L123).

Cutler RSI (simple-MA variant, used by the current dashboard cron) is computed
under a distinct name and must be excluded from canonical pass/fail decisions.
"""

from __future__ import annotations

import pandas as pd

DEFAULT_PERIOD = 14


def wilder_rsi(close: pd.Series, period: int = DEFAULT_PERIOD) -> pd.Series:
    """Canonical Wilder RSI: SMA seed over the first ``period`` deltas, then
    Wilder recursive smoothing (alpha = 1/period)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    # Wilder smoothing with SMA seed: ewm(alpha=1/period) on the deltas but with
    # the first `period`-mean as the seed. pandas ewm with adjust=False and a
    # mean-seeded series reproduces Wilder exactly.
    avg_gain = _wilder_smooth(gain, period)
    avg_loss = _wilder_smooth(loss, period)

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    # When avg_loss == 0 -> RS = inf -> rsi = 100; pandas yields NaN for 0/0.
    rsi = rsi.where(avg_loss != 0.0, 100.0)
    rsi = rsi.where(~((avg_gain == 0.0) & (avg_loss == 0.0)), 50.0)
    return rsi


def _wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """Wilder's moving average: seed = SMA of first `period`, then recursive."""
    arr = series.to_numpy(dtype="float64", copy=True)
    out = [float("nan")] * len(arr)
    if len(arr) <= period:
        return pd.Series(out, index=series.index)
    # First valid delta is at index 1 (diff). Seed window = indices 1..period.
    seed = arr[1 : period + 1].mean()
    out[period] = seed
    prev = seed
    for i in range(period + 1, len(arr)):
        prev = (prev * (period - 1) + arr[i]) / period
        out[i] = prev
    return pd.Series(out, index=series.index)


def cutler_rsi(close: pd.Series, period: int = DEFAULT_PERIOD) -> pd.Series:
    """Cutler RSI: simple moving average of gains/losses. Non-canonical."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.where(avg_loss != 0.0, 100.0)
    rsi = rsi.where(~((avg_gain == 0.0) & (avg_loss == 0.0)), 50.0)
    return rsi
