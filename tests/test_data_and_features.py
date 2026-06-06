from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest_lab.data.base import (
    OHLCVDataset,
    Provenance,
    assert_consistent_adjustment,
    DataIntegrityError,
)
from backtest_lab.data.synthetic import SyntheticAdapter
from backtest_lab.features import compute_features


def _dataset(symbol, adjusted):
    ds = SyntheticAdapter().fetch(symbol, "2022-01-01", "2022-06-30")
    prov = Provenance(
        symbol=symbol, source="synthetic", adjusted=adjusted,
        start="2022-01-01", end="2022-06-30", n_rows=len(ds.frame),
    )
    return OHLCVDataset(frame=ds.frame, provenance=prov)


def test_fail_closed_on_mixed_adjustment():
    datasets = {
        "A": _dataset("A", adjusted=True),
        "B": _dataset("B", adjusted=False),
    }
    with pytest.raises(DataIntegrityError):
        assert_consistent_adjustment(datasets)


def test_consistent_adjustment_ok():
    datasets = {
        "A": _dataset("A", adjusted=True),
        "B": _dataset("B", adjusted=True),
    }
    assert_consistent_adjustment(datasets)  # no raise


def test_synthetic_is_deterministic():
    a = SyntheticAdapter().fetch("MU", "2020-01-01", "2021-01-01").frame
    b = SyntheticAdapter().fetch("MU", "2020-01-01", "2021-01-01").frame
    pd.testing.assert_frame_equal(a, b)


def test_dataset_rejects_unsorted_index():
    frame = SyntheticAdapter().fetch("X", "2022-01-01", "2022-03-01").frame
    frame = frame.iloc[::-1]  # descending
    prov = Provenance("X", "synthetic", True, "2022-01-01", "2022-03-01", len(frame))
    with pytest.raises(DataIntegrityError):
        OHLCVDataset(frame=frame, provenance=prov)


def test_compute_features_columns(synth_frame):
    feats = compute_features(synth_frame)
    for col in [
        "tenkan", "kijun", "senkou_a", "senkou_b", "cloud_top", "bearish_cloud",
        "rsi_wilder_14", "rsi_cutler_14", "atr_14", "bb_upper", "vol_mult",
        "sma50", "sma200", "mu_primary", "mu_secondary", "pct_below_ath",
    ]:
        assert col in feats.columns, col
    # no duplicated columns after assembly
    assert not feats.columns.duplicated().any()


def test_features_no_lookahead(synth_frame):
    """Features at bars < k must be unchanged when future bars are removed."""
    k = 500
    full = compute_features(synth_frame)
    trunc = compute_features(synth_frame.iloc[:k])
    check_cols = ["rsi_wilder_14", "atr_14", "sma50", "sma200", "cloud_top", "vol_mult"]
    a = full[check_cols].iloc[: k - 1]
    b = trunc[check_cols].iloc[: k - 1]
    both = a.notna() & b.notna()
    for c in check_cols:
        m = both[c]
        assert np.allclose(a[c][m], b[c][m]), f"lookahead leak in {c}"
