from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest_lab.data.provenance import verify_data_cache, parse_provenance, ProvenanceError
from backtest_lab.data.csv_adapter import CSVCacheAdapter
from backtest_lab.data.base import DataIntegrityError
from backtest_lab import robustness as rb
from backtest_lab.events import load_events, events_for


def test_provenance_gate_passes_on_committed_cache():
    verified = verify_data_cache()
    assert len(verified) >= 9
    assert all(v and len(v) == 16 for v in verified.values())


def test_provenance_gate_fails_on_tamper(tmp_path):
    # build a fake PROVENANCE with a wrong hash for a copied file
    (tmp_path / "data" / "raw").mkdir(parents=True)
    f = tmp_path / "data" / "raw" / "X.csv"
    f.write_text("date,open,high,low,close,volume\n2020-01-02,1,1,1,1,1\n")
    prov = tmp_path / "PROVENANCE.md"
    prov.write_text("- data/raw/X.csv — sha256 deadbeefdeadbeef\n")
    with pytest.raises(ProvenanceError):
        verify_data_cache(provenance_path=prov, data_root=tmp_path)


def test_csv_adapter_loads_real_symbol():
    ds = CSVCacheAdapter().fetch("MU", "2019-01-02", "2026-06-05")
    assert ds.provenance.adjusted is True
    assert list(ds.frame.columns) == ["open", "high", "low", "close", "volume"]
    assert ds.frame.index.is_monotonic_increasing
    assert len(ds.frame) > 1000


def test_csv_adapter_missing_symbol_fails_closed():
    with pytest.raises(DataIntegrityError):
        CSVCacheAdapter().fetch("NOPE", "2019-01-02", "2026-06-05")


def test_csv_adapter_clip_window():
    ds = CSVCacheAdapter().fetch("MU", "2024-01-01", "2024-12-31")
    assert ds.frame.index[0].year == 2024
    assert ds.frame.index[-1].year == 2024


def _synth_returns(n=800, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2019-01-02", periods=n)
    return pd.Series(rng.normal(0.0005, 0.015, n), index=idx)


def test_walk_forward_by_year():
    r = _synth_returns()
    pos = pd.Series(1.0, index=r.index)
    wf = rb.walk_forward_by_year(r, pos)
    assert "year" in wf.columns and len(wf) >= 3
    assert "sharpe" in wf.columns


def test_classify_regime_labels():
    idx = pd.bdate_range("2019-01-02", periods=600)
    # rising then crash then flat
    close = pd.Series(np.r_[np.linspace(100, 200, 300), np.linspace(200, 120, 150), np.full(150, 120)], index=idx)
    reg = rb.classify_regime(close)
    assert set(reg.unique()).issubset({"bull", "bear", "sideways", "warmup"})
    assert (reg == "bear").any()


def test_bootstrap_ci_brackets_point():
    r = _synth_returns(seed=3)
    out = rb.bootstrap_ci(r, n_boot=300, seed=5)
    assert out["lo"] <= out["point"] <= out["hi"]
    assert out["n"] == len(r)


def test_leave_one_out_rows():
    r1 = _synth_returns(seed=1); r2 = _synth_returns(seed=2); r3 = _synth_returns(seed=3)
    loo = rb.leave_one_out({"A": r1, "B": r2, "C": r3})
    assert set(loo["left_out"]) == {"(none)", "A", "B", "C"}


def test_events_has_june5_stress():
    events = load_events("events.yaml")
    mu = events_for(events, "MU")
    assert any(str(e.date.date()) == "2026-06-05" for e in mu)
