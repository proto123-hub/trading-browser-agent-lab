"""Market-breadth features for Phase 4 (spec p4-breadth-filter-spec.md).

Computes the new-all-time-high count across an *eligible* multi-name universe
(>= ``min_history`` trading days at each date, so a fresh IPO cannot print a
trivial day-1 "new ATH"), then a daily breadth regime label. This is the proper
multi-name basis that the 2-ETF Phase 3 proxy could not provide (Q4).

Breadth is a market-regime overlay, never a single-name v2 rule (Non-Goals).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .data.csv_adapter import CSVCacheAdapter

# 24 single names that form the breadth basis (benchmarks SPY/QQQ excluded).
BREADTH_UNIVERSE = [
    "PLTR", "NVDA", "GOOGL", "TSLA", "META", "MRVL", "CLS", "AMD", "MSFT", "TSM",
    "INTC", "ORCL", "MU", "AVGO", "QCOM", "AMAT", "LRCX", "KLAC", "ARM", "CRWD",
    "SNOW", "RKLB", "WDC", "SNDK",
]
MIN_HISTORY = 252


def load_breadth_panel(
    symbols=None, start="2019-01-02", end="2026-06-05", data_dir="data/raw"
) -> pd.DataFrame:
    """Date x symbol close panel from the sha256-gated cache (fail-closed)."""
    symbols = symbols or BREADTH_UNIVERSE
    adapter = CSVCacheAdapter(data_dir=data_dir)
    closes = {}
    for sym in symbols:
        closes[sym] = adapter.fetch(sym, start, end).frame["close"]
    return pd.DataFrame(closes).sort_index()


def eligible_new_ath_count(panel: pd.DataFrame, min_history: int = MIN_HISTORY) -> pd.Series:
    """Per date: number of names at a new all-time-high close, counting only
    names with >= ``min_history`` observations up to that date."""
    eligible = panel.notna().cumsum() >= min_history
    running_max = panel.cummax()
    is_ath = (panel == running_max) & panel.notna() & eligible
    return is_ath.sum(axis=1).rename("new_ath_count")


@dataclass(frozen=True)
class BreadthRegimeConfig:
    window: int = 5             # rolling window for "lower highs"
    min_eligible: int = 10      # eligible-universe size below this -> warmup
    washout_min_peak: int = 3   # washout = count==0 after a recent peak >= this


def breadth_regime(
    count: pd.Series,
    config: BreadthRegimeConfig | None = None,
    eligible_count: pd.Series | None = None,
) -> pd.Series:
    """Label each day. A plain ``count==0`` is NOT a washout — most days have no
    new all-time-high (during warmup and bear markets count is ~0 the majority of
    the time). We therefore distinguish:

    warmup     : fewer than ``min_eligible`` names have >=252d history yet.
    expansion  : breadth at/above its recent rolling peak (positive count).
    compression: positive count below the recent peak and not rising (lower highs).
    washout    : count collapses to 0 *after* a recent elevated peak (>= washout_min_peak)
                 -- the rare, meaningful event (e.g. the 6/5 episode), not a quiet zero.
    neutral    : everything else (quiet/low breadth that is not a collapse).

    No lookahead: uses count at/before T only (peak via shift(1)).
    """
    cfg = config or BreadthRegimeConfig()
    prior_peak = count.rolling(cfg.window).max().shift(1)
    falling = count <= count.shift(1)
    regime = pd.Series("neutral", index=count.index, dtype=object)
    regime[((count > 0) & (count >= prior_peak)).fillna(False)] = "expansion"
    regime[((count > 0) & (count < prior_peak) & falling).fillna(False)] = "compression"
    regime[((count == 0) & (prior_peak >= cfg.washout_min_peak)).fillna(False)] = "washout"
    if eligible_count is not None:
        regime[eligible_count.reindex(count.index) < cfg.min_eligible] = "warmup"
    return regime.rename("breadth_regime")


def breadth_features(
    symbols=None, start="2019-01-02", end="2026-06-05",
    data_dir="data/raw", min_history: int = MIN_HISTORY,
    regime_config: BreadthRegimeConfig | None = None,
) -> pd.DataFrame:
    panel = load_breadth_panel(symbols, start, end, data_dir)
    count = eligible_new_ath_count(panel, min_history)
    eligible_count = (panel.notna().cumsum() >= min_history).sum(axis=1)
    regime = breadth_regime(count, regime_config, eligible_count=eligible_count)
    out = pd.DataFrame({"new_ath_count": count, "eligible_names": eligible_count,
                        "breadth_regime": regime})
    # the risk-off gate fires on compression + washout (declining/collapsed breadth)
    out["compression"] = out["breadth_regime"].isin(["compression", "washout"])
    return out
