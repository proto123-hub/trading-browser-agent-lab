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
) -> pd.DataFrame:
    open_, high, low, close, volume = (
        frame["open"], frame["high"], frame["low"], frame["close"], frame["volume"],
    )
    ath = ath_features(close)
    running_ath = ath["running_ath"]
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
    return out
