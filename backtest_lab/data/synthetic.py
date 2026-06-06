"""Deterministic synthetic OHLCV source (offline default).

Generates reproducible daily bars from a per-symbol seed so the pipeline and
tests run with no network. The series deliberately contains multiple regimes
(bear -> base -> bull) so Ichimoku cloud-color transitions and the canonical
A-D scenarios actually fire. This is NOT market data; it is a fixture for
exercising the harness. Real research uses the yfinance/Polygon adapters.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from .base import DataAdapter, OHLCVDataset, Provenance


def _seed_for(symbol: str) -> int:
    h = hashlib.sha256(symbol.encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big")


class SyntheticAdapter(DataAdapter):
    """Reproducible synthetic daily bars with bear/base/bull regimes."""

    name = "synthetic"
    adjusted = True

    def __init__(self, base_price: float = 100.0):
        self.base_price = base_price

    def fetch(self, symbol: str, start: str, end: str) -> OHLCVDataset:
        # Business-day calendar (Mon-Fri) so warmup math matches trading days.
        index = pd.bdate_range(start=start, end=end)
        n = len(index)
        if n == 0:
            raise ValueError(f"empty date range for {symbol}: {start}..{end}")

        rng = np.random.default_rng(_seed_for(symbol))

        # Regime drift schedule: bear, then sideways base, then bull. Split the
        # window into thirds so all regimes appear regardless of length.
        third = max(n // 3, 1)
        drift = np.empty(n)
        drift[:third] = -0.0011            # bear
        drift[third : 2 * third] = 0.0001  # sideways
        drift[2 * third :] = 0.0013        # bull
        vol = 0.018

        shocks = rng.normal(0.0, vol, size=n)
        log_ret = drift + shocks
        close = self.base_price * np.exp(np.cumsum(log_ret))

        # Build OHLC around close with intrabar noise.
        prev_close = np.empty(n)
        prev_close[0] = self.base_price
        prev_close[1:] = close[:-1]
        open_ = prev_close * (1.0 + rng.normal(0.0, 0.004, size=n))
        hi_noise = np.abs(rng.normal(0.0, 0.006, size=n))
        lo_noise = np.abs(rng.normal(0.0, 0.006, size=n))
        high = np.maximum(open_, close) * (1.0 + hi_noise)
        low = np.minimum(open_, close) * (1.0 - lo_noise)

        # Volume: lognormal, with bursts on large moves so volume filters bite.
        base_vol = rng.lognormal(mean=13.0, sigma=0.25, size=n)
        burst = 1.0 + 3.0 * np.abs(log_ret) / vol
        volume = np.round(base_vol * burst).astype("int64")

        frame = pd.DataFrame(
            {
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            },
            index=index,
        )
        frame.index.name = "date"

        prov = Provenance(
            symbol=symbol,
            source=self.name,
            adjusted=self.adjusted,
            start=str(index[0].date()),
            end=str(index[-1].date()),
            n_rows=n,
            notes="deterministic synthetic fixture (bear/base/bull); not market data",
        )
        return OHLCVDataset(frame=frame, provenance=prov)
