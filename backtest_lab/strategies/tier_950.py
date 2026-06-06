"""MU $950 tier-trigger strategy and comparison tiers (spec L185-192, L240-245).

The $950 level is a *profit-taking tier trigger on an existing position*, never
an entry trigger (spec L242). The strategy holds a base long and takes a tier
(reduce by ``tier_fraction``) when the configured rule confirms. Four trigger
confirmation variants for the $950 cross, plus comparison tiers (hold / ATR /
RSI / fixed-%) so the $950 rule can be evaluated against alternatives.

Note: ``tier_level`` defaults to 950 and is parameterizable per symbol. On the
synthetic fixture (~100 base) the $950 cross does not fire by design — the
mechanism is verified here; the real $950 evaluation is Phase 3 on yfinance.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Tier950Config:
    mode: str = "tier_950_same_day"
    # tier_950_same_day | tier_950_two_day | tier_950_retest | tier_950_volume |
    # hold | tier_atr | tier_rsi | tier_fixed_pct
    tier_level: float = 950.0
    tier_fraction: float = 1.0 / 3.0
    vol_confirm: float = 1.5
    rsi_level: float = 75.0
    atr_mult: float = 3.0
    fixed_pct: float = 0.20
    entry_ref_lookback: int = 60   # reference entry for ATR/fixed-% tiers


def _two_day_cross(close: pd.Series, level: float) -> pd.Series:
    above = close > level
    return (above & above.shift(1)).fillna(False)


def run_tier950_strategy(
    feats: pd.DataFrame, config: Tier950Config | None = None
) -> tuple[pd.Series, pd.Series]:
    """Return (position[0..1], tier_event_bool). Base position is fully long."""
    cfg = config or Tier950Config()
    idx = feats.index
    close = feats["close"]
    pos = pd.Series(1.0, index=idx)
    events = pd.Series(False, index=idx)

    L = cfg.tier_level
    if cfg.mode == "hold":
        return pos, events

    if cfg.mode == "tier_950_same_day":
        trig = (close > L) & ~(close.shift(1) > L)
    elif cfg.mode == "tier_950_two_day":
        td = _two_day_cross(close, L)
        trig = td & ~td.shift(1).fillna(False)
    elif cfg.mode == "tier_950_retest":
        crossed = (close > L)
        retest = crossed & (close.shift(1) <= L) & (close.shift(2) > L)
        trig = retest.fillna(False)
    elif cfg.mode == "tier_950_volume":
        trig = (close > L) & ~(close.shift(1) > L) & (feats["vol_mult"] >= cfg.vol_confirm)
    elif cfg.mode == "tier_rsi":
        rsi = feats["rsi_wilder_14"]
        trig = (rsi >= cfg.rsi_level) & ~(rsi.shift(1) >= cfg.rsi_level)
    elif cfg.mode == "tier_fixed_pct":
        ref = close.shift(cfg.entry_ref_lookback)
        trig = (close >= ref * (1 + cfg.fixed_pct)) & ~(close.shift(1) >= ref.shift(1) * (1 + cfg.fixed_pct))
    elif cfg.mode == "tier_atr":
        ref = close.shift(cfg.entry_ref_lookback)
        atr = feats["atr_14"]
        hit = (close >= ref + cfg.atr_mult * atr).fillna(False).astype(bool)
        trig = hit & ~hit.shift(1, fill_value=False)
    else:
        raise ValueError(f"unknown tier mode {cfg.mode!r}")

    trig = trig.fillna(False).astype(bool)
    # apply tier reductions cumulatively, max 3 tiers (33/33/33 -> flat-ish)
    size = 1.0
    tiers = 0
    for date in idx:
        if bool(trig[date]) and tiers < 3 and size > 1e-9:
            size = max(0.0, size - cfg.tier_fraction)
            tiers += 1
            events[date] = True
        pos[date] = size
    return pos, events
