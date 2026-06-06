"""Data layer: adapter pattern over OHLCV sources.

Default source is :class:`~backtest_lab.data.synthetic.SyntheticAdapter`, a
deterministic offline generator so the full pipeline and the test suite run
without network access. Swap in :class:`~backtest_lab.data.yfinance_adapter.
YFinanceAdapter` for live daily bars, or the Polygon stub for the planned
cross-validation source (spec "Universe and Data", FIX-6).
"""

from __future__ import annotations

from .base import DataAdapter, OHLCVDataset, Provenance, DataIntegrityError
from .loader import load_universe, get_adapter

__all__ = [
    "DataAdapter",
    "OHLCVDataset",
    "Provenance",
    "DataIntegrityError",
    "load_universe",
    "get_adapter",
]
