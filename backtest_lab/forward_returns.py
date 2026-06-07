"""Post-signal forward returns over standard windows (spec L207, L269).

Forward returns are computed with future prices and are therefore an
*evaluation* output, never a signal input. They quantify what happened after a
signal fired; they must not feed back into any position decision.
"""

from __future__ import annotations

import pandas as pd

FORWARD_WINDOWS = [1, 3, 5, 10, 20, 60]


def forward_returns(
    close: pd.Series, windows: list[int] | None = None
) -> pd.DataFrame:
    windows = windows or FORWARD_WINDOWS
    out = pd.DataFrame(index=close.index)
    for w in windows:
        out[f"fwd_{w}"] = close.shift(-w) / close - 1.0
    return out


def signal_forward_returns(
    close: pd.Series,
    signal: pd.Series,
    symbol: str,
    strategy: str,
    windows: list[int] | None = None,
) -> pd.DataFrame:
    """Long-form forward-return rows for each bar where ``signal`` is True."""
    fwd = forward_returns(close, windows)
    mask = signal.fillna(False).astype(bool)
    rows = []
    for date in close.index[mask.to_numpy()]:
        row = {"date": date, "symbol": symbol, "strategy": strategy}
        for col in fwd.columns:
            row[col] = fwd.at[date, col]
        rows.append(row)
    cols = ["date", "symbol", "strategy"] + list(fwd.columns)
    return pd.DataFrame(rows, columns=cols)
