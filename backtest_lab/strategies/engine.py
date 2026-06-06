"""Minimal long/flat backtest engine with no-lookahead execution.

Execution model (spec L262-265):
- A position decided from data at close of bar T takes effect at T+1 (we shift
  the position series by one bar before applying close-to-close returns). This
  approximates "enter/exit at next session open after signal".
- Slippage charged on turnover (position change); default 5 bps. Commission
  default 0. Both configurable.
- No leverage, no shorting (retail variant, framework v2 L113-114); position in
  {0, 1} or fractional in [0, 1].

This is the harness substrate. Full strategy variants and the complete metric
set (forward returns, parameter sweeps) are Phase 2/3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass(frozen=True)
class ExecConfig:
    slippage_bps: float = 5.0
    commission: float = 0.0


@dataclass
class BacktestResult:
    equity: pd.Series
    returns: pd.Series
    position: pd.Series
    metrics: dict


def backtest_positions(
    frame: pd.DataFrame,
    position: pd.Series,
    config: ExecConfig | None = None,
) -> BacktestResult:
    """Backtest a long/flat position series against close-to-close returns."""
    cfg = config or ExecConfig()
    close = frame["close"]
    asset_ret = close.pct_change().fillna(0.0)

    # Decision at close T -> effective T+1 (no lookahead).
    pos = position.reindex(close.index).fillna(0.0).clip(0.0, 1.0)
    effective = pos.shift(1).fillna(0.0)

    turnover = effective.diff().abs().fillna(effective.abs())
    cost = turnover * (cfg.slippage_bps / 1e4 + cfg.commission)
    strat_ret = effective * asset_ret - cost

    equity = (1.0 + strat_ret).cumprod()
    metrics = compute_metrics(strat_ret, effective, equity)
    return BacktestResult(equity=equity, returns=strat_ret, position=effective, metrics=metrics)


def compute_metrics(returns: pd.Series, position: pd.Series, equity: pd.Series) -> dict:
    returns = returns.fillna(0.0)
    n = len(returns)
    if n == 0:
        return {}
    total_return = float(equity.iloc[-1] - 1.0)
    years = n / TRADING_DAYS
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 and equity.iloc[-1] > 0 else float("nan")
    vol = float(returns.std(ddof=0) * math.sqrt(TRADING_DAYS))
    mean_ann = float(returns.mean() * TRADING_DAYS)
    sharpe = float(mean_ann / vol) if vol > 0 else float("nan")
    downside = returns[returns < 0]
    dvol = float(downside.std(ddof=0) * math.sqrt(TRADING_DAYS)) if len(downside) else 0.0
    sortino = float(mean_ann / dvol) if dvol > 0 else float("nan")
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    max_dd = float(drawdown.min())
    calmar = float(cagr / abs(max_dd)) if max_dd < 0 and not math.isnan(cagr) else float("nan")
    exposure = float((position > 0).mean())

    # trade segmentation (contiguous in-market runs)
    in_mkt = (position > 0).to_numpy()
    trades = []
    start = None
    for i, flag in enumerate(in_mkt):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            trades.append((start, i - 1))
            start = None
    if start is not None:
        trades.append((start, len(in_mkt) - 1))

    trade_returns = []
    holding = []
    for s, e in trades:
        seg = returns.iloc[s : e + 1]
        trade_returns.append(float((1.0 + seg).prod() - 1.0))
        holding.append(e - s + 1)
    n_trades = len(trades)
    wins = [r for r in trade_returns if r > 0]
    win_rate = float(len(wins) / n_trades) if n_trades else float("nan")
    avg_hold = float(np.mean(holding)) if holding else 0.0

    return {
        "total_return": total_return,
        "cagr": cagr,
        "vol_annual": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "exposure": exposure,
        "n_trades": n_trades,
        "win_rate": win_rate,
        "avg_holding_days": avg_hold,
    }
