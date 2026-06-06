"""ATH compression breadth filter as a gate / sizing overlay (spec L247-251).

Compression sequences (e.g. ``11 -> 7 -> 3``) computed on breadth proxies
(QQQ/SPY) are joined to a single-name base strategy as a *gate or sizing*
variable, never as a standalone single-name entry trigger (spec L213). When the
breadth regime is compressing, the base position is scaled by ``risk_off_scale``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..features.ath_breadth import compression_sequence


@dataclass(frozen=True)
class BreadthFilterConfig:
    windows: tuple[int, int, int] = (11, 7, 3)   # also 21->11->7, 50->21->11
    mode: str = "gate"                            # gate | scale
    risk_off_scale: float = 0.0                   # exposure when compressing


def compression_regime(
    proxy_closes: pd.DataFrame, windows: tuple[int, int, int] = (11, 7, 3)
) -> pd.Series:
    comp = compression_sequence(proxy_closes, windows)
    return comp["compression"].fillna(False).astype(bool)


def apply_breadth_filter(
    base_position: pd.Series,
    compression: pd.Series,
    config: BreadthFilterConfig | None = None,
) -> pd.Series:
    """Scale ``base_position`` down where the breadth regime is compressing."""
    cfg = config or BreadthFilterConfig()
    comp = compression.reindex(base_position.index).fillna(False).astype(bool)
    scale = pd.Series(1.0, index=base_position.index)
    if cfg.mode == "gate":
        scale[comp] = cfg.risk_off_scale
    elif cfg.mode == "scale":
        scale[comp] = cfg.risk_off_scale
    else:
        raise ValueError(f"unknown mode {cfg.mode!r}")
    return (base_position * scale).clip(0.0, 1.0)
