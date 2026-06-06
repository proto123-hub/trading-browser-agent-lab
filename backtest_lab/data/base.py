"""Data adapter base classes, dataset container, and provenance.

Data-quality requirements implemented here (spec L79-84):
- Store data provenance per symbol and dataset.
- Fail closed when adjusted/unadjusted price series are mixed.
- Cache raw inputs and derived features separately (see loader.py).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

import pandas as pd

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataIntegrityError(RuntimeError):
    """Raised on data-quality violations (e.g. adjusted/unadjusted mixing)."""


@dataclass(frozen=True)
class Provenance:
    """Where a symbol's data came from and how it was priced."""

    symbol: str
    source: str            # adapter name, e.g. "synthetic", "yfinance"
    adjusted: bool         # True if split/dividend-adjusted close
    start: str
    end: str
    n_rows: int
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OHLCVDataset:
    """A single symbol's daily OHLCV frame plus provenance.

    ``frame`` is indexed by a tz-naive ``DatetimeIndex`` (daily, ascending) with
    columns :data:`OHLCV_COLUMNS`.
    """

    frame: pd.DataFrame
    provenance: Provenance

    def __post_init__(self) -> None:
        missing = [c for c in OHLCV_COLUMNS if c not in self.frame.columns]
        if missing:
            raise DataIntegrityError(
                f"{self.provenance.symbol}: missing OHLCV columns {missing}"
            )
        if not isinstance(self.frame.index, pd.DatetimeIndex):
            raise DataIntegrityError(
                f"{self.provenance.symbol}: index must be a DatetimeIndex"
            )
        if not self.frame.index.is_monotonic_increasing:
            raise DataIntegrityError(
                f"{self.provenance.symbol}: index must be sorted ascending"
            )

    @property
    def symbol(self) -> str:
        return self.provenance.symbol


def assert_consistent_adjustment(datasets: dict[str, OHLCVDataset]) -> None:
    """Fail closed if adjusted and unadjusted series are mixed (spec L82)."""
    flags = {sym: ds.provenance.adjusted for sym, ds in datasets.items()}
    distinct = set(flags.values())
    if len(distinct) > 1:
        adjusted = sorted(s for s, a in flags.items() if a)
        unadjusted = sorted(s for s, a in flags.items() if not a)
        raise DataIntegrityError(
            "adjusted/unadjusted price series mixed in one run (fail-closed). "
            f"adjusted={adjusted} unadjusted={unadjusted}"
        )


class DataAdapter(abc.ABC):
    """Abstract OHLCV source. Concrete adapters return :class:`OHLCVDataset`."""

    #: short stable identifier recorded in provenance
    name: str = "abstract"

    #: whether this source returns split/dividend-adjusted closes
    adjusted: bool = True

    @abc.abstractmethod
    def fetch(self, symbol: str, start: str, end: str) -> OHLCVDataset:
        """Return daily OHLCV for ``symbol`` over ``[start, end]`` inclusive."""

    def fetch_many(
        self, symbols: list[str], start: str, end: str
    ) -> dict[str, OHLCVDataset]:
        out: dict[str, OHLCVDataset] = {}
        for sym in symbols:
            out[sym] = self.fetch(sym, start, end)
        assert_consistent_adjustment(out)
        return out
