"""Phase 2 strategy-variant runner.

Executes the five strategy families and their variants for one symbol, returning
metric rows, transaction (trade-leg) rows, and forward-return rows. The pipeline
aggregates these into results/strategy_summary.csv, results/trades.csv, and
results/forward_returns.csv.
"""

from __future__ import annotations

import pandas as pd

from .strategies import (
    backtest_positions, ExecConfig,
    run_scenario_strategy, ScenarioStrategyConfig,
    run_meltup_overlay, MeltUpConfig,
    run_tier950_strategy, Tier950Config,
    run_tiered_profit_strategy, TieredProfitConfig,
    apply_breadth_filter, BreadthFilterConfig,
    buy_and_hold,
)
from .forward_returns import signal_forward_returns

# variant catalogs
SCENARIO_VARIANTS = ["full", "stage1_only", "stage2_only"]
MELTUP_VARIANTS = ["primary_only", "secondary_only", "stacked", "conflict_aware"]
TIER950_VARIANTS = [
    "tier_950_same_day", "tier_950_two_day", "tier_950_retest", "tier_950_volume",
    "hold", "tier_atr", "tier_rsi", "tier_fixed_pct",
]
TIERED_PROFIT_VARIANTS = [
    ("canonical", "sma50_trailing"),
    ("canonical", "cloud_top_2day"),
    ("atr", "sma50_trailing"),
    ("canonical", "kijun_break"),  # non-canonical remainder variant (labelled)
]
BREADTH_WINDOWS = [(11, 7, 3), (21, 11, 7), (50, 21, 11)]


def run_symbol_variants(
    symbol: str,
    frame: pd.DataFrame,
    feats: pd.DataFrame,
    exec_cfg: ExecConfig,
    compression_by_window: dict[tuple, pd.Series] | None = None,
) -> tuple[list[dict], list[dict], list[dict]]:
    summary: list[dict] = []
    trades: list[dict] = []
    fwd: list[dict] = []
    close = frame["close"]

    def _position_trades(name, pos):
        """Derive verifiable trade legs from a position series (R2a): every
        change in exposure is a BUY/SELL leg priced at that bar's close."""
        p = pos.reindex(close.index).fillna(0.0)
        delta = p.diff().fillna(p)
        legs = []
        for date in close.index[delta.ne(0.0).to_numpy()]:
            d = float(delta[date])
            legs.append({
                "date": date, "action": "BUY" if d > 0 else "SELL",
                "size_delta": round(d, 6), "price": float(close[date]),
                "reason": "position_change", "position_after": round(float(p[date]), 6),
                "symbol": symbol, "strategy": name,
            })
        return legs

    def add(name, pos, signal=None, log_trades=False):
        res = backtest_positions(frame, pos, exec_cfg)
        summary.append({"symbol": symbol, "strategy": name, **res.metrics})
        if signal is not None and signal.any():
            fr = signal_forward_returns(close, signal, symbol, name)
            fwd.extend(fr.to_dict("records"))
        if log_trades:
            trades.extend(_position_trades(name, pos))

    # 1. canonical scenario A-D (3 variants)
    scenario_positions = {}
    for v in SCENARIO_VARIANTS:
        pos, txn, sig = run_scenario_strategy(feats, ScenarioStrategyConfig(variant=v))
        scenario_positions[v] = pos
        add(f"scenario_{v}", pos, sig)
        if not txn.empty:
            txn = txn.assign(symbol=symbol, strategy=f"scenario_{v}")
            trades.extend(txn.to_dict("records"))

    # comparison variants: non-canonical full-liquidation trailing (F2) and the
    # optional SMA50-break Stage 2 stop (F4).
    for label, scfg in [
        ("scenario_full_trailfull_noncanonical",
         ScenarioStrategyConfig(variant="full", trailing_mode="non_canonical_full")),
        ("scenario_full_sma50stop",
         ScenarioStrategyConfig(variant="full", stage2_stop_sma50=True)),
    ]:
        pos, txn, sig = run_scenario_strategy(feats, scfg)
        add(label, pos, sig)
        if not txn.empty:
            trades.extend(txn.assign(symbol=symbol, strategy=label).to_dict("records"))

    # 2. Melt-Up overlays (4 variants + earnings blackout on primary)
    for v in MELTUP_VARIANTS:
        pos, sig = run_meltup_overlay(feats, MeltUpConfig(variant=v))
        add(f"meltup_{v}", pos, sig, log_trades=True)
    pos, sig = run_meltup_overlay(
        feats, MeltUpConfig(variant="primary_only", earnings_blackout=True)
    )
    add("meltup_primary_only_blackout", pos, sig, log_trades=True)

    # 3. MU $950 tier strategy (8 variants)
    for v in TIER950_VARIANTS:
        pos, sig = run_tier950_strategy(feats, Tier950Config(mode=v))
        add(f"tier950_{v}", pos, sig, log_trades=True)

    # 4. ATH breadth filter on scenario_full and buy&hold
    if compression_by_window:
        for w, comp in compression_by_window.items():
            tag = "x".join(str(x) for x in w)
            base = scenario_positions["full"]
            filtered = apply_breadth_filter(base, comp, BreadthFilterConfig(windows=w))
            add(f"scenario_full__breadth_{tag}", filtered)
            bh = apply_breadth_filter(buy_and_hold(frame), comp, BreadthFilterConfig(windows=w))
            add(f"buyhold__breadth_{tag}", bh)

    # 5. standalone tiered profit-taking (4 variants)
    for trig, rem in TIERED_PROFIT_VARIANTS:
        pos, sig = run_tiered_profit_strategy(
            feats, TieredProfitConfig(trigger_mode=trig, remainder_mode=rem)
        )
        add(f"tiered_{trig}_{rem}", pos, sig, log_trades=True)

    return summary, trades, fwd
