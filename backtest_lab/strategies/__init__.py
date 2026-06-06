from __future__ import annotations

from .engine import backtest_positions, compute_metrics, BacktestResult, ExecConfig
from .baselines import (
    buy_and_hold,
    cash_only,
    ma_50_200,
    breakout_20,
    random_placebo,
    all_baselines,
)

__all__ = [
    "backtest_positions",
    "compute_metrics",
    "BacktestResult",
    "ExecConfig",
    "buy_and_hold",
    "cash_only",
    "ma_50_200",
    "breakout_20",
    "random_placebo",
    "all_baselines",
]
