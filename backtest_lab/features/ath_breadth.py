"""All-time-high distance, rolling-high windows, and compression detection.

Per spec L172-179, L209-213: ATH compression (e.g. ``11 -> 7 -> 3``) is a
market-breadth regime feature computed across a set of names; single-symbol
versions are exploratory-only. We provide both, clearly separated.
"""

from __future__ import annotations

import pandas as pd

ROLLING_WINDOWS = [3, 7, 11, 21, 50, 100, 252]


def ath_features(close: pd.Series, windows: list[int] | None = None) -> pd.DataFrame:
    """Single-symbol ATH diagnostics (exploratory; spec L174)."""
    windows = windows or ROLLING_WINDOWS
    running_max = close.cummax()
    out = pd.DataFrame(index=close.index)
    out["running_ath"] = running_max
    out["pct_below_ath"] = close / running_max - 1.0
    out["is_new_ath"] = close >= running_max
    # days since last ATH
    days = []
    last = -1
    for i, flag in enumerate(out["is_new_ath"].to_numpy()):
        if flag:
            last = i
        days.append(0 if last < 0 else i - last)
    out["days_since_ath"] = days
    for w in windows:
        out[f"high_{w}"] = close.rolling(w).max()
        out[f"at_high_{w}"] = close >= close.rolling(w).max()
    return out


def breadth_new_ath_count(closes: pd.DataFrame, window: int) -> pd.Series:
    """Count of names making a new ``window``-day high on each date.

    ``closes`` is a date-indexed frame with one column per symbol.
    """
    is_high = closes >= closes.rolling(window).max()
    return is_high.sum(axis=1)


def compression_sequence(
    closes: pd.DataFrame, windows: tuple[int, int, int] = (11, 7, 3)
) -> pd.DataFrame:
    """Detect a shrinking breadth sequence across the given windows.

    For windows (a, b, c) the breadth counts at each date are compared; a
    compression is flagged when count(a) > count(b) > count(c), i.e. fewer names
    confirming as the lookback tightens (spec L178).
    """
    a, b, c = windows
    ca = breadth_new_ath_count(closes, a)
    cb = breadth_new_ath_count(closes, b)
    cc = breadth_new_ath_count(closes, c)
    out = pd.DataFrame(index=closes.index)
    out[f"breadth_new_ath_{a}"] = ca
    out[f"breadth_new_ath_{b}"] = cb
    out[f"breadth_new_ath_{c}"] = cc
    out["compression"] = (ca > cb) & (cb > cc)
    return out
