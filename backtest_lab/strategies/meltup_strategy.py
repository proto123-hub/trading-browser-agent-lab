"""Melt-Up signal overlay (spec L201-207, L233-238).

Melt-Up signals are *failed new-high on high volume* events (primary) optionally
with a down gap (secondary). They are used as risk-off / exposure-scaling
overlays on a base long position: when a signal fires, exposure is cut for a
cooldown window. Four variants:

  primary_only   : act on the primary signal.
  secondary_only : act on the secondary signal.
  stacked        : act only when both fire on the same bar (high-confidence).
  conflict_aware : act on either; if only one fires reduce to half exposure,
                   if both fire go fully risk-off.

``earnings_blackout`` suppresses signals inside an earnings window (spec L238).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MeltUpConfig:
    variant: str = "primary_only"   # primary_only|secondary_only|stacked|conflict_aware
    risk_off_level: float = 0.0     # exposure during cooldown
    half_level: float = 0.5         # conflict_aware single-signal exposure
    cooldown: int = 5               # bars to hold risk-off after a signal
    earnings_blackout: bool = False
    earnings_window: int = 3


def run_meltup_overlay(
    feats: pd.DataFrame, config: MeltUpConfig | None = None
) -> tuple[pd.Series, pd.Series]:
    """Return (position[0..1], signal_bool) for a Melt-Up risk-off overlay."""
    cfg = config or MeltUpConfig()
    idx = feats.index
    primary = feats["mu_primary"].fillna(False).astype(bool)
    secondary = feats["mu_secondary"].fillna(False).astype(bool)

    if cfg.earnings_blackout and "days_to_earnings" in feats.columns:
        dte = pd.to_numeric(feats["days_to_earnings"], errors="coerce")
        dse = pd.to_numeric(feats["days_since_earnings"], errors="coerce")
        in_window = (dte.abs() <= cfg.earnings_window) | (dse.abs() <= cfg.earnings_window)
        in_window = in_window.fillna(False)
        primary = primary & ~in_window
        secondary = secondary & ~in_window

    pos = pd.Series(1.0, index=idx)
    signal = pd.Series(False, index=idx)
    cooldown_left = 0
    target_level = 1.0

    for date in idx:
        p, s = bool(primary[date]), bool(secondary[date])
        fired = False
        level = cfg.risk_off_level
        if cfg.variant == "primary_only":
            fired = p
        elif cfg.variant == "secondary_only":
            fired = s
        elif cfg.variant == "stacked":
            fired = p and s
        elif cfg.variant == "conflict_aware":
            if p and s:
                fired, level = True, cfg.risk_off_level
            elif p or s:
                fired, level = True, cfg.half_level

        if fired:
            signal[date] = True
            cooldown_left = cfg.cooldown
            target_level = level

        if cooldown_left > 0:
            pos[date] = target_level
            cooldown_left -= 1
        else:
            pos[date] = 1.0

    return pos, signal
