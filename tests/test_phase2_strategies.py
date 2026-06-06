from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_lab.features import compute_features
from backtest_lab.strategies import (
    run_scenario_strategy, ScenarioStrategyConfig,
    run_meltup_overlay, MeltUpConfig,
    run_tier950_strategy, Tier950Config,
    run_tiered_profit_strategy, TieredProfitConfig,
    apply_breadth_filter, compression_regime, BreadthFilterConfig,
    backtest_positions, ExecConfig,
)


def _feats(frame):
    return compute_features(frame)


def test_scenario_variants_produce_bounded_positions(synth_frame):
    feats = _feats(synth_frame)
    for v in ["full", "stage1_only", "stage2_only"]:
        pos, txn, sig = run_scenario_strategy(feats, ScenarioStrategyConfig(variant=v))
        assert pos.index.equals(feats.index)
        assert ((pos >= -1e-9) & (pos <= 1.0 + 1e-9)).all()
        # transaction log columns present
        assert list(txn.columns) == [
            "date", "action", "size_delta", "price", "reason", "position_after",
        ] or txn.empty


def test_scenario_strategy_no_lookahead(synth_frame):
    """Position at bars < k must be identical when future bars are dropped."""
    feats = _feats(synth_frame)
    k = 600
    full_pos, _, _ = run_scenario_strategy(feats, ScenarioStrategyConfig(variant="full"))
    trunc_pos, _, _ = run_scenario_strategy(
        feats.iloc[:k], ScenarioStrategyConfig(variant="full")
    )
    assert np.allclose(full_pos.iloc[:k].to_numpy(), trunc_pos.to_numpy())


def test_scenario_transactions_trace_to_v2_lines(synth_frame):
    feats = _feats(synth_frame)
    _, txn, _ = run_scenario_strategy(feats, ScenarioStrategyConfig(variant="full"))
    if not txn.empty:
        # every reason references a framework v2 line tag
        assert txn["reason"].str.contains(r"v2 L").all()


def test_meltup_risk_off_reduces_exposure(synth_frame):
    feats = _feats(synth_frame)
    for v in ["primary_only", "secondary_only", "stacked", "conflict_aware"]:
        pos, sig = run_meltup_overlay(feats, MeltUpConfig(variant=v))
        assert ((pos >= 0) & (pos <= 1)).all()
        if sig.any():
            # after a signal, at least one bar drops below full exposure
            assert (pos < 1.0).any()


def test_meltup_no_lookahead(synth_frame):
    feats = _feats(synth_frame)
    k = 500
    full, _ = run_meltup_overlay(feats, MeltUpConfig(variant="primary_only"))
    trunc, _ = run_meltup_overlay(feats.iloc[:k], MeltUpConfig(variant="primary_only"))
    assert np.allclose(full.iloc[:k].to_numpy(), trunc.to_numpy())


def test_tier950_does_not_enter_on_cross():
    # $950 tier is profit-taking only: position never exceeds the base long (1.0)
    idx = pd.date_range("2023-01-02", periods=300, freq="B")
    close = pd.Series(np.linspace(900, 1000, 300), index=idx)  # crosses 950
    frame = pd.DataFrame({
        "open": close, "high": close, "low": close, "close": close,
        "volume": pd.Series(2_000_000, index=idx),
    })
    feats = compute_features(frame)
    pos, ev = run_tier950_strategy(feats, Tier950Config(mode="tier_950_same_day"))
    assert pos.max() <= 1.0 + 1e-9       # never adds exposure on the cross
    assert ev.any()                       # but the tier does trigger above 950
    assert pos.iloc[-1] < 1.0             # exposure reduced after tiers


def test_tier950_hold_is_flat_full():
    idx = pd.date_range("2023-01-02", periods=50, freq="B")
    close = pd.Series(np.linspace(900, 1000, 50), index=idx)
    frame = pd.DataFrame({
        "open": close, "high": close, "low": close, "close": close,
        "volume": pd.Series(1, index=idx),
    })
    feats = compute_features(frame)
    pos, ev = run_tier950_strategy(feats, Tier950Config(mode="hold"))
    assert (pos == 1.0).all()
    assert not ev.any()


def test_tiered_profit_takes_tiers_and_is_monotone_down(synth_frame):
    feats = _feats(synth_frame)
    pos, ev = run_tiered_profit_strategy(feats, TieredProfitConfig())
    assert ((pos >= 0) & (pos <= 1)).all()
    # after entry, position is non-increasing within an in-market run (tiers only sell)
    held = pos[pos > 0]
    assert held.diff().dropna().le(1e-9).all()


def test_breadth_filter_gates_exposure():
    idx = pd.date_range("2023-01-02", periods=10, freq="B")
    base = pd.Series(1.0, index=idx)
    comp = pd.Series([False] * 5 + [True] * 5, index=idx)
    filtered = apply_breadth_filter(base, comp, BreadthFilterConfig(mode="gate", risk_off_scale=0.0))
    assert (filtered.iloc[:5] == 1.0).all()
    assert (filtered.iloc[5:] == 0.0).all()


def test_breadth_compression_regime_is_bool(synth_frame):
    proxy = pd.DataFrame({"A": synth_frame["close"], "B": synth_frame["close"] * 1.01})
    comp = compression_regime(proxy, (11, 7, 3))
    assert comp.dtype == bool
    assert comp.index.equals(synth_frame.index)
