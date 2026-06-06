"""Baseline strategies (spec L217-223).

Five baselines, each returning a long/flat position Series in {0, 1} aligned to
the input frame. All use only past/current data (no lookahead); the engine
applies the additional one-bar execution delay.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..features.volume import sma


def buy_and_hold(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(1.0, index=frame.index, name="buy_and_hold")


def cash_only(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(0.0, index=frame.index, name="cash_only")


def ma_50_200(frame: pd.DataFrame) -> pd.Series:
    """Long while SMA50 > SMA200 (golden-cross trend filter)."""
    close = frame["close"]
    pos = (sma(close, 50) > sma(close, 200)).astype("float64")
    pos[sma(close, 200).isna()] = 0.0
    return pos.rename("ma_50_200")


def breakout_20(frame: pd.DataFrame) -> pd.Series:
    """Donchian: enter long above prior 20-day high, exit below prior 20-day low."""
    close = frame["close"]
    hi = close.rolling(20).max().shift(1)
    lo = close.rolling(20).min().shift(1)
    pos = pd.Series(np.nan, index=frame.index)
    pos[close > hi] = 1.0
    pos[close < lo] = 0.0
    pos = pos.ffill().fillna(0.0)
    return pos.rename("breakout_20")


def random_placebo(frame: pd.DataFrame, template: pd.Series | None = None, seed: int = 7) -> pd.Series:
    """Random-entry placebo with holding periods matched to ``template``.

    Reproduces the number of trades and the holding-period distribution of the
    template strategy (default: the 50/200 MA filter) but places entries at
    random start dates, so any edge over this baseline is not from exposure
    alone (spec L223, L278).
    """
    template = template if template is not None else ma_50_200(frame)
    n = len(frame)
    pos = np.zeros(n)

    # extract holding-period lengths from the template
    in_mkt = (template.fillna(0.0).to_numpy() > 0)
    holds = []
    start = None
    for i, flag in enumerate(in_mkt):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            holds.append(i - start)
            start = None
    if start is not None:
        holds.append(n - start)

    rng = np.random.default_rng(seed)
    for length in holds:
        if length <= 0 or length >= n:
            continue
        s = int(rng.integers(0, n - length))
        pos[s : s + length] = 1.0
    return pd.Series(pos, index=frame.index, name="random_placebo")


def all_baselines(frame: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "buy_and_hold": buy_and_hold(frame),
        "cash_only": cash_only(frame),
        "ma_50_200": ma_50_200(frame),
        "breakout_20": breakout_20(frame),
        "random_placebo": random_placebo(frame),
    }
