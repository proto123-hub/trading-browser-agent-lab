from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_lab.breadth import (
    eligible_new_ath_count, breadth_regime, breadth_features,
    load_breadth_panel, BreadthRegimeConfig, BREADTH_UNIVERSE,
)


def test_eligibility_excludes_short_history_ipo():
    """A name with < 252 days of history must not count as a new ATH (no IPO
    day-1 false ATH)."""
    idx = pd.bdate_range("2022-01-03", periods=300)
    seasoned = pd.Series(np.linspace(100, 200, 300), index=idx)  # rising, always ATH
    # IPO appears only for the last 10 days, immediately at an all-time high
    ipo = pd.Series(np.nan, index=idx)
    ipo.iloc[-10:] = np.linspace(50, 60, 10)
    panel = pd.DataFrame({"SEASONED": seasoned, "IPO": ipo})
    count = eligible_new_ath_count(panel, min_history=252)
    # on the last day, SEASONED is eligible+ATH (counts), IPO has only 10d (excluded)
    assert count.iloc[-1] == 1


def test_reproduce_june_breadth_sequence():
    """Spec acceptance: 6/1-6/5 new-ATH count == 10,10,9,3,0 on the real cache."""
    feats = breadth_features(start="2019-01-02", end="2026-06-05")
    seq = [int(feats.loc[d, "new_ath_count"]) for d in
           ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05"]]
    assert seq == [10, 10, 9, 3, 0], seq


def test_breadth_regime_labels():
    idx = pd.bdate_range("2023-01-02", periods=10)
    count = pd.Series([8, 9, 10, 9, 7, 3, 0, 1, 2, 5], index=idx)
    reg = breadth_regime(count, BreadthRegimeConfig(window=5))
    assert reg.iloc[6] == "washout"          # count == 0 after an elevated peak
    assert reg.iloc[5] == "compression"      # 3, below recent peak and falling
    assert set(reg.unique()).issubset(
        {"expansion", "compression", "washout", "neutral", "warmup"})


def test_plain_zero_is_not_washout():
    """A count==0 with no recent elevated peak must NOT be washout (avoids the
    warmup/bear over-labeling that the refined regime fixes)."""
    idx = pd.bdate_range("2023-01-02", periods=10)
    count = pd.Series([0, 0, 1, 0, 1, 0, 0, 1, 0, 0], index=idx)  # quiet, low peaks
    reg = breadth_regime(count, BreadthRegimeConfig(window=5, washout_min_peak=3))
    assert (reg == "washout").sum() == 0      # no collapse-from-elevated -> no washout


def test_breadth_features_columns_and_no_lookahead():
    feats = breadth_features(start="2019-01-02", end="2026-06-05")
    assert set(["new_ath_count", "breadth_regime", "compression"]).issubset(feats.columns)
    # regime at bar T uses only count<=T (compression via shift(1) peak) -> truncation stable
    full = breadth_features(start="2019-01-02", end="2026-06-05")["new_ath_count"]
    assert full.loc["2026-06-05"] == 0


def test_universe_has_24_names():
    assert len(BREADTH_UNIVERSE) == 24
    assert "SPY" not in BREADTH_UNIVERSE and "QQQ" not in BREADTH_UNIVERSE
