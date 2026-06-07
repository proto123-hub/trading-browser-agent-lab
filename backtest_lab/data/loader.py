"""Adapter selection, universe loading, and raw-input caching.

Caches raw inputs separately from derived features (spec L84): raw OHLCV is
parquet/CSV-cached under ``cache/raw/`` keyed by source+symbol+range.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .base import (
    DataAdapter,
    OHLCVDataset,
    Provenance,
    assert_consistent_adjustment,
)
from .synthetic import SyntheticAdapter
from .yfinance_adapter import YFinanceAdapter
from .polygon_adapter import PolygonAdapter
from .csv_adapter import CSVCacheAdapter

_ADAPTERS = {
    "synthetic": SyntheticAdapter,
    "yfinance": YFinanceAdapter,
    "polygon": PolygonAdapter,
    "csv": CSVCacheAdapter,
}


def get_adapter(source: str, **kwargs) -> DataAdapter:
    try:
        cls = _ADAPTERS[source]
    except KeyError:
        raise ValueError(
            f"unknown data source {source!r}; choose from {sorted(_ADAPTERS)}"
        ) from None
    return cls(**kwargs)


def _cache_paths(cache_dir: Path, source: str, symbol: str, start: str, end: str):
    key = f"{source}__{symbol}__{start}__{end}"
    return cache_dir / f"{key}.csv", cache_dir / f"{key}.prov.json"


def load_universe(
    symbols: list[str],
    start: str,
    end: str,
    source: str = "synthetic",
    cache_dir: str | Path | None = "cache/raw",
    use_cache: bool = True,
) -> dict[str, OHLCVDataset]:
    """Load OHLCV for ``symbols``, caching raw inputs, with fail-closed checks."""
    adapter = get_adapter(source)
    cache = Path(cache_dir) if cache_dir else None
    if cache:
        cache.mkdir(parents=True, exist_ok=True)

    out: dict[str, OHLCVDataset] = {}
    for sym in symbols:
        csv_path = prov_path = None
        if cache:
            csv_path, prov_path = _cache_paths(cache, source, sym, start, end)
        if use_cache and csv_path and csv_path.exists() and prov_path.exists():
            frame = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            frame.index.name = "date"
            prov = Provenance(**json.loads(prov_path.read_text()))
            out[sym] = OHLCVDataset(frame=frame, provenance=prov)
            continue

        ds = adapter.fetch(sym, start, end)
        if cache and csv_path:
            ds.frame.to_csv(csv_path)
            prov_path.write_text(json.dumps(ds.provenance.to_dict(), indent=2))
        out[sym] = ds

    assert_consistent_adjustment(out)
    return out
