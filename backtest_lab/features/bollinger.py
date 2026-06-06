"""Bollinger Bands, 20-day, 2 sigma (spec L159, framework v2 L133-136)."""

from __future__ import annotations

import pandas as pd

DEFAULT_PERIOD = 20
DEFAULT_NUM_STD = 2.0


def bollinger(
    close: pd.Series, period: int = DEFAULT_PERIOD, num_std: float = DEFAULT_NUM_STD
) -> pd.DataFrame:
    mid = close.rolling(period).mean()
    # Population std (ddof=0) is the standard Bollinger convention.
    std = close.rolling(period).std(ddof=0)
    out = pd.DataFrame(index=close.index)
    out["bb_mid"] = mid
    out["bb_upper"] = mid + num_std * std
    out["bb_lower"] = mid - num_std * std
    out["bb_std"] = std
    return out
