from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# make the repo root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtest_lab.data.synthetic import SyntheticAdapter  # noqa: E402


@pytest.fixture
def synth_frame() -> pd.DataFrame:
    """A multi-year deterministic synthetic frame (bear/base/bull regimes)."""
    ds = SyntheticAdapter().fetch("TEST", "2019-01-01", "2025-12-31")
    return ds.frame


@pytest.fixture
def short_frame() -> pd.DataFrame:
    ds = SyntheticAdapter().fetch("SHORT", "2022-01-01", "2024-12-31")
    return ds.frame
