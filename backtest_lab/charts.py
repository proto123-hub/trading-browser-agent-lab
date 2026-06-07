"""Chart generation for Phase 3 (spec L288).

All figures are written as PNGs via the non-interactive Agg backend, so the
pipeline produces them headlessly. Charts are diagnostics built from real-data
backtest outputs.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def _save(fig, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path


def equity_vs_baseline(equity: dict[str, pd.Series], title: str, path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, eq in equity.items():
        ax.plot(eq.index, eq.to_numpy(), label=name, linewidth=1.2)
    ax.set_title(title)
    ax.set_ylabel("growth of $1")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    return _save(fig, path)


def drawdown_curves(equity: dict[str, pd.Series], title: str, path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4))
    for name, eq in equity.items():
        dd = eq / eq.cummax() - 1.0
        ax.plot(dd.index, dd.to_numpy(), label=name, linewidth=1.0)
    ax.set_title(title)
    ax.set_ylabel("drawdown")
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(alpha=0.3)
    return _save(fig, path)


def forward_return_distribution(
    forward_df: pd.DataFrame, window_col: str, title: str, path
) -> Path:
    """Box/violin of forward returns grouped by scenario."""
    fig, ax = plt.subplots(figsize=(8, 5))
    groups, labels = [], []
    for scen, sub in forward_df.groupby("scenario"):
        vals = pd.to_numeric(sub[window_col], errors="coerce").dropna().to_numpy()
        if len(vals) >= 3:
            groups.append(vals)
            labels.append(f"{scen}\n(n={len(vals)})")
    if groups:
        ax.boxplot(groups, tick_labels=labels, showmeans=True)
        ax.axhline(0, color="k", linewidth=0.6)
    ax.set_title(title)
    ax.set_ylabel(window_col + " forward return")
    ax.grid(alpha=0.3, axis="y")
    return _save(fig, path)


def sensitivity_heatmap(
    matrix: pd.DataFrame, title: str, path, cbar_label: str = "Sharpe"
) -> Path:
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(matrix.to_numpy(dtype=float), aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels([str(c) for c in matrix.columns], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels([str(i) for i in matrix.index], fontsize=8)
    ax.set_xlabel(matrix.columns.name or "param x")
    ax.set_ylabel(matrix.index.name or "param y")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label=cbar_label)
    for (j, i), v in np.ndenumerate(matrix.to_numpy(dtype=float)):
        if np.isfinite(v):
            ax.text(i, j, f"{v:.2f}", ha="center", va="center", color="w", fontsize=7)
    return _save(fig, path)


def trade_timeline(
    close: pd.Series, txns: pd.DataFrame, title: str, path
) -> Path:
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(close.index, close.to_numpy(), color="#333", linewidth=1.0, label="close")
    if txns is not None and not txns.empty:
        t = txns.copy()
        t["date"] = pd.to_datetime(t["date"])
        buys = t[t["action"] == "BUY"]
        sells = t[t["action"] == "SELL"]
        ax.scatter(buys["date"], buys["price"], marker="^", color="green", s=40, label="BUY", zorder=5)
        ax.scatter(sells["date"], sells["price"], marker="v", color="red", s=40, label="SELL", zorder=5)
    ax.set_title(title)
    ax.set_ylabel("price")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    return _save(fig, path)
