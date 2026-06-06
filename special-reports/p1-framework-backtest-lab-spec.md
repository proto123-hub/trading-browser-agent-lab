# P1 Framework Backtest Lab — Codex Implementation Spec

**Version**: v1.1 (Claude line-level review applied, 2026-06-06)
**Canonical copy**: vault `AI_STOCK_Agent/Reports/special-reports/` — repo copy must match this file.
**Review basis**: `special-reports/yin-yun-breakthrough-framework-v2-2026-05-07.md` (310 lines, SHA-256 prefix `7fc94586eb4b3a0c`). All `[v2 L..]` tags below reference line numbers in that file.

## v1.1 Review Changelog (Claude review fixes vs Codex v1.0)

1. **FIX-1 (critical)**: "Four Scenario Labels" replaced. Codex v1.0 used generic state-based Ichimoku regime labels; canonical scenarios A-D are event-based, cloud-color-specific transitions [v2 L37-44]. Scenario A (bearish-cloud breakthrough — the framework's core rule) was missing entirely.
2. **FIX-2**: Stage 1 accumulation predicates restored: -3% to -5% approach zone below cloud top, SMA200 filter, 25-50% sizing, SMA200 -7% stop [v2 L71-82].
3. **FIX-3**: Canonical stop-loss hierarchy restored (immediate-exit rules, Stage 2 stop, ATR stop) [v2 L93, L108-111, L139]. "Kijun break" demoted to non-canonical variant.
4. **FIX-4**: Re-breakthrough 5 checks enumerated with thresholds [v2 L54-60]; ≤3/5 → max 50% sizing rule added [v2 L63].
5. **FIX-5**: Scenario B staged reduction ladder (33% / 33% / SMA200 100%) added [v2 L113-117].
6. **FIX-6**: AVGO and MRVL added to universe (named Melt-Up/shock cases: 6/4 AVGO -12.59%, MRVL climax watch). WDC/SNDK excluded (insufficient history; SNDK 2025 spin-off).

## Objective

Build a reproducible backtest lab that quantitatively evaluates the current discretionary framework before any portfolio redeployment. The first target is to validate whether the canonical Ichimoku scenario framework, Melt-Up primary/secondary signal logic, market breadth regime filters, and tiered profit-taking rules have measurable edge versus simple benchmarks.

Hard rule: this project must not place, route, recommend immediate execution of, or automate live trades. It is research-only.

## Current Context

- Portfolio state to protect: `GOOGL 150 + Cash`.
- Current process risk: several active rules are being used without historical validation.
- Source-of-truth dependency: the original vault file `yin-yun-breakthrough-framework-v2-2026-05-07.md` must be committed to this repository before implementation starts. Do not reconstruct that file from summaries. (Status: committed `1fea8aa`, integrity verified byte-identical to vault.)
- Required repository path for the source file: `special-reports/yin-yun-breakthrough-framework-v2-2026-05-07.md`.
- Required source integrity: SHA-256 prefix `7fc94586eb4b3a0c`, exactly 310 lines, exactly 310 LF newlines, exactly 16,395 bytes.
- Priority rules needing validation:
  - Canonical scenarios A-D as defined below, including re-breakthrough validation.
  - Melt-Up primary and secondary signal behavior, including the March 18 MU `-30%` stress case.
  - MU `$950` behavior as a tiered profit-taking trigger, not as an entry trigger.
  - ATH compression sequence such as `11 -> 7 -> 3` as a market breadth regime filter, not as a single-name entry rule.
  - Re-entry decisions during a renewed momentum regime.
- Goal: convert qualitative rules into auditable numbers before capital is redeployed.

## Repository Sync Requirements

This repository must contain both the implementation spec and the original framework v2 source before Phase 1 implementation starts. Codex cloud workspaces may be unable to perform raw `git push`; treat a raw push failure as an environment limitation, not as permission to bypass source integrity gates.

Accepted sync paths: (1) GitHub web upload, (2) Codex GitHub integration, (3) local desktop workflow from a clone outside OneDrive or other file-sync folders. All paths must preserve the source path and integrity checks above. The canonical spec lives in the vault; the repo copy must be byte-equivalent in content (line-ending normalization permitted for the spec, not for the framework source).

## Research Questions

1. Do the canonical scenarios A-D predict forward returns, drawdowns, or risk-adjusted outcomes better than baseline exposure?
2. Do Melt-Up primary and secondary signals identify asymmetric upside or downside risk, especially around the March 18 MU `-30%` case?
3. Does the MU `$950` tier trigger improve profit-taking outcomes versus fixed percentage, ATR, or no-tier baselines?
4. Does ATH compression (`11 -> 7 -> 3`) identify a statistically useful market breadth regime when applied as a portfolio or index-level filter?
5. Do tiered profit-taking rules improve terminal wealth, maximum drawdown, or behavioral robustness versus all-in/all-out exits?
6. Which rules are robust across symbols, years, volatility regimes, and earnings windows?

## Universe and Data

### Initial Universe

- `MU` (named events: 2026-03-18 -30% stress case; $950 tier trigger; 2026-06-04 first distribution day)
- `AVGO` (named event: 2026-06-04 -12.59% earnings shock)
- `MRVL` (named event: Melt-Up climax watch, 2026-06-02 +32.5%)
- `GOOGL`
- `NVDA`
- `AMD`
- `ARM`
- `QQQ`
- `SPY`

Excluded for now: `WDC`/`SNDK` (post-spin-off history too short for SMA200 + cloud warmup plus multi-regime coverage).

### Minimum Required Data

For each symbol:

- Daily OHLCV adjusted for splits/dividends, with a minimum 3 to 5 years of history per symbol.
- Corporate actions.
- Earnings dates and after-hours/pre-market timing where available.
- Optional but preferred: intraday bars around earnings, Melt-Up signal days, and tier trigger days.
- Required regime coverage should include the 2022 bear market and the 2024 to 2025 AI-led bull market where data availability permits.
- A 262-trading-day window is insufficient because SMA200 plus Senkou Span B plus 26-session forward cloud warmup can consume roughly one year before signals are usable.

### Data Quality Requirements

- Store data provenance per symbol and dataset.
- Fail closed when adjusted/unadjusted price series are mixed.
- Explicitly mark missing earnings timestamps.
- Cache raw inputs and derived features separately.
- Fail closed if `special-reports/yin-yun-breakthrough-framework-v2-2026-05-07.md` is missing from the repository.
- Fail closed if the source file does not match SHA-256 prefix `7fc94586eb4b3a0c`, exactly 310 lines, exactly 310 LF newlines, and exactly 16,395 bytes.
- Maintain line-level traceability from every canonical threshold in this spec back to the committed framework v2 source file.

## Feature Engineering

### Ichimoku Features

Compute standard Ichimoku components (daily, standard 9/26/52 with 26-session displacement) [v2 L26-33]:

- Tenkan-sen (9-session midpoint).
- Kijun-sen (26-session midpoint).
- Senkou Span A ((Tenkan+Kijun)/2, shifted +26).
- Senkou Span B (52-session midpoint, shifted +26).
- Chikou Span (close shifted -26).
- Cloud color: bearish when Senkou A < Senkou B; bullish when Senkou A > Senkou B [v2 L10-20].
- Cloud top = max(Senkou A, Senkou B); cloud bottom = min(Senkou A, Senkou B).
- Cloud thickness = |Senkou A - Senkou B| (used by re-breakthrough check 3).
- Price position relative to cloud; Tenkan/Kijun cross state.

### Canonical Scenario Labels A-D (event-based) [v2 L37-44]

These are the rules under test. Implement as configurable predicates; every fired predicate must be logged with the bar date.

**Scenario A — Bearish-cloud breakthrough success (LONG signal)** [v2 L41]
- Precondition: bearish cloud at signal date.
- Event: daily close crosses above cloud top, then holds above for 2 consecutive daily closes [v2 L41, L88].
- Action under test: LONG entry per Stage 2 confirmation below.

**Scenario B — Bullish-cloud breakdown (exit/SHORT signal)** [v2 L42]
- Precondition: bullish cloud; price previously above cloud.
- Event: daily close below cloud bottom, held for 2 consecutive daily closes.
- Action under test — staged reduction ladder (retail variant, no short selling) [v2 L113-117]:
  - Cloud-bottom approach within -3% with RSI < 50 -> reduce position 33% [v2 L115].
  - 2-day close below cloud bottom -> reduce a further 33% (cumulative 66%) [v2 L116].
  - SMA200 close break -> exit 100% [v2 L117].

**Scenario C — Failed breakthrough (stand aside; re-breakthrough validation)** [v2 L43, L48-51]
- Event: one daily close above bearish-cloud top followed by a close back inside the cloud [v2 L49].
- Sub-label: attempt volume below 20-day average -> fake breakout [v2 L50].
- Re-breakthrough validation — five checks [v2 L54-60]:
  1. Support: volume-confirmed bullish candle at SMA50 or SMA200 after 3-5 sessions of consolidation [v2 L56].
  2. Volume: second-attempt volume at least +30% versus first attempt [v2 L57].
  3. Cloud thinning: cloud thickness at least 20% smaller than at first attempt [v2 L58].
  4. Bullish RSI divergence: second-attempt price low >= first-failure low while RSI is higher [v2 L59].
  5. Tenkan > Kijun [v2 L60].
- Scoring: >= 4 of 5 -> LONG signal stronger than first attempt [v2 L62]; <= 3 of 5 -> entry permitted only at max 50% of target size [v2 L63].

**Scenario D — Bullish-cloud continuation (HOLD / staged accumulation)** [v2 L44]
- State: price above bullish cloud.
- Action under test: hold; adds and exits governed by the 3-Stage engine and tier rules.

Note: Codex v1.0's generic regime labels (trend continuation / pullback reset / compression / breakdown) are NOT canonical. They may be implemented only as separately named exploratory diagnostics and must never be reported as canonical scenario results.

### Three-Stage Entry/Exit Engine (canonical) [v2 L67-111]

**Stage 1 — Accumulation (pre-entry)** [v2 L71-82]
- Zone: price within -3% to -5% below bearish-cloud top (breakthrough-imminent approach) [v2 L72, L75].
- RSI (Wilder 14d) 45-55 [v2 L76].
- Volume 1.0-1.3x of 20-day average [v2 L77].
- Long-term filter: close above SMA200 [v2 L78].
- Size: 25-50% of target [v2 L79].
- Stop: SMA200 -7% [v2 L80].

**Stage 2 — Confirmed entry** [v2 L84-95]
- Trigger: 2 consecutive daily closes above cloud top [v2 L88].
- Volume >= 1.5x of 20-day average [v2 L89].
- RSI 55-70 [v2 L90].
- Tenkan > Kijun [v2 L91].
- Size: add 25-50% (cumulative 75-100%) [v2 L92].
- Stop: entry -7% to -10%, or SMA50 close break [v2 L93].

**Stage 3 — Tiered profit-taking 33% / 33% / 33%** [v2 L97-104]
- Tier 1: RSI >= 75 OR +20% from entry [v2 L102].
- Tier 2: Bollinger upper band +2 ATR OR +35% from entry [v2 L103].
- Tier 3 (trailing): SMA50 close break [v2 L104].

**Immediate exits (override all holds)** [v2 L108-111]
- Close back below cloud top for 2+ sessions -> sell 50% immediately [v2 L109].
- High-volume bearish candle closing below breakout level -> fake breakout confirmed -> sell 100% [v2 L110].
- SMA50 close break -> trailing 33% exit [v2 L111].

**ATR module (14-day)** [v2 L138-141]
- Alternative stop: entry -1.5 ATR [v2 L139].
- Alternative targets: entry +3 ATR (tier 1) / +5 ATR (tier 2) [v2 L140].
- ATR expansion -> reduce position size [v2 L141].

### ATH Compression Features

Track rolling all-time-high distance and compression windows primarily on market and breadth proxies. Single-symbol calculations are allowed only for explicitly labeled exploratory diagnostics:

- Days since ATH; percent below ATH.
- Rolling high windows: 3, 7, 11, 21, 50, 100, 252 trading days.
- Compression sequence detector for patterns like `11 -> 7 -> 3` (count of names making new ATHs shrinking across sessions).
- Breakout confirmation and failed breakout after compression.

### RSI Calculation Standard

Use Wilder 14-day RSI as the canonical RSI implementation for backtest and operations parity [v2 L123]. Do not silently substitute Cutler 14-day RSI. If Cutler RSI is computed for comparison (current dashboard cron uses Cutler), log it as a separate feature with a distinct name and exclude it from canonical rule pass/fail decisions.

### MU `$950` Tier Trigger Features

Parameterize MU `$950` as a profit-taking tier trigger, not an entry trigger:

- Static tier event: close crosses above `$950`; intraday tier event if intraday data exists.
- Confirmation variants: same-day close; two-day close hold (matching canonical confirmation); retest-and-hold; volume-confirmed cross.
- Failure variants: close back below trigger within 1, 3, 5, or 10 sessions.
- Output must compare selling the configured tier at `$950` versus holding, ATR-based tiering, RSI-based tiering, and fixed percentage tiering.

### Earnings Features

- Days to next earnings; days since last earnings.
- Earnings gap direction and magnitude.
- Post-earnings drift windows: 1, 3, 5, 10, 20 sessions.
- Whether a signal occurred inside an earnings exclusion or event window.

### Melt-Up Signal Features

- Primary signal predicates: open at/near ATH -> new intraday high -> heavy-volume selling -> bearish close (failed new-high day on high volume).
- Secondary signal predicates: failed new high plus down gap.
- Signal stacking and conflict handling when primary and secondary signals disagree.
- Stress-case annotation for March 18 MU `-30%`, including whether the signal would have reduced exposure, delayed re-entry, or created a false positive.
- Forward and adverse excursion windows after each signal: 1, 3, 5, 10, 20, and 60 sessions.

### Market Breadth Regime Features

- Compute `11 -> 7 -> 3` and related compression sequences on index or breadth proxies such as `QQQ`, `SPY`, and declared breadth datasets.
- Join the regime filter to single-name strategies only as a gating, sizing, or risk-control variable.
- Do not treat ATH compression as a standalone single-name entry trigger unless a separate experiment is explicitly labeled exploratory.

## Strategy Rules to Backtest

### Baselines

- Buy and hold.
- Cash-only.
- 50/200-day moving-average trend filter.
- Breakout above prior 20-day high.
- Random-entry placebo with matched holding periods.

### Canonical Scenario Strategy (A-D)

- Enter long on Scenario A confirmation via the Stage 1 + Stage 2 engine; track Stage-1-only and Stage-2-only variants.
- Apply Scenario C re-breakthrough scoring with the 4-of-5 full-size / 3-or-fewer half-size rule.
- Reduce/exit on Scenario B ladder and on immediate-exit overrides.
- Hold/add on Scenario D subject to tier rules.
- Optional earnings blackout toggle; optional minimum volume/liquidity filter.

### Melt-Up Signal Strategy

- Backtest Melt-Up primary and secondary signals as risk-on, risk-off, or exposure-scaling overlays.
- Include the March 18 MU `-30%` case as a named stress event in trade and signal reports.
- Compare primary-only, secondary-only, stacked-confirmation, and conflict-aware variants.
- Run variants with and without earnings blackout.

### MU `$950` Tier Strategy

- Do not enter merely because MU crosses `$950`.
- If a position already exists, test whether crossing and confirming above `$950` should trigger a configured profit-taking tier.
- Compare variants using same-day close, two-day close hold, retest-and-hold, and volume confirmation.
- Exit or reduce further only on failed retest, canonical Scenario B/immediate-exit rules, stop-loss, or subsequent tier target completion.

### ATH Compression Breadth Filter Strategy

- Apply compression sequences as market breadth gates or sizing filters for single-name strategies.
- Compare variants using `11 -> 7 -> 3`, `21 -> 11 -> 7`, and `50 -> 21 -> 11` on declared market or breadth proxies.
- Report whether the filter improves drawdown, hit rate, and false-positive control for scenario, Melt-Up, and tier strategies.

### Tiered Profit-Taking Strategy

- Canonical tier size default: `33% / 33% / 33%`; alternative sizing may be tested separately.
- Canonical tier triggers: Tier 1 at RSI `75` or `+20%`; Tier 2 at Bollinger upper band plus `2 ATR` or `+35%`; final tier via SMA50 trailing logic.
- Alternative triggers based on ATR multiples (+3/+5 ATR) or prior extension bands.
- Remainder management (canonical first, variants labeled): SMA50 trailing (canonical); cloud-top 2-session break 50% rule (canonical); fixed time stop (variant); Kijun break (variant, non-canonical).

## Risk and Execution Assumptions

- No live execution integration.
- Include transaction costs and slippage assumptions.
- Default assumptions: commission `0` unless configured; slippage `5 bps` for liquid megacaps/ETFs, configurable by symbol; enter/exit at next session open after signal by default.
- Prevent lookahead bias: signals use data available at decision time only (note Senkou displacement: the cloud evaluated at date T is the one projected to T, never recomputed with future data); earnings timestamp alignment must distinguish pre-market, regular session, and after-hours events.

## Evaluation Metrics

For every strategy and variant: CAGR, total return, volatility, Sharpe, Sortino, maximum drawdown, Calmar, win rate, average win/loss, profit factor, exposure time, turnover, average holding period, best/worst trades, and post-signal forward returns (1, 3, 5, 10, 20, 60 sessions).

## Robustness Tests

- Walk-forward split by year.
- Bull, bear, and sideways regime segmentation.
- Earnings-window inclusion/exclusion comparison.
- Parameter sensitivity heatmaps.
- Symbol-level leave-one-out validation.
- Placebo/randomized-entry comparison.
- Bootstrap confidence intervals for trade outcomes.

## Outputs

### Required Artifacts

1. Machine-readable results tables: `results/summary.csv`, `results/trades.csv`, `results/forward_returns.csv`, `results/parameter_sweep.csv`.
2. Human-readable report: `reports/p1_framework_backtest_lab.md`.
3. Source traceability table: `results/framework_v2_traceability.csv` with columns `spec_rule`, `framework_v2_line_start`, `framework_v2_line_end`, `status`, `notes`.
4. Charts: equity curves versus baseline; drawdown curves; scenario-conditioned forward return distributions; parameter sensitivity heatmaps; trade timeline overlays for MU and GOOGL.

### Report Must Answer

- Which rules should be kept, modified, or rejected?
- Which rules only work in narrow regimes?
- Whether MU `$950` is useful as a profit-taking tier trigger or merely narrative anchoring.
- Whether ATH compression has value as a market breadth regime filter after costs.
- Whether tiered profit-taking improves drawdown enough to justify opportunity cost.
- What should be tested next before redeployment.
- Whether every canonical parameter was line-checked against `special-reports/yin-yun-breakthrough-framework-v2-2026-05-07.md`.

## Suggested Implementation Plan

### Phase 0 — Source Sync and Traceability (status: complete except traceability CSV)

- Framework v2 source committed (`1fea8aa`) and verified byte-identical to vault.
- Create the line-level traceability table mapping this spec to the framework v2 source (the `[v2 L..]` tags above are the starting point).
- Block implementation if the source file is absent or fails integrity checks.

### Phase 1 — Backtest Harness

- Data loading and validation layer.
- Ichimoku, Wilder RSI, Melt-Up, ATH breadth filter, tier trigger, and earnings features.
- Baseline strategies.
- Unit tests for feature calculations and no-lookahead alignment, including Senkou displacement tests and the 2-day-close confirmation logic.

### Phase 2 — Strategy Variants

- Canonical scenario strategy variants (A-D, Stage engine, re-breakthrough scoring).
- Melt-Up signal variants; MU `$950` tier variants; ATH breadth filter variants; tiered profit-taking variants.

### Phase 3 — Analysis and Reporting

- Metrics, charts, result tables; robustness tests; final markdown report with keep/modify/reject recommendations.

## Acceptance Criteria

- The framework v2 source file exists at the required path and matches SHA-256 prefix `7fc94586eb4b3a0c`, exactly 310 lines, exactly 310 LF newlines, exactly 16,395 bytes.
- Scenario definitions in code are event-based and cloud-color-specific, matching framework v2 lines 37-63 and 67-117 (v1.1 review FIX-1).
- The source traceability table maps canonical thresholds to framework v2 line numbers.
- The full pipeline runs with one command; results reproducible from cached or declared data sources.
- No strategy uses future data.
- Every rule variant is parameterized and logged.
- Backtest results include baselines and robustness checks.
- The final report explicitly flags weak evidence, overfitting risk, and data limitations.

## Non-Goals

- No live trading, brokerage integration, or automatic order generation.
- No claim that backtest performance predicts future returns.
- No unverified single-source data dependency for final conclusions.
- No Hanja characters in this specification or generated report artifacts unless they appear inside an unavoidable source title.
