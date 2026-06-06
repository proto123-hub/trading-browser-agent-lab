from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_lab.strategies import (
    all_baselines,
    backtest_positions,
    ExecConfig,
    buy_and_hold,
    cash_only,
)


def test_all_five_baselines_present(synth_frame):
    bl = all_baselines(synth_frame)
    assert set(bl) == {
        "buy_and_hold", "cash_only", "ma_50_200", "breakout_20", "random_placebo",
    }
    for pos in bl.values():
        assert pos.index.equals(synth_frame.index)
        v = pos.dropna()
        assert ((v >= 0) & (v <= 1)).all()


def test_cash_only_is_flat(synth_frame):
    res = backtest_positions(synth_frame, cash_only(synth_frame))
    assert res.metrics["exposure"] == 0.0
    assert abs(res.metrics["total_return"]) < 1e-9


def test_execution_has_one_bar_delay():
    # position is 1 from the start, but effective position lags by one bar.
    idx = pd.date_range("2023-01-02", periods=5, freq="B")
    frame = pd.DataFrame({
        "open": [10, 11, 12, 13, 14],
        "high": [10, 11, 12, 13, 14],
        "low": [10, 11, 12, 13, 14],
        "close": [10.0, 11.0, 12.0, 13.0, 14.0],
        "volume": [1, 1, 1, 1, 1],
    }, index=idx)
    pos = pd.Series(1.0, index=idx)
    res = backtest_positions(frame, pos, ExecConfig(slippage_bps=0.0))
    # first bar return must be 0 (no position yet); position effective from bar 2.
    assert res.returns.iloc[0] == 0.0
    assert res.position.iloc[0] == 0.0
    assert res.position.iloc[1] == 1.0


def test_slippage_reduces_return():
    idx = pd.date_range("2023-01-02", periods=10, freq="B")
    close = pd.Series(np.linspace(100, 120, 10), index=idx)
    frame = pd.DataFrame({
        "open": close, "high": close, "low": close, "close": close,
        "volume": pd.Series(1, index=idx),
    })
    pos = pd.Series([0, 1, 1, 0, 1, 1, 0, 1, 1, 0], index=idx, dtype=float)
    no_cost = backtest_positions(frame, pos, ExecConfig(slippage_bps=0.0))
    with_cost = backtest_positions(frame, pos, ExecConfig(slippage_bps=50.0))
    assert with_cost.metrics["total_return"] < no_cost.metrics["total_return"]


def test_random_placebo_is_deterministic(synth_frame):
    from backtest_lab.strategies.baselines import random_placebo
    a = random_placebo(synth_frame, seed=7)
    b = random_placebo(synth_frame, seed=7)
    assert a.equals(b)
