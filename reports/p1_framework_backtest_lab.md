# P1 Framework Backtest Lab — Phase 3 Report

**Research-only.** No live trading, order generation, or execution recommendation. Backtest performance does NOT predict future returns (Non-Goals, spec L335-340).

- Data: committed real-data cache `data/raw/` (yfinance auto-adjust), 10 files sha256-gated against PROVENANCE.md (fail-closed).
- Universe: MU, AVGO, MRVL, GOOGL, NVDA, AMD, ARM, QQQ, SPY | Period: 2019-01-02 .. 2026-06-05
- Strategy variants evaluated: 252 | trade legs: 2354 | forward-return rows: 1331
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

> **Footnote (R2):** the table is a 9-symbol mean, which dilutes single-symbol trigger effects (e.g. the MU `$950` tier — see Q3).

## Report Must Answer (spec L290-298)

**Q1 — Which rules to keep / modify / reject?** See the verdict column above (KEEP = better Sharpe AND shallower max drawdown than buy&hold; MODIFY = one of the two; REJECT = neither). These are directional given the data limitations.

**Q2 — Which rules only work in narrow regimes?** Regime-segmented metrics in `results/robustness_regime_*.csv`. The sample is bull-dominated, so any strategy that only outperforms in 'bull' is regime-narrow; the canonical scenario engine in particular barely activates outside bearish-cloud setups.

**Q3 — Is MU `$950` useful as a profit-taking tier or narrative anchor?** The trigger DID fire (MU crossed $950 in May 2026). MU-only total return: **two_day 27.803 > same_day 27.205 > hold 26.036** — the 2-day-confirmed tier was the in-sample best, so on this single symbol the $950 rule reads as a **profit-taking tier (in-sample, MU)**. Caveat: **n=1 trigger event**, statistically negligible; the 9-symbol-mean headline dilutes it to ~buy&hold. All tier legs are now in `results/trades.csv` for audit.

**Q4 — Does ATH compression add value as a breadth filter after costs?** **No evidence — the gate never activated.** Every `*__breadth_*` variant is identical to its ungated base (scenario_full total return 0.082 == gated 0.082). Cause: the `11→7→3` compression sequence needs a broad set of names making new highs; with only 2 ETF proxies (QQQ/SPY) the shrinking-count condition is effectively never met. **Verdict: inconclusive — requires a true multi-symbol breadth dataset before it can be evaluated.**

**Q5 — Does tiered profit-taking improve drawdown enough to justify opportunity cost?** Yes on drawdown, no on return: tiered_canonical max drawdown **-0.190** vs buy&hold **-0.519** (much shallower), but CAGR **0.056** vs **0.484** (large give-up). Tiering buys drawdown protection at a steep return cost in a bull sample — justified only for capital-preservation mandates, not total-wealth maximization.

**Q6 — What to test next before redeployment?** (a) more symbols + a true bear sample (2022 full), (b) intraday/nominal data for the $950 tier and Melt-Up intraday predicates, (c) walk-forward parameter selection rather than in-sample sweep, (d) Polygon cross-validation of the cache.

**Q7 — Was every canonical parameter line-checked vs framework v2?** Yes — `results/framework_v2_traceability.csv` maps all canonical rules to v2 line ranges (2 documented proxies). Integrity gate enforces the source fingerprint.

## Named stress-event verification (Melt-Up pre-catch)

| symbol | date | label | verdict | primary_pre | secondary_pre |
|---|---|---|---|---|---|
| MU | 2026-03-18 | MU Melt-Up -30% stress case | pre_caught | True | False |
| MU | 2026-06-05 | MU -13.25% stress case (close 864.01) | no_signal | False | False |
| MRVL | 2026-06-02 | MRVL +32.5% Melt-Up climax watch | pre_caught | True | False |

`pre_caught` = a Melt-Up primary/secondary signal fired within 5 sessions before the event; `late_signal` = only after; `no_signal` = neither.

## Exploratory (NON-CANONICAL): relaxed Melt-Up primary

The canonical primary missed MU 2026-06-05 because it requires the open within ~1% of the ATH **and** a new intraday high — but 6/5 was a distribution day a couple of sessions *after* the ATH, with no new high. A relaxed, **non-canonical** primary — *failed high within 5 sessions of a recent ATH + elevated-volume (>=1.2x 20d avg, vs canonical 1.5x) bearish close* — is tested only as an exploratory diagnostic (not adopted as canon; one post-hoc case is overfitting-prone). The 1.2x relaxation matters: MU 6/5 volume was ~1.35x its 20d average — elevated, but under the canonical 1.5x because the run-up inflated the average.

- MU 2026-06-05 capture: canonical **False** -> relaxed **True**.
- False-positive cost (total primary signals across 9 symbols): canonical **103** -> relaxed **260** (+157). Per-symbol breakdown: `results/meltup_exploratory.csv`.
- **Recommendation:** do NOT amend the canonical v2 rule on one case. If the relaxed variant is pursued, validate it out-of-sample (more symbols, and measure post-signal forward returns vs the extra false positives) before any vault-canon change.

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
