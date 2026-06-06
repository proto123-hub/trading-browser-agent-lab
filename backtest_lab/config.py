"""Default run configuration (spec L52-66, L264)."""

from __future__ import annotations

from dataclasses import dataclass, field

# Initial universe (spec L56-64). WDC/SNDK excluded (FIX-6, spec L66).
UNIVERSE: list[str] = ["MU", "AVGO", "MRVL", "GOOGL", "NVDA", "AMD", "ARM", "QQQ", "SPY"]

# Breadth proxies for ATH compression (spec L211).
BREADTH_PROXIES: list[str] = ["QQQ", "SPY"]

DEFAULT_START = "2019-01-01"
DEFAULT_END = "2025-12-31"


@dataclass
class RunConfig:
    symbols: list[str] = field(default_factory=lambda: list(UNIVERSE))
    start: str = DEFAULT_START
    end: str = DEFAULT_END
    source: str = "synthetic"      # synthetic (offline default) | yfinance | polygon
    slippage_bps: float = 5.0
    commission: float = 0.0
    results_dir: str = "results"
    cache_dir: str = "cache"
    earnings_csv: str | None = None
