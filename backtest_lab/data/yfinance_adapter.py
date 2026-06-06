"""Live daily-bar adapter backed by yfinance.

Requires network access to Yahoo Finance and the optional ``yfinance``
dependency. In sandboxed/CI environments without egress this adapter will
raise; the pipeline falls back to the synthetic source by default. Use
``--source yfinance`` to opt in.
"""

from __future__ import annotations

import pandas as pd

from .base import DataAdapter, OHLCVDataset, Provenance, DataIntegrityError


class YFinanceAdapter(DataAdapter):
    """Adjusted daily OHLCV from Yahoo Finance via the ``yfinance`` package."""

    name = "yfinance"
    adjusted = True

    def __init__(self, auto_adjust: bool = True):
        # auto_adjust=True -> split/dividend-adjusted OHLC (spec L72).
        self.auto_adjust = auto_adjust
        self.adjusted = auto_adjust

    def fetch(self, symbol: str, start: str, end: str) -> OHLCVDataset:
        try:
            import yfinance as yf
        except ImportError as exc:  # pragma: no cover - env dependent
            raise DataIntegrityError(
                "yfinance not installed; `pip install yfinance` or use --source synthetic"
            ) from exc

        raw = yf.download(
            symbol,
            start=start,
            end=end,
            auto_adjust=self.auto_adjust,
            progress=False,
            actions=False,
        )
        if raw is None or raw.empty:  # pragma: no cover - network dependent
            raise DataIntegrityError(
                f"yfinance returned no data for {symbol} ({start}..{end}); "
                "check symbol/network"
            )

        # yfinance may return a MultiIndex column frame for single symbols.
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        raw = raw.rename(columns=str.lower)
        frame = raw[["open", "high", "low", "close", "volume"]].copy()
        frame.index = pd.DatetimeIndex(frame.index).tz_localize(None)
        frame.index.name = "date"
        frame = frame.sort_index()

        prov = Provenance(
            symbol=symbol,
            source=self.name,
            adjusted=self.adjusted,
            start=str(frame.index[0].date()),
            end=str(frame.index[-1].date()),
            n_rows=len(frame),
            notes=f"yfinance auto_adjust={self.auto_adjust}",
        )
        return OHLCVDataset(frame=frame, provenance=prov)
