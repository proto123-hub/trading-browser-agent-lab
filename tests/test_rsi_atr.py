from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_lab.features.rsi import wilder_rsi, cutler_rsi
from backtest_lab.features.atr import atr, true_range


def test_rsi_bounds(synth_frame):
    rsi = wilder_rsi(synth_frame["close"])
    valid = rsi.dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_rsi_all_up_is_100():
    close = pd.Series(np.arange(1.0, 60.0))  # strictly increasing
    rsi = wilder_rsi(close)
    assert rsi.dropna().iloc[-1] == 100.0


def test_rsi_all_down_is_0():
    close = pd.Series(np.arange(60.0, 1.0, -1.0))  # strictly decreasing
    rsi = wilder_rsi(close)
    assert rsi.dropna().iloc[-1] == 0.0


def test_wilder_seed_is_sma_of_first_gains():
    # Construct deltas with known gains; check seed avg_gain at index `period`.
    period = 14
    close = pd.Series(np.cumsum(np.r_[0.0, np.ones(20)]))  # +1 each step
    # all gains == 1, all losses == 0 -> avg_loss 0 -> RSI 100 at index `period`
    rsi = wilder_rsi(close, period)
    assert rsi.iloc[period] == 100.0
    assert np.isnan(rsi.iloc[period - 1])  # not enough data before seed


def test_cutler_differs_from_wilder(synth_frame):
    w = wilder_rsi(synth_frame["close"])
    c = cutler_rsi(synth_frame["close"])
    valid = w.notna() & c.notna()
    # they should not be identical series (distinct smoothing)
    assert not np.allclose(w[valid], c[valid])


def test_atr_positive_and_wilder_seed(synth_frame):
    a = atr(synth_frame)
    valid = a.dropna()
    assert (valid > 0).all()
    tr = true_range(synth_frame)
    seed = tr.iloc[1:15].mean()
    assert np.isclose(a.iloc[14], seed)


def test_true_range_includes_gaps():
    frame = pd.DataFrame({
        "open": [10, 12, 9],
        "high": [11, 13, 10],
        "low": [9, 11, 8],
        "close": [10, 12, 9],
    })
    tr = true_range(frame)
    # bar 1: high-low=2, |high-prevclose|=|13-10|=3, |low-prevclose|=|11-10|=1 -> 3
    assert tr.iloc[1] == 3
