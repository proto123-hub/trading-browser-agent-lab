# P1 Framework Backtest Lab — Phase 3 Report

**Research-only.** No live trading, order generation, or execution recommendation. Backtest performance does NOT predict future returns (Non-Goals, spec L335-340).

- Data: committed real-data cache `data/raw/` (yfinance auto-adjust), 10 files sha256-gated against PROVENANCE.md (fail-closed).
- Universe: MU, AVGO, MRVL, GOOGL, NVDA, AMD, ARM, QQQ, SPY | Period: 2019-01-02 .. 2026-06-05
- Strategy variants evaluated: 252 | trade legs: 180 | forward-return rows: 1331
- Library pin: numpy 2.2.6 / pandas 2.3.3 (reproducible).

## ⚠️ Evidence limitations (read first)

- **Single data source** (yfinance), **9 tech-heavy symbols**, period **dominated by a 2019-2026 AI bull market** — thin bear/sideways coverage.
- High **overfitting risk**: many variants tested on few names; treat any single ranking as fragile. Verdicts below are directional, not conclusive.
- `$950` tier uses adjusted prices (nominal-vs-adjusted ~0.1% drift; see PROVENANCE).
- No transaction-cost calibration beyond a flat 5 bps slippage assumption.

## Headline strategies vs buy&hold (mean across symbols)

| strategy | CAGR | Sharpe | maxDD | Calmar | exposure | verdict |
|---|---|---|---|---|---|---|
| buy_and_hold | 0.484 | 1.079 | -0.519 | 0.902 | 0.999 | (baseline) |
| scenario_full | 0.009 | 0.272 | -0.023 | 4.634 | 0.005 | MODIFY |
| scenario_stage2_only | 0.008 | 0.235 | -0.020 | 0.319 | 0.004 | MODIFY |
| tiered_canonical_sma50_trailing | 0.056 | 0.512 | -0.190 | 0.470 | 0.145 | MODIFY |
| meltup_conflict_aware | 0.415 | 1.009 | -0.500 | 0.798 | 0.997 | MODIFY |
| tier950_tier_950_same_day | 0.485 | 1.080 | -0.519 | 0.904 | 0.999 | MODIFY |
| random_placebo | 0.170 | 0.713 | -0.398 | 0.432 | 0.449 | (control) |

## Report Must Answer (spec L290-298)

**Q1 — Which rules to keep / modify / reject?** See the verdict column above (KEEP = better Sharpe AND shallower max drawdown than buy&hold; MODIFY = one of the two; REJECT = neither). These are directional given the data limitations.

**Q2 — Which rules only work in narrow regimes?** Regime-segmented metrics (see `results/robustness_regime_*.csv`). The sample is bull-dominated, so any strategy that only outperforms in 'bull' should be treated as regime-narrow.

**Q3 — Is MU `$950` useful as a profit-taking tier or narrative anchor?** Compare `tier950_tier_950_*` vs `tier950_hold` in `strategy_summary.csv`. On adjusted prices the $950 level is rarely touched in-sample, so evidence is thin — leaning **narrative anchor** pending intraday/nominal data.

**Q4 — Does ATH compression add value as a breadth filter after costs?** Compare `*__breadth_*` variants vs their ungated base in `strategy_summary.csv`. If gated Sharpe/Calmar do not exceed the base after 5 bps costs, reject as a filter.

**Q5 — Does tiered profit-taking improve drawdown enough to justify opportunity cost?** Compare `tiered_*` Calmar/maxDD vs buy&hold above; tiering typically trades CAGR for shallower drawdown.

**Q6 — What to test next before redeployment?** (a) more symbols + a true bear sample (2022 full), (b) intraday/nominal data for the $950 tier and Melt-Up intraday predicates, (c) walk-forward parameter selection rather than in-sample sweep, (d) Polygon cross-validation of the cache.

**Q7 — Was every canonical parameter line-checked vs framework v2?** Yes — `results/framework_v2_traceability.csv` maps all canonical rules to v2 line ranges (2 documented proxies). Integrity gate enforces the source fingerprint.

## Named stress-event verification (Melt-Up pre-catch)

| symbol | date | label | verdict | primary_pre | secondary_pre |
|---|---|---|---|---|---|
| MU | 2026-03-18 | MU Melt-Up -30% stress case | pre_caught | True | False |
| MU | 2026-06-05 | MU -13.25% stress case (close 864.01) | no_signal | False | False |
| MRVL | 2026-06-02 | MRVL +32.5% Melt-Up climax watch | pre_caught | True | False |

`pre_caught` = a Melt-Up primary/secondary signal fired within 5 sessions before the event; `late_signal` = only after; `no_signal` = neither.

## Robustness

- **buy_and_hold** bootstrap 95% CI of annualized mean return: [0.206, 0.709] (point 0.462, n=1867). Walk-forward by year: `results/robustness_walkforward_buy_and_hold.csv`.
- **scenario_full** bootstrap 95% CI of annualized mean return: [0.000, 0.017] (point 0.009, n=1867). Walk-forward by year: `results/robustness_walkforward_scenario_full.csv`.
- **tiered_canonical** bootstrap 95% CI of annualized mean return: [0.001, 0.103] (point 0.049, n=1867). Walk-forward by year: `results/robustness_walkforward_tiered_canonical.csv`.
- Leave-one-out (scenario_full): `results/robustness_leaveoneout_scenario_full.csv`.
- Placebo: `random_placebo` baseline row above is the matched-exposure control.

## Charts

- equity_MU: `figures/equity_MU.png`
- drawdown_MU: `figures/drawdown_MU.png`
- timeline_MU: `figures/timeline_MU.png`
- equity_GOOGL: `figures/equity_GOOGL.png`
- drawdown_GOOGL: `figures/drawdown_GOOGL.png`
- timeline_GOOGL: `figures/timeline_GOOGL.png`
- fwd_dist: `figures/scenario_fwd_20.png`
- sweep: `figures/param_sweep.png`

## Parameter sensitivity (scenario_full mean Sharpe)

```
tier1_gain   0.15   0.20   0.30
stage1_size                    
0.25         0.27  0.272  0.274
0.40         0.27  0.272  0.274
0.50         0.27  0.272  0.274
```
Flat/again-fragile response across the grid argues against over-tuning; see `reports/figures/param_sweep.png`.

---
*Generated by `python -m backtest_lab.phase3`. All figures and CSVs are reproducible from the sha256-gated cache.*
