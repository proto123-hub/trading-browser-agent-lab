from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_lab.events import load_events, event_window_flags, events_for
from backtest_lab.forward_returns import forward_returns, signal_forward_returns


def test_load_events_yaml():
    events = load_events("events.yaml")
    assert len(events) >= 1
    mu = events_for(events, "MU")
    assert any(e.kind == "meltup_stress" for e in mu)
    # the March 18 stress date is present and parsed
    assert any(str(e.date.date()) == "2026-03-18" for e in mu)


def test_event_window_flags_are_annotations_only():
    idx = pd.bdate_range("2026-03-02", "2026-04-01")
    events = load_events("events.yaml")
    flags = event_window_flags(idx, events, "MU", pre=2, post=2)
    assert flags["named_event_window"].any()
    # flags carry no price data -- annotation columns only
    assert set(flags.columns) == {"named_event", "named_event_window", "named_event_kind"}


def test_forward_returns_use_future_prices_only():
    close = pd.Series(np.arange(1.0, 21.0))
    fwd = forward_returns(close, [1, 5])
    # fwd_1 at t = close[t+1]/close[t]-1
    assert np.isclose(fwd["fwd_1"].iloc[0], close.iloc[1] / close.iloc[0] - 1)
    # last rows are NaN (no future data)
    assert np.isnan(fwd["fwd_5"].iloc[-1])


def test_signal_forward_returns_rows():
    close = pd.Series(np.linspace(100, 120, 30), index=pd.date_range("2023-01-02", periods=30, freq="B"))
    sig = pd.Series(False, index=close.index)
    sig.iloc[[3, 10]] = True
    out = signal_forward_returns(close, sig, "X", "test")
    assert len(out) == 2
    assert {"date", "symbol", "strategy", "fwd_1", "fwd_60"}.issubset(out.columns)
