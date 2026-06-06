"""Standalone tiered profit-taking strategy (spec L253-258, v2 L97-104).

Holds a base long from the first valid bar and applies a tiered exit. Canonical
sizing is 33/33/33; the ATR variant uses +3/+5 ATR targets. Remainder
management options trace to spec L258 (canonical SMA50 trailing; cloud-top
2-session 50% rule; fixed time stop and Kijun break are labelled non-canonical
variants).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TieredProfitConfig:
    trigger_mode: str = "canonical"   # canonical | atr
    remainder_mode: str = "sma50_trailing"  # sma50_trailing | cloud_top_2day | time_stop | kijun_break(non-canonical)
    tier_fraction: float = 1.0 / 3.0
    tier1_rsi: float = 75.0
    tier1_gain: float = 0.20
    tier2_gain: float = 0.35
    tier2_atr_mult: float = 2.0
    atr_tier1_mult: float = 3.0       # +3 ATR (v2 L140)
    atr_tier2_mult: float = 5.0       # +5 ATR
    time_stop_days: int = 60
    entry_lookback: int = 1           # bars after start to set entry reference


def run_tiered_profit_strategy(
    feats: pd.DataFrame, config: TieredProfitConfig | None = None
) -> tuple[pd.Series, pd.Series]:
    cfg = config or TieredProfitConfig()
    idx = feats.index
    close = feats["close"]
    pos = pd.Series(0.0, index=idx)

    # entry: first bar with a usable SMA50 (so trailing logic is defined)
    valid = feats["sma50"].notna()
    if not valid.any():
        return pos, pd.Series(False, index=idx)
    entry_pos = valid.idxmax()
    entry_loc = idx.get_loc(entry_pos)
    entry_price = close.loc[entry_pos]

    size = 1.0
    t1 = t2 = False
    events = pd.Series(False, index=idx)
    below_top_streak = 0

    for i, date in enumerate(idx):
        if i < entry_loc:
            pos.at[date] = 0.0
            continue
        row = feats.loc[date]
        c = row["close"]
        rsi = row["rsi_wilder_14"]
        atr = row.get("atr_14", float("nan"))
        bb_upper = row.get("bb_upper", float("nan"))
        sma50 = row["sma50"]
        kijun = row.get("kijun", float("nan"))
        cloud_top = row.get("cloud_top", float("nan"))

        if size > 1e-9:
            # tier 1
            if not t1:
                if cfg.trigger_mode == "canonical":
                    hit = rsi >= cfg.tier1_rsi or c >= entry_price * (1 + cfg.tier1_gain)
                else:
                    hit = pd.notna(atr) and c >= entry_price + cfg.atr_tier1_mult * atr
                if hit:
                    t1 = True
                    size = max(0.0, size - cfg.tier_fraction)
                    events.at[date] = True
            # tier 2
            if size > 1e-9 and not t2:
                if cfg.trigger_mode == "canonical":
                    hit = (pd.notna(bb_upper) and pd.notna(atr)
                           and c >= bb_upper + cfg.tier2_atr_mult * atr) \
                        or c >= entry_price * (1 + cfg.tier2_gain)
                else:
                    hit = pd.notna(atr) and c >= entry_price + cfg.atr_tier2_mult * atr
                if hit:
                    t2 = True
                    size = max(0.0, size - cfg.tier_fraction)
                    events.at[date] = True
            # remainder management (tier 3)
            below_top_streak = below_top_streak + 1 if (pd.notna(cloud_top) and c < cloud_top) else 0
            rem_hit = False
            if cfg.remainder_mode == "sma50_trailing":
                rem_hit = pd.notna(sma50) and c < sma50
            elif cfg.remainder_mode == "cloud_top_2day":
                rem_hit = below_top_streak >= 2
            elif cfg.remainder_mode == "time_stop":
                rem_hit = (i - entry_loc) >= cfg.time_stop_days
            elif cfg.remainder_mode == "kijun_break":  # non-canonical variant
                rem_hit = pd.notna(kijun) and c < kijun
            if size > 1e-9 and t1 and t2 and rem_hit:
                size = 0.0
                events.at[date] = True

        pos.at[date] = size

    return pos, events
