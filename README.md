# P1 Framework Backtest Lab

Research-only backtest harness that converts the discretionary Ichimoku
"음운/양운돌파" framework into auditable numbers before any capital redeployment.

> **Hard rule (CLAUDE.md, spec L20):** research-only. No live trading, order
> generation, brokerage integration, or execution recommendations.

Canonical implementation spec:
`special-reports/p1-framework-backtest-lab-spec.md` (v1.1).
Framework source of truth (integrity-gated, never modified):
`special-reports/yin-yun-breakthrough-framework-v2-2026-05-07.md`.

## Quick start

```bash
pip install -r requirements.txt
python run.py                      # offline synthetic source (default)
pytest -q                          # unit tests
```

The default run uses a deterministic **synthetic** data source so the full
pipeline and tests run with no network. For live daily bars:

```bash
python run.py --source yfinance --symbols MU,GOOGL --start 2020-01-01 --end 2025-12-31
```

`--source polygon` is a stub for the planned cross-validation source (no API key
in this environment yet).

## What Phase 1 delivers

| Area | Module | Notes |
|------|--------|-------|
| Source integrity gate | `backtest_lab/integrity.py` | fail-closed: sha256 `7fc94586eb4b3a0c` / 310 lines / 16,395 bytes |
| Line-level traceability | `backtest_lab/traceability.py` -> `results/framework_v2_traceability.csv` | every canonical rule mapped to framework v2 line range |
| Data layer (adapter pattern) | `backtest_lab/data/` | synthetic (default) / yfinance / polygon stub; provenance; fail-closed on adjusted/unadjusted mixing |
| Features | `backtest_lab/features/` | Ichimoku 9/26/52 (+26 displacement), Wilder RSI 14 (Cutler kept separate), Bollinger 20/2, ATR 14, volume 20d multiple, ATH/breadth compression, Melt-Up predicates, earnings (manual CSV) |
| Scenario labeler A-D | `backtest_lab/scenarios/labeler.py` | **event-based, cloud-color-specific** (FIX-1); 2-day-close confirmation; re-breakthrough 5-check scorer; every fired predicate logged with its date |
| Baselines (5) | `backtest_lab/strategies/baselines.py` | buy&hold / cash / 50-200 MA / 20d breakout / random placebo |
| Backtest engine | `backtest_lab/strategies/engine.py` | long/flat, next-bar execution (no lookahead), slippage 5 bps default |
| 1-command pipeline | `backtest_lab/pipeline.py`, `run.py` | integrity -> traceability -> data -> features -> scenarios -> baselines |

### Unit tests (no lookahead is enforced)

- Senkou +26 displacement and cloud no-lookahead (`tests/test_ichimoku.py`)
- Wilder RSI / ATR seeding and bounds (`tests/test_rsi_atr.py`)
- 2-day-close confirmation; scenario A/B/C/D firing; re-breakthrough scoring;
  scenario no-lookahead (`tests/test_scenarios.py`)
- Feature no-lookahead via truncated-series equality (`tests/test_data_and_features.py`)
- Adjusted/unadjusted fail-closed; deterministic synthetic source
- Traceability completeness (`tests/test_traceability.py`)

## Out of scope here (Phase 2 / Phase 3)

Strategy variants (full A-D stage engine execution, Melt-Up / `$950` tier / ATH
breadth / tiered profit-taking strategies), the full metric/forward-return
tables, robustness sweeps, charts, and the final keep/modify/reject report.

## Data caveat

The synthetic source is **not market data** — it is a deterministic fixture
(bear/base/bull regimes) that exercises the harness and makes scenario
transitions fire. Real research conclusions require `--source yfinance` (or the
Polygon cross-check) and the data-quality gates in `backtest_lab/data/`.
