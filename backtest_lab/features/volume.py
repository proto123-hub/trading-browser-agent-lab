"""Volume features: 20-day average and multiple (spec L77, L89, L144)."""

from __future__ import annotations

import pandas as pd

DEFAULT_PERIOD = 20


def volume_features(volume: pd.Series, period: int = DEFAULT_PERIOD) -> pd.DataFrame:
    avg = volume.rolling(period).mean()
    out = pd.DataFrame(index=volume.index)
    out["vol_avg20"] = avg
    out["vol_mult"] = volume / avg
    return out


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()
