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
from .scenario_strategy import run_scenario_strategy, ScenarioStrategyConfig
from .meltup_strategy import run_meltup_overlay, MeltUpConfig
from .tier_950 import run_tier950_strategy, Tier950Config
from .breadth_filter import (
    apply_breadth_filter,
    compression_regime,
    BreadthFilterConfig,
)
from .tiered_profit import run_tiered_profit_strategy, TieredProfitConfig

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
    "run_scenario_strategy",
    "ScenarioStrategyConfig",
    "run_meltup_overlay",
    "MeltUpConfig",
    "run_tier950_strategy",
    "Tier950Config",
    "apply_breadth_filter",
    "compression_regime",
    "BreadthFilterConfig",
    "run_tiered_profit_strategy",
    "TieredProfitConfig",
]
