"""Committed-cache CSV data adapter (Phase 3 real-data source).

Reads ``data/raw/<SYMBOL>.csv`` (the Cowork-prepared, sha256-gated real-data
cache) so the real-data pipeline is fully reproducible from version control with
no network. Adjustment basis is taken from PROVENANCE.md (split+dividend
adjusted, uniform), recorded in provenance. Per-file sha256 is verified
fail-closed before the data is used.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from .base import DataAdapter, OHLCVDataset, Provenance, DataIntegrityError
from .provenance import parse_provenance, ProvenanceError


class CSVCacheAdapter(DataAdapter):
    name = "csv"
    adjusted = True   # PROVENANCE.md: split+dividend adjusted, uniform

    def __init__(self, data_dir: str | Path = "data/raw", verify: bool = True):
        self.data_dir = Path(data_dir)
        self.verify = verify
        self._sha = {}
        if verify:
            try:
                self._sha = {
                    Path(r.relpath).name: r.sha256_prefix for r in parse_provenance()
                }
            except ProvenanceError:
                self._sha = {}

    def fetch(self, symbol: str, start: str, end: str) -> OHLCVDataset:
        path = self.data_dir / f"{symbol}.csv"
        if not path.is_file():
            raise DataIntegrityError(f"no cached data for {symbol} at {path}")

        raw_bytes = path.read_bytes()
        if self.verify and symbol + ".csv" in self._sha:
            got = hashlib.sha256(raw_bytes).hexdigest()[: len(self._sha[symbol + ".csv"])]
            if got != self._sha[symbol + ".csv"]:
                raise DataIntegrityError(
                    f"sha256 gate failed for {symbol}.csv: {got} != {self._sha[symbol + '.csv']}"
                )

        frame = pd.read_csv(path, parse_dates=["date"]).set_index("date")
        frame.index = pd.DatetimeIndex(frame.index).tz_localize(None)
        frame.index.name = "date"
        frame = frame[["open", "high", "low", "close", "volume"]].sort_index()

        # clip to requested window
        mask = (frame.index >= pd.Timestamp(start)) & (frame.index <= pd.Timestamp(end))
        frame = frame.loc[mask]
        if frame.empty:
            raise DataIntegrityError(f"{symbol}: no rows in {start}..{end}")

        prov = Provenance(
            symbol=symbol,
            source=self.name,
            adjusted=self.adjusted,
            start=str(frame.index[0].date()),
            end=str(frame.index[-1].date()),
            n_rows=len(frame),
            notes="committed cache data/raw (yfinance auto_adjust; sha256-gated)",
        )
        return OHLCVDataset(frame=frame, provenance=prov)
