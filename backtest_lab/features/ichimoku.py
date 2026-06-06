"""Ichimoku features, standard 9/26/52 with +26 displacement (spec L93-103).

Cloud-color and cloud-bound definitions trace to framework v2 L10-20, L26-33.

No-lookahead contract (spec L265): the cloud evaluated *at bar T* is the cloud
projected to T, i.e. Senkou values computed 26 bars earlier and displaced
forward. We implement displacement with ``.shift(+26)`` so ``senkou_a[T]``
depends only on data at and before ``T-26``. Chikou (close shifted -26) is a
plotting/visual feature and must never be used as a same-bar signal input.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

TENKAN_PERIOD = 9
KIJUN_PERIOD = 26
SENKOU_B_PERIOD = 52
DISPLACEMENT = 26


def _midpoint(high: pd.Series, low: pd.Series, window: int) -> pd.Series:
    return (high.rolling(window).max() + low.rolling(window).min()) / 2.0


@dataclass(frozen=True)
class IchimokuConfig:
    tenkan: int = TENKAN_PERIOD
    kijun: int = KIJUN_PERIOD
    senkou_b: int = SENKOU_B_PERIOD
    displacement: int = DISPLACEMENT


def ichimoku(frame: pd.DataFrame, config: IchimokuConfig | None = None) -> pd.DataFrame:
    """Return Ichimoku component columns aligned to ``frame``'s index."""
    cfg = config or IchimokuConfig()
    high, low, close = frame["high"], frame["low"], frame["close"]

    tenkan = _midpoint(high, low, cfg.tenkan)
    kijun = _midpoint(high, low, cfg.kijun)

    # Raw spans (undisplaced), then projected forward by `displacement`.
    senkou_a_raw = (tenkan + kijun) / 2.0
    senkou_b_raw = _midpoint(high, low, cfg.senkou_b)
    senkou_a = senkou_a_raw.shift(cfg.displacement)
    senkou_b = senkou_b_raw.shift(cfg.displacement)

    chikou = close.shift(-cfg.displacement)  # visual only; never a signal input

    cloud_top = senkou_a.combine(senkou_b, max)
    cloud_bottom = senkou_a.combine(senkou_b, min)
    cloud_thickness = (senkou_a - senkou_b).abs()
    bearish_cloud = senkou_a < senkou_b  # framework v2 L11
    bullish_cloud = senkou_a > senkou_b  # framework v2 L19

    out = pd.DataFrame(index=frame.index)
    out["tenkan"] = tenkan
    out["kijun"] = kijun
    out["senkou_a"] = senkou_a
    out["senkou_b"] = senkou_b
    out["chikou"] = chikou
    out["cloud_top"] = cloud_top
    out["cloud_bottom"] = cloud_bottom
    out["cloud_thickness"] = cloud_thickness
    out["bearish_cloud"] = bearish_cloud
    out["bullish_cloud"] = bullish_cloud
    out["tenkan_gt_kijun"] = tenkan > kijun
    # price position relative to cloud
    out["above_cloud"] = close > cloud_top
    out["below_cloud"] = close < cloud_bottom
    out["in_cloud"] = (~out["above_cloud"]) & (~out["below_cloud"]) & cloud_top.notna()
    return out
