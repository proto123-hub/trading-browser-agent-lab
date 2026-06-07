"""Robustness analysis (spec L271-279).

Operates on strategy return/position series produced by the engine:
walk-forward by year, bull/bear/sideways regime segmentation, leave-one-out
across symbols, and bootstrap confidence intervals. Earnings-window and
parameter-sensitivity comparisons are driven by re-running strategies with
different configs (see phase3.py); this module provides the slicing + stats.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .strategies.engine import compute_metrics, TRADING_DAYS


def _metrics_for_slice(returns: pd.Series, position: pd.Series) -> dict:
    r = returns.fillna(0.0)
    if len(r) == 0:
        return {}
    equity = (1.0 + r).cumprod()
    return compute_metrics(r, position.reindex(r.index).fillna(0.0), equity)


def walk_forward_by_year(returns: pd.Series, position: pd.Series) -> pd.DataFrame:
    """Per-calendar-year metrics for one strategy."""
    rows = []
    for year, idx in returns.groupby(returns.index.year).groups.items():
        m = _metrics_for_slice(returns.loc[idx], position.loc[idx])
        rows.append({"year": int(year), **m})
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def classify_regime(
    market_close: pd.Series,
    sma_window: int = 200,
    bear_drawdown: float = 0.20,
    bull_drawdown: float = 0.10,
) -> pd.Series:
    """Label each date bull / bear / sideways from a market proxy close.

    bear: drawdown from running peak deeper than ``bear_drawdown``.
    bull: above the SMA and shallow drawdown (< ``bull_drawdown``).
    sideways: everything else. Uses only past data (no lookahead).
    """
    sma = market_close.rolling(sma_window).mean()
    running_max = market_close.cummax()
    dd = market_close / running_max - 1.0
    above = market_close > sma

    regime = pd.Series("sideways", index=market_close.index, dtype=object)
    regime[(above) & (dd > -bull_drawdown)] = "bull"
    regime[dd <= -bear_drawdown] = "bear"
    regime[sma.isna()] = "warmup"
    return regime


def metrics_by_regime(
    returns: pd.Series, position: pd.Series, regime: pd.Series
) -> pd.DataFrame:
    reg = regime.reindex(returns.index).fillna("warmup")
    rows = []
    for label in ["bull", "bear", "sideways"]:
        mask = reg == label
        if mask.sum() == 0:
            continue
        m = _metrics_for_slice(returns[mask], position[mask])
        rows.append({"regime": label, "n_days": int(mask.sum()), **m})
    return pd.DataFrame(rows)


def leave_one_out(returns_by_symbol: dict[str, pd.Series]) -> pd.DataFrame:
    """Equal-weight portfolio metrics with each symbol left out in turn."""
    syms = list(returns_by_symbol)
    panel = pd.DataFrame(returns_by_symbol).fillna(0.0)
    rows = []
    for left_out in [None, *syms]:
        cols = [s for s in syms if s != left_out]
        port = panel[cols].mean(axis=1)
        equity = (1.0 + port).cumprod()
        pos = pd.Series(1.0, index=port.index)
        m = compute_metrics(port, pos, equity)
        rows.append({"left_out": left_out or "(none)", **m})
    return pd.DataFrame(rows)


def bootstrap_ci(
    daily_returns: pd.Series,
    n_boot: int = 1000,
    ci: float = 0.95,
    seed: int = 17,
) -> dict:
    """Bootstrap CI for the annualized mean daily return (block-free, i.i.d.)."""
    r = daily_returns.dropna().to_numpy()
    if len(r) < 30:
        return {"point": float("nan"), "lo": float("nan"), "hi": float("nan"), "n": len(r)}
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    n = len(r)
    for i in range(n_boot):
        sample = r[rng.integers(0, n, n)]
        means[i] = sample.mean() * TRADING_DAYS
    lo = float(np.quantile(means, (1 - ci) / 2))
    hi = float(np.quantile(means, 1 - (1 - ci) / 2))
    return {"point": float(r.mean() * TRADING_DAYS), "lo": lo, "hi": hi, "n": n}
