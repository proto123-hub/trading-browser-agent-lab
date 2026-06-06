"""Polygon.io adapter stub for the planned cross-validation source.

The framework's operations side computes SMA50/SMA200 from Polygon
(framework v2 L152, L284-287). This adapter exists so a Polygon-backed run can
be cross-checked against yfinance via the same interface. It is intentionally
unimplemented here: Claude Code's cloud workspace has no Polygon API key
(see Phase 1 ordering note). Implement against `/v2/aggs/ticker/{T}/range/1/day`
when a key is available.
"""

from __future__ import annotations

from .base import DataAdapter, OHLCVDataset


class PolygonAdapter(DataAdapter):
    name = "polygon"
    adjusted = True

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def fetch(self, symbol: str, start: str, end: str) -> OHLCVDataset:
        raise NotImplementedError(
            "PolygonAdapter is a stub: provide an API key and implement "
            "/v2/aggs/ticker/{T}/range/1/day. Use --source synthetic or "
            "--source yfinance for now."
        )
