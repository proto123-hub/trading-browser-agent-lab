"""Melt-Up signal predicates (spec L201-207, framework context).

Primary signal: open at/near ATH -> new intraday high -> heavy-volume selling
-> bearish close (a failed new-high day on high volume).
Secondary signal: failed new high plus a down gap.

Every fired predicate is returned as a boolean column so the labeler/strategy
layer can log it with the bar date.
"""

from __future__ import annotations

import pandas as pd

from .ath_breadth import ath_features


def meltup_features(
    frame: pd.DataFrame,
    near_ath_pct: float = 0.01,
    heavy_vol_mult: float = 1.5,
    vol_period: int = 20,
    recent_ath_days: int = 5,
    relaxed_vol_mult: float = 1.2,
) -> pd.DataFrame:
    open_, high, low, close, volume = (
        frame["open"], frame["high"], frame["low"], frame["close"], frame["volume"],
    )
    ath = ath_features(close)
    running_ath = ath["running_ath"]
    days_since_ath = ath["days_since_ath"]
    prev_close = close.shift(1)
    prev_high = high.shift(1)
    vol_avg = volume.rolling(vol_period).mean()

    open_near_ath = open_ >= running_ath.shift(1) * (1.0 - near_ath_pct)
    new_intraday_high = high > prev_high
    heavy_volume = volume >= heavy_vol_mult * vol_avg
    bearish_close = close < open_
    down_gap = open_ < prev_close

    out = pd.DataFrame(index=frame.index)
    out["mu_open_near_ath"] = open_near_ath
    out["mu_new_intraday_high"] = new_intraday_high
    out["mu_heavy_volume"] = heavy_volume
    out["mu_bearish_close"] = bearish_close
    out["mu_down_gap"] = down_gap
    out["mu_primary"] = (
        open_near_ath & new_intraday_high & heavy_volume & bearish_close
    )
    out["mu_secondary"] = new_intraday_high & bearish_close & down_gap

    # NON-CANONICAL exploratory variant (R4): covers the "failed-high within a few
    # sessions of a recent ATH" case that the canonical primary misses (e.g. a
    # distribution day 1-2 sessions after the ATH, where open is no longer within
    # 1% of the ATH and the day makes no new intraday high). Not a canonical rule;
    # used only in the exploratory report section.
    within_recent_ath = (days_since_ath >= 0) & (days_since_ath <= recent_ath_days)
    failed_new_high = high < running_ath.shift(1)
    # relaxed uses an "elevated" volume bar (>=1.2x) rather than the canonical
    # 1.5x: a distribution day after a run-up is often elevated but below 1.5x of
    # a run-up-inflated 20d average (e.g. MU 6/5 was ~1.35x avg, under 1.5x).
    relaxed_heavy_volume = volume >= relaxed_vol_mult * vol_avg
    out["mu_relaxed_primary"] = (
        within_recent_ath & failed_new_high & relaxed_heavy_volume & bearish_close
    )
    return out
