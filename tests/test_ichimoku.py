from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_lab.features.ichimoku import ichimoku, DISPLACEMENT


def test_senkou_displacement(synth_frame):
    """senkou_a[T] must equal ((tenkan+kijun)/2) computed 26 bars earlier."""
    ich = ichimoku(synth_frame)
    raw_a = (ich["tenkan"] + ich["kijun"]) / 2.0
    shifted = raw_a.shift(DISPLACEMENT)
    valid = ich["senkou_a"].notna() & shifted.notna()
    assert valid.sum() > 100
    assert np.allclose(ich["senkou_a"][valid], shifted[valid])


def test_senkou_b_displacement(synth_frame):
    ich = ichimoku(synth_frame)
    high, low = synth_frame["high"], synth_frame["low"]
    raw_b = (high.rolling(52).max() + low.rolling(52).min()) / 2.0
    shifted = raw_b.shift(DISPLACEMENT)
    valid = ich["senkou_b"].notna() & shifted.notna()
    assert np.allclose(ich["senkou_b"][valid], shifted[valid])


def test_cloud_no_lookahead(synth_frame):
    """Cloud values at bars <= k must not change when future bars are dropped."""
    k = 400
    full = ichimoku(synth_frame)
    trunc = ichimoku(synth_frame.iloc[:k])
    cols = ["senkou_a", "senkou_b", "cloud_top", "cloud_bottom"]
    a = full[cols].iloc[: k - 1]
    b = trunc[cols].iloc[: k - 1]
    both = a.notna() & b.notna()
    for c in cols:
        m = both[c]
        assert np.allclose(a[c][m], b[c][m]), f"lookahead leak in {c}"


def test_cloud_color_consistency(synth_frame):
    ich = ichimoku(synth_frame)
    valid = ich["senkou_a"].notna() & ich["senkou_b"].notna()
    bearish = ich["bearish_cloud"][valid]
    expected = (ich["senkou_a"] < ich["senkou_b"])[valid]
    assert (bearish == expected).all()
    # bearish and bullish are mutually exclusive where defined
    assert not (ich["bearish_cloud"] & ich["bullish_cloud"]).any()
