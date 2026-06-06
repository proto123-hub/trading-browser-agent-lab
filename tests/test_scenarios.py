from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_lab.scenarios.labeler import (
    label_scenarios,
    rebreakthrough_score,
    consecutive,
    ScenarioConfig,
)


def _feats(above, bearish, bullish=None, vol_mult=None):
    n = len(above)
    idx = pd.date_range("2023-01-02", periods=n, freq="B")
    above = pd.Series(above, index=idx, dtype=bool)
    bearish = pd.Series(bearish, index=idx, dtype=bool)
    if bullish is None:
        bullish = ~bearish
    else:
        bullish = pd.Series(bullish, index=idx, dtype=bool)
    below = pd.Series(False, index=idx, dtype=bool)
    in_cloud = (~above) & (~below)
    vm = pd.Series(1.5 if vol_mult is None else vol_mult, index=idx, dtype=float) \
        if np.isscalar(vol_mult) or vol_mult is None else pd.Series(vol_mult, index=idx)
    return pd.DataFrame({
        "above_cloud": above,
        "below_cloud": below,
        "in_cloud": in_cloud,
        "bearish_cloud": bearish,
        "bullish_cloud": bullish,
        "vol_mult": vm,
    }, index=idx)


def test_consecutive_helper():
    s = pd.Series([False, True, True, True, False])
    c = consecutive(s, 2)
    assert list(c.fillna(False)) == [False, False, True, True, False]


def test_scenario_a_fires_on_second_consecutive_close():
    # below bearish cloud, then 2 consecutive closes above -> A fires on 2nd.
    above = [False, False, False, False, False, True, True, True]
    bearish = [True] * 8
    feats = _feats(above, bearish)
    labels = label_scenarios(feats, ScenarioConfig(confirm_days=2))
    a = labels["scenario_a"]
    assert not a.iloc[5]          # first close above: not yet confirmed
    assert a.iloc[6]              # second consecutive close above: A fires
    assert not a.iloc[:5].any()   # nothing before the breakout


def test_single_close_above_does_not_fire_a_but_fires_c():
    # one close above bearish cloud, then back inside -> failed breakthrough (C).
    above = [False, False, False, False, True, False, False]
    bearish = [True] * 7
    feats = _feats(above, bearish)
    labels = label_scenarios(feats)
    assert not labels["scenario_a"].any()
    assert labels["scenario_c"].iloc[5]   # back inside the bar after the attempt


def test_scenario_c_fake_when_low_volume():
    above = [False, False, False, True, False, False]
    bearish = [True] * 6
    vol = [1.5, 1.5, 1.5, 0.7, 1.5, 1.5]   # attempt bar (idx 3) below 20d avg
    feats = _feats(above, bearish, vol_mult=vol)
    labels = label_scenarios(feats)
    assert labels["scenario_c"].iloc[4]
    assert labels["scenario_c_fake"].iloc[4]


def test_scenario_d_bullish_continuation():
    above = [True, True, True]
    bearish = [False, False, False]
    feats = _feats(above, bearish)
    labels = label_scenarios(feats)
    assert labels["scenario_d"].all()


def test_scenarios_no_lookahead():
    above = [False, False, True, True, False, True, True, True, False, False]
    bearish = [True] * 10
    feats = _feats(above, bearish)
    full = label_scenarios(feats)
    trunc = label_scenarios(feats.iloc[:7])
    cols = full.columns
    assert (full[cols].iloc[:7].reset_index(drop=True)
            == trunc[cols].reset_index(drop=True)).all().all()


def test_rebreakthrough_score_full_vs_half():
    idx = pd.to_datetime(["2023-01-02", "2023-02-02"])
    feats = pd.DataFrame({
        "close": [100.0, 110.0],
        "sma50": [105.0, 108.0],
        "sma200": [95.0, 96.0],
        "vol_mult": [1.0, 1.6],          # +60% > +30% -> volume check pass
        "cloud_thickness": [10.0, 5.0],  # 50% thinner -> cloud check pass
        "rsi_wilder_14": [45.0, 60.0],   # higher RSI -> divergence pass
        "tenkan_gt_kijun": [False, True],
    }, index=idx)
    res = rebreakthrough_score(feats, idx[0], idx[1], consolidation_low=90.0)
    assert res["score"] >= 4
    assert res["verdict"] == "full_size"

    # weaken: low second volume, fat cloud, falling rsi, no TK cross
    feats2 = feats.copy()
    feats2.loc[idx[1], ["vol_mult", "cloud_thickness", "rsi_wilder_14", "tenkan_gt_kijun"]] = \
        [0.9, 12.0, 40.0, False]
    feats2.loc[idx[1], "close"] = 80.0   # below consolidation low -> divergence fail
    feats2.loc[idx[1], ["sma50", "sma200"]] = [120.0, 120.0]  # support fail
    res2 = rebreakthrough_score(feats2, idx[0], idx[1], consolidation_low=90.0)
    assert res2["score"] <= 3
    assert res2["verdict"] == "max_50pct_size"
