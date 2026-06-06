"""Feature engineering layer.

``compute_features`` assembles the full per-symbol feature frame used by the
scenario labeler and strategies. Derived features are cached separately from
raw inputs (spec L84) by the pipeline.
"""

from __future__ import annotations

import pandas as pd

from .ichimoku import ichimoku, IchimokuConfig
from .rsi import wilder_rsi, cutler_rsi
from .bollinger import bollinger
from .atr import atr, true_range
from .volume import volume_features, sma
from .ath_breadth import ath_features, compression_sequence, breadth_new_ath_count
from .meltup import meltup_features
from .earnings import earnings_features, load_earnings_csv

__all__ = [
    "compute_features",
    "ichimoku",
    "IchimokuConfig",
    "wilder_rsi",
    "cutler_rsi",
    "bollinger",
    "atr",
    "true_range",
    "volume_features",
    "sma",
    "ath_features",
    "compression_sequence",
    "breadth_new_ath_count",
    "meltup_features",
    "earnings_features",
    "load_earnings_csv",
]


def compute_features(
    frame: pd.DataFrame, earnings_dates: pd.Series | None = None
) -> pd.DataFrame:
    """Return a single feature frame for one symbol, indexed like ``frame``."""
    close = frame["close"]
    parts = [
        frame.copy(),
        ichimoku(frame),
        bollinger(close),
        volume_features(frame["volume"]),
        ath_features(close),
        meltup_features(frame),
        earnings_features(frame, earnings_dates),
    ]
    feats = pd.concat(parts, axis=1)
    feats["rsi_wilder_14"] = wilder_rsi(close)      # canonical
    feats["rsi_cutler_14"] = cutler_rsi(close)      # non-canonical diagnostic
    feats["atr_14"] = atr(frame)
    feats["sma20"] = sma(close, 20)
    feats["sma50"] = sma(close, 50)
    feats["sma200"] = sma(close, 200)
    # de-duplicate any overlapping column names (keep first occurrence)
    feats = feats.loc[:, ~feats.columns.duplicated()]
    return feats
